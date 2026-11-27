import sqlite3

import discord


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
            title="Configure Reaction Roles",
            description=(
                "Select an existing server role to add to this "
                "reaction-role post.\n\n"
                "Roles must already exist in your server before "
                "they can be added here."
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
            text="Adding a role here won't change its server settings."
        )

        return embed

    @discord.ui.button(
        label="Add an existing role",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def add_existing_role(self, interaction, button):
        if interaction.guild is None:
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

        emoji = self.emoji_input.value.strip()

        if not emoji:
            await interaction.response.send_message(
                "A reaction emoji is required.",
                ephemeral=True,
            )
            return

        self.editor.emoji = emoji
        self.editor.description = self.description_input.value.strip()
        self.editor.role_color = color
        self.editor.role_icon = (
            self.icon_input.value.strip() or None
        )

        await interaction.response.send_message(
            "Entry details updated in the editor. "
            "Click **Add role** to save them to the database.",
            ephemeral=True,
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
