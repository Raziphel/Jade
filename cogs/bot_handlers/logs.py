
#* Discord
from discord import Game
from discord.ext.commands import Cog, CommandOnCooldown
#* Additions
from random import randint
import math

import utils

class log_handler(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def bot_log(self):
        """Returns the bot log channel."""
        return self.bot.get_channel(self.bot.config['logs']['bot'])

    @property
    def discord_log(self):
        """Returns the server log channel."""
        return self.bot.get_channel(self.bot.config['logs']['server'])

    @property
    def message_log(self):
        """Returns the message log channel."""
        return self.bot.get_channel(self.bot.config['logs']['messages'])

    @property
    def staff_log(self):
        """Returns the staff log channel."""
        return self.bot.get_channel(self.bot.config['logs']['staff'])

    @property
    def adult_log(self):
        """Returns the adult log channel."""
        return self.bot.get_channel(self.bot.config['logs']['adult'])

    # Colors for logging
    COLORS = {
        'positive': 0x339c2a,
        'negative': 0xc74822,
        'warning': 0xc77f22,
        'special': lambda: randint(1, 0xffffff)
    }

    #! Brand-new members joining
    @Cog.listener()
    async def on_member_join(self, member):
        await self.discord_log.send(embed=utils.Embed(color=self.COLORS['positive'], title=f"{member.name} has entered the garden and needs verification."))


    #! Logs
    @Cog.listener()
    async def on_ready(self):
        print('Serpent is now online.')

        if not self.bot.connected:
            await self.bot.change_presence(activity=Game(name="Database is Down!!!"))
        else:
            await self.bot.change_presence(activity=Game(name=f"in the mind..."))


        #+ Secret bullshit bro...  Don't question this...
        if math.floor(self.bot.latency*1000) <= 100: 
            await self.bot_log.send(embed=utils.Embed(color=self.COLORS['positive'], title=f"Serpent is Online!", desc=f"Perfect Restart."))
        elif math.floor(self.bot.latency*1000) <= 420:
            await self.bot_log.send(embed=utils.Embed(color=self.COLORS['negative'], title=f"Serpent is Online!", desc=f"Weird Restart."))
        elif math.floor(self.bot.latency*1000) > 200:
            await self.bot_log.send(embed=utils.Embed(color=self.COLORS['warning'], title=f"Serpent is Online!", desc=f"Discord Connection Refresh"))


    @Cog.listener()
    async def on_guild_join(self, guild):
        user_count = len(set(self.bot.get_all_members()))
        await self.bot_log.send(embed=utils.Embed(color=self.COLORS['positive'], title=f"The bot has joined {guild.name}", desc=f"Bot now manages: {user_count:,} users"))
        

    @Cog.listener()
    async def on_guild_remove(self, guild):
        user_count = len(set(self.bot.get_all_members()))
        await self.bot_log.send(embed=utils.Embed(color=self.COLORS['negative'], title=f"The bot has left {guild.name}", desc=f"Bot now manages: {user_count:,} users"))

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        # Ignore cooldown errors
        if isinstance(error, CommandOnCooldown):
            return  # Simply return to ignore the error

        # Log other errors to the bot log
        await self.bot_log.send(f"Command failed - `{error!s}`;")

        # Re-raise the error so it can be handled by default or other handlers
        raise error


    #! Guild Logs
    @Cog.listener()
    async def on_member_remove(self, member):
        try:
            if member.bot: return
            await self.discord_log.send(embed=utils.Embed(color=self.COLORS['negative'], title=f"{member.name} has left the Cult.", thumbnail=member.avatar.url))
            c = utils.Currency.get(member.id)
            c.coins = 0
            async with self.bot.database() as db:
                await c.save(db)
        except Exception as e:
            await self.bot_log.send(f"Error during on_member_remove: {str(e)}")

    @Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            await self.discord_log.send(embed=utils.Embed(color=self.COLORS['warning'], title=f"Nickname Changed",
                                                          desc=f"{before.mention} changed their nickname from {before.nick} to {after.nick}."))

    @Cog.listener()
    async def on_member_ban(self, member):
        try:
            await self.discord_log.send(embed=utils.Embed(color=self.COLORS['warning'], title=f"Member Banned", desc=f"{member} has been banned!"))
        except: pass #? Fail Silently


    @Cog.listener()
    async def on_member_unban(self, member):
        try:
            await self.discord_log.send(embed=utils.Embed(color=self.COLORS['positive'], title=f"Member Unbanned", desc=f"{member} has been unbanned!"))
        except: pass #? Fail Silently


    @Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot: return #? Check it's not a bot.
        image = None
        if message is None:
            return #? Check it's a message with content?
        if message.channel.name is None:
            return #? Check it's a channel.
        if message.author.id == 159516156728836097: 
            return #? Not Razi tho.
        if message.attachments: 
            image = message.attachments[0].url 
        name_list = list(message.channel.name)

        if any(item in name_list for item in ["🔞"]):
            channel = self.adult_log
        elif any(item in name_list for item in ['😢', "✨"]):
            channel = self.staff_log
        elif any(item in name_list for item in ['👑', "🌷", "📭", "📝"]):
            return
        else: channel = self.message_log

        try:
            await channel.send(embed=utils.Embed(color=self.COLORS['negative'], title=f"Message Deleted", desc=f"\"{message.content}\"\n**Channel:** <#{message.channel.id}>\n**Author:** {message.author.mention}", thumbnail=message.author.avatar.url, image=image))
        except: pass



    @Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot: return
        if before.content == after.content: return
        if before.author.id == 159516156728836097: return #? Not Razi tho
        name_list = list(before.channel.name)

        if any(item in name_list for item in ['🔞']):
            channel = self.adult_log
        elif any(item in name_list for item in ['🔥', "✨"]):
            channel = self.staff_log
        elif any(item in name_list for item in ['👑', "🌷", "📯", "📝"]):
            return
        else: channel = self.message_log
        try:
            await channel.send(embed=utils.Embed(color=self.COLORS['warning'], title=f"Message Edited", desc=f"**Author:** {before.author.mention}\n**Channel:** <#{before.channel.id}>\n**Before:**\n{before.content}\n\n**after:**\n{after.content}", thumbnail=before.author.avatar.url))
        except: pass



    @Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        try:
            await self.message_log.send(embed=utils.Embed(type=self.COLORS['special'], title=f"Message Pinned", desc=f"A pinned in: <#{channel.id}>\n{last_pin} was made/modify!"))
        except: pass #? Fail Silently





def setup(bot):
    x = log_handler(bot)
    bot.add_cog(x)
