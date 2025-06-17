import inspect
import logging
import os
from datetime import datetime
from colorama import init, Fore, Style

# colorama ni faollashtirish (Windows uchun kerak)
init(autoreset=True)


def get_test_name(default='test_unknown'):
    """
    Joriy ishga tushgan test funksiyasi nomini topadi.
    """
    stack = inspect.stack()
    for frame in stack:
        name = frame.function
        if name.startswith('test'):
            return name
    return default


def configure_logging(test_name='test_dafault'):
    """
    Kuchli log tizimi: rangli konsol loglari,
    faylga yozish va test nomi asosida farqlash
    """
    # Loglar uchun papka
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # Faylga log nomi
    log_file = os.path.join(log_dir, f"{test_name}_{datetime.now().strftime('%Y%m%d')}.log")

    # Logger yaratish
    logger = logging.getLogger(test_name)
    logger.setLevel(logging.DEBUG)

    # Eski handlerlarni tozalash
    if logger.hasHandlers():
        logger.handlers.clear()

    # Format
    log_format = '%(asctime)s - [%(levelname)s] - %(message)s'

    # Faylga yozuvchi handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    # Rangli konsol formatteri
    class ColorFormatter(logging.Formatter):
        def format(self, record):
            base_message = super().format(record)
            if record.levelno == logging.DEBUG:
                return f'{Fore.LIGHTBLACK_EX}{base_message}{Style.RESET_ALL}'
            elif record.levelno == logging.INFO:
                return f"{Fore.BLUE}{base_message}{Style.RESET_ALL}"
            elif record.levelno == logging.WARNING:
                return f"{Fore.YELLOW}{base_message}{Style.RESET_ALL}"
            elif record.levelno == logging.ERROR:
                return f"{Fore.RED}{base_message}{Style.RESET_ALL}"
            elif record.levelno == logging.CRITICAL:
                return f"{Fore.MAGENTA}{base_message}{Style.RESET_ALL}"
            return base_message

    # Konsolga chiqadigan handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColorFormatter(log_format))
    logger.addHandler(console_handler)

    # Root loggerga propagatsiyani o'chirib qoyamiz
    logger.propagate = False

    return logger