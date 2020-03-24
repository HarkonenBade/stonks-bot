from . import (management, stonks)

def setup(bot):
    bot.add_cog(management.Manage())
    bot.add_cog(stonks.Stonks())
