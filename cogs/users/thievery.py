from discord.ext.commands import command, Cog, BucketType, cooldown, ApplicationCommandMeta
from discord import Member, ApplicationCommandOption, ApplicationCommandOptionType
from datetime import datetime as dt, timedelta
from random import randint

import utils


class Thievery(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    @command(application_command_meta=ApplicationCommandMeta())
    async def larceny(self, ctx):
        """Enable or disable the ability to steal."""
        skills = utils.Skills.get(ctx.author.id)
        cooldown_time = timedelta(hours=2)

        if (skills.larceny_stamp + cooldown_time) >= dt.utcnow():
            remaining_time = skills.larceny_stamp + cooldown_time - dt.utcnow()
            hours, minutes = divmod(remaining_time.seconds // 60, 60)
            return await ctx.interaction.response.send_message(
                embed=utils.Embed(
                    desc=f"You can change your larceny setting in **{hours} hours and {minutes} minutes!**",
                    user=ctx.author
                )
            )

        skills.larceny = not skills.larceny
        status = "enabled" if skills.larceny else "disabled"
        skills.larceny_stamp = dt.utcnow()

        await ctx.interaction.response.send_message(
            embed=utils.Embed(
                desc=f"# Larceny {status.capitalize()}!\nYou can now {'' if skills.larceny else 'no longer '}steal or be stolen from.",
                user=ctx.author)
        )

        async with self.bot.database() as db:
            await skills.save(db)

    @command(
        aliases=['yoink'],
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="The user you would like to steal from!",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
            ],
        ),
    )
    async def steal(self, ctx, user: Member = None):
        """Attempt to steal coins from another user."""
        if not user:
            return await ctx.interaction.response.send_message(
                embed=utils.Embed(desc="Please mention a user to steal from.", user=ctx.author))

        if user.id in [self.bot.user.id, ctx.author.id]:
            return await ctx.interaction.response.send_message(embed=utils.Embed(
                desc=f"You can't steal from {'' if user.id == ctx.author.id else 'yourself or '}the bot!",
                user=ctx.author))

        # Variables
        skills = utils.Skills.get(ctx.author.id)
        target_skills = utils.Skills.get(user.id)

        # Checks
        if not skills.thievery:
            return await ctx.interaction.response.send_message(
                embed=utils.Embed(desc="You need to buy the thievery skill from the shop first!", user=ctx.author))

        if not skills.larceny:
            return await ctx.interaction.response.send_message(
                embed=utils.Embed(desc="You need to enable `/larceny` to steal!", user=ctx.author))

        if not target_skills.larceny:
            return await ctx.interaction.response.send_message(
                embed=utils.Embed(desc=f"{user.mention} hasn't enabled larceny!", user=ctx.author))

        cooldown_time = timedelta(hours=2)
        if (skills.larceny_stamp + cooldown_time) >= dt.utcnow():
            remaining_time = skills.larceny_stamp + cooldown_time - dt.utcnow()
            hours, minutes = divmod(remaining_time.seconds // 60, 60)
            return await ctx.interaction.response.send_message(
                embed=utils.Embed(
                    desc=f"You can't steal for another **{hours} hours and {minutes} minutes!**",
                    user=ctx.author
                )
            )

        # Process stealing
        target_coins = utils.Currency.get(user.id)
        thief_coins = utils.Currency.get(ctx.author.id)
        coins_record_thief = utils.Coins_Record.get(ctx.author.id)
        coins_record_target = utils.Coins_Record.get(user.id)

        # Calculate stolen amount (0.5% to 2% of target's coins)
        amount = randint(int(target_coins.coins * 0.005), int(target_coins.coins * 0.02))

        if target_coins.coins < amount:
            amount = target_coins.coins  # Steal what's available if it's less

        target_coins.coins -= amount
        thief_coins.coins += amount

        skills.larceny_stamp = dt.utcnow()

        # Update coins records
        coins_record_thief.stolen += amount  # Update the thief's stolen record
        coins_record_target.lost += amount  # Update the target's lost record

        # Notifications
        await ctx.interaction.response.send_message(
            content=f"{user.mention}",
            embed=utils.Embed(
                title="🧤 Coins Stolen 🧤",
                desc=f"**{ctx.author.name}** stole **{amount:,} coins** from **{user.name}**!",
                user=ctx.author
            )
        )
        await self.coin_logs.send(
            f"**{ctx.author.name}** stole **{amount:,} coins** from **{user.name}**"
        )

        # Save data to the database
        async with self.bot.database() as db:
            await skills.save(db)
            await thief_coins.save(db)
            await target_coins.save(db)
            await coins_record_thief.save(db)
            await coins_record_target.save(db)


def setup(bot):
    bot.add_cog(Thievery(bot))
