import discord
from discord.ext.commands import Cog, command
import aiohttp
import asyncio


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.node = {
            "host": "172.18.0.1",  # Lavalink host
            "port": 8197,  # Lavalink port
            "password": "youshallnotpass",  # Lavalink password
        }
        self.session_id = None  # Stores Lavalink session ID
        self.players = {}  # Tracks active players
        self.queues = {}  # Tracks song queues

        self.bot.loop.create_task(self.connect_lavalink())

    async def connect_lavalink(self):
        """Connects to Lavalink WebSocket and retrieves session ID."""
        await self.bot.wait_until_ready()

        while True:
            try:
                self.lavalink_ws = await self.session.ws_connect(
                    f"ws://{self.node['host']}:{self.node['port']}/v4/websocket",
                    headers={
                        "Authorization": self.node["password"],
                        "User-Id": str(self.bot.user.id)
                    }
                )

                # Wait for Lavalink's "ready" message to get session ID
                msg = await self.lavalink_ws.receive_json()
                if msg.get("op") == "ready":
                    self.session_id = msg["sessionId"]
                    print(f"🎶 Lavalink Ready! Session ID: {self.session_id}")
                    break
                else:
                    print(f"⚠️ Unexpected Lavalink WS message: {msg}")
            except aiohttp.ClientError as e:
                print(f"⚠️ Lavalink connection error: {e}")
                await asyncio.sleep(5)

    async def send_ws(self, guild_id, data: dict):
        """Sends a PATCH request to Lavalink REST API."""
        if not self.session_id:
            print("❌ Cannot send data, Lavalink session ID is missing!")
            return

        url = f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{self.session_id}/players/{guild_id}"

        async with self.session.patch(
            url,
            headers={
                "Authorization": self.node["password"],
                "Content-Type": "application/json"
            },
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

            print(f"🔍 Lavalink Response: {data}")

            if "data" not in data or not isinstance(data["data"], list):
                print(f"❌ Unexpected Lavalink response structure: {data}")
                return None

            return data["data"][0] if data["data"] else None

    async def join_voice(self, ctx):
        """Joins a voice channel."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return None

        channel = ctx.author.voice.channel
        if ctx.guild.voice_client:
            return ctx.guild.voice_client.channel

        await ctx.guild.change_voice_state(channel=channel)  # Novus-compatible VC join

        self.players[ctx.guild.id] = {"channel": channel.id}

        await self.send_ws(ctx.guild.id, {
            "guildId": str(ctx.guild.id),
            "channelId": str(channel.id),
            "selfDeaf": True
        })

        await asyncio.sleep(1)  # Allow time for Lavalink to process connection
        await ctx.send(f"🎶 Joined **{channel.name}**!")
        return channel

    @command()
    async def play(self, ctx, *, query: str):
        """Plays a song, joining VC if needed."""
        channel = await self.join_voice(ctx)
        if not channel:
            return

        track = await self.search_track(query)
        if not track:
            return await ctx.send("❌ No results found!")

        track_id = track.get("encoded")  # Lavalink v4 fix
        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        await self.send_ws(ctx.guild.id, {
            "track": track_id,
            "guildId": str(ctx.guild.id),
            "paused": False
        })

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            return await ctx.send("❌ No more songs in the queue!")

        track_data = self.queues[ctx.guild.id].pop(0)
        track_id = track_data.get("encoded")

        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        await self.send_ws(ctx.guild.id, {
            "op": "play",
            "guildId": str(ctx.guild.id),
            "track": track_id
        })

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

        await self.send_ws(ctx.guild.id, {
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("🎵 Stopped the music and cleared the queue!")

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            del self.players[ctx.guild.id]

    @command()
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_ws(ctx.guild.id, {
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("⏩ Skipped the song!")
        await self.play_next(ctx)

    @command()
    async def leave(self, ctx):
        """Leaves the voice channel."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not in a voice channel!")

        await self.send_ws(ctx.guild.id, {
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
