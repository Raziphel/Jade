# Discord
from discord import ApplicationCommandOption, ApplicationCommandOptionType, Member, Embed, HTTPException
from discord.ext.commands import command, cooldown, BucketType, Cog, ApplicationCommandMeta
import asyncio

# Utils
import utils

# Set up game states
games = {}
column_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]


class TicTacToe(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def coin_logs(self):
        return self.bot.get_channel(self.bot.config['logs']['coins'])

    # Create an empty TicTacToe grid (3x3)
    def create_grid(self):
        return [["⬜" for _ in range(3)] for _ in range(3)]

    # Display the grid with numbered columns
    def display_grid(self, grid):
        columns = "1️⃣ 2️⃣ 3️⃣\n4️⃣ 5️⃣ 6️⃣\n7️⃣ 8️⃣ 9️⃣\n"
        grid_display = "\n".join(" ".join(row) for row in grid)
        return columns + grid_display

    # Check for a winner (horizontal, vertical, diagonal)
    def check_winner(self, grid, piece):
        # Horizontal
        for row in range(3):
            if all(cell == piece for cell in grid[row]):
                return True
        # Vertical
        for col in range(3):
            if all(grid[row][col] == piece for row in range(3)):
                return True
        # Diagonals
        if all(grid[i][i] == piece for i in range(3)) or all(grid[i][2 - i] == piece for i in range(3)):
            return True
        return False

    # Check if the grid is full (draw)
    def check_draw(self, grid):
        return all(cell != "⬜" for row in grid for cell in row)

    # Ask both players if they want to continue after a draw
    async def ask_continue(self, ctx, challenger, opponent, bet_amount):
        continue_embed = Embed(
            title="It's a Draw!",
            description=f"{challenger.mention} and {opponent.mention}, would you like to play again with the same bet amount of {bet_amount:,} coins?\n\n"
                        f"React with ✅ to continue or ❌ to end the game.",
            color=0xffa500
        )
        msg = await ctx.send(embed=continue_embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check_reaction(reaction, user):
            return user in [challenger, opponent] and str(reaction.emoji) in ["✅", "❌"]

        try:
            # Wait for both players to react
            reaction1, user1 = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_reaction)
            reaction2, user2 = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_reaction)
        except asyncio.TimeoutError:
            await ctx.send("One or both players did not respond in time. The game has ended.")
            return False

        # If either player reacts with ❌, the game ends
        if str(reaction1.emoji) == "❌" or str(reaction2.emoji) == "❌":
            await ctx.send("The players have declined to continue. The game has ended.")
            return False

        # If both react with ✅, continue the game
        if str(reaction1.emoji) == "✅" and str(reaction2.emoji) == "✅":
            await ctx.send(f"Both players agreed to continue! A new Tic-Tac-Toe game has started with {bet_amount:,} coins.")
            return True

        return False

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
    async def tictactoe(self, ctx, opponent: Member, bet_amount: int):
        """Gamble over a game of Tic-Tac-Toe!"""
        challenger = ctx.author
        challenger_coins = utils.Currency.get(challenger.id)
        opponent_coins = utils.Currency.get(opponent.id)
        challenger_skills = utils.Skills.get(challenger.id)

        if not challenger_skills.tictactoe:
            await ctx.send(
                embed=Embed(
                    title="You don't have the skill!",
                    description=f"You must have the Tic-Tac-Toe skill to challenge someone to Tic-Tac-Toe!",
                    color=0xff0000,
                )
            )
            return
        if challenger == opponent:
            await ctx.send(
                embed=Embed(
                    title="You can't play with yourself!",
                    description=f"That's gross...",
                    color=0xff0000,
                )
            )
            return
        if bet_amount < 100:
            await ctx.send(
                embed=Embed(
                    title="Not betting enough!",
                    description=f"Oh come on, you can bet more than {bet_amount:,} coins!",
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
            title="Tic-Tac-Toe Challenge!",
            description=f"{opponent.mention}, you have been challenged by {challenger.mention} to a Tic-Tac-Toe game for {bet_amount:,} coins!\n\n"
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
        except asyncio.TimeoutError:
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

        # Create a new game
        grid = self.create_grid()
        games[ctx.channel.id] = {
            "grid": grid,
            "players": [challenger.id, opponent.id],
            "turn": challenger.id,  # Challenger starts
            "bet_amount": bet_amount
        }

        # Send the initial game state
        game_embed = Embed(
            title="Tic-Tac-Toe Game Started!",
            description=f"{challenger.mention} vs {opponent.mention}\nBet: {bet_amount:,} coins\n\n{self.display_grid(grid)}",
            color=0x3498db
        )
        game_message = await ctx.send(embed=game_embed)

        # Add reactions for each space
        for emoji in column_emojis:
            await game_message.add_reaction(emoji)

        # Store the message ID for game reference
        games[ctx.channel.id]["message_id"] = game_message.id

    # Handle reactions (piece dropping)
    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        msg_id = reaction.message.id
        if reaction.message.channel.id not in games or msg_id != games[reaction.message.channel.id]["message_id"]:
            return  # Not an active game or wrong message

        game = games[reaction.message.channel.id]
        grid = game["grid"]

        # Check if it's the player's turn
        if user.id != game["turn"]:
            return  # Not your turn!

        # Determine the space from the reaction
        if reaction.emoji not in column_emojis:
            return  # Invalid space emoji

        column_index = column_emojis.index(reaction.emoji)  # Get the index (0-based)
        row, col = divmod(column_index, 3)  # Map to row and column for 3x3 grid

        # Remove the player's reaction to keep the board clean
        try:
            await reaction.message.remove_reaction(reaction.emoji, user)
        except HTTPException:
            pass  # Fail silently if removing the reaction fails

        # Place the piece on the grid if the space is empty
        if grid[row][col] != "⬜":
            await reaction.message.channel.send(f"That space is already taken! Try a different one.")
            return

        grid[row][col] = "❌" if user.id == game["players"][0] else "⭕"

        # Check for a winner or a draw
        piece = "❌" if user.id == game["players"][0] else "⭕"
        if self.check_winner(grid, piece):
            winner = user
            loser_id = game["players"][1] if user.id == game["players"][0] else game["players"][0]
            loser = self.bot.get_user(loser_id)

            # Pay the winner using the pay_user function
            try:
                await utils.CoinFunctions.pay_user(payer=loser, receiver=winner, amount=game["bet_amount"], bet=True)
                win_embed = Embed(
                    title="Game Over!",
                    description=f"🎉 {winner.mention} wins the game and takes **{game['bet_amount']:,}** coins! 🎉\n\n{self.display_grid(grid)}",
                    color=0x00ff00
                )
                await reaction.message.channel.send(embed=win_embed)

                # Log the result to the coin log channel
                log_message = f"**Tic-Tac-Toe Winner**: {winner.name} won **{game['bet_amount']:,}** coins and now has a new balance."
                log_channel = self.coin_logs
                if log_channel:
                    await log_channel.send(log_message)

                del games[reaction.message.channel.id]
                return
            except Exception as e:
                await reaction.message.channel.send(
                    embed=Embed(
                        title="Error",
                        description=f"Error occurred when paying the winner: {str(e)}",
                        color=0xff0000
                    )
                )

        elif self.check_draw(grid):
            draw_embed = Embed(
                title="Game Over - It's a Draw!",
                description=f"The game ended in a draw!\n\n{self.display_grid(grid)}",
                color=0xffa500
            )
            await reaction.message.channel.send(embed=draw_embed)

            # Ask players if they want to continue
            challenger = self.bot.get_user(game["players"][0])
            opponent = self.bot.get_user(game["players"][1])
            continue_game = await self.ask_continue(reaction.message.channel, challenger, opponent, game['bet_amount'])

            if continue_game:
                # Reset the grid and restart the game
                games[reaction.message.channel.id]['grid'] = self.create_grid()
                games[reaction.message.channel.id]['turn'] = challenger.id  # Challenger starts again
                game_embed = Embed(
                    title="Tic-Tac-Toe Game Restarted!",
                    description=f"{challenger.mention} vs {opponent.mention}\nBet: {game['bet_amount']:,} coins\n\n{self.display_grid(games[reaction.message.channel.id]['grid'])}",
                    color=0x3498db
                )
                await reaction.message.channel.send(embed=game_embed)
            else:
                del games[reaction.message.channel.id]
            return

        # Change turn to the other player
        game["turn"] = game["players"][1] if user.id == game["players"][0] else game["players"][0]
        next_player = self.bot.get_user(game["turn"])

        # Update the grid and prompt the next player
        grid_embed = Embed(
            title="Tic-Tac-Toe Game",
            description=f"{self.display_grid(grid)}\n\n{next_player.mention}, it's your turn!",
            color=0x3498db
        )
        await reaction.message.edit(embed=grid_embed)


# Add the cog to the bot
def setup(bot):
    bot.add_cog(TicTacToe(bot))
