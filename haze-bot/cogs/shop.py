import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.items = {
            "golden_grinder": {"name": "✨ Golden Grinder", "price": 5000, "desc": "Enhances neural harvest: +200 Influence to all daily collections."},
            "premium_papers": {"name": "📜 Premium Papers", "price": 1000, "desc": "Sovereign-grade papers. (High-status cosmetic)"},
            "og_kush_badge": {"name": "🌿 OG Kush Badge", "price": 10000, "desc": "Neural identification for elite cultivators. (Status)"},
            "diamond_pipe": {"name": "💎 Diamond Pipe", "price": 25000, "desc": "The ultimate luxury asset for high-frequency subjects."}
        }

    @app_commands.command(name="shop", description="Browse the Boutique for seeds, fertilizers, and rare assets")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛍️ THE BOUTIQUE: SOVEREIGN ASSETS",
            description="Acquire high-end neural equipment to enhance your status in the Singularity.",
            color=0x2ecc71
        )
        
        for k, v in self.items.items():
            embed.add_field(
                name=f"{v['name']} — `{v['price']:,} H$`", 
                value=f"◈ {v['desc']}", 
                inline=False
            )
            
        embed.set_footer(text="Influence transactions are final.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Acquire a high-end asset from the Boutique")
    @app_commands.describe(item="The name of the asset to acquire")
    async def buy(self, interaction: discord.Interaction, item: str):
        item_key = item.lower().replace(" ", "_")
        if item_key not in self.items:
            # Try fuzzy matching
            found_key = next((k for k in self.items.keys() if item.lower() in k.replace("_", " ")), None)
            if found_key: item_key = found_key
            else: return await interaction.response.send_message("❌ **Neural Error.** Asset not identified in Boutique records.", ephemeral=True)
            
        user = db.get_user(interaction.user.id, interaction.guild.id)
        details = self.items[item_key]
        
        if user["hash_coins"] < details["price"]:
            return await interaction.response.send_message(f"❌ **Transaction Denied.** Insufficient Influence. Needed: `{details['price']:,} H$`", ephemeral=True)
            
        inv = user.get("inventory", [])
        if details["name"] in inv:
            return await interaction.response.send_message("❌ **Neural Conflict.** Asset already registered in your neural core.", ephemeral=True)

        inv.append(details["name"])
        db.update_user(interaction.user.id, interaction.guild.id, {
            "hash_coins": user["hash_coins"] - details["price"],
            "inventory": inv
        })
        
        await interaction.response.send_message(f"✅ **Transaction Authorized.** `{details['name']}` has been synchronized with your stash.")

    @app_commands.command(name="use", description="Utilize an asset from your inventory")
    async def use(self, interaction: discord.Interaction, item: str):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        inv = user.get("inventory", [])
        
        # Fuzzy matching
        item_name = next((i for i in inv if item.lower() in i.lower()), None)
        
        if not item_name:
            return await interaction.response.send_message("❌ **Neural Error.** Asset not found in your stash.", ephemeral=True)
            
        await interaction.response.send_message(f"✨ **Asset Activated.** You are currently utilizing `{item_name}`. The vibe intensifies.")

    @app_commands.command(name="inventory", description="Inspect your current stash and assets")
    async def inventory(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        inv = user.get("inventory", [])
        
        embed = discord.Embed(
            title="🎒 NEURAL STASH",
            description=f"Status: **{len(inv)}** Assets Synchronized\n\n" + ("\n".join([f"• {i}" for i in inv]) if inv else "*Your stash is currently empty.*"),
            color=0x3498db
        )
        embed.set_footer(text=f"Total Influence: {user['hash_coins']:,} H$")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Shop(bot))
