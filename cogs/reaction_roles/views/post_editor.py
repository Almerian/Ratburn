import discord
from discord.ui import Button, Modal, TextInput, View


class PostDetailsModal(Modal):
    def __init__(self, editor: "PostEditorView"):
        super().__init__(title="Edit Reaction-Role Post")
        self.editor = editor

        self.post_title = TextInput(
            label="Post title",
            placeholder="Choose your roles!",
            default=editor.title,
            max_length=256,
            required=True,
        )
        self.post_description = TextInput(
            label="Post description",
            placeholder="Choose the roles you'd like to receive.",
            default=editor.description,
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False,
        )

        self.add_item(self.post_title)
        self.add_item(self.post_description)

    async def on_submit(self, interaction: discord.Interaction):
        self.editor.title = self.post_title.value.strip()
        self.editor.description = self.post_description.value.strip()

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
                    description=description[:100],
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
        database = view.bot.database

        draft = database.get_reaction_role_post(post_id)

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
        )

        await interaction.response.edit_message(
            content=None,
            embed=editor.create_embed(),
            view=editor,
        )
        editor.message = interaction.message


class ReactionRoleDraftsView(View):
    def __init__(self, bot: discord.Client, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

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
        self.drafts = self.bot.database.get_reaction_role_drafts(
            self.guild_id
        )

        self.clear_items()

        if self.drafts:
            self.add_item(ReactionRoleDraftSelect(self.drafts))

        self.add_item(self.refresh)
        self.add_item(self.back)

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self,
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
        from cogs.reaction_roles.views.dashboard import (
            CreatePostChoiceView,
        )

        view = CreatePostChoiceView(
            bot=self.bot,
            guild_id=self.guild_id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=discord.Embed(
                title="📝 Create a Reaction-Role Post",
                description=(
                    "Would you like to start a new post, or continue "
                    "working on a saved draft?\n\n"
                    "**Create New** — Start with a blank post.\n"
                    "**Use Drafts** — Load a saved draft and continue editing it."
                ),
                color=discord.Color.dark_teal(),
            ),
            view=view,
        )


class PostEditorView(View):
    def __init__(
        self,
        bot: discord.Client,
        guild_id: int,
        draft=None,
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.message: discord.Message | None = None

        self.post_id: int | None = None
        self.channel_id: int | None = None

        self.title = "Choose your roles!"
        self.description = (
            "Choose the roles you'd like to receive by reacting below."
        )

        if draft is not None:
            self.post_id = draft["id"]
            self.channel_id = draft["channel_id"]
            self.title = draft["title"] or self.title
            self.description = draft["description"] or ""

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description or "*No description provided.*",
            color=discord.Color.dark_teal(),
        )

        channel_text = (
            f"<#{self.channel_id}>"
            if self.channel_id is not None
            else "Not selected"
        )

        embed.add_field(
            name="Destination channel",
            value=channel_text,
            inline=False,
        )

        embed.add_field(
            name="Role entries",
            value=(
                "Role selection will be added directly to this editor "
                "in the next step."
            ),
            inline=False,
        )

        if self.post_id is not None:
            embed.set_footer(
                text=f"Mr. Ratburn • Editing Draft #{self.post_id}"
            )
        else:
            embed.set_footer(text="Mr. Ratburn • New Reaction-Role Post")

        return embed

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
            embed=self.create_embed(),
            view=self,
        )

    @discord.ui.button(
        label="Edit title and description",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=1,
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
        row=1,
    )
    async def save_draft(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This draft belongs to a different server.",
                ephemeral=True,
            )
            return

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

        database = self.bot.database

        try:
            if self.post_id is None:
                self.post_id = database.create_reaction_role_post(
                    guild_id=self.guild_id,
                    channel_id=self.channel_id,
                    title=self.title,
                    description=self.description,
                    status="draft",
                )
            else:
                database.save_reaction_role_draft(
                    post_id=self.post_id,
                    guild_id=self.guild_id,
                    channel_id=self.channel_id,
                    title=self.title,
                    description=self.description,
                )
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
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        emoji="✖️",
        row=1,
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="Post editor closed. Unsaved changes were discarded.",
            embed=None,
            view=self,
        )
        self.stop()
