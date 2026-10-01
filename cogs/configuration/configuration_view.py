import discord


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

        self.add_item(ConfigSettingSelect(bot, guild_id))

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
        view = ConfigView(self.bot, self.guild_id)

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
        ]

        super().__init__(
            placeholder="Choose a setting...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        setting = self.values[0]

        await interaction.response.send_message(
            f"You selected `{setting}`.",
            ephemeral=True
        )
