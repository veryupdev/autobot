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
    codes = [ord(c) for c in u]
    asc = all(codes[i] - codes[i - 1] == 1 for i in range(1, 5))
    desc = all(codes[i - 1] - codes[i] == 1 for i in range(1, 5))
    if uniq == 1:
        return 100, "👑 один символ ×5"
    if digits == 0 and (asc or desc):
        return 97, "📈 алфавитная последовательность"
    if digits == 0 and u in WORDS:
        return (96 if palin else 92), "💠 настоящее слово"
    if digits == 0:
        if uniq == 2 and u[0] == u[2] == u[4] and u[1] == u[3]:
            return 90, "🔷 паттерн ABABA"
        if counts[0] == 4:
            return 88, "🔥 четыре одинаковых"
        if uniq == 2:
            return 84, "🔁 всего две буквы"
        if palin:
            return 80, "↔️ палиндром"
        if counts[0] == 3:
            return 74, "♟ тройной повтор"
        base = 40
        why = "буквенный"
        if u[0] == u[4]:
            base = 58; why = "🪞 одинаковые края"
        flow = sum(1 for i in range(1, 5) if (u[i] in V) != (u[i - 1] in V))
        if flow >= 4:
            base += 16; why = "🗣 произносимый"
        if any(u[i] == u[i + 1] for i in range(4)):
            base += 7; why = "сдвоенная буква"
        if uniq == 3:
            base += 8
        run = best = 0
        for c in u:
            run = run + 1 if c not in V else 0
            best = max(best, run)
        if best >= 4:
            base -= 14
        return max(1, min(89, base)), why
    base = 30 - digits * 6
    if not u[0].isdigit():
        base += 3
    return max(1, base), "🗗 с цифрами"

def tier(p):
    if p >= 90:
        return "ЛЕГЕНДА"
    if p >= 75:
        return "ТОП"
    if p >= 60:
        return "редкий"
    if p >= 45:
        return "норм"
    return "обычный"

def card(u, p, why, nft=False):
    url = HOST + "/" + u
    tag = "💜 NFT (Fragment, платно)\n\n" if nft else ""
    if p >= 90:
        return (tag +
                "🏆━━━━━━━━━━━━🏆\n"
                "      <b>✨ ЛЕГЕНДА ✨</b>\n"
                "🏆━━━━━━━━━━━━🏆\n\n"
                f"<b>@{u}</b>\n"
                f"💯 <b>{p}/100</b> · {why}\n"
                f"🔗 {url}")
    if p >= 75:
        return (tag +
                "🔥🔥🔥 <b>ТОП</b> 🔥🔥🔥\n\n"
                f"<b>@{u}</b>\n"
                f"⭐ <b>{p}/100</b> · {why}\n"
                f"🔗 {url}")
    return (tag +
            f"💎 <b>@{u}</b> — редкий\n"
            f"{p}/100 · {why}\n"
            f"🔗 {url}")

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

async def set_status(chat_id, status_id, text, kb):
    try:
        await bot.edit_message_text(text=text, chat_id=chat_id, message_id=status_id, reply_markup=kb)
    except Exception:
        pass

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
                            await bot.send_message(chat_id, card(u, p, why, nft=True), parse_mode="HTML")
                        else:
                            found += 1
                            await bot.send_message(chat_id, card(u, p, why), parse_mode="HTML")
                if checked == 1 or checked % 4 == 0:
                    await set_status(chat_id, status_id, f"🔎 проверено: {checked} · 🏆 {found} · 💜 {nftc} · ошибок: {fails}", stopkb())
                await asyncio.sleep(0.6)
            except Exception:
                fails += 1
                await asyncio.sleep(0.6)
    active[chat_id] = False
    await set_status(chat_id, status_id, f"⏹ стоп · проверено {checked} · 🏆 {found} · 💜 {nftc}", menu())

async def watcher():
    async with new_session() as session:
        while True:
            for u in list(watch):
                if await is_free(session, u):
                    watch.discard(u)
                    p, why = rarity(u)
                    await bot.send_message(OWNER, "🟢 ОСВОБОДИЛСЯ\n\n" + card(u, p, why), parse_mode="HTML")
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
    await m.answer(card(name, p, why, nft=bool(nft)), parse_mode="HTML")

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
