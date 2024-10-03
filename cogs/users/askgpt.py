import openai
from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta


class Askgbt(Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldown(1, 30, BucketType.user)
    @command(application_command_meta=ApplicationCommandMeta())
    async def ask_gpt(self, ctx, *, question):
        """Command to ask GPT a question."""
        await ctx.send("Let me think... 🤔")

        try:
            # Call OpenAI API
            response = openai.Completion.create(
                engine="babbage-002",  #
                prompt=question,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )

            # Extract the response text
            answer = response.choices[0].text.strip()

            # Send the response back to Discord
            await ctx.send(f"🤖: {answer}")

        except Exception as e:
            await ctx.send(f"Oops, something went wrong: {e}")


# Register the cog
def setup(bot):
    bot.add_cog(Askgbt(bot))
