
import json
import sqlite3

import discord

from cogs.reaction_roles.views.publishing import (
    publish_reaction_role_post,
)


PERMISSION_PRESETS = {
    "view": "View channels",
    "participate": "View and participate",
    "read_only": "View only",
    "hidden": "Hide channels",
}

CHANNEL_TYPES = [
    discord.ChannelType.text,
    discord.ChannelType.news,
    discord.ChannelType.voice,
    discord.ChannelType.stage_voice,
    discord.ChannelType.forum,
    discord.ChannelType.category,
]

ROLE_ICON_LIMIT = 100


def get_database(bot):
    database = getattr(bot, "db", None)
    if database is None:
        database = getattr(bot, "database", None)

    if database is None:
        raise RuntimeError(
            "Ratburn's database instance was not found on the bot."
        )

    return database


def parse_color(value):
    value = (value or "").strip()

    if not value:
        return None

    value = value.removeprefix("#")

    if len(value) != 6:
        raise ValueError("Color must be a six-digit hexadecimal value.")

    try:
        color_value = int(value, 16)
    except ValueError as exc:
        raise ValueError(
            "Color must contain only hexadecimal digits."
        ) from exc

    return color_value


def format_color(color):
    if color is None:
        return "Use the server role's color"

    return f"#{color:06X}"


def get_role_icon(role):
    icon = getattr(role, "display_icon", None)

    if icon is None:
        return None

    if isinstance(icon, str):
        return icon

    return getattr(icon, "url", None)


def describe_role_permissions(role):
    permissions = role.permissions

    labels = []

    permission_labels = [
        ("administrator", "Administrator"),
        ("manage_guild", "Manage server"),
        ("manage_roles", "Manage roles"),
        ("manage_channels", "Manage channels"),
        ("manage_messages", "Manage messages"),
        ("kick_members", "Kick members"),
        ("ban_members", "Ban members"),
        ("moderate_members", "Timeout members"),
        ("view_audit_log", "View audit log"),
        ("mention_everyone", "Mention everyone"),
        ("manage_webhooks", "Manage webhooks"),
    ]

    for attribute, label in permission_labels:
        if getattr(permissions, attribute, False):
            labels.append(label)

    if not labels:
        return "No elevated server permissions"

    return ", ".join(labels)


def decode_channel_permissions(value):
    if not value:
        return {"version": 2, "channels": []}

    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {"version": 2, "channels": []}

    if isinstance(data, dict) and isinstance(data.get("channels"), list):
        return {
            "version": 2,
            "channels": data["channels"],
        }

    if isinstance(data, dict) and data.get("channel_id"):
        return {
            "version": 2,
            "channels": [
                {
                    "channel_id": data["channel_id"],
                    "preset": data.get("preset", "view"),
                }
            ],
        }

    return {"version": 2, "channels": []}


def encode_channel_permissions(channels):
    return json.dumps({
        "version": 2,
        "channels": channels,
    })


def build_overwrite(preset):
    if preset == "view":
        return {
            "view_channel": True,
        }

    if preset == "participate":
        return {
            "view_channel": True,
            "send_messages": True,
            "read_message_history": True,
            "connect": True,
            "speak": True,
        }

    if preset == "read_only":
        return {
            "view_channel": True,
            "send_messages": False,
            "add_reactions": False,
            "create_public_threads": False,
            "create_private_threads": False,
            "send_messages_in_threads": False,
        }

    if preset == "hidden":
        return {
            "view_channel": False,
        }

    raise ValueError("Unknown channel permission preset.")


def permission_summary(channels):
    if not channels:
        return "No channel permission changes"

    counts = {}

    for item in channels:
        preset = item.get("preset", "view")
        counts[preset] = counts.get(preset, 0) + 1

    parts = []

    for preset, count in counts.items():
        label = PERMISSION_PRESETS.get(preset, preset)
        parts.append(f"{label}: {count}")

    return ", ".join(parts)


class RoleEditorView(discord.ui.View):
    def __init__(self, bot, guild_id, post_id):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id

    async def make_embed(self):
        database = get_database(self.bot)
        post = database.get_reaction_role_post(self.post_id)
        entries = database.get_reaction_role_entries(self.post_id)

        embed = discord.Embed(
            title="Configure a Role",
            description=(
                "Choose whether to add an existing server role or create "
                "a new one for this reaction-role post."
            ),
            color=discord.Color.blurple(),
        )

        if post:
            embed.add_field(
                name="Post",
                value=post["title"],
                inline=False,
            )

        if entries:
            embed.add_field(
                name="Roles already on this post",
                value=str(len(entries)),
                inline=True,
            )

        embed.set_footer(
            text="Adding an existing role won't change the server role."
        )

        return embed

    @discord.ui.button(
        label="Add an existing role",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def add_existing_role(self, interaction, button):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "This action must be used inside a server.",
                ephemeral=True,
            )
            return

        view = ExistingRoleSelectView(
            self.bot,
            self.guild_id,
            self.post_id,
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="Choose an Existing Role",
                description=(
                    "Select a role to add to this post. Its current "
                    "server color, icon, and permissions will be shown "
                    "before you save."
                ),
                color=discord.Color.blurple(),
            ),
            view=view,
        )

    @discord.ui.button(
        label="Add a new role",
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def add_new_role(self, interaction, button):
        await interaction.response.send_modal(
            NewRoleDetailsModal(
                self.bot,
                self.guild_id,
                self.post_id,
            )
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back(self, interaction, button):
        from cogs.reaction_roles.views.manage_posts import (
            ManagePostsView,
        )

        view = ManagePostsView(
            self.bot,
            self.guild_id,
        )

        await view.reload_posts()

        await interaction.response.edit_message(
            embed=await view.make_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Done",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def done(self, interaction, button):
        await interaction.response.edit_message(
            content="Role configuration closed.",
            embed=None,
            view=None,
        )


class ExistingRoleSelectView(discord.ui.View):
    def __init__(self, bot, guild_id, post_id):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id

        self.add_item(ExistingRoleSelect(self))

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back(self, interaction, button):
        view = RoleEditorView(
            self.bot,
            self.guild_id,
            self.post_id,
        )

        await interaction.response.edit_message(
            embed=await view.make_embed(),
            view=view,
        )


class ExistingRoleSelect(discord.ui.RoleSelect):
    def __init__(self, parent_view):
        self.parent_view = parent_view

        super().__init__(
            placeholder="Select a server role",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction):
        role = self.values[0]

        database = get_database(self.parent_view.bot)
        existing = database.get_reaction_role_entry_by_role(
            self.parent_view.post_id,
            role.id,
        )

        if existing:
            emoji = existing["emoji"]
            description = existing["description"]
            color = existing["role_color"]
            role_icon = (
                existing["role_icon"]
                if "role_icon" in existing.keys()
                else None
            )
        else:
            emoji = "🎮"
            description = ""
            color = None
            role_icon = get_role_icon(role)

        editor = ExistingRoleEntryView(
            self.parent_view.bot,
            self.parent_view.guild_id,
            self.parent_view.post_id,
            role.id,
            emoji=emoji,
            description=description,
            role_color=color,
            role_icon=role_icon,
        )

        await interaction.response.edit_message(
            embed=await editor.make_embed(interaction.guild),
            view=editor,
        )


class ExistingRoleEntryView(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id,
        post_id,
        role_id,
        emoji="🎮",
        description="",
        role_color=None,
        role_icon=None,
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id
        self.role_id = role_id
        self.emoji = emoji
        self.description = description
        self.role_color = role_color
        self.role_icon = role_icon

    async def make_embed(self, guild):
        role = guild.get_role(self.role_id) if guild else None

        embed = discord.Embed(
            title="Add Existing Role",
            description=(
                "Review the role's current server settings. Appearance "
                "overrides below affect this reaction-role entry only."
            ),
            color=(
                discord.Color(self.role_color)
                if self.role_color is not None
                else (
                    role.color
                    if role and role.color.value
                    else discord.Color.blurple()
                )
            ),
        )

        embed.add_field(
            name="Role",
            value=role.mention if role else f"Deleted role ({self.role_id})",
            inline=False,
        )

        embed.add_field(
            name="Server role color",
            value=format_color(role.color.value if role else None),
            inline=True,
        )

        embed.add_field(
            name="Entry color override",
            value=format_color(self.role_color),
            inline=True,
        )

        embed.add_field(
            name="Server permissions",
            value=(
                describe_role_permissions(role)
                if role
                else "Role unavailable"
            ),
            inline=False,
        )

        icon = get_role_icon(role) if role else None
        embed.add_field(
            name="Server role icon",
            value=str(icon) if icon else "No icon",
            inline=True,
        )

        embed.add_field(
            name="Post icon",
            value=self.role_icon or "Use server role icon",
            inline=True,
        )

        embed.add_field(
            name="Reaction emoji",
            value=self.emoji,
            inline=True,
        )

        embed.add_field(
            name="Description",
            value=self.description or "No description",
            inline=False,
        )

        return embed

    @discord.ui.button(
        label="Edit entry details",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def edit_details(self, interaction, button):
        await interaction.response.send_modal(
            ExistingRoleEntryModal(self)
        )

    @discord.ui.button(
        label="Add role",
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def save_entry(self, interaction, button):
        await save_role_entry(
            interaction,
            self.bot,
            self.guild_id,
            self.post_id,
            self.role_id,
            self.emoji,
            self.description,
            self.role_color,
            self.role_icon,
            None,
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back(self, interaction, button):
        view = RoleEditorView(
            self.bot,
            self.guild_id,
            self.post_id,
        )

        await interaction.response.edit_message(
            embed=await view.make_embed(),
            view=view,
        )


class ExistingRoleEntryModal(discord.ui.Modal):
    def __init__(self, editor):
        super().__init__(title="Edit Reaction-Role Entry")

        self.editor = editor

        self.emoji_input = discord.ui.TextInput(
            label="Reaction emoji",
            default=editor.emoji,
            max_length=100,
            required=True,
        )

        self.description_input = discord.ui.TextInput(
            label="Description",
            default=editor.description or "",
            max_length=100,
            required=False,
            style=discord.TextStyle.paragraph,
        )

        self.color_input = discord.ui.TextInput(
            label="Post color override (hex, optional)",
            default=(
                f"{editor.role_color:06X}"
                if editor.role_color is not None
                else ""
            ),
            placeholder="Leave blank to use the server role color",
            max_length=7,
            required=False,
        )

        self.icon_input = discord.ui.TextInput(
            label="Post icon override (optional)",
            default=editor.role_icon or "",
            placeholder="Emoji or image URL",
            max_length=ROLE_ICON_LIMIT,
            required=False,
        )

        self.add_item(self.emoji_input)
        self.add_item(self.description_input)
        self.add_item(self.color_input)
        self.add_item(self.icon_input)

    async def on_submit(self, interaction):
        try:
            color = parse_color(self.color_input.value)
        except ValueError as exc:
            await interaction.response.send_message(
                str(exc),
                ephemeral=True,
            )
            return

        self.editor.emoji = self.emoji_input.value.strip()
        self.editor.description = self.description_input.value.strip()
        self.editor.role_color = color
        self.editor.role_icon = self.icon_input.value.strip() or None

        await interaction.response.edit_message(
            embed=await self.editor.make_embed(interaction.guild),
            view=self.editor,
        )


class NewRoleDetailsModal(discord.ui.Modal):
    def __init__(self, bot, guild_id, post_id):
        super().__init__(title="Create a New Role")

        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id

        self.name_input = discord.ui.TextInput(
            label="Role name",
            max_length=100,
            required=True,
        )

        self.description_input = discord.ui.TextInput(
            label="Description",
            max_length=100,
            required=False,
            style=discord.TextStyle.paragraph,
        )

        self.icon_input = discord.ui.TextInput(
            label="Role icon (optional emoji)",
            max_length=100,
            required=False,
        )

        self.color_input = discord.ui.TextInput(
            label="Role color (optional hex)",
            placeholder="Example: #5865F2",
            max_length=7,
            required=False,
        )

        self.add_item(self.name_input)
        self.add_item(self.description_input)
        self.add_item(self.icon_input)
        self.add_item(self.color_input)

    async def on_submit(self, interaction):
        try:
            color = parse_color(self.color_input.value)
        except ValueError as exc:
            await interaction.response.send_message(
                str(exc),
                ephemeral=True,
            )
            return

        name = self.name_input.value.strip()

        if not name:
            await interaction.response.send_message(
                "Role name is required.",
                ephemeral=True,
            )
            return

        view = NewRoleTypeView(
            self.bot,
            self.guild_id,
            self.post_id,
            name=name,
            description=self.description_input.value.strip(),
            icon=self.icon_input.value.strip() or None,
            color=color,
        )

        embed = discord.Embed(
            title="How should this role work?",
            description=(
                f"**Role:** {name}\n"
                f"**Description:** {view.description or 'None'}\n"
                f"**Icon:** {view.icon or 'None'}\n"
                f"**Color:** {format_color(color)}\n\n"
                "Choose whether this is a cosmetic role or grants "
                "channel permissions."
            ),
            color=discord.Color.blurple(),
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True,
        )


class NewRoleTypeView(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id,
        post_id,
        name,
        description,
        icon,
        color,
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id
        self.name = name
        self.description = description
        self.icon = icon
        self.color = color

    @discord.ui.button(
        label="Cosmetic role",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def cosmetic(self, interaction, button):
        await create_and_save_role(interaction, self, [])

    @discord.ui.button(
        label="Role with permissions",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def permissions(self, interaction, button):
        view = ChannelPermissionEditorView(
            self.bot,
            self.guild_id,
            self.post_id,
            self.name,
            self.description,
            self.icon,
            self.color,
        )

        await interaction.response.edit_message(
            embed=view.make_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            content="New role creation cancelled. No role was created.",
            embed=None,
            view=None,
        )


class ChannelPermissionEditorView(discord.ui.View):
    def __init__(
        self,
        bot,
        guild_id,
        post_id,
        name,
        description,
        icon,
        color,
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id
        self.post_id = post_id
        self.name = name
        self.description = description
        self.icon = icon
        self.color = color
        self.selected_channels = []
        self.preset = "view"

        self.add_item(ChannelMultiSelect(self))
        self.add_item(ChannelPermissionPresetSelect(self))

    def make_embed(self):
        embed = discord.Embed(
            title="Configure Channel Permissions",
            description=(
                f"**New role:** {self.name}\n\n"
                "Select one or more channels and choose a permission "
                "preset. The selected preset will apply to every "
                "selected channel."
            ),
            color=(
                discord.Color(self.color)
                if self.color is not None
                else discord.Color.blurple()
            ),
        )

        if self.selected_channels:
            channel_lines = [
                f"<#{channel_id}>"
                for channel_id in self.selected_channels
            ]
            selected = "\n".join(channel_lines)
        else:
            selected = "No channels selected"

        embed.add_field(
            name="Selected channels",
            value=selected[:1024],
            inline=False,
        )

        embed.add_field(
            name="Permission preset",
            value=PERMISSION_PRESETS[self.preset],
            inline=False,
        )

        embed.set_footer(
            text="No role or channel permissions are changed until you save."
        )

        return embed

    @discord.ui.button(
        label="Save and Add New Role",
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def save_role(self, interaction, button):
        if not self.selected_channels:
            await interaction.response.send_message(
                "Select at least one channel, or go back and choose "
                "Cosmetic role.",
                ephemeral=True,
            )
            return

        rules = [
            {
                "channel_id": channel_id,
                "preset": self.preset,
            }
            for channel_id in self.selected_channels
        ]

        await create_and_save_role(interaction, self, rules)

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def back(self, interaction, button):
        view = NewRoleTypeView(
            self.bot,
            self.guild_id,
            self.post_id,
            self.name,
            self.description,
            self.icon,
            self.color,
        )

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="How should this role work?",
                description=(
                    f"**Role:** {self.name}\n"
                    "Choose cosmetic or channel permissions."
                ),
                color=discord.Color.blurple(),
            ),
            view=view,
        )


class ChannelMultiSelect(discord.ui.ChannelSelect):
    def __init__(self, editor):
        self.editor = editor

        super().__init__(
            placeholder="Select channels",
            channel_types=CHANNEL_TYPES,
            min_values=1,
            max_values=25,
            row=0,
        )

    async def callback(self, interaction):
        self.editor.selected_channels = [
            channel.id for channel in self.values
        ]

        await interaction.response.edit_message(
            embed=self.editor.make_embed(),
            view=self.editor,
        )


class ChannelPermissionPresetSelect(discord.ui.Select):
    def __init__(self, editor):
        self.editor = editor

        options = [
            discord.SelectOption(
                label=label,
                value=value,
            )
            for value, label in PERMISSION_PRESETS.items()
        ]

        super().__init__(
            placeholder="Choose a permission preset",
            options=options,
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction):
        self.editor.preset = self.values[0]

        await interaction.response.edit_message(
            embed=self.editor.make_embed(),
            view=self.editor,
        )


async def create_and_save_role(interaction, editor, channel_rules):
    guild = interaction.guild

    if guild is None or guild.id != editor.guild_id:
        await interaction.response.send_message(
            "This role must be created in the original server.",
            ephemeral=True,
        )
        return

    bot_member = guild.me

    if bot_member is None or not bot_member.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "Ratburn needs the Manage Roles permission to create this role.",
            ephemeral=True,
        )
        return

    try:
        role = await guild.create_role(
            name=editor.name,
            permissions=discord.Permissions.none(),
            color=discord.Color(editor.color or 0),
            reason="Created through Ratburn reaction-role configuration",
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "Discord refused to create the role. Check Ratburn's "
            "permissions and role hierarchy.",
            ephemeral=True,
        )
        return
    except discord.HTTPException:
        await interaction.response.send_message(
            "Discord couldn't create the role. Please try again.",
            ephemeral=True,
        )
        return

    applied_channels = []

    try:
        if editor.icon:
            try:
                await role.edit(
                    display_icon=editor.icon,
                    reason="Set reaction-role icon",
                )
            except (discord.Forbidden, discord.HTTPException, TypeError):
                raise ValueError(
                    "Discord couldn't set that role icon. The server "
                    "may not support role icons, or the icon may be invalid."
                )

        for rule in channel_rules:
            channel = guild.get_channel(rule["channel_id"])

            if channel is None:
                raise ValueError(
                    "One of the selected channels no longer exists."
                )

            overwrite = build_overwrite(rule["preset"])

            await channel.set_permissions(
                role,
                overwrite=discord.PermissionOverwrite(**overwrite),
                reason="Configured through Ratburn reaction roles",
            )

            applied_channels.append(channel)

        database = get_database(editor.bot)
        existing = database.get_reaction_role_entry_by_role(
            editor.post_id,
            role.id,
        )

        permissions_json = (
            encode_channel_permissions(channel_rules)
            if channel_rules
            else None
        )

        if existing:
            database.update_reaction_role_entry(
                existing["id"],
                "emoji",
                "🎮",
            )
            database.update_reaction_role_entry(
                existing["id"],
                "description",
                editor.description,
            )
            database.update_reaction_role_entry(
                existing["id"],
                "role_color",
                editor.color,
            )
            database.update_reaction_role_entry(
                existing["id"],
                "role_icon",
                editor.icon,
            )
            database.update_reaction_role_entry(
                existing["id"],
                "channel_permissions",
                permissions_json,
            )
        else:
            database.add_reaction_role_entry(
                post_id=editor.post_id,
                role_id=role.id,
                emoji="🎮",
                description=editor.description,
                role_color=editor.color,
                channel_permissions=permissions_json,
                role_icon=editor.icon,
            )

    except (ValueError, discord.Forbidden, discord.HTTPException, sqlite3.Error) as exc:
        for channel in applied_channels:
            try:
                await channel.set_permissions(role, overwrite=None)
            except (discord.Forbidden, discord.HTTPException):
                pass

        try:
            await role.delete(
                reason="Rolling back failed reaction-role setup",
            )
        except (discord.Forbidden, discord.HTTPException):
            pass

        await interaction.response.send_message(
            f"Couldn't finish creating the role: {exc}",
            ephemeral=True,
        )
        return

    await interaction.response.edit_message(
        content=f"Added {role.mention} to the reaction-role post.",
        embed=None,
        view=None,
    )


async def save_role_entry(
    interaction,
    bot,
    guild_id,
    post_id,
    role_id,
    emoji,
    description,
    role_color,
    role_icon,
    channel_permissions,
):
    guild = interaction.guild

    if guild is None or guild.id != guild_id:
        await interaction.response.send_message(
            "This role belongs to a different server.",
            ephemeral=True,
        )
        return

    role = guild.get_role(role_id)

    if role is None:
        await interaction.response.send_message(
            "That server role no longer exists.",
            ephemeral=True,
        )
        return

    if role == guild.default_role or role.managed:
        await interaction.response.send_message(
            "This role can't be used for reaction-role assignment.",
            ephemeral=True,
        )
        return

    database = get_database(bot)

    try:
        existing = database.get_reaction_role_entry_by_role(
            post_id,
            role_id,
        )

        if existing:
            entry_id = existing["id"]

            database.update_reaction_role_entry(
                entry_id, "emoji", emoji
            )
            database.update_reaction_role_entry(
                entry_id, "description", description
            )
            database.update_reaction_role_entry(
                entry_id, "role_color", role_color
            )
            database.update_reaction_role_entry(
                entry_id, "role_icon", role_icon
            )

            if channel_permissions is not None:
                database.update_reaction_role_entry(
                    entry_id,
                    "channel_permissions",
                    channel_permissions,
                )
        else:
            database.add_reaction_role_entry(
                post_id=post_id,
                role_id=role_id,
                emoji=emoji,
                description=description,
                role_color=role_color,
                channel_permissions=channel_permissions,
                role_icon=role_icon,
            )

    except sqlite3.IntegrityError:
        await interaction.response.send_message(
            "That emoji is already used by another role on this post. "
            "Choose a different reaction emoji.",
            ephemeral=True,
        )
        return

    await interaction.response.edit_message(
        content=f"Added {role.mention} to the reaction-role post.",
        embed=None,
        view=None,
    )
