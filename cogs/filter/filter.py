import discord
from discord import app_commands
from discord.ext import commands


class Filter(commands.GroupCog, group_name="filter"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="add",
        description="Add words to Ratburn's chat filter."
    )
    @app_commands.default_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction):
        pass

    @app_commands.command(
        name="remove",
        description="Remove words from Ratburn's chat filter."
    )
    @app_commands.default_permissions(administrator=True)
    async def remove(self, interaction: discord.Interaction):
        pass

    @app_commands.command(
        name="list",
        description="View the words currently in Ratburn's chat filter."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def list(self, interaction: discord.Interaction):
        pass


async def setup(bot):
    await bot.add_cog(Filter(bot))
