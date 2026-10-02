import discord


class DisciplineConfigView(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id: int
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(EditDisciplineConfigButton())
        self.add_item(ServerConfigButton())

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        embed = discord.Embed(
            title="Discipline Configuration",
            description=(
                "Configure how Ratburn handles "
                "disciplinary actions."
            )
        )

        if config is None:
            mute_threshold = "Not configured"
            mute_duration = "Not configured"
            detention_threshold = "Not configured"
            ban_threshold = "Not configured"
            expiration = "Not configured"

        else:
            mute_threshold = (
                str(config["mute_demerit_threshold"])
                if config["mute_demerit_threshold"] is not None
                else "Not configured"
            )

            if config["mute_duration_value"] is not None:
                mute_duration = (
                    f"{config['mute_duration_value']} "
                    f"{config['mute_duration_unit']}"
                )
            else:
                mute_duration = "Not configured"

            detention_threshold = (
                str(config["detention_demerit_threshold"])
                if config["detention_demerit_threshold"] is not None
                else "Not configured"
            )

            ban_threshold = (
                str(config["ban_demerit_threshold"])
                if config["ban_demerit_threshold"] is not None
                else "Not configured"
            )

            if config["demerit_expiration_value"] is not None:
                expiration = (
                    f"{config['demerit_expiration_value']} "
                    f"{config['demerit_expiration_unit']}"
                )
            elif config["demerit_expiration_unit"] == "never":
                expiration = "Never"
            else:
                expiration = "Not configured"

        embed.add_field(
            name="Mute",
            value=(
                f"**Demerit threshold:** {mute_threshold}\n"
                f"**Duration:** {mute_duration}"
            ),
            inline=False
        )

        embed.add_field(
            name="Detention",
            value=(
                f"**Demerit threshold:** "
                f"{detention_threshold}"
            ),
            inline=False
        )

        embed.add_field(
            name="Ban",
            value=(
                f"**Demerit threshold:** "
                f"{ban_threshold}"
            ),
            inline=False
        )

        embed.add_field(
            name="Demerit Expiration",
            value=expiration,
            inline=False
        )

        return embed


class EditDisciplineConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Edit Config",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Discipline editing is not built yet.",
            ephemeral=True
        )


class ServerConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Server Config",
            style=discord.ButtonStyle.secondary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        from cogs.configuration.configuration_view import ConfigView

        view = ConfigView(
            self.view.bot,
            interaction.guild.id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )
