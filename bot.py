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

async def sync_commands():
    """Force-sync slash commands when the bot starts."""
    await bot.wait_until_ready()
    bot.tree.copy_global_to(guild=discord.Object(id=bot.config['guild_id']))  # Sync to your main guild
    await bot.tree.sync()
    print("✅ Slash commands have been synced!")

@bot.event
async def on_ready():
    """Sync commands once bot is ready"""
    await sync_commands()
    print(f"✅ Logged in as {bot.user}")

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