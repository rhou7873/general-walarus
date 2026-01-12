from general_walarus_python_osdk_sdk.ontology.objects import (
    Guild, Member, Role, ChannelCategory, TextChannel 
)
from .osdk_globals import osdk
import logging


class OsdkObjects:
    log = logging.getLogger(f"{__name__}.OsdkObjects")

    #region GUILD

    @staticmethod
    def get_guild(guild_id: str):
        return osdk.ontology.objects.Guild.get(guild_id)

    @staticmethod
    def get_guilds() -> list[Guild]:
        return [guild
            for guild
            in osdk.ontology.objects.Guild.iterate()
        ]
    
    #endregion

    #region MEMBER

    @staticmethod
    def get_members() -> list[Member]:
        return [member
            for member
            in osdk.ontology.objects.Member.iterate()
        ]

    #endregion

    #region ROLE

    @staticmethod
    def get_roles() -> list[Role]:
        return [role
            for role
            in osdk.ontology.objects.Role.iterate()
        ]

    #endregion

    #region CHANNEL CATEGORY

    @staticmethod
    def get_channel_categories() -> list[ChannelCategory]:
        return [channel_category
            for channel_category
            in osdk.ontology.objects.ChannelCategory.iterate()
        ]

    #endregion

    #region TEXT CHANNEL
