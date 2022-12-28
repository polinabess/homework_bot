class ProjStatusNotFoundError(Exception):
    """Полученный статус работы не найден среди возможных."""

    pass


class HttpStatusNotOkError(Exception):
    """Статус-код запроса к API домашки неуспешен."""

    pass


class ResponseIsEmptyError(IndexError):
    """В ответе ничего не приходит."""

    pass


class ValueIsNotListError(TypeError):
    """В ответе API тип данных не является списком."""

    pass
