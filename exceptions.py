class ProjStatusNotFoundError(Exception):
    """Полученный статус работы не найден среди возможных."""

    pass


class HttpStatusNotOkError(Exception):
    """Статус-код запроса к API домашки неуспешен."""

    pass


class ResponseIsEmptyError(IndexError):
    """."""

    pass


class ValueIsNotListError(TypeError):
    """."""

    pass
