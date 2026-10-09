
import discord
from discord import app_commands
from discord.ext import commands


QUESTIONS_PER_PAGE = 10
REMOVE_OPTIONS_PER_PAGE = 25
MAX_QUESTION_LENGTH = 300


def can_manage_questions(interaction: discord.Interaction) -> bool:
    return (
        interaction.guild is not None
        and isinstance(interaction.user, discord.Member)
        and interaction.user.guild_permissions.manage_guild
    )


class QuestionAdminView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message(
                "This question manager belongs to another server.",
                ephemeral=True,
            )
            return False

        if not can_manage_questions(interaction):
            await interaction.response.send_message(
                "You need the **Manage Server** permission to do that.",
                ephemeral=True,
            )
            return False

        return True

    def build_embed(self) -> discord.Embed:
        questions = self.bot.database.get_icebreaker_questions(
            self.guild_id
        )

        embed = discord.Embed(
            title="📚 Daily Icebreaker Questions",
            description=(
                "Manage the custom questions Ratburn can post "
                "in this server.\n\n"
                "Built-in questions are managed separately and "
                "cannot be removed through this menu."
            ),
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="Custom questions",
            value=str(len(questions)),
            inline=True,
        )

        embed.add_field(
            name="Built-in questions",
            value="40",
            inline=True,
        )

        embed.set_footer(
            text="Changes apply to future question selections."
        )

        return embed

    @discord.ui.button(
        label="Add Question",
        emoji="➕",
        style=discord.ButtonStyle.success,
    )
    async def add_question(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_modal(
            AddQuestionModal(
                self.bot,
                self.guild_id,
            )
        )

    @discord.ui.button(
        label="Review Questions",
        emoji="📋",
        style=discord.ButtonStyle.primary,
    )
    async def review_questions(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = ReviewQuestionsView(
            self.bot,
            self.guild_id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Remove Question",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
    )
    async def remove_question(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = RemoveQuestionsView(
            self.bot,
            self.guild_id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view,
        )


class AddQuestionModal(
    discord.ui.Modal,
    title="Add an Icebreaker Question",
):
    question = discord.ui.TextInput(
        label="Question",
        placeholder="What is something you could talk about for hours?",
        style=discord.TextStyle.paragraph,
        min_length=3,
        max_length=MAX_QUESTION_LENGTH,
        required=True,
    )

    def __init__(self, bot, guild_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message(
                "This question belongs to another server.",
                ephemeral=True,
            )
            return

        if not can_manage_questions(interaction):
            await interaction.response.send_message(
                "You need the **Manage Server** permission to do that.",
                ephemeral=True,
            )
            return

        question_text = self.question.value.strip()

        if len(question_text) < 3:
            await interaction.response.send_message(
                "Please enter a question with at least 3 characters.",
                ephemeral=True,
            )
            return

        existing_questions = (
            self.bot.database.get_icebreaker_questions(
                self.guild_id
            )
        )

        if any(
            row["question"].casefold() == question_text.casefold()
            for row in existing_questions
        ):
            await interaction.response.send_message(
                "That question already exists in this server's "
                "custom question list.",
                ephemeral=True,
            )
            return

        self.bot.database.add_icebreaker_question(
            self.guild_id,
            question_text,
            interaction.user.id,
        )

        await interaction.response.send_message(
            "✅ Added your custom Icebreaker question!",
            ephemeral=True,
        )


class ReviewQuestionsView(QuestionAdminView):
    def __init__(
        self,
        bot,
        guild_id: int,
        page: int = 0,
    ):
        super().__init__(bot, guild_id)
        self.page = page

        questions = bot.database.get_icebreaker_questions(guild_id)
        total_pages = max(
            1,
            (len(questions) + QUESTIONS_PER_PAGE - 1)
            // QUESTIONS_PER_PAGE,
        )

        self.page = min(self.page, total_pages - 1)

        self.previous_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= total_pages - 1

    def build_embed(self) -> discord.Embed:
        questions = self.bot.database.get_icebreaker_questions(
            self.guild_id
        )

        total_pages = max(
            1,
            (len(questions) + QUESTIONS_PER_PAGE - 1)
            // QUESTIONS_PER_PAGE,
        )

        start = self.page * QUESTIONS_PER_PAGE
        page_questions = questions[
            start:start + QUESTIONS_PER_PAGE
        ]

        embed = discord.Embed(
            title="📋 Custom Icebreaker Questions",
            color=discord.Color.blurple(),
        )

        if not page_questions:
            embed.description = (
                "There are no custom questions yet.\n\n"
                "Use **Add Question** to create one."
            )
        else:
            embed.description = "\n\n".join(
                f"**{start + index + 1}.** {row['question']}"
                for index, row in enumerate(page_questions)
            )

        embed.set_footer(
            text=f"Page {self.page + 1} of {total_pages}"
        )

        return embed

    @discord.ui.button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = ReviewQuestionsView(
            self.bot,
            self.guild_id,
            self.page - 1,
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Next",
        emoji="▶️",
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = ReviewQuestionsView(
            self.bot,
            self.guild_id,
            self.page + 1,
        )

        await interaction.response.edit_message(
            embed=view.build_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Back",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = QuestionAdminView(
            self.bot,
            self.guild_id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view,
        )


class RemoveQuestionSelect(discord.ui.Select):
    def __init__(
        self,
        bot,
        guild_id: int,
        page: int,
    ):
        self.bot = bot
        self.guild_id = guild_id
        self.page = page

        questions = bot.database.get_icebreaker_questions(guild_id)

        start = page * REMOVE_OPTIONS_PER_PAGE
        page_questions = questions[
            start:start + REMOVE_OPTIONS_PER_PAGE
        ]

        options = [
            discord.SelectOption(
                label=row["question"][:100],
                value=str(row["id"]),
                description=f"Custom question #{row['id']}",
            )
            for row in page_questions
        ]

        super().__init__(
            placeholder=(
                "Choose a question to remove..."
                if options
                else "No custom questions to remove"
            ),
            min_values=1,
            max_values=1,
            options=options or [
                discord.SelectOption(
                    label="No custom questions available",
                    value="none",
                )
            ],
            disabled=not bool(options),
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message(
                "This question manager belongs to another server.",
                ephemeral=True,
            )
            return

        if not can_manage_questions(interaction):
            await interaction.response.send_message(
                "You need the **Manage Server** permission to do that.",
                ephemeral=True,
            )
            return

        selected_value = self.values[0]

        if selected_value == "none":
            await interaction.response.send_message(
                "There are no custom questions to remove.",
                ephemeral=True,
            )
            return

        question_id = int(selected_value)

        self.bot.database.remove_icebreaker_question(
            self.guild_id,
            question_id,
        )

        view = RemoveQuestionsView(
            self.bot,
            self.guild_id,
            self.page,
        )

        await interaction.response.edit_message(
            content="🗑️ Custom question removed.",
            embed=view.build_embed(),
            view=view,
        )


class RemoveQuestionsView(QuestionAdminView):
    def __init__(
        self,
        bot,
        guild_id: int,
        page: int = 0,
    ):
        super().__init__(bot, guild_id)

        self.page = page

        questions = bot.database.get_icebreaker_questions(guild_id)
        total_pages = max(
            1,
            (len(questions) + REMOVE_OPTIONS_PER_PAGE - 1)
            // REMOVE_OPTIONS_PER_PAGE,
        )

        self.page = min(self.page, total_pages - 1)

        self.add_item(
            RemoveQuestionSelect(
                bot,
                guild_id,
                self.page,
            )
        )

        self.previous_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= total_pages - 1

    def build_embed(self) -> discord.Embed:
        questions = self.bot.database.get_icebreaker_questions(
            self.guild_id
        )

        total_pages = max(
            1,
            (len(questions) + REMOVE_OPTIONS_PER_PAGE - 1)
            // REMOVE_OPTIONS_PER_PAGE,
        )

        embed = discord.Embed(
            title="🗑️ Remove Custom Questions",
            description=(
                "Choose a question from the dropdown to remove it.\n\n"
                f"**Custom questions:** {len(questions)}"
            ),
            color=discord.Color.red(),
        )

        if not questions:
            embed.description = (
                "There are no custom questions to remove.\n\n"
                "Use **Back** to return to the question manager."
            )

        embed.set_footer(
            text=f"Page {self.page + 1} of {total_pages}"
        )

        return embed

    @discord.ui.button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = RemoveQuestionsView(
            self.bot,
            self.guild_id,
            self.page - 1,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Next",
        emoji="▶️",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = RemoveQuestionsView(
            self.bot,
            self.guild_id,
            self.page + 1,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view,
        )

    @discord.ui.button(
        label="Back",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def back(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        view = QuestionAdminView(
            self.bot,
            self.guild_id,
        )

        await interaction.response.edit_message(
            content=None,
            embed=view.build_embed(),
            view=view,
        )


class IcebreakerQuestionAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    icebreaker_group = app_commands.Group(
        name="icebreaker",
        description="Manage Ratburn's Daily Icebreaker.",
    )

    @icebreaker_group.command(
        name="questions",
        description="Manage custom Daily Icebreaker questions.",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def questions(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True,
            )
            return

        if not can_manage_questions(interaction):
            await interaction.response.send_message(
                "You need the **Manage Server** permission to use this.",
                ephemeral=True,
            )
            return

        view = QuestionAdminView(
            self.bot,
            interaction.guild.id,
        )

        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(IcebreakerQuestionAdmin(bot))
