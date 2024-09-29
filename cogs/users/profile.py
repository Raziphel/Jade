import colorsys
import typing
from collections import Counter
from io import BytesIO
from math import floor
import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps
from discord import Member, ApplicationCommandOption, ApplicationCommandOptionType, File, NotFound
from discord.ext.commands import command, Cog, ApplicationCommandMeta

# Image resources directory
resources_directory = "resources"

# General font and image settings
ttf_font_path = f'{resources_directory}/SourceSansPro-Regular.ttf'
ttf_bold_font_path = f'{resources_directory}/SourceSansPro-SemiBold.ttf'
ttf_italic_font_path = f'{resources_directory}/SourceSansPro-Italic.ttf'
default_ttf_size = 19
username_ttf_size = 26
title_ttf_size = 20
progress_bar_ttf_size = 13

fnt = ImageFont.truetype(ttf_font_path, default_ttf_size)
username_fnt = ImageFont.truetype(ttf_bold_font_path, username_ttf_size)
title_fnt = ImageFont.truetype(ttf_italic_font_path, title_ttf_size)
progress_bar_fnt = ImageFont.truetype(ttf_font_path, progress_bar_ttf_size)

# Helper function for number formatting
def format_number(num):
    if num < 1000:
        return str(floor(num))
    elif num < 1000000:
        return f"{num / 1000:.1f}k"
    elif num < 1000000000:
        return f"{num / 1000000:.1f}m"
    else:
        return f"{num / 1000000000:.1f}b"

# Function to calculate primary image color
def determine_primary_color(image):
    image = image.convert('RGB').resize((50, 50))
    pixels = image.getdata()
    color_count = Counter(pixels)
    return color_count.most_common(1)[0][0]

# Function to calculate contrasting color
def calculate_contrasting_color(background_color):
    value = max(background_color) / 255
    return (255, 255, 255) if value < 0.5 else (0, 0, 0)

class Profile(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(
        aliases=['profile', 'p'],
        application_command_meta=ApplicationCommandMeta(
            options=[ApplicationCommandOption(
                name="user",
                description="The user you want to get the profile of.",
                type=ApplicationCommandOptionType.user,
                required=False,
            )],
        ),
    )
    async def profile(self, ctx, user: Member = None):
        if not user:
            user = ctx.author
        file = await self.generate_profile_image(user)
        await ctx.interaction.response.send_message(file=file)

    async def generate_profile_image(self, member: Member):
        # Example user data
        user_data = {
            "level": 19,
            "xp": 2030,
            "xp_required": 3285,
            "messages": 4,
            "vc_hours": 79,
            "coins": 266500,
            "level_rank": 92,
            "coin_rank": 15,
        }

        # Create canvas (base image)
        base_image_size = (375, 281)
        canvas = Image.new('RGBA', base_image_size, color=(23, 23, 33))

        # Background Image
        background = Image.open(f'{resources_directory}/background.jpg').resize(base_image_size)
        canvas.alpha_composite(background)

        draw = ImageDraw.Draw(canvas)

        # Profile Picture
        avatar = await self.get_user_avatar(member)
        profile_picture = Image.open(avatar).convert('RGBA')
        profile_picture = ImageOps.fit(profile_picture, (85, 85), Image.Resampling.LANCZOS)
        profile_picture = ImageOps.circle(profile_picture)  # Circular avatar
        canvas.alpha_composite(profile_picture, (20, 20))

        # Adding text details: Username, Level, Messages, etc.
        text_color = calculate_contrasting_color(determine_primary_color(background))
        draw.text((120, 30), f"{member.name}", font=username_fnt, fill=text_color)
        draw.text((120, 70), f"Level {user_data['level']}", font=fnt, fill=text_color)
        draw.text((120, 100), f"Coins: {format_number(user_data['coins'])}", font=fnt, fill=text_color)

        # XP Bar
        xp_percentage = user_data['xp'] / user_data['xp_required']
        bar_width = 230
        bar_height = 18
        progress_x, progress_y = 120, 140

        # Draw the XP bar background and progress
        draw.rectangle([progress_x, progress_y, progress_x + bar_width, progress_y + bar_height], fill="gray", outline="white")
        draw.rectangle([progress_x, progress_y, progress_x + int(bar_width * xp_percentage), progress_y + bar_height], fill="aqua")

        # Add XP Text
        draw.text((progress_x + bar_width // 2, progress_y - 5), f"{user_data['xp']:,} / {user_data['xp_required']:,} XP", font=progress_bar_fnt, fill="white", anchor="mm")

        # Add other stats
        draw.text((20, 190), f"Level Rank: {user_data['level_rank']}#", font=fnt, fill=text_color)
        draw.text((20, 220), f"Coin Rank: {user_data['coin_rank']}#", font=fnt, fill=text_color)
        draw.text((120, 190), f"{user_data['messages']} Messages", font=fnt, fill=text_color)
        draw.text((120, 220), f"{user_data['vc_hours']} VC Hours", font=fnt, fill=text_color)

        # Save to buffer
        buffer = BytesIO()
        canvas.save(buffer, 'PNG')
        buffer.seek(0)
        return File(buffer, filename="profile.png")

    async def get_user_avatar(self, member: Member) -> BytesIO:
        avatar = member.display_avatar
        return BytesIO(await avatar.read())

def setup(bot):
    bot.add_cog(Profile(bot))
