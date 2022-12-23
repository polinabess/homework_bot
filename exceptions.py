class RequestError(Exception):
    """Исключение, которое возникает при ошибке во ввремя запроса к API."""

    pass


class TypeIsNotList(Exception):
    """Исключение, возникающее когда в ответе API домашки под ключом\
        `homeworks` данные приходят не в виде списка."""

    pass


class ProjStatusNotFound(Exception):
    """Полученный статус работы не найден среди возможных."""

    pass


class HttpStatusNotOk(Exception):
    """Статус-код запроса к API домашки неуспешен."""

    pass
