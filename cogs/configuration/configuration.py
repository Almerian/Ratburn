import discord
from discord import app_commands
from discord.ext import commands

from .configuration_view import ConfigView


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="config",
        description="View and edit Ratburn's server configuration."
    )
    @app_commands.default_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        view = ConfigView(self.bot, interaction.guild.id)

        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Configuration(bot))
