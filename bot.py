import os
from glob import glob

import discord
from discord.ext import commands

from serpent import Serpent  # Keeping this in case it's part of your bot's structure

intents = discord.Intents.all()

# Replacing Novus-style bot init with discord.py's commands.Bot
bot = Serpent(
    command_prefix=["."],
    config="config/config.toml",
    secret="config/secret.toml",
    intents=intents
)


async def on_ready(self):
    """Sync slash commands and register them with Discord"""
    await self.wait_until_ready()
    await self.tree.sync()  # Sync global commands
    print(f"✅ Bot is ready! Logged in as {self.user}")


logger = bot.logger

# Load all cogs from the "cogs" folder
extensions = [i.replace(os.sep, ".")[:-3] for i in glob("cogs/*/[!_]*.py")]

if __name__ == "__main__":
    """Starts the bot, loading all extensions"""

    logger.info(f"Loading {len(extensions)} extensions")
    print(f"Loading {len(extensions)} extensions")

    for extension in extensions:
        try:
            print(f"Loaded: {extension}")
            bot.load_extension(extension)
        except Exception as e:
            print(f"Failed to load {extension}")
            raise e

    bot.run()