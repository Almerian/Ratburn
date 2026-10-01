import discord

#===========================================================================

TIMEZONE_OPTIONS = [
    ("UTC-12:00", "International Date Line West", "Etc/GMT+12"),
    ("UTC-11:00", "Samoa, Midway Islands", "Pacific/Pago_Pago"),
    ("UTC-10:00", "Hawaii, Cook Islands", "Pacific/Honolulu"),
    ("UTC-09:00", "Alaska", "America/Anchorage"),
    ("UTC-08:00", "Pacific Standard Time (US & Canada)", "America/Los_Angeles"),
    ("UTC-07:00", "Mountain Standard Time (US & Canada)", "America/Denver"),
    ("UTC-06:00", "Central Standard Time (US & Canada), Central America", "America/Chicago"),
    ("UTC-05:00", "Eastern Standard Time (US & Canada), Colombia, Peru", "America/New_York"),
    ("UTC-04:00", "Atlantic Standard Time, Bolivia, Chile (Standard)", "America/Halifax"),
    ("UTC-03:00", "Argentina, Brazil (East), Greenland", "America/Argentina/Buenos_Aires"),
    ("UTC-02:00", "South Georgia & the South Sandwich Islands", "Atlantic/South_Georgia"),
    ("UTC-01:00", "Azores, Cabo Verde", "Atlantic/Azores"),
    ("UTC±00:00", "Greenwich Mean Time (GMT), Western Europe, UK", "Europe/London"),
    ("UTC+01:00", "Central European Time, West Africa", "Europe/Berlin"),
    ("UTC+02:00", "Eastern European Time, Central Africa", "Europe/Bucharest"),
    ("UTC+03:00", "Moscow Standard Time, East Africa, Arabia", "Europe/Moscow"),
    ("UTC+04:00", "Gulf Standard Time, Mauritius", "Asia/Dubai"),
    ("UTC+05:00", "Pakistan Standard Time, Uzbekistan", "Asia/Karachi"),
    ("UTC+06:00", "Bangladesh Standard Time, Kazakhstan (East)", "Asia/Dhaka"),
    ("UTC+07:00", "Indochina Time, Western Indonesia", "Asia/Bangkok"),
    ("UTC+08:00", "China Standard Time, Western Australia, Singapore", "Asia/Shanghai"),
    ("UTC+09:00", "Japan Standard Time, Korea Standard Time", "Asia/Tokyo"),
    ("UTC+10:00", "Australian Eastern Standard Time, Papua New Guinea", "Australia/Sydney"),
    ("UTC+11:00", "Solomon Islands, Vanuatu", "Pacific/Guadalcanal"),
    ("UTC+12:00", "Fiji, New Zealand (Standard)", "Pacific/Auckland"),
]

#===========================================================================

class ConfigView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

    def build_embed(self):
        config = self.bot.database.get_config(self.guild_id)

        def role_value(role_id):
            if not role_id:
                return "🔴 Not configured"

            return f"🟢 <@&{role_id}>"

        def channel_value(channel_id):
            if not channel_id:
                return "🔴 Not configured"

            return f"🟢 <#{channel_id}>"

        embed = discord.Embed(
            title="🐀 Ratburn Configuration",
            description="Current server configuration."
        )

        embed.add_field(
            name="Staff Role",
            value=role_value(config["staff_role_id"]),
            inline=True
        )

        embed.add_field(
            name="Detention Role",
            value=role_value(config["detention_role_id"]),
            inline=True
        )

        embed.add_field(
            name="Detention Channel",
            value=channel_value(config["detention_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Rat-Trap",
            value=channel_value(config["rat_trap_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Welcome Channel",
            value=(
                f"🟢 <#{config['welcome_channel_id']}>"
                if config["welcome_channel_id"]
                else "🔴 Not configured"
            ),
            inline=True
        )

        embed.add_field(
            name="Birthday Channel",
            value=channel_value(config["birthday_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Event Channel",
            value=channel_value(config["event_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Audit Log Channel",
            value=channel_value(config["audit_log_channel_id"]),
            inline=True
        )

        embed.add_field(
            name="Timezone",
            value=(
                f"🟢 {config['timezone']}"
                if config["timezone"]
                else "🔴 Not configured"
            ),
            inline=True
        )

        embed.add_field(
            name="Rules Message",
            value=(
                "🟢 Configured"
                if config["rules_message_id"]
                else "🔴 Not configured"
            ),
            inline=True
        )

        return embed

    @discord.ui.button(
        label="Edit Config?",
        emoji="✏️",
        style=discord.ButtonStyle.primary
    )
    async def edit_config(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=ConfigEditView(
                self.bot,
                self.guild_id
            )
        )


class ConfigEditView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            ConfigSettingSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )


class ConfigSettingSelect(discord.ui.Select):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

        options = [
            discord.SelectOption(
                label="Staff Role",
                value="staff_role_id",
                emoji="👥"
            ),
            discord.SelectOption(
                label="Detention Role",
                value="detention_role_id",
                emoji="🚨"
            ),
            discord.SelectOption(
                label="Detention Channel",
                value="detention_channel_id",
                emoji="🔒"
            ),
            discord.SelectOption(
                label="Rat-Trap Channel",
                value="rat_trap_channel_id",
                emoji="🐀"
            ),
            discord.SelectOption(
                label="Welcome Channel",
                value="welcome_channel_id",
                emoji="👋"
            ),
            discord.SelectOption(
                label="Birthday Channel",
                value="birthday_channel_id",
                emoji="🎂"
            ),
            discord.SelectOption(
                label="Event Channel",
                value="event_channel_id",
                emoji="📅"
            ),
            discord.SelectOption(
                label="Audit Log Channel",
                value="audit_log_channel_id",
                emoji="📋"
            ),
            discord.SelectOption(
                label="Timezone",
                value="timezone",
                emoji="🌎"
            ),
            discord.SelectOption(
                label="Rules Message",
                value="rules_message",
                emoji="📜"
            ),
        ]

        super().__init__(
            placeholder="Choose a setting...",
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        setting = self.values[0]

        if setting == "staff_role_id":
            view = StaffRoleView(
                self.bot,
                self.guild_id
            )

            await interaction.response.edit_message(
                content="**Choose the staff role Ratburn should use.**",
                embed=None,
                view=view
            )
            return

        if setting == "detention_role_id":
            view = DetentionRoleView(
                self.bot,
                self.guild_id
            )
        
            await interaction.response.edit_message(
                content="**Choose the detention role Ratburn should use.**",
                embed=None,
                view=view
            )
            return


        if setting == "detention_channel_id":
            view = DetentionChannelView(
                self.bot,
                self.guild_id
            )
        
            await interaction.response.edit_message(
                content="**Choose the channel Ratburn should use for detention.**",
                embed=None,
                view=view
            )
            return


        if setting == "rat_trap_channel_id":
            view = RatTrapChannelView(
                self.bot,
                self.guild_id
            )
        
            await interaction.response.edit_message(
                content="**Choose the channel Ratburn should use as the Rat-Trap.**",
                embed=None,
                view=view
            )
            return


        if setting == "welcome_channel_id":
            view = WelcomeChannelView(self.bot, self.guild_id)
        
            await interaction.response.edit_message(
                content="**Choose the channel where Ratburn will welcome new members.**",
                embed=None,
                view=view
            )
            return


        if setting == "birthday_channel_id":
            view = BirthdayChannelView(
                self.bot,
                self.guild_id
            )
        
            await interaction.response.edit_message(
                content="**Choose the channel Ratburn should use for birthday announcements.**",
                embed=None,
                view=view
            )
            return
        
        if setting == "event_channel_id":
            view = EventChannelView(
                self.bot,
                self.guild_id
            )
        
            await interaction.response.edit_message(
                content="**Choose the channel Ratburn should use for events and reminders.**",
                embed=None,
                view=view
            )
            return
        
        if setting == "audit_log_channel_id":
            view = AuditLogChannelView(
                self.bot,
                self.guild_id
            )
        
            await interaction.response.edit_message(
                content="**Choose the channel Ratburn should use for audit logs.**",
                embed=None,
                view=view
            )
            return


        if setting == "timezone":
            view = TimezoneView(self.bot, self.guild_id)
        
            await interaction.response.edit_message(
                content="**Choose the timezone used by this server.**",
                embed=None,
                view=view
            )
            return

        if setting == "rules_message":
            view = RulesMessageView(
                self.bot,
                self.guild_id
            )

            await interaction.response.edit_message(
                content=(
                    "**Choose the rules message Ratburn should use.**"
                ),
                embed=None,
                view=view
            )
            return

        await interaction.response.send_message(
            f"`{setting}` is not implemented yet.",
            ephemeral=True
        )


class TimezoneSelect(discord.ui.Select):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_timezone = None

        options = []

        for offset, description, timezone in TIMEZONE_OPTIONS:
            options.append(
                discord.SelectOption(
                    label=offset,
                    description=description,
                    value=timezone
                )
            )

        current_config = self.bot.database.get_config(guild_id)
        current_timezone = current_config["timezone"]

        for option in options:
            if option.value == current_timezone:
                option.default = True
                self.selected_timezone = current_timezone

        super().__init__(
            placeholder="Choose a timezone...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.selected_timezone = self.values[0]

        selected_option = next(
            option
            for option in self.options
            if option.value == self.selected_timezone
        )

        await interaction.response.edit_message(
            content=(
                f"**Timezone selected:** "
                f"{selected_option.label} — {selected_option.description}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class TimezoneView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(TimezoneSelect(bot, guild_id))

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, TimezoneSelect):
            return

        if select.selected_timezone is None:
            await interaction.response.send_message(
                "Please choose a timezone first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "timezone",
            select.selected_timezone
        )

        view = ConfigView(self.bot, self.guild_id)

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(self.bot, self.guild_id)

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class StaffRoleView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            StaffRoleSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, StaffRoleSelect):
            return

        if select.selected_role_id is None:
            await interaction.response.send_message(
                "Please choose a role first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "staff_role_id",
            select.selected_role_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class StaffRoleSelect(discord.ui.RoleSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_role_id = None

        super().__init__(
            placeholder="Choose a staff role...",
            min_values=1,
            max_values=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_role_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Staff role selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class DetentionRoleView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            DetentionRoleSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, DetentionRoleSelect):
            return

        if select.selected_role_id is None:
            await interaction.response.send_message(
                "Please choose a role first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "detention_role_id",
            select.selected_role_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class DetentionRoleSelect(discord.ui.RoleSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_role_id = None

        super().__init__(
            placeholder="Choose a detention role...",
            min_values=1,
            max_values=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_role_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Detention role selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class DetentionChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            DetentionChannelSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, DetentionChannelSelect):
            return

        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "detention_channel_id",
            select.selected_channel_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class DetentionChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_channel_id = None

        super().__init__(
            placeholder="Choose a detention channel...",
            min_values=1,
            max_values=1,
            channel_types=[
                discord.ChannelType.text
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_channel_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Detention channel selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class RatTrapChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            RatTrapChannelSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, RatTrapChannelSelect):
            return

        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "rat_trap_channel_id",
            select.selected_channel_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class RatTrapChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_channel_id = None

        super().__init__(
            placeholder="Choose the Rat-Trap channel...",
            min_values=1,
            max_values=1,
            channel_types=[
                discord.ChannelType.text
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_channel_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Rat-Trap channel selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class WelcomeChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(WelcomeChannelSelect(bot, guild_id))

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(self.bot, self.guild_id)

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class WelcomeChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

        super().__init__(
            placeholder="Choose the welcome channel...",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]

        self.bot.database.set_config(
            self.guild_id,
            "welcome_channel_id",
            channel.id
        )

        view = ConfigView(self.bot, self.guild_id)

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )


class BirthdayChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            BirthdayChannelSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, BirthdayChannelSelect):
            return

        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "birthday_channel_id",
            select.selected_channel_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class BirthdayChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_channel_id = None

        super().__init__(
            placeholder="Choose the birthday channel...",
            min_values=1,
            max_values=1,
            channel_types=[
                discord.ChannelType.text
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_channel_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Birthday channel selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class EventChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            EventChannelSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, EventChannelSelect):
            return

        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "event_channel_id",
            select.selected_channel_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class EventChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_channel_id = None

        super().__init__(
            placeholder="Choose the event channel...",
            min_values=1,
            max_values=1,
            channel_types=[
                discord.ChannelType.text
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_channel_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Event channel selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class AuditLogChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

        self.add_item(
            AuditLogChannelSelect(
                bot,
                guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = self.children[0]

        if not isinstance(select, AuditLogChannelSelect):
            return

        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "audit_log_channel_id",
            select.selected_channel_id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class AuditLogChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.selected_channel_id = None

        super().__init__(
            placeholder="Choose the audit log channel...",
            min_values=1,
            max_values=1,
            channel_types=[
                discord.ChannelType.text
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        self.selected_channel_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Audit log channel selected:** "
                f"{self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            view=self.view
        )


class RulesMessageView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(
        label="Enter Rules Message",
        emoji="📜",
        style=discord.ButtonStyle.primary
    )
    async def enter_rules_message(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            RulesMessageModal(
                self.bot,
                self.guild_id
            )
        )

    @discord.ui.button(
        label="Back",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )


class RulesMessageModal(
    discord.ui.Modal,
    title="Rules Message"
):
    message_link = discord.ui.TextInput(
        label="Discord message link",
        placeholder="https://discord.com/channels/...",
        required=True,
        max_length=200
    )

    def __init__(self, bot, guild_id: int):
        super().__init__()

        self.bot = bot
        self.guild_id = guild_id

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        link = self.message_link.value.strip()

        parts = link.rstrip("/").split("/")

        if len(parts) < 3:
            await interaction.response.send_message(
                "That doesn't look like a valid Discord message link.",
                ephemeral=True
            )
            return

        try:
            message_id = int(parts[-1])
            channel_id = int(parts[-2])
            guild_id = int(parts[-3])
        except ValueError:
            await interaction.response.send_message(
                "That doesn't look like a valid Discord message link.",
                ephemeral=True
            )
            return

        if guild_id != self.guild_id:
            await interaction.response.send_message(
                "That message belongs to a different server.",
                ephemeral=True
            )
            return

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "I couldn't determine which server this is.",
                ephemeral=True
            )
            return

        channel = guild.get_channel(channel_id)

        if channel is None:
            await interaction.response.send_message(
                "I couldn't find that channel in this server.",
                ephemeral=True
            )
            return

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await interaction.response.send_message(
                "I couldn't find that message.",
                ephemeral=True
            )
            return
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to read that message.",
                ephemeral=True
            )
            return
        except discord.HTTPException:
            await interaction.response.send_message(
                "Something went wrong while checking that message.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "rules_channel_id",
            channel.id
        )

        self.bot.database.set_config(
            self.guild_id,
            "rules_message_id",
            message.id
        )

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
        )
