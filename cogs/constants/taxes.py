from discord.ext import tasks
from discord.ext.commands import Cog

import utils


class Coin_Generator(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_loop.start()


    @tasks.loop(hours=24)
    async def daily_loop(self):
        """Main loop to tax and fix the economy every 24 hours."""

        guild = self.bot.get_guild(self.bot.config['guild_id'])

        #+ Fix the economy!
        sc = utils.Currency.get(self.bot.user.id)
        total_coins = utils.Currency.get_total_coins()
        difference = self.bot.config['total_coins']-total_coins

        sc.coins += difference
        async with self.bot.database() as db:
            await sc.save(db)


        # ! BWAHAHAH HOURLY TAXATION!!!
        total = 0
        for user in guild.members:
            try:
                c = utils.Currency.get(user.id)
                if c.coins > 9:
                    c.coins -= 100
                    total += 10
                    async with self.bot.database() as db:
                        await c.save(db)
                elif c.coins != 0:
                    c.coins = 0
                    async with self.bot.database() as db:
                        await c.save(db)
            except Exception as e:
                print(e)
        print(f"Taxed the server for a total of: {total:,} coins")


    @daily_loop.before_loop
    async def before_daily_loop(self):
        """Wait until the bot is ready before running the loop."""
        await self.bot.wait_until_ready()
