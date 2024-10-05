# * Discord
from discord import ApplicationCommandOption, ApplicationCommandOptionType, Member, User, Embed
from discord.ext.commands import ApplicationCommandMeta, Cog, command

# * Additions
import utils
from typing import Optional
from random import randint


class Staff_Actions(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def message_log(self):
        return self.bot.get_channel(self.bot.config['logs']['messages'])

    @property
    def discord_log(self):
        return self.bot.get_channel(self.bot.config['logs']['server'])

    async def log_action(self, channel, color, title, description=None, thumbnail_url=None):
        """Helper method to log actions to a specific log channel."""
        embed = utils.Embed(color=color, title=title, desc=description)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        await channel.send(embed=embed)

    @utils.is_admin_staff()
    @command(
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="The user to be banned from the server!",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
                ApplicationCommandOption(
                    name="reason",
                    description="The reason for the ban!",
                    type=ApplicationCommandOptionType.string,
                    required=False,
                ),
            ],
        ),
    )
    async def ban(self, ctx, user: Member, *, reason: Optional[str] = "[No Reason Given]"):
        """Bans a user from the server."""
        if not user:
            return await ctx.interaction.response.send_message('Please specify a valid user.')

        # Attempt to send the ban notification to the user
        try:
            await user.send(
                f"# Sorry, you were banned from {ctx.guild} for: {reason}\n\n**Honestly that's a rip...**\n**I doubt you will be missed tho! c:**"
            )
        except:
            pass  # It's okay if we can't send the message (e.g., DMs closed)

        await ctx.guild.ban(user, delete_message_days=0, reason=f'{reason} :: banned by {ctx.author}')

        # Send feedback and log the ban
        feedback = f"# {user.name} has been banned!\nBy: {ctx.author}\nReason :: {reason}"
        await ctx.interaction.response.send_message(embed=utils.Embed(color=0xc77f22, desc=feedback))
        await self.log_action(self.discord_log, 0xc77f22, f"{user.name} has been banned!", feedback)

    @utils.is_mod_staff()
    @command(
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="The user to be banned from using images!",
                    type=ApplicationCommandOptionType.user,
                    required=True,
                ),
            ],
        ),
    )
    async def imageban(self, ctx, user: Member):
        """Bans a user from posting images."""
        mod = utils.Moderation.get(user.id)
        mod.image_banned = True

        async with self.bot.database() as db:
            await mod.save(db)

        guild = self.bot.get_guild(self.bot.config['guild_id'])
        image_pass = utils.DiscordGet(guild.roles, id=self.bot.config['purchase_roles']['image_pass'])

        await user.remove_roles(image_pass, reason="Removed Image Pass role.")

        feedback = f"# {user} is now image pass banned."
        await ctx.interaction.response.send_message(embed=utils.Embed(color=0xc77f22, desc=feedback))
        await self.log_action(self.discord_log, 0xc77f22, f"{user.name} has been image banned.",
                              thumbnail_url=user.avatar.url)

    @utils.is_mod_staff()
    @command(
        aliases=['pr'],
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="User whose messages you want to delete.",
                    type=ApplicationCommandOptionType.user,
                    required=False,
                ),
                ApplicationCommandOption(
                    name="amount",
                    description="Amount of messages to delete.",
                    type=ApplicationCommandOptionType.integer,
                    required=False,
                ),
            ],
        )
    )
    async def prune(self, ctx, user: Optional[User] = None, amount: int = 100):
        """Deletes a specific user's messages, up to a specified amount."""
        if amount > 250:
            return await ctx.interaction.response.send_message("**250 is the maximum amount of messages.**")

        check = (lambda m: m.author.id == user.id) if user else None
        removed = await ctx.channel.purge(limit=amount, check=check)

        feedback = f"# Deleted {len(removed)} messages!"
        await ctx.interaction.response.send_message(embed=utils.Embed(color=randint(1, 0xffffff), desc=feedback))

    @utils.is_mod_staff()
    @command(
        aliases=['pu'],
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="amount",
                    description="Amount of messages to delete.",
                    type=ApplicationCommandOptionType.integer,
                    required=True,
                ),
            ],
        )
    )
    async def purge(self, ctx, amount: int = 100):
        """Purges a specified amount of messages from the channel."""
        if amount > 250:
            return await ctx.interaction.response.send_message("**250 is the maximum amount of messages.**")

        removed = await ctx.channel.purge(limit=amount)

        feedback = f"# Deleted {len(removed)} messages!"
        await ctx.interaction.response.send_message(embed=utils.Embed(desc=feedback))
        await self.log_action(
            self.message_log, 0xc74822, f"{ctx.author} purged {amount} messages from {ctx.channel.name}!"
        )

    @utils.is_mod_staff()
    @command(
        aliases=['cl'],
        application_command_meta=ApplicationCommandMeta(),
    )
    async def clean(self, ctx):
        """Cleans up bot-related messages."""
        check = lambda m: m.author.id == self.bot.config['bot_id'] or m.id == ctx.message.id or m.content.startswith(
            self.bot.config['prefix'])
        await ctx.channel.purge(check=check)


def setup(bot):
    bot.add_cog(Staff_Actions(bot))
