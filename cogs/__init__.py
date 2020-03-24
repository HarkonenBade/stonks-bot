from . import (management, misc)

def setup(bot):
    bot.add_cog(management.Manage())
    bot.add_cog(misc.Misc())
