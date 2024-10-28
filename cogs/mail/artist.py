from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta
from discord import Embed, Message, Member, DiscordException
from asyncio import TimeoutError
from typing import Optional
import utils

class VerificationCancelled(Exception):
    pass

class Artist(Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldown(1, 30, BucketType.user)
    @command(application_command_meta=ApplicationCommandMeta())
    async def verify_artist(self, ctx):
        """Begin verification as an artist to get your own channel."""
        await self.artist_verification(ctx.author)
        await ctx.interaction.response.send_message("I have DM'd you to start the artist verification process!")

    @property
    def mailbox(self):
        """Retrieve the mailbox channel."""
        return self.bot.get_channel(self.bot.config['channels']['mailbox'])

    async def artist_verification(self, user: Member):
        """Initiates and manages the artist verification process with the user."""
        table_data = {
            'link': None,
            'socials': None,
            'nsfw': None,
        }

        async def get_input(prompt: str, max_length: int = 50, timeout: float = 120.0) -> Optional[str]:
            """Prompts the user for input, validates input length, and handles cancellations."""
            await user.send(embed=utils.Embed(desc=prompt, color=0x3498db))

            def check(msg):
                return msg.author.id == user.id and not msg.guild

            try:
                message = await self.bot.wait_for('message', check=check, timeout=timeout)
                content = message.content.strip()

                if content.lower() == 'cancel':
                    raise VerificationCancelled

                if len(content) > max_length:
                    await user.send(f"Your response is too long! Please keep it within {max_length} characters.")
                    return await get_input(prompt, max_length, timeout)

                return content
            except TimeoutError:
                await user.send("Verification timed out. Please use the command again to restart the process.")
                raise

        try:
            # Gather necessary information from the user
            table_data['link'] = await get_input("Please link to your commission info!")
            table_data['socials'] = await get_input("Please link to a social account where you can be supported.")
            nsfw_input = await get_input("Is your art primarily NSFW? (yes/no)")
            table_data['nsfw'] = 'Yes' if nsfw_input.lower() == 'yes' else 'No'

            # Prepare the verification request message
            embed_message = (
                f"**Commission Link:** {table_data['link']}\n"
                f"**Socials Link:** {table_data['socials']}\n"
                f"**Primarily NSFW:** {table_data['nsfw']}"
            )
            mailbox_embed = utils.Embed(
                footer="Artist",
                desc=embed_message,
                color=0x1abc9c,
                user=user,
                image=user.avatar.url,
                mail=True,
            )
            verification_message = await self.mailbox.send(embed=mailbox_embed)
            await verification_message.add_reaction('✅')
            await verification_message.add_reaction('🔴')

            # Notify the user that verification is sent
            await user.send(embed=Embed(description="**Your artist verification request has been submitted! Please wait for a response.**"))

        except DiscordException:
            await user.send("I couldn't send a DM. Please enable DMs and try again.")
        except VerificationCancelled:
            await user.send("Artist verification has been cancelled.")
        except TimeoutError:
            await user.send("Artist verification timed out. Please restart the process.")

def setup(bot):
    bot.add_cog(Artist(bot))
