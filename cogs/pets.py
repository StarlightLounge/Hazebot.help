import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
import asyncio
from utils.mongo import db

class Pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cultivate", description="Initialize a Sentient Strain as your virtual pet (Requires Sentient Seed)")
    @app_commands.describe(name="The name of your sentient strain")
    async def cultivate(self, interaction: discord.Interaction, name: str):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        user_data = db.get_user(user_id, guild_id)

        if user_data.get("pet"):
            return await interaction.response.send_message("❌ **Neural Error.** You are already cultivating a sentient strain.", ephemeral=True)

        # REDO: Require a "🌱 Sentient Seed" in inventory instead of raw coins
        inv = user_data.get("inventory", [])
        if "🌱 Sentient Seed" not in inv:
            return await interaction.response.send_message("❌ **Neural Requirement.** You need a **🌱 Sentient Seed** in your stash to cultivate. Acquire one from the `/shop`.", ephemeral=True)

        # Remove the seed from inventory
        inv.remove("🌱 Sentient Seed")

        db.update_user(user_id, guild_id, {
            "pet": {
                "name": name,
                "level": 1,
                "xp": 0,
                "health": 100,
                "last_tend": None,
                "birth_date": datetime.datetime.now().isoformat()
            },
            "inventory": inv
        })

        embed = discord.Embed(
            title="🌱 SENTIENT SEED PLANTED",
            description=f"Congratulations! Your sentient strain **{name}** has been initialized in the local node.",
            color=0x2ecc71
        )
        embed.set_footer(text="Interact daily with /tend to ensure growth.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tend", description="Water and feed your sentient strain (Once every 12 hours)")
    async def tend(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        user_data = db.get_user(user_id, guild_id)
        
        pet = user_data.get("pet")
        if not pet:
            return await interaction.response.send_message("❌ You haven't initialized a sentient strain yet. Use `/cultivate`.", ephemeral=True)

        # Cooldown: 12 Hours
        last_tend = pet.get("last_tend")
        now = datetime.datetime.now()
        if last_tend:
            last_tend_dt = datetime.datetime.fromisoformat(last_tend)
            if (now - last_tend_dt).total_seconds() < 43200:
                remaining = 43200 - (now - last_tend_dt).total_seconds()
                return await interaction.response.send_message(f"⌛ **Strain Saturated.** Your pet is already synchronized. Try again in `{int(remaining//3600)}h {int((remaining%3600)//60)}m`.", ephemeral=True)

        # Growth logic
        xp_gain = random.randint(15, 30)
        new_xp = pet.get("xp", 0) + xp_gain
        new_level = pet.get("level", 1)
        
        # Level up at 100 XP
        if new_xp >= 100:
            new_xp -= 100
            new_level += 1
            await interaction.channel.send(f"🎊 **CULTIVATION ASCENSION!** {interaction.user.mention}'s pet **{pet['name']}** has reached Level `{new_level}`!")

        db.update_user(user_id, guild_id, {
            "pet.xp": new_xp,
            "pet.level": new_level,
            "pet.last_tend": now.isoformat(),
            "pet.health": min(pet.get("health", 100) + 10, 100)
        })
        
        await interaction.response.send_message(f"💧 **{pet['name']}** tended! Gained **{xp_gain} XP**. Current Status: `LV {new_level}`")

    @app_commands.command(name="pet_status", description="Check the health and standing of your sentient strain")
    async def pet_status(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = db.get_user(target.id, interaction.guild.id)
        
        pet = user_data.get("pet")
        if not pet:
            return await interaction.response.send_message(f"❌ {'You' if target == interaction.user else target.name} is not cultivating any strains.", ephemeral=True)

        embed = discord.Embed(title=f"🌿 CULTIVATION REPORT: {pet['name']}", color=0x2ecc71)
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="◈ LEVEL", value=f"`{pet['level']}`", inline=True)
        embed.add_field(name="◈ XP", value=f"`{pet['xp']}/100`", inline=True)
        embed.add_field(name="◈ VITALITY", value=f"`{pet['health']}%`", inline=True)
        
        # Benefits based on level
        bonus = pet['level'] * 0.5
        embed.add_field(name="✨ NEURAL BONUS", value=f"`+{bonus}%` Global Luck", inline=False)
        
        born = datetime.datetime.fromisoformat(pet['birth_date']).strftime("%Y-%m-%d")
        embed.set_footer(text=f"Initialized on {born} | Node Synchronization Active")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Pets(bot))
