import asyncio
import logging
import os
import re
import tempfile

from aiohttp import web
from gtts import gTTS
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", "10000"))

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MYANMAR_RE = re.compile(
    r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]"
)

SPLIT_RE = re.compile(
    r"([\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]+|"
    r"[^\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]+)"
)


def split_text(text: str):
    parts = []

    for part in SPLIT_RE.findall(text):
        if not part or not part.strip():
            if parts:
                lang, previous = parts[-1]
                parts[-1] = (lang, previous + part)
            continue

        lang = "my" if MYANMAR_RE.search(part) else "en"

 
        if parts and parts[-1][0] == lang:
            old_lang, old_text = parts[-1]
            parts[-1] = (old_lang, old_text + part)
        else:
            parts.append((lang, part))

    return parts


def create_mp3(text: str, filename: str):
    parts = split_text(text)

    if not parts:
        raise ValueError("No readable text found")

    with open(filename, "wb") as audio_file:
        for lang, part in parts:
            gTTS(
                text=part,
                lang=lang,
                timeout=30,
            ).write_to_fp(audio_file)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.message:
        await update.message.reply_text(
            "မင်္ဂလာပါ။ 👋\n\n"
            "မြန်မာစာ၊ English သို့မဟုတ် "
            "ဘာသာစကားရောထားတဲ့စာ ပို့လိုက်ပါ။\n"
            "MP3 အသံဖိုင် ပြောင်းပေးပါမယ်။"
        )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    if len(text) > 4000:
        await update.message.reply_text(
            "စာသားက ရှည်လွန်းနေပါတယ်။ "
            "စာလုံး ၄၀၀၀ အောက်ခွဲပြီး ပို့ပေးပါ။"
        )
        return

    status = await update.message.reply_text(
        "🔊 MP3 ဖန်တီးနေပါတယ်..."
    )

    filename = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False,
        ) as temp:
            filename = temp.name

        await asyncio.to_thread(
            create_mp3,
            text,
            filename,
        )

        if not os.path.getsize(filename):
            raise RuntimeError("Generated MP3 is empty")

        with open(filename, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                filename="recap.mp3",
                title="Myanmar English TTS",
                read_timeout=120,
                write_timeout=120,
                connect_timeout=30,
            )

        await status.delete()
        logger.info("MP3 sent successfully")

    except Exception:
        logger.exception("TTS generation failed")

        try:
            await status.edit_text(
                "❌ MP3 ဖန်တီးမရပါ။\n"
                "Internet သို့မဟုတ် TTS service ကို "
                "စစ်ဆေးပြီး ထပ်စမ်းပါ။"
            )
        except Exception:
            pass

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                logger.warning("Could not remove temporary file")


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
logger.error(
        "Telegram bot error",
        exc_info=context.error,
    )


async def health(request: web.Request):
    return web.Response(
        text="Myanmar English TTS Bot is running!"
    )


async def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is missing"
        )

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )
    bot.add_error_handler(error_handler)

    web_app = web.Application()
    web_app.router.add_get("/", health)

    runner = web.AppRunner(web_app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT,
    )
    await site.start()

    try:
        await bot.initialize()
        await bot.start()
        await bot.updater.start_polling(
            drop_pending_updates=False,
        )

        logger.info("Myanmar English TTS Bot started")
        await asyncio.Event().wait()

    finally:
        if bot.updater and bot.updater.running:
            await bot.updater.stop()

        if bot.running:
            await bot.stop()

        await bot.shutdown()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())