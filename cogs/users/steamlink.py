from discord import ApplicationCommandOption, ApplicationCommandOptionType
from discord.ext.commands import command, Cog, ApplicationCommandMeta

import utils


class SteamLink(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(
        # Remove aliases if this is a slash command (application command)
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="steamid",  # Fix the typo, remove the extra `)`
                    description="Please put your STEAM64ID (DEC)",
                    type=ApplicationCommandOptionType.string,
                    required=True,
                ),
            ],
        ),
    )
    async def steamlink(self, ctx, steam_id: int):
        """Links the user's Discord account with their STEAM 64 ID (DEC)"""
        discord_id = ctx.author.id  # Get the Discord user ID from the context

        # Check if the steam_id is already linked to another account
        async with self.bot.database() as db:
            existing_link = await db('SELECT discord_id FROM user_link WHERE steam_id = $1', steam_id)

        if existing_link:
            await ctx.send(
                f"The Steam ID `{steam_id}` is already linked to another account. Please contact a staff member.")
            return

        try:
            # Create the UserLink instance
            user_link = utils.UserLink(discord_id, steam_id)

            # Save the user link to the database
            async with self.bot.database() as db:
                await user_link.save(db)

            await ctx.send(f"Successfully linked your Discord account with Steam ID: {steam_id}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(SteamLink(bot))