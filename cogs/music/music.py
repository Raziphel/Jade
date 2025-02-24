from discord.ext.commands import Cog, command
import aiohttp
import asyncio
import discord

class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
        self.lavalink_ws = None
        self.node = {
            "host": "172.18.0.1",
            "port": 8197,  # Lavalink port (make sure this matches your server config)
            "password": "youshallnotpass",
        }
        self.players = {}

        self.bot.loop.create_task(self.connect_lavalink())

    async def connect_lavalink(self):
        """Connects to the Lavalink WebSocket."""
        await self.bot.wait_until_ready()
        try:
            self.lavalink_ws = await self.session.ws_connect(
                f"ws://{self.node['host']}:{self.node['port']}/v4/websocket",
                headers={
                    "Authorization": self.node["password"],
                    "User-Id": str(self.bot.user.id)  # Required for Lavalink v4
                }
            )
            print("🎶 Connected to Lavalink!")
        except Exception as e:
            print(f"❌ Failed to connect to Lavalink: {e}")

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

    async def join_voice(self, ctx):
        """Joins the voice channel of the user if not already connected."""
        if not ctx.author.voice:
            await ctx.send("❌ You must be in a voice channel!")
            return None

        channel = ctx.author.voice.channel
        if ctx.guild.voice_client:
            return ctx.guild.voice_client.channel

        self.players[ctx.guild.id] = {"channel": channel.id}

        await self.send_ws({
            "op": "voiceUpdate",
            "guildId": str(ctx.guild.id),
            "channelId": str(channel.id)
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

        await self.send_ws({
            "op": "play",
            "guildId": str(ctx.guild.id),
            "track": track["track"]
        })

        await ctx.send(f"🎵 Now playing: **{track['info']['title']}**")

    @command()
    async def stop(self, ctx):
        """Stops music and leaves voice."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_ws({
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("🎵 Stopped the music!")

        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
            del self.players[ctx.guild.id]

    @command()
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.guild.id not in self.players:
            return await ctx.send("❌ I'm not playing anything!")

        await self.send_ws({
            "op": "stop",
            "guildId": str(ctx.guild.id)
        })

        await ctx.send("⏩ Skipped the song!")


def setup(bot):
    bot.add_cog(Music(bot))