import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import UserStatusOnline, UserStatusRecently, UserStatusLastWeek
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, UserAlreadyParticipantError

# Railway panelinden çekilecek değişkenler
API_ID = int(os.getenv("API_ID", 1234567))
API_HASH = os.getenv("API_HASH", "varsayilan_hash")
SESSION_NAME = "userbot_session"

SOURCE_GROUP = os.getenv("SOURCE_GROUP", "cekilecek_grup_username")
TARGET_GROUP = os.getenv("TARGET_GROUP", "eklenecek_grup_username")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

print("[+] Userbot aktif. Grupta /c31k komutu bekleniyor...")

@client.on(events.NewMessage(pattern='/c31k'))
async def start_adding(event):
    # Komutu sadece bot sahibinin çalıştırmasını sağlayan kontrol
    if not event.is_private and event.sender_id == (await client.get_me()).id:
        await event.respond("🚀 Gerçek ve aktif insanları ayıklama ve ekleme işlemi başlatıldı...")
        
        try:
            source = await client.get_entity(SOURCE_GROUP)
            target = await client.get_entity(TARGET_GROUP)
        except Exception as e:
            await event.respond(f"❌ Gruplar bulunamadı, lütfen linkleri kontrol edin. Hata: {e}")
            return

        participants = []
        
        # Gruptaki üyeleri çekiyoruz
        async for user in client.iter_participants(source):
            # 1. Hesap bot olmamalı
            # 2. Mutlaka bir kullanıcı adı (username) olmalı (SMM botlarında genelde olmaz)
            if not user.bot and user.username:
                
                # 3. AKTİFLİK FİLTRESİ (Gerçek insanları tespit eder)
                # Durumu: Çevrimiçi, Yakınlarda (Son 1-2 gün) veya Bu Hafta girmiş olanlar
                if isinstance(user.status, (UserStatusOnline, UserStatusRecently, UserStatusLastWeek)):
                    participants.append(user)

        await event.respond(f"📊 Hedef gruptan {len(participants)} tane **GERÇEK VE AKTİF** kullanıcı tespit edildi. Ekleme başlıyor...")

        added_count = 0
        for user in participants:
            try:
                await client(InviteToChannelRequest(target, [user]))
                added_count += 1
                print(f"[+] Gerçek kullanıcı eklendi: {user.username} (Toplam: {added_count})")
                
                # Telegram filtrelerine takılmamak (ban yememek) için bekleme süresi
                await asyncio.sleep(15)
                
            except PeerFloodError:
                # Günlük sınır dolduğunda Telegram bu hatayı verir ve döngü durur
                await event.respond(f"⚠️ Telegram sınırı doldu (Flood Error). Bugünlük bu kadar. Toplam {added_count} gerçek kişi eklendi.")
                break
            except UserPrivacyRestrictedError:
                # Kullanıcı grup davetlerini gizlediyse sıradakine geçer
                continue
            except UserAlreadyParticipantError:
                # Kullanıcı zaten grupta varsa sıradakine geçer
                continue
            except Exception as e:
                print(f"[-] Hata oluştu ({user.username}): {e}")
                await asyncio.sleep(2)
        
        await event.respond(f"🏁 İşlem tamamlandı. Toplam {added_count} gerçek insan gruba katıldı.")

if __name__ == "__main__":
    client.start()
    client.run_until_disconnected()
