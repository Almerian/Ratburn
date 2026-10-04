from .birthdays import Birthdays


async def setup(bot):
    await bot.add_cog(Birthdays(bot))
