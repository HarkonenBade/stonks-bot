from discord.ext import commands

class Manage(commands.Cog):
    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx: commands.Context):
        await ctx.send(f"Ok **{ctx.author}**\n*SYSTEM RESTARTING*")
        ctx.bot.loop.stop()
