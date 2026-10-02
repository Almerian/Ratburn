import discord
from discord.ext import commands
from discord import app_commands


class Discipline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
#============================================================
    @commands.hybrid_command(
        name="discipline_clear",
        description="Clear all discipline records for a user."
    )
    @app_commands.describe(
        user="The user whose discipline records should be cleared."
    )
    @app_commands.default_permissions(administrator=True)
    async def discipline_clear(
        self,
        ctx: commands.Context,
        user: discord.Member
    ):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(
                "Sorry, you need to be an administrator for that!",
                ephemeral=True
            )
            return
    
        self.bot.database.clear_discipline_records(
            ctx.guild.id,
            user.id
        )
    
        await ctx.send(
            f"Cleared all discipline records for {user.mention}.",
            ephemeral=True
        )
#============================================================    
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
