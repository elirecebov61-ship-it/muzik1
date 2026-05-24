import os
import asyncio
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import RetryAfter, TimedOut

TOKEN = os.environ["BOT_TOKEN"]

VIDEOS = [
    "file_id_1", "file_id_2", "file_id_3",
    "file_id_4", "file_id_5", "file_id_6",
    "file_id_7", "file_id_8", "file_id_9"
]

tasks = {}

async def spam(app, chat_id):
    delay = 0.5  # stabil start

    while True:
        try:
            random.shuffle(VIDEOS)

            for v in VIDEOS:
                try:
                    await app.bot.send_video(chat_id=chat_id, video=v)
                    await asyncio.sleep(delay)

                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)

                    # avtomatik yavaşıma
                    delay = min(delay + 0.1, 1.5)

                except TimedOut:
                    await asyncio.sleep(1)

                    delay = min(delay + 0.1, 1.5)

            # stabilizasiya (yenidən sürətləndir)
            delay = max(delay - 0.05, 0.4)

        except Exception as e:
            print(e)
            await asyncio.sleep(1)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in tasks:
        tasks[chat_id] = asyncio.create_task(
            spam(context.application, chat_id)
        )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in tasks:
        tasks[chat_id].cancel()
        del tasks[chat_id]


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("sik", start))
app.add_handler(CommandHandler("dur", stop))

app.run_polling()
