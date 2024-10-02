from discord.ext import tasks
from discord.ext.commands import Cog
import utils
import logging


class Taxes(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_loop.start()

    @tasks.loop(hours=24)
    async def daily_loop(self):
        """Main loop to tax and fix the economy every 24 hours."""
        guild = self.bot.get_guild(self.bot.config['guild_id'])

        # Fix the economy
        server_currency = utils.Currency.get(self.bot.user.id)
        total_coins = utils.Currency.get_total_coins()
        difference = self.bot.config['total_coins'] - total_coins

        if difference != 0:
            server_currency.coins += difference
            async with self.bot.database() as db:
                await server_currency.save(db)
            print(f"Adjusted economy by {difference:,} coins.")

        # Tax members
        total_taxed = 0
        for member in guild.members:
            try:
                currency = utils.Currency.get(member.id)
                if currency.coins > 9:
                    currency.coins -= 100
                    total_taxed += 100
                    async with self.bot.database() as db:
                        await currency.save(db)
                elif currency.coins > 0:
                    currency.coins = 0
                    async with self.bot.database() as db:
                        await currency.save(db)
            except Exception as e:
                print(f"Error taxing {member.name}: {str(e)}")

        print(f"Taxed the server for a total of: {total_taxed:,} coins")

    @daily_loop.before_loop
    async def before_daily_loop(self):
        """Wait until the bot is ready before running the loop."""
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Taxes(bot))
