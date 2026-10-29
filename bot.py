
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
ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

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
    await update.message.reply_text(
        "💎 Добро пожаловать в NFT Market!\n\n"
        "Выбирай лот и отправляй заявку продавцу.\n"
        "Оплата пока не автоматическая.",
        reply_markup=main_menu(),
    )


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
            "💎 NFT Market\n"
            "Каталог цифровых коллекционных лотов.\n"
            "Заявки отправляются администратору.",
            reply_markup=main_menu(),
        )
        return

    if data.startswith("lot:"):
        lot_id = data.split(":", 1)[1]
        lot = next((item for item in LOTS if item["id"] == lot_id), None)

        if lot is None:
            await query.message.reply_text("Лот не найден.")
            return

        await query.edit_message_text(
            f"💎 {lot['name']}\n\n"
            f"{lot['description']}\n\n"
            f"Цена: {lot['ton']} TON\n"
            f"Цена: ⭐ {lot['stars']} Stars\n\n"
            "Выбери валюту для заявки:",
            reply_markup=lot_keyboard(lot_id),
        )
        return

    if data.startswith(("buyton:", "buystars:")):
        kind, lot_id = data.split(":", 1)
        lot = next((item for item in LOTS if item["id"] == lot_id), None)

        if lot is None:
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
                "Администратор ещё не настроен. Попробуй позже."
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
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text)
    )
    app.run_polling()


if __name__ == "__main__":
    main()
                              
