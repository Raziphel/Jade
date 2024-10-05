from discord import Embed
from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta
from random import choice, randint
from datetime import datetime as dt, timedelta
import utils

class Seasonal(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.treats = [
            "🍬 Candy",
            "🍫 Chocolate",
            "🍭 Lollipop",
            "🍪 Cookie",
            "🍩 Donut",
            "🍰 Cake",
            "🍯 Honeycomb",
            "🍎 Candy Apple",
            "🍡 Mochi",
            "🍦 Ice Cream"
        ]
        self.tricks = [
            "👻 Spooky Ghost",
            "🕷️ Spider",
            "💀 Skeleton",
            "🎃 Evil Pumpkin",
            "🐍 Snake",
            "🦇 Bat",
            "🧟 Zombie",
            "🧛 Vampire",
            "👹 Demon",
            "🌕 Full Moon Werewolf"
        ]

    @cooldown(1, 7200, BucketType.user)  # 2-hour cooldown per user
    @command(application_command_meta=ApplicationCommandMeta())
    async def trick_or_treat(self, ctx):
        """Get a trick or get a treat!"""

        # Get user's coins record
        coins_record = utils.Coins_Record.get(ctx.author.id)

        # Decide if the user gets a treat or a trick
        outcome = choice(["treat", "trick"])

        if outcome == "treat":
            # User gets coins as a treat
            coins = randint(2000, 6000)  # Random amount of coins
            treat = choice(self.treats)
            await ctx.send(
                f"**🎉 {ctx.author.mention}, you went trick-or-treating and got a treat: {treat}! You earned {coins:,} coins!**"
            )
            # Update user's coins using CoinFunctions
            await utils.CoinFunctions.earn(earner=ctx.author, amount=coins)

        else:
            # User loses coins as a trick
            coins = randint(1000, 4000)  # Random amount of coins lost
            trick = choice(self.tricks)
            await ctx.send(
                f"**😈 {ctx.author.mention}, you went trick-or-treating and got a trick: {trick}! You lost {coins:,} coins!**"
            )
            # Retrieve user's currency and reduce their coins
            c = utils.Currency.get(ctx.author.id)
            c.coins -= coins

            # Update coins record for lost coins
            coins_record.lost += coins

            # Save the reduced currency to the database
            async with self.bot.database() as db:
                await c.save(db)

        # Save the coins record to the database
        async with self.bot.database() as db:
            await coins_record.save(db)

# The setup function to load the cog
def setup(bot):
    bot.add_cog(Seasonal(bot))
