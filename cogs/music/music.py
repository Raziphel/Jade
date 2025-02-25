import discord
from discord.ext.commands import Cog, command
import aiohttp
import asyncio


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.lavalink_ws = None
        self.node = {
            "host": "172.18.0.1",
            "port": 8197,
            "password": "youshallnotpass",
        }
        self.players = {}  # Keeps track of guild music states
        self.queues = {}  # New: Track queues for each guild

        self.bot.loop.create_task(self.initialize())

    async def initialize(self):
        """Ensures session is created and connects to Lavalink."""
        await self.bot.wait_until_ready()
        if self.session is None:
            self.session = aiohttp.ClientSession()
        await self.connect_lavalink()

    async def connect_lavalink(self):
        """Connects to the Lavalink WebSocket with auto-reconnect."""
        while True:
            try:
                self.lavalink_ws = await self.session.ws_connect(
                    f"http://{self.node['host']}:{self.node['port']}/v4/websocket",
                    headers={
                        "Authorization": self.node["password"],
                        "User-Id": str(self.bot.user.id),
                    }
                )
                print("🎶 Connected to Lavalink!")
                return
            except aiohttp.ClientError:
                print("⚠️ Failed to connect to Lavalink. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def send_ws(self, data: dict):
        """Sends a JSON payload to Lavalink (Replaced with HTTP API)."""
        session_id = self.bot.user.id  # Lavalink v4 requires a session per bot ID
        async with self.session.patch(
                f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{session_id}/players/{data['guildId']}",
                headers={"Authorization": self.node["password"], "Content-Type": "application/json"},
                json=data
        ) as response:
            if response.status != 204:  # 204 = success with no content
                print(f"❌ Failed to send data to Lavalink: {await response.text()}")

    async def search_track(self, query: str):
        """Searches for a track on Lavalink and handles errors properly."""
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

            # Debugging response
            print(f"🔍 Lavalink Response: {data}")

            # Ensure 'data' key exists and contains tracks
            if "data" not in data or not isinstance(data["data"], list):
                print(f"❌ Unexpected response structure: {data}")
                return None

            # Get the first track from search results
            return data["data"][0] if data["data"] else None

    async def join_voice(self, ctx):
        """Joins the voice channel of the user if not already connected."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return None

        channel = ctx.author.voice.channel
        if ctx.guild.voice_client:  # If already connected, return current channel
            return ctx.guild.voice_client.channel

        # Tell Discord to connect the bot to VC (Novus-compatible)
        await ctx.guild.change_voice_state(channel=channel)

        # Store player info
        self.players[ctx.guild.id] = {"channel": channel.id}

        # Send voice update using REST API
        await self.send_ws({
            "guildId": str(ctx.guild.id),
            "channelId": str(channel.id),
            "selfDeaf": True
        })

        await asyncio.sleep(1)  # Give Lavalink time to process the connection

        await ctx.send(f"🎶 Joined **{channel.name}**!")
        return channel

    @command()
    async def play(self, ctx, *, query: str):
        """Plays a song. Joins voice if not already in one."""
        channel = await self.join_voice(ctx)  # Auto-join before playing
        if not channel:
            return

        track = await self.search_track(query)
        if not track:
            return await ctx.send("❌ No results found!")

        track_id = track.get("encoded")  # Lavalink v4 fix!
        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        # Send play request via REST API
        await self.send_ws({
            "track": track_id,
            "guildId": str(ctx.guild.id),
            "paused": False
        })

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("❌ No more songs in the queue!")

        track_data = self.queues[ctx.guild.id].pop(0)  # Get first track in queue

        # Extract the correct track ID (Lavalink v4 uses 'encoded')
        track_id = track_data.get("encoded")  # Fix here!

        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        # Send play request to Lavalink
        await self.send_ws({
            "op": "play",
            "guildId": str(ctx.guild.id),
            "track": track_id  # Corrected from 'track["track"]' to 'track_id'
        })

        track_info = track_data["info"]
        await ctx.send(f"🎵 Now playing: **{track_info['title']}** - {track_info['uri']}")

    @command()
    async def queue(self, ctx):
        """Displays the queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("📭 The queue is empty!")

        queue_list = "\n".join(
            [f"{i+1}. {track['info']['title']}" for i, track in enumerate(self.queues[ctx.guild.id])]
        )

        embed = discord.Embed(title="🎶 Music Queue", description=queue_list, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @command()
    async def stop(self, ctx):
        """Stops music and clears the queue."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        self.queues[ctx.guild.id] = []  # Clear queue

        await self.send_ws({
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("🎵 Stopped the music and cleared the queue!")

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            del self.players[ctx.guild.id]

    @command()
    async def skip(self, ctx):
        """Skips the current song and plays the next one."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_ws({
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("⏩ Skipped the song!")

        await self.play_next(ctx)  # Play next song in queue

    @command()
    async def leave(self, ctx):
        """Makes the bot leave the voice channel."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not in a voice channel!")

        await self.send_ws({
            "op": "destroy",
            "guildId": str(ctx.guild.id)
        })

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()

        del self.players[ctx.guild.id]
        del self.queues[ctx.guild.id]
        await ctx.send("👋 Left the voice channel!")


def setup(bot):
    """Loads the cog into the bot."""
    bot.add_cog(Music(bot))
