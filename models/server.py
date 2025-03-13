from discord import Guild, User
import database as db


class Server:
    """ Class that encapsulates a Guild object and additional info about a server """

    def __init__(self, guild: Guild) -> None:
        self.guild: Guild = guild
        """ Pycord Guild object associated with this server """
        self.rshuffle: list[str] = db.get_rshuffle(guild)
        """ String list of roles involved in role change """
        self.ushuffle: list[str] = db.get_ushuffle(guild)
        """ List of users involved in role change """
        self.archive_int: int = 2
        """ General chat archive interval (in weeks) """
        self.rc_int: int = 1
        """ Role change interval (in minutes) """
        self.timezone: str = "US/Eastern"
        """ Timezone of server """

    def __str__(self) -> str:
        return f"'{self.guild.name}': {self.guild.member_count} members (id: {self.guild.id})"
