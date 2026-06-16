import asyncio
import random
import string
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8931382600:AAEOWYJGOC9mtYoIssNOX-AyV49fg6TZm6Q"
OWNER = 8048285990
ALLOWED = {OWNER, 111111111, 222222222}
RUDE = ["иди нахуй", "не для тебя бот, вали", "тебя сюда не звали", "соси, доступа нет"]

bot = Bot(TOKEN)
dp = Dispatcher()
active = {}
watch = set()

V = set("aeiou")
GOOD = {"alpha","bravo","delta","ghost","north","raven","storm","vodka","laser","ninja","tiger","onion","mango","blaze","frost","crown","royal","czars","queen","kings","piano","ocean","light","prime","viper","lemon","amber","ivory","pearl","ruby","noble"}

def make(use_digits):
    head = random.choice(string.ascii_lowercase)
    pool = string.ascii_lowercase + (string.digits if use_digits else "")
    return head + "".join(random.choice(pool) for _ in range(4))

def clusters(u, group):
    best = cur = 0
    for c in u:
        cur = cur + 1 if (c in group) == True else cur
        if (c in V) if group is V else (c not in V):
            cur += 0
    return best

def rarity(u):
    digits = sum(c.isdigit() for c in u)
    if digits:
        base = 22 - digits * 6
        if u[0].isdigit():
            base -= 5
        return max(1, base), "🗑 с цифрами — слабо"
    pts = 46
    why = "буквенный"
    flow = sum(1 for i in range(1, len(u)) if (u[i] in V) != (u[i - 1] in V))
    cons_run = 0
    run = 0
    for c in u:
        run = run + 1 if c not in V else 0
        cons_run = max(cons_run, run)
    if u in GOOD:
        pts += 34
        why = "💠 реальное слово"
    elif flow >= 4:
        pts += 17
        why = "произносимый"
    if cons_run >= 4:
        pts -= 14
    if len(set(u)) == 1:
        pts += 40
        why = "👑 один символ ×5"
    elif len(set(u)) == 2:
        pts += 24
        why = "редкий паттерн"
    codes = [ord(c) for c in u]
    if all(codes[i] - codes[i - 1] == 1 for i in range(1, 5)) or all(codes[i - 1] - codes[i] == 1 for i in range(1, 5)):
        pts += 26
        why = "📈 последовательность"
    if u == u[::-1]:
        pts += 16
        why = "палиндром"
    if any(u[i] == u[i + 1] for i in range(4)):
        pts += 5
    return max(1, min(100, pts)), why

def tier(p):
    if p >= 88:
        return "🔥 топ-тир"
    if p >= 68:
        return "💎 редкий"
    if p >= 48:
        return "✨ норм"
    return "обычный"

async def is_free(session, u):
    try:
        async with session.get(f"{{https://t.me/{u}}}", timeout=10) as r:
            html = (await r.text()).lower()
    except Exception:
        return None
    if "tgme_page_title" in html or "tgme_page_extra" in html or "you can contact" in html:
        return False
    return True

async def hunt(chat_id, use_digits):
    async with ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        seen = set()
        while active.get(chat_id):
            u = make(use_digits)
            if u in seen:
                continue
            seen.add(u)
            if await is_free(session, u):
                p, why = rarity(u)
                await bot.send_message(chat_id, f"@{u}\n{p}/100 — {tier(p)} · {why}")
            await asyncio.sleep(1.2)

async def watcher():
    async with ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
        while True:
            for u in list(watch):
                if await is_free(session, u):
                    watch.discard(u)
                    p, why = rarity(u)
                    await bot.send_message(OWNER, f"🟢 освободился @{u}\n{p}/100 — {tier(p)} · {why}")
                await asyncio.sleep(2)
            await asyncio.sleep(15)

def gate(m):
    return m.from_user.id in ALLOWED

@dp.message(Command("start"))
async def start(m: Message):
    if not gate(m):
        await m.answer(random.choice(RUDE))
        return
    await m.answer("/hunt — буквы+цифры\n/clean — только буквы\n/watch юз — следить\n/stop — стоп")

@dp.message(Command("hunt"))
async def h1(m: Message):
    if not gate(m):
        await m.answer(random.choice(RUDE)); return
    if active.get(m.chat.id):
        await m.answer("уже идёт"); return
    active[m.chat.id] = True
    await m.answer("ищу...")
    asyncio.create_task(hunt(m.chat.id, True))

@dp.message(Command("clean"))
async def h2(m: Message):
    if not gate(m):
        await m.answer(random.choice(RUDE)); return
    if active.get(m.chat.id):
        await m.answer("уже идёт"); return
    active[m.chat.id] = True
    await m.answer("ищу чисто буквенные...")
    asyncio.create_task(hunt(m.chat.id, False))

@dp.message(Command("watch"))
async def w(m: Message):
    if not gate(m):
        await m.answer(random.choice(RUDE)); return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("формат: /watch имя"); return
    watch.add(parts[1].lstrip("@").lower())
    await m.answer(f"слежу за @{parts[1].lstrip('@')}, скину как освободится")

@dp.message(Command("stop"))
async def stop(m: Message):
    if not gate(m):
        await m.answer(random.choice(RUDE)); return
    active[m.chat.id] = False
    await m.answer("стоп")

@dp.message()
async def other(m: Message):
    if not gate(m):
        await m.answer(random.choice(RUDE))

async def main():
    asyncio.create_task(watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
