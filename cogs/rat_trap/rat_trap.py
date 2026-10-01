import discord
from discord.ext import commands


class RatTrap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
# Ignore messages that aren't from a server.
        if message.guild is None:
            return

# Ignore bots.
        if message.author.bot:
            return

# Get this server's config.
        config = self.bot.database.get_config(message.guild.id)

# Rat-Trap hasn't been configured.
        if not config["rat_trap_channel_id"]:
            return

# This isn't in the Rat-Trap channel.
        if message.channel.id != config["rat_trap_channel_id"]:
            return

# Get the staff role.
        if not config["staff_role_id"]:
            return

        staff_role = message.guild.get_role(config["staff_role_id"])

# The staff role no longer exists.
        if staff_role is None:
            return

# Staff above are exempt.
        if message.author.top_role >= staff_role:
            return

# Delete the message.
        try:
            await message.delete()
        except discord.HTTPException:
            pass

# Ban the offender.
        try:
            await message.guild.ban(
                message.author,
                reason="Rat-Trap violation"
            )
        except discord.HTTPException:
            pass


async def setup(bot):
    await bot.add_cog(RatTrap(bot))
