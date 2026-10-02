
import discord
from discord import app_commands
from discord.ext import commands


class FilterView(discord.ui.View):
    WORDS_PER_PAGE = 10

    def __init__(self, bot, guild_id, words):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.words = words
        self.page = 0

        self.update_buttons()

    @property
    def total_pages(self):
        return max(
            1,
            (len(self.words) + self.WORDS_PER_PAGE - 1)
            // self.WORDS_PER_PAGE
        )

    def update_buttons(self):
        self.previous_button.disabled = self.page == 0
        self.next_button.disabled = self.page >= self.total_pages - 1

    def build_embed(self):
        embed = discord.Embed(
            title="📚 Ratburn's Chat Filter",
            color=discord.Color.dark_teal()
        )

        if not self.words:
            embed.description = "No filtered words have been added yet."
        else:
            start = self.page * self.WORDS_PER_PAGE
            end = start + self.WORDS_PER_PAGE
            page_words = self.words[start:end]

            embed.description = "\n".join(
                f"**{i}.** {word}"
                for i, word in enumerate(page_words, start=start + 1)
            )

        embed.set_footer(
            text=f"Page {self.page + 1} of {self.total_pages}"
        )
        return embed

    @discord.ui.button(
        label="Previous",
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )

    @discord.ui.button(
        label="Next",
        emoji="▶️",
        style=discord.ButtonStyle.secondary
    )
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self
        )

    @discord.ui.button(
        label="Add Words",
        emoji="➕",
        style=discord.ButtonStyle.success,
        row=1
    )
    async def add_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you need to be an admin for that!",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            AddWordsModal(self)
        )

    @discord.ui.button(
        label="Remove Words",
        emoji="➖",
        style=discord.ButtonStyle.danger,
        row=1
    )
    async def remove_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Sorry, you need to be an admin for that!",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            RemoveWordsModal(self)
        )



class AddWordsModal(discord.ui.Modal, title="Add Filtered Words"):
    words = discord.ui.TextInput(
        label="Words to add",
        placeholder="word1, word2, word3",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, view):
        super().__init__()
        self.filter_view = view

    async def on_submit(self, interaction: discord.Interaction):
        words = {
            word.strip()
            for word in self.words.value.split(",")
            if word.strip()
        }

        if not words:
            await interaction.response.send_message(
                "Please enter at least one word.",
                ephemeral=True
            )
            return

        added = 0
        for word in words:
            before = len(
                self.filter_view.bot.database.get_filtered_words(
                    self.filter_view.guild_id
                )
            )
            self.filter_view.bot.database.add_filtered_word(
                self.filter_view.guild_id,
                word
            )
            after = len(
                self.filter_view.bot.database.get_filtered_words(
                    self.filter_view.guild_id
                )
            )
            added += after - before

        self.filter_view.words = [
            row["word"]
            for row in self.filter_view.bot.database.get_filtered_words(
                self.filter_view.guild_id
            )
        ]
        self.filter_view.page = min(
            self.filter_view.page,
            self.filter_view.total_pages - 1
        )
        self.filter_view.update_buttons()

        await interaction.response.edit_message(
            embed=self.filter_view.build_embed(),
            view=self.filter_view
        )


class RemoveWordsModal(discord.ui.Modal, title="Remove Filtered Words"):
    words = discord.ui.TextInput(
        label="Words to remove",
        placeholder="word1, word2, word3",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    def __init__(self, view):
        super().__init__()
        self.filter_view = view

    async def on_submit(self, interaction: discord.Interaction):
        words = {
            word.strip()
            for word in self.words.value.split(",")
            if word.strip()
        }

        if not words:
            await interaction.response.send_message(
                "Please enter at least one word.",
                ephemeral=True
            )
            return

        removed = 0
        for word in words:
            before = len(
                self.filter_view.bot.database.get_filtered_words(
                    self.filter_view.guild_id
                )
            )
            self.filter_view.bot.database.remove_filtered_word(
                self.filter_view.guild_id,
                word
            )
            after = len(
                self.filter_view.bot.database.get_filtered_words(
                    self.filter_view.guild_id
                )
            )
            removed += before - after

        self.filter_view.words = [
            row["word"]
            for row in self.filter_view.bot.database.get_filtered_words(
                self.filter_view.guild_id
            )
        ]
        self.filter_view.page = min(
            self.filter_view.page,
            self.filter_view.total_pages - 1
        )
        self.filter_view.update_buttons()

        await interaction.response.edit_message(
            embed=self.filter_view.build_embed(),
            view=self.filter_view
        )


class Filter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="filter",
        description="View and manage Ratburn's chat filter."
    )
    async def filter(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used inside a server.",
                ephemeral=True
            )
            return

        config = self.bot.database.get_config(interaction.guild.id)
        staff_role_id = config["staff_role_id"]

        if staff_role_id is None:
            await interaction.response.send_message(
                "The Staff Role hasn't been configured yet.",
                ephemeral=True
            )
            return

        staff_role = interaction.guild.get_role(staff_role_id)

        if staff_role is None:
            await interaction.response.send_message(
                "The configured Staff Role no longer exists.",
                ephemeral=True
            )
            return

        if not isinstance(interaction.user, discord.Member):
            return

        if interaction.user.top_role < staff_role:
            await interaction.response.send_message(
                "Sorry, you need the Staff Role to view this!",
                ephemeral=True
            )
            return

        words = [
            row["word"]
            for row in self.bot.database.get_filtered_words(
                interaction.guild.id
            )
        ]

        view = FilterView(
            self.bot,
            interaction.guild.id,
            words
        )

        await interaction.response.send_message(
            embed=view.build_embed(),
            view=view,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Filter(bot))
