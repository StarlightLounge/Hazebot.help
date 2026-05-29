import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import elite_only

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        elite_enabled = db.is_elite_enabled(interaction.guild_id)
        
        embed = discord.Embed(
            title="🍃 Haze Bot: Sovereign HUD" if elite_enabled else "🍃 Haze Bot: Command Registry",
            description="Access your neural protocols below:" if elite_enabled else "List of available stoner commands:",
            color=discord.Color.green()
        )

        economy = (
            "• `/balance` - Check your Influence stash\n"
            "• `/daily` - Harvest daily rewards (24h)\n"
            "• `/work` - Cultivate for coins (30m)\n"
            "• `/haze` - High-grade hit (2m)\n"
            "• `/puff` - Traditional hit (30s)\n"
            "• `/profile` - View stats & gear\n"
            "• `/give` - Transfer Influence"
        )
        
        # Only show leveling in help if enabled
        if elite_enabled:
            economy += "\n• `/level` - View Tier progress"

        gambling = (
            "• `/slots` - High-stakes reels\n"
            "• `/coinflip` - Double or nothing\n"
            "• `/blackjack` - Beat the Dealer\n"
            "• `/roulette` - Bet on destiny\n"
            "• `/high_stakes_haze` - Card battle"
        )
        hazedex = (
            "• `/explore` - Locate wild smoke & strains\n"
            "• `/catch` - Secure active spawn\n"
            "• `/hazedex` - View your collection\n"
            "• `/all_strains` - Master list of gear\n"
            "• `/smoke_off` - Battle others\n"
            "• `/trade_smoke` - Swap items"
        )
        
        staff = (
            "• `/purge` - Remove message spam\n"
            "• `/kick` / `/ban` - Subject isolation\n"
            "• `/add_role` / `/remove_role` - Frequency control\n"
            "• `/toggle_elite` - Toggle Elite Mode"
        )
        
        if elite_enabled:
            staff += (
                "\n• `/set_level` - Assign subject Tier\n"
                "• `/add_xp` - Inject neural growth\n"
                "• `/set_balance` - Adjust coin stash\n"
                "• `/setup_elysium` - Rebuild infrastructure"
            )

        embed.add_field(name="🌿 Economy & Growth", value=economy, inline=False)
        embed.add_field(name="🎰 Risk & Reward", value=gambling, inline=False)
        embed.add_field(name="📖 HazeDex Collection", value=hazedex, inline=False)
        
        if interaction.user.guild_permissions.administrator:
            embed.add_field(name="⚖️ Sovereign Control (Staff)", value=staff, inline=False)
        
        status = "ELITE MODE ACTIVE" if elite_enabled else "STANDARD MODE"
        embed.set_footer(text=f"Elite Elysium Protocol | System Status: {status}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong! Latency: `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command(name="elysium_intel", description="Access the singularity's core metadata")
    @elite_only()
    async def elysium_intel(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title="🛰️ ELYSIUM INTELLIGENCE REPORT",
            description=f"Neural network diagnostics for **{guild.name}**",
            color=0x2ecc71
        )
        
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        
        # Core Stats
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        embed.add_field(name="📡 Connectivity", value=f"• Total Nodes: `{guild.member_count}`\n• Online/Active: `{online}`", inline=True)
        
        # Security & Prestige
        boosts = guild.premium_subscription_count
        tier = guild.premium_tier
        embed.add_field(name="🛡️ Security Level", value=f"• Boosts: `{boosts}`\n• Tier: `{tier}`", inline=True)
        
        # Technical Data
        created = guild.created_at.strftime("%Y-%m-%d")
        owner = guild.owner.name if guild.owner else "Unknown"
        embed.add_field(name="⚙️ System Specs", value=f"• Initialization: `{created}`\n• Principal Architect: `{owner}`\n• Protocol Version: `2.6.5-PRO`", inline=False)
        
        embed.set_footer(text="Singularity Status: STABLE")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
