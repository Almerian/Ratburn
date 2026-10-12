import discord
from discord.ui import Button, Modal, TextInput, View

from cogs.reaction_roles.views.role_editor import RoleEditorView

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

        if self.editor.message is not None:
            await self.editor.message.edit(
                embed=self.editor.create_embed(),
                view=self.editor,
            )

        await interaction.response.send_message(
            "Post details updated!",
            ephemeral=True,
        )


class PostEditorView(View):

    def __init__(self, bot: discord.Client, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.channel_id: int | None = None
        self.message: discord.Message | None = None

        self.title = "Choose your roles!"
        self.description = (
            "Choose the roles you'd like to receive by reacting below."
        )

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=discord.Color.dark_teal(),
        )

        if self.channel_id is None:
            channel_text = "Not selected"
        else:
            channel_text = f"<#{self.channel_id}>"

        embed.add_field(
            name="Destination channel",
            value=channel_text,
            inline=False,
        )
        embed.add_field(
            name="Next step",
            value=(
                "Save this draft when you're happy with the settings. "
                "Role entries and publishing will be configured separately."
            ),
            inline=False,
        )
        embed.set_footer(text="Mr. Ratburn • Reaction-Role Editor")
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
        await interaction.response.send_modal(
            PostDetailsModal(self)
        )

    @discord.ui.button(
        label="Save draft",
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

        post_id = self.bot.database.create_reaction_role_post(
            guild_id=self.guild_id,
            channel_id=self.channel_id,
            title=self.title,
            description=self.description,
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=(
                f"Draft saved successfully! **Post ID:** `{post_id}`\n"
                f"**Channel:** {channel.mention}\n\n"
                "You can now configure its role entries."
            ),
            embed=self.create_embed(),
            view=self,
        )

        self.stop()

        await interaction.followup.send(
            embed=discord.Embed(
                title="Configure a role",
                description=(
                    "Choose or create a role, configure its reaction "
                    "and description, then save the entry."
                ),
                color=discord.Color.dark_teal(),
            ),
            view=RoleEditorView(
                bot=self.bot,
                guild_id=self.guild_id,
                post_id=post_id,
            ),
            ephemeral=True,
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
            content="Reaction-role draft cancelled. Nothing was saved.",
            embed=None,
            view=self,
        )
        self.stop()
