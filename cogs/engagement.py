import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import elite_only
import datetime
import asyncio

class Engagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.categories = {
            "economy": ["daily", "work", "balance", "slots", "profile"],
            "social": ["poll", "giveaway", "afk", "remind"],
            "rpg": ["hazedex explore", "hazedex battle", "hazedex view", "hazedex registry", "synergy", "expedition", "cultivate"],
            "music": ["play", "queue", "skip", "leave", "hud"],
            "governance": ["purge", "kick", "ban", "timeout", "server lock", "server nuke"]
        }

    @app_commands.command(name="synergy", description="Check your current Daily Neural Synergy progress")
    @elite_only()
    async def synergy(self, interaction: discord.Interaction):
        user_data = db.get_user(interaction.user.id, interaction.guild_id)
        synergy = user_data.get('synergy', {'last_reset': datetime.datetime.now().date().isoformat(), 'used_categories': []})
        
        today = datetime.datetime.now().date().isoformat()
        if synergy['last_reset'] != today:
            synergy = {'last_reset': today, 'used_categories': []}

        completed = len(synergy['used_categories'])
        total = len(self.categories)
        
        embed = discord.Embed(
            title="🧬 NEURAL SYNERGY STATUS",
            description=f"Synchronize with all modules daily for a **2-hour Global XP Multiplier**.",
            color=0x00FFCC
        )
        
        from utils.logic import get_progress_bar
        embed.add_field(name="◈ PROGRESS", value=f"{get_progress_bar(completed, total)}\n`{completed}/{total}` Modules Synchronized", inline=False)
        
        modules_list = ""
        for cat in self.categories.keys():
            status = "✅" if cat in synergy['used_categories'] else "❌"
            modules_list += f"{status} **{cat.title()}**\n"
        
        embed.add_field(name="◈ CORE MODULES", value=modules_list, inline=True)
        
        if completed == total:
            embed.set_footer(text="✨ HIGH VIBE STATE ACTIVE")
        else:
            embed.set_footer(text="Sync all modules to activate Multiplier.")
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Engagement(bot))
