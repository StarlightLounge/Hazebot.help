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

    @tasks.loop(minutes=10)
    async def update_stats(self):
        """Background task to update server stat channels."""
        await self.bot.wait_until_ready()
        
        # Iterate through all guilds the bot is in
        for guild in self.bot.guilds:
            guild_data = db.db.guilds.find_one({"guild_id": str(guild.id)})
            if not guild_data or "stats_channels" not in guild_data:
                continue

            stats_config = guild_data["stats_channels"]
            
            # Helper to edit channel name if it changed
            async def update_ch(key, new_name):
                ch_id = stats_config.get(key)
                if not ch_id: return
                ch = guild.get_channel(int(ch_id))
                if ch and ch.name != new_name:
                    try: await ch.edit(name=new_name)
                    except: pass

            # 1. Total Members
            await update_ch("total", f"👤 Total: {guild.member_count}")

            # 2. Online Members
            online_count = sum(1 for m in guild.members if m.status != discord.Status.offline)
            await update_ch("online", f"🟢 Online: {online_count}")

            # 3. Boosts
            await update_ch("boosts", f"💎 Boosts: {guild.premium_subscription_count}")

            # 4. Top Rank Count (Eternal)
            role = discord.utils.get(guild.roles, name="〔 Ω 〕ETERNAL")
            eternal_count = len(role.members) if role else 0
            await update_ch("eternal", f"👑 Eternals: {eternal_count}")

            # 5. Economy (Total Hash Coins)
            all_users = list(db.users.find({"guild_id": str(guild.id)}))
            total_coins = sum(u.get("hash_coins", 0) for u in all_users)
            await update_ch("coins", f"💰 Economy: {total_coins:,} H$")

            # 6. Activity (Total Puffs)
            total_puffs = sum(u.get("puff_count", 0) for u in all_users)
            await update_ch("puffs", f"🌬️ Total Puffs: {total_puffs:,}")
            
            # 7. Global Vibe
            vibe = guild_data.get("vibe_level", 0)
            await update_ch("vibe", f"🌌 Global Vibe: {vibe:,}")

    @app_commands.command(name="setup_stats", description="Establish the Sovereign Metrics HUD (Live Stats Channels)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_stats(self, interaction: discord.Interaction):
        """Creates a dedicated category and channels for live server statistics."""
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # Create Category
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False) # Viewable but not joinable
        }
        
        category = await guild.create_category("📊 [ SERVER METRICS ]", overwrites=overwrites, position=0)

        # Gather initial data
        guild_data = db.db.guilds.find_one({"guild_id": str(guild.id)}) or {}
        total_count = guild.member_count
        online_count = sum(1 for m in guild.members if m.status != discord.Status.offline)
        boost_count = guild.premium_subscription_count
        
        role = discord.utils.get(guild.roles, name="〔 Ω 〕ETERNAL")
        eternal_count = len(role.members) if role else 0
        
        all_users = list(db.users.find({"guild_id": str(guild.id)}))
        total_coins = sum(u.get("hash_coins", 0) for u in all_users)
        total_puffs = sum(u.get("puff_count", 0) for u in all_users)
        vibe_level = guild_data.get("vibe_level", 0)

        # Create Stat Channels
        ch_total = await guild.create_voice_channel(f"👤 Total: {total_count}", category=category)
        ch_online = await guild.create_voice_channel(f"🟢 Online: {online_count}", category=category)
        ch_boosts = await guild.create_voice_channel(f"💎 Boosts: {boost_count}", category=category)
        ch_eternal = await guild.create_voice_channel(f"👑 Eternals: {eternal_count}", category=category)
        ch_coins = await guild.create_voice_channel(f"💰 Economy: {total_coins:,} H$", category=category)
        ch_puffs = await guild.create_voice_channel(f"🌬️ Total Puffs: {total_puffs:,}", category=category)
        ch_vibe = await guild.create_voice_channel(f"🌌 Global Vibe: {vibe_level:,}", category=category)

        # Save to DB
        db.db.guilds.update_one(
            {"guild_id": str(guild.id)},
            {"$set": {
                "stats_channels": {
                    "category": str(category.id),
                    "total": str(ch_total.id),
                    "online": str(ch_online.id),
                    "boosts": str(ch_boosts.id),
                    "eternal": str(ch_eternal.id),
                    "coins": str(ch_coins.id),
                    "puffs": str(ch_puffs.id),
                    "vibe": str(ch_vibe.id)
                }
            }},
            upsert=True
        )

        await interaction.followup.send("📡 **Sovereign Metrics HUD established at the top of the directory.**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerStats(bot))
