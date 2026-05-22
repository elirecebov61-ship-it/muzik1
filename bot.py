import asyncio
import os
import logging
from collections import deque

from pytgcalls import PyTgCalls, idle
from pytgcalls.types import MediaStream, StreamEnded

from hydrogram import Client, filters
from hydrogram.types import Message

import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID         = int(os.environ["API_ID"])
API_HASH       = os.environ["API_HASH"]
STRING_SESSION = os.environ["STRING_SESSION"]
BOT_TOKEN      = os.environ["BOT_TOKEN"]

DEV = "\n\n🛠 Dev. @emektas"

user = Client("music_user", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
bot  = Client("music_bot",  api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call = PyTgCalls(user)

queues:  dict[int, deque] = {}
playing: dict[int, dict]  = {}

def get_queue(chat_id: int) -> deque:
    if chat_id not in queues:
        queues[chat_id] = deque()
    return queues[chat_id]

def fetch_audio(query: str) -> tuple[str, str]:
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info["title"], info["url"]

async def play_next(chat_id: int):
    q = get_queue(chat_id)
    if not q:
        playing.pop(chat_id, None)
        try:
            await call.leave_group_call(chat_id)
        except Exception:
            pass
        await bot.send_message(chat_id, "✅ Sıra bitti, sesli sohbetten ayrıldım." + DEV)
        return

    title, url = q.popleft()
    playing[chat_id] = {"title": title, "url": url}

    try:
        await call.play(chat_id, MediaStream(url))
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Hata: {e}" + DEV)
        return

    await bot.send_message(chat_id, f"🎵 Şu an çalınıyor: **{title}**" + DEV)

@call.on_update(filters.stream_ended)
async def on_stream_end(client, update: StreamEnded):
    await play_next(update.chat_id)

@bot.on_message(filters.command("play") & filters.group)
async def cmd_play(client, message: Message):
    chat_id = message.chat.id

    if len(message.command) < 2:
        await message.reply("❗ Kullanım: `/play <şarkı adı veya link>`" + DEV)
        return

    query = " ".join(message.command[1:])
    msg   = await message.reply("🔍 Aranıyor...")

    try:
        loop       = asyncio.get_event_loop()
        title, url = await loop.run_in_executor(None, fetch_audio, query)
    except Exception as e:
        await msg.edit(f"❌ Bulunamadı: {e}" + DEV)
        return

    q = get_queue(chat_id)

    if chat_id in playing:
        q.append((title, url))
        await msg.edit(f"➕ Sıraya eklendi: **{title}**\n📋 Sırada: {len(q)} şarkı" + DEV)
        return

    playing[chat_id] = {"title": title, "url": url}
    await msg.edit(f"🎵 Yükleniyor: **{title}**")

    try:
        await call.play(chat_id, MediaStream(url))
        await msg.edit(f"▶️ Çalınıyor: **{title}**" + DEV)
    except Exception as e:
        playing.pop(chat_id, None)
        await msg.edit(f"❌ Hata: {e}" + DEV)

@bot.on_message(filters.command("skip") & filters.group)
async def cmd_skip(client, message: Message):
    chat_id = message.chat.id
    if chat_id not in playing:
        await message.reply("❌ Şu an hiçbir şey çalmıyor." + DEV)
        return
    await message.reply("⏭ Geçildi." + DEV)
    await play_next(chat_id)

@bot.on_message(filters.command("stop") & filters.group)
async def cmd_stop(client, message: Message):
    chat_id = message.chat.id
    queues[chat_id] = deque()
    playing.pop(chat_id, None)
    try:
        await call.leave_group_call(chat_id)
    except Exception:
        pass
    await message.reply("⏹ Durduruldu, sıra temizlendi." + DEV)

@bot.on_message(filters.command("pause") & filters.group)
async def cmd_pause(client, message: Message):
    chat_id = message.chat.id
    try:
        await call.pause(chat_id)
        await message.reply("⏸ Duraklatıldı." + DEV)
    except Exception as e:
        await message.reply(f"❌ Hata: {e}" + DEV)

@bot.on_message(filters.command("resume") & filters.group)
async def cmd_resume(client, message: Message):
    chat_id = message.chat.id
    try:
        await call.resume(chat_id)
        await message.reply("▶️ Devam ettirildi." + DEV)
    except Exception as e:
        await message.reply(f"❌ Hata: {e}" + DEV)

@bot.on_message(filters.command("queue") & filters.group)
async def cmd_queue(client, message: Message):
    chat_id = message.chat.id
    q = get_queue(chat_id)

    now = playing.get(chat_id)
    if not now and not q:
        await message.reply("📋 Sıra boş." + DEV)
        return

    text = "🎵 **Müzik Sırası**\n\n"
    if now:
        text += f"▶️ **Şu an:** {now['title']}\n\n"
    if q:
        text += "📋 **Sırada:**\n"
        for i, (title, _) in enumerate(q, 1):
            text += f"{i}. {title}\n"
    await message.reply(text + DEV)

@bot.on_message(filters.command(["help", "start"]))
async def cmd_help(client, message: Message):
    await message.reply(
        "🎵 **Müzik Bot Komutları**\n\n"
        "▶️ `/play <isim veya link>` — Şarkı çal\n"
        "⏭ `/skip` — Sıradakini geç\n"
        "⏹ `/stop` — Durdur ve sırayı temizle\n"
        "⏸ `/pause` — Duraklat\n"
        "▶️ `/resume` — Devam ettir\n"
        "📋 `/queue` — Sırayı göster\n" + DEV
    )

async def main():
    await user.start()
    await bot.start()
    await call.start()
    print("Müzik botu başladı!")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
