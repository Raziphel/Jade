from asyncio import TimeoutError
from random import randint
from re import findall
from typing import Optional

from discord import RawReactionActionEvent, Embed, DiscordException
from discord.ext.commands import Cog

import utils


class VerificationCancelled(BaseException):
    pass


def get_only_numbers(data: str):
    try:
        numbers_list = findall(r'\d+', data)
        numbers = ''.join(numbers_list)

        return int(numbers)
    except ValueError:
        return None


class verify(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener('on_ready')
    async def setup_verification_and_rules(self):
        guild = self.bot.get_guild(self.bot.config['guild_id'])

        # Verification banners setup
        verify_channel = guild.get_channel(self.bot.config['channels']['verify'])
        await self.setup_verification_banners(verify_channel)

        # Rules setup
        rules_channel = guild.get_channel(self.bot.config['channels']['rules'])
        await self.setup_rules_banners(rules_channel)

    async def setup_verification_banners(self, ch):
        banners = ['welcome', 'tos', 'verify']
        for banner in banners:
            banner_id = self.bot.config['purgatory_banners'][f'{banner}_id']
            banner_url = self.bot.config['purgatory_banners'][f'{banner}_url']
            banner_message = await ch.fetch_message(banner_id)
            await banner_message.edit(content=banner_url)

        embeds = [embed1, embed2, embed3]
        rules = {i: await ch.fetch_message(self.bot.config['welcome_messages'][str(i)]) for i in range(1, 4)}
        for i, rule in rules.items():
            await self.bot.message_edit_manager.queue_edit(message=rule, new_content="", new_embed=embeds[i - 1])

    async def setup_rules_banners(self, ch):
        banners = ['etiquette', 'respect', 'society', 'council']
        for banner in banners:
            banner_id = self.bot.config['purgatory_banners'][f'{banner}_id']
            banner_url = self.bot.config['purgatory_banners'][f'{banner}_url']
            banner_message = await ch.fetch_message(banner_id)
            await banner_message.edit(content=banner_url)

        embeds = [embed1, embed2, embed3, embed4]
        rules = {i: await ch.fetch_message(self.bot.config['rules_messages'][str(i)]) for i in range(1, 5)}
        for i, rule in rules.items():
            await self.bot.message_edit_manager.queue_edit(message=rule, new_content="", new_embed=embeds[i - 1])

    @Cog.listener('on_raw_reaction_add')
    async def verify(self, payload: RawReactionActionEvent):
        if payload.channel_id != self.bot.config['channels']['verify'] or self.bot.get_user(payload.user_id).bot:
            return

        # Get reaction emoji
        emoji = payload.emoji.name if payload.emoji.is_unicode_emoji() else str(payload.emoji.id)

        # Verification process
        if emoji == "✅":
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            verified_role = guild.get_role(self.bot.config['access_roles']['verified'])

            if verified_role not in member.roles:
                try:
                    await self.verification(member)
                except VerificationCancelled:
                    await member.send("Verification cancelled.")
                except TimeoutError:
                    await member.send("You took too long to verify.")
                except DiscordException as e:
                    await self.discord_log.send(f"Error during verification: {e}")

        # Manage reactions
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if message and sum(reaction.count for reaction in message.reactions) > 5000:
            await message.clear_reactions()
            for reaction in message.reactions:
                if reaction.emoji not in emoji:
                    await message.add_reaction(reaction.emoji)

    async def verification(self, author):
        async def get_input(prompt: str, timeout: float = 300.0, max_length: Optional[int] = 50):
            await author.send(embed=utils.Embed(color=randint(1, 0xffffff), desc=prompt))
            return await self.get_response(author, timeout, max_length)

        try:
            invite_source = await get_input("Where did you receive an invitation to Serpent's Garden from?")
            age = await self.get_verified_age(author)
            color_choice = await self.get_color_choice(author)

            mod, tracking = self.update_mod_and_tracking(author, age, color_choice)
            verify_answer = await get_input("Do you agree to the server's TOS and plan to read the rules once verified? (Only answer is 'yes')")

            if verify_answer.content.lower() == "yes" and age > 12:
                await author.send(embed=Embed(description="**You have been accepted!**"))
                await utils.UserFunctions.verify_user(author)
            else:
                await author.send(embed=Embed(description="**Your verification has been denied!**"))

        except (DiscordException, VerificationCancelled, TimeoutError) as e:
            await self.handle_verification_exception(e, author)

    async def get_verified_age(self, author):
        age_answer = await get_input("How old are you?")
        return get_only_numbers(age_answer.content)

    async def get_color_choice(self, author):
        color_response = await get_input("What's your favorite color? (Say a color name or a hex code)")
        return utils.Colors.get(color_response.content.lower()) or int(color_response.content.strip('#'), 16)

    async def handle_verification_exception(self, e, author):
        if isinstance(e, DiscordException):
            await author.send("I can't send you a DM! Please enable DMs and try again.")
        elif isinstance(e, VerificationCancelled):
            await author.send("Verification cancelled.")
        elif isinstance(e, TimeoutError):
            await author.send("Sorry, but you took too long to respond. Please click the check emoji again to verify.")


def setup(bot):
    bot.add_cog(verify(bot))
