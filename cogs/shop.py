import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db

class BoutiqueView(discord.ui.View):
    def __init__(self, shop_cog):
        super().__init__(timeout=60)
        self.shop = shop_cog

    def create_category_embed(self, cat_name):
        items = self.shop.categories.get(cat_name, {})
        embed = discord.Embed(
            title=f"🛍️ BOUTIQUE: {cat_name.upper()}",
            description="Acquire high-end assets to synchronize with your neural core.",
            color=0x2ecc71
        )
        
        item_list = ""
        for k, v in items.items():
            item_list += f"◈ **{v['name']}** — `{v['price']:,} H$`\n*{v['desc']}*\n\n"
        
        embed.add_field(name="AVAILABILITY", value=item_list if item_list else "*No items detected in this sector.*", inline=False)
        embed.set_footer(text="Use /buy [item_name] to acquire.")
        return embed

    @discord.ui.button(label="Consumables", style=discord.ButtonStyle.secondary, emoji="🚬")
    async def consumables(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.create_category_embed("Consumables"))

    @discord.ui.button(label="Equipment", style=discord.ButtonStyle.secondary, emoji="🫧")
    async def equipment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.create_category_embed("Equipment"))

    @discord.ui.button(label="Cultivation", style=discord.ButtonStyle.secondary, emoji="🌱")
    async def cultivation(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.create_category_embed("Cultivation"))

    @discord.ui.button(label="Elite Assets", style=discord.ButtonStyle.secondary, emoji="💎")
    async def elite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.create_category_embed("Elite Assets"))

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Grouped by category for better organization
        self.categories = {
            "Consumables": {
                "raw_cone": {"name": "🚬 Raw Classic Cone", "price": 100, "desc": "A basic necessity for any subject. (Cosmetic)"},
                "blazy_susan": {"name": "🎀 Blazy Susan Pink Cone", "price": 250, "desc": "High-fidelity pink papers. (Cosmetic)"},
                "filter_tips": {"name": "🧩 Pure-Flo Filter Tips", "price": 50, "desc": "Surgical filtration for a smoother experience. (Cosmetic)"},
                "wick_lighter": {"name": "🔥 Hemp Wick Lighter", "price": 500, "desc": "Clean ignition for pure frequencies. (Cosmetic)"}
            },
            "Equipment": {
                "glass_chillum": {"name": "🪵 Glass One-Hitter", "price": 1500, "desc": "Efficient neural delivery. (Cosmetic)"},
                "silicon_bong": {"name": "🫧 Silicon Travel Bong", "price": 3500, "desc": "Indestructible glassware for expeditions. (Cosmetic)"},
                "erig": {"name": "📱 Smart E-Rig", "price": 12500, "desc": "Digital temperature control for perfect synchronization. (Cosmetic)"},
                "golden_grinder": {"name": "✨ Golden Grinder", "price": 10000, "desc": "Enhances neural harvest: **+200 Influence** to all daily collections."},
                "volcano_vape": {"name": "🌋 The Volcano", "price": 50000, "desc": "Legendary vaporizer. Grants a **Permanent 1.2x Luck Bonus** in HazeDex catches."}
            },
            "Cultivation": {
                "sentient_seed": {"name": "🌱 Sentient Seed", "price": 1000, "desc": "Required to initialize a **Sentient Strain** virtual pet. (/cultivate)"},
                "high_grade_fertilizer": {"name": "🧪 Neural Fertilizer", "price": 2500, "desc": "Boosts your sentient strain's growth speed. (Single Use)"}
            },
            "Elite Assets": {
                "og_kush_badge": {"name": "🌿 OG Kush Badge", "price": 15000, "desc": "Neural identification for elite cultivators. (Status)"},
                "diamond_pipe": {"name": "💎 Diamond Pipe", "price": 75000, "desc": "The ultimate luxury asset for high-frequency subjects. (Ultimate Status)"},
                "void_vapor": {"name": "🌀 Void Vapor Signature", "price": 150000, "desc": "A Mythic-tier smoke signature. Purely for the most elite nodes."},
                "eternal_ember": {"name": "🔥 The Eternal Ember", "price": 250000, "desc": "The ultimate source of heat. Grants a **Permanent 2x Luck Bonus** in HazeDex catches. (God-Tier)"}
            }
        }
        
        # Flattened for internal logic
        self.items = {}
        for cat in self.categories.values():
            self.items.update(cat)

    @app_commands.command(name="shop", description="Browse the Boutique for high-fidelity stoner assets")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛍️ THE SOVEREIGN BOUTIQUE",
            description="Select a category below to browse the singularity's offerings.",
            color=0x2ecc71
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, view=BoutiqueView(self))

    @app_commands.command(name="buy", description="Acquire a high-end asset from the Boutique")
    @app_commands.describe(item="The name of the asset to acquire")
    async def buy(self, interaction: discord.Interaction, item: str):
        found_details = None
        # Try direct key match or fuzzy search in names
        item_key = item.lower().replace(" ", "_")
        if item_key in self.items:
            found_details = self.items[item_key]
        else:
            for k, v in self.items.items():
                if item.lower() in v["name"].lower():
                    found_details = v
                    break

        if not found_details:
            return await interaction.response.send_message("❌ **Neural Error.** Asset not identified in Boutique records.", ephemeral=True)
            
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if user["hash_coins"] < found_details["price"]:
            return await interaction.response.send_message(f"❌ **Transaction Denied.** Insufficient Influence. Needed: `{found_details['price']:,} H$`", ephemeral=True)
            
        inv = user.get("inventory", [])
        uniques = ["✨ Golden Grinder", "🌋 The Volcano", "🌿 OG Kush Badge", "💎 Diamond Pipe", "🌀 Void Vapor Signature", "🔥 The Eternal Ember"]
        if found_details["name"] in inv and found_details["name"] in uniques:
            return await interaction.response.send_message("❌ **Neural Conflict.** This unique asset is already registered in your stash.", ephemeral=True)

        inv.append(found_details["name"])
        db.update_user(interaction.user.id, interaction.guild.id, {
            "hash_coins": user["hash_coins"] - found_details["price"],
            "inventory": inv
        })
        
        embed = discord.Embed(
            title="✅ TRANSACTION AUTHORIZED",
            description=f"Successfully acquired: **{found_details['name']}**\nInfluence deducted: `{found_details['price']:,} H$`",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="Inspect your current stash and secured assets")
    async def inventory(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        inv = user.get("inventory", [])
        from collections import Counter
        item_counts = Counter(inv)
        inv_list = "\n".join([f"• **{item}** {'x' + str(count) if count > 1 else ''}" for item, count in item_counts.items()])

        embed = discord.Embed(
            title="🎒 NEURAL STASH",
            description=f"Synchronized Assets: **{len(inv)}**\n\n" + (inv_list if inv_list else "*Your stash is currently empty.*"),
            color=0x3498db
        )
        embed.set_footer(text=f"Influence Balance: {user['hash_coins']:,} H$")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Shop(bot))
