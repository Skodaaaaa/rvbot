from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RaidParticipant:
    telegram_user_id: int
    game_user_id: int
    nickname: str
    damage: int
    message_id: int
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RaidParticipant":
        return cls(
            telegram_user_id=int(data.get("telegram_user_id", 0)),
            game_user_id=int(data.get("game_user_id", 0)),
            nickname=str(data.get("nickname") or "Без ника"),
            damage=int(data.get("damage", 0)),
            message_id=int(data.get("message_id", 0)),
            updated_at=str(data.get("updated_at") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Raid:
    raid_id: str
    chat_id: int
    thread_id: int
    raid_date: str
    start_time: str
    minimum_damage: int
    total_guild_members: int
    created_by: int
    created_at: str
    status: str = "open"
    announcement_message_id: int | None = None
    last_service_message_id: int | None = None
    closed_at: str | None = None
    participants: dict[str, RaidParticipant] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Raid":
        participants: dict[str, RaidParticipant] = {}
        raw_participants = data.get("participants", {})

        if isinstance(raw_participants, dict):
            for key, raw_participant in raw_participants.items():
                if isinstance(raw_participant, dict):
                    participants[str(key)] = RaidParticipant.from_dict(raw_participant)

        announcement_message_id = data.get("announcement_message_id")
        last_service_message_id = data.get("last_service_message_id")

        return cls(
            raid_id=str(data.get("raid_id") or ""),
            chat_id=int(data.get("chat_id", 0)),
            thread_id=int(data.get("thread_id", 0)),
            raid_date=str(data.get("raid_date") or ""),
            start_time=str(data.get("start_time") or ""),
            minimum_damage=int(data.get("minimum_damage", 0)),
            total_guild_members=int(data.get("total_guild_members", 0)),
            created_by=int(data.get("created_by", 0)),
            created_at=str(data.get("created_at") or ""),
            status=str(data.get("status") or "open"),
            announcement_message_id=(
                int(announcement_message_id)
                if announcement_message_id is not None
                else None
            ),
            last_service_message_id=(
                int(last_service_message_id)
                if last_service_message_id is not None
                else None
            ),
            closed_at=(str(data["closed_at"]) if data.get("closed_at") else None),
            participants=participants,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["participants"] = {
            user_id: participant.to_dict()
            for user_id, participant in self.participants.items()
        }
        return data

    @property
    def total_damage(self) -> int:
        return sum(item.damage for item in self.participants.values())

    @property
    def participants_count(self) -> int:
        return len(self.participants)
