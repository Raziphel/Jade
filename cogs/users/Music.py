from discord.ext.commands import command, Cog, cooldown, BucketType, ApplicationCommandMeta
import novus_lavalink
import asyncio


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lavalink = None

    async def on_ready(self):
        self.lavalink = await novus_lavalink.LavalinkClient.create(
            bot=self.bot,
            host="127.0.0.1",  # Change if your Lavalink is hosted elsewhere
            port=7779,
            password="youshallnotpass",
            identifier="MainNode",
            secure=False
        )
        print("🎵 Lavalink connected!")

    @command()
    async def join(self, ctx):
        """Make the bot join the voice channel."""
        if not ctx.author.voice:
            return await ctx.send("You need to be in a voice channel! 🎤")

        channel = ctx.author.voice.channel
        await self.lavalink.connect(ctx.guild.id, channel.id)
        await ctx.send(f"🎶 Joined {channel.name}!")

    @command()
    async def play(self, ctx, *, query: str):
        """Search and play a song from YouTube."""
        if not self.lavalink.get_player(ctx.guild.id):
            return await ctx.send("I'm not connected to a voice channel! ❌")

        search = await self.lavalink.get_tracks(f"ytsearch:{query}")
        if not search.tracks:
            return await ctx.send("No results found! 🔍")

        track = search.tracks[0]
        await self.lavalink.play(ctx.guild.id, track)

        await ctx.send(f"🎶 Now playing: **{track.title}**")

    @command()
    async def stop(self, ctx):
        """Stop the music and disconnect."""
        player = self.lavalink.get_player(ctx.guild.id)
        if not player:
            return await ctx.send("I'm not playing anything! 😿")

        await self.lavalink.stop(ctx.guild.id)
        await self.lavalink.disconnect(ctx.guild.id)
        await ctx.send("🎵 Stopped music and left the channel!")

    @command()
    async def pause(self, ctx):
        """Pause the current song."""
        player = self.lavalink.get_player(ctx.guild.id)
        if not player or not player.is_playing:
            return await ctx.send("Nothing is playing right now! ⏸️")

        await player.pause()
        await ctx.send("⏸️ Paused the song!")

    @command()
    async def resume(self, ctx):
        """Resume the paused song."""
        player = self.lavalink.get_player(ctx.guild.id)
        if not player or not player.is_paused:
            return await ctx.send("There's nothing to resume! ▶️")

        await player.resume()
        await ctx.send("▶️ Resumed the song!")

    @command()
    async def skip(self, ctx):
        """Skip the current song."""
        player = self.lavalink.get_player(ctx.guild.id)
        if not player or not player.is_playing:
            return await ctx.send("Nothing to skip! 🎵")

        await self.lavalink.skip(ctx.guild.id)
        await ctx.send("⏭️ Skipped the song!")


async def setup(bot):
    await bot.add_cog(Music(bot))
