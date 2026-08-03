import json
from pathlib import Path
from typing import Any

from app.game_api.client import GameApiClient


class GuildService:
    """
    Получает и объединяет данные бригады,
    участников и недельного топа.
    """

    PLAYERS_PER_PAGE = 8

    def __init__(
        self,
        api_client: GameApiClient,
    ) -> None:
        self.api_client = api_client
        self.debug_directory = Path("data/debug")

    async def get_guild_status(
        self,
    ) -> dict[str, Any]:
        """
        Получает текущую бригаду.
        """

        payload = await self.api_client.get_guild_status()

        if not isinstance(payload, dict):
            raise RuntimeError(
                "API вернул неизвестный формат данных бригады."
            )

        self.save_debug_json(
            file_name="guild_status.json",
            data=payload,
        )

        return payload

    async def get_weekly_top(
        self,
        limit: int = 3000,
    ) -> Any:
        """
        Получает общий недельный топ.
        """

        payload = await self.api_client.get_weekly_top(
            limit=limit,
        )

        self.save_debug_json(
            file_name="weekly_top.json",
            data=payload,
        )

        return payload

    async def get_player_summary(
        self,
        user_id: int,
    ) -> Any:
        """
        Получает сводку выбранного игрока.
        """

        payload = await self.api_client.get_player_summary(
            user_id=user_id,
        )

        self.save_debug_json(
            file_name=f"player_summary_{user_id}.json",
            data=payload,
        )

        return payload

    async def get_combined_players(
        self,
    ) -> tuple[
        dict[str, Any],
        list[dict[str, Any]],
    ]:
        """
        Получает бригаду и недельный топ,
        а затем объединяет записи по userId.
        """

        guild_payload = await self.get_guild_status()
        weekly_payload = await self.get_weekly_top(
            limit=3000,
        )

        players = self.combine_guild_and_weekly_top(
            guild_payload=guild_payload,
            weekly_payload=weekly_payload,
        )

        return guild_payload, players

    def extract_guild_info(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Извлекает информацию о бригаде.
        """

        guild = payload.get("guild")

        if not isinstance(guild, dict):
            guild = {}

        return {
            "name": str(
                guild.get("name")
                or "Без названия"
            ),
            "level": self.safe_int(
                guild.get("level")
            ) or 0,
            "experience": self.safe_int(
                guild.get("exp")
            ) or 0,
            "experience_to_next": self.safe_int(
                guild.get("expToNext")
            ) or 0,
            "member_count": self.safe_int(
                guild.get("memberCount")
            ) or 0,
            "max_members": self.safe_int(
                guild.get("maxMembers")
            ) or 0,
            "leader_nickname": str(
                payload.get("leaderNickname")
                or "Не определён"
            ),
        }

    def extract_members(
        self,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Извлекает участников бригады.
        """

        raw_members = payload.get("members")

        if not isinstance(raw_members, list):
            return []

        members: list[dict[str, Any]] = []

        for raw_member in raw_members:
            if not isinstance(raw_member, dict):
                continue

            user_id = self.safe_int(
                raw_member.get("userId")
            )

            if user_id is None:
                continue

            members.append(
                {
                    "user_id": user_id,
                    "nickname": str(
                        raw_member.get("nickname")
                        or "Без ника"
                    ),
                    "guild_rank_id": (
                        self.safe_int(
                            raw_member.get("rankId")
                        )
                        or 999
                    ),
                    "guild_rank_name": str(
                        raw_member.get("rankName")
                        or "Без ранга"
                    ),
                }
            )

        members.sort(
            key=lambda player: (
                player["guild_rank_id"],
                player["nickname"].casefold(),
            )
        )

        return members

    def extract_weekly_records(
        self,
        payload: Any,
    ) -> list[dict[str, Any]]:
        """
        Извлекает записи недельного топа.

        Поддерживает как массив в корне,
        так и массив внутри популярных полей.
        """

        raw_records: Any = None

        if isinstance(payload, list):
            raw_records = payload

        elif isinstance(payload, dict):
            for field_name in (
                "items",
                "players",
                "top",
                "data",
                "results",
                "records",
            ):
                candidate = payload.get(field_name)

                if isinstance(candidate, list):
                    raw_records = candidate
                    break

            if raw_records is None:
                nested_data = payload.get("data")

                if isinstance(nested_data, dict):
                    for field_name in (
                        "items",
                        "players",
                        "top",
                        "results",
                        "records",
                    ):
                        candidate = nested_data.get(
                            field_name
                        )

                        if isinstance(candidate, list):
                            raw_records = candidate
                            break

        if not isinstance(raw_records, list):
            return []

        records: list[dict[str, Any]] = []

        for raw_record in raw_records:
            if not isinstance(raw_record, dict):
                continue

            user_id = self.safe_int(
                raw_record.get("userId")
                or raw_record.get("user_id")
                or raw_record.get("id")
            )

            if user_id is None:
                continue

            records.append(
                {
                    "user_id": user_id,
                    "weekly_rank": self.safe_int(
                        raw_record.get("rank")
                        or raw_record.get("position")
                    ),
                    "weekly_damage": (
                        self.safe_int(
                            raw_record.get("damage")
                            or raw_record.get("score")
                            or raw_record.get("value")
                        )
                        or 0
                    ),
                    "weekly_nickname": str(
                        raw_record.get("nickname")
                        or ""
                    ),
                    "photo_url": str(
                        raw_record.get("photoUrl")
                        or raw_record.get("photo_url")
                        or ""
                    ),
                }
            )

        return records

    def combine_guild_and_weekly_top(
        self,
        guild_payload: dict[str, Any],
        weekly_payload: Any,
    ) -> list[dict[str, Any]]:
        """
        Объединяет участников и недельный топ по userId.
        """

        members = self.extract_members(
            guild_payload
        )

        weekly_records = self.extract_weekly_records(
            weekly_payload
        )

        weekly_by_user_id = {
            record["user_id"]: record
            for record in weekly_records
        }

        combined: list[dict[str, Any]] = []

        for member in members:
            weekly = weekly_by_user_id.get(
                member["user_id"],
                {},
            )

            combined.append(
                {
                    **member,
                    "weekly_rank": weekly.get(
                        "weekly_rank"
                    ),
                    "weekly_damage": weekly.get(
                        "weekly_damage",
                        0,
                    ),
                    "photo_url": weekly.get(
                        "photo_url",
                        "",
                    ),
                }
            )

        return combined

    def get_members_catalog(
        self,
        players: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Участники сортируются по рангу бригады,
        а внутри ранга — по нику.
        """

        return sorted(
            players,
            key=lambda player: (
                player["guild_rank_id"],
                player["nickname"].casefold(),
            ),
        )

    def get_damage_catalog(
        self,
        players: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Топ сортируется по недельному урону
        от большего к меньшему.
        """

        return sorted(
            players,
            key=lambda player: (
                -player["weekly_damage"],
                player["nickname"].casefold(),
            ),
        )

    def get_page(
        self,
        players: list[dict[str, Any]],
        page: int,
    ) -> tuple[
        list[dict[str, Any]],
        int,
        int,
    ]:
        """
        Возвращает одну страницу каталога.
        """

        total_pages = max(
            1,
            (
                len(players)
                + self.PLAYERS_PER_PAGE
                - 1
            )
            // self.PLAYERS_PER_PAGE,
        )

        safe_page = max(
            0,
            min(
                page,
                total_pages - 1,
            ),
        )

        start = (
            safe_page
            * self.PLAYERS_PER_PAGE
        )

        end = start + self.PLAYERS_PER_PAGE

        return (
            players[start:end],
            safe_page,
            total_pages,
        )

    def find_player(
        self,
        players: list[dict[str, Any]],
        user_id: int,
    ) -> dict[str, Any] | None:
        """
        Ищет игрока по ID.
        """

        for player in players:
            if player["user_id"] == user_id:
                return player

        return None

    def extract_talent_points_total(
        self,
        payload: Any,
    ) -> int | None:
        """
        Ищет поле talentPointsTotal во всём ответе API.

        Поле может находиться:
        - в корне ответа;
        - внутри data;
        - внутри player;
        - внутри summary;
        - глубже во вложенных объектах и массивах.
        """

        value = self._find_nested_value(
            payload=payload,
            target_key="talentPointsTotal",
        )

        return self.safe_int(value)

    def _find_nested_value(
        self,
        payload: Any,
        target_key: str,
    ) -> Any:
        """
        Рекурсивно ищет ключ во вложенных
        словарях и списках.
        """

        if isinstance(payload, dict):
            if target_key in payload:
                return payload[target_key]

            for nested_value in payload.values():
                result = self._find_nested_value(
                    payload=nested_value,
                    target_key=target_key,
                )

                if result is not None:
                    return result

        elif isinstance(payload, list):
            for nested_value in payload:
                result = self._find_nested_value(
                    payload=nested_value,
                    target_key=target_key,
                )

                if result is not None:
                    return result

        return None

    def save_debug_json(
        self,
        file_name: str,
        data: Any,
    ) -> None:
        """
        Сохраняет диагностический JSON.
        """

        self.debug_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = self.debug_directory / file_name

        with file_path.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

    @staticmethod
    def safe_int(
        value: Any,
    ) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None