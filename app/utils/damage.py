import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


DAMAGE_PATTERN = re.compile(
    r"^(?P<number>\d+(?:[.,]\d+)?)(?P<suffix>ккк|kkk|млрд|b|кк|kk|млн|м|m|к|k)?$",
    re.IGNORECASE,
)

DAMAGE_MULTIPLIERS: dict[str, int] = {
    "": 1,
    "к": 1_000,
    "k": 1_000,
    "кк": 1_000_000,
    "kk": 1_000_000,
    "м": 1_000_000,
    "m": 1_000_000,
    "млн": 1_000_000,
    "ккк": 1_000_000_000,
    "kkk": 1_000_000_000,
    "b": 1_000_000_000,
    "млрд": 1_000_000_000,
}


def normalize_damage_text(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("\u00a0", "").replace(" ", "")
    normalized = normalized.rstrip(".!?:;")
    return normalized


def parse_damage(value: str) -> int | None:
    normalized = normalize_damage_text(value)
    match = DAMAGE_PATTERN.fullmatch(normalized)

    if match is None:
        return None

    raw_number = match.group("number").replace(",", ".")
    suffix = (match.group("suffix") or "").lower()
    multiplier = DAMAGE_MULTIPLIERS.get(suffix)

    if multiplier is None:
        return None

    try:
        decimal_value = Decimal(raw_number)
    except InvalidOperation:
        return None

    if decimal_value <= 0:
        return None

    result = (decimal_value * Decimal(multiplier)).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )

    try:
        damage = int(result)
    except (ValueError, OverflowError):
        return None

    return damage if damage > 0 else None


def format_damage(value: int) -> str:
    return f"{value:,}".replace(",", " ")
