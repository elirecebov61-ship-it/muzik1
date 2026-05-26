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

print(f"[+] Çiftli sistem aktif! Mavi bot sadece {OWNER_ID} ID'li sahibinden komut bekliyor...")

# --- YENİƏNƏN HİSSƏ: ŞƏXSİ ÇATDA BOTUN İŞLƏMƏSİNİ YOXLAMAQ ---
@bot.on(events.NewMessage(pattern='/start', incoming=True))
async def check_status(event):
    # Eğer /start yazan kişi sen değilsen, bot cevap vermez
    if event.sender_id != OWNER_ID:
        return
    
    # Sadece sana özel cevap
    await event.respond("🟢 Bot aktivdir və əmrinizi gözləyir, sahibim!")

# --- QRUPDA ADAM ƏLAVƏ ETMƏ HİSSƏSİ ---
@bot.on(events.NewMessage(pattern='/c31k'))
async def start_adding(event):
    # KESİN GÜVENLİK KONTROLÜ: Komutu yazan kişinin ID'si senin ID'ne eşit mi?
    if event.sender_id != OWNER_ID:
        return

    await event.respond("🚀 [BOT] Giriş doğrulandı. Gerçek ve aktif insanları ekleme işlemi senin hesabın üzerinden başlatıldı...")
    
    try:
        source = await userbot.get_entity(SOURCE_GROUP)
        target = await userbot.get_entity(TARGET_GROUP)
    except Exception as e:
        await event.respond(f"❌ Gruplar bulunamadı. Hata: {e}")
        return

    participants = []
    
    # Senin hesabınla hedef gruptaki üyeleri çekiyoruz
    async for user in userbot.iter_participants(source):
        if not user.bot and user.username:
            if isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
                participants.append(user)

    await event.respond(f"📊 [BOT] {len(participants)} tane GERÇEK insan tespit edildi. Senin hesabınla ekleme başlıyor...")

    added_count = 0
    for user in participants:
        try:
            # Ekleme işlemini senin hesabın (userbot) tetikliyor
            await userbot(InviteToChannelRequest(target, [user]))
            added_count += 1
            print(f"[+] Eklendi: {user.username}")
            await asyncio.sleep(15) # Ban yememe süresi
            
        except PeerFloodError:
            await event.respond(f"⚠️ Telegram sınırı doldu. Bugünlük bu kadar. Toplam {added_count} kişi eklendi.")
            break
        except UserPrivacyRestrictedError:
            continue
        except UserAlreadyParticipantError:
            continue
        except Exception as e:
            print(f"[-] Hata: {e}")
            await asyncio.sleep(2)
    
    await event.respond(f"🏁 [BOT] İşlem bitti! Toplam {added_count} kişi gruba katıldı.")

# Her iki bota da start verip sistemi açık tutuyoruz
async def main():
    await userbot.start()
    await bot.run_until_disconnected()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

