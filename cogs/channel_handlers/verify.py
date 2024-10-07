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
        # Define the embed objects here
        embed1 = Embed(description=f"# __**Welcome to Serpent's Garden**__\nSerpent's Garden has an advanced way of prevent scammers, spammers and beggars from the server!\n\n**All members are required to accept the Serpent's - Terms of Service.**", color=0x269f00)

        embed2 = Embed(description=f"# __**Terms of Service**__\nBy choosing to be apart of Serpent's Garden and completing the verification process.\n\n**__You agree to the following__:** \nYou are okay and willing to be subject to lots of gay, furry, degenerates and crazy people.\n\nYou will fully read, understand and will uphold the rules of Serpent's Garden.\n\nI have fully read, understand and will uphold Discord's Terms of Service.", color=0x0ca994)

        embed3 = Embed(description=f"# __**Verification**__\nIf you agree to the Serpent's Terms of Service and are capable of receiving a private message then please click the ✅ reaction button to being the verification process.\n\n**Please make sure the bot is able to message you!!!**", color=0xde1326)

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
        embed1 = Embed(description=f"# Etiquette\n🐍 **All text & voice channels are english only.**\n🐍 **No Drama.** No matter how you feel about others you can't bring it up here.\n🐍 **No Politics, No Religion.**  Only allowed in specific chats.\n🐍 **No Spamming.**  Anything that is cluttering up a chat or repetitive in VC.\n🐍 **No Self Promotion.** Unless done so in a channel dedicated to self promotion.\n", color=0xff0000)

        embed2 = Embed(description=f"# Respect\n🩸 **Excessively argumentative, rude, dismissive, or aggressive members will be removed.** \n🩸 We will not tolerate any instances of offensive behaviour towards anyone, nor any occurrences of **racism, homophobia, transphobia or other types of discriminatory language.**\n🩸 **Personal arguments or conversations.** This should be taken to direct messages if both users wish to continue, rather than affecting the atmosphere/mood/feeling of the chat.", color=0x8F00FF)

        embed3 = Embed(description=f"# Secret Society's\n🔮 **You must respect the areas you choose to be in!**\n🔮 **Not all staff members** manage every area of the server.\n🔮 People who choose to be apart of both can not be treated poorly in different area", color=0xff0000)

        embed4 = Embed(description=f"# Knights, Architects, Council and Overlords\n🔱 **Overlords are owners.**\n🔱 **Decisions made by council are final.**\n🔱 **Knights are only helpers to council.**\n🔱 **All roles get in-game perms.**\n🔱 **Architects are developers** and can still moderate.", color=0x8F00FF)

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
        age_answer = await self.get_input("How old are you?")
        return get_only_numbers(age_answer.content)

    async def get_color_choice(self, author):
        color_response = await self.get_input("What's your favorite color? (Say a color name or a hex code)")
        return utils.Colors.get(color_response.content.lower()) or int(color_response.content.strip('#'), 16)

    async def get_response(self, author, timeout, max_length):
        """Waits for user responses"""
        msg = await self.bot.wait_for('message', check=lambda m: m.author.id == author.id and not m.guild, timeout=timeout)
        if 'cancel' == msg.content.lower():
            raise VerificationCancelled
        if max_length is not None and len(msg.content) > max_length:
            await author.send(f"Sorry, but the value you've responded with is too long. Please keep it within {max_length} characters.")
            return await self.get_response(author, timeout, max_length)
        return msg

    async def handle_verification_exception(self, e, author):
        if isinstance(e, DiscordException):
            await author.send("I can't send you a DM! Please enable DMs and try again.")
        elif isinstance(e, VerificationCancelled):
            await author.send("Verification cancelled.")
        elif isinstance(e, TimeoutError):
            await author.send("Sorry, but you took too long to respond. Please click the check emoji again to verify.")


def setup(bot):
    bot.add_cog(verify(bot))
