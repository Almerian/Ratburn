import discord
from discord.ui import View, Button

from cogs.reaction_roles.views.post_editor import PostEditorView


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
        label="Create a reaction-role post",
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

        editor = PostEditorView(
            bot=self.bot,
            guild_id=interaction.guild.id,
        )

        await interaction.response.send_message(
            embed=editor.create_embed(),
            view=editor,
            ephemeral=True,
        )

        editor.message = await interaction.original_response()

    @discord.ui.button(
        label="Manage existing posts",
        style=discord.ButtonStyle.primary,
        emoji="📝",
        row=0,
    )
    async def manage_posts(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        posts = self.bot.database.get_reaction_role_posts(
            interaction.guild.id
        )

        if not posts:
            await interaction.response.send_message(
                "There are no reaction-role posts to manage yet. "
                "Choose **Create a reaction-role post** first!",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "The existing-post editor hasn't been connected yet. "
            f"I found **{len(posts)}** saved post(s), though!",
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
    """Build the main reaction-role dashboard embed."""
    embed = discord.Embed(
        title="🎭 Reaction Roles",
        description=(
            "Welcome to Ratburn's reaction-role manager!\n\n"
            "Create posts that let members choose their own roles "
            "by reacting to a message. You can configure the emoji, "
            "description, role, and post channel for each entry.\n\n"
            "Choose an action below to get started."
        ),
        color=discord.Color.dark_teal(),
    )
    embed.set_footer(
        text="Mr. Ratburn • Server Configuration"
    )
    return embed
