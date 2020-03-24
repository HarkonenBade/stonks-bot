import discord

discord.Member.__str__ = lambda self: self.display_name
