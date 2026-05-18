from fastapi import HTTPException, status


class ResourceGoneException(HTTPException):
    """
    Исключение для навсегда удалённых ресурсов (HTTP 410 Gone).

    Используется, когда ресурс существовал, но был удалён,
    и не должен появляться в поисковой выдаче.
    """

    def __init__(self, detail: str = "Ресурс был удалён"):
        super().__init__(status_code=status.HTTP_410_GONE, detail=detail)


class InsufficientPermissionsException(HTTPException):
    """Недостаточно прав для выполнения действия (403)"""

    def __init__(self, detail: str = "Доступ запрещён"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationException(HTTPException):
    """Ошибка валидации данных (422) с кастомным сообщением"""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )
