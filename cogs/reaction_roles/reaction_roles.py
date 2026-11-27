import logging

import discord
from discord.ext import commands

logger = logging.getLogger("ratburn.reaction_roles")


class ReactionRoles(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_member(
        self,
        guild: discord.Guild,
        user_id: int,
        cached_member: discord.Member | None = None,
    ) -> discord.Member | None:
        if cached_member is not None:
            return cached_member

        member = guild.get_member(user_id)
        if member is not None:
            return member

        try:
            return await guild.fetch_member(user_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def change_role_from_reaction(
        self,
        payload: discord.RawReactionActionEvent,
        *,
        add_role: bool,
    ):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        if self.bot.user and payload.user_id == self.bot.user.id:
            return

        post = self.bot.database.get_reaction_role_post_by_message(
            payload.message_id
        )
        if post is None or post["guild_id"] != guild.id:
            return

        emoji = str(payload.emoji)
        entry = self.bot.database.get_reaction_role_entry_by_emoji(
            post["id"],
            emoji,
        )
        if entry is None:
            return

        member = await self.get_member(
            guild,
            payload.user_id,
            getattr(payload, "member", None),
        )
        if member is None or member.bot:
            return

        role = guild.get_role(entry["role_id"])
        if role is None:
            logger.warning(
                "Reaction role %s no longer exists in guild %s.",
                entry["role_id"],
                guild.id,
            )
            return

        if role.is_default() or role.managed:
            logger.warning(
                "Skipping default or integration-managed role %s.",
                role.id,
            )
            return

        try:
            if add_role:
                if role not in member.roles:
                    await member.add_roles(
                        role,
                        reason="Reaction role selection",
                    )
            else:
                if role in member.roles:
                    await member.remove_roles(
                        role,
                        reason="Reaction role deselected",
                    )

        except discord.Forbidden:
            logger.warning(
                "Cannot manage role %s in guild %s. Check Ratburn's "
                "Manage Roles permission and role hierarchy.",
                role.id,
                guild.id,
            )
        except discord.HTTPException:
            logger.exception(
                "Discord rejected a reaction-role update for member %s "
                "in guild %s.",
                member.id,
                guild.id,
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent,
    ):
        await self.change_role_from_reaction(
            payload,
            add_role=True,
        )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ):
        await self.change_role_from_reaction(
            payload,
            add_role=False,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
