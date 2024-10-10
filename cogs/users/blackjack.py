# Discord
from discord import ApplicationCommandOption, ApplicationCommandOptionType, Member, Embed, HTTPException
from discord.ext.commands import command, cooldown, BucketType, Cog, ApplicationCommandMeta
import random

# Utils
import utils

# Set up coin tracking and game states
games = {}

class Blackjack(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    # Blackjack card values
    def card_value(self, card):
        if card in ["J", "Q", "K"]:
            return 10
        if card == "A":
            return 11  # Ace will be handled separately in the score calculation
        return int(card)

    # Calculate score for a player's hand
    def calculate_hand(self, hand):
        total = sum(self.card_value(card) for card in hand)
        # Handle Aces: If total is over 21 and there's an Ace, convert the Ace from 11 to 1
        aces = hand.count("A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    # Create a deck of cards
    def create_deck(self):
        deck = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"] * 4
        random.shuffle(deck)
        return deck

    @cooldown(1, 30, BucketType.user)
    @command(
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="opponent",
                    description="The user you want to bet with.",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
                ApplicationCommandOption(
                    name="bet_amount",
                    description="The amount of coins you want to bet.",
                    type=ApplicationCommandOptionType.integer,
                    required=True,
                ),
            ],
        ),
    )
    async def blackjack(self, ctx, opponent: Member, bet_amount: int):
        """Gamble over a game of Blackjack!"""
        challenger = ctx.author
        challenger_coins = utils.Currency.get(challenger.id)
        opponent_coins = utils.Currency.get(opponent.id)
        challenger_skills = utils.Skills.get(challenger.id)


        if challenger_skills.blackjack is False:
            await ctx.send(
                embed=Embed(
                    title="You don't have the skill!",
                    description=f"You must have the Black Jack skill to challenge someone to Black Jack!",
                    color=0xff0000,
                )
            )
            return
        if bet_amount < 100:
            await ctx.send(
                embed=Embed(
                    title="Not betting enough!",
                    description=f"Oh come on you can bet more than {bet_amount:,} coins!",
                    color=0xff0000,
                )
            )
            return
        if bet_amount > challenger_coins.coins:
            await ctx.send(
                embed=Embed(
                    title="Not enough coins!",
                    description=f"You only have {challenger_coins.coins:,} coins, but you tried to bet {bet_amount:,} coins!",
                    color=0xff0000,
                )
            )
            return
        if bet_amount > opponent_coins.coins:
            await ctx.send(
                embed=Embed(
                    title="Opponent doesn't have enough coins!",
                    description=f"{opponent.mention} doesn't have enough coins to bet {bet_amount:,} coins.",
                    color=0xff0000,
                )
            )
            return

        # Ask the opponent to accept the challenge
        challenge_embed = Embed(
            title="Blackjack Challenge!",
            description=f"{opponent.mention}, you have been challenged by {challenger.mention} to a Blackjack game for {bet_amount:,} coins!\n\n"
                        f"React with ✅ to accept or ❌ to decline.",
            color=0x00ff00
        )
        msg = await ctx.send(embed=challenge_embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == opponent and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except TimeoutError:
            await ctx.send(
                embed=Embed(
                    title="Game Canceled",
                    description=f"{opponent.mention} did not respond in time! The challenge has been canceled.",
                    color=0xffa500
                )
            )
            return

        if str(reaction.emoji) == "❌":
            await ctx.send(
                embed=Embed(
                    title="Challenge Declined",
                    description=f"{opponent.mention} declined the challenge! The game has been canceled.",
                    color=0xff0000
                )
            )
            return

        # Create a new game with a shuffled deck
        deck = self.create_deck()

        # Initialize game state
        games[ctx.channel.id] = {
            "players": {
                challenger.id: {"hand": [deck.pop(), deck.pop()], "stand": False},
                opponent.id: {"hand": [deck.pop(), deck.pop()], "stand": False}
            },
            "deck": deck,
            "turn": challenger.id,  # Challenger starts
            "bet_amount": bet_amount
        }

        # Send initial game state
        game_message = await self.send_game_state(ctx, challenger, opponent)

        # Add reactions for the player to hit or stand
        await game_message.add_reaction("✅")  # Hit
        await game_message.add_reaction("🛑")  # Stand

    async def send_game_state(self, ctx, challenger, opponent):
        """Send the current game state to the channel."""
        game = games[ctx.channel.id]

        def hand_display(player_id):
            hand = game["players"][player_id]["hand"]
            return ", ".join(hand)

        # Embed showing both players' hands
        game_embed = Embed(
            title="Blackjack Game",
            description=f"**{challenger.mention}'s Hand**: {hand_display(challenger.id)}\n"
                        f"**{opponent.mention}'s Hand**: {hand_display(opponent.id)}\n\n"
                        f"**{self.bot.get_user(game['turn']).mention}**, it's your turn! React with ✅ to `Hit` or 🛑 to `Stand`.",
            color=0x3498db
        )
        return await ctx.send(embed=game_embed)

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reactions for hit/stand."""
        if user.bot:
            return

        game = games.get(reaction.message.channel.id)
        if not game or game["turn"] != user.id:
            return  # Not the player's turn or no active game

        if str(reaction.emoji) == "✅":  # Hit
            player_hand = game["players"][user.id]["hand"]
            player_hand.append(game["deck"].pop())  # Draw a card

            # Check if player busts (over 21 points)
            if self.calculate_hand(player_hand) > 21:
                await self.end_game(reaction.message.channel, winner_id=self.get_other_player(user.id), loser_id=user.id)
            else:
                # Continue game and send updated state
                await self.send_game_state(reaction.message.channel,
                                           self.bot.get_user(game["players"][0]),
                                           self.bot.get_user(game["players"][1]))

        elif str(reaction.emoji) == "🛑":  # Stand
            game["players"][user.id]["stand"] = True
            game["turn"] = self.get_other_player(user.id)

            # Check if both players have stood, if so, end the game
            if all(p["stand"] for p in game["players"].values()):
                await self.end_game(reaction.message.channel)
            else:
                # Send updated state
                await self.send_game_state(reaction.message.channel,
                                           self.bot.get_user(game["players"][0]),
                                           self.bot.get_user(game["players"][1]))

        try:
            # Remove the player's reaction to keep the board clean
            await reaction.message.remove_reaction(reaction.emoji, user)
        except HTTPException:
            pass  # Fail silently if removing the reaction fails

    async def end_game(self, channel, winner_id=None, loser_id=None):
        """End the game and declare the winner."""
        game = games[channel.id]

        # If no specific winner, calculate winner by hand scores
        if not winner_id:
            p1_score = self.calculate_hand(game["players"][game["players"][0]]["hand"])
            p2_score = self.calculate_hand(game["players"][game["players"][1]]["hand"])
            if p1_score > p2_score:
                winner_id, loser_id = game["players"][0], game["players"][1]
            else:
                winner_id, loser_id = game["players"][1], game["players"][0]

        winner = self.bot.get_user(winner_id)
        loser = self.bot.get_user(loser_id)

        # Pay the winner
        await utils.CoinFunctions.pay_user(payer=loser, receiver=winner, amount=game["bet_amount"], bet=True)

        # Send game result
        await channel.send(
            embed=Embed(
                title="Blackjack Game Over!",
                description=f"🎉 {winner.mention} wins the game and takes **{game['bet_amount']:,}** coins! 🎉",
                color=0x00ff00
            )
        )

        # Log the result
        log_channel = self.coin_logs
        if log_channel:
            await log_channel.send(f"**Blackjack Winner**: {winner.name} won **{game['bet_amount']:,}** coins.")

        del games[channel.id]

    def get_other_player(self, current_player_id):
        """Return the other player's ID."""
        game = games.get(current_player_id)
        players = list(game["players"].keys())
        return players[1] if players[0] == current_player_id else players[0]


# Add the cog to the bot
def setup(bot):
    bot.add_cog(Blackjack(bot))
