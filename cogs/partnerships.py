import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import staff_or_owner
import datetime
import os

class PartnerRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Notify Me: Partnerships", style=discord.ButtonStyle.secondary, custom_id="notify_partners", emoji="🤝")
    async def notify_partners(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Partnership Pings")
        if not role:
            # Create if it doesn't exist
            try:
                role = await interaction.guild.create_role(name="Partnership Pings", color=0x00FFCC, mentionable=True)
            except:
                return await interaction.response.send_message("❌ Cannot manage roles in this sector.", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("🌬️ You will no longer receive alliance notifications.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✨ You are now synchronized with the **Sovereign Alliance** news frequency.", ephemeral=True)

class PartnershipView(discord.ui.View):
    def __init__(self, applicant_guild_id, invite, description, bot):
        super().__init__(timeout=None)
        self.applicant_guild_id = applicant_guild_id
        self.invite = invite
        self.description = description
        self.bot = bot

    @discord.ui.button(label="Approve Alliance", style=discord.ButtonStyle.success, custom_id="approve_partner")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Determine if user is staff (Arbiters, Overseers, Keepers, Owners)
        is_staff = any(r.name in ["「 ⟡ 」THE HIGH ARCHITECT", "「 ⚖️ 」THE CHRONIC ARBITER", "「 💀 」THE CRYPT KEEPER", "「 🔮 」KUSH NECROMANCER", "「 🌿 」THE HIGH MASTER", "「 🖤 」AFTERDARK OVERSEER", "「 ⚖️ 」SUPPORT LEAD", "「 💻 」HAZE DEVELOPER", "「 👑 」THE SUPREME VIBE", "「 ⚖️ 」HIGH COUNCIL"] for r in interaction.user.roles)
        if not is_staff and interaction.user.id not in self.bot.owner_ids and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ **Hierarchy Error.** You lack the clearance to approve alliances.", ephemeral=True)
        
        await interaction.response.edit_message(content="✅ **Partnership Approved by Staff.**", view=None)

        # 1. Post Applicant's server info in THIS server's partner hub
        local_hub_id = db.get_partner_hub(interaction.guild_id)
        applicant_guild = self.bot.get_guild(int(self.applicant_guild_id))
        app_name = applicant_guild.name if applicant_guild else "Unknown Sector"

        if local_hub_id:
            local_hub = interaction.guild.get_channel(int(local_hub_id))
            if local_hub:
                embed = discord.Embed(
                    title="🤝 NEW SOVEREIGN ALLIANCE",
                    description=f"We have synchronized with **{app_name}**.\n\n**◈ Dossier:**\n{self.description}\n\n[**>> SYNCHRONIZE WITH SECTOR <<**]({self.invite})",
                    color=0x00FFCC
                )
                role = discord.utils.get(interaction.guild.roles, name="Partnership Pings")
                content = role.mention if role else None
                await local_hub.send(content=content, embed=embed)

        # 2. Save to Database
        db.add_partner(self.applicant_guild_id, app_name, self.invite, self.description)
        db.update_partner_status(self.applicant_guild_id, "approved")

        # 3. Try to get THIS server's invite to send back to the applicant
        try:
            invite_link = "No invite available."
            # Try to grab an existing invite or create one from the local hub
            invites = await interaction.guild.invites()
            if invites:
                invite_link = invites[0].url
            elif local_hub:
                new_inv = await local_hub.create_invite(max_age=0, max_uses=0)
                invite_link = new_inv.url

            # Find Applicant's hub and post our info there
            partner_hub_id = db.get_partner_hub(int(self.applicant_guild_id))
            if partner_hub_id:
                partner_guild = self.bot.get_guild(int(self.applicant_guild_id))
                if partner_guild:
                    partner_hub = partner_guild.get_channel(int(partner_hub_id))
                    if partner_hub:
                        back_embed = discord.Embed(
                            title="🤝 MUTUAL ALLIANCE ACCEPTED",
                            description=f"**{interaction.guild.name}** has approved your partnership request and synchronized with your sector.\n\n[**>> SYNCHRONIZE WITH SECTOR <<**]({invite_link})",
                            color=0xFDB931
                        )
                        p_role = discord.utils.get(partner_guild.roles, name="Partnership Pings")
                        p_content = p_role.mention if p_role else None
                        await partner_hub.send(content=p_content, embed=back_embed)
                        
                        # Also DM the applicant owner
                        if partner_guild.owner:
                            try: await partner_guild.owner.send(embed=back_embed)
                            except: pass
        except Exception as e:
            print(f"⚠️ Failed to complete mutual alliance sync: {e}")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="deny_partner")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_staff = any(r.name in ["「 ⟡ 」THE HIGH ARCHITECT", "「 ⚖️ 」THE CHRONIC ARBITER", "「 💀 」THE CRYPT KEEPER", "「 🔮 」KUSH NECROMANCER", "「 🌿 」THE HIGH MASTER", "「 🖤 」AFTERDARK OVERSEER", "「 ⚖️ 」SUPPORT LEAD", "「 💻 」HAZE DEVELOPER", "「 👑 」THE SUPREME VIBE", "「 ⚖️ 」HIGH COUNCIL"] for r in interaction.user.roles)
        if not is_staff and interaction.user.id not in self.bot.owner_ids and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("❌ **Hierarchy Error.** You lack the clearance to deny alliances.", ephemeral=True)
            
        await interaction.response.edit_message(content="❌ **Partnership Denied by Staff.**", view=None)

class Partnerships(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    partner_group = app_commands.Group(name="partner", description="Sovereign Alliances: Cross-sector partnerships")

    @partner_group.command(name="apply", description="Apply for a neural partnership with another sector")
    @app_commands.describe(target_guild_id="The Server ID you want to partner with", invite="Your Server's Permanent Invite Link", description="Brief summary of your sector")
    @staff_or_owner("administrator")
    async def apply(self, interaction: discord.Interaction, target_guild_id: str, invite: str, description: str):
        await interaction.response.defer(ephemeral=True)
        if "discord.gg/" not in invite and "discord.com/invite/" not in invite:
            return await interaction.followup.send("❌ Invalid invite link. Please use a permanent Discord invite.", ephemeral=True)

        try: target_id = int(target_guild_id)
        except: return await interaction.followup.send("❌ Invalid Target Guild ID.", ephemeral=True)

        target_guild = self.bot.get_guild(target_id)
        if not target_guild:
            return await interaction.followup.send("❌ **Neural Error.** Haze Bot is not connected to that sector. Ensure the bot is in the target server.", ephemeral=True)

        # Find target staff hub
        hub_names = ["󠇲 ┇ ◌ terminal-logs", "󠇲 ┇ ◌ grave-logs", "󠇲 ┇ ◌ void-logs", "󠇲 ┇ ◌ staff-chat", "󠇲 ┇ ◌ bot-alerts"]
        staff_hub = None
        for name in hub_names:
            staff_hub = discord.utils.get(target_guild.text_channels, name=name)
            if staff_hub: break
            
        if not staff_hub:
            return await interaction.followup.send(f"❌ **Neural Error.** The target sector ({target_guild.name}) has not configured a valid Staff Hub. Cannot route application.", ephemeral=True)

        embed = discord.Embed(
            title="🤝 INCOMING PARTNERSHIP REQUEST",
            description=f"**From Sector:** {interaction.guild.name}\n**Applicant:** {interaction.user.mention}\n**Invite:** {invite}\n\n**Dossier:**\n{description}",
            color=0xFDB931
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        try:
            await staff_hub.send(embed=embed, view=PartnershipView(interaction.guild_id, invite, description, self.bot))
            await interaction.followup.send(f"📡 **Application Dispatched.** Transmission securely routed to the High Architects of **{target_guild.name}**.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ **Transmission Failed.** Could not penetrate the target sector's firewall. ({e})", ephemeral=True)

    @partner_group.command(name="add", description="STAFF: Directly add a partnered server to the hub and registry")
    @app_commands.describe(server_name="Name of the partnered server", invite_link="Permanent invite link to the server", description="Brief description of the partner")
    @staff_or_owner("administrator")
    async def partner_add(self, interaction: discord.Interaction, server_name: str, invite_link: str, description: str):
        await interaction.response.defer(ephemeral=True)
        if "discord.gg/" not in invite_link and "discord.com/invite/" not in invite_link:
            return await interaction.followup.send("❌ Invalid invite link.", ephemeral=True)

        # 1. Post to local hub
        hub_id = db.get_partner_hub(interaction.guild_id)
        if hub_id:
            hub = interaction.guild.get_channel(int(hub_id))
            if hub:
                embed = discord.Embed(
                    title="🤝 NEW SOVEREIGN ALLIANCE",
                    description=f"We have synchronized with **{server_name}**.\n\n**◈ Dossier:**\n{description}\n\n[**>> SYNCHRONIZE WITH SECTOR <<**]({invite_link})",
                    color=0x00FFCC
                )
                role = discord.utils.get(interaction.guild.roles, name="Partnership Pings")
                content = role.mention if role else None
                await hub.send(content=content, embed=embed)

        # 2. Save to global registry (using a dummy ID if it's external, or try to resolve)
        # We'll use a hash or just the server name if we can't find the ID
        db.add_partner(server_name.lower().replace(" ", "_"), server_name, invite_link, description)
        db.update_partner_status(server_name.lower().replace(" ", "_"), "approved")

        await interaction.followup.send(f"✅ **Alliance Registered.** **{server_name}** has been added to the hub and global registry.", ephemeral=True)

    @partner_group.command(name="setup", description="STAFF: Deploy the complete Sovereign Alliance infrastructure")
    @staff_or_owner("administrator")
    async def partner_setup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # 1. Role Initialization
        roles_to_create = [
            ("「 💎 」ELITE CONNOISSEUR", 0xADD8E6),
            ("Partnership Pings", 0x00FFCC)
        ]
        
        for name, color in roles_to_create:
            if not discord.utils.get(guild.roles, name=name):
                try: await guild.create_role(name=name, color=color, hoist=True)
                except: pass

        # 2. Category & Channel Initialization
        category = discord.utils.get(guild.categories, name="◌ [ ALLIANCES ]")
        if not category:
            category = await guild.create_category("◌ [ ALLIANCES ]")
            
        channel = discord.utils.get(category.text_channels, name="󠇲-┇-◌-partnerships") or discord.utils.get(guild.text_channels, name="partnerships")
        if not channel:
            channel = await guild.create_text_channel("󠇲 ┇ ◌ partnerships", category=category)

        # 3. Database Sync
        db.set_partner_hub(interaction.guild_id, channel.id)
        
        # 4. Welcome HUD
        embed = discord.Embed(
            title="🤝 SOVEREIGN ALLIANCE HUB",
            description=(
                "Welcome to the central node for cross-sector alliances.\n\n"
                "**◈ NOTIFICATIONS:** Click below to be pinged for new partners.\n"
                "**◈ APPLICATIONS:** Use `/partner apply` to join our network.\n\n"
                "All synchronized sectors are reviewed by the High Architect."
            ),
            color=0x00FFCC
        )
        await channel.send(embed=embed, view=PartnerRoleView())
        await interaction.followup.send(f"✅ **Alliance Infrastructure Deployed.** Hub synchronized in {channel.mention}.", ephemeral=True)

    @partner_group.command(name="list", description="Registry: Access the list of approved Sovereign Partners")
    async def list_partners(self, interaction: discord.Interaction):
        await interaction.response.defer()
        partners = db.get_partners("approved")
        
        if not partners:
            return await interaction.followup.send("🌫️ **No alliances found.** The registry is currently void.")

        embed = discord.Embed(title="🤝 SOVEREIGN PARTNER REGISTRY", color=0x00FFCC)
        for p in partners:
            embed.add_field(
                name=f"◈ {p['name']}",
                value=f"{p['description']}\n[**Join Sector**]({p['invite']})",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

    admin_partner_group = app_commands.Group(name="admin_partner", description="GOD MODE: Manage partnership records")

    @admin_partner_group.command(name="approve", description="GOD MODE: Manually approve a sector partnership")
    @staff_or_owner()
    async def admin_approve(self, interaction: discord.Interaction, guild_id: str):
        db.update_partner_status(guild_id, "approved")
        await interaction.response.send_message(f"✅ Sector `{guild_id}` approved.", ephemeral=True)

    @admin_partner_group.command(name="deny", description="GOD MODE: Manually deny a sector partnership")
    @staff_or_owner()
    async def admin_deny(self, interaction: discord.Interaction, guild_id: str):
        db.update_partner_status(guild_id, "denied")
        await interaction.response.send_message(f"❌ Sector `{guild_id}` denied.", ephemeral=True)

    @admin_partner_group.command(name="remove", description="GOD MODE: Permanently dissolve an alliance")
    @staff_or_owner()
    async def admin_remove(self, interaction: discord.Interaction, guild_id: str):
        db.remove_partner(guild_id)
        await interaction.response.send_message(f"🧹 Alliance with `{guild_id}` dissolved.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Partnerships(bot))
