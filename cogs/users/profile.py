from collections import Counter
from io import BytesIO
from math import floor

import discord
from PIL import Image, ImageDraw, ImageFont
from discord import Member, ApplicationCommandOption, ApplicationCommandOptionType, File
from discord.ext.commands import command, Cog, BucketType, cooldown, ApplicationCommandMeta

import utils

Number = int | float
base_image_size = (375, 281)
resources_directory = "resources"
progress_bar_color = "aqua"
level_bar_height = 40  # Taller level bar
progress_bar_radius = 20  # Rounded corners

# Font settings #
ttf_font_path = f'{resources_directory}/SourceSansPro-Regular.ttf'
ttf_bold_font_path = f'{resources_directory}/SourceSansPro-SemiBold.ttf'
ttf_italic_font_path = f'{resources_directory}/SourceSansPro-Italic.ttf'
default_ttf_size = 19
username_ttf_size = 24
title_ttf_size = 20
progress_bar_ttf_size = 13

# Loading fonts
fnt = ImageFont.truetype(ttf_font_path, default_ttf_size)
username_fnt = ImageFont.truetype(ttf_bold_font_path, username_ttf_size)
title_fnt = ImageFont.truetype(ttf_italic_font_path, title_ttf_size)
progress_bar_fnt = ImageFont.truetype(ttf_font_path, progress_bar_ttf_size)


# Helper functions
def determine_primary_color(image):
    image = image.convert('RGB')
    image = image.resize((50, 50))
    pixels = image.getdata()
    color_count = Counter(pixels)
    primary_color = color_count.most_common(1)[0][0]
    return primary_color


def calculate_contrasting_color(background_color):
    value = max(background_color) / 255
    return (255, 255, 255) if value < 0.5 else (0, 0, 0)


def format_number(num):
    if num < 1000:
        return str(floor(num))
    elif num < 1000000:
        return f"{num / 1000:.1f}k"
    elif num < 1000000000:
        return f"{num / 1000000:.1f}m"
    else:
        return f"{num / 1000000000:.1f}b"


def create_rounded_bar(width, height, percentage, fill_color, bg_color, radius):
    bar = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(bar)

    # Draw the rounded background bar
    draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=bg_color)

    # Draw the filled portion representing progress
    filled_width = int(percentage * width)
    draw.rounded_rectangle([0, 0, filled_width, height], radius=radius, fill=fill_color)

    return bar


class Profile(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(aliases=['Profile'])
    async def profile(self, ctx, user: Member = None):
        if not user:
            user = ctx.author
        file = await self.generate_screenshot(user)
        await ctx.send(file=file)

    async def generate_screenshot(self, member: Member):
        levels = utils.Levels.get(member.id)
        currency = utils.Currency.get(member.id)
        tracking = utils.Tracking.get(member.id)

        required_exp = round(
            levels.level ** 2.75) if levels.level >= 5 else levels.level * 25 if levels.level > 0 else 10
        experience_percentage = levels.exp / required_exp

        # Create base image
        canvas = Image.new('RGBA', base_image_size, (255, 255, 255, 0))
        background = Image.open(f'{resources_directory}/default-background.jpg').convert('RGBA')
        canvas.paste(background, (0, 0))

        # Circular avatar
        avatar = await self.get_user_avatar(member)
        avatar_image = Image.open(avatar).convert('RGBA').resize((100, 100), Image.Resampling.LANCZOS)
        mask = Image.new('L', avatar_image.size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0) + avatar_image.size, fill=255)
        canvas.paste(avatar_image, (22, 22), mask)

        draw = ImageDraw.Draw(canvas)
        primary_color = determine_primary_color(background)
        text_color = calculate_contrasting_color(primary_color)

        # Draw username and title
        username = member.name[:16] + '..' if len(member.name) > 16 else member.name
        draw.text((140, 30), username, font=username_fnt, fill=text_color)
        draw.text((140, 65), str(member.top_role), font=title_fnt, fill=text_color)

        # Draw user stats
        messages = format_number(tracking.messages)
        voice_activity = format_number(tracking.vc_mins // 60)
        networth = format_number(currency.coins)
        draw.text((170, 100), f': {messages} Messages', font=fnt, fill=text_color)
        draw.text((170, 140), f': {voice_activity} VC hours', font=fnt, fill=text_color)
        draw.text((170, 180), f': {networth} Coins', font=fnt, fill=text_color)

        # Progress bar (spanning the bottom)
        progress_bar = create_rounded_bar(
            width=base_image_size[0] - 40,
            height=level_bar_height,
            percentage=experience_percentage,
            fill_color=progress_bar_color,
            bg_color="grey",
            radius=progress_bar_radius
        )
        canvas.alpha_composite(progress_bar, dest=(20, base_image_size[1] - 50))

        # Level and rank text
        draw.text((30, base_image_size[1] - 100), f'Level {levels.level}', font=fnt, fill=text_color)
        level_rank = self.get_level_rank(member)
        wealth_rank = self.get_wealth_rank(member)
        draw.text((17, 190), f'Level rank:  {level_rank}#', font=fnt, fill=text_color)
        draw.text((17, 215), f'Coin rank:   {wealth_rank}#', font=fnt, fill=text_color)

        # Save to buffer and return as file
        buffer = BytesIO()
        canvas.save(buffer, "png")
        buffer.seek(0)
        return File(buffer, filename='profile.png')

    async def get_user_avatar(self, member: Member) -> BytesIO:
        avatar = member.display_avatar
        try:
            data = await avatar.read()
        except discord.NotFound:
            user = await self.bot.fetch_user(member.id)
            avatar = user.display_avatar
            data = await avatar.read()
        return BytesIO(data)

    def get_level_rank(self, member: discord.Member) -> int:
        sorted_levels = utils.Levels.sort_levels()
        member_level = utils.Levels.get(member.id)
        try:
            return sorted_levels.index(member_level) + 1
        except ValueError:
            return -1

    def get_wealth_rank(self, member: discord.Member) -> int:
        sorted_wealth = utils.Currency.sort_coins()
        member_wealth = utils.Currency.get(member.id)
        try:
            return sorted_wealth.index(member_wealth) + 1
        except ValueError:
            return -1

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
