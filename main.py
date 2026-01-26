import os
import warnings
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, CallbackQueryHandler, filters
)
from Database import Database

warnings.filterwarnings("ignore")
load_dotenv()

db = Database()
TOKEN = os.getenv("BOT_TOKEN")

# States (Holatlar)
PHOTO, NAME, SIZE, PRICE, STOCK = range(5)
EDIT_STOCK = 10


# --- Klaviaturalar ---
def get_admin_keyboard():
    return ReplyKeyboardMarkup([
        ["📝 Mahsulotlar", "➕ Mahsulot qo‘shish"],
        ["📦 Bugungi buyurtmalar", "🗄 Arxiv"]
    ], resize_keyboard=True)


def get_customer_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍 Mahsulotlar", "🛒 Savatcha"],
        ["📊 Status", "🔍 Qidirish"]
    ], resize_keyboard=True)
def get_kuryer_keyboard():
    return ReplyKeyboardMarkup([
        ["🚚 Mening buyurtmalarim"],
        ["📊 Kunlik hisobot", "🏠 Asosiy menyu"]
    ], resize_keyboard=True)

def is_admin(user_id):
    return db.get_user_role(user_id) == 'admin'


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.full_name, user.username)
    role = db.get_user_role(user.id)

    if role == 'admin':
        await update.message.reply_text("👨‍💼 Admin paneli:", reply_markup=get_admin_keyboard())
    elif role=='kuryer':
        await update.message.reply_text(f"👋 Salom {user.first_name} kuryer paneliga xush kelibsiz!", reply_markup=get_kuryer_keyboard())
    else:
        await update.message.reply_text(f"👋 Salom {user.first_name}",reply_markup=get_customer_keyboard())

# --- ADMIN: Mahsulot qo'shish (Conversation) ---
async def add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("📸 Mahsulot rasmini yuboring:")
    return PHOTO


# Misol uchun get_photo funksiyasi ichida:
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_photo'] = update.message.photo[-1].file_id

    kb = ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    await update.message.reply_text("🏷 Mahsulot nomini kiriting:", reply_markup=kb)
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_name'] = update.message.text
    await update.message.reply_text("📏 O'lchamini kiriting:")
    return SIZE


async def get_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_size'] = update.message.text
    await update.message.reply_text("💰 Narxi (faqat raqam):")
    return PRICE


async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("Faqat raqam yozing!")
        return PRICE
    context.user_data['p_price'] = int(update.message.text)
    await update.message.reply_text("🔢 Ombordagi soni:")
    return STOCK


async def get_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("Faqat raqam!")
        return STOCK

    d = context.user_data
    db.add_product(d['p_name'], d['p_size'], d['p_price'], d['p_photo'], int(update.message.text))
    await update.message.reply_text("✅ Mahsulot saqlandi!", reply_markup=get_admin_keyboard())
    return ConversationHandler.END


# --- Mahsulotlarni chiqarish ---
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_mode = is_admin(user_id)
    products = db.get_all_products() if admin_mode else db.get_active_products()

    if not products:
        await update.message.reply_text("Hozircha mahsulot yo'q.")
        return

    for p in products:
        text = f"🆔 ID:{p['id']}\n 📦 Nomi:<b>{p['name']}</b>\n📏: {p['razmer']}\n💰: {p['price']:,} so'm\n🔢: {p['stock_quantity']} ta"

        if admin_mode:
            kb = [[InlineKeyboardButton("🗑 O'chirish", callback_data=f"del_{p['id']}"),
                   InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_{p['id']}")]]
        else:
            kb = [[InlineKeyboardButton("🛒 Savatchaga", callback_data=f"add_{p['id']}"),
                   InlineKeyboardButton("💳 Sotib olish", callback_data=f"buy_{p['id']}")]]

        if p['image_id']:
            await update.message.reply_photo(p['image_id'], caption=text, reply_markup=InlineKeyboardMarkup(kb),
                                             parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


# --- SAVATCHA ---
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get('cart', {})
    if not cart:
        await update.message.reply_text("Savatchangiz bo'sh. 🛒")
        return

    text = "🛒 <b>Sizning savatchangiz:</b>\n\n"
    total = 0
    for p_id, count in cart.items():
        p = db.get_product_by_id(p_id)
        if p:
            summa = p['price'] * count
            total += summa
            text += f"🔹 {p['name']} x {count} = {summa:,.0f} so'm\n"

    text += f"\n━━━━━━━━━━━━━━━\n💰 <b>Jami: {total:,.0f} so'm</b>"
    kb = [[InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout"),
           InlineKeyboardButton("🗑 Tozalash", callback_data="clear_cart")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


# --- CALLBACK HANDLER (Barcha tugmalar uchun) ---
async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("add_"):
        p_id = int(data.split("_")[1])
        cart = context.user_data.setdefault('cart', {})
        cart[p_id] = cart.get(p_id, 0) + 1
        await query.answer("Savatchaga qo'shildi! ✅")

    elif data == "clear_cart":
        context.user_data['cart'] = {}
        await query.message.edit_text("Savatchangiz tozalandi. 🗑")

    elif data.startswith("del_"):
        db.delete_product(int(data.split("_")[1]))
        await query.message.delete()

    elif data.startswith("edit_"):
        context.user_data['edit_id'] = int(data.split("_")[1])
        await query.message.reply_text("🔢 Yangi miqdorni yuboring:")
        return EDIT_STOCK


async def save_stock_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.isdigit():
        db.update_stock(context.user_data['edit_id'], int(update.message.text))
        await update.message.reply_text("✅ Miqdor yangilandi.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Vaqtinchalik ma'lumotlarni tozalash
    context.user_data.clear()

    # Foydalanuvchi roliga qarab asosiy menyuni chiqarish
    role = db.get_user_role(user_id)
    if role == 'admin':
        reply_markup = get_admin_keyboard()
    elif role == 'kuryer':
        reply_markup = get_kuryer_keyboard()
    else:
        reply_markup = get_customer_keyboard()

    await update.message.reply_text(
        "❌ Amaliyot bekor qilindi.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END
async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    await update.message.reply_text(f"Bu chat turi: {chat_type}\nID: <code>{chat_id}</code>", parse_mode="HTML")

# main() funksiyasi ichiga:
def main():
    app = Application.builder().token(TOKEN).build()

    # Conversation Handlers
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Mahsulot qo‘shish$"), add_product_start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_size)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stock)],
        },
        fallbacks=[
           MessageHandler(filters.Regex("^(❌ Bekor qilish|Bekor qilish)$"), cancel),
           CommandHandler("cancel", cancel)
        ]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callbacks, pattern="^edit_")],
        states={EDIT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_stock_edit)]},
        fallbacks=[MessageHandler(filters.Regex("^(❌ Bekor qilish|Bekor qilish)$"), cancel),
        CommandHandler("cancel", cancel)]
    ))

    # General Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^(📝 Mahsulotlar|🛍 Mahsulotlar)$"), show_products))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Savatcha$"), show_cart))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(CommandHandler("groupid", get_group_id))
    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == '__main__':
    main()

