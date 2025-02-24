from discord.ext.commands import Cog, command
import aiohttp
import asyncio


class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.lavalink_ws = None
        self.node = {
            "host": "127.0.0.1",
            "port": 7779,  # Lavalink port (make sure this matches your server config)
            "password": "youshallnotpass",
        }
        self.players = {}

        self.bot.loop.create_task(self.initialize())

    async def initialize(self):
        """Ensures session is created and connects to Lavalink."""
        await self.bot.wait_until_ready()
        if self.session is None:  # Ensure session is only created once
            self.session = aiohttp.ClientSession()
        await self.connect_lavalink()

    async def connect_lavalink(self):
        """Connects to the Lavalink WebSocket with auto-reconnect."""
        while True:
            try:
                self.lavalink_ws = await self.session.ws_connect(
                    f"ws://{self.node['host']}:{self.node['port']}",
                    headers={"Authorization": self.node["password"]}
                )
                print("🎶 Connected to Lavalink!")
                return  # Exit loop when successfully connected
            except aiohttp.ClientError:
                print("⚠️ Failed to connect to Lavalink. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def send_ws(self, data: dict):
        """Sends a JSON payload to Lavalink."""
        if self.lavalink_ws:
            await self.lavalink_ws.send_json(data)

    async def search_track(self, query: str):
        """Searches for a track on Lavalink."""
        async with self.session.get(
            f"http://{self.node['host']}:{self.node['port']}/loadtracks",
            params={"identifier": f"ytsearch:{query}"},
            headers={"Authorization": self.node["password"]}
        ) as response:
            data = await response.json()
            return data["tracks"][0] if data["tracks"] else None

    @command()
    async def join(self, ctx):
        """Make the bot join the user's voice channel."""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel! 🎤")

        channel = ctx.author.voice.channel
        self.players[ctx.guild.id] = {"channel": channel.id}

        await self.send_ws({
            "op": "voiceUpdate",
            "guildId": str(ctx.guild.id),
            "channelId": str(channel.id)
        })

        await ctx.send(f"🎶 Joined **{channel.name}**!")

    @command()
    async def play(self, ctx, *, query: str):
        """Search and play a song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("I'm not in a voice channel! ❌")

        track = await self.search_track(query)
        if not track:
            return await ctx.send("No results found! 😿")

        await self.send_ws({
            "op": "play",
            "guildId": str(ctx.guild.id),
            "track": track["track"]
        })

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    @command()
    async def stop(self, ctx):
        """Stop playback."""
        if ctx.guild.id not in self.players:
            return await ctx.send("I'm not playing anything! ❌")

        await self.send_ws({
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("🎵 Stopped the music!")

    @command()
    async def skip(self, ctx):
        """Skip the current song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("I'm not playing anything! ⏭️")

        await self.send_ws({
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("⏩ Skipped the song!")

    async def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        if self.session:
            await self.session.close()
        if self.lavalink_ws:
            await self.lavalink_ws.close()


def setup(bot):
    """Loads the cog into the bot."""
    bot.add_cog(Music(bot))
