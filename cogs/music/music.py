import discord
from discord.ext.commands import command, Cog, cog
import aiohttp
import asyncio
import uuid  # Lavalink needs a unique session ID

class Music(Cog):
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
        """Ensures HTTP session is created."""
        await self.bot.wait_until_ready()
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def send_lavalink(self, guild_id: int, data: dict):
        """Sends a correctly formatted update request to Lavalink."""
        url = f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{self.session_id}/players/{guild_id}"
        headers = {
            "Authorization": self.node["password"],
            "Content-Type": "application/json",
        }

        async with self.session.patch(url, headers=headers, json=data) as response:  # 🔹 Changed `PUT` → `PATCH`
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

    @command()
    async def play(self, ctx, *, query: str):
        """Plays a song. Joins voice if not already in one."""
        channel = await self.join_voice(ctx)  # Ensure bot joins VC
        if not channel:
            return

        track = await self.search_track(query)
        if not track:
            return await ctx.send("❌ No results found!")

        track_id = track.get("encoded")  # Lavalink v4 requires "encoded" only!
        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        # 🔹 FIXED: Sending only "encoded" string, NOT an object!
        payload = {
            "track": track_id,  # ✅ Correct format
            "paused": False,
            "volume": 100
        }

        await self.send_lavalink(ctx.guild.id, payload)

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")


    @command()
    async def stop(self, ctx):
        """Stops music and clears the queue."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        self.queues[ctx.guild.id] = []  # Clear queue
        await self.send_lavalink(ctx.guild.id, {"paused": True})
        await ctx.guild.voice_client.disconnect()

        del self.players[ctx.guild.id]
        await ctx.send("🎵 Stopped the music!")

    @command()
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_lavalink(ctx.guild.id, {"track": None})
        await ctx.send("⏩ Skipped the song!")

    @command()
    async def leave(self, ctx):
        """Disconnects the bot from the voice channel."""
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            del self.players[ctx.guild.id]
            await ctx.send("👋 Left the voice channel!")

def setup(bot):
    bot.add_cog(Music(bot))
