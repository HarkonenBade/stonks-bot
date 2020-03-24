import os

from . import extensions
from .bot import Bot

def main():
    client = Bot()
    client.load_extension("cogs")
    client.run(os.environ['DISCORD_TOKEN'])
