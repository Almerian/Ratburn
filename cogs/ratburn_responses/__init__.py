from .ratburn_responses import RatburnResponses


async def setup(bot):
    await bot.add_cog(RatburnResponses(bot))
