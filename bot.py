
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

LOTS = [
    {
        "id": "1",
        "name": "NFT Gift #001",
        "ton": "5",
        "stars": "350",
        "description": "Коллекционный подарок Telegram",
    },
    {
        "id": "2",
        "name": "NFT Gift #002",
        "ton": "10",
        "stars": "700",
        "description": "Редкий цифровой подарок",
    },
]


def is_admin(user_id):
    return user_id in ADMIN_IDS


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Каталог NFT", callback_data="catalog")],
        [InlineKeyboardButton("ℹ️ О маркете", callback_data="about")],
    ])


def catalog_keyboard():
    buttons = [
        [InlineKeyboardButton(
            f"{lot['name']} — {lot['ton']} TON",
            callback_data=f"lot:{lot['id']}",
        )]
        for lot in LOTS
    ]
    buttons.append([
        InlineKeyboardButton("⬅️ В меню", callback_data="home")
    ])
    return InlineKeyboardMarkup(buttons)


def lot_keyboard(lot_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📩 Заявка в TON",
                callback_data=f"buyton:{lot_id}",
            ),
            InlineKeyboardButton(
                "⭐ Заявка в Stars",
                callback_data=f"buystars:{lot_id}",
            ),
        ],
        [InlineKeyboardButton("⬅️ Каталог", callback_data="catalog")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 Добро пожаловать в NFT Market!\n\n"
        "Выбирай лот и отправляй заявку продавцу.\n"
        "Оплата пока не автоматическая."
    )
    if is_admin(update.effective_user.id):
        text += (
            "\n\n🛠 Админ-команды:\n"
            "/addlot название | TON | Stars | описание\n"
            "/dellot ID\n"
            "/lots"
        )
    await update.message.reply_text(text, reply_markup=main_menu())


async def addlot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [p.strip() for p in raw.split("|")]

    if len(parts) != 4 or not all(parts):
        await update.message.reply_text(
            "Формат:\n"
            "/addlot Название | цена TON | цена Stars | описание\n\n"
            "Пример:\n"
            "/addlot Rare Gift | 5 | 350 | Редкий подарок"
        )
        return

    name, ton, stars, description = parts

    try:
        if float(ton) <= 0 or float(stars) <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ Обе цены должны быть числами больше нуля."
        )
        return

    next_id = str(max((int(x["id"]) for x in LOTS), default=0) + 1)
    LOTS.append({
        "id": next_id,
        "name": name,
        "ton": ton,
        "stars": stars,
        "description": description,
    })

    await update.message.reply_text(
        f"✅ Лот добавлен!\n"
        f"ID: {next_id}\n"
        f"Название: {name}\n"
        f"Цена: {ton} TON / ⭐ {stars} Stars"
    )


async def dellot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    if not context.args:
        await update.message.reply_text(
            "Укажи ID лота.\nПример: /dellot 2"
        )
        return

    lot_id = context.args[0]
    lot = next((x for x in LOTS if x["id"] == lot_id), None)

    if lot is None:
        await update.message.reply_text("❌ Лот с таким ID не найден.")
        return

    LOTS.remove(lot)
    await update.message.reply_text(
        f"🗑 Лот «{lot['name']}» удалён из каталога."
    )


async def lots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    if not LOTS:
        await update.message.reply_text("Каталог пока пуст.")
        return

    text = "💎 Текущие лоты:\n\n"
    for lot in LOTS:
        text += (
            f"ID: {lot['id']}\n"
            f"Название: {lot['name']}\n"
            f"Цена: {lot['ton']} TON / ⭐ {lot['stars']} Stars\n\n"
        )
    await update.message.reply_text(text)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "home":
        await query.edit_message_text(
            "💎 NFT Market — главное меню",
            reply_markup=main_menu(),
        )
        return

    if data == "catalog":
        await query.edit_message_text(
            "💎 Каталог NFT\nВыбери лот:",
            reply_markup=catalog_keyboard(),
        )
        return

    if data == "about":
        await query.edit_message_text(
            "💎 NFT Market\nКаталог цифровых коллекционных лотов.\n"
            "Заявки отправляются администратору.",
            reply_markup=main_menu(),
        )
        return

    if data.startswith("lot:"):
        lot_id = data.split(":", 1)[1]
        lot = next((x for x in LOTS if x["id"] == lot_id), None)
        if not lot:
            await query.message.reply_text("Лот не найден.")
            return

        await query.edit_message_text(
            f"💎 {lot['name']}\n\n{lot['description']}\n\n"
            f"Цена: {lot['ton']} TON\n"
            f"Цена: ⭐ {lot['stars']} Stars\n\n"
            "Выбери валюту для заявки:",
            reply_markup=lot_keyboard(lot_id),
        )
        return

    if data.startswith(("buyton:", "buystars:")):
        kind, lot_id = data.split(":", 1)
        lot = next((x for x in LOTS if x["id"] == lot_id), None)
        if not lot:
            await query.message.reply_text("Лот не найден.")
            return

        user = query.from_user
        currency = "TON" if kind == "buyton" else "Telegram Stars"
        price = lot["ton"] if kind == "buyton" else lot["stars"]
        username = f"@{user.username}" if user.username else "не указан"

        message = (
            "📩 Новая заявка на NFT!\n"
            f"Лот: {lot['name']}\n"
            f"Цена: {price} {currency}\n"
            f"Покупатель: {user.full_name}\n"
            f"Username: {username}\n"
            f"Telegram ID: {user.id}"
        )

        if not ADMIN_IDS:
            await query.message.reply_text(
                "Администратор ещё не настроен."
            )
            return

        delivered = False
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(admin_id, message)
                delivered = True
            except Exception:
                logging.exception("Не удалось отправить заявку админу")

        if delivered:
            await query.message.reply_text(
                "✅ Заявка отправлена! Продавец свяжется с тобой."
            )
        else:
            await query.message.reply_text(
                "Не удалось отправить заявку. Попробуй позже."
            )


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Используй кнопки меню, чтобы посмотреть каталог NFT.",
        reply_markup=main_menu(),
    )


def main():
    if not TOKEN:
        raise RuntimeError("Добавь BOT_TOKEN в GitHub Secrets")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addlot", addlot))
    app.add_handler(CommandHandler("dellot", dellot))
    app.add_handler(CommandHandler("lots", lots_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text)
    )
    app.run_polling()


if __name__ == "__main__":
    main()
        
