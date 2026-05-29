import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os

class GuildMusicState:
    def __init__(self):
        self.queue = []
        self.is_playing = False
        self.voice_client = None

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}

    def get_state(self, guild_id):
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    # yt-dlp configuration for best audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'nocheckcertificate': True,
        'quiet': True,
        # Remove custom headers/user_agent as they can interfere with SoundCloud's API
    }

    # FFmpeg options for streaming
    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    async def play_next(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if len(state.queue) > 0:
            state.is_playing = True
            url, title, webpage_url = state.queue.pop(0)

            try:
                # Use a fresh ydl with same opts for extraction
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    stream_url = info['url']
                    
                    executable = "./ffmpeg.exe" if os.path.exists("./ffmpeg.exe") else "ffmpeg"
                    
                    source = await discord.FFmpegOpusAudio.from_probe(stream_url, executable=executable, **self.ffmpeg_opts)
                    state.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(interaction)))
                    
                    embed = discord.Embed(
                        title="🔊 NOW ANCHORING FREQUENCY",
                        description=f"**Target:** [{title}]({webpage_url})\n**District:** `◌ [ SOUNDSTAGE ]`",
                        color=0x1db954 # Spotify-ish green
                    )
                    embed.set_footer(text="Elite Elysium Audio Protocol")
                    await interaction.channel.send(embed=embed)
            except Exception as e:
                print(f"Error playing track: {e}")
                await self.play_next(interaction)
        else:
            state.is_playing = False

    @app_commands.command(name="play", description="Synchronize the Soundstage with a neural audio frequency")
    @app_commands.describe(query="The frequency source (YouTube/SoundCloud link or search)")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ **Neural Link Failed.** Join a voice frequency first.", ephemeral=True)

        await interaction.response.defer()
        
        state = self.get_state(interaction.guild_id)
        channel = interaction.user.voice.channel
        
        if not state.voice_client or not state.voice_client.is_connected():
            state.voice_client = await channel.connect()

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                if "soundcloud.com" in query:
                    search_query = query
                elif query.startswith('http'):
                    search_query = query
                else:
                    search_query = f"ytsearch:{query}"
                
                info = ydl.extract_info(search_query, download=False)
                
                if 'entries' in info:
                    info = info['entries'][0]
                
                webpage_url = info.get('webpage_url') or info.get('url')
                title = info.get('title', 'Unknown Frequency')
                
                state.queue.append((webpage_url, title, webpage_url))
                await interaction.followup.send(f"✅ **Frequency Queued:** `{title}`")
                
                if not state.is_playing:
                    await self.play_next(interaction)
        except Exception as e:
            print(f"❌ [Music] Play error: {e}")
            await interaction.followup.send(f"❌ **Sync Failed:** `{e}`")

    @app_commands.command(name="skip", description="Move to the next audio frequency")
    async def skip(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.stop()
            await interaction.response.send_message("⏭️ **Frequency Advanced.**")
        else:
            await interaction.response.send_message("❌ No active frequency detected.", ephemeral=True)

    @app_commands.command(name="leave", description="Disconnect the bot from the Soundstage")
    async def leave(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if state.voice_client:
            await state.voice_client.disconnect()
            state.voice_client = None
            state.queue = []
            state.is_playing = False
            await interaction.response.send_message("👋 **Frequencies Neutralized.** Leaving Soundstage.")
        else:
            await interaction.response.send_message("❌ Not currently anchored to any frequency.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))
