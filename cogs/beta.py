import discord
from discord.ext import commands
from discord import app_commands
import functools
import random
import datetime
import asyncio
import os
from utils.mongo import db

# AUTHORIZED BETA NODES
BETA_SERVER_ID = 775914934180773958
AUTHORIZED_SUBJECTS = [900563137114292265, 296687038546182144, 775913593396264974]

def beta_only():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in AUTHORIZED_SUBJECTS and interaction.guild_id == BETA_SERVER_ID
    return app_commands.check(predicate)

class BetaFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="beta_status", description="BETA: Check your synchronization with the Laboratory Frequency")
    @beta_only()
    async def beta_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🧪 LABORATORY SYNCHRONIZATION",
            description="Your neural link is successfully synced with the Laboratory Frequency.",
            color=0x9B59B6
        )
        embed.add_field(name="◈ SECTOR", value=f"`{BETA_SERVER_ID}`", inline=True)
        embed.add_field(name="◈ STATUS", value="`AUTHORIZED RAT`", inline=True)
        embed.set_footer(text="Haze Bot Laboratory Protocol")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="beta_telemetry", description="BETA: Access the singularity's raw performance metrics")
    @beta_only()
    async def beta_telemetry(self, interaction: discord.Interaction):
        # Simulated/Calculated telemetry
        latency = round(self.bot.latency * 1000)
        guilds = len(self.bot.guilds)
        users = sum(g.member_count for g in self.bot.guilds)
        
        embed = discord.Embed(title="📊 LABORATORY TELEMETRY", color=0x9B59B6)
        embed.add_field(name="📡 Neural Latency", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="🌐 Linked Nodes", value=f"`{guilds}` servers", inline=True)
        embed.add_field(name="👥 Subject Count", value=f"`{users:,}` users", inline=True)
        
        # System Load Simulation (Realistic feel)
        cpu = random.randint(5, 18)
        ram = random.randint(120, 240)
        embed.add_field(name="🧠 CPU Frequency", value=f"`{cpu}%`", inline=True)
        embed.add_field(name="💾 Buffer Memory", value=f"`{ram} MB`", inline=True)
        embed.add_field(name="⚙️ Shards", value="`1 / 1`", inline=True)
        
        embed.set_footer(text="Real-time Neural Analysis")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="beta_simulation", description="BETA: Run a high-stakes mutation simulation (5x Payout or XP Debuff)")
    @app_commands.describe(bet="Amount of Influence to wager")
    @beta_only()
    async def beta_simulation(self, interaction: discord.Interaction, bet: int):
        if bet <= 0: return await interaction.response.send_message("❌ **Neural Error.** Invalid bet.", ephemeral=True)
        
        user_data = db.get_user(interaction.user.id, interaction.guild_id)
        if user_data.get("coins", 0) < bet:
            return await interaction.response.send_message("❌ **Neural Error.** Insufficient Influence.", ephemeral=True)

        await interaction.response.send_message("⚙️ **Initializing Simulation...** Analyzing mutation path...", ephemeral=True)
        await asyncio.sleep(2)

        # 25% Success chance for 5x payout
        success = random.random() < 0.25
        
        if success:
            reward = bet * 5
            db.update_user(interaction.user.id, interaction.guild_id, {"$inc": {"coins": reward}})
            embed = discord.Embed(
                title="🧬 MUTATION SUCCESSFUL",
                description=f"Neural pathways optimized. You have gained **{reward}** Hash Coins!",
                color=0x2ecc71
            )
            await interaction.edit_original_response(content=None, embed=embed)
        else:
            db.update_user(interaction.user.id, interaction.guild_id, {"$inc": {"coins": -bet}})
            # Apply 1 hour XP Debuff (simulated via DB flag)
            db.update_user(interaction.user.id, interaction.guild_id, {"$set": {"debuff_until": (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()}})
            
            embed = discord.Embed(
                title="🔥 MUTATION FAILED",
                description=f"Neural cascade failure. Lost **{bet}** coins and received a **1-HOUR XP DEBUFF**.",
                color=0xe74c3c
            )
            await interaction.edit_original_response(content=None, embed=embed)

    @app_commands.command(name="beta_airdrop", description="BETA: Call in a localized airdrop of Influence")
    @beta_only()
    async def beta_airdrop(self, interaction: discord.Interaction):
        amount = random.randint(100, 1000)
        
        embed = discord.Embed(
            title="📦 INCOMING AIRDROP",
            description=f"A laboratory airdrop is descending! Be the first to synchronize to claim **{amount}** Hash Coins.",
            color=0x9B59B6
        )
        
        class ClaimButton(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.claimed = False

            @discord.ui.button(label="SYNCHRONIZE & CLAIM", style=discord.ButtonStyle.success, emoji="⚡")
            async def claim(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if self.claimed: return
                self.claimed = True
                
                db.update_user(btn_interaction.user.id, btn_interaction.guild_id, {"$inc": {"coins": amount}})
                
                success_embed = discord.Embed(
                    title="📦 AIRDROP SECURED",
                    description=f"Subject {btn_interaction.user.mention} has claimed **{amount}** Hash Coins!",
                    color=0x2ecc71
                )
                await btn_interaction.response.edit_message(embed=success_embed, view=None)
                self.stop()

        await interaction.response.send_message("🚀 **Airdrop deployed.**", ephemeral=True)
        await interaction.channel.send(embed=embed, view=ClaimButton())

    @app_commands.command(name="beta_grant_role", description="BETA: Manually grant the Lab Rat role to authorized subjects")
    @beta_only()
    async def beta_grant_role(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name="〔 🧪 〕LABORATORY LAB RAT")
        if not role:
            return await interaction.response.send_message("❌ **Neural Error.** Lab Rat role not found. Run `/setup_elysium` first.", ephemeral=True)
        
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ **Laboratory Role Synced.** You are now officially recognized as a Laboratory Lab Rat.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BetaFeatures(bot))
