import logging
import sqlite3

import discord
from discord.ui import Button, Modal, TextInput, View

from cogs.reaction_roles.views.publishing import (
    publish_reaction_role_post,
)

logger = logging.getLogger("ratburn.reaction_roles.editor")


class PostCreationModal(Modal):
    """Collect the title and body before opening the post editor."""

    def __init__(self, bot, guild_id, back_view):
        super().__init__(title="Create Reaction-Role Post")

        self.bot = bot
        self.guild_id = guild_id
        self.back_view = back_view

        self.post_title = TextInput(
            label="Post Title",
            placeholder="Choose your roles!",
            max_length=256,
            required=True,
        )

        self.post_body = TextInput(
            label="Post Body",
            placeholder="Choose the roles you'd like to receive.",
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False,
        )

        self.add_item(self.post_title)
        self.add_item(self.post_body)

    async def on_submit(self, interaction: discord.Interaction):
        title = self.post_title.value.strip()

        if not title:
            await interaction.response.send_message(
                "The post title cannot be empty.",
                ephemeral=True,
            )
            return

        editor = PostEditorView(
            bot=self.bot,
            guild_id=self.guild_id,
            title=title,
            description=self.post_body.value.strip(),
            back_view=self.back_view,
        )

        await interaction.response.send_message(
            embed=editor.create_embed(),
            view=editor,
            ephemeral=True,
        )

        editor.message = await interaction.original_response()


class AddRoleEmojiModal(Modal):
    """Collect the reaction emoji for an existing server role."""

    def __init__(self, editor, role_id):
        super().__init__(title="Add Reaction Role")

        self.editor = editor
        self.role_id = role_id

        self.emoji_input = TextInput(
            label="Reaction Emoji",
            placeholder="🎮",
            max_length=100,
            required=True,
        )

        self.description_input = TextInput(
            label="Role Description (optional)",
            placeholder="Gaming updates and game nights",
            max_length=200,
            required=False,
        )

        self.add_item(self.emoji_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None or guild.id != self.editor.guild_id:
            await interaction.response.send_message(
                "This post belongs to a different server.",
                ephemeral=True,
            )
            return

        role = guild.get_role(self.role_id)

        if role is None or role.is_default() or role.managed:
            await interaction.response.send_message(
                "That role is unavailable or cannot be assigned.",
                ephemeral=True,
            )
            return

        me = guild.me

        if me is None or role >= me.top_role:
            await interaction.response.send_message(
                "Ratburn's highest role must be above the selected role.",
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

        description = self.description_input.value.strip()

        database = self.editor.bot.database

        try:
            post_id = self.editor.ensure_post_record()

            existing_role = database.get_reaction_role_entry_by_role(
                post_id,
                role.id,
            )

            if existing_role:
                await interaction.response.send_message(
                    "That role is already included in this post.",
                    ephemeral=True,
                )
                return

            entries = database.get_reaction_role_entries(post_id)

            if any(entry["emoji"] == emoji for entry in entries):
                await interaction.response.send_message(
                    "That emoji is already being used in this post. "
                    "Please choose another.",
                    ephemeral=True,
                )
                return

            database.add_reaction_role_entry(
                post_id=post_id,
                role_id=role.id,
                emoji=emoji,
                description=description,
                role_color=None,
                channel_permissions=None,
                role_icon=None,
            )

        except sqlite3.IntegrityError:
            await interaction.response.send_message(
                "That role or emoji is already in use in this post.",
                ephemeral=True,
            )
            return

        except Exception:
            logger.exception(
                "Couldn't add role %s to reaction-role post %s.",
                role.id,
                self.editor.post_id,
            )
            await interaction.response.send_message(
                "Couldn't add that role. Check Ratburn's logs.",
                ephemeral=True,
            )
            return

        self.editor.refresh_message()

        if self.editor.message is not None:
            try:
                await self.editor.message.edit(
                    embed=self.editor.create_embed(),
                    view=self.editor,
                )
            except discord.HTTPException:
                logger.exception(
                    "Couldn't refresh the reaction-role editor."
                )

        await interaction.response.send_message(
            f"Added {role.mention} with reaction {emoji}.",
            ephemeral=True,
        )


class AddRoleSelect(discord.ui.RoleSelect):
    def __init__(self, editor):
        self.editor = editor

        super().__init__(
            placeholder="Search for an existing server role",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]

        if interaction.guild is None or interaction.guild.id != self.editor.guild_id:
            await interaction.response.send_message(
                "This post belongs to a different server.",
                ephemeral=True,
            )
            return

        self.editor.message = interaction.message

        await interaction.response.send_modal(
            AddRoleEmojiModal(self.editor, role.id)
        )


class AddRoleView(View):
    def __init__(self, editor):
        super().__init__(timeout=300)

        self.editor = editor
        self.add_item(AddRoleSelect(editor))

    @discord.ui.button(
        label="Back to Post",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await interaction.response.edit_message(
            embed=self.editor.create_embed(),
            view=self.editor,
        )


class ReactionRoleDraftSelect(discord.ui.Select):
    def __init__(self, drafts):
        options = []

        for draft in drafts[:25]:
            title = (draft["title"] or "Untitled post").strip()
            description = (
                draft["description"] or "No description"
            ).strip()

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
                "That draft is no longer available. Refresh the list.",
                ephemeral=True,
            )
            return

        if draft["status"] != "draft":
            await interaction.response.send_message(
                "That post is no longer a draft. Refresh the list.",
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

        editor.message = interaction.message


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
        title: str = "Choose your roles!",
        description: str = "",
        draft=None,
        back_view: View | None = None,
    ):
        super().__init__(timeout=300)

        self.bot = bot
        self.guild_id = guild_id
        self.back_view = back_view
        self.message = None

        self.post_id = None
        self.channel_id = None

        self.title = title
        self.description = description

        if draft is not None:
            self.post_id = draft["id"]
            self.channel_id = draft["channel_id"] or None
            self.title = draft["title"] or self.title
            self.description = draft["description"] or ""

    def refresh_message(self):
        """Refresh the editor's displayed role list after a change."""
        return

    def get_entries(self):
        if self.post_id is None:
            return []

        return self.bot.database.get_reaction_role_entries(self.post_id)

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description or "*No description provided.*",
            color=discord.Color.dark_teal(),
        )

        embed.add_field(
            name="Destination Channel",
            value=(
                f"<#{self.channel_id}>"
                if self.channel_id is not None
                else "Not selected"
            ),
            inline=False,
        )

        entries = self.get_entries()
        guild = self.bot.get_guild(self.guild_id)

        if entries:
            lines = []

            for entry in entries[:25]:
                role = guild.get_role(entry["role_id"]) if guild else None
                role_name = role.name if role else "Unavailable role"

                line = f"{entry['emoji']} **{role_name}**"

                if entry["description"]:
                    line += f" — {entry['description']}"

                lines.append(line)

            value = "\n".join(lines)

            if len(entries) > 25:
                value += f"\n…and {len(entries) - 25} more."
        else:
            value = "No roles added yet. Choose **Add Role** to get started."

        embed.add_field(
            name=f"Roles ({len(entries)})",
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

    def ensure_post_record(self) -> int:
        self.post_id = self.bot.database.save_reaction_role_draft(
            post_id=self.post_id,
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            title=self.title,
            description=self.description,
        )

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
        placeholder="Search for a destination channel",
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
                "Choose a channel from this server.",
                ephemeral=True,
            )
            return

        self.channel_id = channel.id

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Add Role",
        style=discord.ButtonStyle.success,
        emoji="➕",
        row=1,
    )
    async def add_role(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        picker = AddRoleView(self)

        await interaction.response.edit_message(
            content="Choose an existing server role to add.",
            embed=None,
            view=picker,
        )

        self.message = interaction.message

    @discord.ui.button(
        label="Save as Draft",
        style=discord.ButtonStyle.secondary,
        emoji="💾",
        row=2,
    )
    async def save_draft(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        try:
            self.ensure_post_record()
        except (ValueError, TypeError) as error:
            await interaction.response.send_message(
                f"Couldn't save this draft: {error}",
                ephemeral=True,
            )
            return

        await interaction.response.edit_message(
            content=f"💾 Draft **{self.title}** saved successfully.",
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Publish",
        style=discord.ButtonStyle.success,
        emoji="📣",
        row=2,
    )
    async def publish_post(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if self.channel_id is None:
            await interaction.response.send_message(
                "Choose a destination channel before publishing.",
                ephemeral=True,
            )
            return

        if not self.get_entries():
            await interaction.response.send_message(
                "Add at least one role before publishing.",
                ephemeral=True,
            )
            return

        try:
            post_id = self.ensure_post_record()
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
            post_id=post_id,
        )

        await interaction.followup.send(message, ephemeral=True)

        if success and interaction.message is not None:
            try:
                await interaction.message.edit(
                    embed=self.create_embed(),
                    view=self,
                )
            except discord.HTTPException:
                logger.exception(
                    "Couldn't refresh the editor after publishing."
                )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️",
        row=3,
    )
    async def go_back(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await self.return_to_previous_menu(interaction)
