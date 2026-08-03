from aiogram.fsm.state import State, StatesGroup


class RaidCreationStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_minimum_damage = State()
    waiting_for_confirmation = State()
