# Discord
from discord import Embed
from discord.ext.commands import command, Cog
from random import choice

import utils

class Embed(Embed):
    bot = None

    def __init__(self, *args, **kwargs):
        #? Gets the variables for the embed
        user = kwargs.pop('user', None)
        color = kwargs.pop('color', None)
        title = kwargs.pop('author', None)
        thumbnail = kwargs.pop('thumbnail', None)
        image = kwargs.pop('image', None)
        desc = kwargs.pop('desc', None)
        footer = kwargs.pop('footer', None)
        mail = kwargs.pop('mail', False)

        #+ Make the Embed
        super().__init__(*args, **kwargs)

        #* Add Color
        if user:
            t = utils.Tracking.get(user.id)
            if t.color == 0 or t.color is None:
                t.color = 0xff69b4

            self.color = t.color
        elif color:
            self.color = color

        #* Add Author
        if title:
            self.set_author(name=title)

        #* Check if mail
        if mail:
            self.set_author(name=author.display_name, icon_url=author.avatar_url)

        #* Add Thumbnail
        if thumbnail:
            self.set_thumbnail(url=thumbnail)

        #* Add Image
        if image:
            self.set_image(url=image)

        #* Add Description
        if desc:
            self.description = f"{desc}"

        #* Add Footer
        if footer:
            self.set_footer(text=footer)