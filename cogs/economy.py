import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from utils.mongo import db
from utils.logic import get_luck_bonus, get_progress_bar, get_xp_needed, get_xp_multiplier, elite_only

class AuraSelector(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def update_aura(self, interaction: discord.Interaction, aura_key: str):
        if interaction.user.id != self.user_id: return
        db.update_user(self.user_id, interaction.guild_id, {"equipped_aura": aura_key})
        await interaction.response.edit_message(content=f"✨ **Neural Frequency Aligned.** Your aura is now: `{aura_key.upper()}`.", embed=None, view=None)

    @discord.ui.button(label="Obsidian", style=discord.ButtonStyle.secondary, emoji="🌑")
    async def obsidian(self, interaction: discord.Interaction, button: discord.ui.Button): await self.update_aura(interaction, "obsidian")
    @discord.ui.button(label="Liquid Gold", style=discord.ButtonStyle.secondary, emoji="💎")
    async def gold(self, interaction: discord.Interaction, button: discord.ui.Button): await self.update_aura(interaction, "liquid_gold")
    @discord.ui.button(label="Neon Haze", style=discord.ButtonStyle.secondary, emoji="💜")
    async def neon(self, interaction: discord.Interaction, button: discord.ui.Button): await self.update_aura(interaction, "neon_haze")
    @discord.ui.button(label="Emerald", style=discord.ButtonStyle.secondary, emoji="🌿")
    async def emerald(self, interaction: discord.Interaction, button: discord.ui.Button): await self.update_aura(interaction, "emerald")

class BlackjackView(discord.ui.View):
    def __init__(self, interaction, amount, user_data):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.amount = amount
        self.user_data = user_data
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        self.player_hand = [self.draw(), self.draw()]
        self.dealer_hand = [self.draw(), self.draw()]
        self.ended = False

    def draw(self):
        return self.deck.pop(random.randint(0, len(self.deck) - 1))

    def get_score(self, hand):
        score = sum(hand)
        if score > 21 and 11 in hand:
            hand[hand.index(11)] = 1
            return self.get_score(hand)
        return score

    def create_embed(self, title="🃏 NEURAL BLACKJACK"):
        embed = discord.Embed(title=title, color=0xFDB931)
        p_score = self.get_score(self.player_hand)
        d_score = self.get_score(self.dealer_hand)
        
        d_display = f"`{self.dealer_hand[0]}, ?`" if not self.ended else f"`{', '.join(map(str, self.dealer_hand))}` (Total: `{d_score}`)"
        embed.add_field(name="◈ DEALER", value=d_display, inline=True)
        embed.add_field(name="◈ YOU", value=f"`{', '.join(map(str, self.player_hand))}` (Total: `{p_score}`)", inline=True)
        embed.set_footer(text=f"Stake: {self.amount:,} H$")
        return embed

    @discord.ui.button(label="HIT", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id: return
        self.player_hand.append(self.draw())
        if self.get_score(self.player_hand) > 21:
            self.ended = True
            db.update_user(interaction.user.id, interaction.guild_id, {"hash_coins": self.user_data["hash_coins"] - self.amount})
            await interaction.response.edit_message(embed=self.create_embed("💥 BUSTED! You lost."), view=None)
        else:
            await interaction.response.edit_message(embed=self.create_embed())

    @discord.ui.button(label="STAND", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id: return
        self.ended = True
        while self.get_score(self.dealer_hand) < 17:
            self.dealer_hand.append(self.draw())
        
        p_score = self.get_score(self.player_hand)
        d_score = self.get_score(self.dealer_hand)
        
        if d_score > 21 or p_score > d_score:
            winnings = self.amount
            db.update_user(interaction.user.id, interaction.guild_id, {"hash_coins": self.user_data["hash_coins"] + winnings})
            await interaction.response.edit_message(embed=self.create_embed("🏆 YOU WIN!"), view=None)
        elif p_score < d_score:
            db.update_user(interaction.user.id, interaction.guild_id, {"hash_coins": self.user_data["hash_coins"] - self.amount})
            await interaction.response.edit_message(embed=self.create_embed("💀 DEALER WINS."), view=None)
        else:
            await interaction.response.edit_message(embed=self.create_embed("🌫️ PUSH. Stake returned."), view=None)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Harvest your daily Influence")
    async def daily(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        last_daily = user.get("last_daily")
        now = datetime.datetime.now(datetime.timezone.utc)
        streak = user.get("daily_streak", 0)
        if last_daily:
            if isinstance(last_daily, str): last_daily = datetime.datetime.fromisoformat(last_daily)
            if last_daily.tzinfo is None: last_daily = last_daily.replace(tzinfo=datetime.timezone.utc)
            diff = now - last_daily
            if diff.days < 1:
                rem = datetime.timedelta(days=1) - diff
                return await interaction.response.send_message(f"🌱 Haze is still growing! Wait {int(rem.seconds//3600)}h.", ephemeral=True)
            streak = streak + 1 if diff.days == 1 else 1
        else: streak = 1
        reward = int((420 + (streak * 20)) * (1 + (user.get("prestige", 0) * 0.5)))
        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + reward, "last_daily": now, "daily_streak": streak})
        await interaction.response.send_message(f"🌿 **Harvest Complete.** Secured **{reward:,} H$**!")

    @app_commands.command(name="balance", description="Check your current Influence stash")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = db.get_user(target.id, interaction.guild.id)
        await interaction.response.send_message(f"💰 **{target.name}** holds **{user.get('hash_coins', 0):,} Hash Coins**.")

    @app_commands.command(name="work", description="Cultivate the fields for Influence")
    async def work(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        last_work = user.get("last_work")
        now = datetime.datetime.now(datetime.timezone.utc)
        if last_work:
            if isinstance(last_work, str): last_work = datetime.datetime.fromisoformat(last_work)
            if last_work.tzinfo is None: last_work = last_work.replace(tzinfo=datetime.timezone.utc)
            if (now - last_work).total_seconds() < 1800: return await interaction.response.send_message("⌛ Recovering...", ephemeral=True)
        reward = int(random.randint(100, 300) * (1 + (user.get("prestige", 0) * 0.5)))
        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + reward, "last_work": now})
        await interaction.response.send_message(f"🚜 **Cultivation Complete.** Earned **{reward:,} H$**!")

    @app_commands.command(name="haze", description="Take a high-grade hit")
    async def haze(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        db.update_user(interaction.user.id, interaction.guild.id, {"puff_count": user["puff_count"] + 1})
        db.db.guilds.update_one({"guild_id": str(interaction.guild.id)}, {"$inc": {"vibe_level": 5, "total_tokes": 1}}, upsert=True)
        await interaction.response.send_message(f"🌬️ **{interaction.user.name}** is getting hazy!")

    @app_commands.command(name="puff", description="Take a quick puff")
    async def puff(self, interaction: discord.Interaction):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        db.update_user(interaction.user.id, interaction.guild.id, {"puff_count": user["puff_count"] + 1})
        db.db.guilds.update_one({"guild_id": str(interaction.guild.id)}, {"$inc": {"vibe_level": 1, "total_tokes": 1}}, upsert=True)
        await interaction.response.send_message(f"💨 **{interaction.user.name}** took a hit!")

    @app_commands.command(name="server_stats", description="View the node's collective metrics")
    async def server_stats(self, interaction: discord.Interaction):
        guild_data = db.guilds.find_one({"guild_id": str(interaction.guild_id)})
        if not guild_data: return await interaction.response.send_message("❌ No data.", ephemeral=True)
        embed = discord.Embed(title=f"📊 SECTOR METRICS: {interaction.guild.name}", color=0xFDB931)
        embed.add_field(name="☁️ Total Tokes", value=f"`{guild_data.get('total_tokes', 0):,}`")
        embed.add_field(name="✨ Vibe Level", value=f"`{guild_data.get('vibe_level', 0):,}`")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the top ranking nodes in the sector")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        top_users = db.get_leaderboard(interaction.guild_id, sort_by="hash_coins", limit=10)

        if not top_users:
            return await interaction.followup.send("❌ No economic data available for this sector.")

        desc = ""
        for i, u in enumerate(top_users):
            member = interaction.guild.get_member(int(u['user_id']))
            name = member.name if member else f"Unknown Node ({u['user_id']})"
            desc += f"**{i+1}.** `{name}` — **{u.get('hash_coins', 0):,} H$** (Tier {u.get('level', 1)})\n"

        embed = discord.Embed(
            title="🏆 SOVEREIGN LEADERBOARD",
            description=desc,
            color=0xFDB931
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="slots", description="Gamble your Influence on the reels")
    async def slots(self, interaction: discord.Interaction, amount: int):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0 or user["hash_coins"] < amount: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
        symbols = ['🍒', '🍋', '🍇', '🍉', '⭐', '🍀', '💎']
        s1, s2, s3 = [random.choice(symbols) for _ in range(3)]
        winnings = amount * 10 if s1 == s2 == s3 else (amount * 2 if s1 == s2 or s2 == s3 or s1 == s3 else -amount)
        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + winnings})
        await interaction.response.send_message(f"🎰 | {s1} | {s2} | {s3} | -> **{'Won' if winnings > 0 else 'Lost'} {abs(winnings):,} H$**")

    @app_commands.command(name="coinflip", description="Flip a coin for double or nothing")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, amount: int, choice: str):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0 or user["hash_coins"] < amount: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
        
        result = random.choice(["heads", "tails"])
        win = choice == result
        winnings = amount if win else -amount
        
        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + winnings})
        
        embed = discord.Embed(
            title="🪙 COIN FLIP",
            description=f"The coin landed on **{result.upper()}**!\n\n**{'✅ YOU WON' if win else '❌ YOU LOST'}** `{amount:,} H$`",
            color=0x2ecc71 if win else 0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll the dice against the bot")
    async def dice(self, interaction: discord.Interaction, amount: int):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0 or user["hash_coins"] < amount: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
        
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if player_roll > bot_roll:
            winnings = amount
            res = "🏆 YOU WIN!"
            color = 0x2ecc71
        elif player_roll < bot_roll:
            winnings = -amount
            res = "💀 YOU LOST."
            color = 0xe74c3c
        else:
            winnings = 0
            res = "🌫️ DRAW."
            color = 0x95a5a6

        db.update_user(interaction.user.id, interaction.guild.id, {"hash_coins": user["hash_coins"] + winnings})
        
        embed = discord.Embed(title="🎲 DICE DUEL", description=res, color=color)
        embed.add_field(name="◈ YOUR ROLL", value=f"`{player_roll}`", inline=True)
        embed.add_field(name="◈ BOT ROLL", value=f"`{bot_roll}`", inline=True)
        embed.set_footer(text=f"Balance Shift: {winnings:+,} H$")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="blackjack", description="Play a game of high-stakes blackjack")
    async def blackjack(self, interaction: discord.Interaction, amount: int):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0 or user["hash_coins"] < amount: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
        
        view = BlackjackView(interaction, amount, user)
        await interaction.response.send_message(embed=view.create_embed(), view=view)

    @app_commands.command(name="roulette", description="Bet on a color in the neural roulette")
    @app_commands.choices(color=[
        app_commands.Choice(name="🔴 Red (2x)", value="red"),
        app_commands.Choice(name="⚫ Black (2x)", value="black"),
        app_commands.Choice(name="🟢 Green (14x)", value="green")
    ])
    async def roulette(self, interaction: discord.Interaction, amount: int, color: str):
        user = db.get_user(interaction.user.id, interaction.guild.id)
        if amount <= 0 or user["hash_coins"] < amount: return await interaction.response.send_message("❌ Invalid bet.", ephemeral=True)
        
        roll = random.randint(0, 36)
        if roll == 0: result = "green"
        elif roll % 2 == 0: result = "black"
        else: result = "red"
        
        win = color == result
        if win:
            multiplier = 14 if result == "green" else 2
            winnings = amount * (multiplier - 1)
        else:
            winnings = -amount
            
        db.update_user(interaction.user.id, interaction.guild_id, {"hash_coins": user["hash_coins"] + winnings})
        
        res_text = f"The ball landed on **{result.upper()}** ({roll})!"
        embed = discord.Embed(
            title="🎡 NEURAL ROULETTE",
            description=f"{res_text}\n\n**{'✅ YOU WON' if win else '❌ YOU LOST'}** `{abs(winnings):,} H$`",
            color=0x2ecc71 if win else 0xe74c3c
        )
        await interaction.response.send_message(embed=embed)

    card_group = app_commands.Group(name="card", description="Identity: Manage your digital membership card")
    @card_group.command(name="view", description="Generate a stunning visual membership card")
    async def profile_card(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        await interaction.response.defer()
        user_data = db.get_user(target.id, interaction.guild.id)
        user_data['premium_status'] = db.is_premium(interaction.guild_id)
        from utils.images import img_gen
        image_buffer = await img_gen.generate_profile_card(target, user_data)
        await interaction.followup.send(file=discord.File(image_buffer, filename=f"card_{target.name}.png"))

    @card_group.command(name="customize", description="Align your aura")
    async def card_customize(self, interaction: discord.Interaction):
        await interaction.response.send_message("Select an aura:", view=AuraSelector(interaction.user.id), ephemeral=True)

    @app_commands.command(name="profile", description="View Haze Profile")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user = db.get_user(target.id, interaction.guild.id)
        embed = discord.Embed(title=f"🌿 {target.name}'s Profile", color=discord.Color.green())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="💰 Influence", value=f"`{user['hash_coins']:,} H$`", inline=True)
        if db.is_elite_enabled(interaction.guild_id):
            embed.add_field(name="📈 Tier", value=f"`{user.get('level', 1)}`", inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
