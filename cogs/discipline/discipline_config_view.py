import discord


class DisciplineConfigView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(EditDisciplineConfigButton())
        self.add_item(ServerConfigButton())

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        if config is None:
            mute_threshold = "Not configured"
            mute_duration = "Not configured"
            detention_threshold = "Not configured"
            ban_threshold = "Not configured"
            expiration = "Not configured"

        else:
            mute_threshold = format_config_value(
                config["mute_demerit_threshold"]
            )

            mute_duration = format_duration(
                config["mute_duration_value"],
                config["mute_duration_unit"]
            )

            detention_threshold = format_config_value(
                config["detention_demerit_threshold"]
            )

            ban_threshold = format_config_value(
                config["ban_demerit_threshold"]
            )

            expiration = format_expiration(
                config["demerit_expiration_value"],
                config["demerit_expiration_unit"]
            )

        embed = discord.Embed(
            title="Discipline Configuration",
            description=(
                "Configure how Ratburn handles "
                "disciplinary actions."
            )
        )

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
            value=f"**Demerit threshold:** {detention_threshold}",
            inline=False
        )

        embed.add_field(
            name="Ban",
            value=f"**Demerit threshold:** {ban_threshold}",
            inline=False
        )

        embed.add_field(
            name="Demerit Expiration",
            value=expiration,
            inline=False
        )

        return embed


class DisciplineEditView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(DisciplineSettingSelect())
        self.add_item(NavigationButton(
            label="Back",
            destination=DisciplineConfigView
        ))

    def build_embed(self):
        return discord.Embed(
            title="Discipline Configuration",
            description="Select a setting to configure."
        )


class DisciplineSettingSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Mute",
                emoji="🔇",
                description="Configure the mute/timeout punishment."
            ),
            discord.SelectOption(
                label="Detention",
                emoji="⛓️",
                description="Configure the detention punishment."
            ),
            discord.SelectOption(
                label="Ban",
                emoji="🔨",
                description="Configure the permanent ban punishment."
            ),
            discord.SelectOption(
                label="Demerit Expiration",
                emoji="⏳",
                description="Configure when demerits expire."
            ),
        ]

        super().__init__(
            placeholder="Select a setting...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        if selected == "Mute":
            view = MuteConfigView(
                self.view.bot,
                self.view.guild_id
            )

        elif selected == "Detention":
            view = DetentionConfigView(
                self.view.bot,
                self.view.guild_id
            )

        elif selected == "Ban":
            view = BanConfigView(
                self.view.bot,
                self.view.guild_id
            )

        elif selected == "Demerit Expiration":
            view = DemeritExpirationConfigView(
                self.view.bot,
                self.view.guild_id
            )

        else:
            await interaction.response.send_message(
                f"{selected} editing isn't built yet.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class MuteConfigView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(MuteSettingSelect())
        self.add_item(NavigationButton(
            label="Back",
            destination=DisciplineEditView
        ))

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        if config is None:
            threshold = "Not configured"
            duration = "Not configured"

        else:
            threshold = format_config_value(
                config["mute_demerit_threshold"]
            )

            duration = format_duration(
                config["mute_duration_value"],
                config["mute_duration_unit"]
            )

        embed = discord.Embed(
            title="🔇 Mute Configuration",
            description="Select a setting to configure."
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


class MuteSettingSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Demerit Threshold",
                emoji="⚠️",
                description="Set how many demerits trigger a mute."
            ),
            discord.SelectOption(
                label="Duration",
                emoji="⏱️",
                description="Set how long the mute lasts."
            ),
        ]

        super().__init__(
            placeholder="Select a setting...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        if selected == "Demerit Threshold":
            await interaction.response.send_modal(
                ThresholdModal(
                    bot=self.view.bot,
                    guild_id=self.view.guild_id,
                    setting="mute_demerit_threshold",
                    title="Mute Demerit Threshold",
                    destination=MuteConfigView
                )
            )

        elif selected == "Duration":
            view = MuteDurationView(
                self.view.bot,
                self.view.guild_id
            )

            await interaction.response.edit_message(
                embed=view.build_embed(),
                view=view
            )


class DetentionConfigView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(DetentionSettingSelect())
        self.add_item(NavigationButton(
            label="Back",
            destination=DisciplineEditView
        ))

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        threshold = (
            format_config_value(
                config["detention_demerit_threshold"]
            )
            if config is not None
            else "Not configured"
        )

        embed = discord.Embed(
            title="⛓️ Detention Configuration",
            description="Select a setting to configure."
        )

        embed.add_field(
            name="Demerit Threshold",
            value=threshold,
            inline=False
        )

        return embed


class DetentionSettingSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Demerit Threshold",
                emoji="⚠️",
                description="Set how many demerits trigger detention."
            ),
        ]

        super().__init__(
            placeholder="Select a setting...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            ThresholdModal(
                bot=self.view.bot,
                guild_id=self.view.guild_id,
                setting="detention_demerit_threshold",
                title="Detention Demerit Threshold",
                destination=DetentionConfigView
            )
        )


class BanConfigView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(BanSettingSelect())
        self.add_item(NavigationButton(
            label="Back",
            destination=DisciplineEditView
        ))

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        threshold = (
            format_config_value(
                config["ban_demerit_threshold"]
            )
            if config is not None
            else "Not configured"
        )

        embed = discord.Embed(
            title="🔨 Ban Configuration",
            description="Select a setting to configure."
        )

        embed.add_field(
            name="Demerit Threshold",
            value=threshold,
            inline=False
        )

        return embed


class BanSettingSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Demerit Threshold",
                emoji="⚠️",
                description="Set how many demerits trigger a permanent ban."
            ),
        ]

        super().__init__(
            placeholder="Select a setting...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            ThresholdModal(
                bot=self.view.bot,
                guild_id=self.view.guild_id,
                setting="ban_demerit_threshold",
                title="Ban Demerit Threshold",
                destination=BanConfigView
            )
        )


class DemeritExpirationConfigView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(DemeritExpirationSelect())
        self.add_item(NavigationButton(
            label="Back",
            destination=DisciplineEditView
        ))

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        if config is None:
            expiration = "Not configured"
        else:
            expiration = format_expiration(
                config["demerit_expiration_value"],
                config["demerit_expiration_unit"]
            )

        embed = discord.Embed(
            title="⏳ Demerit Expiration",
            description="Select how long each demerit remains active."
        )

        embed.add_field(
            name="Expiration",
            value=expiration,
            inline=False
        )

        return embed


class DemeritExpirationSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Days",
                emoji="📅",
                description="Expire demerits after a number of days."
            ),
            discord.SelectOption(
                label="Weeks",
                emoji="📅",
                description="Expire demerits after a number of weeks."
            ),
            discord.SelectOption(
                label="Months",
                emoji="📅",
                description="Expire demerits after a number of months."
            ),
            discord.SelectOption(
                label="Never",
                emoji="♾️",
                description="Demerits remain active permanently."
            ),
        ]

        super().__init__(
            placeholder="Select an expiration...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        if selected == "Never":
            self.view.bot.database.set_discipline_config(
                self.view.guild_id,
                "demerit_expiration_value",
                None
            )

            self.view.bot.database.set_discipline_config(
                self.view.guild_id,
                "demerit_expiration_unit",
                "never"
            )

            view = DemeritExpirationConfigView(
                self.view.bot,
                self.view.guild_id
            )

            await interaction.response.edit_message(
                embed=view.build_embed(),
                view=view
            )

            return

        await interaction.response.send_modal(
            ExpirationValueModal(
                bot=self.view.bot,
                guild_id=self.view.guild_id,
                unit=selected.lower()
            )
        )


class ExpirationValueModal(discord.ui.Modal):
    def __init__(
        self,
        bot,
        guild_id: int,
        unit: str
    ):
        super().__init__(title="Demerit Expiration")

        self.bot = bot
        self.guild_id = guild_id
        self.unit = unit

        self.duration = discord.ui.TextInput(
            label=f"Number of {unit}",
            placeholder="Example: 30",
            required=True,
            max_length=3
        )

        self.add_item(self.duration)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.duration.value)

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
            "demerit_expiration_value",
            value
        )

        self.bot.database.set_discipline_config(
            self.guild_id,
            "demerit_expiration_unit",
            self.unit
        )

        view = DemeritExpirationConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class MuteDurationView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(EditMuteDurationButton())
        self.add_item(NavigationButton(
            label="Back",
            destination=MuteConfigView
        ))

    def build_embed(self):
        config = self.bot.database.get_discipline_config(
            self.guild_id
        )

        if (
            config is not None
            and config["mute_duration_value"] is not None
            and config["mute_duration_unit"] is not None
        ):
            duration = (
                f"{config['mute_duration_value']} "
                f"{config['mute_duration_unit']}"
            )
        else:
            duration = "Not configured"

        embed = discord.Embed(
            title="⏱️ Mute Duration",
            description="Configure how long a mute/timeout lasts."
        )

        embed.add_field(
            name="Duration",
            value=duration,
            inline=False
        )

        return embed


class EditMuteDurationButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Edit Duration",
            style=discord.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            MuteDurationModal(
                self.view.bot,
                self.view.guild_id
            )
        )


class ThresholdModal(discord.ui.Modal):
    def __init__(
        self,
        bot,
        guild_id: int,
        setting: str,
        title: str,
        destination
    ):
        super().__init__(title=title)

        self.bot = bot
        self.guild_id = guild_id
        self.setting = setting
        self.destination = destination

        self.threshold = discord.ui.TextInput(
            label="Demerit Threshold",
            placeholder="Example: 3",
            required=True,
            max_length=3
        )

        self.add_item(self.threshold)

    async def on_submit(self, interaction: discord.Interaction):
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
            self.setting,
            value
        )

        view = self.destination(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class MuteDurationModal(discord.ui.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="Mute Duration")

        self.bot = bot
        self.guild_id = guild_id

        self.duration_value = discord.ui.TextInput(
            label="Duration",
            placeholder="Example: 10",
            required=True,
            max_length=5
        )

        self.duration_unit = discord.ui.TextInput(
            label="Unit",
            placeholder="minutes, hours, or days",
            required=True,
            max_length=7
        )

        self.add_item(self.duration_value)
        self.add_item(self.duration_unit)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.duration_value.value)

            if value < 1:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "Duration must be a whole number greater than 0.",
                ephemeral=True
            )
            return

        unit = self.duration_unit.value.strip().lower()

        allowed_units = {
            "minute": "minutes",
            "minutes": "minutes",
            "hour": "hours",
            "hours": "hours",
            "day": "days",
            "days": "days"
        }

        if unit not in allowed_units:
            await interaction.response.send_message(
                "Unit must be minutes, hours, or days.",
                ephemeral=True
            )
            return

        unit = allowed_units[unit]

        max_minutes = 28 * 24 * 60
        minutes = value

        if unit == "hours":
            minutes *= 60

        elif unit == "days":
            minutes *= 24 * 60

        minutes = min(minutes, max_minutes)

        if unit == "hours":
            value = minutes // 60

        elif unit == "days":
            value = minutes // (24 * 60)

        else:
            value = minutes

        self.bot.database.set_discipline_config(
            self.guild_id,
            "mute_duration_value",
            value
        )

        self.bot.database.set_discipline_config(
            self.guild_id,
            "mute_duration_unit",
            unit
        )

        view = MuteDurationView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


class NavigationButton(discord.ui.Button):
    def __init__(self, label: str, destination):
        super().__init__(
            label=label,
            emoji="⬅️",
            style=discord.ButtonStyle.secondary
        )

        self.destination = destination

    async def callback(self, interaction: discord.Interaction):
        view = self.destination(
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

    async def callback(self, interaction: discord.Interaction):
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

    async def callback(self, interaction: discord.Interaction):
        from cogs.configuration.configuration_view import ConfigView

        view = ConfigView(
            self.view.bot,
            interaction.guild.id
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view
        )


def format_config_value(value):
    if value is None:
        return "Not configured"

    return str(value)


def format_duration(value, unit):
    if value is None or unit is None:
        return "Not configured"

    return f"{value} {unit}"


def format_expiration(value, unit):
    if unit == "never":
        return "Never"

    if value is None or unit is None:
        return "Not configured"

    return f"{value} {unit}"
