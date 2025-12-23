from .osdk_globals import osdk
from .objects import OsdkObjects
import discord
from foundry_sdk_runtime.types import (
    ActionConfig,
    ActionMode,
    ReturnEditsMode,
    SyncApplyActionResponse
)
import logging


class OsdkActions:
    log = logging.getLogger(f"{__name__}.OsdkActions")

    ############ ONTOLOGY ############

    @staticmethod
    def sync_ontology(guilds: list[discord.Guild], force_sync: bool = False):
        guilds_in_osdk = [guild.server_id for guild in OsdkObjects.get_guilds()]
        members_in_osdk = [member.member_id for member in OsdkObjects.get_members()]

        # Iterate over Pycord guilds
        guild_ids = set()
        member_ids = set()
        for guild in guilds:
            guild_ids.add(str(guild.id))

            # Create missing OSDK guilds
            if str(guild.id) not in guilds_in_osdk or force_sync:
                OsdkActions.upsert_guild(guild)

            # Create missing OSDK members & link to guild
            for member in guild.members:
                if OsdkActions.get_member_ontology_id(member) not in members_in_osdk or force_sync:
                    OsdkActions.upsert_member(member)
                member_ids.add(OsdkActions.get_member_ontology_id(member))

        # Remove guild objects for guilds that bot is no longer connected to
        guilds_no_longer_connected = [guild_id
            for guild_id in guilds_in_osdk 
            if guild_id not in guild_ids]
        OsdkActions.delete_guilds(guilds_no_longer_connected)

        # Remove member objects for members that no longer exist in guilds
        members_no_longer_existing = [member_id
            for member_id in members_in_osdk 
            if member_id not in member_ids]
        OsdkActions.delete_members(members_no_longer_existing)

    @staticmethod
    def link_members_to_guild(members: list[discord.Member]) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.link_members_to_guild(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                members=[OsdkActions.get_member_ontology_id(member) for member in members],
                guild=str(members[0].guild.id)
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run link members to guild action: "
                    f"members={members}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running link members to guild action: "
                f"members={members}, error={e}")
            return False

        return True

    ############ GUILD ############

    @staticmethod
    def upsert_guild(guild: discord.Guild) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_guild(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                server_id=str(guild.id),
                name=guild.name
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run upsert guild action: guild={guild}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running upsert guild action: "
                f"guild={guild}, error={e}")
            return False

        return True

    @staticmethod
    def delete_guild(guild: discord.Guild | str) -> bool:
        return OsdkActions.delete_guilds([guild])

    @staticmethod
    def delete_guilds(guilds: list[discord.Guild | str]) -> bool:
        guild_ids = ([str(guild.id) for guild in guilds] 
            if len(guilds) > 0 and isinstance(guilds[0], discord.Guild)
            else guilds)

        if len(guild_ids) == 0:
            return True

        # First delete members
        OsdkActions.delete_members(
            [member for member in OsdkObjects.get_members() if member.linked_server_id in guild_ids]
        )

        # Now delete guilds
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.delete_guilds(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                guilds=guild_ids
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run delete guilds action: guilds={guilds}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running delete guilds action: "
                f"guilds={guilds}, error={e}")
            return False

        return True

    ############ MEMBER ############

    @staticmethod
    def upsert_member(member: discord.Member) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_member(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                member_id=OsdkActions.get_member_ontology_id(member),
                name=member.name,
                is_bot=member.bot,
                linked_server_id=str(member.guild.id),
                nickname=member.nick,
                roles=[str(role.id) for role in member.roles]
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run upsert member action: member={member}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running upsert member action: "
                f"member={member}, error={e}")
            return False

        return True

    @staticmethod
    def delete_member(member: discord.Member) -> bool:
        return OsdkActions.delete_members([member])

    @staticmethod
    def delete_members(members: list[discord.Member | str]) -> bool:
        member_ids = ([OsdkActions.get_member_ontology_id(member) for member in members] 
            if len(members) > 0 and isinstance(members[0], discord.Member)
            else members)

        if len(member_ids) == 0:
            return True

        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.delete_members(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                members=member_ids
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run delete members action: members={members}")
                return False
        except Exception as e:
            OsdkActions.log.error(f"Error when running delete members action: members={members}, error={e}")
            return False

        return True

    @staticmethod
    def get_member_ontology_id(member: discord.Member) -> str:
        return f"{member.guild.id}_{member.id}"

    ############ ROLE ############

    @staticmethod
    def upsert_role(role: discord.Role) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_role(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                role_id=str(role.id),
                name=role.name
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run upsert role action: role={role}")
                return False
        except Exception as e:
            OsdkActions.log.error(f"Error when running upsert role action: role={role}, error={e}")
            return False

        return True

    @staticmethod
    def delete_role(role: discord.Role) -> bool:
        return OsdkActions.delete_roles([role])

    @staticmethod
    def delete_roles(roles: list[discord.Role]) -> bool:
        if len(roles) == 0:
            return True

        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.delete_roles(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                roles=[str(role.id) for role in roles]
            )

            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run delete roles action: roles={roles}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running delete roles action: "
                f"roles={roles}, error={e}")
            return False

        return True
