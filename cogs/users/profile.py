import colorsys
import typing
from collections import Counter
from io import BytesIO
from math import floor

import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps
from discord import Member, ApplicationCommandOption, ApplicationCommandOptionType, File, NotFound
from discord.ext.commands import command, Cog, BucketType, cooldown, ApplicationCommandMeta

import utils

Number = int | float

# base_image_size = (500, 300)  # New size for the improved image
base_image_size = (375, 281)

resources_directory = "resources"

level_details_x = 100
parent_progress_bar_h_w = (113, 25)
parent_progress_bar_x_y = (17, 161)
inner_progress_bar_padding = 2.5  # px
progress_bar_color = "aqua"

# Font settings #

ttf_font_path = f'{resources_directory}/SourceSansPro-Regular.ttf'
ttf_bold_font_path = f'{resources_directory}/SourceSansPro-SemiBold.ttf'
ttf_italic_font_path = f'{resources_directory}/SourceSansPro-Italic.ttf'

# The default size for all text that's not the username, title (i.e. their highest Discord role), or the progress bar.
default_ttf_size = 19

username_ttf_size = 24
title_ttf_size = 20
progress_bar_ttf_size = 13

fnt = ImageFont.truetype(ttf_font_path, default_ttf_size)
username_fnt = ImageFont.truetype(ttf_bold_font_path, username_ttf_size)
title_fnt = ImageFont.truetype(ttf_italic_font_path, title_ttf_size)
progress_bar_fnt = ImageFont.truetype(ttf_font_path, progress_bar_ttf_size)


def determine_primary_color(image):
    # Load the image and convert it to the RGB color space
    image = image.convert('RGB')

    # Resize the image to a smaller size
    image = image.resize((50, 50))

    # Get the pixel data of the image
    pixels = image.getdata()

    # Count the number of occurrences of each color using a Counter object
    color_count = Counter(pixels)

    # Find the color with the highest count
    primary_color = color_count.most_common(1)[0][0]

    return primary_color


def calculate_contrasting_color(background_color):
    # Convert the background color to the HSV color space
    h, s, v = colorsys.rgb_to_hsv(*background_color)

    # Calculate the value of the background color
    value = max(background_color) / 255

    # Choose a text color based on the value of the background color
    if value < 0.5:
        text_color = (255, 255, 255)  # white
    else:
        text_color = (0, 0, 0)  # black

    return text_color


def calculate_xy_size(
        x: Number,
        y: Number,
        height: Number,
        width: Number
) -> typing.Tuple[Number, Number, Number, Number]:
    """A helper function for simply calculating an image's size."""
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


class Profile(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(
        aliases=['p', 'P', 'Profile'],
        application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="user",
                    description="The user you want to get the profile of.",
                    type=ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    async def profile(self, ctx, user: Member = None):
        """Shows a user's profile"""
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
        voice_activity = format_number(floor(tracking.vc_mins / 60))
        level_rank = self.get_level_rank(member)
        wealth_rank = self.get_wealth_rank(member)
        experience_percentage = current_experience / required_exp

        # Create a new base image (RGBA mode) with a gradient background
        canvas = Image.new('RGBA', base_image_size, color=(128, 128, 128, 255))
        background = Image.new('RGBA', base_image_size, color=(30, 30, 30, 255))
        gradient = ImageDraw.Draw(background)

        for y in range(base_image_size[1]):
            r = int(30 + (70 * (y / base_image_size[1])))
            gradient.line([(0, y), (base_image_size[0], y)], fill=(r, r, r, 255))

        canvas = Image.alpha_composite(canvas, background)

        draw = ImageDraw.Draw(canvas)

        # Avatar handling
        avatar_size = 120
        avatar_image = Image.open(avatar).convert('RGBA')
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        avatar_image = ImageOps.fit(avatar_image, (avatar_size, avatar_size), method=Image.Resampling.LANCZOS)
        avatar_image.putalpha(mask)
        canvas.paste(avatar_image, (35, 35), avatar_image)

        # Draw username and title
        draw.text((180, 40), username, font=username_fnt, fill="white")
        draw.text((180, 80), title, font=title_fnt, fill="lightgray")

        # Draw stats
        stats_font = ImageFont.truetype(ttf_font_path, 18)
        draw.text((180, 120), f'Level: {current_level}', font=stats_font, fill="aqua")
        draw.text((180, 150), f'Level Rank: #{level_rank}', font=stats_font, fill="white")
        draw.text((180, 180), f'Coin Rank: #{wealth_rank}', font=stats_font, fill="white")
        draw.text((180, 210), f'Messages: {messages}', font=stats_font, fill="white")
        draw.text((180, 240), f'VC Hours: {voice_activity}', font=stats_font, fill="white")
        draw.text((180, 270), f'Net Worth: {networth} Coins', font=stats_font, fill="gold")

        # Improved progress bar
        progress_bar_width = 200
        progress_bar_height = 30
        progress_bar_x = 35
        progress_bar_y = 180

        draw.rounded_rectangle(
            [(progress_bar_x, progress_bar_y), (progress_bar_x + progress_bar_width, progress_bar_y + progress_bar_height)],
            radius=10, fill=(50, 50, 50, 255), outline="white", width=2
        )

        draw.rounded_rectangle(
            [(progress_bar_x, progress_bar_y), (progress_bar_x + int(experience_percentage * progress_bar_width), progress_bar_y + progress_bar_height)],
            radius=10, fill="aqua"
        )

        # Progress bar text
        progress_text = f"XP: {current_experience:,} / {required_exp:,}"
        progress_text_bbox = draw.textbbox((0, 0), progress_text, font=stats_font)
        progress_text_width = progress_text_bbox[2] - progress_text_bbox[0]
        progress_text_height = progress_text_bbox[3] - progress_text_bbox[1]
        progress_text_x = progress_bar_x + (progress_bar_width - progress_text_width) // 2
        progress_text_y = progress_bar_y + (progress_bar_height - progress_text_height) // 2

        # Save the improved profile image to a buffer
        buffer = BytesIO()
        canvas.save(buffer, format="PNG")
        buffer.seek(0)

        file = File(buffer, filename='profile.png')
        return file


    @command(application_command_meta=ApplicationCommandMeta(), aliases=['i', 'inv', 'items', 'Inv'])
    async def inventory(self, ctx, user: Member = None):
        """Quick Check inventory"""
        if not user:
            user = ctx.author
        await ctx.interaction.response.send_message(embed=utils.Embed(type="Items", user=user, quick=True))


    @cooldown(1, 5, BucketType.user)
    @command(aliases=['color', 'Color', 'Setcolor', 'SetColor'],
            application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="colour",
                    description="the color you are wanting...",
                    type=ApplicationCommandOptionType.string,
                    required=False
                    )
                ],
            ),
        )
    async def setcolor(self, ctx, colour=None):
        """Sets your user color"""

        if colour is None:
            file = discord.File('config/lists/colors.py', filename='config/lists/colors.py')
            await ctx.interaction.response.send_message(f"**Here's a list of colors you can use!**", file=file)
            return

        colour_value = utils.Colors.get(colour.lower())
        tr = utils.Tracking.get(ctx.author.id)

        if colour_value is None:
            try:
                colour_value = int(colour.strip('#'), 16)
            except ValueError:
                await ctx.interaction.response.send_message(embed=utils.Embed(title="Incorrect colour usage!"))
                return

        tr.color = colour_value
        async with self.bot.database() as db:
            await tr.save(db)

        await ctx.interaction.response.send_message(embed=utils.Embed(title="Your color setting has been set!", user=ctx.author))


    @cooldown(1, 5, BucketType.user)
    @command(application_command_meta=ApplicationCommandMeta(), aliases=["coin_record", "cr"])
    async def coinrecord(self, ctx, user=None):
        """Displays a user's coin record in a stylish embed."""

        user = user or ctx.author
        coins_record = utils.Coins_Record.get(user.id)

        if coins_record is None:
            return await ctx.send(embed=utils.Embed(description="No coins record found for this user.", color=0xff0000))

        embed = utils.Embed(
            title=f"{user.display_name}'s Coins Record",
            description=f"Here is a detailed overview of {user.mention}'s coin activity!",
            color=0xFFD700,
        )

        embed.set_thumbnail(url=user.avatar.url)

        embed.add_field(name="💰 Earned Coins", value=f"{coins_record.earned:,} coins", inline=False)
        embed.add_field(name="🛍️ Spent Coins", value=f"{coins_record.spent:,} coins", inline=False)
        embed.add_field(name="💸 Taxed Coins", value=f"{coins_record.taxed:,} coins", inline=False)
        embed.add_field(name="💀 Lost Coins", value=f"{coins_record.lost:,} coins", inline=False)
        embed.add_field(name="🧤 Stolen Coins", value=f"{coins_record.stolen:,} coins", inline=False)
        embed.add_field(name="🎁 Gifted Coins", value=f"{coins_record.gifted:,} coins", inline=False)
        embed.add_field(name="🎉 Given Coins", value=f"{coins_record.given:,} coins", inline=False)
        embed.add_field(name="🏆 Won Coins", value=f"{coins_record.won:,} coins", inline=False)

        embed.set_footer(text="Serpent's Garden Economy", icon_url=self.bot.user.avatar.url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Profile(bot))
