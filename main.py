import logging
import asyncio
import os
import tempfile

import edge_tts
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
VOICE = "my-MM-NilarNeural"

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START command received")

    await update.message.reply_text(
        "မင်္ဂလာပါ။ Bot အလုပ်လုပ်နေပါပြီ။ "
        "မြန်မာစာသား ပို့ကြည့်ပါ။"
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    print("Received:", text)

    status = await update.message.reply_text(
        "အသံဖိုင် ဖန်တီးနေပါပြီ..."
    )

    filename = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False
        ) as f:
            filename = f.name

        tts = edge_tts.Communicate(text, VOICE)
        await tts.save(filename)

        with open(filename, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                filename="recap.mp3"
            )

        await status.delete()
        print("Audio sent successfully")

    except Exception as e:
        logging.exception("TTS error")
        await status.edit_text(
            f"အသံဖိုင်ဖန်တီးမရပါ: {e}"
        )

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)


def main():
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: Bot Token ထည့်ရန် လိုအပ်ပါသည်။")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("Bot is starting...")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()