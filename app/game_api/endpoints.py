class GameApiEndpoints:
    """
    Эндпоинты игрового API.
    """

    AUTH_REFRESH = "/api/auth/refresh"

    PLAYER_INIT = "/api/player/init"
    PLAYER_ME = "/api/player/me"

    GUILD_STATUS = "/api/guild/status"
    GUILD_INVITE = "/api/guild/invite"

    @staticmethod
    def guild_view(guild_id: int) -> str:
        return f"/api/guild/{guild_id}"

    @staticmethod
    def weekly_top(limit: int = 3000) -> str:
        return f"/api/weekly-top/top?limit={limit}"

    @staticmethod
    def player_summary(user_id: int) -> str:
        return f"/api/summary/{user_id}"