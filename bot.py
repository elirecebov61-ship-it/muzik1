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
    "BAACAgIAAyEFAATiigGuAAID5WoTF0-6pMl1xNoOTidHo9JYLOHTAAKfmgAC2gKYSDcYz6HiPhumOwQ",
    "BAACAgIAAyEFAATiigGuAAID7GoTF1BA09JEpNPSQfxnvfBdGsrgAAIXmgAC2gKYSAr2PGXbhAHVOwQ",
    "BAACAgIAAyEFAATiigGuAAID8WoTF1CR7uIveWWGuKDWLCG0bT-TAAIdmgAC2gKYSJXDbDkGMPsdOwQ"
]

TASKS = {}

async def worker(app, chat_id):
    delay = 1.0  # 👉 STABLE 60/min

    while True:
        try:
            for m in MEDIA:
                try:
                    await app.bot.send_video(chat_id=chat_id, video=m)
                    await asyncio.sleep(delay)

                except RetryAfter as e:
                    wait = max(30, e.retry_after)
                    print(f"LIMIT → sleeping {wait}s")
                    await asyncio.sleep(wait)
                    delay = min(delay + 0.2, 2.5)

                except TimedOut:
                    await asyncio.sleep(5)
                    delay = min(delay + 0.2, 2.0)

            # stabil saxlamaq
            delay = max(delay, 1.0)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(5)


async def sik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in TASKS:
        TASKS[chat_id] = asyncio.create_task(worker(context.application, chat_id))
        await update.message.reply_text("STARTED (STABLE MODE)")


async def dur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in TASKS:
        TASKS[chat_id].cancel()
        del TASKS[chat_id]
        await update.message.reply_text("STOPPED")


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("sik", sik))
app.add_handler(CommandHandler("dur", dur))

print("BOT RUNNING")
app.run_polling()
