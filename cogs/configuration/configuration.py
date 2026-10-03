import discord
from discord import app_commands
from discord.ext import commands

from .configuration_view import ConfigView


class Configuration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def configure_detention_channel(
        self,
        guild: discord.Guild,
        detention_channel: discord.TextChannel,
        staff_role: discord.Role | None,
        detention_role: discord.Role,
        previous_detention_role: discord.Role | None = None
    ):
        # Remove any old detention-role overwrites first.
        if previous_detention_role is not None:
            for channel in guild.channels:
                try:
                    await channel.set_permissions(
                        previous_detention_role,
                        overwrite=None
                    )
                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):
                    continue

        for channel in guild.channels:
            try:
                if channel.id == detention_channel.id:
                    # The detention channel is private.
                    await channel.set_permissions(
                        guild.default_role,
                        view_channel=False
                    )

                    await channel.set_permissions(
                        detention_role,
                        view_channel=True,
                        send_messages=False,
                        add_reactions=False,
                        create_public_threads=False,
                        create_private_threads=False,
                        send_messages_in_threads=False,
                        connect=False,
                        speak=False
                    )

                    # Staff can see and use the detention channel.
                    if staff_role is not None:
                        await channel.set_permissions(
                            staff_role,
                            view_channel=True,
                            send_messages=True,
                            read_message_history=True
                        )

                    # Ratburn can see and use the detention channel.
                    await channel.set_permissions(
                        guild.me,
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True
                    )

                else:
                    await channel.set_permissions(
                        detention_role,
                        view_channel=False,
                        send_messages=False,
                        add_reactions=False,
                        create_public_threads=False,
                        create_private_threads=False,
                        send_messages_in_threads=False,
                        connect=False,
                        speak=False
                    )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):
                continue

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

        view = ConfigView(
            self.bot,
            interaction.guild.id
        )

        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Configuration(bot))
