import asyncio
import logging
import os
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

logging.basicConfig(level=logging.INFO)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.message:
        await update.message.reply_text(
            "မင်္ဂလာပါ။ မြန်မာစာ ပို့လိုက်ပါ။ "
            "အသံဖိုင်အဖြစ် ပြောင်းပေးပါမယ်။"
        )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    status = await update.message.reply_text(
        "အသံဖိုင် ဖန်တီးနေပါပြီ..."
    )

    filename = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as f:
            filename = f.name

        # gTTS က synchronous ဖြစ်တဲ့အတွက်
        # Telegram Bot မရပ်သွားစေရန် thread မှာ run မယ်
        await asyncio.to_thread(
            gTTS(text=text, lang="my").save,
            filename
        )

        with open(filename, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                filename="recap.mp3",
                title="Myanmar TTS"
            )

        await status.delete()
        logging.info("Audio sent successfully")

    except Exception:
        logging.exception("TTS error")

        try:
            await status.edit_text(
                "အသံဖိုင် ဖန်တီးမရပါ။ "
                "Internet ချိတ်ဆက်မှုကို စစ်ပြီး ထပ်စမ်းပါ။"
            )
        except Exception:
            pass

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)


async def error_handler(update, context):
    logging.error(
        "Telegram bot error",
        exc_info=context.error
    )


async def health(request):
    return web.Response(text="Myanmar TTS Bot is running!")


async def main():
    if not TOKEN:
        raise RuntimeError(
            "Render Environment မှာ "
            "TELEGRAM_BOT_TOKEN ထည့်ပေးပါ။"
        )

    bot = Application.builder().token(TOKEN).build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )
    bot.add_error_handler(error_handler)

    web_app = web.Application()
    web_app.router.add_get("/", health)

    runner = web.AppRunner(web_app)
    await runner.setup()

    port = int(os.environ.get("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    try:
        await bot.initialize()
        await bot.start()
        await bot.updater.start_polling(
            drop_pending_updates=False
        )

        logging.info("Myanmar gTTS Bot started!")

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