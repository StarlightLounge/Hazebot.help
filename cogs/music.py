import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import random
from utils.mongo import db
from utils.logic import premium_only

class GuildMusicState:
    def __init__(self):
        self.queue = []
        self.is_playing = False
        self.voice_client = None
        self.volume = 0.5
        self.shuffle = False
        self.radio = False
        self.current_track = None
        self.hud_message = None

class MusicHUD(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    def get_state(self):
        cog = self.bot.get_cog("Music")
        return cog.get_state(self.guild_id) if cog else None

    async def update_hud(self, interaction=None):
        state = self.get_state()
        if not state: return
        
        cog = self.bot.get_cog("Music")
        embed = cog.create_hud_embed(state)
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        elif state.hud_message:
            try: await state.hud_message.edit(embed=embed, view=self)
            except: pass

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, custom_id="music_prev")
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Feature coming soon!", ephemeral=True)

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, custom_id="music_pause")
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.get_state()
        if not state or not state.voice_client: return
        if state.voice_client.is_paused():
            state.voice_client.resume()
        else:
            state.voice_client.pause()
        await self.update_hud(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="music_skip")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.get_state()
        if state and state.voice_client:
            state.voice_client.stop()
            await interaction.response.send_message("⏭️ **Frequency Advanced.**", ephemeral=True)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="music_shuffle")
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not db.is_premium(interaction.guild_id):
            return await interaction.response.send_message("💎 **Elite Premium Required.** Contact the High Architect to unlock Neural Shuffling.", ephemeral=True)
            
        state = self.get_state()
        if not state: return
        state.shuffle = not state.shuffle
        if state.shuffle:
            random.shuffle(state.queue)
        button.style = discord.ButtonStyle.success if state.shuffle else discord.ButtonStyle.secondary
        await self.update_hud(interaction)

    @discord.ui.button(emoji="📻", style=discord.ButtonStyle.secondary, custom_id="music_radio")
    async def radio(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not db.is_premium(interaction.guild_id):
            return await interaction.response.send_message("💎 **Elite Premium Required.** Contact the High Architect to unlock Neural Radio.", ephemeral=True)

        state = self.get_state()
        if not state: return
        state.radio = not state.radio
        button.style = discord.ButtonStyle.success if state.radio else discord.ButtonStyle.secondary
        await self.update_hud(interaction)

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, custom_id="music_vol_down")
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.get_state()
        if not state: return
        state.volume = max(0.0, state.volume - 0.1)
        if state.voice_client and state.voice_client.source:
            state.voice_client.source.volume = state.volume
        await self.update_hud(interaction)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, custom_id="music_vol_up")
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.get_state()
        if not state: return
        state.volume = min(1.0, state.volume + 0.1)
        if state.voice_client and state.voice_client.source:
            state.voice_client.source.volume = state.volume
        await self.update_hud(interaction)

    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger, custom_id="music_stop")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = self.get_state()
        if state and state.voice_client:
            # Clear Voice Status
            try:
                vc_chan = state.voice_client.channel
                if vc_chan and vc_chan.permissions_for(vc_chan.guild.me).manage_channels:
                    await vc_chan.set_status(None)
            except: pass
            
            await state.voice_client.disconnect()
            state.voice_client = None
            state.queue = []
            state.is_playing = False
            if state.hud_message:
                try: await state.hud_message.delete()
                except: pass
                state.hud_message = None
            await interaction.response.send_message("👋 **Soundstage neutralized.**", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}

    def get_state(self, guild_id):
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': False, # Enabled for full playlist sync
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True # Faster extraction for playlists
    }

    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    def create_hud_embed(self, state):
        track = state.current_track
        title = track[1] if track else "Nothing Playing"
        url = track[2] if track else "#"
        
        embed = discord.Embed(
            title="🔊 SOUNDSTAGE HUD",
            description=f"**Now Synchronizing:** [{title}]({url})\n\n",
            color=0x1db954
        )
        
        queue_text = "\n".join([f"• {t[1][:40]}..." if len(t[1]) > 40 else f"• {t[1]}" for t in state.queue[:5]]) or "Queue Empty"
        embed.add_field(name="📋 UP NEXT", value=f"```\n{queue_text}\n```", inline=False)
        
        status = "⏸️ PAUSED" if state.voice_client and state.voice_client.is_paused() else "▶️ PLAYING"
        mode = "📻 RADIO ON" if state.radio else "⏹️ RADIO OFF"
        shuffle = "🔀 SHUFFLE ON" if state.shuffle else "⏹️ SHUFFLE OFF"
        
        embed.add_field(name="📊 STATUS", value=f"`{status}`", inline=True)
        embed.add_field(name="📡 MODE", value=f"`{mode}`", inline=True)
        embed.add_field(name="🔊 VOLUME", value=f"`{int(state.volume * 100)}%`", inline=True)
        
        embed.set_footer(text=f"Elite Elysium Audio Protocol | {shuffle}")
        return embed

    async def play_next(self, guild_id, channel):
        state = self.get_state(guild_id)
        if state.radio and len(state.queue) == 0 and state.current_track:
            await self.fetch_radio_track(guild_id)

        if len(state.queue) > 0:
            state.is_playing = True
            track = state.queue.pop(0)
            state.current_track = track
            url, title, webpage_url = track

            try:
                loop = self.bot.loop or asyncio.get_event_loop()
                # Need specific extraction for the stream URL here as extract_flat was True
                with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
                    info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                    stream_url = info['url']
                    
                    executable = "ffmpeg"
                    if os.name == 'nt' and os.path.exists("./ffmpeg.exe"):
                        executable = "./ffmpeg.exe"
                    
                    is_premium = db.is_premium(guild_id)
                    current_ffmpeg_opts = self.ffmpeg_opts.copy()
                    if is_premium:
                        current_ffmpeg_opts['options'] += ' -b:a 192k'
                    
                    source = discord.FFmpegPCMAudio(stream_url, executable=executable, **current_ffmpeg_opts)
                    volume_source = discord.PCMVolumeTransformer(source, volume=state.volume)
                    
                    def handle_after(error):
                        if error: print(f"Voice Error: {error}")
                        self.bot.loop.create_task(self.play_next(guild_id, channel))

                    state.voice_client.play(volume_source, after=handle_after)
                    
                    # ROBUST VOICE STATUS PROTOCOL
                    try:
                        if state.voice_client and state.voice_client.channel:
                            vc = state.voice_client.channel
                            if vc.permissions_for(vc.guild.me).manage_channels:
                                # Using edit(status=...) as it is more standard in some environments
                                await vc.edit(status=f"🎶 {title[:45]}")
                            else:
                                # Notify staff once if permissions are missing
                                print(f"⚠️ [Music] Missing Manage Channels in {guild_id}")
                                await channel.send("⚠️ **Neural Alert:** I cannot set the Voice Status. Grant me `Manage Channels` in this VC to enable high-fidelity labels.", delete_after=10)
                    except Exception as vs_e:
                        print(f"⚠️ [Music] VS Neural Error: {vs_e}")
                    
                    hud_embed = self.create_hud_embed(state)
                    if not state.hud_message:
                        state.hud_message = await channel.send(embed=hud_embed, view=MusicHUD(self.bot, guild_id))
                    else:
                        try: await state.hud_message.edit(embed=hud_embed, view=MusicHUD(self.bot, guild_id))
                        except: state.hud_message = await channel.send(embed=hud_embed, view=MusicHUD(self.bot, guild_id))
            except Exception as e:
                print(f"🔥 [Music] Error playing track: {e}")
                await self.play_next(guild_id, channel)
        else:
            state.is_playing = False
            state.current_track = None
            if state.voice_client:
                try: await state.voice_client.channel.set_status(None)
                except: pass
            if state.hud_message:
                try: await state.hud_message.edit(embed=self.create_hud_embed(state), view=None)
                except: pass

    async def fetch_radio_track(self, guild_id):
        state = self.get_state(guild_id)
        if not state.current_track: return
        query = f"related to {state.current_track[1]}"
        try:
            loop = self.bot.loop or asyncio.get_event_loop()
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(f"ytsearch:{query}", download=False))
                if 'entries' in info and len(info['entries']) > 1:
                    entry = random.choice(info['entries'][1:6])
                    state.queue.append((entry['url'], entry['title'], entry.get('webpage_url', entry['url'])))
        except: pass

    async def web_play(self, guild, member, query):
        """Helper to queue music from a raw text query (Web-to-Voice Bridge)."""
        if not member.voice or not member.voice.channel:
            return "❌ Target is not synchronized with a voice frequency."

        state = self.get_state(guild.id)
        channel = member.voice.channel
        
        if not state.voice_client or not state.voice_client.is_connected():
            try:
                state.voice_client = await channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                return f"❌ **Connection Failed:** `{e}`"

        try:
            loop = self.bot.loop or asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                search_query = query if query.startswith('http') else f"ytsearch:{query}"
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
                
                tracks_added = 0
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            track = (entry['url'], entry['title'], entry.get('webpage_url', entry['url']))
                            state.queue.append(track)
                            tracks_added += 1
                else:
                    track = (info['url'], info['title'], info.get('webpage_url', info['url']))
                    state.queue.append(track)
                    tracks_added = 1

                if state.shuffle: random.shuffle(state.queue)
                
                if not state.is_playing:
                    hud_channel = guild.system_channel
                    if not hud_channel:
                        for ch in guild.text_channels:
                            if ch.permissions_for(guild.me).send_messages:
                                hud_channel = ch
                                break
                    if hud_channel:
                        await self.play_next(guild.id, hud_channel)
                        
                return f"✅ **Neural Synchronization:** Queued `{tracks_added}` frequencies via Web Portal."
        except Exception as e:
            print(f"🔥 [Music Web-Play] Extraction Failed: {e}")
            return "❌ **Sync Failed:** Neural extraction error."

    @app_commands.command(name="play", description="Synchronize the Soundstage with a neural audio frequency (Supports Playlists)")
    @app_commands.describe(query="The frequency source (YouTube/SoundCloud link or search)")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join a voice frequency first.", ephemeral=True)

        await interaction.response.defer()
        state = self.get_state(interaction.guild_id)
        channel = interaction.user.voice.channel
        
        if not state.voice_client or not state.voice_client.is_connected():
            try:
                state.voice_client = await channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                return await interaction.followup.send(f"❌ **Connection Failed:** `{e}`")

        try:
            loop = self.bot.loop or asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                search_query = query if query.startswith('http') else f"ytsearch:{query}"
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
                
                tracks_added = 0
                if 'entries' in info:
                    # It's a playlist or search results
                    for entry in info['entries']:
                        if entry:
                            track = (entry['url'], entry['title'], entry.get('webpage_url', entry['url']))
                            state.queue.append(track)
                            tracks_added += 1
                else:
                    # Single track
                    track = (info['url'], info['title'], info.get('webpage_url', info['url']))
                    state.queue.append(track)
                    tracks_added = 1

                if state.shuffle: random.shuffle(state.queue)
                
                if tracks_added > 1:
                    await interaction.followup.send(f"🌌 **Neural Sync Complete.** Enqueued `{tracks_added}` frequencies from playlist.")
                else:
                    await interaction.followup.send(f"✅ **Queued:** `{state.queue[-1][1]}`")

                if not state.is_playing: 
                    await self.play_next(interaction.guild_id, interaction.channel)
        except Exception as e:
            print(f"🔥 [Music] Extraction Failed: {e}")
            await interaction.followup.send(f"❌ **Sync Failed:** Neural extraction error.")

    @app_commands.command(name="insert", description="Neural Priority: Add a track to the front of the queue")
    @app_commands.describe(query="The frequency source to play next")
    async def insert(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join a voice frequency first.", ephemeral=True)

        await interaction.response.defer()
        state = self.get_state(interaction.guild_id)
        channel = interaction.user.voice.channel
        
        if not state.voice_client or not state.voice_client.is_connected():
            try:
                state.voice_client = await channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                return await interaction.followup.send(f"❌ **Connection Failed:** `{e}`")

        try:
            loop = self.bot.loop or asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                search_query = query if query.startswith('http') else f"ytsearch:{query}"
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=False))
                
                tracks_to_insert = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            tracks_to_insert.append((entry['url'], entry['title'], entry.get('webpage_url', entry['url'])))
                else:
                    tracks_to_insert.append((info['url'], info['title'], info.get('webpage_url', info['url'])))

                # Insert at the front (reversed to maintain playlist order)
                for track in reversed(tracks_to_insert):
                    state.queue.insert(0, track)
                
                if len(tracks_to_insert) > 1:
                    await interaction.followup.send(f"⚡ **Priority Injected:** Enqueued `{len(tracks_to_insert)}` tracks to play next.")
                else:
                    await interaction.followup.send(f"⚡ **Priority Injected:** `{tracks_to_insert[0][1]}` will play next.")

                if not state.is_playing: 
                    await self.play_next(interaction.guild_id, interaction.channel)
        except Exception as e:
            print(f"🔥 [Music] Insertion Failed: {e}")
            await interaction.followup.send(f"❌ **Priority Failed:** Neural extraction error.")


    @app_commands.command(name="hud", description="Redeploy the Soundstage HUD")
    async def hud(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if not state.is_playing:
            return await interaction.response.send_message("❌ Soundstage is idle.", ephemeral=True)
        
        if state.hud_message:
            try: await state.hud_message.delete()
            except: pass
            
        state.hud_message = await interaction.channel.send(embed=self.create_hud_embed(state), view=MusicHUD(self.bot, interaction.guild_id))
        await interaction.response.send_message("📡 **HUD Relocated.**", ephemeral=True)

    @app_commands.command(name="queue", description="Display the current neural audio sequence")
    async def queue(self, interaction: discord.Interaction):
        """Displays the current music queue."""
        state = self.get_state(interaction.guild_id)
        if not state.queue and not state.current_track:
            return await interaction.response.send_message("❌ The sequence is currently void.", ephemeral=True)

        embed = discord.Embed(
            title="📋 NEURAL AUDIO SEQUENCE",
            color=0x1db954
        )

        if state.current_track:
            embed.add_field(name="▶️ SYNCHRONIZING", value=f"[{state.current_track[1]}]({state.current_track[2]})", inline=False)

        if state.queue:
            queue_list = ""
            for i, t in enumerate(state.queue[:10]):
                queue_list += f"**{i+1}.** [{t[1]}]({t[2]})\n"
            
            if len(state.queue) > 10:
                queue_list += f"\n*...and {len(state.queue) - 10} more frequencies.*"
            
            embed.add_field(name="⏳ UP NEXT", value=queue_list, inline=False)
        else:
            embed.add_field(name="⏳ UP NEXT", value="No upcoming frequencies.", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="music_debug", description="OWNER: Run a diagnostic on the audio engine")
    async def music_debug(self, interaction: discord.Interaction):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("❌ OWNER ONLY", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        embed = discord.Embed(title="🔊 AUDIO ENGINE DIAGNOSTICS", color=0x3498db)
        embed.add_field(name="◈ FFmpeg", value=f"`{ffmpeg_path}`" if ffmpeg_path else "❌ MISSING", inline=False)
        embed.add_field(name="◈ OS", value=f"`{os.name}`", inline=True)
        state = self.get_state(interaction.guild_id)
        vc = "CONNECTED" if state.voice_client and state.voice_client.is_connected() else "DISCONNECTED"
        embed.add_field(name="◈ VC", value=f"`{vc}`", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="vc_status", description="STAFF: Manually set or clear the voice channel status")
    @app_commands.describe(status="The text to display (Leave empty to clear)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def vc_status_cmd(self, interaction: discord.Interaction, status: str = None):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join a voice frequency first.", ephemeral=True)
        try:
            await interaction.user.voice.channel.set_status(status)
            await interaction.response.send_message(f"✅ **Voice Status Updated:** `{status or 'Cleared'}`", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Failed to set status:** `{e}`", ephemeral=True)

    @app_commands.command(name="save_playlist", description="PREMIUM: Save current queue as a permanent playlist")
    @app_commands.describe(name="Name for your playlist")
    @premium_only()
    async def save_playlist(self, interaction: discord.Interaction, name: str):
        state = self.get_state(interaction.guild_id)
        if not state.queue and not state.current_track:
            return await interaction.response.send_message("❌ Queue is empty.", ephemeral=True)
        tracks = []
        if state.current_track: tracks.append(state.current_track)
        tracks.extend(state.queue)
        db.update_user(interaction.user.id, interaction.guild_id, {f"playlists.{name}": tracks})
        await interaction.response.send_message(f"💾 **Playlist Saved:** `{name}`", ephemeral=True)

    @app_commands.command(name="load_playlist", description="PREMIUM: Synchronize a saved playlist")
    @app_commands.describe(name="The name of your saved playlist")
    @premium_only()
    async def load_playlist(self, interaction: discord.Interaction, name: str):
        user_data = db.get_user(interaction.user.id, interaction.guild_id)
        playlists = user_data.get("playlists", {})
        if name not in playlists:
            return await interaction.response.send_message(f"❌ Playlist `{name}` not found.", ephemeral=True)
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join a voice frequency first.", ephemeral=True)
        await interaction.response.defer()
        state = self.get_state(interaction.guild_id)
        state.queue.extend(playlists[name])
        await interaction.followup.send(f"🌌 **Neural Sync Complete.** Loaded `{len(playlists[name])}` tracks.")
        if not state.is_playing: await self.play_next(interaction.guild_id, interaction.channel)

    @app_commands.command(name="skip", description="Move to the next audio frequency")
    async def skip(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if state.voice_client:
            state.voice_client.stop()
            await interaction.response.send_message("⏭️ **Frequency Advanced.**")
        else:
            await interaction.response.send_message("❌ Idle.", ephemeral=True)

    @app_commands.command(name="leave", description="Disconnect from the Soundstage")
    async def leave(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        if state.voice_client:
            # Clear Voice Status
            try:
                vc_chan = state.voice_client.channel
                if vc_chan and vc_chan.permissions_for(vc_chan.guild.me).manage_channels:
                    await vc_chan.set_status(None)
            except: pass
            
            await state.voice_client.disconnect()
            state.voice_client = None
            state.queue = []
            state.is_playing = False
            if state.hud_message:
                try: await state.hud_message.delete()
                except: pass
                state.hud_message = None
            await interaction.response.send_message("👋 **Soundstage neutralized.**")
        else:
            await interaction.response.send_message("❌ Not connected.", ephemeral=True)

    @app_commands.command(name="vc_status_sync", description="OWNER: Force a neural synchronization of the current Voice Status")
    async def vc_status_sync(self, interaction: discord.Interaction):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
            
        state = self.get_state(interaction.guild_id)
        if not state.voice_client or not state.voice_client.channel:
            return await interaction.response.send_message("❌ Not in a voice frequency.", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        title = state.current_track[1] if state.current_track else "Haze Bot Synchronized"
        
        try:
            vc = state.voice_client.channel
            await vc.edit(status=f"📡 SYNC: {title[:40]}")
            await interaction.followup.send("✅ **Neural Pulse Sent.** The Voice Status has been force-synchronized.")
        except Exception as e:
            await interaction.followup.send(f"❌ **Sync Failed:** `{e}`\nEnsure the bot has `Manage Channels` in this VC.")

async def setup(bot):
    await bot.add_cog(Music(bot))
