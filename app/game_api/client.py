import json
from datetime import datetime
from pathlib import Path
from typing import Any

import aiohttp

from app.config import Config
from app.game_api.endpoints import GameApiEndpoints
from app.game_api.exceptions import (
    GameApiAuthorizationError,
    GameApiError,
    GameApiResponseError,
)


class GameApiClient:
    """
    Асинхронный клиент игрового API.

    Использует один игровой аккаунт владельца бота.
    """

    def __init__(
        self,
        config: Config,
    ) -> None:
        self.base_url = config.game_api_base_url

        self.access_token = config.game_access_token
        self.refresh_token = config.game_refresh_token

        self.language = config.game_language
        self.country = config.game_country
        self.platform = config.game_platform

        self.session: aiohttp.ClientSession | None = None

        self.tokens_file = Path(
            "secrets/game_tokens.json"
        )

    async def start(self) -> None:
        """
        Создаёт HTTP-сессию и загружает сохранённые токены.
        """

        self._load_saved_tokens()

        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(
                total=30,
            )

            self.session = aiohttp.ClientSession(
                timeout=timeout,
            )

    async def close(self) -> None:
        """
        Закрывает HTTP-сессию.
        """

        if self.session is not None:
            await self.session.close()

    def _load_saved_tokens(self) -> None:
        """
        Если токены уже обновлялись, берёт их из secrets.
        """

        if not self.tokens_file.exists():
            return

        try:
            with self.tokens_file.open(
                mode="r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return

        saved_access_token = str(
            data.get("access_token", "")
        ).strip()

        saved_refresh_token = str(
            data.get("refresh_token", "")
        ).strip()

        if saved_access_token:
            self.access_token = saved_access_token

        if saved_refresh_token:
            self.refresh_token = saved_refresh_token

    def _save_tokens(self) -> None:
        """
        Сохраняет новые токены в локальный закрытый файл.
        """

        self.tokens_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "updated_at": datetime.now().isoformat(),
        }

        temp_file = self.tokens_file.with_suffix(
            ".json.tmp"
        )

        with temp_file.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temp_file.replace(
            self.tokens_file
        )

    def _build_url(
        self,
        path: str,
    ) -> str:
        return f"{self.base_url}{path}"

    def _build_headers(
        self,
        with_authorization: bool = True,
    ) -> dict[str, str]:
        """
        Базовые заголовки веб-клиента.

        Обфусцированные X-* пока не добавляем.
        Сначала проверим, достаточно ли основных.
        """

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Language": self.language,
            "X-Country": self.country,
            "X-Platform": self.platform,
        }

        if with_authorization:
            if not self.access_token:
                raise GameApiAuthorizationError(
                    "GAME_ACCESS_TOKEN не заполнен."
                )

            headers["Authorization"] = (
                f"Bearer {self.access_token}"
            )

        return headers

    async def request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        retry_after_refresh: bool = True,
    ) -> Any:
        """
        Выполняет запрос к игровому API.

        Сервер может сообщать об истёкшей авторизации
        двумя способами:

        - HTTP 401;
        - HTTP 403 с текстом Unauthorized.

        В обоих случаях один раз обновляем токен
        и повторяем исходный запрос.
        """

        await self.start()

        if self.session is None:
            raise RuntimeError(
                "HTTP-сессия игрового API не создана."
            )

        url = self._build_url(path)

        try:
            async with self.session.request(
                method=method.upper(),
                url=url,
                headers=self._build_headers(),
                json=json_body,
            ) as response:
                payload = await self._read_payload(
                    response
                )

                authorization_failed = (
                    response.status == 401
                    or (
                        response.status == 403
                        and self._payload_contains_unauthorized(
                            payload
                        )
                    )
                )

                if (
                    authorization_failed
                    and retry_after_refresh
                ):
                    await self.refresh_tokens()

                    return await self.request(
                        method=method,
                        path=path,
                        json_body=json_body,
                        retry_after_refresh=False,
                    )

                if response.status >= 400:
                    raise GameApiResponseError(
                        message=self._extract_error_message(
                            payload
                        ),
                        status=response.status,
                        payload=payload,
                    )

                return payload

        except aiohttp.ClientError as error:
            raise GameApiError(
                message=(
                    "Сетевая ошибка при обращении "
                    "к игровому API."
                ),
            ) from error

    async def _read_payload(
        self,
        response: aiohttp.ClientResponse,
    ) -> Any:
        """
        Пытается прочитать JSON.

        Если сервер вернул не JSON, сохраняет текст.
        """

        try:
            return await response.json(
                content_type=None
            )
        except (
            aiohttp.ContentTypeError,
            json.JSONDecodeError,
        ):
            return {
                "raw_text": await response.text(),
            }

    def _payload_contains_unauthorized(
        self,
        payload: Any,
    ) -> bool:
        """
        Проверяет, сообщает ли сервер
        об ошибке авторизации внутри ответа.
        """

        if isinstance(payload, dict):
            values: list[str] = []

            for field_name in (
                "raw_text",
                "message",
                "error",
                "detail",
            ):
                value = payload.get(field_name)

                if value is not None:
                    values.append(
                        str(value).lower()
                    )

            combined_text = " ".join(values)

            return (
                "unauthorized" in combined_text
                or "access denied" in combined_text
            )

        if isinstance(payload, str):
            lowered = payload.lower()

            return (
                "unauthorized" in lowered
                or "access denied" in lowered
            )

        return False

    def _extract_error_message(
        self,
        payload: Any,
    ) -> str:
        """
        Извлекает понятный текст ошибки сервера.
        """

        if isinstance(payload, dict):
            for field_name in (
                "message",
                "error",
                "detail",
                "raw_text",
            ):
                value = payload.get(field_name)

                if value:
                    return str(value)

        if isinstance(payload, str):
            return payload

        return "Игровой API вернул ошибку."

    async def refresh_tokens(self) -> None:
        """
        Обновляет игровую пару токенов.

        По клиентскому коду тело запроса:
        {
            "refresh": "<refreshToken>"
        }
        """

        await self.start()

        if self.session is None:
            raise RuntimeError(
                "HTTP-сессия игрового API не создана."
            )

        if not self.refresh_token:
            raise GameApiAuthorizationError(
                "GAME_REFRESH_TOKEN не заполнен."
            )

        url = self._build_url(
            GameApiEndpoints.AUTH_REFRESH
        )

        try:
            async with self.session.post(
                url=url,
                headers=self._build_headers(
                    with_authorization=False,
                ),
                json={
                    "refresh": self.refresh_token,
                },
            ) as response:
                payload = await self._read_payload(
                    response
                )

                if response.status >= 400:
                    raise GameApiAuthorizationError(
                        message=self._extract_error_message(
                            payload
                        ),
                        status=response.status,
                        payload=payload,
                    )

                if not isinstance(payload, dict):
                    raise GameApiAuthorizationError(
                        "Ответ обновления токена "
                        "имеет неизвестный формат.",
                        payload=payload,
                    )

                new_access_token = (
                    payload.get("access")
                    or payload.get("accessToken")
                )

                new_refresh_token = (
                    payload.get("refresh")
                    or payload.get("refreshToken")
                    or self.refresh_token
                )

                if not new_access_token:
                    raise GameApiAuthorizationError(
                        "Сервер не вернул новый access token.",
                        payload=payload,
                    )

                self.access_token = str(
                    new_access_token
                )

                self.refresh_token = str(
                    new_refresh_token
                )

                self._save_tokens()

        except aiohttp.ClientError as error:
            raise GameApiAuthorizationError(
                "Не удалось обновить игровой токен."
            ) from error

    async def init_player(self) -> Any:
        """
        Инициализирует игровые данные владельца.
        """

        return await self.request(
            method="POST",
            path=GameApiEndpoints.PLAYER_INIT,
        )

    async def get_player_me(self) -> Any:
        """
        Получает профиль владельца,
        если эндпоинт доступен.
        """

        return await self.request(
            method="GET",
            path=GameApiEndpoints.PLAYER_ME,
        )

    async def get_guild_status(self) -> Any:
        """
        Получает статус текущей бригады.

        По найденному клиентскому коду используется GET.
        """

        return await self.request(
            method="GET",
            path=GameApiEndpoints.GUILD_STATUS,
        )

    async def get_guild_view(
        self,
        guild_id: int,
    ) -> Any:
        """
        Получает отдельное представление бригады.
        """

        return await self.request(
            method="GET",
            path=GameApiEndpoints.guild_view(
                guild_id
            ),
        )

    async def get_weekly_top(
        self,
        limit: int = 3000,
    ) -> Any:
        """
        Получает общий недельный топ игроков.

        Затем сервис бригады оставит только
        участников нашей бригады.
        """

        return await self.request(
            method="GET",
            path=GameApiEndpoints.weekly_top(
                limit=limit,
            ),
        )


    async def get_player_summary(
        self,
        user_id: int,
    ) -> Any:
        """
        Получает публичную сводку выбранного игрока.
        """

        return await self.request(
            method="GET",
            path=GameApiEndpoints.player_summary(
                user_id=user_id,
            ),
        )