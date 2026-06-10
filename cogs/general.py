import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import elite_only
import datetime
import asyncio

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if message.author.id in self.afk_users:
            del self.afk_users[message.author.id]
            await message.channel.send(f"👋 Welcome back {message.author.mention}, your AFK is cleared.", delete_after=5)
        for mention in message.mentions:
            if mention.id in self.afk_users:
                await message.channel.send(f"💤 **{mention.name} is AFK:** {self.afk_users[mention.id]}", delete_after=10)

    @app_commands.command(name="afk", description="Set AFK status")
    async def afk(self, interaction: discord.Interaction, status: str = "Away"):
        self.afk_users[interaction.user.id] = status
        await interaction.response.send_message(f"💤 AFK Set: {status}", ephemeral=True)

    @app_commands.command(name="remindme", description="Set a neural reminder")
    @app_commands.describe(minutes="Minutes to wait", message="What to remind you about")
    async def remindme(self, interaction: discord.Interaction, minutes: int, message: str):
        if minutes <= 0: return await interaction.response.send_message("❌ Minutes must be positive.", ephemeral=True)
        await interaction.response.send_message(f"⏰ **Reminder Set.** I'll ping you in `{minutes}` minutes.", ephemeral=True)
        await asyncio.sleep(minutes * 60)
        try:
            await interaction.user.send(f"⏰ **NEURAL REMINDER:** {message}")
        except:
            await interaction.channel.send(f"{interaction.user.mention} ⏰ **NEURAL REMINDER:** {message}")

    @app_commands.command(name="quote", description="Archive a legendary quote from a subject")
    @app_commands.describe(user="The subject who said it", quote="The legendary words")
    async def quote(self, interaction: discord.Interaction, user: discord.Member, quote: str):
        embed = discord.Embed(description=f"*{quote}*", color=0xFDB931)
        embed.set_author(name=user.name, icon_url=user.display_avatar.url)
        embed.set_footer(text=f"Archived by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Show command protocols")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🍃 Haze Bot: Registry", color=discord.Color.green())
        embed.add_field(name="🌿 Economy", value="`/daily`, `/balance`, `/work`, `/slots`, `/profile`, `/server_stats`", inline=False)
        embed.add_field(name="🎉 Social/RPG", value="`/poll`, `/giveaway`, `/afk`, `/hazedex explore`, `/expedition`", inline=False)
        embed.add_field(name="🔊 Music", value="`/play`, `/queue`, `/skip`, `/leave`, `/hud`", inline=False)
        if interaction.user.guild_permissions.manage_messages:
            embed.add_field(name="⚖️ Admin", value="`/purge`, `/kick`, `/ban`, `/server_info`, `/setup_stats`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server_info", description="View server metadata")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"🛰️ SECTOR REPORT: {guild.name}", color=0x2ecc71)
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Nodes", value=f"`{guild.member_count}`", inline=True)
        embed.add_field(name="Security", value=f"Tier `{guild.premium_tier}`", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="user_info", description="View user dossier")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        embed = discord.Embed(title="👤 SUBJECT DOSSIER", color=target.color)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Identity", value=f"`{target.name}`", inline=True)
        embed.add_field(name="Joined", value=f"`{target.joined_at.strftime('%Y-%m-%d')}`", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Neural link latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Latency: `{round(self.bot.latency * 1000)}ms`", ephemeral=True)

    @app_commands.command(name="generate_icon", description="Neural Synthesis: Create a custom high-end profile picture for this sector")
    @app_commands.choices(theme=[
        app_commands.Choice(name="Obsidian (Dark/Gold)", value="obsidian"),
        app_commands.Choice(name="Liquid Gold (Yellow/White)", value="liquid_gold"),
        app_commands.Choice(name="Neon Haze (Purple/Cyan)", value="neon_haze"),
        app_commands.Choice(name="Emerald (Green/Silver)", value="emerald")
    ])
    async def generate_icon(self, interaction: discord.Interaction, theme: str = "obsidian"):
        await interaction.response.defer()
        from utils.images import img_gen
        image_buffer = await img_gen.generate_server_icon(interaction.guild, theme)
        await interaction.followup.send(content="✨ **Neural Synthesis Complete.** Your custom sector icon has been finalized.", file=discord.File(image_buffer, filename=f"icon_{interaction.guild.name.replace(' ', '_')}.png"))

    @app_commands.command(name="generate_banner", description="Neural Synthesis: Create a custom high-end banner for this sector")
    @app_commands.choices(theme=[
        app_commands.Choice(name="Obsidian (Dark/Gold)", value="obsidian"),
        app_commands.Choice(name="Liquid Gold (Yellow/White)", value="liquid_gold"),
        app_commands.Choice(name="Neon Haze (Purple/Cyan)", value="neon_haze"),
        app_commands.Choice(name="Emerald (Green/Silver)", value="emerald")
    ])
    async def generate_banner(self, interaction: discord.Interaction, theme: str = "obsidian"):
        await interaction.response.defer()
        from utils.images import img_gen
        image_buffer = await img_gen.generate_server_banner(interaction.guild, theme)
        await interaction.followup.send(content="✨ **Neural Synthesis Complete.** Your custom sector asset has been finalized.", file=discord.File(image_buffer, filename=f"banner_{interaction.guild.name.replace(' ', '_')}.png"))

    @app_commands.command(name="invite", description="Bot invite link")
    async def invite(self, interaction: discord.Interaction):
        url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&integration_type=0&scope=bot"
        await interaction.response.send_message(f"🛰️ **BOT INTEGRATION:** [Authorize]({url})", ephemeral=True)

    @app_commands.command(name="premium_status", description="Intelligence: View the current node's Elite Premium benefits")
    async def premium_status(self, interaction: discord.Interaction):
        is_premium = db.is_premium(interaction.guild_id)
        
        embed = discord.Embed(
            title="💎 ELITE PREMIUM STATUS",
            description=f"Neural Synchronization: **{'🟢 ACTIVE' if is_premium else '🔴 INACTIVE'}**",
            color=0xFDB931 if is_premium else 0x95a5a6
        )
        
        benefits = (
            "◈ **High-Fidelity Audio:** 192kbps frequency streaming\n"
            "◈ **Neural Snapshots:** `/backup` and `/restore` architecture\n"
            "◈ **Advanced Moderation:** Surgical `/nuke` protocols\n"
            "◈ **Economic Boost:** 2x Daily Rewards & Half Cooldowns\n"
            "◈ **Exclusive ID:** Premium visual Membership Cards"
        )
        
        embed.add_field(name="◈ ELITE BENEFITS", value=benefits, inline=False)
        
        if not is_premium:
            embed.set_footer(text="Contact the High Architect to upgrade this sector.")
        else:
            embed.set_footer(text="Thank you for supporting the Elysium network.")
            
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(General(bot))
