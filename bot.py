import os
import asyncio
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import RetryAfter, TimedOut

TOKEN = os.environ["BOT_TOKEN"]

MEDIA = [
    # file_id-lər
]

TASKS = {}

async def spam(app, chat_id):
    delay = 0.4

    while True:
        try:
            random.shuffle(MEDIA)

            for m in MEDIA:
                try:
                    await app.bot.send_video(chat_id=chat_id, video=m)
                    await asyncio.sleep(delay)

                except RetryAfter as e:
                    # 🔥 minimum 30 saniyə pause
                    wait_time = max(30, e.retry_after)
                    print(f"Paused {wait_time}s")
                    await asyncio.sleep(wait_time)

                    delay = min(delay + 0.2, 2.0)

                except TimedOut:
                    await asyncio.sleep(5)
                    delay = min(delay + 0.2, 2.0)

            delay = max(delay - 0.05, 0.35)

        except Exception:
            await asyncio.sleep(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in TASKS:
        TASKS[chat_id] = asyncio.create_task(
            spam(context.application, chat_id)
        )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in TASKS:
        TASKS[chat_id].cancel()
        del TASKS[chat_id]


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("sik", start))
app.add_handler(CommandHandler("dur", stop))

app.run_polling()
