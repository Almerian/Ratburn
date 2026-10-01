import discord
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.bot.database.get_config(member.guild.id)

        if not config["welcome_channel_id"]:
            return

        channel = member.guild.get_channel(
            config["welcome_channel_id"]
        )

        if channel is None:
            return

        await channel.send(
            "Welcome! Just take a moment to get situated, if you please."
        )


async def setup(bot):
    await bot.add_cog(Welcome(bot))
