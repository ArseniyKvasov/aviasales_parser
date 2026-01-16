from urllib.parse import urlencode


def generate_affiliate_link(
    origin: str,
    destination: str,
    departure_date: str,
    price: int,
    marker: str,
    currency: str = "rub"
) -> str:
    """
    Генерирует партнёрскую ссылку Aviasales через Travelpayouts.
    """

    base_url = "https://www.aviasales.ru/search"

    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": departure_date,
        "adults": 1,
        "currency": currency,
        "price": price,
        "marker": marker,
    }

    return f"{base_url}?{urlencode(params)}"