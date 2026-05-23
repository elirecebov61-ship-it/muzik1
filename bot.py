import logging
import os
import time
import asyncio
from collections import defaultdict
from contextlib import contextmanager
from psycopg2 import pool
from telegram import Update, BotCommand, ChatPermissions
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN        = os.environ["BOT_TOKEN"]
FOUNDER_ID   = 8034872992
DATABASE_URL = os.environ["DATABASE_URL"]

DEV = "\n\n🛠 Dev. @emektas"

FLOOD_LIMIT   = 10
FLOOD_SECONDS = 3

flood_tracker: dict = defaultdict(lambda: defaultdict(list))

cache_exempt = set()
cache_pro    = set()
cache_ready  = False

db_pool = None

def get_pool():
    global db_pool
    if db_pool is None:
        for attempt in range(10):
            try:
                db_pool = pool.ThreadedConnectionPool(2, 10, DATABASE_URL)
                return db_pool
            except Exception as e:
                print(f"Pool hatası ({attempt+1}/10): {e}")
                time.sleep(3)
        raise Exception("DB pool oluşturulamadı!")
    return db_pool

@contextmanager
def get_conn():
    p = get_pool()
    conn = p.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pro_users (
                    chat_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name    TEXT,
                    PRIMARY KEY (chat_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS exempt_users (
                    chat_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name    TEXT,
                    PRIMARY KEY (chat_id, user_id)
                );
            """)

def load_cache():
    global cache_exempt, cache_pro, cache_ready
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT chat_id, user_id FROM exempt_users")
            cache_exempt = {(r[0], r[1]) for r in cur.fetchall()}

            cur.execute("SELECT chat_id, user_id FROM pro_users")
            cache_pro = {(r[0], r[1]) for r in cur.fetchall()}

    cache_ready = True
    print(f"Cache yüklendi: {len(cache_exempt)} istisna, {len(cache_pro)} pro")

def c_is_exempt(chat_id, user_id):
    return (str(chat_id), str(user_id)) in cache_exempt

def c_is_pro(chat_id, user_id):
    return (str(chat_id), str(user_id)) in cache_pro

def get_name(user) -> str:
    name = user.first_name or ""
    if user.last_name:
        name += " " + user.last_name
    return name.strip() or user.username or str(user.id)

def ensure_group(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type == "private":
            await update.message.reply_text("🚫 Bu komut sadece gruplarda çalışır!" + DEV)
            return
        return await func(update, ctx)
    return wrapper

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Merhaba!\n\n"
        "🔇 Ben bir *flood koruma botuyum*.\n\n"
        "📌 Komutlar:\n"
        "• `/exempt` — Kişiyi istisnaya ekle\n"
        "• `/unexempt` — Kişiyi istisnadan çıkar\n"
        "• `/pro` — Yetki ver\n"
        "• `/unpro` — Yetkiyi al\n"
        "• `/unmute` — Kişinin mutesini aç\n"
        "• `/ayar <limit> <saniye>` — Flood limitini ayarla\n\n"
        f"⚙️ Şu an: *{FLOOD_SECONDS}* saniyede *{FLOOD_LIMIT}* mesaj → daimi mute" + DEV,
        parse_mode="Markdown"
    )

@ensure_group
async def cmd_pro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if update.effective_user.id != FOUNDER_ID:
        await msg.reply_text("🚫 Yetkin yok!" + DEV)
        return
    if not msg.reply_to_message:
        await msg.reply_text("❗ Birinin mesajına yanıt verip `/pro` yaz." + DEV, parse_mode="Markdown")
        return
    target = msg.reply_to_message.from_user
    cid, tid = str(update.effective_chat.id), str(target.id)
    name = get_name(target)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO pro_users (chat_id, user_id, name) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (cid, tid, name)
            )
    cache_pro.add((cid, tid))
    await msg.reply_text(f"✅ *{name}* yetki aldı!" + DEV, parse_mode="Markdown")

@ensure_group
async def cmd_unpro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if update.effective_user.id != FOUNDER_ID:
        await msg.reply_text("🚫 Yetkin yok!" + DEV)
        return
    if not msg.reply_to_message:
        await msg.reply_text("❗ Birinin mesajına yanıt verip `/unpro` yaz." + DEV, parse_mode="Markdown")
        return
    target = msg.reply_to_message.from_user
    cid, tid = str(update.effective_chat.id), str(target.id)
    name = get_name(target)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM pro_users WHERE chat_id=%s AND user_id=%s", (cid, tid))
    cache_pro.discard((cid, tid))
    await msg.reply_text(f"❌ *{name}* yetkisi alındı." + DEV, parse_mode="Markdown")

@ensure_group
async def cmd_exempt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = update.effective_user.id
    cid = str(update.effective_chat.id)
    if uid != FOUNDER_ID and not c_is_pro(cid, uid):
        await msg.reply_text("🚫 Yetkin yok!" + DEV)
        return
    if not msg.reply_to_message:
        await msg.reply_text("❗ Birinin mesajına yanıt verip `/exempt` yaz." + DEV, parse_mode="Markdown")
        return
    target = msg.reply_to_message.from_user
    tid = str(target.id)
    name = get_name(target)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO exempt_users (chat_id, user_id, name) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (cid, tid, name)
            )
    cache_exempt.add((cid, tid))
    await msg.reply_text(f"✅ *{name}* istisna listesine eklendi!" + DEV, parse_mode="Markdown")

@ensure_group
async def cmd_unexempt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = update.effective_user.id
    cid = str(update.effective_chat.id)
    if uid != FOUNDER_ID and not c_is_pro(cid, uid):
        await msg.reply_text("🚫 Yetkin yok!" + DEV)
        return
    if not msg.reply_to_message:
        await msg.reply_text("❗ Birinin mesajına yanıt verip `/unexempt` yaz." + DEV, parse_mode="Markdown")
        return
    target = msg.reply_to_message.from_user
    tid = str(target.id)
    name = get_name(target)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM exempt_users WHERE chat_id=%s AND user_id=%s", (cid, tid))
    cache_exempt.discard((cid, tid))
    await msg.reply_text(f"❌ *{name}* istisna listesinden çıkarıldı." + DEV, parse_mode="Markdown")

@ensure_group
async def cmd_unmute(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = update.effective_user.id
    cid = str(update.effective_chat.id)
    if uid != FOUNDER_ID and not c_is_pro(cid, uid):
        await msg.reply_text("🚫 Yetkin yok!" + DEV)
        return
    if not msg.reply_to_message:
        await msg.reply_text("❗ Birinin mesajına yanıt verip `/unmute` yaz." + DEV, parse_mode="Markdown")
        return
    target = msg.reply_to_message.from_user
    tid = str(target.id)
    name = get_name(target)
    try:
        await ctx.bot.restrict_chat_member(
            chat_id=int(cid),
            user_id=int(tid),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await msg.reply_text(f"✅ *{name}* mutesi açıldı!" + DEV, parse_mode="Markdown")
    except Exception as e:
        await msg.reply_text(f"❌ Hata: {e}" + DEV)

@ensure_group
async def cmd_ayar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = update.effective_user.id
    cid = str(update.effective_chat.id)
    if uid != FOUNDER_ID and not c_is_pro(cid, uid):
        await msg.reply_text("🚫 Yetkin yok!" + DEV)
        return
    if not ctx.args:
        await msg.reply_text(
            f"⚙️ Şu an ayarlar:\n"
            f"• Flood limit: *{FLOOD_LIMIT}* mesaj\n"
            f"• Süre: *{FLOOD_SECONDS}* saniye\n\n"
            f"Kullanım: `/ayar <limit> <saniye>`\n"
            f"Örnek: `/ayar 10 3`" + DEV,
            parse_mode="Markdown"
        )
        return
    try:
        global FLOOD_LIMIT, FLOOD_SECONDS
        FLOOD_LIMIT   = int(ctx.args[0])
        FLOOD_SECONDS = int(ctx.args[1]) if len(ctx.args) > 1 else FLOOD_SECONDS
        await msg.reply_text(
            f"✅ Ayarlar güncellendi!\n"
            f"• Flood limit: *{FLOOD_LIMIT}* mesaj\n"
            f"• Süre: *{FLOOD_SECONDS}* saniye" + DEV,
            parse_mode="Markdown"
        )
    except Exception:
        await msg.reply_text("❗ Kullanım: `/ayar <limit> <saniye>`" + DEV, parse_mode="Markdown")

async def flood_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.effective_chat.type == "private":
        return
    if not cache_ready:
        return

    cid = str(update.effective_chat.id)
    uid = str(update.effective_user.id)
    user = update.effective_user

    if update.effective_user.id == FOUNDER_ID:
        return
    if c_is_exempt(cid, uid) or c_is_pro(cid, uid):
        return

    now = time.time()
    flood_tracker[cid][uid] = [t for t in flood_tracker[cid][uid] if now - t < FLOOD_SECONDS]
    flood_tracker[cid][uid].append(now)

    if len(flood_tracker[cid][uid]) >= FLOOD_LIMIT:
        flood_tracker[cid][uid] = []
        name = get_name(user)
        try:
            await ctx.bot.restrict_chat_member(
                chat_id=int(cid),
                user_id=int(uid),
                permissions=ChatPermissions(can_send_messages=False)
            )
            await update.message.reply_text(
                f"🔇 *{name}* flood yaptığı için susturuldu!\n"
                f"Yetkili biri `/unmute` ile açabilir." + DEV,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Mute xətası: {e}")

async def post_init(app: Application):
    init_db()
    load_cache()
    await app.bot.set_my_commands([
        BotCommand("start",    "Botu başlat"),
        BotCommand("exempt",   "Kişiyi istisnaya ekle"),
        BotCommand("unexempt", "Kişiyi istisnadan çıkar"),
        BotCommand("unmute",   "Kişinin mutesini aç"),
        BotCommand("pro",      "Yetki ver"),
        BotCommand("unpro",    "Yetkiyi al"),
        BotCommand("ayar",     "Flood ayarlarını düzenle"),
    ])

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("pro",      cmd_pro))
    app.add_handler(CommandHandler("unpro",    cmd_unpro))
    app.add_handler(CommandHandler("exempt",   cmd_exempt))
    app.add_handler(CommandHandler("unexempt", cmd_unexempt))
    app.add_handler(CommandHandler("unmute",   cmd_unmute))
    app.add_handler(CommandHandler("ayar",     cmd_ayar))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, flood_check))

    print("Bot başladı...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
