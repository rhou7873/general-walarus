from .osdk_globals import osdk
from .objects import OsdkObjects
import discord
from datetime import date, datetime
from foundry_sdk_runtime.types import (
    ActionConfig,
    ActionMode,
    ReturnEditsMode,
    SyncApplyActionResponse
)
import logging


class OsdkActions:
    log = logging.getLogger(f"{__name__}.OsdkActions")

    #region ONTOLOGY

    @staticmethod
    def sync_ontology(guilds: list[discord.Guild], force_sync: bool = False):
        OsdkActions.log.info("Syncing ontology...")
    
        guilds_in_osdk = [guild.server_id for guild in OsdkObjects.get_guilds()]
        roles_in_osdk = [role.role_id for role in OsdkObjects.get_roles()]
        members_in_osdk = [member.member_id for member in OsdkObjects.get_members()]
        channel_categories_in_osdk = [channel_category.category_id
            for channel_category in OsdkObjects.get_channel_categories()]
        text_channels_in_osdk = [text_channel.channel_id
            for text_channel in OsdkObjects.get_text_channels()]

        # Iterate over Pycord guilds
        guild_ids = set()
        role_ids = set()
        member_ids = set()
        category_ids = set()
        text_channel_ids = set()
        for guild in guilds:
            OsdkActions.log.info(f"Syncing guild {guild.name} (id: {guild.id})")
            guild_ids.add(str(guild.id))

            # Create missing OSDK guilds
            if str(guild.id) not in guilds_in_osdk or force_sync:
                OsdkActions.upsert_guild(guild)

            # Create missing OSDK roles & link to guild
            for role in guild.roles:
                OsdkActions.log.info(f"Syncing role {role.name} (id: {role.id})")
                if str(role.id) not in roles_in_osdk or force_sync:
                    OsdkActions.upsert_role(role)
                role_ids.add(str(role.id))

            # Create missing OSDK members & link to guild
            for member in guild.members:
                OsdkActions.log.info(f"Syncing member {member.name} (id: {member.id})")
                if OsdkActions.get_member_ontology_id(member) not in members_in_osdk or force_sync:
                    OsdkActions.upsert_member(member)
                member_ids.add(OsdkActions.get_member_ontology_id(member))

            # Create missing OSDK channel categories & link to guild
            for category in guild.categories:
                OsdkActions.log.info(f"Syncing channel category {category.name} "
                    f"(id: {category.id})")
                if str(category.id) not in channel_categories_in_osdk or force_sync:
                    OsdkActions.upsert_channel_category(category)
                category_ids.add(str(category.id))

            # Create missing OSDK text channels & link to guild and category
            for text_channel in guild.text_channels:
                OsdkActions.log.info(f"Syncing text channel {text_channel.name} "
                    f"(id: {text_channel.id})")
                if str(text_channel.id) not in text_channels_in_osdk or force_sync:
                    OsdkActions.upsert_text_channel(text_channel)
                text_channel_ids.add(str(text_channel.id))
        
        # Remove role objects that no longer exist in guilds
        roles_no_longer_existing = [role_id
            for role_id in roles_in_osdk 
            if role_id not in role_ids]
        OsdkActions.delete_roles(roles_no_longer_existing)

        # Remove member objects for members that no longer exist in guilds
        members_no_longer_existing = [member_id
            for member_id in members_in_osdk 
            if member_id not in member_ids]
        OsdkActions.delete_members(members_no_longer_existing)
        
        # Remove text channel objects for channels that no longer exist in guilds
        text_channels_no_longer_existing = [text_channel_id
            for text_channel_id in text_channels_in_osdk 
            if text_channel_id not in text_channel_ids]
        OsdkActions.delete_text_channels(text_channels_no_longer_existing)

        # Remove channel category objects for categories that no longer exist in guilds
        categories_no_longer_existing = [category_id
            for category_id in channel_categories_in_osdk 
            if category_id not in category_ids]
        OsdkActions.delete_channel_categories(categories_no_longer_existing)

        # Remove guild objects for guilds that bot is no longer connected to
        guilds_no_longer_connected = [guild_id
            for guild_id in guilds_in_osdk 
            if guild_id not in guild_ids]
        OsdkActions.delete_guilds(guilds_no_longer_connected)


        OsdkActions.log.info("Ontology sync complete!")

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

    #endregion

    #region GUILD

    @staticmethod
    def upsert_guild(
        guild: discord.Guild,
        archive_category: str = None,
        archive_freq: int = None,
        channel_to_archive: str = None,
        election_members: list[str] = None,
        election_roles: list[str] = None,
        election_cadence: int = None,
        next_archive_date: date = None
    ) -> bool:
        try:
            # Need to explicitly fetch these pass into upsert guild action
            # to make sure we don't overrwrite existing values
            # (this is a workaround we must do because of this: 
            # https://www.palantir.com/docs/foundry/functions/edits-overview#optional-arrays-in-function-backed-actions)
            osdk_guild = OsdkObjects.get_guild(str(guild.id))
            if election_members is None:
                election_members = [] if osdk_guild is None else osdk_guild.setting_election_members
            if election_roles is None:
                election_roles = [] if osdk_guild is None else osdk_guild.setting_election_roles
            if election_cadence is None:
                election_cadence = 1 if osdk_guild is None else osdk_guild.setting_election_cadence

            # Safely extracting parameters
            server_id = str(guild.id)
            name = guild.name
            description = guild.description
            icon_url = None if guild.icon is None else guild.icon.url

            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_guild(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                server_id=server_id,
                name=name,
                description=description,
                icon_url=icon_url,
                setting_archive_category=archive_category,
                setting_archive_frequency=archive_freq,
                setting_channel_to_archive=channel_to_archive,
                setting_election_members=election_members,
                setting_election_roles=election_roles,
                setting_election_cadence=election_cadence,
                setting_next_archive_date=next_archive_date
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

        # Delete guilds
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

    #endregion

    #region MEMBER

    @staticmethod
    def upsert_member(member: discord.Member) -> bool:
        try:
            # Safely extracting parameters
            member_id = OsdkActions.get_member_ontology_id(member)
            name = member.name
            is_bot = member.bot
            linked_server_id = str(member.guild.id)
            display_name = member.display_name
            roles_id = [str(role.id) for role in member.roles]
            roles_names = [role.name for role in member.roles]

            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_member(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                member_id=member_id,
                name=name,
                is_bot=is_bot,
                linked_server_id=linked_server_id,
                display_name=display_name,
                roles_ids=roles_id,
                roles_names=roles_names
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

    #endregion

    #region ROLE

    @staticmethod
    def upsert_role(role: discord.Role) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_role(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                role_id=str(role.id),
                linked_server_id=str(role.guild.id),
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
    def delete_role(role: discord.Role | str) -> bool:
        return OsdkActions.delete_roles([role])

    @staticmethod
    def delete_roles(roles: list[discord.Role | str]) -> bool:
        role_ids = ([str(role.id) for role in roles] 
            if len(roles) > 0 and isinstance(roles[0], discord.Role)
            else roles)

        if len(role_ids) == 0:
            return True

        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.delete_roles(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                roles=role_ids
            )

            if response.validation.result != "VALID":
                OsdkActions.log.error(f"Failed to run delete roles action: roles={roles}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running delete roles action: "
                f"roles={roles}, error={e}")
            return False

        return True

    #endregion

    #region TEXT CHANNEL

    @staticmethod
    def upsert_text_channel(text_channel: discord.TextChannel) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_text_channel(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                channel_id=str(text_channel.id),
                linked_server_id=str(text_channel.guild.id),
                name=text_channel.name,
                linked_category_id=str(text_channel.category_id),
                position=text_channel.position
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run upsert text channel action: "
                    f"text_channel={text_channel}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running upsert text channel action: "
                f"text_channel={text_channel}, error={e}")
            return False

        return True

    @staticmethod
    def delete_text_channel(text_channel: discord.TextChannel | str) -> bool:
        return OsdkActions.delete_text_channels([text_channel])

    @staticmethod
    def delete_text_channels(text_channels: list[discord.TextChannel | str]) -> bool:
        text_channel_ids = ([str(text_channel.id) for text_channel in text_channels] 
            if len(text_channels) > 0 and isinstance(text_channels[0], discord.TextChannel)
            else text_channels)

        if len(text_channel_ids) == 0:
            return True

        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.delete_text_channels(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                channels=text_channel_ids
            )

            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run delete text channels action: "
                    f"text_channels={text_channels}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running delete text channels action: "
                f"text_channels={text_channels}, error={e}")
            return False

        return True

    #endregion

    #region CHANNEL CATEGORY

    @staticmethod
    def upsert_channel_category(category: discord.CategoryChannel) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_channel_category(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                category_id=str(category.id),
                linked_server_id=str(category.guild.id),
                name=category.name,
                position=category.position
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run upsert channel category action: "
                    f"category={category}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running upsert channel category action: "
                f"category={category}, error={e}")
            return False

        return True

    @staticmethod
    def delete_channel_category(category: discord.CategoryChannel | str) -> bool:
        return OsdkActions.delete_channel_categories([category])

    @staticmethod
    def delete_channel_categories(categories: list[discord.CategoryChannel | str]) -> bool:
        category_ids = ([str(category.id) for category in categories] 
            if len(categories) > 0 and isinstance(categories[0], discord.CategoryChannel)
            else categories)

        if len(category_ids) == 0:
            return True

        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.delete_channel_categories(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                categories=category_ids
            )

            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run delete channel categories action: "
                    f"categories={categories}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running delete channel categories action: "
                f"categories={categories}, error={e}")
            return False

        return True

    #endregion

    #region ARCHIVE EVENTS

    @staticmethod
    def upsert_archive_event(
        channel: discord.TextChannel,
        category: discord.CategoryChannel,
        date_: date | None = None
    ) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.upsert_archive_event(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                archived_channel_id=str(channel.id),
                archived_channel_name=channel.name,
                archive_category_id=str(category.id),
                archive_category_name=category.name,
                guild_name=channel.guild.name,
                date_=date_ if date_ is not None else datetime.now().date()
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run upsert archive event action: "
                    f"channel={channel}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running upsert archive event action: "
                f"channel={channel}, error={e}")
            return False

        return True

    #endregion

    #region ELECTIONS

    @staticmethod
    def start_election(
        guild: discord.Guild
    ) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.start_election(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                linked_server_id=str(guild.id),
                guild_name=guild.name,
                status="In Progress",
                start_time=datetime.now()
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run start election action: "
                    f"guild={guild}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running start election action: "
                f"guild={guild}, error={e}")
            return False

        return True

    @staticmethod
    def stop_election(
        guild: discord.Guild
    ) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.stop_election(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                server=str(guild.id)
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run stop election action: "
                    f"guild={guild}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running stop election action: "
                f"guild={guild}, error={e}")
            return False

        return True

    @staticmethod
    def get_election_result(
        guild: discord.Guild,
        member: discord.Member,
        role: discord.Role
    ) -> bool:
        try:
            response: SyncApplyActionResponse = osdk.ontology.actions.get_election_result(
                action_config=ActionConfig(
                    mode=ActionMode.VALIDATE_AND_EXECUTE,
                    return_edits=ReturnEditsMode.ALL
                ),
                server=str(guild.id),
                member=str(member.id),
                role=str(role.id)
            )
            if response.validation.result != "VALID":
                OsdkActions.log.error("Failed to run get election result action: "
                    f"guild={guild}, member={member}, role={role}")
                return False
        except Exception as e:
            OsdkActions.log.error("Error when running get election result action: "
                f"guild={guild}, member={member}, role={role}, error={e}")
            return False

        return True

    #endregion
