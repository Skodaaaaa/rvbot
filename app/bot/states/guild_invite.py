from aiogram.fsm.state import State, StatesGroup


class GuildInviteStates(StatesGroup):
    """
    Этапы приглашения игрока в бригаду.
    """

    waiting_for_user_id = State()
    waiting_for_confirmation = State()