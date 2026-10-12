import os
import edge_tts
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

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
        text="🎙️အသံဖိုင် ဖန်တီးနေပါပြီ..."
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

def main():
    print("Bot စတင်အလုပ်လုပ်နေပါပြီ...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()