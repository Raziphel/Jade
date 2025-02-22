import novus
from novus.ext import commands
import nextwave

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Connect to Lavalink when the cog loads."""
        await self.bot.wait_until_ready()
        await nextwave.NodePool.create_node(
            bot=self.bot,
            host="localhost",  # Change if your Lavalink server is remote
            port=2333,  # Default Lavalink port
            password="youshallnotpass",  # Change this to match your Lavalink config
            secure=False  # Set to True if using SSL
        )

    @commands.command(name="join")
    async def join(self, ctx: commands.Context):
        """Make the bot join a voice channel."""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel first! >w<")

        channel = ctx.author.voice.channel
        if ctx.voice_client:
            return await ctx.send("I'm already connected! :o")

        vc = await channel.connect(cls=nextwave.Player)
        return await ctx.send(f"Joined **{channel.name}**! 🎶")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):
        """Search and play a song from YouTube."""
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        vc: nextwave.Player = ctx.voice_client
        tracks = await nextwave.YouTubeTrack.search(query)

        if not tracks:
            return await ctx.send("No results found! ;w;")

        await vc.play(tracks[0])
        await ctx.send(f"Now playing: **{tracks[0].title}** 🎵")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        """Pause the music."""
        vc: nextwave.Player = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send("Nothing is playing right now! ;w;")

        await vc.pause()
        await ctx.send("Paused the music! ⏸️")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        """Resume the music."""
        vc: nextwave.Player = ctx.voice_client

        if not vc or not vc.is_paused():
            return await ctx.send("The music isn't paused! >w<")

        await vc.resume()
        await ctx.send("Resumed the music! ▶️")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        """Stop the music and disconnect."""
        vc: nextwave.Player = ctx.voice_client

        if not vc:
            return await ctx.send("I'm not even in a voice channel! :o")

        await vc.disconnect()
        await ctx.send("Disconnected from voice! Bye-bye! ✨")

async def setup(bot):
    await bot.add_cog(Music(bot))
