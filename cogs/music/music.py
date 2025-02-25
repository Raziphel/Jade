import discord
from discord.ext.commands import Cog, command
import aiohttp
import asyncio


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.node = {
            "host": "172.18.0.1",
            "port": 8197,
            "password": "youshallnotpass",
        }
        self.players = {}  # Keeps track of guild music states
        self.queues = {}  # Track queues for each guild

        self.bot.loop.create_task(self.initialize())

    async def initialize(self):
        """Ensures session is created and Lavalink session is registered."""
        await self.bot.wait_until_ready()
        if self.session is None:
            self.session = aiohttp.ClientSession()
        await self.create_lavalink_session()  # 🔹 Creates a session before using Lavalink!

    async def create_lavalink_session(self):
        """Creates a Lavalink session for the bot."""
        async with self.session.post(
            f"http://{self.node['host']}:{self.node['port']}/v4/sessions",
            headers={"Authorization": self.node["password"], "Content-Type": "application/json"},
            json={"resumingKey": "my-session", "timeout": 60}
        ) as response:
            if response.status == 201:
                print("✅ Lavalink session created successfully!")
            else:
                print(f"❌ Failed to create session: {await response.text()}")

    async def send_ws(self, data: dict):
        """Sends a JSON payload to Lavalink using REST API."""
        session_id = "my-session"
        async with self.session.patch(
            f"http://{self.node['host']}:{self.node['port']}/v4/sessions/{session_id}/players/{data['guildId']}",
            headers={"Authorization": self.node["password"], "Content-Type": "application/json"},
            json=data
        ) as response:
            if response.status not in [200, 204]:
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

            print(f"🔍 Lavalink Response: {data}")

            if "data" not in data or not isinstance(data["data"], list):
                print(f"❌ Unexpected response structure: {data}")
                return None

            return data["data"][0] if data["data"] else None

    async def join_voice(self, ctx):
        """Joins the user's voice channel."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return None

        channel = ctx.author.voice.channel
        if ctx.guild.voice_client:
            return ctx.guild.voice_client.channel

        await ctx.guild.change_voice_state(channel=channel)

        self.players[ctx.guild.id] = {"channel": channel.id}

        await asyncio.sleep(1)

        await self.send_ws({
            "guildId": str(ctx.guild.id),
            "channelId": str(channel.id),
            "selfDeaf": True
        })

        await ctx.send(f"🎶 Joined **{channel.name}**!")
        return channel

    @command()
    async def play(self, ctx, *, query: str):
        """Plays a song. Joins voice if not already in one."""
        channel = await self.join_voice(ctx)
        if not channel:
            return

        track = await self.search_track(query)
        if not track:
            return await ctx.send("❌ No results found!")

        track_id = track.get("encoded")
        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = []

        if ctx.guild.id in self.players and self.players[ctx.guild.id].get("playing"):
            self.queues[ctx.guild.id].append(track)
            return await ctx.send(f"📌 Added to queue: **{track['info']['title']}**")

        self.players[ctx.guild.id]["playing"] = True

        await self.send_ws({
            "track": track_id,
            "guildId": str(ctx.guild.id),
            "paused": False
        })

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            self.players[ctx.guild.id]["playing"] = False
            return await ctx.send("❌ No more songs in the queue!")

        track_data = self.queues[ctx.guild.id].pop(0)
        track_id = track_data.get("encoded")

        if not track_id:
            return await ctx.send("❌ Failed to retrieve track data!")

        await self.send_ws({
            "track": track_id,
            "guildId": str(ctx.guild.id),
            "paused": False
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

        self.queues[ctx.guild.id] = []
        self.players[ctx.guild.id]["playing"] = False

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

        await self.play_next(ctx)

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
