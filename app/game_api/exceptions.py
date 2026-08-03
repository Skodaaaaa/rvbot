from typing import Any


class GameApiError(Exception):
    """
    Базовая ошибка игрового API.
    """

    def __init__(
        self,
        message: str,
        status: int | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status = status
        self.payload = payload


class GameApiAuthorizationError(GameApiError):
    """
    Ошибка авторизации или обновления токена.
    """


class GameApiResponseError(GameApiError):
    """
    Сервер вернул неожиданный или неуспешный ответ.
    """