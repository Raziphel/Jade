from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import utils


class LevelCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_level_card(self, username, level, xp, next_level_xp, avatar_url):
        # Define card dimensions
        width, height = 450, 150
        bar_width = 350
        bar_height = 20

        # Create a blank image with a solid color
        card = Image.new('RGB', (width, height), (45, 70, 85))  # A similar background color

        draw = ImageDraw.Draw(card)

        # Load a font (you will need a TTF font file)
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 15)

        # Calculate XP progress
        progress = min(xp / next_level_xp, 1.0)

        # Draw the progress bar background
        draw.rectangle([50, 100, 50 + bar_width, 100 + bar_height], fill=(60, 80, 100))

        # Draw the progress
        draw.rectangle([50, 100, 50 + int(bar_width * progress), 100 + bar_height], fill=(85, 170, 220))

        # Add the level, XP, and username
        draw.text((50, 20), username, font=font, fill=(255, 255, 255))
        draw.text((50, 50), f"Level: {level}", font=font, fill=(255, 255, 255))
        draw.text((50, 70), f"XP: {xp} / {next_level_xp}", font=small_font, fill=(255, 255, 255))

        # Download the avatar and paste it into the image (assuming avatar_url is valid)
        avatar = Image.open(io.BytesIO(avatar_url))
        avatar = avatar.resize((60, 60))
        card.paste(avatar, (370, 40))

        # Save to a bytes object
        output_buffer = io.BytesIO()
        card.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        return output_buffer

    @commands.command()
    async def levelcard(self, ctx, member: commands.MemberConverter = None):
        """Generate a level card image for a user."""
        if member is None:
            member = ctx.author

        # Fetch user data from your system (replace with actual logic)
        user_data = await utils.fetch_user_data(member.id)
        username = str(member)
        level = user_data['level']
        xp = user_data['xp']
        next_level_xp = user_data['next_level_xp']

        # Assume avatar_url is fetched in bytes format
        avatar_url = await utils.get_avatar_bytes(member.avatar_url)

        # Create the level card
        buffer = self.create_level_card(username, level, xp, next_level_xp, avatar_url)

        # Send the image
        await ctx.send(file=discord.File(fp=buffer, filename="level_card.png"))


def setup(bot):
    bot.add_cog(LevelCard(bot))
