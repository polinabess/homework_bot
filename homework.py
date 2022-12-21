import os
import sys
import time
import requests

import logging

import telegram

from dotenv import load_dotenv

from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ONE_DAY = 86400
ONE_MNTH = 2629743
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
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)


def check_tokens():
    """Информация о функции.
    Проверяет доступность переменных окружения,
    которые необходимы для работы программы.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error(f"Не удается отправить вообщение в чат. {Exception}")
    else:
        logger.debug("Сообщение успешно отправлено")


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    payload = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        raise error(f"Ошибка при запросе к основному API: {error}")
    if response.status_code != HTTPStatus.OK:
        raise Exception(f"Ошибка {response.status_code}")
    try:
        return response.json()
    except TypeError:
        raise TypeError("Тип ответа имеет недопустимый формат")


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        response["homeworks"] and response["current_date"]
    except KeyError:
        raise KeyError("Нет доступных значений в ответе сервера")
    if type(response["homeworks"]) != list:
        raise TypeError(
            "В ответе API домашки под ключом `homeworks` данные приходят\
             не в виде списка."
        )
    try:
        return response.get("homeworks")[0]
    except IndexError:
        raise IndexError("Список работ пуст")


def parse_status(homework):
    """Информация о функции.
    Извлекает из информации о конкретной
    домашней работе статус этой работы.
    """
    data_of_hw = ("homework_name", "status")
    for data in data_of_hw:
        if data not in homework:
            raise KeyError(f"Ключ {data} отсутствует в ответе сервера")

    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    if homework_status not in HOMEWORK_VERDICTS:
        raise Exception(f"Неопределенный статус работы: {homework_status}")
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logger.debug("Основная логика работы бота.")
    if not check_tokens():
        logger.critical("Отсутствуют токены")
        sys.exit(1)
    # timestamp = int(time.time()) - ONE_MNTH
    message_of_error = ""
    while True:
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            timestamp = int(time.time()) - ONE_DAY
            response = get_api_answer(timestamp)
            homework_status = parse_status(check_response(response))
            send_message(bot, homework_status)

        except Exception as error:
            logging.error(error)
            message = f"Сбой в работе программы: {error}"
            if message != message_of_error:
                send_message(bot, message)
                message_of_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
