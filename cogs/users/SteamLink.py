from discord.ext.commands import command, Cog, ApplicationCommandMeta


import utils


class SteamLink(Cog):
    def __init__(self, bot):
        self.bot = bot



    @command(application_command_meta=ApplicationCommandMeta())
    async def steamlink(self, ctx, steam_id:str):
        """Links the user's Discord account with their STEAM 64 ID (DEC)"""
        discord_id = ctx.author.id  # Get the Discord user ID from the context

        try:
            # Create or get the UserLink instance
            user_link = utils.UserLink(discord_id, steam_id)

            # Save the user link to the database
            async with self.bot.database() as db:
                await user_link.save(db)

            await ctx.send(f"Successfully linked your Discord account with Steam ID: {steam_id}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(SteamLink(bot))