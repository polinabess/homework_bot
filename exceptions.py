class ProjStatusNotFound(Exception):
    """Полученный статус работы не найден среди возможных."""

    pass


class HttpStatusNotOk(Exception):
    """Статус-код запроса к API домашки неуспешен."""

    pass
