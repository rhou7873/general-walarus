from osdk import osdk
from foundry_sdk_runtime.types import (
    ActionConfig,
    ActionMode,
    SyncApplyActionResponse
)
import logging


class ActionTypes:
    log = logging.getLogger(f"{__name__}.ActionTypes")

    def __init__(self, response: SyncApplyActionResponse):
        self.response = response

    def delete_guild(guild_id: str) -> bool:
        response: SyncApplyActionResponseosdk.ontology.actions.delete_guilds(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_result=ReturnResultType.ALL
            ),
            guilds=[guild_id]
        )

        if response.validation.result != "VALID":
            log.error("Failed to run delete guild action")
            return False

        return True

    def delete_guilds(guild_ids: list[str]) -> bool:
        for guild_id in guild_ids:
            if not delete_guild(guild_id):
                return False
        return True

    def delete_member(member_id: str) -> bool:
        response: SyncApplyActionResponseosdk.ontology.actions.delete_members(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_result=ReturnResultType.ALL
            ),
            members=[member_id]
        )

        if response.validation.result != "VALID":
            log.error("Failed to run delete member action")
            return False

        return True

    def delete_members(member_ids: list[str]) -> bool:
        for member_id in member_ids:
            if not delete_member(member_id):
                return False
        return True

    def delete_role(role_id: str) -> bool:
        response: SyncApplyActionResponseosdk.ontology.actions.delete_roles(
            action_config=ActionConfig(
                mode=ActionMode.VALIDATE_AND_EXECUTE,
                return_result=ReturnResultType.ALL
            ),
            roles=[role_id]
        )

        if response.validation.result != "VALID":
            log.error("Failed to run delete role action")
            return False

        return True

    def delete_roles(role_ids: list[str]) -> bool:
        for role_id in role_ids:
            if not delete_role(role_id):
                return False
        return True
