import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import staff_or_owner

class Affiliates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    sponsor_group = app_commands.Group(name="sponsor", description="Commerce: Manage community sponsor transmissions")

    @sponsor_group.command(name="post", description="Authorized: Post a professional sponsor or affiliate transmission")
    @app_commands.describe(name="Sponsor Name", link="Affiliate/Sponsor Link", description="Brief summary of the offering")
    async def sponsor_post(self, interaction: discord.Interaction, name: str, link: str, description: str):
        # Permissions: Staff or Elite Connoisseur
        is_staff = interaction.user.guild_permissions.manage_messages
        is_partner = any("ELITE CONNOISSEUR" in r.name.upper() for r in interaction.user.roles)
        
        if not is_staff and not is_partner:
            return await interaction.response.send_message("❌ **Access Denied.** Only **Elite Connoisseurs** and **Staff** can post sponsors.", ephemeral=True)

        if "http" not in link:
            return await interaction.response.send_message("❌ Invalid link protocol.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        hub_id = db.get_affiliate_hub(interaction.guild_id)
        channel = interaction.guild.get_channel(int(hub_id)) if hub_id else None
        
        if not channel:
            # Fallback: Look for channels by name
            channel = discord.utils.get(interaction.guild.text_channels, name="󠇲 ┇ ◌ sponsor-hub") or \
                      discord.utils.get(interaction.guild.text_channels, name="󠇲 ┇ ◌ tomb-sponsors")

        if not channel:
            return await interaction.followup.send("❌ **Neural Error.** Affiliate Hub not found in this sector. Run `/setup` first.", ephemeral=True)

        embed = discord.Embed(
            title=f"💎 SOVEREIGN SPONSOR: {name.upper()}",
            description=f"{description}\n\n[**Access Frequency**]({link})",
            color=0xFDB931
        )
        embed.set_author(name="Authorized Transmission", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Synchronized by {interaction.user.name}")
        
        await channel.send(embed=embed)
        await interaction.followup.send(f"✅ **Transmission Dispatched.** Sponsor posted in {channel.mention}.", ephemeral=True)

    @sponsor_group.command(name="setup", description="STAFF: Establish the Sponsor Hub in this channel")
    @staff_or_owner("administrator")
    async def sponsor_setup(self, interaction: discord.Interaction):
        db.set_affiliate_hub(interaction.guild_id, interaction.channel_id)
        
        embed = discord.Embed(
            title="💎 SOVEREIGN SPONSOR HUB",
            description=(
                "Welcome to the central frequency for synchronized sponsors.\n\n"
                "**◈ PROTOCOL:** Authorized partners may use `/sponsor post` to share their links.\n"
                "**◈ VISIBILITY:** All transmissions here are community-vetted."
            ),
            color=0xFDB931
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Affiliates(bot))
