import discord
from discord.ext import commands

async def print_help(self: commands.Context):
    for page in await self.bot.formatter.format_help_for(self, self.command):
        await self.send(page)

commands.Context.print_help = print_help

discord.Member.__str__ = lambda self: self.display_name
