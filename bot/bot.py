import traceback

import discord
from discord.ext import commands

DESCRIPTION = """
A bot for tracking the animal crossing stalk market.
"""

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(commands.when_mentioned_or("+"),
                         game=discord.Game(name="+help"),
                         description=DESCRIPTION,
                         help_command=commands.DefaultHelpCommand(dm_help=None),
                         intents=intents)
        self.get_command('help').after_invoke(self.post_help)

    async def post_help(self, ctx: commands.Context):
        await ctx.message.add_reaction("✅")

    async def on_ready(self):
        print('We have logged in as {0.user}'.format(self))
        self.owner_id = (await self.application_info()).owner.id
        await self.pm_owner(content="Yutu starting up")

    async def pm_owner(self, *args, **kwargs):
        owner = await self.fetch_user(self.owner_id)
        await owner.send(*args, **kwargs)

    async def on_command_error(self, ctx: commands.Context, exception: Exception):
        if(isinstance(exception, commands.errors.MissingRequiredArgument) or
           isinstance(exception, commands.errors.BadArgument)):
            await ctx.print_help()
        elif isinstance(exception, commands.CommandOnCooldown):
            await ctx.send(content=str(exception))
        elif isinstance(exception, commands.MissingPermissions):
            await ctx.send(content="I'm sorry {}, I can't let you do that.".format(ctx.author.mention))

        if not isinstance(exception, commands.CommandNotFound):
            await self.pm_owner(content="".join(traceback.format_exception(None, exception, None)))

        await super().on_command_error(ctx, exception)
