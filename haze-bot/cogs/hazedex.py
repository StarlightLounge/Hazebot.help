import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import datetime
from utils.logic import sync_member_roles, get_luck_bonus

class HazeDex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_spawns = {} # guild_id: {item, message_id, owner_id}
        self.explore_cooldowns = {} # user_id: last_explore
        self.catch_cooldowns = {} # user_id: last_failed_catch
        
        self.smoke_types = {
            "Bong": "🫧", "Rig": "🍯", "Pipe": "🪵", "Joint": "🚬", "Vape": "💨"
        }
        
        self.items = [
            {"name": "Glass Beaker Bong", "type": "Bong", "rarity": "Common"},
            {"name": "Zong Spiral Bong", "type": "Bong", "rarity": "Uncommon"},
            {"name": "Silicon Travel Bong", "type": "Bong", "rarity": "Common"},
            {"name": "Gravity Bong", "type": "Bong", "rarity": "Epic"},
            {"name": "Gas Mask Bong", "type": "Bong", "rarity": "Legendary"},
            {"name": "Ice Catcher Bong", "type": "Bong", "rarity": "Rare"},
            {"name": "Scientific Recycler Rig", "type": "Rig", "rarity": "Rare"},
            {"name": "Mini Nectar Collector", "type": "Rig", "rarity": "Uncommon"},
            {"name": "E-Rig (Smart)", "type": "Rig", "rarity": "Rare"},
            {"name": "Titanium Nail Rig", "type": "Rig", "rarity": "Uncommon"},
            {"name": "Sherlock Glass Pipe", "type": "Pipe", "rarity": "Common"},
            {"name": "Crystal Healing Pipe", "type": "Pipe", "rarity": "Rare"},
            {"name": "Wood Dugout Pipe", "type": "Pipe", "rarity": "Common"},
            {"name": "One-Hitter Chillum", "type": "Pipe", "rarity": "Common"},
            {"name": "Gold Plated Grinder", "type": "Joint", "rarity": "Epic"},
            {"name": "Raw Classic Cone", "type": "Joint", "rarity": "Common"},
            {"name": "Blazy Susan Pink Cones", "type": "Joint", "rarity": "Uncommon"},
            {"name": "24k Gold Rolling Papers", "type": "Joint", "rarity": "Epic"},
            {"name": "Pax 3 Vaporizer", "type": "Vape", "rarity": "Rare"},
            {"name": "Disposable Distillate Pen", "type": "Vape", "rarity": "Common"},
            {"name": "Storz & Bickel Volcano", "type": "Vape", "rarity": "Legendary"},
            {"name": "Purple Haze Strain", "type": "Joint", "rarity": "Rare"},
            {"name": "OG Kush Flower", "type": "Joint", "rarity": "Uncommon"},
            {"name": "Northern Lights Strain", "type": "Joint", "rarity": "Rare"},
            {"name": "White Widow Flower", "type": "Joint", "rarity": "Uncommon"},
            {"name": "Blue Dream Bud", "type": "Joint", "rarity": "Common"},
            {"name": "Girl Scout Cookies", "type": "Joint", "rarity": "Rare"},
            {"name": "Wedding Cake Strain", "type": "Joint", "rarity": "Epic"},
            {"name": "Moon Rocks (Full Potency)", "type": "Joint", "rarity": "Epic"},
            {"name": "Thai Stick (Ancient)", "type": "Joint", "rarity": "Epic"},
            {"name": "Rosin Press (Studio)", "type": "Rig", "rarity": "Legendary"},
            {"name": "Star Dive Exclusive", "type": "Rig", "rarity": "Legendary"},
            {"name": "The Null Smoke", "type": "Vape", "rarity": "Mythic"},
            {"name": "Void Vapor", "type": "Vape", "rarity": "Mythic"},
            {"name": "The Eternal Ember", "type": "Pipe", "rarity": "Mythic"}
        ]

    def get_rarity_color(self, rarity):
        colors = {
            "Common": 0x95a5a6, "Uncommon": 0x2ecc71, "Rare": 0x3498db,
            "Epic": 0x9b59b6, "Legendary": 0xe67e22, "Mythic": 0xff00ff
        }
        return colors.get(rarity, 0x34495e)

    @app_commands.command(name="explore", description="Scan the vicinity for wild smoke and strains")
    async def explore(self, interaction: discord.Interaction):
        # 30s Cooldown
        now = datetime.datetime.now(datetime.timezone.utc)
        if interaction.user.id in self.explore_cooldowns:
            diff = (now - self.explore_cooldowns[interaction.user.id]).total_seconds()
            if diff < 30:
                return await interaction.response.send_message(f"⌛ Your neural scanners are recharging. Wait **{int(30-diff)}s**.", ephemeral=True)

        if interaction.guild_id in self.active_spawns:
            return await interaction.response.send_message("📡 **Signal Jammed.** Another smoke signature is already active here.", ephemeral=True)

        await interaction.response.defer()
        self.explore_cooldowns[interaction.user.id] = now
        await asyncio.sleep(1.5)
        
        item = random.choice(self.items).copy()
        is_shiny = random.randint(1, 100) == 1
        if is_shiny:
            item["name"] = f"✨ SHINY {item['name']}"
            item["rarity"] = "Legendary" if item["rarity"] in ["Common", "Uncommon", "Rare"] else "Mythic"
        
        emoji = self.smoke_types.get(item["type"], "🌫️")
        embed = discord.Embed(
            title="🌫️ NEURAL SCAN: SMOKE DETECTED" if not is_shiny else "🌟 NEURAL SCAN: SHINY SIGNATURE!",
            description=f"**Target:** {item['name']}\n**Type:** {emoji} {item['type']}\n**Stability:** `{item['rarity']}`\n\n*Use `/catch` to attempt synchronization.*",
            color=self.get_rarity_color(item["rarity"])
        )
        if is_shiny: embed.set_author(name="Rare Frequency Detected")
        
        msg = await interaction.followup.send(embed=embed)
        self.active_spawns[interaction.guild_id] = {"item": item, "message_id": msg.id, "owner_id": interaction.user.id}
        
        # Despawn after 45s
        await asyncio.sleep(45)
        if interaction.guild_id in self.active_spawns and self.active_spawns[interaction.guild_id]["message_id"] == msg.id:
            del self.active_spawns[interaction.guild_id]
            try: await msg.edit(content="🌫️ **Signal Lost.** The smoke has dissipated.", embed=None)
            except: pass

    @app_commands.command(name="catch", description="Attempt to synchronize with the active smoke")
    async def catch(self, interaction: discord.Interaction):
        if interaction.guild_id not in self.active_spawns:
            return await interaction.response.send_message("❌ No active signals detected. Use `/explore`.", ephemeral=True)
            
        # Catch Cooldown (2 mins after failure)
        now = datetime.datetime.now(datetime.timezone.utc)
        if interaction.user.id in self.catch_cooldowns:
            diff = (now - self.catch_cooldowns[interaction.user.id]).total_seconds()
            if diff < 120:
                return await interaction.response.send_message(f"⌛ Your lungs are recovering. Try again in **{int(120-diff)}s**.", ephemeral=True)

        spawn = self.active_spawns[interaction.guild_id]
        item = spawn["item"]
        
        chances = {"Common": 95, "Uncommon": 80, "Rare": 60, "Epic": 35, "Legendary": 15, "Mythic": 5}
        chance = chances.get(item["rarity"], 50)
        
        # Add Luck Bonuses
        luck = get_luck_bonus(interaction.user)
        chance += luck
        
        # Owner bonus
        if interaction.user.id == spawn["owner_id"]: chance += 5
        
        chance = min(chance, 100)

        await interaction.response.defer()
        await asyncio.sleep(1)

        roll = random.randint(1, 100)
        if roll <= chance:
            db.add_to_hazedex(interaction.user.id, interaction.guild_id, item["name"])
            del self.active_spawns[interaction.guild_id]
            
            embed = discord.Embed(
                title="✨ SYNCHRONIZATION COMPLETE",
                description=f"Successfully secured: **{item['name']}**\nAdded to your **HazeDex** collection.",
                color=0x2ecc71
            )
            await interaction.followup.send(embed=embed)
        else:
            self.catch_cooldowns[interaction.user.id] = now
            await interaction.followup.send(f"💨 **Sync Failed.** The {item['name']} resisted your attempt. Your lungs need to recover (2m).")

    @app_commands.command(name="sesh", description="Start a group sesh for a high-rarity spawn")
    async def sesh(self, interaction: discord.Interaction):
        """Competitive group catch event."""
        if interaction.guild_id in self.active_spawns:
            return await interaction.response.send_message("Singularity is already hazy.", ephemeral=True)

        await interaction.response.send_message("🔥 **SESH INITIALIZED.** A rare cloud is forming... Everyone get ready!")
        await asyncio.sleep(5)

        item = random.choice([i for i in self.items if i["rarity"] in ["Rare", "Epic", "Legendary"]]).copy()
        
        embed = discord.Embed(
            title="🌫️ MEGA SESH SPAWN",
            description=f"A massive cloud of **{item['name']}** has appeared!\nFirst one to `/catch` wins it!",
            color=self.get_rarity_color(item["rarity"])
        )
        msg = await interaction.channel.send(embed=embed)
        self.active_spawns[interaction.guild_id] = {"item": item, "message_id": msg.id, "owner_id": 0} 

    @app_commands.command(name="smoke_off", description="Battle a subject with your HazeDex collection")
    async def smoke_off(self, interaction: discord.Interaction, opponent: discord.Member, your_item: str):
        if opponent.id == interaction.user.id: return await interaction.response.send_message("❌ Self-competition is futile.", ephemeral=True)
        if opponent.bot: return await interaction.response.send_message("❌ Machines don't breathe.", ephemeral=True)

        user_data = db.get_user(interaction.user.id, interaction.guild_id)
        opp_data = db.get_user(opponent.id, interaction.guild_id)
        
        # Precision matching
        your_item_data = next((i for i in user_data.get("hazedex", []) if your_item.lower() in i.lower()), None)
        if not your_item_data:
            return await interaction.response.send_message(f"❌ `{your_item}` not found in your collection.", ephemeral=True)
            
        if not opp_data.get("hazedex"):
            return await interaction.response.send_message(f"❌ {opponent.name} has no collection to battle with.", ephemeral=True)

        opp_item_name = random.choice(opp_data["hazedex"])
        
        def get_power(name):
            clean_name = name.replace("✨ SHINY ", "")
            item_data = next((i for i in self.items if i["name"] == clean_name), None)
            base = 10
            if item_data:
                powers = {"Common": 20, "Uncommon": 40, "Rare": 65, "Epic": 90, "Legendary": 140, "Mythic": 250}
                base = powers.get(item_data["rarity"], 10)
            
            if "✨ SHINY" in name: base = int(base * 1.5)
            return base + random.randint(1, 30)

        p1_pwr = get_power(your_item_data)
        p2_pwr = get_power(opp_item_name)
        
        embed = discord.Embed(title="🔥 NEURAL SMOKE-OFF", color=0xe74c3c)
        embed.add_field(name=f"💨 {interaction.user.name}", value=f"Item: `{your_item_data}`\nPower: `{p1_pwr}`", inline=True)
        embed.add_field(name=f"💨 {opponent.name}", value=f"Item: `{opp_item_name}`\nPower: `{p2_pwr}`", inline=True)
        
        if p1_pwr > p2_pwr:
            reward = 250
            embed.description = f"🏆 **{interaction.user.name}** dominated the session!\n**Reward:** `250 H$`"
            db.update_user(interaction.user.id, interaction.guild_id, {"hash_coins": user_data.get("hash_coins", 0) + reward})
        elif p2_pwr > p1_pwr:
            reward = 250
            embed.description = f"🏆 **{opponent.name}** dominated the session!\n**Reward:** `250 H$`"
            db.update_user(opponent.id, interaction.guild_id, {"hash_coins": opp_data.get("hash_coins", 0) + reward})
        else:
            embed.description = "🌫️ **DRAW.** The room is too thick to determine a victor."
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hazedex", description="Access your collection of smoke and strains")
    async def hazedex(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = db.get_user(target.id, interaction.guild_id)
        collection = user.get("hazedex", [])
        
        total_items = len(self.items)
        caught_count = len(set(i.replace("✨ SHINY ", "") for i in collection))
        
        embed = discord.Embed(
            title=f"📖 {target.name}'s Sovereign HazeDex",
            description=f"**Completion:** `{caught_count}/{total_items}` ({(caught_count/total_items)*100:.1f}%)",
            color=0x9b59b6
        )
        
        if collection:
            sorted_coll = {}
            for item_name in collection:
                clean_name = item_name.replace("✨ SHINY ", "")
                item_data = next((i for i in self.items if i["name"] == clean_name), None)
                if item_data:
                    t = item_data["type"]
                    if t not in sorted_coll: sorted_coll[t] = []
                    sorted_coll[t].append(f"`{item_name}`")
            
            for t, items in sorted_coll.items():
                emoji = self.smoke_types.get(t, "🌫️")
                from collections import Counter
                counts = Counter(items)
                display_items = [f"{name} x{count}" if count > 1 else name for name, count in counts.items()]
                embed.add_field(name=f"{emoji} {t}s", value="\n".join(display_items), inline=False)
        else:
            embed.description += "\n\n*No data found. Explore the singularity to begin.*"
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="all_strains", description="Access the master registry of smoke signatures")
    async def all_strains(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🌿 Master Haze Registry", color=0x27ae60)
        types = {}
        for item in self.items:
            t = item["type"]
            if t not in types: types[t] = []
            types[t].append(f"`{item['name']}` ({item['rarity']})")
            
        for t, items in types.items():
            emoji = self.smoke_types.get(t, "🌫️")
            embed.add_field(name=f"{emoji} {t}s", value="\n".join(items), inline=False)
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="trade_smoke", description="Initiate a neural swap with another subject")
    async def trade_smoke(self, interaction: discord.Interaction, target: discord.Member, your_item: str, their_item: str):
        if target.id == interaction.user.id: return await interaction.response.send_message("❌ Neural looping is prohibited.", ephemeral=True)
            
        user_data = db.get_user(interaction.user.id, interaction.guild_id)
        target_data = db.get_user(target.id, interaction.guild_id)
        
        u_item = next((i for i in user_data.get("hazedex", []) if your_item.lower() in i.lower()), None)
        t_item = next((i for i in target_data.get("hazedex", []) if their_item.lower() in i.lower()), None)
        
        if not u_item: return await interaction.response.send_message(f"❌ `{your_item}` not found in your stash.", ephemeral=True)
        if not t_item: return await interaction.response.send_message(f"❌ `{their_item}` not found in their stash.", ephemeral=True)

        embed = discord.Embed(
            title="🤝 NEURAL SWAP PROPOSAL",
            description=f"**{interaction.user.name}** offers a trade to **{target.name}**.\n\n**Giving:** `{u_item}`\n**Receiving:** `{t_item}`",
            color=0x3498db
        )
        
        class TradeView(discord.ui.View):
            def __init__(self, sender, receiver, s_item, r_item):
                super().__init__(timeout=60)
                self.sender, self.receiver = sender, receiver
                self.s_item, self.r_item = s_item, r_item
                
            @discord.ui.button(label="ACCEPT SWAP", style=discord.ButtonStyle.green)
            async def accept(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.receiver.id: return
                
                s_data = db.get_user(self.sender.id, btn_interaction.guild_id)
                r_data = db.get_user(self.receiver.id, btn_interaction.guild_id)
                if self.s_item not in s_data.get("hazedex", []) or self.r_item not in r_data.get("hazedex", []):
                    return await btn_interaction.response.send_message("❌ **SWAP FAILED.** Items no longer available.", ephemeral=True)
                
                db.remove_from_hazedex(self.sender.id, btn_interaction.guild_id, self.s_item)
                db.remove_from_hazedex(self.receiver.id, btn_interaction.guild_id, self.r_item)
                db.add_to_hazedex(self.sender.id, btn_interaction.guild_id, self.r_item)
                db.add_to_hazedex(self.receiver.id, btn_interaction.guild_id, self.s_item)
                
                await btn_interaction.response.edit_message(content=f"✅ **SWAP COMPLETE.** `{self.s_item}` and `{self.r_item}` have been exchanged.", embed=None, view=None)

            @discord.ui.button(label="ABORT", style=discord.ButtonStyle.red)
            async def decline(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.receiver.id: return
                await btn_interaction.response.edit_message(content="❌ **SWAP ABORTED.**", embed=None, view=None)

        await interaction.response.send_message(target.mention, embed=embed, view=TradeView(interaction.user, target, u_item, t_item))

async def setup(bot):
    await bot.add_cog(HazeDex(bot))
