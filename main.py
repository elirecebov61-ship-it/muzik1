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
SESSION_STRING = os.getenv("SESSION_STRING", "")

SOURCE_GROUP = os.getenv("SOURCE_GROUP", "cekilecek_grup_username")
TARGET_GROUP = os.getenv("TARGET_GROUP", "eklenecek_grup_username")

# Fayl yerinə StringSession istifadə edirik
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

print("[+] Userbot StringSession ile aktif edildi. Grupta /c31k komutu bekleniyor...")

@client.on(events.NewMessage(pattern='/c31k'))
async def start_adding(event):
    if not event.is_private and event.sender_id == (await client.get_me()).id:
        await event.respond("🚀 Gerçek ve aktif insanları ayıklama ve ekleme işlemi başlatıldı...")
        
        try:
            source = await client.get_entity(SOURCE_GROUP)
            target = await client.get_entity(TARGET_GROUP)
        except Exception as e:
            await event.respond(f"❌ Gruplar bulunamadı, lütfen linkleri kontrol edin. Hata: {e}")
            return

        participants = []
        
        async range in [1]: # Blok daxili axışı qorumaq üçün
            async for user in client.iter_participants(source):
                if not user.bot and user.username:
                    if isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
                        participants.append(user)

        await event.respond(f"📊 Hedef gruptan {len(participants)} tane **GERÇEK VE AKTİF** kullanıcı tespit edildi. Ekleme başlıyor...")

        added_count = 0
        for user in participants:
            try:
                await client(InviteToChannelRequest(target, [user]))
                added_count += 1
                print(f"[+] Gerçek kullanıcı eklendi: {user.username} (Toplam: {added_count})")
                await asyncio.sleep(15)
                
            except PeerFloodError:
                await event.respond(f"⚠️ Telegram sınırı doldu (Flood Error). Bugünlük bu kadar. Toplam {added_count} gerçek kişi eklendi.")
                break
            except UserPrivacyRestrictedError:
                continue
            except UserAlreadyParticipantError:
                continue
            except Exception as e:
                print(f"[-] Hata oluştu ({user.username}): {e}")
                await asyncio.sleep(2)
        
        await event.respond(f"🏁 İşlem tamamlandı. Toplam {added_count} gerçek insan gruba katıldı.")

if __name__ == "__main__":
    client.start()
    client.run_until_disconnected()

