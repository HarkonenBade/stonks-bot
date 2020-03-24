from discord.ext import commands

def can_manage():
    def pred(ctx: commands.Context):
        return ctx.bot.is_owner(ctx.author)
    return commands.check(pred)

class Manage(commands.Cog):
    @commands.command(hidden=True)
    @can_manage()
    async def restart(self, ctx: commands.Context):
        await ctx.send("Ok **{author}**\n*SYSTEM RESTARTING*")
        ctx.bot.loop.stop()
