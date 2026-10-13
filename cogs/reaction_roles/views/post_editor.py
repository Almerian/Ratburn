import json
import logging

import discord
from discord.ui import Button, Modal, TextInput, View

from cogs.reaction_roles.views.publishing import (
    publish_reaction_role_post,
)

logger = logging.getLogger("ratburn.reaction_roles.editor")


PERMISSION_PRESETS = {
    "none": "No permission changes",
    "view": "Allow viewing the channel",
    "participate": "View, send messages, and add reactions",
    "read_only": "View channel without sending messages",
    "hidden": "Hide the channel from this role",
}

PERMISSION_OPTIONS = [
    discord.SelectOption(label="No permission changes", value="none"),
    discord.SelectOption(label="Allow viewing", value="view"),
    discord.SelectOption(label="Participate in chat", value="participate"),
    discord.SelectOption(label="Read only", value="read_only"),
    discord.SelectOption(label="Hide channel", value="hidden"),
]


def _role_color_value(color_hex: str) -> int | None:
    if not color_hex:
        return None
    return int(color_hex.lstrip("#"), 16)


def _entry_options(bot: discord.Client, guild_id: int, post_id: int | None):
    if post_id is None:
        return [
            discord.SelectOption(
                label="No saved roles yet",
                value="none",
                description="Choose Add Role to create the first entry.",
            )
        ]

    guild = bot.get_guild(guild_id)
    entries = bot.database.get_reaction_role_entries(post_id)
    options = []

    for entry in entries[:25]:
        role = guild.get_role(entry["role_id"]) if guild else None
        role_name = (
            role.name if role else f"Unavailable role {entry['role_id']}"
        )
        options.append(
            discord.SelectOption(
                label=role_name[:100],
                description=(
                    f"{entry['emoji']} • "
                    f"{entry['description'] or 'No description'}"
                )[:100],
                value=str(entry["id"]),
            )
        )

    if not options:
        options.append(
            discord.SelectOption(
                label="No saved roles yet",
                value="none",
                description="Choose Add Role to create the first entry.",
            )
        )

    return options


class PostDetailsModal(Modal):
    def __init__(self, editor: "PostEditorView"):
        super().__init__(title="Edit Reaction-Role Post")
        self.editor = editor

        self.post_title = TextInput(
            label="Post title",
            placeholder="Choose your roles!",
            default=editor.title[:256],
            max_length=256,
            required=True,
        )
        self.post_description = TextInput(
            label="Post description",
            placeholder="Choose the roles you'd like to receive.",
            default=editor.description[:4000],
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False,
        )

        self.add_item(self.post_title)
        self.add_item(self.post_description)

    async def on_submit(self, interaction: discord.Interaction):
        title = self.post_title.value.strip()
        if not title:
            await interaction.response.send_message(
                "The post title cannot be empty.",
                ephemeral=True,
            )
            return

        self.editor.title = title
        self.editor.description = self.post_description.value.strip()

        await interaction.response.edit_message(
            content=None,
            embed=self.editor.create_embed(),
            view=self.editor,
        )


class RoleEntryDetailsModal(Modal):
    def __init__(self, entry_editor: "RoleEntryEditorView"):
        super().__init__(title="Reaction-Role Details")
        self.entry_editor = entry_editor

        self.emoji_input = TextInput(
            label="Reaction emoji",
            placeholder="🎮",
            default=entry_editor.emoji[:100],
            max_length=100,
            required=True,
        )
        self.description_input = TextInput(
            label="Role description",
            placeholder="Gaming updates and game nights",
            default=entry_editor.description[:200],
            max_length=200,
            required=True,
        )
        self.color_input = TextInput(
            label="Role color (hex)",
            placeholder="#5865F2",
            default=entry_editor.color_hex[:7],
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

        if not emoji:
            await interaction.response.send_message(
                "Enter a reaction emoji.",
                ephemeral=True,
            )
            return

        if not description:
            await interaction.response.send_message(
                "Enter a short role description.",
                ephemeral=True,
            )
            return

        if color_hex:
            color_hex = color_hex.lstrip("#")
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

            color_hex = f"#{color_hex}"

        self.entry_editor.emoji = emoji
        self.entry_editor.description = description
        self.entry_editor.color_hex = color_hex

        await interaction.response.edit_message(
            content=None,
            embed=self.entry_editor.create_embed(),
            view=self.entry_editor,
        )


class CreateRoleModal(Modal):
    def __init__(self, entry_editor: "RoleEntryEditorView"):
        super().__init__(title="Create a Discord Role")
        self.entry_editor = entry_editor

        self.role_name = TextInput(
            label="Role name",
            placeholder="Gaming Updates",
            max_length=100,
            required=True,
        )
        self.add_item(self.role_name)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None or guild.id != self.entry_editor.guild_id:
            await interaction.response.send_message(
                "This must be used in the correct server.",
                ephemeral=True,
            )
            return

        me = guild.me
        if me is None or not me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "Ratburn needs the **Manage Roles** permission.",
                ephemeral=True,
            )
            return

        name = self.role_name.value.strip()
        if not name:
            await interaction.response.send_message(
                "Enter a role name.",
                ephemeral=True,
            )
            return

        try:
            role = await guild.create_role(
                name=name,
                reason="Created through Ratburn's reaction-role editor",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "Discord wouldn't let Ratburn create that role. "
                "Check its permissions and role hierarchy.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            logger.exception(
                "Failed to create reaction role in guild %s.",
                guild.id,
            )
            await interaction.response.send_message(
                "Discord couldn't create that role. Check Ratburn's logs.",
                ephemeral=True,
            )
            return

        self.entry_editor.role_id = role.id

        await interaction.response.edit_message(
            content=None,
            embed=self.entry_editor.create_embed(),
            view=self.entry_editor,
        )


class RoleEntrySelect(discord.ui.Select):
    def __init__(self, editor: "PostEditorView"):
        self.editor = editor

        super().__init__(
            placeholder="Select a saved role entry to edit or remove",
            min_values=1,
            max_values=1,
            options=_entry_options(
                editor.bot,
                editor.guild_id,
                editor.post_id,
            ),
            row=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            self.editor.selected_entry_id = None
        else:
            self.editor.selected_entry_id = int(self.values[0])

        await interaction.response.edit_message(
            content=None,
            embed=self.editor.create_embed(),
            view=self.editor,
        )


class RoleEntryEditorView(View):
    """Role configuration screen that replaces the parent editor message."""

    def __init__(
        self,
        editor: "PostEditorView",
        entry=None,
    ):
        super().__init__(timeout=300)
        self.editor = editor
        self.bot = editor.bot
        self.guild_id = editor.guild_id
        self.entry_id = entry["id"] if entry is not None else None

        self.role_id = entry["role_id"] if entry is not None else None
        self.emoji = entry["emoji"] if entry is not None else "🎮"
        self.description = (
            entry["description"] if entry is not None else "Gaming updates"
        )
        self.color_hex = ""
        self.channel_id = None
        self.permission_preset = "none"

        if entry is not None:
            if entry["role_color"] is not None:
                self.color_hex = f"#{entry['role_color']:06X}"

            raw_permissions = entry["channel_permissions"]
            if raw_permissions:
                try:
                    permission_data = json.loads(raw_permissions)
                    self.channel_id = permission_data.get("channel_id")
                    self.permission_preset = permission_data.get(
                        "preset", "none"
                    )
                except (TypeError, json.JSONDecodeError):
                    logger.warning(
                        "Invalid saved permission data for entry %s.",
                        entry["id"],
                    )

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎭 Reaction-Role Entry",
            description=(
                "Choose the role members will receive, then configure its "
                "emoji, description, and optional channel permissions."
            ),
            color=discord.Color.dark_teal(),
        )

        guild = self.bot.get_guild(self.guild_id)
        role = guild.get_role(self.role_id) if guild and self.role_id else None
        channel = (
            guild.get_channel(self.channel_id)
            if guild and self.channel_id
            else None
        )

        embed.add_field(
            name="Role",
            value=role.mention if role else "Not selected",
            inline=True,
        )
        embed.add_field(name="Emoji", value=self.emoji, inline=True)
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
        embed.add_field(
            name="Permission channel",
            value=channel.mention if channel else "None selected",
            inline=True,
        )
        embed.add_field(
            name="Permission preset",
            value=PERMISSION_PRESETS[self.permission_preset],
            inline=False,
        )
        embed.set_footer(
            text=(
                f"Editing entry #{self.entry_id}"
                if self.entry_id is not None
                else "New reaction-role entry"
            )
        )
        return embed

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This editor belongs to a different server.",
                ephemeral=True,
            )
            return False

        if not isinstance(interaction.user, discord.Member) or not (
            interaction.user.guild_permissions.manage_roles
        ):
            await interaction.response.send_message(
                "You need **Manage Roles** to configure reaction roles.",
                ephemeral=True,
            )
            return False

        return True

    async def return_to_parent(
        self,
        interaction: discord.Interaction,
        notice: str | None = None,
    ):
        self.editor.reload_entries()

        await interaction.response.edit_message(
            content=notice,
            embed=self.editor.create_embed(),
            view=self.editor,
        )
        self.stop()

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
        options=PERMISSION_OPTIONS,
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
        await interaction.response.send_modal(RoleEntryDetailsModal(self))

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
        label="Save Role Entry",
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

        if not isinstance(interaction.user, discord.Member) or not (
            interaction.user.guild_permissions.manage_roles
        ):
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

        me = guild.me
        role = guild.get_role(self.role_id)

        if role is None or role.is_default() or role.managed:
            await interaction.response.send_message(
                "That role is unavailable or cannot be assigned by Ratburn.",
                ephemeral=True,
            )
            return

        if me is None or role >= me.top_role:
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

        channel = None
        if self.permission_preset != "none":
            channel = guild.get_channel(self.channel_id)
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "The selected channel is no longer available.",
                    ephemeral=True,
                )
                return

        database = self.bot.database

        # A role entry needs a parent post record. Save the current draft
        # details first, without sending anything to Discord.
        if self.editor.channel_id is None:
            await interaction.response.send_message(
                "Choose the post's destination channel before adding roles.",
                ephemeral=True,
            )
            return

        try:
            self.editor.post_id = database.save_reaction_role_draft(
                post_id=self.editor.post_id,
                guild_id=self.guild_id,
                channel_id=self.editor.channel_id,
                title=self.editor.title,
                description=self.editor.description,
            )
        except (ValueError, TypeError) as error:
            await interaction.response.send_message(
                f"Couldn't prepare the draft: {error}",
                ephemeral=True,
            )
            return

        color_value = _role_color_value(self.color_hex)

        if color_value is not None:
            try:
                await role.edit(
                    colour=discord.Colour(color_value),
                    reason="Updated through Ratburn's reaction-role editor",
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "Ratburn cannot change that role's color. "
                    "Check its role hierarchy and Manage Roles permission.",
                    ephemeral=True,
                )
                return
            except discord.HTTPException:
                logger.exception("Failed to update role color for %s.", role.id)
                await interaction.response.send_message(
                    "Discord couldn't update that role's color.",
                    ephemeral=True,
                )
                return

        permission_data = None

        if self.permission_preset != "none" and channel is not None:
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
            except discord.HTTPException:
                logger.exception(
                    "Failed to update channel permissions for role %s.",
                    role.id,
                )
                await interaction.response.send_message(
                    "Discord couldn't update those channel permissions.",
                    ephemeral=True,
                )
                return

            permission_data = json.dumps({
                "channel_id": channel.id,
                "preset": self.permission_preset,
            })

        try:
            existing = database.get_reaction_role_entry_by_role(
                self.editor.post_id,
                role.id,
            )

            # Prevent duplicate emojis on a single post.
            all_entries = database.get_reaction_role_entries(
                self.editor.post_id
            )
            for item in all_entries:
                if item["emoji"] == self.emoji and (
                    existing is None or item["id"] != existing["id"]
                ):
                    await interaction.response.send_message(
                        "That emoji is already used by another role entry in this post.",
                        ephemeral=True,
                    )
                    return

            if existing:
                entry_id = existing["id"]
                database.update_reaction_role_entry(
                    entry_id, "emoji", self.emoji
                )
                database.update_reaction_role_entry(
                    entry_id, "description", self.description
                )
                database.update_reaction_role_entry(
                    entry_id, "role_color", color_value
                )
                database.update_reaction_role_entry(
                    entry_id, "channel_permissions", permission_data
                )
            else:
                database.add_reaction_role_entry(
                    post_id=self.editor.post_id,
                    role_id=role.id,
                    emoji=self.emoji,
                    description=self.description,
                    role_color=color_value,
                    channel_permissions=permission_data,
                )
        except Exception:
            logger.exception(
                "Couldn't save reaction-role entry for post %s.",
                self.editor.post_id,
            )
            await interaction.response.send_message(
                "Couldn't save that role entry. Check Ratburn's logs.",
                ephemeral=True,
            )
            return

        await self.return_to_parent(
            interaction,
            notice=f"✅ Saved **{role.name}** with reaction {self.emoji}.",
        )

    @discord.ui.button(
        label="Back to Post",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️",
        row=4,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await self.return_to_parent(interaction)


class ReactionRoleDraftSelect(discord.ui.Select):
    def __init__(self, drafts):
        options = []

        for draft in drafts[:25]:
            title = (draft["title"] or "Untitled post").strip()
            description = (draft["description"] or "No description").strip()

            options.append(
                discord.SelectOption(
                    label=title[:100] or "Untitled post",
                    description=description[:100] or "No description",
                    value=str(draft["id"]),
                )
            )

        super().__init__(
            placeholder="Choose a draft to continue editing",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        view: ReactionRoleDraftsView = self.view

        if interaction.guild is None or interaction.guild.id != view.guild_id:
            await interaction.response.send_message(
                "This draft belongs to a different server.",
                ephemeral=True,
            )
            return

        post_id = int(self.values[0])
        draft = view.bot.database.get_reaction_role_post(post_id)

        if draft is None or draft["guild_id"] != view.guild_id:
            await interaction.response.send_message(
                "That draft is no longer available. Please refresh the list.",
                ephemeral=True,
            )
            return

        if draft["status"] != "draft":
            await interaction.response.send_message(
                "That post is no longer a draft. Please refresh the list.",
                ephemeral=True,
            )
            return

        editor = PostEditorView(
            bot=view.bot,
            guild_id=view.guild_id,
            draft=draft,
            back_view=view,
        )

        await interaction.response.edit_message(
            content=None,
            embed=editor.create_embed(),
            view=editor,
        )


class ReactionRoleDraftsView(View):
    def __init__(
        self,
        bot: discord.Client,
        guild_id: int,
        back_view: View | None = None,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.back_view = back_view
        self.drafts = bot.database.get_reaction_role_drafts(guild_id)

        if self.drafts:
            self.add_item(ReactionRoleDraftSelect(self.drafts))

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📂 Saved Reaction-Role Drafts",
            color=discord.Color.dark_teal(),
        )

        if not self.drafts:
            embed.description = (
                "There are no saved drafts right now.\n\n"
                "Go back and choose **Create New** to start a post."
            )
        else:
            embed.description = (
                "Choose a draft below to load it into the editor.\n\n"
                "Drafts expire 14 days after their most recent save."
            )

        embed.set_footer(text="Mr. Ratburn • Draft Manager")
        return embed

    @discord.ui.button(
        label="Refresh",
        style=discord.ButtonStyle.primary,
        emoji="🔄",
        row=1,
    )
    async def refresh(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        refreshed = ReactionRoleDraftsView(
            bot=self.bot,
            guild_id=self.guild_id,
            back_view=self.back_view,
        )
        await interaction.response.edit_message(
            content=None,
            embed=refreshed.create_embed(),
            view=refreshed,
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️",
        row=1,
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        from cogs.reaction_roles.views.dashboard import CreatePostChoiceView

        view = self.back_view or CreatePostChoiceView(
            bot=self.bot,
            guild_id=self.guild_id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.create_embed(),
            view=view,
        )


class PostEditorView(View):
    def __init__(
        self,
        bot: discord.Client,
        guild_id: int,
        draft=None,
        back_view: View | None = None,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.back_view = back_view

        self.post_id: int | None = None
        self.channel_id: int | None = None
        self.selected_entry_id: int | None = None

        self.title = "Choose your roles!"
        self.description = (
            "Choose the roles you'd like to receive by reacting below."
        )

        if draft is not None:
            self.post_id = draft["id"]
            self.channel_id = draft["channel_id"]
            self.title = draft["title"] or self.title
            self.description = draft["description"] or ""

        self.refresh_components()

    def refresh_components(self):
        self.clear_items()
        self.add_item(self.select_channel)
        self.add_item(RoleEntrySelect(self))
        self.add_item(self.add_role)
        self.add_item(self.edit_role)
        self.add_item(self.remove_role)
        self.add_item(self.edit_details)
        self.add_item(self.save_draft)
        self.add_item(self.publish_post)
        self.add_item(self.go_back)
        self.add_item(self.cancel)

    def reload_entries(self):
        self.refresh_components()

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description or "*No description provided.*",
            color=discord.Color.dark_teal(),
        )

        embed.add_field(
            name="Destination channel",
            value=(
                f"<#{self.channel_id}>"
                if self.channel_id is not None
                else "Not selected"
            ),
            inline=False,
        )

        entries = (
            self.bot.database.get_reaction_role_entries(self.post_id)
            if self.post_id is not None
            else []
        )
        guild = self.bot.get_guild(self.guild_id)

        if entries:
            lines = []
            for entry in entries[:25]:
                role = guild.get_role(entry["role_id"]) if guild else None
                role_name = role.name if role else "Unavailable role"
                selected = (
                    " ← selected"
                    if entry["id"] == self.selected_entry_id
                    else ""
                )
                lines.append(
                    f"{entry['emoji']} **{role_name}** — "
                    f"{entry['description'] or 'No description'}{selected}"
                )
            value = "\n".join(lines)
            if len(entries) > 25:
                value += f"\n…and {len(entries) - 25} more."
        else:
            value = "No roles added yet. Choose **Add Role** to get started."

        embed.add_field(
            name=f"Role entries ({len(entries)})",
            value=value[:1024],
            inline=False,
        )

        embed.set_footer(
            text=(
                f"Mr. Ratburn • Draft #{self.post_id}"
                if self.post_id is not None
                else "Mr. Ratburn • New Reaction-Role Post"
            )
        )
        return embed

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This editor belongs to a different server.",
                ephemeral=True,
            )
            return False

        if not isinstance(interaction.user, discord.Member) or not (
            interaction.user.guild_permissions.manage_roles
        ):
            await interaction.response.send_message(
                "You need **Manage Roles** to use this editor.",
                ephemeral=True,
            )
            return False

        return True

    async def ensure_post_record(self) -> int:
        if self.channel_id is None:
            raise ValueError("Choose a destination channel first.")

        self.post_id = self.bot.database.save_reaction_role_draft(
            post_id=self.post_id,
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            title=self.title,
            description=self.description,
        )
        self.refresh_components()
        return self.post_id

    async def return_to_previous_menu(
        self,
        interaction: discord.Interaction,
    ):
        if self.back_view is None:
            from cogs.reaction_roles.views.dashboard import CreatePostChoiceView

            self.back_view = CreatePostChoiceView(
                bot=self.bot,
                guild_id=self.guild_id,
            )

        await interaction.response.edit_message(
            content=None,
            embed=self.back_view.create_embed(),
            view=self.back_view,
        )
        self.stop()

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="Choose the destination channel",
        channel_types=[discord.ChannelType.text],
        min_values=1,
        max_values=1,
        row=0,
    )
    async def select_channel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect,
    ):
        channel = select.values[0]

        if channel.guild.id != self.guild_id:
            await interaction.response.send_message(
                "Please select a channel from this server.",
                ephemeral=True,
            )
            return

        self.channel_id = channel.id
        await interaction.response.edit_message(
            content=None,
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Add Role",
        style=discord.ButtonStyle.success,
        emoji="➕",
        row=2,
    )
    async def add_role(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        entry_editor = RoleEntryEditorView(self)
        await interaction.response.edit_message(
            content=None,
            embed=entry_editor.create_embed(),
            view=entry_editor,
        )

    @discord.ui.button(
        label="Edit Role",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=2,
    )
    async def edit_role(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if self.selected_entry_id is None or self.post_id is None:
            await interaction.response.send_message(
                "Select a saved role entry first.",
                ephemeral=True,
            )
            return

        entry = next(
            (
                item
                for item in self.bot.database.get_reaction_role_entries(
                    self.post_id
                )
                if item["id"] == self.selected_entry_id
            ),
            None,
        )

        if entry is None:
            await interaction.response.send_message(
                "That role entry no longer exists. Refresh the editor and try again.",
                ephemeral=True,
            )
            return

        entry_editor = RoleEntryEditorView(self, entry=entry)
        await interaction.response.edit_message(
            content=None,
            embed=entry_editor.create_embed(),
            view=entry_editor,
        )

    @discord.ui.button(
        label="Remove Role",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
        row=2,
    )
    async def remove_role(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if self.selected_entry_id is None or self.post_id is None:
            await interaction.response.send_message(
                "Select a saved role entry first.",
                ephemeral=True,
            )
            return

        self.bot.database.delete_reaction_role_entry(self.selected_entry_id)
        self.selected_entry_id = None
        self.reload_entries()

        await interaction.response.edit_message(
            content=None,
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Edit title and description",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=3,
    )
    async def edit_details(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await interaction.response.send_modal(PostDetailsModal(self))

    @discord.ui.button(
        label="Save as Draft",
        style=discord.ButtonStyle.success,
        emoji="💾",
        row=3,
    )
    async def save_draft(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if self.channel_id is None:
            await interaction.response.send_message(
                "Choose a destination channel before saving the draft.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "That channel is no longer available. Please select another.",
                ephemeral=True,
            )
            return

        try:
            await self.ensure_post_record()
        except (ValueError, TypeError) as error:
            await interaction.response.send_message(
                f"Couldn't save this draft: {error}",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content=(
                f"💾 Draft **{self.title}** saved successfully!\n"
                f"**Post ID:** `{self.post_id}`\n"
                f"**Channel:** {channel.mention}\n\n"
                "You can return to this draft later using **Use Drafts**."
            ),
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Publish",
        style=discord.ButtonStyle.primary,
        emoji="📣",
        row=3,
    )
    async def publish_post(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This post belongs to a different server.",
                ephemeral=True,
            )
            return

        if self.channel_id is None:
            await interaction.response.send_message(
                "Choose a destination channel before publishing.",
                ephemeral=True,
            )
            return

        try:
            await self.ensure_post_record()
        except (ValueError, TypeError) as error:
            await interaction.response.send_message(
                f"Couldn't prepare the post: {error}",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        success, message = await publish_reaction_role_post(
            bot=self.bot,
            guild=interaction.guild,
            post_id=self.post_id,
        )

        await interaction.followup.send(message, ephemeral=True)

        if success:
            self.reload_entries()
            try:
                await interaction.message.edit(
                    embed=self.create_embed(),
                    view=self,
                )
            except (discord.HTTPException, discord.NotFound):
                pass

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️",
        row=4,
    )
    async def go_back(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await self.return_to_previous_menu(interaction)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
        emoji="✖️",
        row=4,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await self.return_to_previous_menu(interaction)
