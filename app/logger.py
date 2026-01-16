import logging
import sys


def setup_logger() -> logging.Logger:
    """
    Настраивает логгер приложения для вывода в stdout.
    """

    logger = logging.getLogger("aviasales_watcher")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger