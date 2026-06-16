import asyncio
import random
import string
from collections import Counter
from aiohttp import ClientSession, TCPConnector, ClientTimeout
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8931382600:AAEOWYJGOC9mtYoIssNOX-AyV49fg6TZm6Q"
OWNER = 8048285990
ALLOWED = {OWNER, 7209594427}
RUDE = ["иди нахуй", "не для тебя бот, вали", "тебя сюда не звали", "доступа нет, соси"]
UA = {"User-Agent": "Mozilla/5.0"}
MIN_SCORE = 60

HOST = "t.me"
FRAG_HOST = "fragment.com"
WORDS_HOST = "raw.githubusercontent.com"
WORDS_PATH = "/dwyl/english-words/master/words_alpha.txt"

bot = Bot(TOKEN)
dp = Dispatcher()
active = {}
watch = set()
V = set("aeiou")

WORDS = {"alpha","bravo","delta","ghost","north","raven","storm","vodka","laser","ninja","tiger","onion","mango","blaze","frost","crown","royal","queen","kings","piano","ocean","light","prime","viper","lemon","amber","ivory","pearl","noble","eagle","brave","pizza","cocic","money","power","metal","stone","flame","shark","wolfs","skull","cyber","pixel"}

def link(u):
    return "https://" + HOST + "/" + u

def frag(u):
    return "https://" + FRAG_HOST + "/username/" + u

def new_session():
    return ClientSession(headers=UA, connector=TCPConnector(ssl=False), timeout=ClientTimeout(total=15))

async def load_words():
    global WORDS
    try:
        async with new_session() as s:
            async with s.get("https://" + WORDS_HOST + WORDS_PATH) as r:
                txt = await r.text()
        w = {x.strip().lower() for x in txt.split() if len(x.strip()) == 5 and x.strip().isalpha()}
        if len(w) > 1000:
            WORDS = w
    except Exception:
        pass

def make(use_digits):
    head = random.choice(string.ascii_lowercase)
    pool = string.ascii_lowercase + (string.digits if use_digits else "")
    return head + "".join(random.choice(pool) for _ in range(4))

def rarity(u):
    digits = sum(c.isdigit() for c in u)
    uniq = len(set(u))
    counts = sorted(Counter(u).values(), reverse=True)
    palin = u == u[::-1]
    seq = digits == 0 and len(u) == 5 and (all(ord(u[i]) - ord(u[i - 1]) == 1 for i in range(1, 5)) or all(ord(u[i - 1]) - ord(u[i]) == 1 for i in range(1, 5)))
    if uniq == 1:
        return 100, "👑 один символ ×5"
    if seq:
        return 96, "📈 последовательность"
    if digits == 0 and u in WORDS:
        return (95 if palin else 90), "💠 слово из словаря"
    if digits:
        return max(1, 26 - digits * 6), "🗑 с цифрами"
    s = 32
    why = "буквенный"
    if counts[0] >= 4:
        s = 84; why = "🔥 4 одинаковых"
    elif uniq == 2:
        s = 76; why = "🔁 всего 2 символа"
    elif palin:
        s = 72; why = "↔️ палиндром"
    elif uniq == 3:
        s = 56; why = "повторы"
    flow = sum(1 for i in range(1, 5) if (u[i] in V) != (u[i - 1] in V))
    if flow >= 4 and s < 65:
        s += 18; why = "произносимый"
    run = best = 0
    for c in u:
        run = run + 1 if c not in V else 0
        best = max(best, run)
    if best >= 4:
        s -= 12
    return max(1, min(100, s)), why

def tier(p):
    if p >= 90:
        return "🏆 ЛЕГЕНДА"
    if p >= 75:
        return "🔥 топ"
    if p >= 60:
        return "💎 редкий"
    if p >= 45:
        return "✨ норм"
    return "обычный"

def menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Только буквы", callback_data="clean")],
        [InlineKeyboardButton(text="🔢 Буквы + цифры", callback_data="mixed")],
        [InlineKeyboardButton(text="📖 По словам", callback_data="words")],
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

async def is_nft(session, u):
    try:
        async with session.get(frag(u), allow_redirects=True) as r:
            html = await r.text()
    except Exception:
        return None
    low = html.lower()
    if "<title>" not in low:
        return False
    title = low.split("<title>", 1)[1].split("</title>", 1)[0].strip()
    return title.startswith(u.lower() + " ")

async def hunt(chat_id, mode, status_id):
    checked = found = nftc = fails = 0
    seen = set()
    it = None
    if mode == "words":
        pool = list(WORDS)
        random.shuffle(pool)
        it = iter(pool)
    async with new_session() as session:
        while active.get(chat_id):
            try:
                if mode == "words":
                    u = next(it, None)
                    if u is None:
                        break
                else:
                    u = make(mode == "mixed")
                    if u in seen:
                        continue
                    seen.add(u)
                res = await is_free(session, u)
                checked += 1
                if res is None:
                    fails += 1
                elif res:
                    p, why = rarity(u)
                    if p >= MIN_SCORE:
                        nft = await is_nft(session, u)
                        if nft is True:
                            nftc += 1
                            await bot.send_message(chat_id, f"💜 @{u} — NFT (Fragment, платно)\n{p}/100 · {why}")
                        else:
                            found += 1
                            await bot.send_message(chat_id, f"🏆 @{u} свободен\n{p}/100 — {tier(p)} · {why}")
                if checked == 1 or checked % 5 == 0:
                    try:
                        await bot.edit_message_text(f"🔎 проверено: {checked} · 🏆 {found} · 💜 {nftc} · ошибок: {fails}", chat_id, status_id, reply_markup=stopkb())
                    except Exception:
                        pass
                await asyncio.sleep(0.6)
            except Exception:
                fails += 1
                await asyncio.sleep(0.6)
    active[chat_id] = False
    try:
        await bot.edit_message_text(f"⏹ стоп · проверено {checked} · 🏆 {found} · 💜 {nftc}", chat_id, status_id, reply_markup=menu())
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
    await m.answer(f"Свободные пятизнаки. Шлю только рейтинг ≥ {MIN_SCORE}. Выбери режим 👇", reply_markup=menu())

@dp.message(Command("check"))
async def check(m: Message):
    if not okq(m.from_user.id):
        await m.answer(random.choice(RUDE)); return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("формат: /check имя"); return
    name = parts[1].lstrip("@").lower()
    async with new_session() as s:
        free = await is_free(s, name)
        if free is None:
            await m.answer("не смог проверить"); return
        if not free:
            await m.answer(f"🔴 @{name} занят"); return
        nft = await is_nft(s, name)
    p, why = rarity(name)
    if nft:
        await m.answer(f"💜 @{name} — NFT на Fragment (только платно)\n{p}/100 · {why}")
    else:
        await m.answer(f"🏆 @{name} свободен, можно занять\n{p}/100 — {tier(p)} · {why}")

@dp.message(Command("watch"))
async def w(m: Message):
    if not okq(m.from_user.id):
        await m.answer(random.choice(RUDE)); return
    parts = m.text.split()
    if len(parts) < 2:
        await m.answer("формат: /watch имя"); return
    watch.add(parts[1].lstrip("@").lower())
    await m.answer(f"слежу за @{parts[1].lstrip('@')}, скину как освободится")

@dp.callback_query(F.data.in_({"clean", "mixed", "words"}))
async def go(c: CallbackQuery):
    if not okq(c.from_user.id):
        await c.answer(random.choice(RUDE), show_alert=True); return
    if active.get(c.message.chat.id):
        await c.answer("уже идёт"); return
    active[c.message.chat.id] = True
    await c.message.edit_text("🔎 запускаю поиск...", reply_markup=stopkb())
    asyncio.create_task(hunt(c.message.chat.id, c.data, c.message.message_id))
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
    await load_words()
    asyncio.create_task(watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
