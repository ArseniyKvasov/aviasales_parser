from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.config import TELEGRAM_BOT_TOKEN, ORIGINS, DESTINATIONS, DATES, MAX_PRICE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origins = ", ".join(ORIGINS)
    destinations = ", ".join(DESTINATIONS)
    dates = ", ".join(DATES)
    await update.message.reply_text(
        f"Привет! Я слежу за билетами.\n"
        f"Направления: {origins} → {destinations}\n"
        f"Даты: {dates}\n"
        f"Макс. цена: {MAX_PRICE} ₽"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot is running...")
    app.run_polling()