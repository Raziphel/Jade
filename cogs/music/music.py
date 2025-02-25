import discord
from discord.ext.commands import Cog, command
import aiohttp
import asyncio
import uuid  # Used to generate session IDs


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.node = {
            "host": "172.18.0.1",
            "port": 8197,
            "password": "youshallnotpass",
        }
        self.players = {}
        self.queues = {}
        self.session_id = str(uuid.uuid4())  # Generate a session ID

        self.bot.loop.create_task(self.initialize())

    async def initialize(self):
        """Ensures session is created and Lavalink is ready."""
        await self.bot.wait_until_ready()
        if self.session is None:
            self.session = aiohttp.ClientSession()
        await self.create_lavalink_session()

    async def create_lavalink_session(self):
        """Creates a Lavalink session."""
        url = f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{self.session_id}"
        async with self.session.post(
            url,
            headers={"Authorization": self.node["password"], "Content-Type": "application/json"},
            json={"resuming": False, "timeout": 60}
        ) as response:
            if response.status not in [200, 204]:
                print(f"❌ Failed to create Lavalink session: {await response.text()}")
            else:
                print(f"✅ Created Lavalink session: {self.session_id}")

    async def send_lavalink(self, guild_id, data: dict, method="PUT"):
        """Sends a request to Lavalink using the correct session-based endpoint."""
        url = f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self.session.request(
            method, url,
            headers={"Authorization": self.node["password"], "Content-Type": "application/json"},
            json=data
        ) as response:
            if response.status not in [200, 204]:
                print(f"❌ Lavalink REST Error: {await response.text()}")

    async def search_track(self, query: str):
        """Searches for a track using Lavalink."""
        async with self.session.get(
            f"http://{self.node['host']}:{self.node['port']}/v4/loadtracks",
            params={"identifier": f"ytsearch:{query}"},
            headers={"Authorization": self.node["password"]}
        ) as response:
            try:
                data = await response.json()
            except Exception as e:
                print(f"❌ Error parsing Lavalink response: {e}")
                return None

            if "data" not in data or not isinstance(data["data"], list):
                print(f"❌ Unexpected Lavalink response: {data}")
                return None

            return data["data"][0] if data["data"] else None

    async def join_voice(self, ctx):
        """Joins a voice channel and sends voice update to Lavalink."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return None

        channel = ctx.author.voice.channel
        if ctx.guild.voice_client:
            return ctx.guild.voice_client.channel

        await ctx.guild.change_voice_state(channel=channel)  # Works with Novus

        self.players[ctx.guild.id] = {"channel": channel.id}

        # Send voice update event to Lavalink (important for v4)
        await self.send_lavalink(ctx.guild.id, {
            "guildId": str(ctx.guild.id),
            "channelId": str(channel.id),
            "selfDeaf": True
        }, method="PATCH")  # v4 requires PATCH for voice updates

        await asyncio.sleep(1)
        await ctx.send(f"🎶 Joined **{channel.name}**!")
        return channel

    @command()
    async def play(self, ctx, *, query: str):
        """Plays a song and joins VC if needed."""
        channel = await self.join_voice(ctx)
        if not channel:
            return

        track = await self.search_track(query)
        if not track:
            return await ctx.send("❌ No results found!")

        track_id = track.get("encoded")
        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        # Send `PUT` request to create a player before playing (Lavalink v4 fix)
        await self.send_lavalink(ctx.guild.id, {
            "track": track_id,
            "guildId": str(ctx.guild.id),
            "paused": False
        }, method="PUT")

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("❌ No more songs in the queue!")

        track_data = self.queues[ctx.guild.id].pop(0)
        track_id = track_data.get("encoded")

        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        await self.send_lavalink(ctx.guild.id, {
            "track": track_id,
            "guildId": str(ctx.guild.id),
            "paused": False
        }, method="PUT")

        track_info = track_data["info"]
        await ctx.send(f"🎵 Now playing: **{track_info['title']}** - {track_info['uri']}")

    @command()
    async def queue(self, ctx):
        """Displays the current queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("📭 The queue is empty!")

        queue_list = "\n".join(
            [f"{i+1}. {track['info']['title']}" for i, track in enumerate(self.queues[ctx.guild.id])]
        )

        embed = discord.Embed(title="🎶 Music Queue", description=queue_list, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @command()
    async def stop(self, ctx):
        """Stops the music and clears the queue."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        self.queues[ctx.guild.id] = []

        await self.send_lavalink(ctx.guild.id, {
            "paused": True
        }, method="PUT")

        await ctx.send("🎵 Stopped the music and cleared the queue!")

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            del self.players[ctx.guild.id]

    @command()
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_lavalink(ctx.guild.id, {
            "paused": True
        }, method="PUT")

        await ctx.send("⏩ Skipped the song!")
        await self.play_next(ctx)

    @command()
    async def leave(self, ctx):
        """Leaves the voice channel."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not in a voice channel!")

        await self.send_lavalink(ctx.guild.id, {
            "paused": True
        }, method="PUT")

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()

        del self.players[ctx.guild.id]
        del self.queues[ctx.guild.id]
        await ctx.send("👋 Left the voice channel!")


def setup(bot):
    """Loads the cog into the bot (legacy discord.py)."""
    bot.add_cog(Music(bot))
