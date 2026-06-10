import discord
from discord.ext import commands, tasks
from discord import app_commands
from utils.mongo import db
import asyncio

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    async def force_update_guild(self, guild: discord.Guild):
        """Helper to update a guild's metrics immediately."""
        try:
            if not db.connected or db.db is None: return
            guild_data = db.guilds.find_one({"guild_id": str(guild.id)})
            if not guild_data or "stats_channels" not in guild_data: return
            
            stats_config = guild_data["stats_channels"]
            
            # 1. Gather Node Data
            online_count = sum(1 for m in guild.members if m.status != discord.Status.offline)
            
            # 2. Gather Economy Data (Guild-Specific)
            all_users = list(db.users.find({"guild_id": str(guild.id)}))
            total_puffs = sum(u.get("puff_count", 0) for u in all_users)
            total_balance = sum(u.get("hash_coins", 0) for u in all_users)
            
            # Total Assets = Sum of inventory items + HazeDex items
            total_assets = sum(len(u.get("inventory", [])) + len(u.get("hazedex", [])) for u in all_users)
            
            stats_map = {
                "total": f"👤 Total: {guild.member_count}",
                "online": f"🟢 Online: {online_count}",
                "boosts": f"💎 Boosts: {guild.premium_subscription_count}",
                "tokes": f"🌬️ Total Puffs: {total_puffs:,}",
                "economy": f"💰 Influence: {total_balance:,} H$",
                "assets": f"📦 Total Assets: {total_assets:,}"
            }
            
            for key, new_name in stats_map.items():
                ch_id = stats_config.get(key)
                if not ch_id: continue
                ch = guild.get_channel(int(ch_id))
                if ch and ch.name != new_name:
                    try: await ch.edit(name=new_name)
                    except: pass
        except Exception as e:
            print(f"🔥 [Stats] Force update failed for {guild.name}: {e}")

    @tasks.loop(minutes=5)
    async def update_stats(self):
        """Standard telemetry sync every 5 minutes."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            await self.force_update_guild(guild)

    @app_commands.command(name="setup_stats", description="Establish or Synchronize the Sovereign Metrics HUD")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_stats(self, interaction: discord.Interaction):
        """Initializes or restores the level-locked metrics channels."""
        if not db.connected: return await interaction.response.send_message("❌ Database Offline.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        
        guild_data = db.guilds.find_one({"guild_id": str(guild.id)}) or {}
        existing = guild_data.get("stats_channels", {})
        category = guild.get_channel(int(existing.get("category", 0)))
        if not category:
            overwrites = {guild.default_role: discord.PermissionOverwrite(connect=False)}
            category = await guild.create_category("📊 [ SERVER METRICS ]", position=0, overwrites=overwrites)
        
        # Initial Data gathering
        online_count = sum(1 for m in guild.members if m.status != discord.Status.offline)
        all_users = list(db.users.find({"guild_id": str(guild.id)}))
        total_puffs = sum(u.get("puff_count", 0) for u in all_users)
        total_balance = sum(u.get("hash_coins", 0) for u in all_users)
        total_assets = sum(len(u.get("inventory", [])) + len(u.get("hazedex", [])) for u in all_users)

        stats_map = {
            "total": f"👤 Total: {guild.member_count}",
            "online": f"🟢 Online: {online_count}",
            "boosts": f"💎 Boosts: {guild.premium_subscription_count}",
            "tokes": f"🌬️ Total Puffs: {total_puffs:,}",
            "economy": f"💰 Influence: {total_balance:,} H$",
            "assets": f"📦 Total Assets: {total_assets:,}"
            
        }
        
        new_config = {"category": str(category.id)}
        for key, name in stats_map.items():
            ch = guild.get_channel(int(existing.get(key, 0)))
            if not ch:
                ch = await guild.create_voice_channel(name, category=category)
            else:
                try: await ch.edit(name=name)
                except: pass
            new_config[key] = str(ch.id)
            
        db.guilds.update_one({"guild_id": str(guild.id)}, {"$set": {"stats_channels": new_config}}, upsert=True)
        await interaction.followup.send("📡 **Sovereign Metrics HUD Synchronized.** Economy telemetry established.", ephemeral=True)

    @app_commands.command(name="cleanup_stats", description="ADMIN: Remove the Sovereign Metrics HUD")
    @app_commands.checks.has_permissions(administrator=True)
    async def cleanup_stats(self, interaction: discord.Interaction):
        """Purges the HUD categories and records."""
        await interaction.response.defer(ephemeral=True)
        guild_data = db.guilds.find_one({"guild_id": str(interaction.guild_id)})
        if not guild_data or "stats_channels" not in guild_data:
            return await interaction.followup.send("❌ No Metrics HUD found in records.")
            
        stats_config = guild_data["stats_channels"]
        
        # 1. Delete Channels
        for key, ch_id in stats_config.items():
            if key == "category": continue
            ch = interaction.guild.get_channel(int(ch_id))
            if ch: 
                try: await ch.delete()
                except: pass
        
        # 2. Delete Category
        category = interaction.guild.get_channel(int(stats_config.get("category", 0)))
        if category:
            try: await category.delete()
            except: pass
            
        # 3. Clear DB
        db.guilds.update_one({"guild_id": str(interaction.guild_id)}, {"$unset": {"stats_channels": ""}})
        await interaction.followup.send("🧹 **Sovereign Metrics HUD Purged.**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerStats(bot))
