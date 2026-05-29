import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge", description="SOVEREIGN MANDATE: Surgically remove low-quality message frequencies")
    @app_commands.describe(amount="Number of frequencies to purge (1-100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100: 
            return await interaction.response.send_message("❌ **Neural Error.** Purge range must be 1-100.", ephemeral=True)
            
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ **Mandate Executed.** `{len(deleted)}` message frequencies surgically removed.")

    @app_commands.command(name="kick", description="SOVEREIGN MANDATE: Expel a subject from the Elysium")
    @app_commands.describe(member="The subject to expel", reason="Authorization rationale")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Unspecified"):
        if member.id == interaction.user.id: return await interaction.response.send_message("❌ Cannot expel self.", ephemeral=True)
        
        await member.kick(reason=reason)
        await interaction.response.send_message(f"✅ **Subject Expelled.** {member.name} has been removed from the sector.")

    @app_commands.command(name="ban", description="SOVEREIGN MANDATE: Permanently isolate a subject from the Singularity")
    @app_commands.describe(member="The subject to isolate", reason="Authorization rationale")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Unspecified"):
        if member.id == interaction.user.id: return await interaction.response.send_message("❌ Cannot isolate self.", ephemeral=True)
        
        await member.ban(reason=reason)
        await interaction.response.send_message(f"✅ **Subject Isolated.** {member.name} has been blacklisted from the Singularity.")

    @app_commands.command(name="add_role", description="SOVEREIGN PROTOCOL: Grant a new role frequency to a subject")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def add_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message("❌ **Neural Link Failed.** Role frequency is too high.", ephemeral=True)
        
        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ **Frequency Assigned.** `{role.name}` granted to {member.mention}.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ **Access Denied.** Insufficient role management permissions.", ephemeral=True)

    @app_commands.command(name="remove_role", description="SOVEREIGN PROTOCOL: Manually strip a role frequency from a subject")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if interaction.guild.me.top_role <= role:
            return await interaction.response.send_message("❌ **Neural Link Failed.** Role frequency is too high.", ephemeral=True)
        
        try:
            await member.remove_roles(role)
            await interaction.response.send_message(f"✅ **Frequency Neutralized.** `{role.name}` stripped from {member.mention}.")
        except discord.Forbidden:
            await interaction.response.send_message("❌ **Access Denied.** Insufficient role management permissions.", ephemeral=True)

    @app_commands.command(name="set_autorole", description="SOVEREIGN PROTOCOL: Configure the default frequency for new subjects")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def set_autorole(self, interaction: discord.Interaction, role: discord.Role = None):
        if role and interaction.guild.me.top_role <= role:
            return await interaction.response.send_message("❌ **Neural Link Failed.** Role frequency is too high.", ephemeral=True)
        
        db.set_autorole(interaction.guild_id, role.id if role else None)
        
        if role:
            await interaction.response.send_message(f"✅ **Auto-Synchronization Active.** New subjects will align with: **{role.name}**.")
        else:
            await interaction.response.send_message("✅ **Auto-Synchronization Offline.**")

    async def guild_autocomplete(self, interaction: discord.Interaction, current: str):
        if not await self.bot.is_owner(interaction.user):
            return []
        
        choices = [
            app_commands.Choice(name=g.name, value=str(g.id))
            for g in self.bot.guilds
            if current.lower() in g.name.lower()
        ][:25] 
        return choices

    @app_commands.command(name="toggle_elite", description="ADMIN: Enable or Disable Elite Elysium features")
    @app_commands.describe(status="ON to enable, OFF to disable", server_id="OWNER ONLY: Target a specific server by ID or Name")
    @app_commands.choices(status=[
        app_commands.Choice(name="ON (Elite Mode)", value="on"),
        app_commands.Choice(name="OFF (Standard Mode)", value="off")
    ])
    @app_commands.autocomplete(server_id=guild_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    async def toggle_elite(self, interaction: discord.Interaction, status: str, server_id: str = None):
        target_guild_id = interaction.guild_id
        
        if server_id:
            if not await self.bot.is_owner(interaction.user):
                return await interaction.response.send_message("❌ **Neural Link Denied.** Remote management is restricted to the Architect.", ephemeral=True)
            try: target_guild_id = int(server_id)
            except ValueError: return await interaction.response.send_message("❌ **Invalid ID.**", ephemeral=True)

        enabled = (status == "on")
        db.toggle_elite_mode(target_guild_id, enabled)
        
        guild_name = "this server"
        if server_id:
            g = self.bot.get_guild(target_guild_id)
            guild_name = g.name if g else f"Server {target_guild_id}"

        mode_str = "**ELITE ELYSIUM**" if enabled else "**STANDARD HAZE**"
        await interaction.response.send_message(f"📡 **Singularity Frequency Shifted.** `{guild_name}` is now operating in {mode_str} mode.")

    @app_commands.command(name="server_mode", description="ADMIN: Check the current operational mode of this server")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_mode(self, interaction: discord.Interaction):
        enabled = db.is_elite_enabled(interaction.guild_id)
        mode = "ELITE ELYSIUM" if enabled else "STANDARD HAZE"
        status = "ACTIVE" if enabled else "OFFLINE"
        
        embed = discord.Embed(title="🛰️ SECTOR DIAGNOSTICS", color=0x2ecc71 if enabled else 0x95a5a6)
        embed.add_field(name="Operational Mode", value=f"**{mode}**", inline=False)
        embed.add_field(name="Elite Protocols", value=f"`{status}`", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- SOVEREIGN ADMINISTRATION (ECONOMY & ACCOUNTS) ---

    @app_commands.command(name="set_balance", description="ADMIN: Set a subject's Hash Coin balance")
    @app_commands.describe(member="The subject to modify", amount="New balance amount")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_balance(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if amount < 0: amount = 0
        db.update_user(member.id, interaction.guild_id, {"hash_coins": amount})
        await interaction.response.send_message(
            f"💰 **Financial Mandate Executed.** {member.mention}'s balance set to **{amount:,} H$**.",
            ephemeral=True
        )

    @app_commands.command(name="add_balance", description="ADMIN: Inject Hash Coins into a subject's account")
    @app_commands.describe(member="The subject to modify", amount="Amount to inject")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_balance(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        user = db.get_user(member.id, interaction.guild_id)
        current = user.get("hash_coins", 0)
        new_total = current + amount
        if new_total < 0: new_total = 0
        
        db.update_user(member.id, interaction.guild_id, {"hash_coins": new_total})
        await interaction.response.send_message(
            f"💰 **Financial Injection Complete.** Added **{amount:,} H$** to {member.mention}. New Balance: **{new_total:,} H$**.",
            ephemeral=True
        )

    @app_commands.command(name="reset_account", description="ADMIN: Purge a subject's profile from the Singularity")
    @app_commands.describe(member="The subject to reset")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_account(self, interaction: discord.Interaction, member: discord.Member):
        class ResetConfirm(discord.ui.View):
            def __init__(self, user_id):
                super().__init__(timeout=60)
                self.user_id = user_id
                self.confirmed = False

            @discord.ui.button(label="AUTHORIZE PURGE", style=discord.ButtonStyle.danger)
            async def confirm(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.user_id: return
                self.confirmed = True
                await btn_interaction.response.edit_message(content="🗑️ **Wiping neural data...**", view=None)
                self.stop()

        view = ResetConfirm(interaction.user.id)
        await interaction.response.send_message(
            f"⚠️ **URGENT AUTHORIZATION REQUIRED**\n\n"
            f"This will **WIPE ALL DATA** for {member.mention}:\n"
            f"◈ Economy Balance, Level/XP, and Inventory will be deleted.\n"
            f"◈ All Hazedex progress will be lost.\n\n"
            f"This action is irreversible. Proceed?",
            view=view,
            ephemeral=True
        )
        
        await view.wait()
        if not view.confirmed: return

        db.users.delete_one({"user_id": str(member.id), "guild_id": str(interaction.guild_id)})
        
        prestige_roles = ["〔 Ω 〕ETERNAL", "〔 Ψ 〕MYSTIC", "〔 Φ 〕SYNDICATE", "〔 Σ 〕TITAN", "〔 Δ 〕ELITE", "〔 Λ 〕NOBLE", "〔 Ζ 〕CITIZEN"]
        to_remove = [r for r in member.roles if r.name in prestige_roles]
        if to_remove:
            try: await member.remove_roles(*to_remove)
            except: pass

        await interaction.followup.send(f"✅ **Account Purged.** {member.mention} has been factory reset.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
