import discord
from discord.ext.commands import command, Cog, ApplicationCommandMeta
import wavelink

class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.node = None

    async def cog_load(self):
        """Connect to Lavalink when the cog is loaded."""
        self.node = await wavelink.NodePool.create_node(
            bot=self.bot,
            host="localhost",  # Change if your Lavalink server is remote
            port=7779,  # Default Lavalink port
            password="youshallnotpass",  # Change this if your server has a different password
            secure=False  # Set to True if using SSL
        )

    @command(name="join")
    async def join(self, ctx):
        """Join the voice channel."""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel first! >w<")

        channel = ctx.author.voice.channel
        player = await channel.connect(cls=wavelink.Player)
        return await ctx.send(f"Joined {channel.name}! :3")

    @command(name="play")
    async def play(self, ctx, *, query: str):
        """Play a song from YouTube."""
        if not ctx.voice_client:
            return await ctx.invoke(self.join)

        vc: wavelink.Player = ctx.voice_client
        tracks = await wavelink.YouTubeTrack.search(query)

        if not tracks:
            return await ctx.send("No results found! ;w;")

        await vc.play(tracks[0])
        await ctx.send(f"Now playing: **{tracks[0].title}** 🎶")

    @command(name="pause")
    async def pause(self, ctx):
        """Pause the music."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("Nothing is playing right now! ;w;")

        await ctx.voice_client.pause()
        await ctx.send("Paused the music! ⏸️")

    @command(name="resume")
    async def resume(self, ctx):
        """Resume the music."""
        if not ctx.voice_client or not ctx.voice_client.is_paused():
            return await ctx.send("The music isn't paused! >w<")

        await ctx.voice_client.resume()
        await ctx.send("Resumed the music! ▶️")

    @command(name="stop")
    async def stop(self, ctx):
        """Stop the music and disconnect."""
        if not ctx.voice_client:
            return await ctx.send("I'm not even in a voice channel! :o")

        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from voice! Bye-bye! ✨")

async def setup(bot):
    await bot.add_cog(Music(bot))
