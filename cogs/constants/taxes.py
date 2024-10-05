from discord.ext import tasks
from discord.ext.commands import Cog
import utils
import logging


class Taxes(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_loop.start()

    @tasks.loop(hours=1)
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

        total_taxed = 0

        # Tax members
        async with self.bot.database() as db:
            # Fetch all users from the database
            all_users = await utils.Currency.get_all_users_from_db(db)

            for user in all_users:
                try:
                    # Tax logic remains the same
                    if user.coins > 10:
                        user.coins -= 10
                        total_taxed += 10
                    else:
                        total_taxed += user.coins
                        user.coins -= user.coins

                    # Save the updated currency back to the database
                    await user.save(db)

                except Exception as e:
                    print(f"Error taxing user {user.user_id}: {str(e)}")

        # Add taxed coins to the server's currency
        server_currency = utils.Currency.get(self.bot.user.id)
        server_currency.coins += total_taxed
        async with self.bot.database() as db:
            await server_currency.save(db)


        print(f"Taxed the server for a total of: {total_taxed:,} coins")

    @daily_loop.before_loop
    async def before_daily_loop(self):
        """Wait until the bot is ready before running the loop."""
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Taxes(bot))
