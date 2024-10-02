from datetime import datetime as dt, timedelta
from random import choice

import discord
from discord import Embed
from discord.ext import commands, tasks

import utils


async def manage_reactions(message):
    """Handle message reactions cleanup and re-adding of correct reactions."""
    # Maximum reaction threshold before clearing all reactions
    max_reactions = 69
    current_reactions = sum(reaction.count for reaction in message.reactions)

    if current_reactions > max_reactions:
        await message.clear_reactions()

        # Add back the appropriate reactions
        ticket_options = ["🍏", "🍎", "🍐", "🍋", "🍪"]
        for emoji in ticket_options:
            await message.add_reaction(emoji)


class LotteryHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lottery_update.start()
        self.lottery_runner.start()
        self.lottery_pot_increaser.start()
        self.previous_winner_message = None

    def cog_unload(self):
        self.lottery_update.cancel()
        self.lottery_runner.cancel()
        self.lottery_pot_increaser.cancel()

    @tasks.loop(minutes=1)
    async def lottery_update(self):
        """Updates the lottery message every minute with the latest stats."""
        await self.bot.wait_until_ready()

        # Fetch the lottery and the necessary Discord objects
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])
        lottery = utils.Lottery.get(1)
        tickets = utils.Currency.get_total_tickets()

        # Update lottery messages with the latest prize pool info
        msg = await channel.fetch_message(self.bot.config['lottery_messages']['1'])

        # Ticket options with emojis and costs
        ticket_options = {
            "🍏": (1, 3000),
            "🍎": (5, 10000),
            "🍐": (20, 25000),
            "🍋": (50, 50000)
        }

        # Build the embed with ticket information
        embed = Embed(
            title="Welcome to the Lottery!",
            description="Click 🍪 to get updates!\nThe more tickets you buy, the better your odds!",
            color=0xff00ff
        )

        # Add ticket options to the embed
        for emoji, (tickets, cost) in ticket_options.items():
            embed.add_field(
                name=f"{emoji} - {tickets} Tickets",
                value=f"Cost: {cost:,} coins",
                inline=False
            )

        embed.add_field(name="Current Prize Pool", value=f"Coins: {lottery.coins:,}", inline=False)

        await msg.edit(embed=embed)

    @tasks.loop(hours=1)
    async def lottery_pot_increaser(self):
        """Increases the lottery pot every hour."""
        await self.bot.wait_until_ready()

        lottery = utils.Lottery.get(1)
        lottery.coins += 50  # Add a fixed amount to the pot every hour

        async with self.bot.database() as db:
            await lottery.save(db)

    @tasks.loop(minutes=1)
    async def lottery_runner(self):
        """Runs the lottery every week and announces the winner."""
        await self.bot.wait_until_ready()

        lottery = utils.Lottery.get(1)
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])

        # Check if it's time to run the lottery
        if lottery.lot_time is None or dt.now() >= lottery.lot_time + timedelta(days=7):
            # Remove the previous winner message if it exists
            if self.previous_winner_message:
                try:
                    await self.previous_winner_message.delete()
                except discord.NotFound:
                    pass  # Message was already deleted or not found

            lottery.lot_time = dt.now()

            # Fetch all tickets and select a winner based on the weight of tickets
            users_with_tickets = await self.bot.database().fetch(
                "SELECT user_id, tickets FROM currency WHERE tickets > 0")
            all_tickets = [user_id for user_id, tickets in users_with_tickets for _ in range(tickets)]

            if not all_tickets:
                await channel.send(embed=Embed(description="No one entered the lottery this week. No winner."))
                return

            winner_id = choice(all_tickets)
            winner = guild.get_member(winner_id)

            # Announce the winner and store the message
            winner_message = await channel.send(
                embed=Embed(description=f"🎉 Congratulations! The winner of the lottery is: **{winner.display_name}**!"))
            self.previous_winner_message = winner_message  # Store the winner message for later removal

            # Distribute the prize
            winner_currency = utils.Currency.get(winner.id)
            winner_currency.coins += lottery.coins

            # Reset lottery
            lottery.last_winner_id = winner.id
            lottery.last_amount = lottery.coins
            lottery.coins = 0

            # Save changes to the database
            async with self.bot.database() as db:
                await lottery.save(db)
                await winner_currency.save(db)

            # Reset everyone's tickets
            await self.bot.database().execute("UPDATE currency SET tickets = 0")

    @commands.Cog.listener('on_raw_reaction_add')
    async def lot_buy(self, payload):
        """Handles lottery ticket purchases based on reactions."""
        if payload.channel_id != self.bot.config['channels']['lottery']:  # Lottery channel
            return

        # Ensure the user is not a bot
        if self.bot.get_user(payload.user_id).bot:
            return

        # Fetch user, lottery, and roles
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        currency = utils.Currency.get(member.id)
        lottery = utils.Lottery.get(1)

        role_restricted = utils.DiscordGet(guild.roles, id=self.bot.config['lottery_roles']['winner'])
        if role_restricted in member.roles:
            await member.send("You are restricted from participating in the lottery.")
            return

        emoji = str(payload.emoji)

        # Mapping of ticket options to cost
        ticket_options = {
            "🍏": (1, 3000),
            "🍎": (5, 10000),
            "🍐": (20, 25000),
            "🍋": (50, 50000)
        }

        if emoji == "🍪":
            updates_role = utils.DiscordGet(guild.roles, id=self.bot.config['lottery_roles']['ping'])
            if updates_role not in member.roles:
                await member.add_roles(updates_role, reason="Subscribed to lottery pings.")
                await member.send("You have subscribed to lottery pings.")
            else:
                await member.remove_roles(updates_role, reason="Unsubscribed from lottery pings.")
                await member.send("You have unsubscribed from lottery pings.")
            return

        # Process ticket purchase based on emoji reaction
        if emoji in ticket_options:
            tickets, cost = ticket_options[emoji]

            if currency.coins >= cost:
                # Deduct the coins and add tickets
                currency.coins -= cost
                currency.tickets += tickets
                lottery.coins += cost

                # Confirmation via DM with details of the purchase
                embed = Embed(
                    title="Lottery Ticket Purchase Confirmation",
                    description=f"You have successfully purchased {tickets} tickets for {cost} coins!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Current Tickets", value=f"{currency.tickets} tickets", inline=False)
                embed.add_field(name="Remaining Coins", value=f"{currency.coins} coins", inline=False)

                await member.send(embed=embed)

            else:
                # If not enough coins
                await member.send(f"You don't have enough coins to buy {tickets} tickets.")

            # Call manage reactions to maintain the reactions on the lottery message
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await manage_reactions(message)


@tasks.loop(minutes=10)
async def lottery_leaderboard_update(self):
    """Updates the lottery leaderboard message every 10 minutes."""
    await self.bot.wait_until_ready()

    # Fetch the necessary Discord objects
    guild = self.bot.get_guild(self.bot.config['guild_id'])
    channel = guild.get_channel(self.bot.config['channels']['lottery'])

    # Fetch the leaderboard message
    msg = await channel.fetch_message(self.bot.config['lottery_messages']['2'])

    # Fetch the top 10 users with the most tickets from the database
    async with self.bot.database() as db:
        top_users = await db.fetch(
            "SELECT user_id, tickets FROM currency WHERE tickets > 0 ORDER BY tickets DESC LIMIT 10"
        )

    # Build the leaderboard embed
    embed = Embed(
        title="🎟️ Lottery Leaderboard",
        description="Top 10 users with the most tickets",
        color=0xffd700
    )

    if not top_users:
        embed.add_field(name="No tickets yet!", value="Be the first to buy some tickets!", inline=False)
    else:
        # Add top users to the embed
        for idx, row in enumerate(top_users, 1):
            user = self.bot.get_user(row['user_id']) or (await self.bot.fetch_user(row['user_id']))
            tickets = row['tickets']
            embed.add_field(
                name=f"#{idx} {user.display_name}",
                value=f"{tickets:,} tickets",
                inline=False
            )

    # Update the leaderboard message
    await msg.edit(embed=embed)



def setup(bot):
    bot.add_cog(LotteryHandler(bot))
