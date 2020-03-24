import discord
from discord.ext import commands

class Misc(commands.Cog):

    @commands.command()
    async def echo(self, ctx: commands.Context):
        await ctx.send(content="Hey!")
