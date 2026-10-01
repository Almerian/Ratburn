import discord
from discord import app_commands
from discord.ext import commands


class RatburnGroup(app_commands.Group):
    def __init__(self, bot):
        super().__init__(
            name="ratburn",
            description="Mr. Ratburn's server management commands."
        )

        self.bot = bot

    @app_commands.command(
        name="status",
        description="Check whether Mr. Ratburn is present."
    )
    async def status(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "📚 **Mr. Ratburn is in class!**\n"
            "Please take your seats."
        )

    @app_commands.command(
        name="info",
        description="Display information about Mr. Ratburn."
    )
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 Mr. Ratburn",
            description=(
                "Server management, moderation, scheduling, "
                "and other educational necessities."
            )
        )

        embed.add_field(
            name="Version",
            value="0.1",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ratburn = RatburnGroup(bot)

    async def cog_load(self):
        self.bot.tree.add_command(self.ratburn)

    async def cog_unload(self):
        self.bot.tree.remove_command(
            self.ratburn.name
        )


async def setup(bot):
    await bot.add_cog(General(bot))
