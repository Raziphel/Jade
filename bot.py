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

@bot.tree.command(name="sync", description="Manually syncs all slash commands.")
async def sync(interaction: discord.Interaction):
    await bot.tree.sync()
    await interaction.response.send_message("✅ Slash commands have been synced!", ephemeral=True)


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