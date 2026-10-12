import json

import discord
from discord.ui import Button, Modal, TextInput, View


class RoleDetailsModal(Modal):
    def __init__(self, editor: "RoleEditorView"):
        super().__init__(title="Reaction-Role Details")
        self.editor = editor

        self.emoji_input = TextInput(
            label="Reaction emoji",
            placeholder="🎮",
            default=editor.emoji,
            max_length=100,
            required=True,
        )
        self.description_input = TextInput(
            label="Role description",
            placeholder="Gaming updates and game nights",
            default=editor.description,
            max_length=200,
            required=True,
        )
        self.color_input = TextInput(
            label="Role color (hex)",
            placeholder="#5865F2",
            default=editor.color_hex,
            max_length=7,
            required=False,
        )

        self.add_item(self.emoji_input)
        self.add_item(self.description_input)
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        emoji = self.emoji_input.value.strip()
        description = self.description_input.value.strip()
        color_hex = self.color_input.value.strip()

        if color_hex:
            if color_hex.startswith("#"):
                color_hex = color_hex[1:]

            if len(color_hex) != 6:
                await interaction.response.send_message(
                    "Enter a six-digit hex color, such as `#5865F2`.",
                    ephemeral=True,
                )
                return

            try:
                int(color_hex, 16)
            except ValueError:
                await interaction.response.send_message(
                    "That color isn't valid hex. Example: `#5865F2`.",
                    ephemeral=True,
                )
                return

        self.editor.emoji = emoji
        self.editor.description = description
        self.editor.color_hex = f"#{color_hex}" if color_hex else ""

        await interaction.response.edit_message(
            embed=self.editor.create_embed(),
            view=self.editor,
        )


class CreateRoleModal(Modal):
    def __init__(self, editor: "RoleEditorView"):
        super().__init__(title="Create a Discord Role")
        self.editor = editor

        self.role_name = TextInput(
            label="Role name",
            placeholder="Gaming Updates",
            max_length=100,
            required=True,
        )
        self.add_item(self.role_name)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This must be used in a server.",
                ephemeral=True,
            )
            return

        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "Ratburn needs the **Manage Roles** permission.",
                ephemeral=True,
            )
            return

        try:
            role = await interaction.guild.create_role(
                name=self.role_name.value.strip(),
                reason="Created through Ratburn's reaction-role editor",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord wouldn't let Ratburn create that role. "
                "Check its permissions and role hierarchy.",
                ephemeral=True,
            )
            return

        self.editor.role_id = role.id

        await interaction.response.send_message(
            f"Created {role.mention}. You can now configure and save it.",
            embed=self.editor.create_embed(),
            view=self.editor,
            ephemeral=True,
        )


class RoleEditorView(View):

    PERMISSION_PRESETS = {
        "none": "No permission changes",
        "view": "Allow viewing the channel",
        "participate": "View, send messages, and add reactions",
        "read_only": "View channel without sending messages",
        "hidden": "Hide the channel from this role",
    }

    def __init__(
        self,
        bot: discord.Client,
        guild_id: int,
        post_id: int,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id

        self.role_id: int | None = None
        self.channel_id: int | None = None
        self.permission_preset = "none"

        self.emoji = "🎮"
        self.description = "Gaming updates"
        self.color_hex = ""

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎭 Reaction-Role Entry",
            description=(
                "Configure one role that members can obtain by reacting "
                "to the published post."
            ),
            color=discord.Color.dark_teal(),
        )

        guild = self.bot.get_guild(self.guild_id)
        role = guild.get_role(self.role_id) if guild and self.role_id else None

        embed.add_field(
            name="Role",
            value=role.mention if role else "Not selected",
            inline=True,
        )
        embed.add_field(
            name="Emoji",
            value=self.emoji,
            inline=True,
        )
        embed.add_field(
            name="Description",
            value=self.description or "None",
            inline=False,
        )
        embed.add_field(
            name="Color",
            value=self.color_hex or "Keep the current color",
            inline=True,
        )

        channel = (
            guild.get_channel(self.channel_id)
            if guild and self.channel_id
            else None
        )
        embed.add_field(
            name="Permission channel",
            value=channel.mention if channel else "None selected",
            inline=True,
        )
        embed.add_field(
            name="Permission preset",
            value=self.PERMISSION_PRESETS[self.permission_preset],
            inline=False,
        )
        embed.set_footer(text=f"Reaction-role post ID: {self.post_id}")
        return embed

    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="Select an existing role",
        min_values=1,
        max_values=1,
        row=0,
    )
    async def select_role(
        self,
        interaction: discord.Interaction,
        select: discord.ui.RoleSelect,
    ):
        self.role_id = select.values[0].id

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Select a channel for permission changes",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1,
        row=1,
    )
    async def select_channel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect,
    ):
        channel = select.values[0]

        if channel.guild.id != self.guild_id:
            await interaction.response.send_message(
                "Choose a channel from this server.",
                ephemeral=True,
            )
            return

        self.channel_id = channel.id

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.select(
        placeholder="Choose a channel-permission preset",
        options=[
            discord.SelectOption(
                label="No permission changes",
                value="none",
            ),
            discord.SelectOption(
                label="Allow viewing",
                value="view",
            ),
            discord.SelectOption(
                label="Participate in chat",
                value="participate",
            ),
            discord.SelectOption(
                label="Read only",
                value="read_only",
            ),
            discord.SelectOption(
                label="Hide channel",
                value="hidden",
            ),
        ],
        min_values=1,
        max_values=1,
        row=2,
    )
    async def select_permission_preset(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select,
    ):
        self.permission_preset = select.values[0]

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Edit details",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=3,
    )
    async def edit_details(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await interaction.response.send_modal(RoleDetailsModal(self))

    @discord.ui.button(
        label="Create role",
        style=discord.ButtonStyle.secondary,
        emoji="➕",
        row=3,
    )
    async def create_role(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await interaction.response.send_modal(CreateRoleModal(self))

    @discord.ui.button(
        label="Save role entry",
        style=discord.ButtonStyle.success,
        emoji="💾",
        row=4,
    )
    async def save_entry(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        guild = interaction.guild

        if guild is None or guild.id != self.guild_id:
            await interaction.response.send_message(
                "This entry belongs to a different server.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "You need **Manage Roles** to save reaction-role entries.",
                ephemeral=True,
            )
            return

        if self.role_id is None:
            await interaction.response.send_message(
                "Select or create a role first.",
                ephemeral=True,
            )
            return

        role = guild.get_role(self.role_id)
        if role is None or role.is_default() or role.managed:
            await interaction.response.send_message(
                "That role is unavailable or cannot be assigned by Ratburn.",
                ephemeral=True,
            )
            return

        if role >= guild.me.top_role:
            await interaction.response.send_message(
                "Ratburn's highest role must be above the role it manages.",
                ephemeral=True,
            )
            return

        if self.permission_preset != "none" and self.channel_id is None:
            await interaction.response.send_message(
                "Choose a channel before applying a permission preset.",
                ephemeral=True,
            )
            return

        if self.color_hex:
            try:
                await role.edit(
                    colour=discord.Colour(
                        int(self.color_hex.lstrip("#"), 16)
                    ),
                    reason="Updated through Ratburn's reaction-role editor",
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "Ratburn cannot change that role's color. "
                    "Check its role hierarchy and Manage Roles permission.",
                    ephemeral=True,
                )
                return

        permission_data = None

        if self.permission_preset != "none":
            channel = guild.get_channel(self.channel_id)

            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "The selected channel is no longer available.",
                    ephemeral=True,
                )
                return

            overwrite = channel.overwrites_for(role)

            if self.permission_preset == "hidden":
                overwrite.view_channel = False
            else:
                overwrite.view_channel = True

                if self.permission_preset == "participate":
                    overwrite.send_messages = True
                    overwrite.add_reactions = True
                elif self.permission_preset == "read_only":
                    overwrite.send_messages = False
                    overwrite.add_reactions = False
                elif self.permission_preset == "view":
                    # Leave other permissions unchanged.
                    pass

            try:
                await channel.set_permissions(
                    role,
                    overwrite=overwrite,
                    reason="Configured through Ratburn's reaction-role editor",
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "Ratburn cannot change permissions in that channel. "
                    "Check its Manage Channels permission.",
                    ephemeral=True,
                )
                return

            permission_data = json.dumps({
                "channel_id": channel.id,
                "preset": self.permission_preset,
            })

        existing = self.bot.database.get_reaction_role_entry_by_role(
            self.post_id,
            role.id,
        )

        try:
            if existing:
                entry_id = existing["id"]
                self.bot.database.update_reaction_role_entry(
                    entry_id, "emoji", self.emoji
                )
                self.bot.database.update_reaction_role_entry(
                    entry_id, "description", self.description
                )
                self.bot.database.update_reaction_role_entry(
                    entry_id, "role_color",
                    int(self.color_hex.lstrip("#"), 16)
                    if self.color_hex else None,
                )
                self.bot.database.update_reaction_role_entry(
                    entry_id, "channel_permissions", permission_data
                )
            else:
                self.bot.database.add_reaction_role_entry(
                    post_id=self.post_id,
                    role_id=role.id,
                    emoji=self.emoji,
                    description=self.description,
                    role_color=(
                        int(self.color_hex.lstrip("#"), 16)
                        if self.color_hex else None
                    ),
                    channel_permissions=permission_data,
                )
        except Exception as exc:
            await interaction.response.send_message(
                f"Couldn't save the entry: `{type(exc).__name__}`. "
                "Check Ratburn's logs for details.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Saved **{role.name}** with reaction {self.emoji}.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Done",
        style=discord.ButtonStyle.secondary,
        emoji="✔️",
        row=4,
    )
    async def done(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await interaction.response.edit_message(
            content="Role editor closed.",
            embed=None,
            view=None,
        )
        self.stop()
