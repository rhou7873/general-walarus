from datetime import datetime, timedelta
import discord
from models.server import Server
import utilities as ut


class Election:
    """ Class that encapsulates election info per guild """

    def __init__(self, server: Server) -> None:
        self.server: Server = server
        """ Server that election is occurring in """
        self.start_time = ut.now_time(server)
        """ Datetime of the start of the election """
        self.next_time: datetime = self.start_time + \
            timedelta(minutes=server.rc_int)
        """ Datetime of next election """
        self.roles = server.rshuffle
        """ List of roles that are to be shuffled """
        self.members = server.ushuffle
        """ List of members whose roles are to be shuffled """

    def __str__(self) -> str:
        guild: discord.Guild = self.server.guild
        return f"Guild '{guild.name}' (id: {guild.id}), next_time at {ut.timef(self.next_time)}"
