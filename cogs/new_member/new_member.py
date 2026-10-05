import logging

import discord
from discord.ext import commands


logger = logging.getLogger("ratburn.new_member")


class NewMember(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_new_member_role(
        self,
        guild: discord.Guild
    ):
        role = discord.utils.get(
            guild.roles,
            name="✨ New Member"
        )

        if role is not None:
            return role

        try:
            role = await guild.create_role(
                name="✨ New Member"
            )
        except discord.Forbidden:
            logger.error(
                "Could not create New Member role in guild %s.",
                guild.id
            )
            return None
        except discord.HTTPException:
            logger.exception(
                "Failed creating New Member role in guild %s.",
                guild.id
            )
            return None

        logger.info(
            "Created New Member role in guild %s.",
            guild.id
        )

        return role

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.ensure_new_member_role(guild)


async def setup(bot):
    await bot.add_cog(NewMember(bot))
