from discord.ext.commands import command, Cog
from discord import Embed, Message, Member, DiscordException
from asyncio import TimeoutError
from typing import Optional
import utils


class VerificationCancelled(Exception):
    pass


class Verification(Cog):

    def __init__(self, bot):
        self.bot = bot

    @property
    def mailbox(self):
        """Retrieve the mailbox channel."""
        return self.bot.get_channel(self.bot.config['channels']['mailbox'])

    async def verification(self, user: Member):
        """Initiates and manages the verification process with the user."""

        table_data = {
            'invited': None,
            'reason': None,
            'age': None,
            'color': None,
        }

        async def get_input(prompt: str, timeout: float = 120.0, max_length: Optional[int] = 50):
            """Prompts the user for input, validates, and handles cancellations."""
            await user.send(embed=utils.SpecialEmbed(desc=prompt))

            def check(msg):
                return msg.author.id == user.id and not msg.guild

            try:
                message = await self.bot.wait_for('message', check=check, timeout=timeout)

                if message.content.lower() == 'cancel':
                    raise VerificationCancelled
                elif len(message.content) > max_length:
                    await user.send(f"Your response is too long! Please keep it within {max_length} characters.")
                    return await get_input(prompt, timeout, max_length)
                else:
                    return message.content
            except TimeoutError:
                await user.send('Verification timed out. Please start again by clicking the verification icon.')
                raise

        async def extract_age(content: str) -> Optional[int]:
            """Extracts and validates age from user input."""
            try:
                age = int(content)
                return age if age > 0 else None
            except ValueError:
                await user.send("Please enter a valid age in numbers.")
                return None

        async def process_color(content: str) -> int:
            """Attempts to interpret color from user input as hex or color name."""
            color = utils.Colors.get(content.lower())
            if color:
                return color
            try:
                return int(content.strip('#'), 16)
            except ValueError:
                await user.send("Invalid color. Using a default color.")
                return 0x0

        try:
            # Gather verification information
            table_data['invited'] = await get_input("Where did you receive an invitation to Serpent's Garden from?")
            table_data['reason'] = await get_input("What is your reason for joining?")

            age_content = await get_input("How old are you?")
            age = await extract_age(age_content)
            if age:
                table_data['age'] = age

            mod = utils.Moderation.get(user.id)
            if age and age < 18:
                mod.child = True

            color_content = await get_input("What's your favourite color? (name or hex code)")
            table_data['color'] = await process_color(color_content)

            # Save information to the database
            t = utils.Tracking.get(user.id)
            t.color = table_data['color']
            async with self.bot.database() as db:
                await t.save(db)
                await mod.save(db)

            # Confirm TOS acceptance
            verify_answer = await get_input(
                "Do you agree to the server's TOS and will read the rules once verified? (Answer 'yes')")
            if verify_answer.lower() != 'yes':
                await user.send("You must agree to the TOS to complete verification.")
                raise VerificationCancelled

            # Send verification message to mailbox
            embed_message = (
                f"**Invitation Source:** {table_data['invited']}\n"
                f"**Reason for Joining:** {table_data['reason']}\n"
                f"**Age:** {table_data['age']}\n"
                f"**Agreed to TOS:** Yes"
            )
            mailbox_embed = utils.MailEmbed(
                footer="Verification",
                message=embed_message,
                color=t.color,
                user=user,
                image=user.avatar_url
            )
            msg = await self.mailbox.send(embed=mailbox_embed)
            await msg.add_reaction('✅')
            await msg.add_reaction('🔴')

            # Notify the user
            await user.send(
                embed=Embed(description="**Your verification request has been sent! Please wait for a response.**"))

        except DiscordException:
            await user.send("I couldn't send a DM. Please enable DMs and try again.")
        except VerificationCancelled:
            await user.send("Verification has been cancelled.")
        except TimeoutError:
            await user.send("Verification timed out. Please restart the process.")


def setup(bot):
    bot.add_cog(Verification(bot))
