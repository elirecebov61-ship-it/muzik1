import os
import asyncio
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import RetryAfter, TimedOut

TOKEN = os.environ["BOT_TOKEN"]

MEDIA = [
    "BAACAgIAAyEFAATiigGuAAID3moTF082JdD2T_A9G7dQMc5ZYKQvAAKbmgAC2gKYSFxXymQ1r-qVOwQ",
    "AgACAgIAAyEFAATiigGuAAID32oTF0_1bM6-6n30wfMPxP9LVmLiAAJ2G2sb2gKYSFWxqKC4ryL0AQADAgADeAADOwQ",
    "AgACAgIAAyEFAATiigGuAAID4GoTF0_JRBHzMCIjhgsoQw9EL6cHAAJ3G2sb2gKYSPm2omeScseCAQADAgADeAADOwQ",
    "AgACAgIAAyEFAATiigGuAAID4WoTF0-XfAJZFG8oYpJ8Bwb8gbCKAAJ4G2sb2gKYSM_bjANR52g7AQADAgADeAADOwQ",
    "BAACAgIAAyEFAATiigGuAAID4moTF09jDXaBKctqwWQRyUGr_AmmAAKcmgAC2gKYSMjh08FXMwABETsE",
    "BAACAgIAAyEFAATiigGuAAID42oTF0_dxDt-VanFeXeyD2Z-kkT1AAKdmgAC2gKYSHIDdx7XE39IOwQ",
    "BAACAgIAAyEFAATiigGuAAID5GoTF0-WMl2ZkT71zFvqqIywEFMmAAKemgAC2gKYSJjuS6OzyqkgOwQ",
    "BAACAgIAAyEFAATiigGuAAID5WoTF0-6pMl1xNoOTidHo9JYLOHTAAKfmgAC2gKYSDcYz6HiPhumOwQ",
    "BAACAgIAAyEFAATiigGuAAID5moTF0-Qq-L0-xIbJRBtMeEu-poDAAKgmgAC2gKYSLi2TETIwyW3OwQ",
    "BAACAgIAAyEFAATiigGuAAID52oTF0-P9JhTeCGtjz2xziQXtwRYAAKhmgAC2gKYSLwp72WQq8SMOwQ",
    "BAACAgIAAyEFAATiigGuAAID7GoTF1BA09JEpNPSQfxnvfBdGsrgAAIXmgAC2gKYSAr2PGXbhAHVOwQ",
    "BAACAgIAAyEFAATiigGuAAID7WoTF1B8HtQrJc4jThfHnNFD1IC3AAIZmgAC2gKYSLmDplDICzq6OwQ",
    "BAACAgIAAyEFAATiigGuAAID7moTF1BcV1EH2k_mCAWU8vDRuW_HAAIYmgAC2gKYSF6vhjNu6W0ROwQ",
    "BAACAgIAAyEFAATiigGuAAID72oTF1BRzbNz9fmaGBSZfDowyRKdAAIamgAC2gKYSCAXMikuHhRjOwQ",
    "BAACAgIAAyEFAATiigGuAAID8GoTF1BTmAKpIWLhuvmIM9FbnS72AAIbmgAC2gKYSIZ7r3wAAe0X3DsE",
    "BAACAgIAAyEFAATiigGuAAID8WoTF1CR7uIveWWGuKDWLCG0bT-TAAIdmgAC2gKYSJXDbDkGMPsdOwQ",
    "BAACAgIAAyEFAATiigGuAAID8moTF1CQxx5v3hA61GeamL0O0aqkAAIemgAC2gKYSOG9qt1e47OxOwQ",
    "BAACAgIAAyEFAATiigGuAAID82oTF1DWag5Y9ux0AAHrA0In3x-LHgACHJoAAtoCmEjMkDYxjg53CDsE",
    "BAACAgIAAyEFAATiigGuAAID9WoTF1D4yPEasCTEJQABMBvkq7C-QAACH5oAAtoCmEj0gMrEVUEgWDsE"
]

TASKS = {}

async def spam(app, chat_id):
    delay = 0.4

    while True:
        try:
            random.shuffle(MEDIA)

            for m in MEDIA:
                try:
                    if m.startswith("BAACAg"):
                        await app.bot.send_video(chat_id=chat_id, video=m)
                    else:
                        await app.bot.send_photo(chat_id=chat_id, photo=m)

                    await asyncio.sleep(delay)

                except RetryAfter as e:
                    wait = max(30, e.retry_after)
                    print(f"Cooldown {wait}s")
                    await asyncio.sleep(wait)
                    delay = min(delay + 0.2, 2.0)

                except TimedOut:
                    await asyncio.sleep(5)
                    delay = min(delay + 0.2, 2.0)

            delay = max(delay - 0.05, 0.35)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(5)


async def sik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in TASKS:
        TASKS[chat_id] = asyncio.create_task(
            spam(context.application, chat_id)
        )
        await update.message.reply_text("STARTED")


async def dur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in TASKS:
        TASKS[chat_id].cancel()
        del TASKS[chat_id]
        await update.message.reply_text("STOPPED")


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("sik", sik))
app.add_handler(CommandHandler("dur", dur))

print("BOT RUNNING...")
app.run_polling()
