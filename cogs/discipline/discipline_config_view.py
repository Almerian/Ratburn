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
        

class DisciplineEditView(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id: int
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(MuteConfigButton())
        self.add_item(DetentionConfigButton())
        self.add_item(BanConfigButton())
        self.add_item(ExpirationConfigButton())
        self.add_item(BackToDisciplineConfigButton())

    def build_embed(self):
        embed = discord.Embed(
            title="Discipline Configuration",
            description="What would you like to configure?"
        )

        return embed


class MuteConfigView(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id: int
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(EditMuteThresholdButton())
        self.add_item(EditMuteDurationButton())
        self.add_item(BackToDisciplineEditButton())

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        if config is None:
            threshold = "Not configured"
            duration = "Not configured"

        else:
            threshold = (
                str(config["mute_demerit_threshold"])
                if config["mute_demerit_threshold"] is not None
                else "Not configured"
            )

            if config["mute_duration_value"] is not None:
                duration = (
                    f"{config['mute_duration_value']} "
                    f"{config['mute_duration_unit']}"
                )
            else:
                duration = "Not configured"

        embed = discord.Embed(
            title="🔇 Mute Configuration",
            description="Configure the mute/timeout punishment."
        )

        embed.add_field(
            name="Demerit Threshold",
            value=threshold,
            inline=False
        )

        embed.add_field(
            name="Duration",
            value=duration,
            inline=False
        )

        return embed


class EditMuteThresholdButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Edit Threshold",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_modal(
            MuteThresholdModal(
                self.view.bot,
                self.view.guild_id
            )
        )


class MuteThresholdModal(discord.ui.Modal):
    def __init__(
        self,
        bot,
        guild_id: int
    ):
        super().__init__(title="Mute Demerit Threshold")

        self.bot = bot
        self.guild_id = guild_id

        self.threshold = discord.ui.TextInput(
            label="Demerit Threshold",
            placeholder="Example: 3",
            required=True,
            max_length=3
        )

        self.add_item(self.threshold)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        try:
            value = int(self.threshold.value)

            if value < 1:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "Please enter a whole number greater than 0.",
                ephemeral=True
            )
            return

        self.bot.database.set_discipline_config(
            self.guild_id,
            "mute_demerit_threshold",
            value
        )

        view = MuteConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class EditMuteDurationButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Edit Duration",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Mute duration editing isn't built yet.",
            ephemeral=True
        )


class BackToDisciplineEditButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Back",
            emoji="⬅️",
            style=discord.ButtonStyle.secondary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        view = DisciplineEditView(
            self.view.bot,
            self.view.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class MuteConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Mute",
            emoji="🔇",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        view = MuteConfigView(
            self.view.bot,
            self.view.guild_id
        )
    
        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class DetentionConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Detention",
            emoji="⛓️",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Detention editing isn't built yet.",
            ephemeral=True
        )


class BanConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Ban",
            emoji="🔨",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Ban editing isn't built yet.",
            ephemeral=True
        )


class ExpirationConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Demerit Expiration",
            emoji="⏳",
            style=discord.ButtonStyle.primary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            "Demerit expiration editing isn't built yet.",
            ephemeral=True
        )


class BackToDisciplineConfigButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Back",
            emoji="⬅️",
            style=discord.ButtonStyle.secondary
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        view = DisciplineConfigView(
            self.view.bot,
            self.view.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


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
        view = DisciplineEditView(
            self.view.bot,
            self.view.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
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
