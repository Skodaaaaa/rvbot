from pathlib import Path

from app.models.raid import Raid
from app.storage.json_storage import JsonStorage


class RaidStorage:
    def __init__(self, file_path: str | Path = "data/raids.json") -> None:
        self.storage = JsonStorage(
            file_path=file_path,
            default_data={"active_raids": {}, "history": []},
        )

    async def initialize(self) -> None:
        await self.storage.initialize()

    async def get_active_raid(self, chat_id: int) -> Raid | None:
        data = await self.storage.read()
        active_raids = data.get("active_raids", {})

        if not isinstance(active_raids, dict):
            return None

        raw_raid = active_raids.get(str(chat_id))
        if not isinstance(raw_raid, dict):
            return None

        raid = Raid.from_dict(raw_raid)
        return raid if raid.status == "open" else None

    async def save_active_raid(self, raid: Raid) -> None:
        data = await self.storage.read()
        active_raids = data.setdefault("active_raids", {})

        if not isinstance(active_raids, dict):
            active_raids = {}
            data["active_raids"] = active_raids

        active_raids[str(raid.chat_id)] = raid.to_dict()
        await self.storage.write(data)

    async def close_active_raid(self, chat_id: int, closed_at: str) -> Raid | None:
        data = await self.storage.read()
        active_raids = data.setdefault("active_raids", {})

        if not isinstance(active_raids, dict):
            return None

        raw_raid = active_raids.pop(str(chat_id), None)
        if not isinstance(raw_raid, dict):
            return None

        raid = Raid.from_dict(raw_raid)
        raid.status = "closed"
        raid.closed_at = closed_at

        history = data.setdefault("history", [])
        if not isinstance(history, list):
            history = []
            data["history"] = history

        history.append(raid.to_dict())
        await self.storage.write(data)
        return raid

    async def cancel_active_raid(self, chat_id: int) -> Raid | None:
        data = await self.storage.read()
        active_raids = data.setdefault("active_raids", {})

        if not isinstance(active_raids, dict):
            return None

        raw_raid = active_raids.pop(str(chat_id), None)
        if not isinstance(raw_raid, dict):
            return None

        await self.storage.write(data)
        return Raid.from_dict(raw_raid)

    async def get_history(self, chat_id: int) -> list[Raid]:
        data = await self.storage.read()
        raw_history = data.get("history", [])

        if not isinstance(raw_history, list):
            return []

        raids: list[Raid] = []
        for raw_raid in raw_history:
            if not isinstance(raw_raid, dict):
                continue
            raid = Raid.from_dict(raw_raid)
            if raid.chat_id == chat_id:
                raids.append(raid)

        return list(reversed(raids))
