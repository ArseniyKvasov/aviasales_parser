import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger("aviasales_watcher")


def fetch_tickets(
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
) -> list[Dict]:
    """
    Возвращает список всех билетов на дату, подходящих под фильтры.
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
        return []

    data = response.json()
    if not data.get("success") or not data.get("data"):
        logger.info("Aviasales: нет данных %s → %s на %s", origin, destination, date)
        return []

    results = []
    for offer in data["data"]:
        price = int(offer.get("price", 0))
        duration = int(offer.get("duration", 0))
        if price > max_price or duration > max_duration_minutes:
            continue

        results.append({
            "price": price,
            "departure_at": offer.get("departure_at"),
            "return_at": offer.get("return_at"),
            "destination_airport": offer.get("destination_airport"),
            "origin_airport": offer.get("origin_airport"),
            "link": offer.get("link"),
            "transfers": offer.get("transfers"),
            "duration": duration,
            "flight_number": offer.get("flight_number"),
        })

    return results


def fetch_special_offers(
    token: str,
    origin: str,
    destination: str,
    max_price: int,
    currency: str = "rub",
) -> list[Dict]:
    """
    Возвращает список всех специальных предложений, подходящих по цене.
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
        return []

    data = response.json()
    if not data.get("success") or not data.get("data"):
        logger.info("Aviasales: нет специальных предложений %s → %s", origin, destination)
        return []

    results = []
    for offer in data["data"]:
        price = int(offer.get("price", 0))
        departure_at = offer.get("departure_at")
        if not departure_at or (max_price and price > max_price):
            continue

        results.append({
            "price": price,
            "departure_at": departure_at,
            "return_at": offer.get("return_at"),
            "origin_airport": offer.get("origin_airport"),
            "destination_airport": offer.get("destination_airport"),
            "link": offer.get("link"),
            "airline": offer.get("airline"),
            "flight_number": offer.get("flight_number"),
            "signature": offer.get("signature"),
            "duration": offer.get("duration"),
        })

    return results