from .daily_quiz import DailyQuiz


async def setup(bot):
    await bot.add_cog(DailyQuiz(bot))
