import time
from typing import Optional, Dict
from datetime import datetime

from app.config import (
    AVIASALES_TOKEN,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_USER_ID,
    AFFILIATE_MARKER,
    ORIGINS,
    DESTINATIONS,
    DATES,
    MAX_PRICE,
    MAX_DURATION_MINUTES,
    CURRENCY,
    CHECK_INTERVAL_SECONDS,
)
from app.aviasales import fetch_cheapest_ticket, fetch_special_offers
from app.telegram import send_ticket_notification
from app.logger import setup_logger

logger = setup_logger()


def get_weekday(date_str: str) -> str:
    """
    Преобразует дату 'YYYY-MM-DD' в день недели на русском.
    """
    weekdays = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return weekdays[dt.weekday()]


def build_ticket_link(ticket: Dict) -> str:
    """
    Формирует прямую ссылку на конкретный билет с affiliate-меткой.
    """
    base_url = "https://www.aviasales.ru"
    raw_link = ticket.get("link", "")
    if not raw_link:
        return ""

    link = f"{base_url}{raw_link}"
    if AFFILIATE_MARKER:
        if "?" in link:
            link += f"&marker={AFFILIATE_MARKER}"
        else:
            link += f"?marker={AFFILIATE_MARKER}"
    return link


def get_ticket_key(ticket: Dict, is_special: bool = False) -> str:
    """
    Генерирует уникальный ключ рейса для отслеживания цены.
    """
    if is_special:
        # Для спецпредложения используем signature
        return ticket.get("signature", "")
    else:
        # Для обычного рейса origin+destination+departure+flight_number
        return f"{ticket.get('origin_airport','')}_{ticket.get('destination_airport','')}_{ticket.get('departure_at','')}_{ticket.get('flight_number','')}"


def run_watcher() -> None:
    """
    Основной цикл приложения:
    - каждые CHECK_INTERVAL_SECONDS проверяет билеты на все даты и аэропорты
    - отправляет уведомления для обычных и спецпредложений
    - уведомляет только если цена нового билета меньше предыдущей
    """
    logger.info("Aviasales watcher запущен")
    notified_prices: Dict[str, int] = {}  # ключ рейса → последняя отправленная цена

    while True:
        try:
            for date in DATES:
                for origin in ORIGINS:
                    for destination in DESTINATIONS:
                        # ===== обычные билеты =====
                        ticket = fetch_cheapest_ticket(
                            token=AVIASALES_TOKEN,
                            origin=origin,
                            destination=destination,
                            date=date,
                            max_price=MAX_PRICE,
                            max_duration_minutes=MAX_DURATION_MINUTES,
                            currency=CURRENCY,
                        )
                        if ticket:
                            ticket["date"] = date
                            ticket["origin_airport"] = origin
                            ticket["destination_airport"] = destination

                            # ключ по рейсу
                            key = get_ticket_key(ticket, is_special=False)
                            prev_price = notified_prices.get(key)

                            if prev_price is None or ticket["price"] < prev_price:
                                link = build_ticket_link(ticket)
                                if link:
                                    day_of_week = get_weekday(ticket["date"])
                                    send_ticket_notification(
                                        bot_token=TELEGRAM_BOT_TOKEN,
                                        user_id=TELEGRAM_USER_ID,
                                        origin=ticket["origin_airport"],
                                        destination=ticket["destination_airport"],
                                        date=ticket["date"],
                                        price=ticket["price"],
                                        affiliate_link=link,
                                    )
                                    notified_prices[key] = ticket["price"]
                                    logger.info(
                                        "Уведомление отправлено для обычного билета: %s → %s, %s ₽ (%s)",
                                        origin,
                                        destination,
                                        ticket["price"],
                                        day_of_week
                                    )
                            else:
                                logger.debug(
                                    "Цена не изменилась для обычного билета: %s → %s, %s ₽",
                                    origin,
                                    destination,
                                    ticket["price"]
                                )

                        # ===== специальные предложения =====
                        special_ticket = fetch_special_offers(
                            token=AVIASALES_TOKEN,
                            origin=origin,
                            destination=destination,
                            max_price=MAX_PRICE,
                            currency=CURRENCY,
                        )
                        if special_ticket:
                            special_ticket["date"] = special_ticket["departure_at"][:10]
                            special_ticket["origin_airport"] = origin
                            special_ticket["destination_airport"] = destination

                            # ключ по signature
                            key = get_ticket_key(special_ticket, is_special=True)
                            prev_price = notified_prices.get(key)

                            if prev_price is None or special_ticket["price"] < prev_price:
                                link = build_ticket_link(special_ticket)
                                if link:
                                    day_of_week = get_weekday(special_ticket["date"])
                                    send_ticket_notification(
                                        bot_token=TELEGRAM_BOT_TOKEN,
                                        user_id=TELEGRAM_USER_ID,
                                        origin=special_ticket["origin_airport"],
                                        destination=special_ticket["destination_airport"],
                                        date=special_ticket["date"],
                                        price=special_ticket["price"],
                                        affiliate_link=link,
                                    )
                                    notified_prices[key] = special_ticket["price"]
                                    logger.info(
                                        "Уведомление отправлено для спецпредложения: %s → %s, %s ₽ (%s)",
                                        origin,
                                        destination,
                                        special_ticket["price"],
                                        day_of_week
                                    )
                            else:
                                logger.debug(
                                    "Цена не изменилась для спецпредложения: %s → %s, %s ₽",
                                    origin,
                                    destination,
                                    special_ticket["price"]
                                )

            logger.info("Ожидание %s секунд", CHECK_INTERVAL_SECONDS)
            time.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as exc:
            logger.exception("Ошибка в цикле поиска: %s", exc)
            time.sleep(CHECK_INTERVAL_SECONDS)