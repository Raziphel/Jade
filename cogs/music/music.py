import discord
from discord.ext import commands
import aiohttp
import asyncio
import uuid  # Generates a session ID for Lavalink

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.node = {
            "host": "172.18.0.1",
            "port": 8197,
            "password": "youshallnotpass",
        }
        self.players = {}  # Tracks active players
        self.queues = {}  # Track queues
        self.session_id = str(uuid.uuid4())  # Unique session ID for Lavalink

        bot.loop.create_task(self.initialize())

    async def initialize(self):
        """Ensures HTTP session is created and connects to Lavalink."""
        await self.bot.wait_until_ready()
        if self.session is None:
            self.session = aiohttp.ClientSession()
        await self.create_lavalink_session()

    async def create_lavalink_session(self):
        """Creates a session for the bot in Lavalink v4."""
        url = f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{self.session_id}"
        headers = {
            "Authorization": self.node["password"],
            "Content-Type": "application/json",
        }

        async with self.session.post(url, headers=headers, json={}) as response:
            if response.status != 201:  # 201 = Created
                error_text = await response.text()
                print(f"❌ Failed to create Lavalink session: {error_text}")
                return None
            print(f"✅ Lavalink session created: {self.session_id}")

    async def send_lavalink(self, guild_id: int, data: dict):
        """Sends an update request to Lavalink (PATCH request)."""
        url = f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{self.session_id}/players/{guild_id}"
        headers = {
            "Authorization": self.node["password"],
            "Content-Type": "application/json",
        }

        async with self.session.patch(url, headers=headers, json=data) as response:
            if response.status not in (200, 204):
                error_text = await response.text()
                print(f"❌ Lavalink REST Error: {error_text}")
                return None
            return await response.json() if response.status == 200 else None

    async def search_track(self, query: str):
        """Searches for a track on Lavalink."""
        url = f"http://{self.node['host']}:{self.node['port']}/v4/loadtracks"
        headers = {"Authorization": self.node["password"]}
        params = {"identifier": f"ytsearch:{query}"}

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status != 200:
                print(f"❌ Failed to search track: {await response.text()}")
                return None

            data = await response.json()
            return data["data"][0] if data["data"] else None

    async def join_voice(self, ctx):
        """Joins a voice channel and updates Lavalink."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return None

        channel = ctx.author.voice.channel

        if ctx.guild.voice_client:  # Already connected
            return ctx.guild.voice_client.channel

        await ctx.guild.change_voice_state(channel=channel)

        self.players[ctx.guild.id] = {"channel": channel.id}
        await asyncio.sleep(1)  # Let Lavalink process connection

        return channel

    @commands.command()
    async def play(self, ctx, *, query: str):
        """Plays a song or adds to queue."""
        channel = await self.join_voice(ctx)
        if not channel:
            return

        track = await self.search_track(query)
        if not track:
            return await ctx.send("❌ No results found!")

        track_id = track.get("encoded")
        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        # **PATCH request (not PUT) to play the track**
        await self.send_lavalink(ctx.guild.id, {"track": track_id, "paused": False})

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    @commands.command()
    async def stop(self, ctx):
        """Stops music and clears the queue."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        self.queues[ctx.guild.id] = []  # Clear queue
        await self.send_lavalink(ctx.guild.id, {"paused": True})
        await ctx.guild.voice_client.disconnect()

        del self.players[ctx.guild.id]
        await ctx.send("🎵 Stopped the music!")

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_lavalink(ctx.guild.id, {"track": None})
        await ctx.send("⏩ Skipped the song!")

    @commands.command()
    async def leave(self, ctx):
        """Disconnects the bot from the voice channel."""
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            del self.players[ctx.guild.id]
            await ctx.send("👋 Left the voice channel!")

def setup(bot):
    bot.add_cog(Music(bot))
