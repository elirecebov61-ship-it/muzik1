import os
import asyncio
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import RetryAfter, TimedOut

TOKEN = os.environ["BOT_TOKEN"]

VIDEOS = [
    "BAACAgIAAyEFAATiigGuAAICeGoTDAdJ2vFS1KKZiTgZTgtYIw-7AAIXmgAC2gKYSE_QVOHqeyrYOwQ",
    "BAACAgIAAyEFAATiigGuAAICeWoTDAfWwjVEz5osBfUgdhEmv1gGAAIYmgAC2gKYSB7epngzz5DrOwQ",
    "BAACAgIAAyEFAATiigGuAAICemoTDAeAmEp_XwOpFYmAJ8F5_MevAAIZmgAC2gKYSJHrzaSElA3SOwQ",
    "BAACAgIAAyEFAATiigGuAAICe2oTDAfF05ZpyqqSD3azz8hOORavAAIamgAC2gKYSELbVE0H4c3WOwQ",
    "BAACAgIAAyEFAATiigGuAAICfGoTDAfydB4AAaNuqbySu4gGwgRH3QACG5oAAtoCmEh3cpvucfyqNzsE",
    "BAACAgIAAyEFAATiigGuAAICfWoTDAcqhgwzhHBzHRAEAR75tcuZAAIcmgAC2gKYSDRdu_BDawfkOwQ",
    "BAACAgIAAyEFAATiigGuAAICfmoTDAdAz4er2e9Vzf4Wy3yu33XUAAIdmgAC2gKYSB2Ha-2TEmbGOwQ",
    "BAACAgIAAyEFAATiigGuAAICf2oTDAcJH0hEjRp2-HrEE70dG8zbAAIemgAC2gKYSBbm0FKdcQ4uOwQ",
    "BAACAgIAAyEFAATiigGuAAICgGoTDAdX9zwfR-b5D3HN-4EEj9J1AAIfmgAC2gKYSMwVZmXw56s-OwQ"
]

tasks = {}

async def spam(app, chat_id):
    delay = 0.6  # stabil başlanğıc

    while True:
        try:
            random.shuffle(VIDEOS)

            for v in VIDEOS:
                try:
                    await app.bot.send_video(chat_id=chat_id, video=v)

                    # çox kiçik delay = maksimum real sürət
                    await asyncio.sleep(delay)

                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                    delay = min(delay + 0.2, 2.0)

                except TimedOut:
                    await asyncio.sleep(1)
                    delay = min(delay + 0.2, 2.0)

            # tədricən sürətləndirmə
            delay = max(delay - 0.05, 0.4)

        except Exception:
            await asyncio.sleep(1)


async def sik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in tasks:
        tasks[chat_id] = asyncio.create_task(
            spam(context.application, chat_id)
        )


async def dur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in tasks:
        tasks[chat_id].cancel()
        del tasks[chat_id]


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("sik", sik))
app.add_handler(CommandHandler("dur", dur))

app.run_polling()
