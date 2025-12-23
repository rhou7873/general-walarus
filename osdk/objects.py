from general_walarus_python_osdk_sdk.ontology.objects import Guild, Member, Role 
from .osdk_globals import osdk
import logging


class OsdkObjects:
    log = logging.getLogger(f"{__name__}.OsdkObjects")

    ############ GUILD ############

    @staticmethod
    def get_guilds() -> list[Guild]:
        return [guild for guild in osdk.ontology.objects.Guild.iterate()]
    
    ############ MEMBER ############

    @staticmethod
    def get_members() -> list[Member]:
        return [member for member in osdk.ontology.objects.Member.iterate()]

    ############ ROLE ############

    @staticmethod
    def get_roles() -> list[Role]:
        return [role for role in osdk.ontology.objects.Role.iterate()]
