from aiogram import Dispatcher

from app.bot.handlers import (
    admin,
    brigade,
    camps,
    guild_invite,
    info,
    menu,
    raid_creation,
    raid_damage,
    raids,
    setup,
    start,
)


def register_routers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(start.router)
    dispatcher.include_router(info.router)
    dispatcher.include_router(setup.router)
    dispatcher.include_router(menu.router)
    dispatcher.include_router(guild_invite.router)
    dispatcher.include_router(raid_creation.router)
    dispatcher.include_router(raid_damage.router)
    dispatcher.include_router(brigade.router)
    dispatcher.include_router(raids.router)
    dispatcher.include_router(camps.router)
    dispatcher.include_router(admin.router)
