import discord
from datetime import datetime

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
            return f"🟢 <@&{role_id}>" if role_id else "🔴 Not configured"

        def channel_value(channel_id):
            return f"🟢 <#{channel_id}>" if channel_id else "🔴 Not configured"

        timezone = config["timezone"] or "Timezone not configured"
        posting_time = config["icebreaker_posting_time"] or "09:00"

        embed = discord.Embed(
            title="🐀 Ratburn Configuration",
            description="Current server configuration."
        )

        fields = [
            ("Staff Role", role_value(config["staff_role_id"])),
            ("Detention Role", role_value(config["detention_role_id"])),
            ("Detention Channel", channel_value(config["detention_channel_id"])),
            ("Rat-Trap", channel_value(config["rat_trap_channel_id"])),
            ("Welcome Channel", channel_value(config["welcome_channel_id"])),
            ("Birthday Channel", channel_value(config["birthday_channel_id"])),
            ("Event Channel", channel_value(config["event_channel_id"])),
            ("Audit Log Channel", channel_value(config["audit_log_channel_id"])),
            (
                "Timezone",
                f"🟢 {config['timezone']}" if config["timezone"] else "🔴 Not configured"
            ),
            (
                "Rules Message",
                "🟢 Configured" if config["rules_message_id"] else "🔴 Not configured"
            ),
            ("Icebreaker Channel", channel_value(config["icebreaker_channel_id"])),
            (
                "Icebreaker Posting Time",
                f"🟢 {posting_time} ({timezone})"
            ),
            (
                "Daily Icebreaker",
                "🟢 Enabled" if config["icebreaker_enabled"] else "🔴 Disabled"
            ),
        ]

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=True)

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
        view = ConfigEditView(self.bot, self.guild_id)
        await interaction.response.edit_message(
            content="**What would you like to configure?**",
            embed=None,
            view=view
        )

    @discord.ui.button(
        label="Discipline Config",
        emoji="⚖️",
        style=discord.ButtonStyle.primary
    )
    async def discipline_config(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        from cogs.discipline.discipline_config_view import DisciplineConfigView

        view = DisciplineConfigView(self.bot, self.guild_id)
        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view
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
            discord.SelectOption(label="Staff Role", value="staff_role_id", emoji="👥"),
            discord.SelectOption(label="Detention Role", value="detention_role_id", emoji="🚨"),
            discord.SelectOption(label="Detention Channel", value="detention_channel_id", emoji="🔒"),
            discord.SelectOption(label="Rat-Trap Channel", value="rat_trap_channel_id", emoji="🐀"),
            discord.SelectOption(label="Welcome Channel", value="welcome_channel_id", emoji="👋"),
            discord.SelectOption(label="Birthday Channel", value="birthday_channel_id", emoji="🎂"),
            discord.SelectOption(label="Event Channel", value="event_channel_id", emoji="📅"),
            discord.SelectOption(label="Audit Log Channel", value="audit_log_channel_id", emoji="📋"),
            discord.SelectOption(label="Timezone", value="timezone", emoji="🌎"),
            discord.SelectOption(label="Rules Message", value="rules_message", emoji="📜"),
            discord.SelectOption(label="Icebreaker Channel", value="icebreaker_channel_id", emoji="💬"),
            discord.SelectOption(label="Icebreaker Posting Time", value="icebreaker_posting_time", emoji="⏰"),
            discord.SelectOption(label="Icebreaker Enabled/Disabled", value="icebreaker_enabled", emoji="🔔"),
        ]

        super().__init__(
            placeholder="Choose a setting...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        setting = self.values[0]

        view_map = {
            "staff_role_id": (
                StaffRoleView,
                "**Choose the staff role Ratburn should use.**"
            ),
            "detention_role_id": (
                DetentionRoleView,
                "**Choose the detention role Ratburn should use.**"
            ),
            "detention_channel_id": (
                DetentionChannelView,
                "**Choose the channel Ratburn should use for detention.**"
            ),
            "rat_trap_channel_id": (
                RatTrapChannelView,
                "**Choose the channel Ratburn should use as the Rat-Trap.**"
            ),
            "welcome_channel_id": (
                WelcomeChannelView,
                "**Choose the channel where Ratburn will welcome new members.**"
            ),
            "birthday_channel_id": (
                BirthdayChannelView,
                "**Choose the channel Ratburn should use for birthday announcements.**"
            ),
            "event_channel_id": (
                EventChannelView,
                "**Choose the channel Ratburn should use for events and reminders.**"
            ),
            "audit_log_channel_id": (
                AuditLogChannelView,
                "**Choose the channel Ratburn should use for audit logs.**"
            ),
            "timezone": (
                TimezoneView,
                "**Choose the timezone used by this server.**"
            ),
            "rules_message": (
                RulesMessageView,
                "**Choose the rules message Ratburn should use.**"
            ),
            "icebreaker_channel_id": (
                IcebreakerChannelView,
                "**Choose the channel where the daily Icebreaker will be posted.**"
            ),
            "icebreaker_posting_time": (
                IcebreakerPostingTimeView,
                "**Choose when the daily Icebreaker should be posted.**"
            ),
            "icebreaker_enabled": (
                IcebreakerEnabledView,
                "**Enable or disable the daily Icebreaker for this server.**"
            ),
        }

        selected = view_map.get(setting)
        if selected is None:
            await interaction.response.send_message(
                f"`{setting}` is not implemented yet.",
                ephemeral=True
            )
            return

        view_class, message = selected
        view = view_class(self.bot, self.guild_id)

        embed = view.build_embed() if hasattr(view, "build_embed") else None

        await interaction.response.edit_message(
            content=message if embed is None else None,
            embed=embed,
            view=view
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

    async def callback(
        self,
        interaction: discord.Interaction
    ):
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

        self.add_item(
            TimezoneSelect(
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, TimezoneSelect)
            ),
            None
        )

        if select is None:
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, StaffRoleSelect)
            ),
            None
        )

        if select is None:
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, DetentionRoleSelect)
            ),
            None
        )
    
        if select is None:
            return
    
        if select.selected_role_id is None:
            await interaction.response.send_message(
                "Please choose a role first.",
                ephemeral=True
            )
            return
    
        await interaction.response.defer()
    
        old_config = self.bot.database.get_config(
            self.guild_id
        )
    
        old_detention_role = None
    
        if old_config is not None:
            old_role_id = old_config["detention_role_id"]
    
            if old_role_id:
                old_detention_role = interaction.guild.get_role(
                    old_role_id
                )
    
        self.bot.database.set_config(
            self.guild_id,
            "detention_role_id",
            select.selected_role_id
        )
    
        config = self.bot.database.get_config(
            self.guild_id
        )
    
        channel = interaction.guild.get_channel(
            config["detention_channel_id"]
        )
    
        if channel is not None:
            configuration = self.bot.get_cog("Configuration")
    
            if configuration is not None:
                detention_role = interaction.guild.get_role(
                    select.selected_role_id
                )
    
                staff_role = (
                    interaction.guild.get_role(
                        config["staff_role_id"]
                    )
                    if config["staff_role_id"]
                    else None
                )
    
                if detention_role is not None:
                    await configuration.configure_detention_channel(
                        interaction.guild,
                        channel,
                        staff_role,
                        detention_role,
                        old_detention_role
                    )
    
        view = ConfigView(
            self.bot,
            self.guild_id
        )
    
        await interaction.edit_original_response(
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, DetentionChannelSelect)
            ),
            None
        )
    
        if select is None:
            return
    
        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return
    
        await interaction.response.defer()
    
        self.bot.database.set_config(
            self.guild_id,
            "detention_channel_id",
            select.selected_channel_id
        )
    
        config = self.bot.database.get_config(
            self.guild_id
        )
    
        detention_role_id = config["detention_role_id"]
    
        if detention_role_id is not None:
            detention_role = interaction.guild.get_role(
                detention_role_id
            )
    
            detention_channel = interaction.guild.get_channel(
                select.selected_channel_id
            )
    
            staff_role = (
                interaction.guild.get_role(
                    config["staff_role_id"]
                )
                if config["staff_role_id"]
                else None
            )
    
            configuration = self.bot.get_cog("Configuration")
    
            if (
                configuration is not None
                and detention_role is not None
                and detention_channel is not None
            ):
                await configuration.configure_detention_channel(
                    interaction.guild,
                    detention_channel,
                    staff_role,
                    detention_role
                )
    
        view = ConfigView(
            self.bot,
            self.guild_id
        )
    
        await interaction.edit_original_response(
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
                "📢 **This will edit the channel permissions!** "
                "If you change this later, you'll have to manually "
                "reset the permissions for the former Detention channel.\n\n"
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
        label="Create New Channel",
        emoji="➕",
        style=discord.ButtonStyle.primary,
        row=1
    )
    async def create_channel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            RatTrapChannelNameModal(
                self.bot,
                self.guild_id
            )
        )

    @discord.ui.button(
        label="Save",
        emoji="💾",
        style=discord.ButtonStyle.success,
        row=1
    )
    async def save(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, RatTrapChannelSelect)
            ),
            None
        )

        if select is None:
            return

        if select.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first, or create a new one.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "rat_trap_channel_id",
            select.selected_channel_id
        )

        new_member = self.bot.get_cog("NewMember")

        if new_member is not None:
            await new_member.configure_channel_permissions(
                interaction.guild
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
        style=discord.ButtonStyle.secondary,
        row=1
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



class RatTrapChannelNameModal(
    discord.ui.Modal,
    title="Create Rat-Trap Channel"
):
    channel_name = discord.ui.TextInput(
        label="Channel name",
        placeholder="rat-trap",
        required=True,
        min_length=1,
        max_length=100
    )

    def __init__(self, bot, guild_id: int):
        super().__init__()

        self.bot = bot
        self.guild_id = guild_id

    
    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        guild = interaction.guild

        if guild is None or guild.id != self.guild_id:
            await interaction.response.send_message(
                "I couldn't determine which server to use.",
                ephemeral=True
            )
            return

        name = self.channel_name.value.strip()

        if not name:
            await interaction.response.send_message(
                "Please enter a channel name.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            channel = await guild.create_text_channel(
                name=name,
                position=0,
                reason="Ratburn Rat-Trap configuration"
            )

        except discord.Forbidden:
            await interaction.edit_original_response(
                content=(
                    "I couldn't create the channel. Please check "
                    "that Ratburn has the **Manage Channels** permission."
                ),
                embed=None,
                view=None
            )
            return

        except discord.HTTPException:
            await interaction.edit_original_response(
                content=(
                    "Something went wrong while creating the channel. "
                    "Please try again."
                ),
                embed=None,
                view=None
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "rat_trap_channel_id",
            channel.id
        )

        new_member = self.bot.get_cog("NewMember")

        if new_member is not None:
            await new_member.configure_channel_permissions(guild)

        view = ConfigView(
            self.bot,
            self.guild_id
        )

        await interaction.edit_original_response(
            content=(
                f"✅ Created {channel.mention} and saved it as "
                "the Rat-Trap channel."
            ),
            embed=view.build_embed(),
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

        self.add_item(
            WelcomeChannelSelect(
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
        view = ConfigEditView(
            self.bot,
            self.guild_id
        )

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
            channel_types=[
                discord.ChannelType.text
            ],
            min_values=1,
            max_values=1
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        channel = self.values[0]

        self.bot.database.set_config(
            self.guild_id,
            "welcome_channel_id",
            channel.id
        )

        new_member = self.bot.get_cog("NewMember")

        if new_member is not None:
            await new_member.configure_channel_permissions(
                interaction.guild
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, BirthdayChannelSelect)
            ),
            None
        )

        if select is None:
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, EventChannelSelect)
            ),
            None
        )

        if select is None:
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
        select = next(
            (
                child
                for child in self.children
                if isinstance(child, AuditLogChannelSelect)
            ),
            None
        )

        if select is None:
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



class IcebreakerChannelView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.selected_channel_id = None
        self.add_item(IcebreakerChannelSelect())

    def build_embed(self):
        config = self.bot.database.get_config(self.guild_id)
        channel_id = config["icebreaker_channel_id"]

        return discord.Embed(
            title="💬 Icebreaker Channel",
            description=(
                f"Current channel: <#{channel_id}>"
                if channel_id
                else "Current channel: Not configured"
            )
            + "\n\nChoose a text channel, then click **Save**."
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
        if self.selected_channel_id is None:
            await interaction.response.send_message(
                "Please choose a channel first.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "icebreaker_channel_id",
            self.selected_channel_id
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


class IcebreakerChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Choose the Icebreaker channel...",
            min_values=1,
            max_values=1,
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_channel_id = self.values[0].id

        await interaction.response.edit_message(
            content=(
                f"**Icebreaker channel selected:** {self.values[0].mention}\n\n"
                "Click **Save** to apply this change."
            ),
            embed=None,
            view=self.view
        )


class IcebreakerPostingTimeView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

    def build_embed(self):
        config = self.bot.database.get_config(self.guild_id)
        posting_time = config["icebreaker_posting_time"] or "09:00"
        timezone = config["timezone"] or "Timezone not configured"

        return discord.Embed(
            title="⏰ Icebreaker Posting Time",
            description=(
                f"Current posting time: **{posting_time}**\n"
                f"Server timezone: **{timezone}**\n\n"
                "Use 24-hour time in `HH:MM` format, such as `09:00` or `18:30`."
            )
        )

    @discord.ui.button(
        label="Set Posting Time",
        emoji="⏰",
        style=discord.ButtonStyle.primary
    )
    async def set_posting_time(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            IcebreakerPostingTimeModal(self.bot, self.guild_id)
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


class IcebreakerPostingTimeModal(
    discord.ui.Modal,
    title="Icebreaker Posting Time"
):
    posting_time = discord.ui.TextInput(
        label="Posting time (24-hour HH:MM)",
        placeholder="09:00",
        required=True,
        min_length=5,
        max_length=5
    )

    def __init__(self, bot, guild_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        value = self.posting_time.value.strip()

        try:
            parsed_time = datetime.strptime(value, "%H:%M")
        except ValueError:
            await interaction.response.send_message(
                "Invalid time. Please use 24-hour `HH:MM` format, "
                "for example `09:00` or `18:30`.",
                ephemeral=True
            )
            return

        if parsed_time.strftime("%H:%M") != value:
            await interaction.response.send_message(
                "Please enter the time in `HH:MM` format, "
                "for example `09:00` or `18:30`.",
                ephemeral=True
            )
            return

        self.bot.database.set_config(
            self.guild_id,
            "icebreaker_posting_time",
            value
        )

        await interaction.response.send_message(
            f"✅ Icebreaker posting time saved as **{value}**.",
            ephemeral=True
        )


class IcebreakerEnabledView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.update_button()

    def build_embed(self):
        config = self.bot.database.get_config(self.guild_id)
        enabled = bool(config["icebreaker_enabled"])

        return discord.Embed(
            title="🔔 Daily Icebreaker",
            description=(
                "Status: **🟢 Enabled**\n\n"
                "Ratburn will post a daily conversation starter "
                "at the configured time."
                if enabled
                else
                "Status: **🔴 Disabled**\n\n"
                "Daily conversation starters are currently turned off."
            )
        )

    def update_button(self):
        enabled = bool(
            self.bot.database.get_config(self.guild_id)["icebreaker_enabled"]
        )

        button = discord.utils.get(
            self.children,
            custom_id="icebreaker_toggle"
        )

        if button is not None:
            button.label = "Disable Icebreaker" if enabled else "Enable Icebreaker"
            button.style = (
                discord.ButtonStyle.danger
                if enabled
                else discord.ButtonStyle.success
            )

    @discord.ui.button(
        label="Toggle Icebreaker",
        custom_id="icebreaker_toggle",
        style=discord.ButtonStyle.primary
    )
    async def toggle_icebreaker(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = self.bot.database.get_config(self.guild_id)
        currently_enabled = bool(config["icebreaker_enabled"])
        new_value = 0 if currently_enabled else 1

        self.bot.database.set_config(
            self.guild_id,
            "icebreaker_enabled",
            new_value
        )

        self.update_button()

        await interaction.response.edit_message(
            content=None,
            embed=self.build_embed(),
            view=self
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
