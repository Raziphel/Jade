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
    numbers_list = findall(r'\d+', data)
    if not numbers_list:
        return None
    return int(''.join(numbers_list))


class Verify(Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def discord_log(self):
        return self.bot.get_channel(self.bot.config['logs']['server'])

    async def edit_banner(self, channel, message_id, url):
        banner = await channel.fetch_message(message_id)
        await banner.edit(content=url, embed=None)

    async def update_rules(self, channel, rules, embeds):
        for i, rule in rules.items():
            await self.bot.message_edit_manager.queue_edit(
                message=rule,
                new_content="",
                new_embed=embeds[i - 1]
            )

    @Cog.listener('on_ready')
    async def verify_page(self):
        embed1 = Embed(
            description=(
                "# __**Welcome to Serpent's Garden**__\n"
                "Serpent's Garden has an advanced way of preventing scammers, "
                "spammers, and beggars from the server!\n\n"
                "**All members are required to accept the Serpent's - Terms of Service.**"
            ),
            color=0x269f00
        )
        embed2 = Embed(
            description=(
                "# __**Terms of Service**__\n"
                "By choosing to be a part of Serpent's Garden and completing the verification process.\n\n"
                "**__You agree to the following__:** \n"
                "You are okay and willing to be subject to lots of gay, furry, degenerates, and crazy people.\n\n"
                "You will fully read, understand and will uphold the rules of Serpent's Garden.\n\n"
                "I have fully read, understood and will uphold Discord's Terms of Service."
            ),
            color=0x0ca994
        )
        embed3 = Embed(
            description=(
                "# __**Verification**__\n"
                "If you agree to the Serpent's Terms of Service and are capable of receiving a private message "
                "then please click the ✅ reaction button to begin the verification process.\n\n"
                "**Please make sure the bot is able to message you!!!**"
            ),
            color=0xde1326
        )

        guild = self.bot.get_guild(self.bot.config['guild_id'])
        ch = guild.get_channel(self.bot.config['channels']['verify'])

        await self.edit_banner(ch, self.bot.config['purgatory_banners']['welcome_id'], self.bot.config['purgatory_banners']['welcome_url'])
        await self.edit_banner(ch, self.bot.config['purgatory_banners']['tos_id'], self.bot.config['purgatory_banners']['tos_url'])
        await self.edit_banner(ch, self.bot.config['purgatory_banners']['verify_id'], self.bot.config['purgatory_banners']['verify_url'])

        rules = {}
        for i in range(1, 4):
            rules[i] = await ch.fetch_message(self.bot.config['welcome_messages'][str(i)])

        embeds = [embed1, embed2, embed3]
        await self.update_rules(ch, rules, embeds)

    @Cog.listener('on_ready')
    async def rules(self):
        embed1 = Embed(
            description=(
                "# Etiquette\n🐍 **All text & voice channels are english only.**\n"
                "🐍 **No Drama.** No matter how you feel about others you can't bring it up here.\n"
                "🐍 **No Politics, No Religion.**  Only allowed in specific chats.\n"
                "🐍 **No Spamming.**  Anything that is cluttering up a chat or repetitive in VC.\n"
                "🐍 **No Self Promotion.** Unless done so in a channel dedicated to self promotion."
            ),
            color=0xff0000
        )
        embed2 = Embed(
            description=(
                "# Respect\n🩸 **Excessively argumentative, rude, dismissive, or aggressive members will be removed.**\n"
                "🩸 We will not tolerate any instances of offensive behaviour towards anyone, "
                "nor any occurrences of **racism, homophobia, transphobia, or other types of discriminatory language.**\n"
                "🩸 **Personal arguments or conversations.** This should be taken to direct messages if both users wish to continue, "
                "rather than affecting the atmosphere/mood/feeling of the chat."
            ),
            color=0x8F00FF
        )
        embed3 = Embed(
            description=(
                "# Secret Society's\n🔮 **You must respect the areas you choose to be in!**\n"
                "🔮 **Not all staff members** manage every area of the server.\n"
                "🔮 People who choose to be a part of both cannot be treated poorly in different areas."
            ),
            color=0xff0000
        )
        embed4 = Embed(
            description=(
                "# Knights, Architects, Council, and Overlords\n🔱 **Overlords are owners.**\n"
                "🔱 **Decisions made by the council are final.**\n"
                "🔱 **Knights are only helpers to the council.**\n"
                "🔱 **All roles get in-game perms.**\n"
                "🔱 **Architects are developers** and can still moderate."
            ),
            color=0x8F00FF
        )

        guild = self.bot.get_guild(self.bot.config['guild_id'])
        ch = guild.get_channel(self.bot.config['channels']['rules'])

        await self.edit_banner(ch, self.bot.config['purgatory_banners']['etiquette_id'], self.bot.config['purgatory_banners']['etiquette_url'])
        await self.edit_banner(ch, self.bot.config['purgatory_banners']['respect_id'], self.bot.config['purgatory_banners']['respect_url'])
        await self.edit_banner(ch, self.bot.config['purgatory_banners']['society_id'], self.bot.config['purgatory_banners']['society_url'])
        await self.edit_banner(ch, self.bot.config['purgatory_banners']['council_id'], self.bot.config['purgatory_banners']['council_url'])

        rules = {}
        for i in range(1, 5):
            rules[i] = await ch.fetch_message(self.bot.config['rules_messages'][str(i)])

        embeds = [embed1, embed2, embed3, embed4]
        await self.update_rules(ch, rules, embeds)

    @Cog.listener('on_raw_reaction_add')
    async def verify(self, payload: RawReactionActionEvent):
        if payload.channel_id != self.bot.config['channels']['verify']:
            return

        user = self.bot.get_user(payload.user_id)
        if user.bot:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if payload.emoji.name == "✅":
            verified = utils.DiscordGet(guild.roles, id=self.bot.config['access_roles']['verified'])
            if verified not in member.roles:
                try:
                    await self.verification(author=member)
                except DiscordException:
                    pass

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if sum(reaction.count for reaction in message.reactions) > 5000:
            await message.clear_reactions()
            for reaction in message.reactions:
                await message.add_reaction(reaction.emoji)

    async def verification(self, author):
        async def get_input(prompt: str, timeout: float = 300.0, max_length: Optional[int] = 50):
            await author.send(embed=utils.Embed(color=randint(1, 0xffffff), description=prompt))

            def check(msg):
                return msg.author.id == author.id and not msg.guild

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=timeout)
            except TimeoutError:
                await author.send('Sorry, but you took too long to respond.\nPlease re-click the check emoji and verify.')
                return None

            if 'cancel' == msg.content.lower():
                raise VerificationCancelled

            while max_length and len(msg.content) > max_length:
                await author.send(f"Sorry, but the value you've responded with is too long. Please keep it within {max_length} characters.")
                msg = await self.bot.wait_for('message', check=check, timeout=timeout)

            return msg

        try:
            invited_answer = await get_input("Where did you receive an invitation to Serpent's Garden from?")
            age_answer = await get_input("How old are you?")
            age_answer = get_only_numbers(age_answer.content)

            mod = utils.Moderation.get(author.id)
            if age_answer and age_answer < 18:
                mod.child = True

            color = await get_input("What's your favourite color? (Say a color name or a hex code)")
            colour_value = utils.Colors.get(color.content.lower())
            if colour_value is None:
                try:
                    colour_value = int(color.content.strip('#'), 16)
                except ValueError:
                    colour_value = None

            t = utils.Tracking.get(author.id)
            t.color = colour_value or randint(1, 0xffffff)
            async with self.bot.database() as db:
                await t.save(db)
                await mod.save(db)

            verify_answer = await get_input("Do you agree to the server's TOS and plan to read the rules once verified? (Only answer is 'yes')")

            msg = f"How they were invited: {invited_answer.content}\nAge given: {age_answer}\nAgreed?: {verify_answer.content}"
            await self.discord_log.send(embed=utils.Embed(footer="Verification", description=msg, color=t.color, author=author, image=author.avatar.url))

            if verify_answer.content.lower() == "yes" and age_answer and age_answer > 12:
                embed = Embed(description="**You have been accepted!**")
                await author.send(embed=embed)
                await utils.UserFunctions.verify_user(author)
            else:
                embed = Embed(description="**Your verification has been denied!**")
                await author.send(embed=embed)

        except DiscordException:
            await author.send('I\'m unable to DM you?')

        except VerificationCancelled:
            await author.send('Aborting Verification!')

        except TimeoutError:
            await author.send('Sorry, but you took too long to respond.\nPlease re-click the check emoji and verify.')


def setup(bot):
    bot.add_cog(Verify(bot))
