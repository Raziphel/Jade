# * Discord
from discord.ext.commands import command, Cog, Greedy
from discord import Member, Message, User, ApplicationCommandOption, ApplicationCommandOptionType
from discord.ext.commands import ApplicationCommandMeta

import utils

class NSFW(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property  # + Members Log Channel
    def discord_log(self):
        return self.bot.get_channel(self.bot.config['logs']['server'])

    async def _remove_role(self, user: Member, role_id: int):
        """Helper method to remove a role from a user if it exists."""
        role = utils.DiscordGet(user.guild.roles, id=role_id)
        if role in user.roles:
            try:
                await user.remove_roles(role)
            except Exception as e:
                print(f"Error removing role {role_id} from {user}: {e}")

    @utils.is_mod_staff()
    @command(
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="The user to be revoked NSFW access!",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
            ],
        ),
    )
    async def notnsfw(self, ctx, user: Member):
        """Revokes NSFW access from a user by removing the adult role and assigning underage role."""

        # + Fetch roles from configuration
        adult_role_id = self.bot.config['age_roles']['adult']
        underage_role_id = self.bot.config['age_roles']['underage']

        # Remove 18+ role if assigned and add underage role
        await self._remove_role(user, adult_role_id)
        underage_role = utils.DiscordGet(user.guild.roles, id=underage_role_id)
        await user.add_roles(underage_role)

        # Update moderation records
        mod = utils.Moderation.get(user.id)
        mod.child = True
        mod.adult = False
        async with self.bot.database() as db:
            await mod.save(db)

        # Log the action
        log_msg = utils.Embed(color=0xc77f22, desc=f"# {user.name} has been restricted from NSFW access.")
        await self.discord_log.send(embed=log_msg)
        await ctx.send(embed=log_msg)

    @utils.is_mod_staff()
    @command(
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="The user to be granted NSFW access!",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
            ],
        ),
    )
    async def nsfw(self, ctx, user: Member):
        """Grants NSFW access to a user by adding the adult role and removing underage role."""

        # + Fetch roles from configuration
        adult_role_id = self.bot.config['age_roles']['adult']
        underage_role_id = self.bot.config['age_roles']['underage']

        # Remove underage role if assigned and add adult role
        await self._remove_role(user, underage_role_id)
        adult_role = utils.DiscordGet(user.guild.roles, id=adult_role_id)
        await user.add_roles(adult_role)

        # Update moderation records
        mod = utils.Moderation.get(user.id)
        mod.child = False
        mod.adult = True
        async with self.bot.database() as db:
            await mod.save(db)

        # Log the action
        log_msg = utils.Embed(color=0x339c2a, desc=f"# {user.name} has been granted NSFW access.")
        await self.discord_log.send(content=f"<@{user.id}>", embed=log_msg)
        await ctx.send(content=f"<@{user.id}>", embed=log_msg)

def setup(bot):
    bot.add_cog(NSFW(bot))
