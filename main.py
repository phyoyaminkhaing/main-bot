import os
import asyncio
import edge_tts
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from aiohttp import web

TELEGRAM_BOT_TOKEN = "8822846047:AAHDBuf1g9MK_TxE-TFPRNH8O4tLotbefRQ"
VOICE = "my-MM-NilarNeural"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "ကြိုဆိုပါတယ်၊ Text to voice ပြောင်းရန် မြန်မာစာသားများရိုက်ထည့်ပါ"
    await update.message.reply_text(welcome_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id
    output_audio = f"recap_{chat_id}.mp3"

    status_msg = await context.bot.send_message(
        chat_id=chat_id, 
        text="အသံဖိုင် ဖန်တီးနေပါပြီ..."
    )

    try:
        communicate = edge_tts.Communicate(user_text, VOICE)
        await communicate.save(output_audio)

        with open(output_audio, "rb") as audio:
            await context.bot.send_voice(chat_id=chat_id, voice=audio)

        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
        if os.path.exists(output_audio):
            os.remove(output_audio)

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=f"မှားယွင်းမှု တစ်ခုရှိနေပါသည်: {str(e)}"
        )

async def handle_web(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

def main():
    print("စတင်အလုပ်လုပ်နေပါပြီ...")
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
   
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    async def run_services():
        await web_server()
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        await asyncio.Event().wait()

    asyncio.run(run_services())

if __name__ == "__main__":
    main()