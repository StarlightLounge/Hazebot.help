import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
import asyncio
import datetime
from utils.mongo import db

class Expeditions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="expedition", description="Initialize an expedition into the void for rare loot and influence")
    @app_commands.describe(duration="Length of expedition (minutes: 15, 30, or 60)")
    @app_commands.choices(duration=[
        app_commands.Choice(name="15 Minutes (Short Scout)", value=15),
        app_commands.Choice(name="30 Minutes (Deep Probe)", value=30),
        app_commands.Choice(name="60 Minutes (Elite Harvest)", value=60)
    ])
    async def expedition(self, interaction: discord.Interaction, duration: int):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        user_data = db.get_user(user_id, guild_id)
        
        # Check if already on expedition
        on_exp = user_data.get("expedition_until")
        if on_exp:
            end_time = datetime.datetime.fromisoformat(on_exp)
            if datetime.datetime.now() < end_time:
                remaining = round((end_time - datetime.datetime.now()).total_seconds() / 60)
                return await interaction.response.send_message(f"❌ **Subject Busy.** You are currently on an expedition for another `{remaining}` minutes.", ephemeral=True)

        await interaction.response.defer()
        
        finish_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
        db.update_user(user_id, guild_id, {"$set": {"expedition_until": finish_time.isoformat(), "expedition_type": duration}})
        
        embed = discord.Embed(
            title="🌌 EXPEDITION INITIALIZED",
            description=f"Your avatar has departed for a **{duration}-minute** probe into the uncharted void.",
            color=0x3498db
        )
        embed.add_field(name="◈ ESTIMATED RETURN", value=f"<t:{int(finish_time.timestamp())}:R>", inline=True)
        embed.add_field(name="◈ STATUS", value="`IN TRANSIT`", inline=True)
        embed.set_footer(text="Haze Bot Expedition Protocol")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="return", description="Recall your avatar and claim expedition rewards (If complete)")
    async def return_exp(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        user_data = db.get_user(user_id, guild_id)
        
        on_exp = user_data.get("expedition_until")
        if not on_exp:
            return await interaction.response.send_message("❌ **Neural Error.** No active expedition detected.", ephemeral=True)
            
        end_time = datetime.datetime.fromisoformat(on_exp)
        if datetime.datetime.now() < end_time:
            remaining = round((end_time - datetime.datetime.now()).total_seconds() / 60)
            return await interaction.response.send_message(f"⌛ **Expedition in progress.** Avatar returns in `{remaining}` minutes.", ephemeral=True)

        # Calculate Rewards
        duration = user_data.get("expedition_type", 15)
        base_coins = duration * random.randint(10, 30)
        base_xp = duration * random.randint(5, 15)
        
        # Chance for items
        found_item = None
        if random.random() < (duration / 100):
            items = ["Rare Seed", "Neural Link", "High Grade Fertilizer", "Elite Blueprint"]
            found_item = random.choice(items)
            # Add to inventory logic placeholder (if db supports it)
            db.update_user(user_id, guild_id, {"$push": {"inventory": found_item}})

        db.update_user(user_id, guild_id, {"$set": {"expedition_until": None}, "$inc": {"coins": base_coins, "xp": base_xp}})
        
        embed = discord.Embed(title="🌌 EXPEDITION SUCCESSFUL", color=0x2ecc71)
        embed.add_field(name="💰 Influence Harvested", value=f"`{base_coins}`", inline=True)
        embed.add_field(name="✨ XP Synchronized", value=f"`{base_xp}`", inline=True)
        if found_item:
            embed.add_field(name="📦 Rare Discovery", value=f"`{found_item}`", inline=False)
            
        embed.set_footer(text="Avatar has returned to the local node.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bounties", description="View active daily bounties for massive rewards")
    async def bounties(self, interaction: discord.Interaction):
        # Semi-randomized daily bounties
        embed = discord.Embed(title="🎯 DAILY BOUNTY MANIFESTO", color=0xe67e22)
        embed.description = "Complete these synchronization tasks for bonus Influence and XP."
        
        embed.add_field(name="◈ THE HARVESTER", value="Complete 3 `/work` cycles.\nReward: `500 Coins`", inline=False)
        embed.add_field(name="◈ HIGH ROLLER", value="Win a `/slots` bet over 100.\nReward: `1000 XP`", inline=False)
        embed.add_field(name="◈ VOID STALKER", value="Catch a strain in `/explore`.\nReward: `250 Coins`", inline=False)
        
        embed.set_footer(text="Resets every 24 hours.")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Expeditions(bot))
