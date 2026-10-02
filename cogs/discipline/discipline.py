import discord
from discord.ext import commands


class Discipline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def process_filter_violation(
        self,
        guild_id: int,
        user_id: int
    ) -> str:
        database = self.bot.database

        if database.has_active_warning(
            guild_id,
            user_id
        ):
            action = "demerit"
        else:
            action = "warning"

        database.add_discipline_record(
            guild_id,
            user_id,
            action,
            "chat_filter"
        )

        return action


async def setup(bot):
    await bot.add_cog(Discipline(bot))
