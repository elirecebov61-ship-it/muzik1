import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import UserStatusOnline, UserStatusRecently, UserStatusLastWeek
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError

# Railway panelinden çekilecek değişkenler
API_ID = int(os.getenv("API_ID", 1234567))
API_HASH = os.getenv("API_HASH", "varsayilan_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "bura_bot_token")
SESSION_STRING = os.getenv("SESSION_STRING", "")

SOURCE_GROUP = os.getenv("SOURCE_GROUP", "cekilecek_grup_username")
TARGET_GROUP = os.getenv("TARGET_GROUP", "eklenecek_grup_username")

# Sadece senin kullanabilmen için sabit Telegram ID'n
OWNER_ID = 8034872992

# 1. Mavi Botu Başlatıyoruz
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# 2. Senin Hesabını (Userbotu) Başlatıyoruz
userbot = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

print(f"[+] Maksimum Güc Rejimi (12s + Avtomatik Skip) aktivdir. Əmr gözlənilir...")

# --- ÖZEL SOHBETTE /START KONTROLÜ ---
@bot.on(events.NewMessage(pattern='/start', incoming=True))
async def check_status(event):
    if event.sender_id != OWNER_ID or not event.is_private:
        return
    await event.respond("🟢 Bot aktif və əmrlərinizi gözləyir!")

# --- GRUPTA SESSİZ ADAM EKLEME BÖLÜMÜ ---
@bot.on(events.NewMessage(pattern='/c31k'))
async def start_adding(event):
    if event.sender_id != OWNER_ID:
        return

    try:
        source = await userbot.get_entity(SOURCE_GROUP)
        target = await userbot.get_entity(TARGET_GROUP)
    except Exception as e:
        print(f"[-] Qruplar tapılmadı: {e}")
        return

    print("[*] Sənin qrupunun mövcud üzvləri yoxlanılır...")
    
    # Sənin qrupundakı mövcud adamların ID-lərini yadda saxlayırıq (Skip etmək üçün)
    existing_users = set()
    async for user in userbot.iter_participants(target):
        existing_users.add(user.id)

    print(f"[+] Sənin qrupunda artıq {len(existing_users)} nəfər var. Dubllar avtomatik skip ediləcək.")
    print("[*] Hədəf qrupdan aktiv insanlar çəkilir...")

    participants = []
    # Hədəf qrupun üzvlərini çəkirik
    async for user in userbot.iter_participants(source):
        if not user.bot and user.username:
            # Əgər adam artıq sənin qrupunda VARSA, siyahıya əlavə etmirik (SKIP)
            if user.id in existing_users:
                continue
            
            # Yalnız son vaxtlar aktiv olan insanları seçirik
            if isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
                participants.append(user)

    print(f"[+] Əlavə edilə biləcek {len(participants)} yeni şəxs tapıldı. Proses başlayır...")

    added_count = 0  # Əlavə olunan adamları saymaq üçün

    # Ekleme döngüsü
    for user in participants:
        try:
            await userbot(InviteToChannelRequest(target, [user]))
            added_count += 1
            print(f"[{added_count}] Əlavə edildi: {user.username}")
            
            # 12 saniyəlik təhlükəsiz interval
            await asyncio.sleep(12) 
            
        except PeerFloodError:
            print(f"[-] Telegram limitinə takıldı (FloodWait). Bu hesab üçün işlem durduruldu. Toplam {added_count} nəfər əlavə edildi.")
            break
        except UserPrivacyRestrictedError:
            continue
        except UserAlreadyParticipantError:
            continue
        except Exception as e:
            print(f"[-] Xəta: {e}")
            await asyncio.sleep(2)

    print(f"[🏁] Döngü dayandı. Bu hesab cəmi {added_count} nəfər əlavə edə bildi.")

async def main():
    await userbot.start()
    await bot.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

