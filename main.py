import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
load_dotenv()
TOKEN=os.getenv("BOT_TOKEN")
async def start(uptade:Update,context: ContextTypes.DEFAULT_TYPE):
    await uptade.message.reply_text('salom shop botga xush kelibsiz')

def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    print("bot ishga tushdi")
    app.run_polling()
if __name__=='__main__':
    main()