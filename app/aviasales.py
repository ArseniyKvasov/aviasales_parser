import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger("aviasales_watcher")


def fetch_cheapest_ticket(
    token: str,
    origin: str,
    destination: str,
    date: str,
    max_price: int,
    max_duration_minutes: int,
    one_way: bool = True,
    direct: bool = False,
    currency: str = "rub",
    limit: int = 1000,
    page: int = 1
) -> Optional[Dict]:
    """
    Запрашивает Aviasales Prices for Dates API и возвращает
    самый дешёвый билет на конкретную дату не дороже max_price.
    """

    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": date,
        "one_way": str(one_way).lower(),
        "direct": str(direct).lower(),
        "currency": currency,
        "market": "ru",
        "limit": limit,
        "page": page,
        "token": token,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logger.exception("Ошибка запроса Aviasales: %s", e)
        return None

    data = response.json()

    if not data.get("success") or not data.get("data"):
        logger.info(
            "Aviasales: нет данных %s → %s на %s",
            origin,
            destination,
            date,
        )
        return None

    cheapest = None

    for offer in data["data"]:
        price = int(offer.get("price", 0))
        duration = int(offer.get("duration", 0))

        if price > max_price:
            continue

        if duration > max_duration_minutes:
            continue

        if cheapest is None or price < cheapest["price"]:
            cheapest = {
                "price": price,
                "departure_at": offer.get("departure_at"),
                "return_at": offer.get("return_at"),
                "destination_airport": offer.get("destination_airport"),
                "origin_airport": offer.get("origin_airport"),
                "link": offer.get("link"),
                "transfers": offer.get("transfers"),
                "duration": offer.get("duration"),
            }

    if cheapest:
        logger.info(
            "Aviasales: найден билет %s → %s на %s — %s ₽",
            origin,
            destination,
            date,
            cheapest["price"],
        )
    else:
        logger.info(
            "Aviasales: билетов на %s не найдено в диапазоне ≤ %s ₽ (%s → %s)",
            date,
            max_price,
            origin,
            destination,
        )

    return cheapest


def fetch_special_offers(
    token: str,
    origin: str,
    destination: str,
    max_price: int,
    currency: str = "rub",
) -> Optional[Dict]:
    """
    Получает аномально дешёвые билеты через Aviasales get_special_offers API.
    Фильтрует по цене и по месяцу, если задан.
    Возвращает самый дешёвый билет среди найденных.
    """
    url = "https://api.travelpayouts.com/aviasales/v3/get_special_offers"
    params = {
        "origin": origin,
        "destination": destination,
        "locale": "ru",
        "currency": currency,
        "market": "ru",
        "token": token,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logger.exception("Ошибка запроса Aviasales special offers: %s", e)
        return None

    data = response.json()
    if not data.get("success") or not data.get("data"):
        logger.info("Aviasales: нет специальных предложений %s → %s", origin, destination)
        return None

    cheapest = None
    for offer in data["data"]:
        price = int(offer.get("price", 0))
        departure_at = offer.get("departure_at", "")
        if not departure_at:
            continue

        if max_price and price > max_price:
            continue

        if cheapest is None or price < cheapest["price"]:
            cheapest = {
                "price": price,
                "departure_at": departure_at,
                "return_at": offer.get("return_at"),
                "origin_airport": offer.get("origin_airport"),
                "destination_airport": offer.get("destination_airport"),
                "link": offer.get("link"),
                "airline": offer.get("airline"),
                "flight_number": offer.get("flight_number"),
                "duration": offer.get("duration"),
            }

    if cheapest:
        logger.info(
            "Aviasales special offer: найден билет %s → %s на %s ₽ (%s)",
            origin,
            destination,
            cheapest["price"],
            cheapest["departure_at"],
        )
    else:
        logger.info(
            "Aviasales special offer: билетов не найдено в диапазоне ≤ %s ₽ (%s → %s)",
            max_price,
            origin,
            destination,
        )

    return cheapest