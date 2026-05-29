import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from utils.mongo import db
from utils.logic import get_luck_bonus, get_progress_bar, get_xp_needed, get_xp_multiplier, elite_only

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banners = {
            "neon_haze": "https://i.imgur.com/8QpY6v9.png",
            "galaxy_kush": "https://i.imgur.com/uR1D6eZ.png",
            "deep_forest": "https://i.imgur.com/2PzQ1tS.png",
            "golden_harvest": "https://i.imgur.com/7w3uVvW.png",
            "void_smoke": "https://i.imgur.com/o7xK4M0.png"
        }

    @app_commands.command(name="daily", description="Harvest your daily Influence")
    async def daily(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        
        last_daily = user.get("last_daily")
        now = datetime.datetime.now(datetime.timezone.utc)
        streak = user.get("daily_streak", 0)
        
        if last_daily:
            # Handle potential string or datetime
            if isinstance(last_daily, str):
                last_daily = datetime.datetime.fromisoformat(last_daily)
            if last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=datetime.timezone.utc)
            
            diff = now - last_daily
            if diff.days < 1:
                remaining = datetime.timedelta(days=1) - diff
                hours, remainder = divmod(remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                return await interaction.response.send_message(f"🌱 Haze is still growing! Come back in **{hours}h {minutes}m**.", ephemeral=True)
            
            # Check for streak (within 48 hours)
            if diff.days == 1:
                streak += 1
            else:
                streak = 1
        else:
            streak = 1

        reward = 420 + (streak * 20)
        
        # Shop Item: Golden Grinder (+200 Influence)
        if "✨ Golden Grinder" in user.get("inventory", []):
            reward += 200
        
        prestige_multiplier = 1 + (user.get("prestige", 0) * 0.5)
        reward = int(reward * prestige_multiplier)
        
        new_balance = user["hash_coins"] + reward
        db.update_user(interaction.user.id, interaction.guild.id, {
            "hash_coins": new_balance,
            "last_daily": now, # Store as native datetime
            "daily_streak": streak
        })
        
        embed = discord.Embed(title="🌿 Haze Harvest", description=f"You harvested **{reward:,} Influence**!\nStreak: `{streak} days`", color=discord.Color.green())
        embed.add_field(name="Current Balance", value=f"💰 `{new_balance:,} H$`")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="Check your current Influence stash")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = db.get_user(target.id, interaction.guild.id)
        bal = user.get("hash_coins", 0)
        
        embed = discord.Embed(
            description=f"💰 **{target.name}** currently holds **{bal:,} Hash Coins**.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Cultivate the fields for Influence")
    async def work(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        
        # Check cooldown (30 mins)
        last_work = user.get("last_work")
        now = datetime.datetime.now(datetime.timezone.utc)
        if last_work:
            if isinstance(last_work, str): last_work = datetime.datetime.fromisoformat(last_work)
            if last_work.tzinfo is None: last_work = last_work.replace(tzinfo=datetime.timezone.utc)
            
            diff = now - last_work
            if diff.total_seconds() < 1800:
                remaining = 1800 - diff.total_seconds()
                return await interaction.response.send_message(f"⌛ Your fields are still recovering. Try again in **{int(remaining//60)}m**.", ephemeral=True)

        reward = random.randint(100, 300)
        prestige_multiplier = 1 + (user.get("prestige", 0) * 0.5)
        reward = int(reward * prestige_multiplier)
        
        new_bal = user["hash_coins"] + reward
        db.update_user(interaction.user.id, interaction.guild.id, {
            "hash_coins": new_bal,
            "last_work": now
        })
        
        jobs = ["Trimming the canopy", "Curing the harvest", "Checking the pH", "Rolling the stock", "Polishing the glass"]
        job = random.choice(jobs)
        
        await interaction.response.send_message(f"🚜 **{job}...** You earned **{reward:,} Influence**!")

    @app_commands.command(name="haze", description="Take a high-grade hit (Cooldown: 2m)")
    async def haze(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        
        # 2m Cooldown
        last_haze = user.get("last_haze")
        now = datetime.datetime.now(datetime.timezone.utc)
        if last_haze:
            if isinstance(last_haze, str): last_haze = datetime.datetime.fromisoformat(last_haze)
            if last_haze.tzinfo is None: last_haze = last_haze.replace(tzinfo=datetime.timezone.utc)
            if (now - last_haze).total_seconds() < 120:
                return await interaction.response.send_message("🌬️ You're still too hazy! Wait a few minutes.", ephemeral=True)

        new_count = user["puff_count"] + 1
        db.update_user(interaction.user.id, interaction.guild.id, {
            "puff_count": new_count, 
            "last_haze": now
        })
        
        # Increment Global Vibe
        db.db.guilds.update_one({"guild_id": str(interaction.guild.id)}, {"$inc": {"vibe_level": 5}}, upsert=True)
        
        await interaction.response.send_message(f"🌬️ **{interaction.user.name}** is getting hazy! Total hits: `{new_count}`")

    @app_commands.command(name="puff", description="Take a quick puff (Cooldown: 30s)")
    async def puff(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        
        # 30s Cooldown
        last_puff = user.get("last_puff")
        now = datetime.datetime.now(datetime.timezone.utc)
        if last_puff:
            if isinstance(last_puff, str): last_puff = datetime.datetime.fromisoformat(last_puff)
            if last_puff.tzinfo is None: last_puff = last_puff.replace(tzinfo=datetime.timezone.utc)
            if (now - last_puff).total_seconds() < 30:
                return await interaction.response.send_message("💨 Chill out, you're puffing too fast!", ephemeral=True)

        new_count = user["puff_count"] + 1
        db.update_user(interaction.user.id, interaction.guild.id, {
            "puff_count": new_count,
            "last_puff": now
        })
        
        # Increment Global Vibe
        db.db.guilds.update_one({"guild_id": str(interaction.guild.id)}, {"$inc": {"vibe_level": 1}}, upsert=True)
        
        await interaction.response.send_message(f"💨 **{interaction.user.name}** took a hit! Total: `{new_count}`")

    @app_commands.command(name="give", description="Transfer Influence to another subject")
    async def give(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.id == interaction.user.id: return await interaction.response.send_message("❌ Cannot transfer to yourself.", ephemeral=True)
        if amount <= 0: return await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
        if member.bot: return await interaction.response.send_message("❌ Bots don't need Influence.", ephemeral=True)
            
        sender = db.get_user(interaction.user.id, interaction.guild.id)
        if sender["hash_coins"] < amount: return await interaction.response.send_message("❌ Insufficient Influence.", ephemeral=True)
            
        receiver = db.get_user(member.id, interaction.guild.id)
        
        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": sender["hash_coins"] - amount})
        db.update_user(member.id, interaction.guild.id, {"hash_coins": receiver["hash_coins"] + amount})
        
        await interaction.response.send_message(f"🤝 **{interaction.user.name}** transferred **{amount:,} Influence** to **{member.name}**.")

    # --- GAMBLING REFINEMENT ---

    @app_commands.command(name="slots", description="Gamble your Influence on the reels")
    async def slots(self, interaction: discord.Interaction, amount: int):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0: return await interaction.response.send_message("❌ Bet must be positive.", ephemeral=True)
        if user["hash_coins"] < amount: return await interaction.response.send_message("❌ Insufficient Influence.", ephemeral=True)

        symbols = ['🍒', '🍋', '🍇', '🍉', '⭐', '🍀', '💎']
        s1, s2, s3 = [random.choice(symbols) for _ in range(3)]
        
        if s1 == s2 == s3:
            multiplier = 10 if s1 == '💎' else 7 if s1 == '⭐' else 5
            winnings = amount * multiplier
            result = f"JACKPOT! ({multiplier}x)"
            color = discord.Color.gold()
        elif s1 == s2 or s2 == s3 or s1 == s3:
            winnings = amount * 2
            result = "Small Win (2x)"
            color = discord.Color.green()
        else:
            winnings = -amount
            result = "Lost"
            color = discord.Color.red()

        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + winnings})
        
        embed = discord.Embed(title=f"🎰 Slots: {result}", description=f"```\n| {s1} | {s2} | {s3} |\n```\n{'Won' if winnings > 0 else 'Lost'}: **{abs(winnings):,} Influence**", color=color)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin for double or nothing")
    @app_commands.describe(side="heads or tails", amount="Amount to bet")
    async def coinflip(self, interaction: discord.Interaction, side: str, amount: int):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        side = side.lower()
        if side not in ['heads', 'tails', 'h', 't']: return await interaction.response.send_message("❌ Choose `heads` or `tails`!", ephemeral=True)
        if amount <= 0: return await interaction.response.send_message("❌ Bet must be positive.", ephemeral=True)
        if user["hash_coins"] < amount: return await interaction.response.send_message("❌ Insufficient Influence.", ephemeral=True)

        side = 'heads' if side in ['heads', 'h'] else 'tails'
        
        # Apply Luck (Default 50/50)
        luck = get_luck_bonus(interaction.user)
        win_threshold = 50 - (luck / 2) # e.g. Staff get 50 - 12.5 = 37.5 threshold
        
        roll = random.uniform(0, 100)
        win = roll >= win_threshold
        
        # Determine the "result" to show the user
        result = side if win else ("tails" if side == "heads" else "heads")
        
        winnings = amount if win else -amount
        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + winnings})
        
        res_str = "WINNER!" if win else "LOST"
        color = discord.Color.green() if win else discord.Color.red()
        
        embed = discord.Embed(title=f"🪙 Coinflip: {res_str}", description=f"The coin landed on **{result}**!\n\n{'Won' if win else 'Lost'}: **{amount:,} Influence**", color=color)
        if luck > 0 and win:
            embed.set_footer(text=f"✨ Luck Multiplier Active (+{luck}%)")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="high_stakes_haze", description="Stoner Card Game: Draw strains to beat the Dealer's Stash")
    async def high_stakes_haze(self, interaction: discord.Interaction, amount: int):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0: return await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        if user["hash_coins"] < amount: return await interaction.response.send_message("❌ Insufficient Influence!", ephemeral=True)

        strains = [
            ("🌿 Low Grade Shake", 2), ("🍃 Mid-Grade Bud", 5), ("🔥 OG Kush", 8), 
            ("💎 Diamond Dust", 10), ("🔮 Purple Haze", 12), ("🌌 Star Dive", 15),
            ("🍄 Magic Muffin", 18), ("👑 Royal Resin", 20), ("💥 Super Nova", 25)
        ]

        player_strain = random.choice(strains)
        dealer_strain = random.choice(strains)

        # Apply Luck
        luck = get_luck_bonus(interaction.user)
        player_val = player_strain[1] + (luck / 5) # +5 for Staff, etc.

        win = player_val > dealer_strain[1]
        tie = player_val == dealer_strain[1]
        
        if win:
            winnings = amount
            res = "ULTIMATE HIGH (Win)"
            color = discord.Color.green()
        elif tie:
            winnings = 0
            res = "SMOKE SESH (Tie)"
            color = discord.Color.light_grey()
        else:
            winnings = -amount
            res = "BAD TRIP (Loss)"
            color = discord.Color.red()

        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + winnings})

        embed = discord.Embed(title=f"💨 High Stakes Haze: {res}", color=color)
        embed.add_field(name="Your Strain", value=f"{player_strain[0]}\nValue: `{player_val}` {'✨' if luck > 0 else ''}", inline=True)
        embed.add_field(name="Dealer's Stash", value=f"{dealer_strain[0]}\nValue: `{dealer_strain[1]}`", inline=True)
        embed.description = f"{'Won' if win else 'Lost' if not tie else 'Returned'}: **{abs(winnings):,} Influence**"
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="level", description="View your current Tier and Neural Progress")
    @elite_only()
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = db.get_user(target.id, interaction.guild.id)
        
        current_lv = user.get('level', 1)
        current_xp = user.get('xp', 0)
        needed_xp = get_xp_needed(current_lv)
        progress = get_progress_bar(current_xp, needed_xp, length=15)
        
        embed = discord.Embed(
            title=f"📊 Neural Standing: {target.name}",
            description=f"**Tier {current_lv}**\n{progress}\n`{current_xp:,} / {needed_xp:,} XP`",
            color=0x2ecc71
        )
        
        banner_key = user.get("banner", "neon_haze")
        banner_url = self.banners.get(banner_key, self.banners["neon_haze"])
        embed.set_image(url=banner_url)
        
        # Calculate Rank (Position on leaderboard)
        all_users = db.get_leaderboard(interaction.guild_id, sort_by="level", limit=100)
        rank = "100+"
        for i, u in enumerate(all_users, 1):
            if int(u["user_id"]) == target.id:
                rank = f"#{i}"
                break
        
        embed.set_footer(text=f"Global Rank: {rank} | Prestige: {user.get('prestige', 0)}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_banner", description="Customize your Neural Card with a Sovereign Banner")
    @app_commands.choices(banner=[
        app_commands.Choice(name="Neon Haze (Purple/Cyan)", value="neon_haze"),
        app_commands.Choice(name="Galaxy Kush (Space)", value="galaxy_kush"),
        app_commands.Choice(name="Deep Forest (Dark Green)", value="deep_forest"),
        app_commands.Choice(name="Golden Harvest (Luxury)", value="golden_harvest"),
        app_commands.Choice(name="Void Smoke (Monochrome)", value="void_smoke")
    ])
    @elite_only()
    async def set_banner(self, interaction: discord.Interaction, banner: str):
        db.update_user(interaction.user.id, interaction.guild.id, {"banner": banner})
        
        embed = discord.Embed(
            title="✅ Banner Synchronized",
            description=f"Your profile has been updated with the **{banner.replace('_', ' ').title()}** frequency.",
            color=0x2ecc71
        )
        embed.set_image(url=self.banners[banner])
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="profile", description="View your Haze Profile and Neural Stats")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = db.get_user(target.id, interaction.guild.id)
        elite_enabled = db.is_elite_enabled(interaction.guild_id)
        
        embed = discord.Embed(title=f"🌿 {target.name}'s Neural Profile" if elite_enabled else f"🌿 {target.name}'s Stash", color=discord.Color.green())
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="💰 Influence", value=f"`{user['hash_coins']:,} H$`", inline=True)
        embed.add_field(name="💨 Puffs", value=f"`{user['puff_count']:,}`", inline=True)
        
        if elite_enabled:
            current_lv = user.get('level', 1)
            current_xp = user.get('xp', 0)
            needed_xp = get_xp_needed(current_lv)
            progress = get_progress_bar(current_xp, needed_xp)
            multiplier = get_xp_multiplier(target, user)
            
            embed.add_field(name="📈 Tier", value=f"`{current_lv}` (Prestige: `{user.get('prestige', 0)}`)", inline=True)
            embed.add_field(name="🧠 Neural Growth", value=f"{progress}\nXP: `{current_xp:,} / {needed_xp:,}`\nMultiplier: `{multiplier}x`", inline=False)
        
        inv = user.get("inventory", [])
        inv_str = "\n".join([f"• {i}" for i in inv]) if inv else "*No items in stash.*"
        embed.add_field(name="🎒 Stash", value=inv_str, inline=False)
        
        if elite_enabled:
            banner_key = user.get("banner", "neon_haze")
            banner_url = self.banners.get(banner_key, self.banners["neon_haze"])
            embed.set_image(url=banner_url)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
