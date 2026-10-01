import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ratburn",
        description="Check whether Mr. Ratburn is present."
    )
    async def ratburn(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "📚 **Mr. Ratburn is present.**\n"
            "Please take your seats."
        )

    @app_commands.command(
        name="ratburn_info",
        description="Display information about Mr. Ratburn."
    )
    async def ratburn_info(self, interaction: discord.Interaction):
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


async def setup(bot):
    await bot.add_cog(General(bot))
