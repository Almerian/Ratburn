from .new_member import NewMember


async def setup(bot):
    await bot.add_cog(NewMember(bot))
