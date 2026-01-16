import requests


def send_ticket_notification(
    bot_token: str,
    user_id: int,
    origin: str,
    destination: str,
    date: str,
    price: int,
    affiliate_link: str
) -> None:
    """
    Отправляет сообщение в Telegram с информацией о билете
    и партнёрской ссылкой.
    """

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    text = (
        f"✈️ Найден дешёвый билет\n\n"
        f"{origin} → {destination}\n"
        f"Дата: {date}\n"
        f"Цена: {price} ₽\n\n"
        f"Купить билет:\n{affiliate_link}"
    )

    payload = {
        "chat_id": user_id,
        "text": text,
        "disable_web_page_preview": False,
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()