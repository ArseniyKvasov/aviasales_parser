import threading

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.config import (
    TELEGRAM_BOT_TOKEN,
    ORIGINS,
    DESTINATIONS,
    DATES,
    MAX_PRICE,
)
from app.watcher import run_watcher
from app.logger import setup_logger


logger = setup_logger()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origins = ", ".join(ORIGINS)
    destinations = ", ".join(DESTINATIONS)
    dates = ", ".join(DATES)

    await update.message.reply_text(
        "✈️ Aviasales watcher запущен\n\n"
        f"Направления: {origins} → {destinations}\n"
        f"Даты: {dates}\n"
        f"Макс. цена: {MAX_PRICE} ₽"
    )


def start_watcher() -> None:
    """
    Запускает watcher в отдельном потоке.
    """
    logger.info("Starting watcher thread")
    run_watcher()


def main() -> None:
    """
    Точка входа приложения:
    - watcher работает в фоне
    - Telegram-бот в основном потоке
    """
    logger.info("Application starting")

    watcher_thread = threading.Thread(
        target=start_watcher,
        name="WatcherThread",
        daemon=True,
    )
    watcher_thread.start()

    logger.info("Watcher started")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    logger.info("Telegram bot starting")
    app.run_polling()


if __name__ == "__main__":
    main()