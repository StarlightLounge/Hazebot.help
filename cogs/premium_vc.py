import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import premium_only

class PremiumVC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    vc_group = app_commands.Group(name="vc", description="Bandwidth: Manage your premium voice frequency")

    @vc_group.command(name="setup", description="Establish a Premium VC Hub for your sector")
    @app_commands.checks.has_permissions(administrator=True)
    async def vc_setup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        hub = await interaction.guild.create_voice_channel("➕ Create Frequency")
        db.set_vc_hub(interaction.guild_id, hub.id)
        await interaction.followup.send(f"🛰️ **VC Hub Deployed:** {hub.mention}")

    @vc_group.command(name="name", description="PREMIUM: Rename your current voice frequency")
    @premium_only()
    async def vc_name(self, interaction: discord.Interaction, name: str):
        if not interaction.user.voice: return await interaction.response.send_message("❌ Join VC.", ephemeral=True)
        await interaction.user.voice.channel.edit(name=name)
        await interaction.response.send_message(f"✅ Frequency renamed: `{name}`", ephemeral=True)

    @vc_group.command(name="lock", description="PREMIUM: Lock or unlock your current voice frequency")
    @premium_only()
    async def vc_lock(self, interaction: discord.Interaction, status: bool):
        if not interaction.user.voice: return await interaction.response.send_message("❌ Join VC.", ephemeral=True)
        await interaction.user.voice.channel.set_permissions(interaction.guild.default_role, connect=not status)
        await interaction.response.send_message(f"✅ Frequency `{'LOCKED' if status else 'UNLOCKED'}`", ephemeral=True)

    @vc_group.command(name="limit", description="PREMIUM: Set a member limit for your current voice frequency")
    @premium_only()
    async def vc_limit(self, interaction: discord.Interaction, limit: int):
        if not interaction.user.voice: return await interaction.response.send_message("❌ Join VC.", ephemeral=True)
        await interaction.user.voice.channel.edit(user_limit=limit)
        await interaction.response.send_message(f"✅ Limit set to `{limit}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PremiumVC(bot))
