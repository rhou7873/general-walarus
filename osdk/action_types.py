from .osdk_globals import osdk
import discord
from foundry_sdk_runtime.types import (
    ActionConfig,
    ActionMode,
    ReturnEditsMode,
    SyncApplyActionResponse
)
import logging


class ActionTypes:
    log = logging.getLogger(f"{__name__}.ActionTypes")

    @staticmethod
    def create_guild(guild: discord.Guild) -> bool:
        response: SyncApplyActionResponse = osdk.ontology.actions.create_guild(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_edits=ReturnEditsMode.ALL
            ),
            server_id=str(guild.id),
            name=guild.name
        )

        if response.validation.result != "VALID":
            ActionTypes.log.error("Failed to run create guild action")
            return False

        return True

    @staticmethod
    def delete_guild(guild: discord.Guild) -> bool:
        return ActionTypes.delete_guilds([guild])

    @staticmethod
    def delete_guilds(guilds: list[discord.Guild]) -> bool:
        response: SyncApplyActionResponse = osdk.ontology.actions.delete_guilds(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_edits=ReturnEditsMode.ALL
            ),
            guilds=[str(guild.id) for guild in guilds]
        )

        if response.validation.result != "VALID":
            ActionTypes.log.error("Failed to run delete guilds action")
            return False

        return True

    @staticmethod
    def create_member(member: discord.Member) -> bool:
        response: SyncApplyActionResponse = osdk.ontology.actions.create_member(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_edits=ReturnEditsMode.ALL
            ),
            member_id=str(member.id),
            name=member.name,
            linked_server_id=str(member.guild.id),
            nickname=member.nick,
            roles=[str(role.id) for role in member.roles]
        )

        if response.validation.result != "VALID":
            ActionTypes.log.error("Failed to run create member action")
            return False

        return True

    @staticmethod
    def delete_member(member: discord.Member) -> bool:
        return ActionTypes.delete_members([member])

    @staticmethod
    def delete_members(members: list[discord.Member]) -> bool:
        response: SyncApplyActionResponse = osdk.ontology.actions.delete_members(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_edits=ReturnEditsMode.ALL
            ),
            members=[str(member.id) for member in members]
        )

        if response.validation.result != "VALID":
            ActionTypes.log.error("Failed to run delete members action")
            return False

        return True

    @staticmethod
    def create_role(role: discord.Role) -> bool:
        response: SyncApplyActionResponse = osdk.ontology.actions.create_role(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_edits=ReturnEditsMode.ALL
            ),
            role_id=str(role.id),
            name=role.name
        )

        if response.validation.result != "VALID":
            ActionTypes.log.error("Failed to run create role action")
            return False

        return True

    @staticmethod
    def delete_role(role: discord.Role) -> bool:
        return ActionTypes.delete_roles([role])

    @staticmethod
    def delete_roles(roles: list[discord.Role]) -> bool:
        response: SyncApplyActionResponse = osdk.ontology.actions.delete_roles(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_edits=ReturnEditsMode.ALL
            ),
            roles=[str(role.id) for role in roles]
        )

        if response.validation.result != "VALID":
            ActionTypes.log.error("Failed to run delete roles action")
            return False

        return True
