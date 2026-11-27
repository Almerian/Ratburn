import discord
from discord.ui import Button, View

from cogs.reaction_roles.views.manage_posts import ManagePostsView
from cogs.reaction_roles.views.post_editor import (
    PostCreationModal,
    ReactionRoleDraftsView,
)


def create_post_choice_embed() -> discord.Embed:
    return discord.Embed(
        title="📝 Create a Reaction-Role Post",
        description=(
            "Would you like to start a new post, or continue "
            "working on a saved draft?\n\n"
            "**Create New** — Start with a blank post.\n"
            "**Use Drafts** — Load a saved draft and continue editing it."
        ),
        color=discord.Color.dark_teal(),
    )


class CreatePostChoiceView(View):
    def __init__(self, bot: discord.Client, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

    def create_embed(self) -> discord.Embed:
        return create_post_choice_embed()

    @discord.ui.button(
        label="Create New",
        style=discord.ButtonStyle.success,
        emoji="➕",
        row=0,
    )
    async def create_new(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        await interaction.response.send_modal(
            PostCreationModal(
                bot=self.bot,
                guild_id=self.guild_id,
                back_view=self,
            )
        )

    @discord.ui.button(
        label="Use Drafts",
        style=discord.ButtonStyle.primary,
        emoji="📂",
        row=0,
    )
    async def use_drafts(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        drafts = ReactionRoleDraftsView(
            bot=self.bot,
            guild_id=self.guild_id,
            back_view=self,
        )

        await interaction.response.edit_message(
            content=None,
            embed=drafts.create_embed(),
            view=drafts,
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        emoji="⬅️",
        row=1,
    )
    async def go_back(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        dashboard = ReactionRolesDashboardView(self.bot)

        await interaction.response.edit_message(
            content=None,
            embed=create_dashboard_embed(),
            view=dashboard,
        )


class ReactionRolesDashboardView(View):
    def __init__(self, bot: discord.Client):
        super().__init__(timeout=300)
        self.bot = bot

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This dashboard can only be used in a server.",
                ephemeral=True,
            )
            return False

        if not isinstance(interaction.user, discord.Member):
            return False

        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "You need the **Manage Roles** permission to use this dashboard.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Create a post",
        style=discord.ButtonStyle.success,
        emoji="➕",
        row=0,
    )
    async def create_post(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This dashboard can only be used in a server.",
                ephemeral=True,
            )
            return

        view = CreatePostChoiceView(
            bot=self.bot,
            guild_id=interaction.guild.id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.create_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Manage a post",
        style=discord.ButtonStyle.primary,
        emoji="🗂️",
        row=0,
    )
    async def manage_posts(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This dashboard can only be used in a server.",
                ephemeral=True,
            )
            return

        manager = ManagePostsView(
            bot=self.bot,
            guild_id=interaction.guild.id,
        )

        await interaction.response.send_message(
            embed=manager.create_embed(),
            view=manager,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.secondary,
        emoji="✖️",
        row=1,
    )
    async def close_dashboard(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="Reaction-role dashboard closed.",
            embed=None,
            view=self,
        )

        self.stop()


def create_dashboard_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎭 Reaction Roles",
        description=(
            "Welcome to Ratburn's reaction-role manager!\n\n"
            "Create posts that let members choose their own roles "
            "by reacting to a message, or manage posts you've already created.\n\n"
            "Choose an action below to get started."
        ),
        color=discord.Color.dark_teal(),
    )

    embed.set_footer(text="Mr. Ratburn • Server Configuration")
    return embed
