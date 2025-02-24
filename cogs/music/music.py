import discord
from discord.ext import commands
import wavelink


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        """Connect to Lavalink server"""
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host="127.0.0.1",  # Change this if hosting Lavalink elsewhere
            port=7779,
            password="youshallnotpass",
            region="us_central"
        )
        print("🎶 Connected to Lavalink!")

    @commands.command()
    async def join(self, ctx):
        """Join the user's voice channel"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel! 🎤")

        channel = ctx.author.voice.channel
        player = await wavelink.NodePool.get_node().get_player(ctx.guild)

        if not player.is_connected:
            await player.connect(channel.id)
            await ctx.send(f"🎶 Joined **{channel.name}**!")

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Search and play a song"""
        player = await wavelink.NodePool.get_node().get_player(ctx.guild)

        if not player.is_connected:
            return await ctx.send("I'm not connected to a voice channel! ❌")

        tracks = await wavelink.YouTubeTrack.search(query)
        if not tracks:
            return await ctx.send("No results found! 😿")

        track = tracks[0]
        await player.play(track)
        await ctx.send(f"🎵 Now playing: **{track.title}**")

    @commands.command()
    async def pause(self, ctx):
        """Pause the current song"""
        player = await wavelink.NodePool.get_node().get_player(ctx.guild)
        if player.is_playing:
            await player.pause()
            await ctx.send("⏸️ Paused the song!")

    @commands.command()
    async def resume(self, ctx):
        """Resume the paused song"""
        player = await wavelink.NodePool.get_node().get_player(ctx.guild)
        if player.is_paused:
            await player.resume()
            await ctx.send("▶️ Resumed the song!")

    @commands.command()
    async def skip(self, ctx):
        """Skip the current song"""
        player = await wavelink.NodePool.get_node().get_player(ctx.guild)
        if player.is_playing:
            await player.stop()
            await ctx.send("⏭️ Skipped the song!")

    @commands.command()
    async def stop(self, ctx):
        """Stop playback and disconnect"""
        player = await wavelink.NodePool.get_node().get_player(ctx.guild)
        if player.is_connected:
            await player.disconnect()
            await ctx.send("🎵 Stopped music and left the channel!")


async def setup(bot):
    await bot.add_cog(Music(bot))
