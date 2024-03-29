import os
import sys
import time
import requests

import logging

import telegram

from dotenv import load_dotenv

from http import HTTPStatus
from typing import Dict, List, NoReturn

from exceptions import (
    ProjStatusNotFoundError,
    HttpStatusNotOkError,
    ResponseIsEmptyError,
    ValueIsNotListError,
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ONE_DAY = 60 * 60 * 24
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    "%(asctime)s - %(module)s - %(lineno)d \
        - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)


def check_tokens() -> bool:
    """Информация о функции.
    Проверяет доступность переменных окружения,
    которые необходимы для работы программы.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    logger.info("Начало отправки сообщения в Telegram")
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logging.error(f"Не удается отправить вообщение в чат. {error}")
    else:
        logger.debug("Сообщение успешно отправлено")


def get_api_answer(timestamp: int) -> Dict:
    """Делает запрос к единственному эндпоинту API-сервиса."""
    logger.info("Начали запрос к API")
    payload = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise error(f"Ошибка при запросе к основному API: {error}")
    if response.status_code != HTTPStatus.OK:
        raise HttpStatusNotOkError(
            f"Ошибка запроса {response.status_code} {response.reason}"
        )
    return response.json()


def check_response(response: Dict) -> Dict:
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(f"Переменная {response} не является словарем.")
    if not response.get("homeworks"):
        raise KeyError("Нет доступных значений в ответе сервера: homeworks")
    if not response.get("current_date"):
        raise KeyError("Нет доступных значений в ответе сервера: current_date")
    if not isinstance(response["homeworks"], list):
        raise ValueIsNotListError(
            f"В ответе API домашки под ключом `homeworks` данные приходят\
             не в виде списка, {type(response['homeworks'])}."
        )
    if not response.get("homeworks")[0]:
        raise ResponseIsEmptyError("Список работ пуст")
    return response.get("homeworks")[0]


def parse_status(homework: Dict) -> str:
    """Информация о функции.
    Извлекает из информации о конкретной
    домашней работе статус этой работы.
    """
    data_of_hw = ("homework_name", "status")
    for data in data_of_hw:
        if data not in homework:
            raise KeyError(f"Ключ {data} отсутствует в ответе сервера")

    homework_name = homework.get("homework_name")
    message = homework.get("status")
    if message not in HOMEWORK_VERDICTS:
        raise ProjStatusNotFoundError(
            f"Неопределенный статус работы: {message}"
        )
    verdict = HOMEWORK_VERDICTS[message]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def missing_tokens() -> List:
    """Возвращает список отсутствующих токенов."""
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return [i for i in tokens if not i]


def main() -> NoReturn:
    """Основная логика работы бота."""
    logger.debug("Основная логика работы бота.")
    if not check_tokens():
        logger.critical(f"Отсутствуют токены {missing_tokens()}")
        sys.exit("Отсутствуют токены")

    previous_message = ""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            timestamp = int(time.time()) - ONE_DAY
            response = get_api_answer(timestamp)
            message = parse_status(check_response(response))

        except Exception as error:
            logging.error(error)
            message = f"Сбой в работе программы: {error}"

        finally:
            if message != previous_message:
                send_message(bot, message)
                previous_message = message
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
