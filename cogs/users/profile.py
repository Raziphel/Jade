import colorsys
import typing
from collections import Counter
from io import BytesIO
from math import floor

import discord
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from discord import Member, File, NotFound
from discord.ext.commands import command, Cog

import utils

Number = int | float

# Basic settings for the profile card
base_image_size = (375, 281)
resources_directory = "resources"

# Coordinates and dimensions for the progress bar
level_details_x = 100
parent_progress_bar_h_w = (113, 25)
parent_progress_bar_x_y = (17, 161)
inner_progress_bar_padding = 2.5  # px

# Gradient colors for XP bar
progress_bar_start_color = (0, 255, 255)  # Start color (aqua)
progress_bar_end_color = (0, 128, 255)  # End color (blue)

# Font settings
ttf_font_path = f'{resources_directory}/SourceSansPro-Regular.ttf'
ttf_bold_font_path = f'{resources_directory}/SourceSansPro-SemiBold.ttf'
ttf_italic_font_path = f'{resources_directory}/SourceSansPro-Italic.ttf'

default_ttf_size = 19
username_ttf_size = 24
title_ttf_size = 20
progress_bar_ttf_size = 13

fnt = ImageFont.truetype(ttf_font_path, default_ttf_size)
username_fnt = ImageFont.truetype(ttf_bold_font_path, username_ttf_size)
title_fnt = ImageFont.truetype(ttf_italic_font_path, title_ttf_size)
progress_bar_fnt = ImageFont.truetype(ttf_font_path, progress_bar_ttf_size)

def determine_primary_color(image):
    image = image.convert('RGB')
    image = image.resize((50, 50))
    pixels = image.getdata()
    color_count = Counter(pixels)
    primary_color = color_count.most_common(1)[0][0]
    return primary_color

def calculate_contrasting_color(background_color):
    value = max(background_color) / 255
    if value < 0.5:
        return (255, 255, 255)  # white
    else:
        return (0, 0, 0)  # black

def calculate_xy_size(
        x: Number,
        y: Number,
        height: Number,
        width: Number
) -> typing.Tuple[Number, Number, Number, Number]:
    return (
        x,
        y,
        x + height,
        y + width
    )

def format_number(num):
    if num < 1000:
        return str(floor(num))
    elif num < 1000000:
        return f"{num / 1000:.1f}k"
    elif num < 1000000000:
        return f"{num / 1000000:.1f}m"
    else:
        return f"{num / 1000000000:.1f}b"

def gradient_horizontal(draw: ImageDraw.Draw, xy: tuple, start_color: tuple, end_color: tuple):
    left, top, right, bottom = xy
    width = right - left

    for i in range(width):
        r = start_color[0] + (end_color[0] - start_color[0]) * i // width
        g = start_color[1] + (end_color[1] - start_color[1]) * i // width
        b = start_color[2] + (end_color[2] - start_color[2]) * i // width
        draw.line([(left + i, top), (left + i, bottom)], fill=(r, g, b))

class Profile(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(
        aliases=['p', 'Profile']
    )
    async def profile(self, ctx, user: Member = None):
        '''Shows a user's profile'''
        if not user:
            user = ctx.author

        file = await self.generate_screenshot(user)
        await ctx.send(file=file)

    async def get_user_avatar(self, member: Member) -> BytesIO:
        avatar = member.display_avatar
        try:
            data = await avatar.read()
        except NotFound:
            user = await self.bot.fetch_user(member.id)
            avatar = user.display_avatar
            data = await avatar.read()

        return BytesIO(data)

    def get_level_rank(self, member: discord.Member) -> int:
        sorted_levels = utils.Levels.sort_levels()
        member_level = utils.Levels.get(member.id)
        try:
            level_rank = sorted_levels.index(member_level)
            return level_rank + 1
        except ValueError:
            return -1

    def get_wealth_rank(self, member: discord.Member) -> int:
        sorted_wealth = utils.Currency.sort_coins()
        member_wealth = utils.Currency.get(member.id)
        try:
            wealth_rank = sorted_wealth.index(member_wealth)
            return wealth_rank + 1
        except ValueError:
            return -1

    async def generate_screenshot(self, member: Member):
        levels = utils.Levels.get(member.id)
        currency = utils.Currency.get(member.id)
        tracking = utils.Tracking.get(member.id)

        if levels.level == 0:
            required_exp = 10
        elif levels.level < 5:
            required_exp = levels.level * 25
        else:
            required_exp = round(levels.level ** 2.75)

        avatar = await self.get_user_avatar(member)
        username = str(member.name)
        title = str(member.top_role)
        current_level = levels.level
        current_experience = floor(levels.exp)
        networth = format_number(currency.coins)
        messages = format_number(tracking.messages)

        voice_activity = floor(tracking.vc_mins / 60)
        voice_activity = format_number(voice_activity)

        level_rank = self.get_level_rank(member)
        wealth_rank = self.get_wealth_rank(member)

        experience_percentage = current_experience / required_exp
        relative_inner_progress_bar_width = experience_percentage * parent_progress_bar_h_w[0]

        progress_bar = Image.new(
            mode='RGBA',
            size=parent_progress_bar_h_w,
            color=(255, 255, 255, 0)
        )

        progress_bar_draw = ImageDraw.Draw(progress_bar)

        # Cool gradient for inner progress bar
        inner_progress_bar_size = calculate_xy_size(
            inner_progress_bar_padding,
            inner_progress_bar_padding,
            relative_inner_progress_bar_width,
            parent_progress_bar_h_w[1] - inner_progress_bar_padding * 2
        )

        gradient_horizontal(progress_bar_draw, inner_progress_bar_size, progress_bar_start_color, progress_bar_end_color)

        # Center alignment for progress bar text
        progress_bar_text_x_y = (
            progress_bar.size[0] / 2,
            progress_bar.size[1] / 2
        )

        progress_bar_draw.text(
            progress_bar_text_x_y,
            f'XP: {current_experience:,} / {required_exp:,}',
            font=progress_bar_fnt,
            fill="black",
            anchor="mm",
            align="center"
        )

        progress_bar.putalpha(225)

        canvas = Image.new('RGBA', base_image_size, color=128)
        background = Image.open(f'{resources_directory}/default-background.jpg')
        canvas.paste(background)

        primary_color = determine_primary_color(background)
        text_color = calculate_contrasting_color(primary_color)

        draw = ImageDraw.Draw(canvas)

        # Draw the main border with shadow
        draw.rectangle(
            xy=calculate_xy_size(
                4, 4,
                canvas.size[0] - 8,
                canvas.size[1] - 8
            ),
            outline=text_color,
            width=3
        )

        # User's profile picture
        profile_picture = Image.open(avatar).convert('RGBA')
        profile_picture = profile_picture.resize((103, 103), Image.Resampling.LANCZOS)
        canvas.paste(profile_picture, (22, 22))

        draw.text(
            xy=(38 if current_level > 10 else 40, 132),
            text=f'Level {current_level}',
            fill=text_color,
            font=fnt
        )

        if len(username) > 16:
            username = username[:16] + '..'

        draw.text(
            xy=(140, 20),
            text=username,
            fill=text_color,
            font=username_fnt
        )

        draw.text(
            xy=(140, 50),
            text=title,
            fill=text_color,
            font=title_fnt
        )

        draw.text(
            xy=(17, 190),
            text=f'Level rank:  {level_rank}#',
            fill=text_color,
            font=fnt
        )

        draw.text(
            xy=(17, 215),
            text=f'Coin rank:   {wealth_rank}#',
            fill=text_color,
            font=fnt
        )

        draw.text(
            xy=(17, 240),
            text=f'Messages:    {messages}',
            fill=text_color,
            font=fnt
        )

        draw.text(
            xy=(17, 265),
            text=f'Voice:       {voice_activity}hrs',
            fill=text_color,
            font=fnt
        )

        # Paste the XP bar into the final canvas
        canvas.paste(progress_bar, parent_progress_bar_x_y, progress_bar)

        buffer = BytesIO()
        canvas.save(buffer, "png")
        buffer.seek(0)
        return File(buffer, filename='profile.png')


def setup(bot):
    x = Profile(bot)
    bot.add_cog(x)