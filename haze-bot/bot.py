import discord
from discord.ext import commands
import os
import random
import datetime
from dotenv import load_dotenv
from utils.mongo import db
from utils.logic import sync_member_roles, get_xp_needed, get_xp_multiplier

# Load .env
load_dotenv()

class HazeBot(commands.Bot):
    def __init__(self):
        # Initialize with all intents enabled
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.xp_cooldowns = {} # user_id: last_xp_time

    async def setup_hook(self):
        # 1. Load cogs with verbose logging
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"📦 [System] Neural Module Loaded: {filename}")
                except Exception as e:
                    print(f"❌ [System] Neural Module FAILED: {filename} -> {e}")
        
        # 2. Register views
        try:
            from cogs.server_setup import RoleView
            self.add_view(RoleView())
        except: pass

        # 3. Diagnostic command check
        all_cmds = self.tree.get_commands()
        print(f"🛰️ [Tree] Commands discovered in registry: {len(all_cmds)}")
        for c in all_cmds:
            print(f"  • /{c.name}")

        # 4. Global sync
        try:
            synced = await self.tree.sync()
            print(f"🌍 [Bot] Global synchronization complete. `{len(synced)}` signals established.")
        except Exception as e:
            print(f"❌ [Bot] Global sync FAILED: {e}")

bot = HazeBot()

@bot.event
async def on_ready():
    print(f"🚀 [Bot] Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.CustomActivity(name="💨 Staying hazy & synced"))
    print("✨ [Bot] Ready!")

@bot.event
async def on_member_join(member):
    # Sovereign Concierge Vibe Check
    try:
        await member.send(
            "⚜️ **Welcome to ELITE ELYSIUM.**\n"
            "I am the **Sovereign Concierge**. Before you are granted access to the Singularity, "
            "we must perform a **Neural Vibe Check**.\n\n"
            "Please tell me: **What is your philosophy on the perfect harvest?**"
        )
        print(f"📥 [Concierge] Vibe check initiated for {member.name}")
    except Exception as e:
        print(f"❌ [Concierge] Failed to DM {member.name}: {e}")

@bot.tree.command(name="plug", description="Consult with the Sovereign Concierge")
async def plug(interaction: discord.Interaction, thought: str):
    from utils.ai import ai
    await interaction.response.defer(ephemeral=True)
    response = await ai.get_response(thought, context=f"User: {interaction.user.name}")
    await interaction.followup.send(response)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    
    # Handle DMs for Vibe Check
    if isinstance(message.channel, discord.DMChannel):
        from utils.ai import ai
        response = await ai.vibe_check(message.author.name, message.content)
        await message.channel.send(response)
        return

    # --- ELITE ELYSIUM PROTOCOLS ---
    if db.is_elite_enabled(message.guild.id):
        # XP Cooldown Check (60 seconds)
        now = datetime.datetime.now()
        user_id = message.author.id
        if user_id in bot.xp_cooldowns:
            if (now - bot.xp_cooldowns[user_id]).total_seconds() < 60:
                return await bot.process_commands(message)

        user = db.get_user(message.author.id, message.guild.id)
        
        # Apply XP Multipliers
        multiplier = get_xp_multiplier(message.author, user)
        
        # metabolic Leveling: XP gain based on message length + high vibe bonus
        base_xp = min(len(message.content) // 5 + 10, 50) # Boosted base
        random_bonus = random.randint(5, 15)
        xp_gain = int((base_xp + random_bonus) * multiplier)

        new_xp = user.get("xp", 0) + xp_gain
        current_level = user.get("level", 1)

        next_level_xp = get_xp_needed(current_level)
        update_data = {"xp": new_xp}

        if new_xp >= next_level_xp:
            new_level = current_level + 1
            update_data["level"] = new_level
            update_data["xp"] = 0
            # Milestone Rewards
            reward = 0
            if new_level % 10 == 0: # Every 10 levels
                reward = new_level * 100
                update_data["hash_coins"] = user.get("hash_coins", 0) + reward
            
            # Sync prestige roles
            await sync_member_roles(message.author, new_level)
            
            desc = f"**{message.author.name}** has ascended to **Tier {new_level}**."
            if reward > 0:
                desc += f"\n💰 **Milestone Injection:** +`{reward:,} H$`"
                
            embed = discord.Embed(
                title="✨ ASTRAL ASCENSION",
                description=desc,
                color=discord.Color.from_rgb(255, 255, 255)
            )
            await message.channel.send(embed=embed, delete_after=15)
            
        db.update_user(message.author.id, message.guild.id, update_data)
        bot.xp_cooldowns[user_id] = now
    
    await bot.process_commands(message)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "your_token_here":
        print("ERROR: Please set a valid DISCORD_TOKEN in your .env file!")
    else:
        bot.run(token)
