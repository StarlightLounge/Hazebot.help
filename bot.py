import sys
import os
import subprocess
import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import datetime
import aiohttp
import base64
import json
from dotenv import load_dotenv
from utils.mongo import db
from utils.logic import sync_member_roles, get_xp_needed, get_xp_multiplier

# Load .env
load_dotenv()

# --- NEURAL AUTO-SYNC (DAVE PROTOCOL) ---
try:
    import dave
except ImportError:
    try:
        print("🛠️ [System] Neural Voice protocols missing. Attempting force-sync...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "dave.py", "--user"])
        print("✅ [System] Neural Voice protocols synchronized.")
    except: pass

class HazeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        raw_ids = os.getenv("OWNER_IDS", os.getenv("OWNER_ID", ""))
        owner_ids = {int(i.strip()) for i in raw_ids.split(",") if i.strip().isdigit()}
        super().__init__(command_prefix="!", intents=intents, owner_ids=owner_ids)
        self.xp_cooldowns = {}
        self.launch_time = datetime.datetime.now(datetime.timezone.utc)

    async def setup_hook(self):
        # 0. Background Tasks
        self.stats_sync_task.start()
        self.voice_xp_task.start()
        self.status_loop.start()

        # 1. Module Initialization
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"📦 [Module] {filename} -> ONLINE")
                except Exception as e:
                    print(f"❌ [Module] {filename} -> FAILED: {e}")
        
        # 2. View Persistence
        try:
            from cogs.server_setup import RoleView, ColorView, SupportTicketView, CloseTicketView, GenderView
            from cogs.verification import VerificationReview
            from cogs.partnerships import PartnershipView, PartnerRoleView
            self.add_view(RoleView())
            self.add_view(ColorView())
            self.add_view(GenderView())
            self.add_view(SupportTicketView())
            self.add_view(CloseTicketView())
            self.add_view(VerificationReview())
            self.add_view(PartnerRoleView())
        except: pass

        # 3. Global Error Handling (Tree Level)
        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandOnCooldown):
                return await interaction.response.send_message(f"⌛ **Cooldown Active.** Retry in `{error.retry_after:.1f}s`.", ephemeral=True)
            elif isinstance(error, app_commands.MissingPermissions):
                return await interaction.response.send_message("❌ **Access Denied.** Your permissions do not match the required frequency.", ephemeral=True)
            elif isinstance(error, app_commands.CheckFailure):
                return # Handled by elite_only or other checks
            
            # Handle Hierarchy and Discord permission errors specifically
            inner_error = getattr(error, "original", error)
            if isinstance(inner_error, discord.Forbidden):
                try: return await interaction.response.send_message("❌ **Hierarchy/Permission Error.** The bot does not have sufficient clearance to perform this action (Check role position).", ephemeral=True)
                except: pass

            print(f"🔥 [Neural Error] {error}")
            try:
                await interaction.response.send_message("⚠️ **Neural Link Unstable.** A system error occurred. The High Architect has been notified.", ephemeral=True)
            except: pass

        # 4. Neural Synchronization (Command Tree Sync)
        try:
            print("🛰️ [Tree] Synchronizing frequencies with Discord...")
            await self.tree.sync()
            print("✅ [Tree] Neural Core Stabilized & Synced.")
        except Exception as e:
            print(f"❌ [Tree] Synchronization FAILED: {e}")

    async def on_app_command_completion(self, interaction: discord.Interaction, command: app_commands.Command | app_commands.ContextMenu):
        """Universal tracker for the Neural Synergy system."""
        engagement = self.get_cog("Engagement")
        if not engagement: return
        
        # Find category by command name (handling nested group commands)
        full_name = command.qualified_name
        found_cat = None
        for cat, cmds in engagement.categories.items():
            if full_name in cmds or any(full_name.startswith(c) for c in cmds):
                found_cat = cat
                break
        
        if not found_cat: return
        
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        user_data = db.get_user(user_id, guild_id)
        synergy = user_data.get('synergy', {'last_reset': datetime.datetime.now().date().isoformat(), 'used_categories': []})
        
        today = datetime.datetime.now().date().isoformat()
        if synergy['last_reset'] != today:
            synergy = {'last_reset': today, 'used_categories': []}

        if found_cat not in synergy['used_categories']:
            synergy['used_categories'].append(found_cat)
            db.update_user(user_id, guild_id, {"synergy": synergy})
            
            if len(synergy['used_categories']) == len(engagement.categories):
                try:
                    await interaction.followup.send(
                        "✨ **HIGH VIBE STATE ACHIEVED.**\n"
                        "You have synchronized with every neural module today. "
                        "Global Multipliers are now active for the next 2 hours!",
                        ephemeral=True
                    )
                except: pass

    @tasks.loop(minutes=1)
    async def status_loop(self):
        """Dynamic Status Loop: Updates presence with real-time uptime and community metrics."""
        await self.wait_until_ready()
        
        # Calculate Uptime
        uptime = datetime.datetime.now(datetime.timezone.utc) - self.launch_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        uptime_str = f"{days}d {hours}h {minutes}m"
        server_count = len(self.guilds)
        user_count = sum(g.member_count for g in self.guilds if g.member_count)
        
        # Cycle through statuses
        statuses = [
            f"⚡ Uptime: {uptime_str}",
            f"🛰️ Nodes: {server_count}",
            f"👥 Subjects: {user_count:,}",
            "💨 Join: discord.gg/CSwYkE57DE"
        ]
        
        status = random.choice(statuses)
        await self.change_presence(activity=discord.CustomActivity(name=status))
        # print(f"📡 [Status] Cycle: {status}")

    @tasks.loop(minutes=1)
    async def voice_xp_task(self):
        """Metabolic VC Leveling: Grants XP to active nodes in voice frequencies every minute."""
        await self.wait_until_ready()
        for guild in self.guilds:
            if not db.is_elite_enabled(guild.id): continue
            
            for vc in guild.voice_channels:
                if len(vc.members) < 2: continue # Prevent AFK solo farming
                
                for member in vc.members:
                    if member.bot: continue
                    if member.voice.self_deaf or member.voice.deaf: continue # Must be listening/active
                    
                    user = db.get_user(member.id, guild.id)
                    multiplier = get_xp_multiplier(member, user)
                    
                    # Grant 5-15 metabolic XP per minute
                    xp_gain = int(random.randint(5, 15) * multiplier)
                    new_xp = user.get("xp", 0) + xp_gain
                    current_level = user.get("level", 1)
                    next_level_xp = get_xp_needed(current_level)

                    if new_xp >= next_level_xp:
                        new_level = current_level + 1
                        await sync_member_roles(member, new_level)
                        
                        # THEMATIC ASCENSION PROTOCOL
                        is_crypt = "CRYPT" in guild.name.upper()
                        title_text = "🦴 NECROTIC ASCENSION (VOICE)" if is_crypt else "✨ ASTRAL ASCENSION (VOICE)"
                        desc_text = f"**{member.name}** has been resurrected to **Tier {new_level}** through audio synchronization." if is_crypt else f"**{member.name}** has ascended to **Tier {new_level}** through audio synchronization."
                        color_code = 0x000000 if is_crypt else 0x00FFCC

                        embed = discord.Embed(
                            title=title_text,
                            description=desc_text,
                            color=color_code
                        )
                        
                        terminal = discord.utils.get(guild.text_channels, name="󠇲 ┇ ◌ ascension-terminal")
                        if terminal: await terminal.send(embed=embed)
                        
                        db.update_user(member.id, guild.id, {"level": new_level, "xp": 0})
                    else:
                        db.update_user(member.id, guild.id, {"xp": new_xp})

    @tasks.loop(seconds=30)
    async def stats_sync_task(self):
        """Background task to sync bot stats and Bisect telemetry."""
        await self.wait_until_ready()
        try:
            # 1. Basic Discord Stats
            server_count = len(self.guilds)
            user_count = sum(g.member_count for g in self.guilds if g.member_count)
            
            # Music Metrics
            music_cog = self.get_cog("Music")
            active_sessions = 0
            if music_cog:
                active_sessions = sum(1 for state in music_cog.states.values() if state.voice_client and state.voice_client.is_connected())

            # Global Playlists (Aggregate from DB)
            top_playlists = []
            if db.connected:
                # Find users with playlists and get a sample of names
                pipeline = [
                    {"$match": {"playlists": {"$exists": True}}},
                    {"$project": {"playlists": {"$objectToArray": "$playlists"}}},
                    {"$unwind": "$playlists"},
                    {"$project": {"name": "$playlists.k", "count": {"$size": "$playlists.v"}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 5}
                ]
                top_playlists = list(db.users.aggregate(pipeline))

            stats = {
                "serverCount": server_count,
                "userCount": user_count,
                "influenceHarvested": "1.5M+",
                "activeSoundstages": active_sessions,
                "globalPlaylists": [{"name": p['name'], "tracks": p['count']} for p in top_playlists],
                "telemetry": {
                    "status": "OFFLINE",
                    "cpu": "0%",
                    "ram": "0MB",
                    "uptime": "0h 0m"
                }
            }

            # 2. Bisect Hosting Telemetry
            bisect_url = os.getenv("BISECT_URL")
            bisect_id = os.getenv("BISECT_SERVER_ID")
            bisect_key = os.getenv("BISECT_API_KEY")

            if bisect_url and bisect_id and bisect_key and bisect_key != "YOUR_CLIENT_API_KEY_HERE":
                api_url = f"{bisect_url.rstrip('/')}/api/client/servers/{bisect_id}/resources"
                headers = {
                    "Authorization": f"Bearer {bisect_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            res = data.get('attributes', {})
                            
                            # Format uptime
                            ms = res.get('uptime', 0)
                            hours, remainder = divmod(int(ms / 1000), 3600)
                            minutes, _ = divmod(remainder, 60)
                            
                            stats["telemetry"] = {
                                "status": res.get('current_state', 'UNKNOWN').upper(),
                                "cpu": f"{res.get('resources', {}).get('cpu_absolute', 0):.1f}%",
                                "ram": f"{res.get('resources', {}).get('memory_bytes', 0) / 1024 / 1024:.0f}MB",
                                "uptime": f"{hours}h {minutes}m"
                            }

            # 3. Update local and remote stats
            with open("stats.json", "w") as f:
                json.dump(stats, f, indent=2)
                
            await self.update_website_stats(stats)
            # print(f"🛰️ [Sync] Telemetry updated: {stats['telemetry']['status']}")
        except Exception as e:
            print(f"🔥 [Sync] Failed to sync stats: {e}")

    async def update_website_stats(self, stats_dict):
        """Pushes stats.json to GitHub repository."""
        token = os.getenv("GITHUB_TOKEN")
        repo = "StarlightLounge/Hazebot.help" 
        path = "stats.json"
        
        if not token: return

        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {"Authorization": f"token {token}"}

        async with aiohttp.ClientSession() as session:
            try:
                # 1. Get the current file SHA
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200: return
                    data = await resp.json()
                    sha = data['sha']

                # 2. Push updated content
                content = base64.b64encode(json.dumps(stats_dict, indent=2).encode()).decode()
                payload = {
                    "message": "🛰️ Auto-sync: Neural node count update",
                    "content": content,
                    "sha": sha,
                    "branch": "main"
                }
                
                async with session.put(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        print(f"❌ [GitHub API] Error: {await resp.text()}")
            except: pass

bot = HazeBot()

@bot.event
async def on_ready():
    print(f"🚀 [Bot] Logged in as {bot.user}")
    
    # --- CUSTOM STATUS ---
    discord_invite = "discord.gg/CSwYkE57DE"
    status_text = f"💨 Join our Discord! | {discord_invite}"
    
    await bot.change_presence(
        activity=discord.CustomActivity(name=status_text)
    )
    print(f"📡 [Status] Online: {status_text}")

@bot.event
async def on_member_join(member):
    # Sovereign Arrival Synchronization
    print(f"📥 [Singularity] New node detected: {member.name}")
    
    # 1. Automatic Frequency Alignment (Thematic Auto-Roles)
    if db.is_elite_enabled(member.guild.id):
        # Priority list for automatic assignment across all templates
        auto_roles = [
            "〔 ⟡ 〕SUPPORTER", "〔 ⟡ 〕NEW BUD", 
            "〔 🌑 〕RECENTLY DEPARTED", "〔 ⟡ 〕NEW ARRIVAL",
            "〔 ⟡ 〕LATE ARRIVAL", "〔 ⟡ 〕CRYPT MEMBER"
        ]
        
        for role_name in auto_roles:
            role = discord.utils.get(member.guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-alignment: Subject Arrival")
                    print(f"✅ [Sync] Assigned {role_name} to {member.name}")
                    break # Assign only the first one found
                except Exception as e:
                    print(f"❌ [Sync] Role assignment failed for {member.name}: {e}")
                    break

    # 2. Database Initialization
    db.update_user(member.id, member.guild.id, {
        "$setOnInsert": {
            "expedition_until": None,
            "debuff_until": None,
            "inventory": []
        }
    })

    # 3. Custom Welcome Protocol
    welcome_channel_id, welcome_text = db.get_welcome_config(member.guild.id)
    if welcome_channel_id and welcome_text:
        channel = member.guild.get_channel(int(welcome_channel_id))
        if channel:
            formatted_text = welcome_text.replace("{user}", member.mention).replace("{server}", member.guild.name)
            
            # Thematic Vibe Check for Welcome Embed
            is_crypt = "CRYPT" in member.guild.name.upper()
            embed = discord.Embed(
                title="⚜️ NEW NODE SYNCHRONIZED" if not is_crypt else "🦴 NEW SOUL RESURRECTED",
                description=formatted_text,
                color=0x00FFCC if not is_crypt else 0x000000
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            try:
                await channel.send(content=member.mention, embed=embed)
            except Exception as e:
                print(f"⚠️ [Welcome] Failed to broadcast in {channel.name}: {e}")
            return # Exit here so we don't send the fallback DM

    # 4. Fallback: Neural Vibe Check DM
    try:
        embed = discord.Embed(
            title="⚜️ WELCOME TO ELITE ELYSIUM",
            description=(
                "I am the **Sovereign Concierge**. You have been successfully synchronized "
                "with our neural network frequency.\n\n"
                "**◈ ACCESS GRANTED:** Base Tier Status\n"
                "**◈ PROTOCOL:** Review the information channels immediately.\n\n"
                "To fully stabilize your frequency, tell me: **What is your philosophy on the perfect harvest?**"
            ),
            color=0xFFFFFF
        )
        await member.send(embed=embed)
    except:
        print(f"⚠️ [Concierge] DM blocked by subject: {member.name}")

@bot.tree.command(name="plug", description="Consult with the Sovereign Concierge")
async def plug(interaction: discord.Interaction, thought: str):
    from utils.ai import ai
    await interaction.response.defer(ephemeral=True)
    response = await ai.get_response(thought, context=f"User: {interaction.user.name}", guild_id=interaction.guild_id)
    await interaction.followup.send(response)

@bot.command()
@commands.is_owner()
async def test(ctx):
    """Simple prefix test command"""
    await ctx.send(f"📡 **Neural Link Active.** Prefix: `{bot.command_prefix}` | Latency: `{round(bot.latency * 1000)}ms`")

@bot.command()
@commands.is_owner()
async def debug(ctx):
    """Owner only: Debug cog loading and command registration"""
    loaded_cogs = [c for c in bot.cogs]
    all_commands = [cmd.name for cmd in bot.tree.get_commands()]
    
    embed = discord.Embed(title="🛰️ SYSTEM DIAGNOSTICS", color=0x00FFCC)
    embed.add_field(name="📦 Loaded Modules", value=f"```\n{', '.join(loaded_cogs) if loaded_cogs else 'NONE'}\n```", inline=False)
    embed.add_field(name="📜 Global App Commands", value=f"```\n{', '.join(all_commands) if all_commands else 'NONE'}\n```", inline=False)
    
    # Check authorized guilds
    authorized_ids = [1379345399612969091, 1510757827369767012, 775914934180773958]
    guild_status = []
    for g_id in authorized_ids:
        g = bot.get_guild(g_id)
        status = "✅ ONLINE" if g else "❌ NOT FOUND"
        guild_status.append(f"{g_id}: {status}")
    
    embed.add_field(name="🌐 Authorized Nodes", value=f"```\n" + "\n".join(guild_status) + "\n```", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def sync(ctx, mode: str = None):
    """
    Sovereign Sync Protocol.
    !sync           - Global sync to all servers (Takes 1 hour)
    !sync guild     - Instant sync to THIS server
    !sync all       - Instant sync to EVERY server the bot is in
    !sync clear     - Wipe all global commands
    """
    try:
        if mode == "guild":
            print(f"🛰️ [Sync] Pushing to {ctx.guild.id}...")
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"⚡ **Instant Sync Complete.** `{len(synced)}` commands are live in this sector.")
        
        elif mode == "all":
            await ctx.send(f"🌌 **Omni-Sync Initiated.** Pushing to `{len(bot.guilds)}` nodes...")
            total = 0
            for guild in bot.guilds:
                try:
                    bot.tree.copy_global_to(guild=guild)
                    synced = await bot.tree.sync(guild=guild)
                    total += len(synced)
                    print(f"✅ Synced {guild.name}")
                except Exception as e:
                    print(f"❌ Failed to sync {guild.name}: {e}")
            await ctx.send(f"🌌 **Omni-Sync Complete.** `{total}` command instances stabilized across the singularity.")

        elif mode == "clear":
            print("🧨 [Clear] Wiping Global Command Tree...")
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            await ctx.send("🧹 **Global Commands Purged.** Now run `!sync` to rebuild.")
            
        else:
            print("🛰️ [Global Sync] Rebuilding Singularity...")
            synced = await bot.tree.sync()
            await ctx.send(f"🌍 **Global Sync Dispatched.** `{len(synced)}` app commands will propagate to all nodes within 1 hour.")
            
    except Exception as e:
        await ctx.send(f"❌ **Sync Error:** `{e}`")
        print(f"🔥 Sync Error: {e}")

@bot.event
async def on_message(message):
    # --- WEB-TO-VOICE BRIDGE ---
    if message.webhook_id and message.content.startswith("!webplay"):
        try:
            parts = message.content.replace("!webplay ", "").split("|", 1)
            if len(parts) == 2:
                username = parts[0].strip()
                query = parts[1].strip()
                
                # Try to find the member by username
                target_member = discord.utils.get(message.guild.members, name=username.split("#")[0])
                if not target_member:
                    target_member = discord.utils.get(message.guild.members, display_name=username)

                if target_member:
                    music_cog = bot.get_cog("Music")
                    if music_cog:
                        response = await music_cog.web_play(message.guild, target_member, query)
                        await message.channel.send(f"🛰️ **Web Request Processed:** {response}", delete_after=15)
                else:
                    await message.channel.send(f"❌ **Web Request Failed:** Subject `{username}` not found in this sector.", delete_after=15)
        except Exception as e:
            print(f"🔥 [Web Bridge Error] {e}")
        return

    if message.author.bot or not message.guild: return
    
    # Handle DMs for Vibe Check
    if isinstance(message.channel, discord.DMChannel):
        from utils.ai import ai
        response = await ai.vibe_check(message.author.name, message.content)
        await message.channel.send(response)
        return

    # --- AUTO-THREAD PROTOCOL ---
    if message.attachments:
        has_image = any(att.content_type and "image" in att.content_type for att in message.attachments)
        if has_image:
            try:
                # Create a thread based on the author's name or a default title
                thread_name = f"📸 {message.author.name}'s Transmission"
                await message.create_thread(name=thread_name, auto_archive_duration=1440)
            except Exception as e:
                print(f"⚠️ [Auto-Thread] Failed to create thread for {message.author.name}: {e}")

    # --- ELITE ELYSIUM PROTOCOLS ---
    if db.is_elite_enabled(message.guild.id):
        now = datetime.datetime.now()
        user_id = message.author.id
        if user_id in bot.xp_cooldowns:
            if (now - bot.xp_cooldowns[user_id]).total_seconds() < 60:
                return await bot.process_commands(message)

        user = db.get_user(message.author.id, message.guild.id)
        multiplier = get_xp_multiplier(message.author, user)
        
        # metabolic Leveling: XP gain based on message length + high vibe bonus
        base_xp = min(len(message.content) // 5 + 10, 50) # Boosted base
        random_bonus = random.randint(5, 15)
        xp_gain = int((base_xp + random_bonus) * multiplier)

        new_xp = user.get("xp", 0) + xp_gain
        current_level = user.get("level", 1)
        next_level_xp = get_xp_needed(current_level)

        if new_xp >= next_level_xp:
            new_level = current_level + 1
            await sync_member_roles(message.author, new_level)
            
            embed = discord.Embed(
                title="✨ ASTRAL ASCENSION",
                description=f"**{message.author.name}** has ascended to **Tier {new_level}**.",
                color=0xFFFFFF
            )
            
            # ROUTE TO ASCENSION TERMINAL
            terminal = discord.utils.get(message.guild.text_channels, name="󠇲 ┇ ◌ ascension-terminal")
            if terminal:
                await terminal.send(embed=embed)
            else:
                await message.channel.send(embed=embed, delete_after=15)
                
            db.update_user(message.author.id, message.guild.id, {"level": new_level, "xp": 0})
        else:
            db.update_user(message.author.id, message.guild.id, {"xp": new_xp})
        
        bot.xp_cooldowns[user_id] = now
    
    await bot.process_commands(message)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
    else: print("ERROR: Set DISCORD_TOKEN in .env")
