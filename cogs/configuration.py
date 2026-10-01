import discord
from discord import app_commands
from discord.ext import commands


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="config",
        description="View Ratburn's current server configuration."
    )
    @app_commands.default_permissions(administrator=True)
    async def config(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        config = self.bot.database.get_config(interaction.guild.id)

        def mention_role(role_id):
            return f"<@&{role_id}>" if role_id else "Not configured"

        def mention_channel(channel_id):
            return f"<#{channel_id}>" if channel_id else "Not configured"

        embed = discord.Embed(
            title="🐀 Ratburn Configuration",
            description="Current server configuration."
        )

        embed.add_field(
            name="Staff Role",
            value=mention_role(config["staff_role_id"]),
            inline=True
        )

        embed.add_field(
            name="Detention Role",
            value=mention_role(config["detention_role_id"]),
            inline=True
        )

        embed.add_field(
            name="Detention Channel",
            value=mention_channel(config["detention_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Rat-Trap",
            value=mention_channel(config["rat_trap_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Birthday Channel",
            value=mention_channel(config["birthday_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Event Channel",
            value=mention_channel(config["event_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Audit Log Channel",
            value=mention_channel(config["audit_log_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Timezone",
            value=config["timezone"] or "Not configured",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Configuration(bot))
