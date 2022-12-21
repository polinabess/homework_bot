# import pytest
#import homework as homework_module
from tests import utils
import inspect
import logging
import re
import time
from http import HTTPStatus

import pytest
import requests
import telegram


def create_mock_response_get_with_custom_status_and_data(random_timestamp,
                                                         http_status,
                                                         data):
    def mocked_response(*args, **kwargs):
        response = utils.MockResponseGET(
            *args, random_timestamp=random_timestamp,
            http_status=http_status, **kwargs
        )

        def mock_json():
            return data

        response.json = mock_json
        return response
    return mocked_response


def get_mock_telegram_bot(monkeypatch, random_message):
    def mock_telegram_bot(random_message=random_message, *args, **kwargs):
        return utils.MockTelegramBot(*args, message=random_message, **kwargs)

    monkeypatch.setattr(telegram, 'Bot', mock_telegram_bot)
    return telegram.Bot(token='')


class TestHomework:
    HOMEWORK_VERDICTS = {
        'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
        'reviewing': 'Работа взята на проверку ревьюером.',
        'rejected': 'Работа проверена: у ревьюера есть замечания.'
    }
    ENV_VARS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
    HOMEWORK_CONSTANTS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN',
                          'TELEGRAM_CHAT_ID', 'RETRY_PERIOD',
                          'ENDPOINT', 'HEADERS', 'HOMEWORK_VERDICTS')
    HOMEWORK_FUNC_WITH_PARAMS_QTY = {
        'send_message': 2,
        'get_api_answer': 1,
        'check_response': 1,
        'parse_status': 1,
        'check_tokens': 0,
        'main': 0
    }
    RETRY_PERIOD = 600
    INVALID_RESPONSES = {
        'no_homework_key': utils.InvalidResponse(
            {
                "current_date": 123246
            },
            'homeworks'
        ),
        'not_dict_response': utils.InvalidResponse(
            [{
                'homeworks': [
                    {
                        'homework_name': 'hw123',
                        'status': 'approved'
                    }
                ],
                "current_date": 123246
            }],
            None
        ),
        'homeworks_not_in_list': utils.InvalidResponse(
            {
                'homeworks':
                    {
                        'homework_name': 'hw123',
                        'status': 'approved'
                    },
                'current_date': 123246
            },
            None
        )
    }
    NOT_OK_RESPONSES = {
        500: (
            create_mock_response_get_with_custom_status_and_data(
                random_timestamp=1000198000,
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
                data={}
            )
        ),
        401: (
            create_mock_response_get_with_custom_status_and_data(
                random_timestamp=1000198991,
                http_status=HTTPStatus.UNAUTHORIZED,
                data={
                    'code': 'not_authenticated',
                    'message': 'Учетные данные не были предоставлены.',
                    'source': '__response__'
                }
            )
        )
    }

    def test_main_without_env_vars_raise_exception(
                self, caplog, monkeypatch, random_timestamp, current_timestamp,
                random_message, homework_module
        ):
            self.mock_main(
                monkeypatch,
                random_message,
                random_timestamp,
                current_timestamp,
                homework_module
            )
            homework_module.PRACTICUM_TOKEN = None
            homework_module.TELEGRAM_TOKEN = None
            homework_module.TELEGRAM_CHAT_ID = None
            with utils.check_logging(caplog, level=logging.CRITICAL, message=(
                'Убедитесь, что при отсутствии обязательных переменных '
                'окружения событие логируется с уровнем `CRITICAL`.'
            )):
                try:
                    homework_module.main()
                except utils.BreakInfiniteLoop:
                    raise AssertionError(
                        'Убедитесь, что при запуске бота без переменных окружения '
                        'программа принудительно останавливается.'
                    )
                except SystemExit:
                    pass
                except Exception:
                    pass


if __name__ == '__main__':
    pytest.main()