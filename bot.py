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

logger = bot.logger

async def sync_commands():
    """Sync slash commands and register them with Discord"""
    await bot.wait_until_ready()
    await bot.tree.sync()  # Sync global commands
    print(f"✅ Slash commands synced for {bot.user}")

@bot.event
async def on_ready():
    """Runs when the bot is fully ready"""
    await sync_commands()  # Sync commands once the bot is ready
    logger.info(f"✅ Bot is ready! Logged in as {bot.user}")
    print(f"✅ Bot is ready! Logged in as {bot.user}")

# Load all cogs from the "cogs" folder
extensions = [i.replace(os.sep, ".")[:-3] for i in glob("cogs/*/[!_]*.py")]

async def load_extensions():
    """Loads all cogs asynchronously to avoid errors"""
    for extension in extensions:
        try:
            print(f"Loaded: {extension}")
            await bot.load_extension(extension)  # Await it properly
        except Exception as e:
            print(f"Failed to load {extension}")
            raise e

async def main():
    """Starts the bot and loads extensions before running"""
    async with bot:
        await load_extensions()  # Load all extensions properly
        await bot.start(bot.secret["token"])  # Start the bot

if __name__ == "__main__":
    """Runs the bot using asyncio"""
    import asyncio
    asyncio.run(main())
