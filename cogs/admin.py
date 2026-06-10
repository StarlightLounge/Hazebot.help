import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import staff_or_owner

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    admin_group = app_commands.Group(name="admin", description="GOD MODE: High-level system overrides")

    @admin_group.command(name="add_coins", description="GOD MODE: Inject Hash Coins into a subject")
    @staff_or_owner("administrator")
    async def add_coins(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user = db.get_user(member.id, interaction.guild_id)
        db.update_user(member.id, interaction.guild_id, {"hash_coins": user.get("hash_coins", 0) + amount})
        await interaction.response.send_message(f"✅ **Injection Complete.** Added `{amount:,} H$` to {member.mention}.", ephemeral=True)

    @admin_group.command(name="set_puffs", description="GOD MODE: Manually adjust a subject's puff count")
    @staff_or_owner("administrator")
    async def set_puffs(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        db.update_user(member.id, interaction.guild_id, {"puff_count": amount})
        await interaction.response.send_message(f"✅ **Neural Shift.** {member.mention}'s puff density set to `{amount}`.", ephemeral=True)

    @admin_group.command(name="servers", description="GOD MODE: List all synchronized sectors")
    @staff_or_owner()
    async def servers(self, interaction: discord.Interaction):
        guilds = "\n".join([f"• {g.name} (`{g.id}`)" for g in self.bot.guilds])
        await interaction.response.send_message(f"🌐 **Synchronized Sectors:**\n{guilds}", ephemeral=True)

    @admin_group.command(name="announce", description="HIGH ARCHITECT: Broadcast a global transmission")
    @staff_or_owner()
    async def announce(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(title="🛰️ GLOBAL TRANSMISSION", description=message, color=0x00FFCC)
        embed.set_footer(text="Sent by the High Architect")
        
        success = 0
        for guild in self.bot.guilds:
            target = guild.public_updates_channel or discord.utils.get(guild.text_channels, name="󠇲 ┇ ◌ announcements") or guild.system_channel
            if target:
                try: 
                    await target.send(embed=embed)
                    success += 1
                except: pass
        await interaction.followup.send(f"✅ **Transmission Successful.** Reached `{success}` sectors.", ephemeral=True)

    @admin_group.command(name="eval", description="OWNER: Execute raw neural logic")
    @staff_or_owner()
    async def eval_cmd(self, interaction: discord.Interaction, code: str):
        # Extremely dangerous, only for owner
        owner_ids = [int(i.strip()) for i in os.getenv("OWNER_IDS", "").split(",") if i.strip().isdigit()]
        if interaction.user.id not in owner_ids:
            return await interaction.response.send_message("❌ Access Denied.", ephemeral=True)
        await interaction.response.send_message("⚙️ **Executing...**", ephemeral=True)
        try: exec(code)
        except Exception as e: await interaction.followup.send(f"🔥 **Error:** `{e}`")

    @admin_group.command(name="reload", description="OWNER: Live-reload a system cog")
    @staff_or_owner()
    async def admin_reload(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await interaction.response.send_message(f"✅ Module `{cog}` synchronized.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Synchronization Failed: {e}", ephemeral=True)

    @admin_group.command(name="shutdown", description="OWNER: Terminate the singularity")
    @staff_or_owner()
    async def admin_shutdown(self, interaction: discord.Interaction):
        await interaction.response.send_message("🛑 **Neural Core Terminated.**", ephemeral=True)
        await self.bot.close()

    @admin_group.command(name="db_stats", description="OWNER: View database neural density")
    @staff_or_owner()
    async def admin_db_stats(self, interaction: discord.Interaction):
        users_count = db.users.count_documents({})
        guilds_count = db.guilds.count_documents({})
        embed = discord.Embed(title="🧠 NEURAL DATABASE STATS", color=0x3498db)
        embed.add_field(name="◈ Users", value=f"`{users_count}`")
        embed.add_field(name="◈ Guilds", value=f"`{guilds_count}`")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin_group.command(name="premium_grant", description="HIGH ARCHITECT: Grant or revoke Elite Premium status for a node")
    @staff_or_owner()
    async def premium_grant(self, interaction: discord.Interaction, guild_id: str, status: bool):
        try:
            db.set_premium(guild_id, status)
            await interaction.response.send_message(f"💎 **Premium Update.** Sector `{guild_id}` status: {status}")
        except:
            await interaction.response.send_message("❌ Error updating status.", ephemeral=True)

    @admin_group.command(name="airdrop", description="GOD MODE: Inject Hash Coins into every subject in the sector")
    @app_commands.describe(amount="Amount of Influence to airdrop")
    @staff_or_owner("administrator")
    async def airdrop(self, interaction: discord.Interaction, amount: int):
        if amount <= 0: return await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
        
        await interaction.response.defer()
        
        # Gathering all non-bot members
        members = [m for m in interaction.guild.members if not m.bot]
        count = 0
        
        for member in members:
            try:
                user = db.get_user(member.id, interaction.guild_id)
                db.update_user(member.id, interaction.guild_id, {"hash_coins": user.get("hash_coins", 0) + amount})
                count += 1
            except: pass
            
        embed = discord.Embed(
            title="📦 NEURAL AIRDROP COMPLETE",
            description=f"A massive injection of **{amount:,} H$** has been synchronized with **{count}** subjects.",
            color=0x00FFCC
        )
        embed.set_footer(text=f"Total Influence Distributed: {amount * count:,} H$")
        await interaction.followup.send(embed=embed)

    @admin_group.command(name="send_brand_asset", description="GOD MODE: Transmit professional community branding to a subject's DMs")
    @app_commands.describe(member="The subject to receive the asset", type="The specific brand frequency to send")
    @app_commands.choices(type=[
        app_commands.Choice(name="Elite Elysium Banner", value="elysium"),
        app_commands.Choice(name="Chronic Crypt Banner", value="crypt"),
        app_commands.Choice(name="Elite Afterdark Banner", value="afterdark")
    ])
    @staff_or_owner("administrator")
    async def send_brand_asset(self, interaction: discord.Interaction, member: discord.Member, type: str):
        await interaction.response.defer(ephemeral=True)
        
        # Neural Asset Mapping
        # Elysium: Using the local project file
        # Others: Using high-fidelity stable public links
        assets = {
            "elysium": "elysium_logo.png",
            "crypt": "https://images.unsplash.com/photo-1519074063912-ad25b5ce4970?q=80&w=1000", # Dark Gothic
            "afterdark": "https://images.unsplash.com/photo-1614850523296-d8c1af93d400?q=80&w=1000" # Deep Dark Red/Black
        }
        
        target = assets.get(type)
        
        embed = discord.Embed(
            title=f"🛰️ INCOMING BRAND TRANSMISSION: {type.upper()}",
            description="The High Architect has synchronized this professional community asset with your neural core.",
            color=0x00FFCC
        )
        embed.set_footer(text="Elite Elysium | Neural Asset Distribution")

        try:
            if type == "elysium":
                # Send local file
                file = discord.File(target, filename=target)
                embed.set_image(url=f"attachment://{target}")
                await member.send(file=file, embed=embed)
            else:
                # Send external URL
                embed.set_image(url=target)
                await member.send(embed=embed)
                
            await interaction.followup.send(f"✅ **Transmission Successful.** Asset `{type}` delivered to {member.name}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ **Transmission Failed.** Error: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
import os
