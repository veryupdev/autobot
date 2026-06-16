import asyncio
import random
import string
from aiohttp import ClientSession, TCPConnector, ClientTimeout
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8931382600:AAEOWYJGOC9mtYoIssNOX-AyV49fg6TZm6Q"
OWNER = 8048285990
ALLOWED = {OWNER, 7209594427}
RUDE = ["иди нахуй", "не для тебя бот, вали", "тебя сюда не звали", "доступа нет, соси"]
UA = {"User-Agent": "Mozilla/5.0"}
HOST = "t.me"

bot = Bot(TOKEN)
dp = Dispatcher()
active = {}
watch = set()

V = set("aeiou")
GOOD = {"alpha","bravo","delta","ghost","north","raven","storm","vodka","laser","ninja","tiger","onion","mango","blaze","frost","crown","royal","queen","kings","piano","ocean","light","prime","viper","lemon","amber","ivory","pearl","noble","eagle","wolfs","brave"}

def link(u):
    return "https://" + HOST + "/" + u

def new_session():
    return ClientSession(headers=UA, connector=TCPConnector(ssl=False), timeout=ClientTimeout(total=15))

def make(use_digits):
    head = random.choice(string.ascii_lowercase)
    pool = string.ascii_lowercase + (string.digits if use_digits else "")
    return head + "".join(random.choice(pool) for _ in range(4))

def rarity(u):
    digits = sum(c.isdigit() for c in u)
    if digits:
        return max(1, 22 - digits * 6), "🗑 с цифрами — слабо"
    pts = 46
    why = "буквенный"
    flow = sum(1 for i in range(1, 5) if (u[i] in V) != (u[i - 1] in V))
    run = best = 0
    for c in u:
        run = run + 1 if c not in V else 0
        best = max(best, run)
    if u in GOOD:
        pts += 34; why = "💠 реальное слово"
    elif flow >= 4:
        pts += 17; why = "произносимый"
    if best >= 4:
        pts -= 14
    if len(set(u)) == 1:
        pts += 40; why = "👑 один символ ×5"
    elif len(set(u)) == 2:
        pts += 24; why = "редкий паттерн"
    codes = [ord(c) for c in u]
    if all(codes[i] - codes[i - 1] == 1 for i in range(1, 5)) or all(codes[i - 1] - codes[i] == 1 for i in range(1, 5)):
        pts += 26; why = "📈 последовательность"
    if u == u[::-1]:
        pts += 16; why = "палиндром"
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

def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Только буквы", callback_data="clean")],
        [InlineKeyboardButton(text="🔢 Буквы + цифры", callback_data="mixed")],
    ])

def stopkb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⏹ Стоп", callback_data="stop")]])

async def is_free(session, u):
    try:
        async with session.get(link(u), allow_redirects=True) as r:
            html = await r.text()
    except Exception:
        return None
    return "tgme_page_title" not in html

async def hunt(chat_id, use_digits, status_id):
    checked = found = fails = 0
    seen = set()
    async with new_session() as session:
        while active.get(chat_id):
            u = make(use_digits)
            if u in seen:
                continue
            seen.add(u)
            res = await is_free(session, u)
            checked += 1
            if res is None:
                fails += 1
            elif res:
                p, why = rarity(u)
                found += 1
                await bot.send_message(chat_id, f"🟢 @{u}\n{p}/100 — {tier(p)} · {why}")
            if checked % 8 == 0:
                try:
                    await bot.edit_message_text(f"🔎 проверено: {checked} · найдено: {found} · ошибок: {fails}", chat_id, status_id, reply_markup=stopkb())
                except Exception:
                    pass
            await asyncio.sleep(0.5)
    tail = "свободных не нашёл 😕" if found == 0 else f"найдено: {found}"
    try:
        await bot.edit_message_text(f"⏹ стоп · проверено {checked} · {tail}", chat_id, status_id, reply_markup=menu())
    except Exception:
        pass

async def watcher():
    async with new_session() as session:
        while True:
            for u in list(watch):
                if await is_free(session, u):
                    watch.discard(u)
                    p, why = rarity(u)
                    await bot.send_message(OWNER, f"🟢 освободился @{u}\n{p}/100 — {tier(p)} · {why}")
                await asyncio.sleep(2)
            await asyncio.sleep(15)

def okq(uid):
    return uid in ALLOWED

@dp.message(Command("start"))
async def start(m: Message):
    if not okq(m.from_user.id):
        await m.answer(random.choice(RUDE)); return
    await m.answer("Выбери режим поиска свободных пятизнаков 👇", reply_markup=menu())

@dp.message(Command("check"))
async def check(m: Message):
    if not okq(m.from_user.id):
        await m.answer(random.choice(RUDE)); return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("формат: /check имя"); return
    name = parts[1].lstrip("@").lower()
    try:
        async with new_session() as s:
            async with s.get(link(name), allow_redirects=True) as r:
                html = await r.text()
        if "tgme_page_title" not in html:
            p, why = rarity(name)
            await m.answer(f"🟢 @{name} свободен · {p}/100 — {tier(p)} · {why}")
        else:
            await m.answer(f"🔴 @{name} занят")
    except Exception as e:
        await m.answer(f"ошибка: {type(e).__name__}: {e}")

@dp.message(Command("watch"))
async def w(m: Message):
    if not okq(m.from_user.id):
        await m.answer(random.choice(RUDE)); return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("формат: /watch имя"); return
    watch.add(parts[1].lstrip("@").lower())
    await m.answer(f"слежу за @{parts[1].lstrip('@')}, скину как освободится")

@dp.callback_query(F.data.in_({"clean", "mixed"}))
async def go(c: CallbackQuery):
    if not okq(c.from_user.id):
        await c.answer(random.choice(RUDE), show_alert=True); return
    if active.get(c.message.chat.id):
        await c.answer("уже идёт"); return
    active[c.message.chat.id] = True
    await c.message.edit_text("🔎 запускаю поиск...", reply_markup=stopkb())
    asyncio.create_task(hunt(c.message.chat.id, c.data == "mixed", c.message.message_id))
    await c.answer("поехали")

@dp.callback_query(F.data == "stop")
async def stop(c: CallbackQuery):
    if not okq(c.from_user.id):
        await c.answer(random.choice(RUDE), show_alert=True); return
    active[c.message.chat.id] = False
    await c.answer("останавливаю")

@dp.message()
async def other(m: Message):
    if not okq(m.from_user.id):
        await m.answer(random.choice(RUDE))

async def main():
    asyncio.create_task(watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
