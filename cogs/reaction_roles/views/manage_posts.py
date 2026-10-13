
import discord
from discord.ui import Button, Modal, TextInput, View

from cogs.reaction_roles.views.role_editor import RoleEditorView
from cogs.reaction_roles.views.publishing import (
    publish_reaction_role_post,
)


class EditSavedPostModal(Modal):
    def __init__(self, manager: "ManagePostsView"):
        super().__init__(title="Edit Reaction-Role Post")
        self.manager = manager

        post = manager.selected_post
        self.title_input = TextInput(
            label="Post title",
            default=post["title"],
            max_length=256,
            required=True,
        )
        self.description_input = TextInput(
            label="Post description",
            default=post["description"],
            style=discord.TextStyle.paragraph,
            max_length=4000,
            required=False,
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        post_id = self.manager.selected_post["id"]

        self.manager.bot.database.update_reaction_role_post(
            post_id, "title", self.title_input.value.strip()
        )
        self.manager.bot.database.update_reaction_role_post(
            post_id, "description", self.description_input.value.strip()
        )

        self.manager.reload_posts()

        await interaction.response.edit_message(
            embed=self.manager.create_embed(),
            view=self.manager,
        )


class SavedPostSelect(discord.ui.Select):
    def __init__(self, manager: "ManagePostsView"):
        self.manager = manager

        options = []
        for post in manager.posts[:25]:
            status = (
                "Published"
                if post["message_id"]
                else "Draft"
            )
            channel = f" • {status}"
            label = post["title"][:100] or f"Post {post['id']}"

            options.append(
                discord.SelectOption(
                    label=label,
                    description=f"Post #{post['id']}{channel}"[:100],
                    value=str(post["id"]),
                    default=post["id"] == manager.selected_post_id,
                )
            )

        super().__init__(
            placeholder="Select a saved reaction-role post",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        self.manager.selected_post_id = int(self.values[0])
        self.manager.reload_posts()

        await interaction.response.edit_message(
            embed=self.manager.create_embed(),
            view=self.manager,
        )


class ManagePostsView(View):
    def __init__(self, bot: discord.Client, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.posts = []
        self.selected_post_id = None
        self.reload_posts()

    @property
    def selected_post(self):
        for post in self.posts:
            if post["id"] == self.selected_post_id:
                return post
        return None

    def reload_posts(self):
        self.posts = self.bot.database.get_reaction_role_posts(
            self.guild_id
        )

        if (
            self.selected_post_id is None
            or not any(
                post["id"] == self.selected_post_id
                for post in self.posts
            )
        ):
            self.selected_post_id = (
                self.posts[0]["id"] if self.posts else None
            )

        self.clear_items()

        if self.posts:
            self.add_item(SavedPostSelect(self))

            self.add_item(self.edit_details)
            self.add_item(self.configure_role)
            self.add_item(self.publish_refresh)
            self.add_item(self.delete_post)
            self.add_item(self.close_manager)

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📝 Manage Reaction-Role Posts",
            color=discord.Color.dark_teal(),
        )

        post = self.selected_post
        if post is None:
            embed.description = (
                "No saved reaction-role posts yet. "
                "Create a draft from the main dashboard first."
            )
            return embed

        status = "Published" if post["message_id"] else "Draft"
        channel = self.bot.get_guild(self.guild_id).get_channel(
            post["channel_id"]
        )

        entries = self.bot.database.get_reaction_role_entries(
            post["id"]
        )

        embed.description = (
            f"**Post ID:** `{post['id']}`\n"
            f"**Status:** {status}\n"
            f"**Channel:** {channel.mention if channel else 'Unavailable'}\n"
            f"**Role entries:** {len(entries)}\n\n"
            "Select a post above, then choose an action."
        )
        embed.add_field(
            name=post["title"],
            value=post["description"] or "No description set.",
            inline=False,
        )
        embed.set_footer(text="Mr. Ratburn • Reaction-Role Manager")
        return embed

    async def interaction_check(
        self, interaction: discord.Interaction
    ) -> bool:
        if interaction.guild is None or interaction.guild.id != self.guild_id:
            await interaction.response.send_message(
                "This manager belongs to a different server.",
                ephemeral=True,
            )
            return False

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "You need **Manage Roles** to manage reaction-role posts.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Edit details",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=1,
    )
    async def edit_details(
        self, interaction: discord.Interaction, button: Button
    ):
        if self.selected_post is None:
            await interaction.response.send_message(
                "Select a post first.", ephemeral=True
            )
            return

        await interaction.response.send_modal(EditSavedPostModal(self))

    @discord.ui.button(
        label="Configure a role",
        style=discord.ButtonStyle.secondary,
        emoji="🎭",
        row=1,
    )
    async def configure_role(
        self, interaction: discord.Interaction, button: Button
    ):
        if self.selected_post is None:
            await interaction.response.send_message(
                "Select a post first.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="Configure a role",
                description=(
                    "Choose an existing role or create one, then save "
                    "its emoji and description."
                ),
                color=discord.Color.dark_teal(),
            ),
            view=RoleEditorView(
                bot=self.bot,
                guild_id=self.guild_id,
                post_id=self.selected_post["id"],
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Publish / Refresh",
        style=discord.ButtonStyle.success,
        emoji="📣",
        row=1,
    )
    async def publish_refresh(
        self, interaction: discord.Interaction, button: Button
    ):
        if self.selected_post is None:
            await interaction.response.send_message(
                "Select a post first.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        success, message = await publish_reaction_role_post(
            bot=self.bot,
            guild=interaction.guild,
            post_id=self.selected_post["id"],
        )

        await interaction.followup.send(message, ephemeral=True)

        self.reload_posts()

    @discord.ui.button(
        label="Delete post",
        style=discord.ButtonStyle.danger,
        emoji="🗑️",
        row=2,
    )
    async def delete_post(
        self, interaction: discord.Interaction, button: Button
    ):
        post = self.selected_post
        if post is None:
            await interaction.response.send_message(
                "Select a post first.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Are you sure you want to delete **{post['title']}**? "
            "This removes its saved setup and role entries. "
            "The published Discord message, if any, will also be deleted.",
            view=DeletePostConfirmationView(self, post["id"]),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.secondary,
        emoji="✖️",
        row=2,
    )
    async def close_manager(
        self, interaction: discord.Interaction, button: Button
    ):
        await interaction.response.edit_message(
            content="Reaction-role manager closed.",
            embed=None,
            view=None,
        )
        self.stop()


class DeletePostConfirmationView(View):
    def __init__(self, manager: ManagePostsView, post_id: int):
        super().__init__(timeout=60)
        self.manager = manager
        self.post_id = post_id

    @discord.ui.button(
        label="Yes, delete it",
        style=discord.ButtonStyle.danger,
    )
    async def confirm(
        self, interaction: discord.Interaction, button: Button
    ):
        post = self.manager.bot.database.get_reaction_role_post(
            self.post_id
        )

        if post is None or post["guild_id"] != interaction.guild.id:
            await interaction.response.edit_message(
                content="That saved post no longer exists.",
                view=None,
            )
            return

        if post["message_id"]:
            channel = interaction.guild.get_channel(post["channel_id"])
            if isinstance(channel, discord.TextChannel):
                try:
                    message = await channel.fetch_message(post["message_id"])
                    await message.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

        self.manager.bot.database.delete_reaction_role_post(
            self.post_id
        )
        self.manager.reload_posts()

        await interaction.response.edit_message(
            content="Reaction-role setup deleted.",
            view=None,
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel(
        self, interaction: discord.Interaction, button: Button
    ):
        await interaction.response.edit_message(
            content="Deletion cancelled.",
            view=None,
        )
        self.stop()
