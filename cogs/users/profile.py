import colorsys
import typing
from collections import Counter
from io import BytesIO
from math import floor

import discord
from PIL import Image, ImageDraw, ImageFont
from discord import Member, ApplicationCommandOption, ApplicationCommandOptionType, File, NotFound
from discord.ext.commands import command, Cog, BucketType, cooldown, ApplicationCommandMeta

import utils

Number = int | float

# base_image_size = (475, 356)
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
        self.speech_balloon = Image.open(f'{resources_directory}/speech-balloon.png').convert('RGBA').resize((27, 27))
        self.microphone = Image.open(f'{resources_directory}/microphone-3.png').convert('RGBA').resize((27, 27))
        self.coin = Image.open(f'{resources_directory}/gold-coin.png').convert('RGBA').resize((27, 27))

    def generate_rounded_bar(self, width, height, fill_color, outline_color, border_radius, progress_percent):
        # Create a new RGBA image for the progress bar
        bar = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Draw a rounded rectangle with the specified border radius
        draw = ImageDraw.Draw(bar)
        rect = [0, 0, width, height]
        draw.rounded_rectangle(rect, radius=border_radius, fill=outline_color)

        # Calculate the progress based on the percentage
        progress_width = int(progress_percent * width)
        draw.rounded_rectangle([0, 0, progress_width, height], radius=border_radius, fill=fill_color)

        return bar

    async def generate_screenshot(self, member: Member):
        # Fetch user data
        levels = utils.Levels.get(member.id)
        currency = utils.Currency.get(member.id)
        tracking = utils.Tracking.get(member.id)

        # Calculate experience percentage and required experience for next level
        if levels.level == 0:
            required_exp = 10
        elif levels.level < 5:
            required_exp = levels.level * 25
        else:
            required_exp = round(levels.level ** 2.75)

        experience_percentage = levels.exp / required_exp

        # Increase size for the level bar and make it rounded
        level_bar_width = base_image_size[0] - 40  # Spanning the bottom of the image
        level_bar_height = 40  # A thicker level bar
        level_bar_radius = 20  # Rounded corners

        # Create a rounded progress bar at the bottom
        progress_bar = self.generate_rounded_bar(
            width=level_bar_width,
            height=level_bar_height,
            fill_color="aqua",
            outline_color="gray",
            border_radius=level_bar_radius,
            progress_percent=experience_percentage
        )

        # User's avatar
        avatar = await self.get_user_avatar(member)

        # Create a new blank canvas for the profile card
        canvas = Image.new('RGBA', base_image_size, color=(255, 255, 255, 0))  # Transparent background

        # Paste the background image
        background = Image.open(f'{resources_directory}/default-background.jpg').convert('RGBA')
        canvas.paste(background, (0, 0))

        # Draw the rounded level bar on the canvas at the bottom
        canvas.alpha_composite(progress_bar, dest=(20, base_image_size[1] - 60))

        # Draw the avatar with a circular mask
        avatar_image = Image.open(avatar).convert('RGBA').resize((100, 100), Image.Resampling.LANCZOS)
        mask = Image.new('L', avatar_image.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + avatar_image.size, fill=255)

        canvas.paste(avatar_image, (22, 22), mask)

        # Adjust text for improved readability
        draw = ImageDraw.Draw(canvas)

        # Determine the primary color for the text contrast
        primary_color = determine_primary_color(background)
        text_color = calculate_contrasting_color(primary_color)

        # Draw the username and title with improved spacing
        username = member.name[:16] + ".." if len(member.name) > 16 else member.name
        draw.text((140, 30), username, font=username_fnt, fill=text_color)
        draw.text((140, 65), member.top_role.name, font=title_fnt, fill=text_color)

        # Level text with larger font for emphasis
        draw.text((30, base_image_size[1] - 100), f'Level {levels.level}', font=fnt, fill=text_color)

        # Add messages, voice hours, and coins data
        draw.text((170, 100), f': {format_number(tracking.messages)} Messages', font=fnt, fill=text_color)
        draw.text((170, 140), f': {format_number(tracking.vc_mins // 60)} VC hours', font=fnt, fill=text_color)
        draw.text((170, 180), f': {format_number(currency.coins)} Coins', font=fnt, fill=text_color)

        # Draw the preloaded icons for messages, voice hours, and coins
        canvas.alpha_composite(self.speech_balloon, dest=(140, 100))
        canvas.alpha_composite(self.microphone, dest=(140, 140))
        canvas.alpha_composite(self.coin, dest=(140, 180))

        # Save the final image to a buffer and return it
        buffer = BytesIO()
        canvas.save(buffer, "png")
        buffer.seek(0)
        canvas.close()

        file = File(buffer, filename='profile.png')
        return file


    # async def base_profile(self, ctx, user, msg):
    #     if msg == None:
    #         msg = await ctx.send(embed=utils.ProfileEmbed(type="Default", user=user))
    #     else:
    #         await msg.edit(embed=utils.ProfileEmbed(type="Default", user=user))

    #     await msg.clear_reactions()
    #     # ! adds the reactions
    #     if ctx.channel.id in self.bot.config['fur-channels'].values():
    #         await msg.add_reaction("✨")
    #     if ctx.channel.id in self.bot.config['nsfw-fur-channels'].values():
    #         await msg.add_reaction("🔞")
    #     # for role in user.roles:
    #     #     if role.id == self.bot.config['roles']['council']:
    #     #         await msg.add_reaction("🍃")

    #     # Watches for the reactions
    #     check = lambda x, y: y.id == ctx.author.id and x.message.id == msg.id and x.emoji in ["✨", "🍃"]
    #     r, _ = await self.bot.wait_for('reaction_add', check=check)
    #     if ctx.channel.id in self.bot.config['fur-channels'].values():
    #         if r.emoji == "✨":
    #             await msg.edit(embed=utils.ProfileEmbed(type="Sfw_Sona", user=user))
    #             pass
    #     if r.emoji == "🍃":
    #         await msg.edit(embed=utils.ProfileEmbed(type="Staff-Track", user=user))
    #         pass
    #     await msg.clear_reactions()
    #     await msg.add_reaction("🔷")
    #     check = lambda x, y: y.id == ctx.author.id and x.message.id == msg.id and x.emoji in ["🔷"]
    #     r, _ = await self.bot.wait_for('reaction_add', check=check)
    #     if r.emoji == "🔷":
    #         await self.base_profile(ctx=ctx, user=user, msg=msg)
    #         return




    @command(application_command_meta=ApplicationCommandMeta(), aliases=['i', 'inv', 'items', 'Inv'])
    async def inventory(self, ctx, user:Member=None):
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

def setup(bot):
    x = Profile(bot)
    bot.add_cog(x)
