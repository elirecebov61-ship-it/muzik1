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

print(f"[+] Ultra süratli mod (2s) aktif. Komut bekleniyor...")

# --- ÖZEL SOHBETTE /START KONTROLÜ (TÜRKÇE) ---
@bot.on(events.NewMessage(pattern='/start', incoming=True))
async def check_status(event):
    if event.sender_id != OWNER_ID or not event.is_private:
        return
    await event.respond("🟢 Bot aktif ve emirlerinizi bekliyor, sahibim!")

# --- GRUPTA SESSİZ ADAM EKLEME BÖLÜMÜ ---
@bot.on(events.NewMessage(pattern='/c31k'))
async def start_adding(event):
    if event.sender_id != OWNER_ID:
        return

    try:
        source = await userbot.get_entity(SOURCE_GROUP)
        target = await userbot.get_entity(TARGET_GROUP)
    except Exception as e:
        print(f"[-] Gruplar bulunamadı: {e}")
        return

    participants = []
    
    # Üyeleri çekiyoruz
    async for user in userbot.iter_participants(source):
        if not user.bot and user.username:
            if isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
                participants.append(user)

    # Ekleme döngüsü (2 saniye fasile ile ultra süratli)
    for user in participants:
        try:
            await userbot(InviteToChannelRequest(target, [user]))
            print(f"[+] Eklendi: {user.username}")
            
            # Gözleme müddəti 2 saniyəyə endirildi
            await asyncio.sleep(2) 
            
        except PeerFloodError:
            print("[-] Telegram sınırına takıldı (FloodWait). İşlem durduruldu.")
            break
        except UserPrivacyRestrictedError:
            continue
        except UserAlreadyParticipantError:
            continue
        except Exception as e:
            print(f"[-] Hata: {e}")
            await asyncio.sleep(1)

async def main():
    await userbot.start()
    await bot.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

