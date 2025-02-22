import os
import asyncio
from glob import glob

from discord import Intents
from serpent import Serpent

intents = Intents.all()
bot = Serpent(
    command_prefix=["."],
    config="config/config.toml",
    secret="config/secret.toml",
    intents=intents
)
logger = bot.logger
extensions = [i.replace(os.sep, '.')[:-3] for i in glob("cogs/*/[!_]*.py")]

async def main():
    """Loads extensions and starts the bot properly."""
    logger.info(f"Loading {len(extensions)} extensions")
    print(f"Loading {len(extensions)} extensions")

    for extension in extensions:
        try:
            print(f"Loading: {extension}")
            await bot.load_extension(extension)  # ✅ Now it's inside an async function
        except Exception as e:
            print(f"Failed to load {extension}: {e}")

    await bot.start(bot.secret['token'])  # ✅ Use 'start()' instead of 'run()' in an async function

if __name__ == "__main__":
    asyncio.run(main())  # ✅ Now 'main()' runs properly with asyncio!
