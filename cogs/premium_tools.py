import discord
from discord.ext import commands
from discord import app_commands
from utils.logic import premium_only, staff_or_owner
from utils.mongo import db

class PremiumTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    premium_group = app_commands.Group(name="premium", description="Elite Premium: Advanced community features")

    @premium_group.command(name="custom_embed", description="PREMIUM: Deploy a high-fidelity custom embed")
    @app_commands.describe(title="Embed Title", description="Embed Description", color="Hex Color (e.g. FDB931)", image_url="Optional Image URL")
    @staff_or_owner("manage_messages")
    @premium_only()
    async def custom_embed(self, interaction: discord.Interaction, title: str, description: str, color: str = "00FFCC", image_url: str = None):
        try:
            color_int = int(color.replace("#", ""), 16)
        except:
            color_int = 0x00FFCC

        embed = discord.Embed(
            title=title,
            description=description.replace("\\n", "\n"),
            color=color_int
        )
        if image_url:
            embed.set_image(url=image_url)
            
        embed.set_footer(text=f"Elite Premium | {interaction.guild.name}")
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ **Custom Embed Dispatched.**", ephemeral=True)

    @premium_group.command(name="haze_bomb", description="PREMIUM: Airdrop massive Influence to all active Voice Channel nodes")
    @app_commands.describe(amount="Influence to drop per user (Max 5000)")
    @staff_or_owner("administrator")
    @premium_only()
    async def haze_bomb(self, interaction: discord.Interaction, amount: int):
        if amount > 5000:
            return await interaction.response.send_message("❌ **Neural Error.** Maximum airdrop per node is 5000 H$.", ephemeral=True)
            
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ **Neural Error.** You must be in a Voice Channel to initiate a Haze Bomb.", ephemeral=True)

        vc = interaction.user.voice.channel
        members = [m for m in vc.members if not m.bot]
        
        if not members:
            return await interaction.response.send_message("❌ **Neural Error.** No valid subjects found in this frequency.", ephemeral=True)

        await interaction.response.defer(ephemeral=False)

        count = 0
        for m in members:
            user = db.get_user(m.id, interaction.guild.id)
            db.update_user(m.id, interaction.guild.id, {"hash_coins": user.get("hash_coins", 0) + amount})
            count += 1

        embed = discord.Embed(
            title="💣 NEURAL HAZE BOMB DEPLOYED",
            description=f"**{interaction.user.name}** just dropped a massive **{amount:,} H$** payload on `{vc.name}`!",
            color=0x2ecc71
        )
        embed.add_field(name="◈ SUBJECTS SYNCHRONIZED", value=f"`{count}` nodes", inline=True)
        embed.add_field(name="◈ TOTAL INFLUENCE", value=f"`{amount * count:,} H$`", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumTools(bot))
