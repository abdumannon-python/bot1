import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes,MessageHandler, filters
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
def get_main_keyboard():
    keyboard=[
        [KeyboardButton("🛍 Mahsulotlar"),KeyboardButton("🛒 Savatcha")],
        [KeyboardButton("ℹ️ Yordam"),KeyboardButton("📞Aloqa")],
        [KeyboardButton("⚙️ Sozlamalar!")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
def get_settings_keyboard():
    keyboard=[
        [KeyboardButton("🇺🇿 Tilni o'zgartirish")],
        [KeyboardButton("🔔 Bildirishnomalar")],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard,resize_keyboard=True)
async def start(update:Update,context: ContextTypes.DEFAULT_TYPE):
    user_name=update.effective_user.first_name
    await update.message.reply_text(
        "👋 Assalomu alaykum!\n"
        f"{user_name}\n"
        "🤖 Men yangi botman.\n"
        "📚 Hali ko'p narsani o'rganaman.",
        reply_markup=get_main_keyboard()
    )

async def handle_message(update:Update,context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if text=="🛍 Mahsulotlar":
        await update.message.reply_text("📦 Mahsulotlar ro'yxati...")
    elif text=="🛒 Savatcha":
        await update.message.reply_text("Savatiz bo'sh")
    elif text=="ℹ️ Yordam":
        await update.message.reply_text("🆘 Yordam bo'limi...")
    elif text=="📞Aloqa":
        await update.message.reply_text("+998 99 113 45 43 📞 Aloqaga chiqing")
    elif text=="⚙️ Sozlamalar!":
        await update.message.reply_text(
            "⚙️ Sozlamalar!",
            reply_markup=get_settings_keyboard()
        )
    elif text=="🔙 Orqaga":
        await update.message.reply_text(
            "🏠 Asosiy menyu:",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text("shu yerga muamoyizni yozib qoldiring iltimos")
async def help_command(update:Update,context: ContextTypes.DEFAULT_TYPE):
    help_text=""""🆘 Yordam

/start - Botni ishga tushirish
/help - Bu yordam xabari
"""
    await update.message.reply_text(help_text)


def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help",help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("bot ishga tushdi")
    app.run_polling()
if __name__=='__main__':
    main()