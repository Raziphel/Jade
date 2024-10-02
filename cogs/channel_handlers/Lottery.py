import asyncio
from datetime import datetime as dt, timedelta
from random import choice

import discord
from discord import Embed
from discord.ext import commands, tasks

import utils


class LotteryHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lottery_update.start()  # Updates lottery status and ticket options
        self.lottery_runner.start()  # Runs the lottery weekly
        self.lottery_pot_increaser.start()  # Increases the lottery pot every hour
        self.lottery_leaderboard_update.start()  # Updates the leaderboard
        self.previous_winner_message = None

    def cog_unload(self):
        self.lottery_update.cancel()
        self.lottery_runner.cancel()
        self.lottery_pot_increaser.cancel()
        self.lottery_leaderboard_update.cancel()

    @tasks.loop(minutes=1)
    async def lottery_update(self):
        """Updates the lottery message every minute with the latest stats."""
        await self.bot.wait_until_ready()

        # Fetch lottery data and channel
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])
        lottery = utils.Lottery.get(1)

        # Fetch the message to be updated
        msg = await channel.fetch_message(self.bot.config['lottery_messages']['1'])

        # Ticket options with emojis and costs
        ticket_options = {
            "🍏": (1, 3000),
            "🍎": (5, 10000),
            "🍐": (20, 25000),
            "🍋": (50, 50000)
        }

        # Calculate time remaining for the lottery
        if lottery.lot_time is not None:
            time_remaining = (lottery.lot_time + timedelta(days=7)) - dt.now()
            if time_remaining.total_seconds() > 0:
                time_remaining_str = str(time_remaining).split('.')[0]  # Format time without milliseconds
            else:
                time_remaining_str = "Lottery ended. Drawing soon..."
        else:
            time_remaining_str = "Lottery not started yet."

        # Build the embed with ticket information, prize pool, and timer
        description = (
            "🎉 **Welcome to the Weekly Lottery!** 🎉\n\n"
            "💰 **Prize Pool:**\n"
            f"```css\n{lottery.coins:,} coins\n```\n"
            "⏳ **Time Until Draw:**\n"
            f"```css\n{time_remaining_str}\n```\n"
            "**The more tickets you buy, the better your odds of winning!**\n\n"
            "Click 🍪 to get updates!"
        )

        embed = Embed(
            title="🎟️ Lottery Information 🎟️",
            description=description,
            color=discord.Color.purple()  # Use a more vibrant color for the embed
        )

        # Add ticket options to the embed
        embed.add_field(
            name="🎫 **Ticket Options:**",
            value="\n".join(
                [f"{emoji} - **{tickets} Tickets**\nCost: {cost:,} {self.bot.config['emojis']['coin']} coins"
                 for emoji, (tickets, cost) in ticket_options.items()]),
            inline=False
        )

        # Edit the message with updated content
        await msg.edit(content=" ", embed=embed)

        # Call manage reactions to maintain the reactions on the lottery message
        await self.manage_reactions(msg)

    @tasks.loop(minutes=10)
    async def lottery_leaderboard_update(self):
        """Updates the lottery leaderboard message every 10 minutes."""
        await self.bot.wait_until_ready()

        # Fetch the necessary Discord objects
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])

        # Fetch the leaderboard message
        msg = await channel.fetch_message(self.bot.config['lottery_messages']['2'])

        # Get the top 10 users with the most tickets using the sort_tickets method, filter out users with zero tickets
        sorted_users = [user for user in utils.Currency.sort_tickets()[:10] if user.tickets > 0]

        # Calculate the total number of tickets for the chance calculation
        total_tickets = sum(user.tickets for user in sorted_users)

        # Build the leaderboard embed
        embed = Embed(
            title="🎟️ Lottery Leaderboard",
            description="Top 10 users with the most tickets and their chances of winning:",
            color=0xffd700
        )

        if not sorted_users:
            embed.add_field(name="No tickets yet!", value="Be the first to buy some tickets!", inline=False)
        else:
            # Create a leaderboard list with winning chances
            leaderboard_text = ""
            for idx, user in enumerate(sorted_users, 1):
                discord_user = await self.bot.fetch_user(user.user_id)
                win_chance = (user.tickets / total_tickets) * 100 if total_tickets > 0 else 0
                leaderboard_text += f"**#{idx}** {discord_user.display_name} - {user.tickets:,} 🎟 - Chance: {win_chance:.2f}%\n"

            embed.description += f"\n{leaderboard_text}"

        # Update the leaderboard message
        await msg.edit(content=" ", embed=embed)

    @tasks.loop(hours=1)
    async def lottery_pot_increaser(self):
        """Increases the lottery pot every hour."""
        await self.bot.wait_until_ready()

        lottery = utils.Lottery.get(1)
        lottery.coins += 250  # Add a fixed amount to the pot every hour

        # Save the updated lottery pot to the database
        async with self.bot.database() as db:
            await lottery.save(db)

    @tasks.loop(minutes=1)
    async def lottery_runner(self):
        """Runs the lottery every week and announces the winner."""
        await self.bot.wait_until_ready()

        lottery = utils.Lottery.get(1)
        guild = self.bot.get_guild(self.bot.config['guild_id'])
        channel = guild.get_channel(self.bot.config['channels']['lottery'])

        # Check if the lottery time has been set
        if lottery.lot_time is None:
            return  # Skip processing if the lottery hasn't started yet

        # Calculate time remaining for the lottery
        time_remaining = (lottery.lot_time + timedelta(days=7)) - dt.now()

        # Check if it's 1 hour before the draw and send a ping to the lottery ping role
        if timedelta(hours=0) < time_remaining <= timedelta(hours=1):
            # Fetch the lottery ping role
            lottery_ping_role = guild.get_role(self.bot.config['lottery_roles']['ping'])

            # Send a reminder message and ping the role
            await channel.send(
                f"{lottery_ping_role.mention} ⏳ The lottery draw will take place in 1 hour! Get your tickets now!")

        # Check if it's time to run the lottery
        if time_remaining <= timedelta(0):
            # Remove the previous winner message if it exists
            if self.previous_winner_message:
                try:
                    await self.previous_winner_message.delete()
                except discord.NotFound:
                    pass  # Message was already deleted or not found

            lottery.lot_time = dt.now()

            # Get all tickets using the get_total_tickets method
            total_tickets = utils.Currency.get_total_tickets()
            if total_tickets == 0:
                await channel.send(embed=Embed(description="No one entered the lottery this week. No winner."))
                return

            # Fetch all users with tickets using the sort_tickets method
            all_tickets = []
            sorted_users = utils.Currency.sort_tickets()
            for user in sorted_users:
                all_tickets.extend([user.id] * user.tickets)

            # Select a winner
            winner_id = choice(all_tickets)
            winner = guild.get_member(winner_id)

            # Announce the winner and store the message
            winner_message = await channel.send(
                embed=Embed(description=f"🎉 Congratulations! The winner of the lottery is: **{winner.display_name}**!")
            )
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
            for member in guild.members:
                c = utils.Currency.get(member.id)
                c.lot_tickets = 0
                async with self.bot.database() as db:
                    await c.save(db)

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

        # Restriction check for lottery participation
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
                await member.add_roles(updates_role, reason="Subscribed to lottery updates.")
                await member.send("You have subscribed to lottery updates.")
            else:
                await member.remove_roles(updates_role, reason="Unsubscribed from lottery updates.")
                await member.send("You have unsubscribed from lottery updates.")
            return

        # Process ticket purchase based on emoji reaction
        if emoji in ticket_options:
            tickets, cost = ticket_options[emoji]

            # Ensure user has enough coins
            if currency.coins < cost:
                await member.send(f"You don't have enough coins to buy {tickets} tickets.")
                return

            # Send confirmation message
            confirm_embed = Embed(
                title="Confirm Your Lottery Ticket Purchase",
                description=(
                    f"Are you sure you want to purchase {tickets} tickets for {cost:,} {self.bot.config['emojis']['coin']} coins?\n"
                    f"React with ✅ to confirm or ❌ to cancel."
                ),
                color=discord.Color.blue()
            )

            confirmation_msg = await member.send(embed=confirm_embed)

            # Add confirmation and cancellation reactions
            await confirmation_msg.add_reaction("✅")
            await confirmation_msg.add_reaction("❌")

            def check(reaction, user):
                return user == member and str(reaction.emoji) in ["✅",
                                                                  "❌"] and reaction.message.id == confirmation_msg.id

            try:
                # Wait for user to confirm or cancel purchase
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "✅":
                    # Deduct the coins and add tickets if confirmed
                    currency.coins -= cost
                    currency.tickets += tickets
                    lottery.coins += cost

                    # Confirmation via DM with details of the purchase
                    embed = Embed(
                        title="Lottery Ticket Purchase Confirmation",
                        description=f"You have successfully purchased {tickets} tickets for {cost:,} {self.bot.config['emojis']['coin']} coins!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Current Tickets", value=f"{currency.tickets} tickets", inline=False)
                    embed.add_field(name=f"Remaining {self.bot.config['emojis']['coin']} Coins",
                                    value=f"{currency.coins:,} coins", inline=False)

                    await member.send(embed=embed)

                    # Save updates to the database
                    async with self.bot.database() as db:
                        await currency.save(db)
                        await lottery.save(db)

                else:
                    # Send cancellation message if user chose to cancel
                    await member.send("Your lottery ticket purchase has been canceled.")

            except asyncio.TimeoutError:
                # Handle timeout, assume purchase is canceled if no response within the time limit
                await member.send("You took too long to respond. Your lottery ticket purchase has been canceled.")

            finally:
                # Clean up the confirmation message to remove reactions
                try:
                    await confirmation_msg.delete()
                except discord.NotFound:
                    pass  # Message was already deleted

        # Call manage reactions to maintain the reactions on the lottery message
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await self.manage_reactions(message)

    async def manage_reactions(self, message):
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


def setup(bot):
    bot.add_cog(LotteryHandler(bot))
