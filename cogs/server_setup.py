import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.logic import elite_only, staff_or_owner
from utils.mongo import db

# --- Persistent Views ---

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Indica", style=discord.ButtonStyle.primary, custom_id="role_indica", emoji="🍃")
    async def indica(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "〔 🍃 〕INDICA")

    @discord.ui.button(label="Sativa", style=discord.ButtonStyle.secondary, custom_id="role_sativa", emoji="⚡")
    async def sativa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "〔 ⚡ 〕SATIVA")

    @discord.ui.button(label="Hybrid", style=discord.ButtonStyle.success, custom_id="role_hybrid", emoji="☯️")
    async def hybrid(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "〔 ☯️ 〕HYBRID")

    @discord.ui.button(label="Session Pings", style=discord.ButtonStyle.secondary, custom_id="role_sesh", emoji="🔔")
    async def sesh_ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_names = ["〔 🛰️ 〕SYNC SIGNAL", "〔 💀 〕CRYPT SUMMONS", "〔 🔔 〕SESH PINGS", "〔 🔔 〕AFTERDARK SIGNAL"]
        role = None
        for name in role_names:
            role = discord.utils.get(interaction.guild.roles, name=name)
            if role: break
        
        if not role:
            return await interaction.response.send_message("❌ Notification frequency not found in hierarchy.", ephemeral=True)
            
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("🌬️ Session notifications deactivated.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✨ Session notifications activated.", ephemeral=True)

    async def toggle_role(self, interaction: discord.Interaction, role_name: str):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            return await interaction.response.send_message(f"❌ Role `{role_name}` not found.", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🌬️ Removed the **{role_name}** frequency.", ephemeral=True)
        else:
            prefixes = ["〔 🍃 〕INDICA", "〔 ⚡ 〕SATIVA", "〔 ☯️ 〕HYBRID"]
            to_remove = [r for r in interaction.user.roles if r.name in prefixes]
            if to_remove: await interaction.user.remove_roles(*to_remove)
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✨ Synchronized with the **{role_name}** aura.", ephemeral=True)

class GenderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="King", style=discord.ButtonStyle.primary, custom_id="gender_king", emoji="👑")
    async def king(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_gender(interaction, "KING")

    @discord.ui.button(label="Queen", style=discord.ButtonStyle.danger, custom_id="gender_queen", emoji="👸")
    async def queen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_gender(interaction, "QUEEN")

    async def toggle_gender(self, interaction: discord.Interaction, type: str):
        role_map = {
            "KING": ["〔 👑 〕SOVEREIGN KING", "〔 💀 〕CRYPT KING", "〔 👑 〕LOUNGE KING", "〔 👑 〕AFTERDARK KING"],
            "QUEEN": ["〔 👸 〕SOVEREIGN QUEEN", "〔 🕯️ 〕CRYPT QUEEN", "〔 👸 〕LOUNGE QUEEN", "〔 👸 〕AFTERDARK QUEEN"]
        }
        target_name = None
        for name in role_map[type]:
            if discord.utils.get(interaction.guild.roles, name=name):
                target_name = name
                break
        if not target_name:
            return await interaction.response.send_message("❌ Gender frequency not initialized.", ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name=target_name)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🌬️ Neutralized your **{type}** alignment.", ephemeral=True)
        else:
            all_gender_roles = role_map["KING"] + role_map["QUEEN"]
            to_remove = [r for r in interaction.user.roles if r.name in all_gender_roles]
            if to_remove: await interaction.user.remove_roles(*to_remove)
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✨ Alignment confirmed: **{target_name}**.", ephemeral=True)

class ColorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_color(self, interaction: discord.Interaction, color_name: str):
        guild = interaction.guild
        color_role = discord.utils.get(guild.roles, name=f"〔 ✧ 〕{color_name}")
        if not color_role:
            return await interaction.response.send_message(f"❌ Color role `{color_name}` not found.", ephemeral=True)
        color_prefixes = ["〔 ✧ 〕"]
        to_remove = [r for r in interaction.user.roles if any(p in r.name for p in color_prefixes)]
        if color_role in interaction.user.roles:
            await interaction.user.remove_roles(color_role)
            return await interaction.response.send_message(f"🌬️ Neutralized your chromatic frequency.", ephemeral=True)
        if to_remove: await interaction.user.remove_roles(*to_remove)
        await interaction.user.add_roles(color_role)
        await interaction.response.send_message(f"🎨 Synced with the **{color_name}** spectrum.", ephemeral=True)

    @discord.ui.button(label="Obsidian", style=discord.ButtonStyle.secondary, custom_id="color_obsidian", row=0)
    async def obsidian(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "OBSIDIAN")
    @discord.ui.button(label="Diamond", style=discord.ButtonStyle.secondary, custom_id="color_diamond", row=0)
    async def diamond(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "DIAMOND")
    @discord.ui.button(label="Violet", style=discord.ButtonStyle.secondary, custom_id="color_violet", row=0)
    async def violet(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "NEON VIOLET")
    @discord.ui.button(label="Electric", style=discord.ButtonStyle.secondary, custom_id="color_electric", row=0)
    async def electric(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "ELECTRIC BLUE")
    @discord.ui.button(label="Gold", style=discord.ButtonStyle.secondary, custom_id="color_gold", row=0)
    async def gold(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "LIQUID GOLD")
    
    @discord.ui.button(label="Ruby", style=discord.ButtonStyle.secondary, custom_id="color_ruby", row=1)
    async def ruby(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "RUBY RED")
    @discord.ui.button(label="Emerald", style=discord.ButtonStyle.secondary, custom_id="color_emerald", row=1)
    async def emerald(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "EMERALD")
    @discord.ui.button(label="Sapphire", style=discord.ButtonStyle.secondary, custom_id="color_sapphire", row=1)
    async def sapphire(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "SAPPHIRE")
    @discord.ui.button(label="Rose", style=discord.ButtonStyle.secondary, custom_id="color_rose", row=1)
    async def rose(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "ROSE")
    @discord.ui.button(label="Silver", style=discord.ButtonStyle.secondary, custom_id="color_silver", row=1)
    async def silver(self, interaction: discord.Interaction, button: discord.ui.Button): await self.handle_color(interaction, "SILVER")

class SupportTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Open Support Ticket", style=discord.ButtonStyle.success, custom_id="open_ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower().replace(' ', '-')}")
        if existing_channel:
            return await interaction.response.send_message(f"❌ You already have an active ticket: {existing_channel.mention}", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        
        # Support roles to ping or grant access
        support_roles = ["「 🛠️ 」SUPPORT AGENT", "「 ⚖️ 」SUPPORT LEAD", "「 💻 」HAZE DEVELOPER", "CHRONIC SUPPORT"]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }
        
        for r_name in support_roles:
            role = discord.utils.get(guild.roles, name=r_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
        
        category = discord.utils.get(guild.categories, name="◌ [ STAFF HQ ]")
        if not category: category = discord.utils.get(guild.categories, name="◌ [ STAFF HUB ]")
        
        ticket_channel = await guild.create_text_channel(name=f"ticket-{member.name}", category=category, overwrites=overwrites)
        embed = discord.Embed(title="🎫 TICKET OPENED", description=f"Hello {member.mention}, staff have been notified. Please describe your issue in detail.", color=0x00FFCC)
        await ticket_channel.send(embed=embed, view=CloseTicketView())
        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class VelvetRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Indica", style=discord.ButtonStyle.primary, custom_id="velvet_indica", emoji="🍃")
    async def indica(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "〔 🍃 〕INDICA")

    @discord.ui.button(label="Sativa", style=discord.ButtonStyle.secondary, custom_id="velvet_sativa", emoji="⚡")
    async def sativa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "〔 ⚡ 〕SATIVA")

    @discord.ui.button(label="Hybrid", style=discord.ButtonStyle.success, custom_id="velvet_hybrid", emoji="☯️")
    async def hybrid(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "〔 ☯️ 〕HYBRID")

    async def toggle_role(self, interaction: discord.Interaction, role_name: str):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role: return await interaction.response.send_message(f"❌ Aura `{role_name}` not found.", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🌬️ Neutralized the **{role_name}** frequency.", ephemeral=True)
        else:
            prefixes = ["〔 🍃 〕INDICA", "〔 ⚡ 〕SATIVA", "〔 ☯️ 〕HYBRID"]
            to_remove = [r for r in interaction.user.roles if r.name in prefixes]
            if to_remove: await interaction.user.remove_roles(*to_remove)
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✨ Synchronized with the **{role_name}** aura.", ephemeral=True)

class VelvetGenderView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="King", style=discord.ButtonStyle.primary, custom_id="velvet_king", emoji="👑")
    async def king(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_gender(interaction, "KING")

    @discord.ui.button(label="Queen", style=discord.ButtonStyle.danger, custom_id="velvet_queen", emoji="👸")
    async def queen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_gender(interaction, "QUEEN")

    async def toggle_gender(self, interaction: discord.Interaction, type: str):
        # Specific names for Velvet template if needed, or fallback to standard
        role_map = {
            "KING": ["〔 👑 〕SOVEREIGN KING", "〔 👑 〕UNDERWORLD KING"],
            "QUEEN": ["〔 👸 〕SOVEREIGN QUEEN", "〔 👸 〕UNDERWORLD QUEEN"]
        }
        target_name = None
        for name in role_map[type]:
            if discord.utils.get(interaction.guild.roles, name=name):
                target_name = name
                break
        if not target_name: return await interaction.response.send_message("❌ Gender frequency not initialized.", ephemeral=True)
        role = discord.utils.get(interaction.guild.roles, name=target_name)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🌬️ Neutralized your **{type}** alignment.", ephemeral=True)
        else:
            all_gender_roles = role_map["KING"] + role_map["QUEEN"]
            to_remove = [r for r in interaction.user.roles if r.name in all_gender_roles]
            if to_remove: await interaction.user.remove_roles(*to_remove)
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✨ Alignment confirmed: **{target_name}**.", ephemeral=True)

# --- Main Cog ---

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_sovereign_overwrites(self, guild, required_role_name=None, is_read_only=False, is_voice=False, is_affiliate=False, gender_gate=None, is_movie=False):
        roles = {r.name.upper(): r for r in guild.roles}
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False, use_application_commands=True)}
        
        staff_keys = [
            "THE HIGH ARCHITECT", "THE CHRONIC ARBITER", "SYSTEM HASH", "CHRONIC SUPPORT", 
            "CULTIVATOR", "THE CRYPT KEEPER", "KUSH NECROMANCER", "GRAVE DIGGER", 
            "THE VIBE MASTER", "LOUNGE ARBITER", "AFTERDARK OVERSEER", "SHADOW ARBITER", 
            "AFTERDARK SUPPORT", "THE HIGH MASTER", "SYSTEM OVERSEER", "HAZE DEVELOPER", 
            "SUPPORT LEAD", "SUPPORT AGENT"
        ]
        for key in staff_keys:
            for name, role in roles.items():
                if key in name:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, stream=True, send_messages=True, embed_links=True, attach_files=True, manage_messages=True, manage_channels=True, use_application_commands=True)

        if is_affiliate:
            for name, role in roles.items():
                if "ELITE CONNOISSEUR" in name: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True)

        if gender_gate:
            male_keys = ["KING"]
            female_keys = ["QUEEN"]
            for name, role in roles.items():
                is_king = any(k in name for k in male_keys)
                is_queen = any(k in name for k in female_keys)
                if gender_gate == "MALE":
                    if is_king: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True, use_application_commands=True)
                    if is_queen: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, connect=False, use_application_commands=True)
                elif gender_gate == "FEMALE":
                    if is_queen: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True, use_application_commands=True)
                    if is_king: overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, connect=False, use_application_commands=True)

        tier_roles = [
            "NEW BUD", "CITIZEN STONER", "NOBLE BLAZER", "ELITE SMOKER", "TITAN BUD", "SYNDICATE", "MYSTIC", "ETERNAL O.G.", 
            "RECENTLY DEPARTED", "REVENANT BUD", "SHADOW HAZER", "CRYPT GHOUL", "TOMB SMOKER", "ANCIENT ASH", 
            "NEW ARRIVAL", "VIBE CITIZEN", "EMBER ENTHUSIAST", "CLOUD CHASER", "HIGH ROLLER", "LOUNGE LEGEND", 
            "LATE ARRIVAL", "DARK CITIZEN", "MIDNIGHT O.G.", "CRIMSON BLAZER", "SHADOW SYNDICATE", "NOCTURNAL MYSTIC", "VELVET ROGUE",
            "VERIFIED MEMBER", 
            "NEW HARVEST", "GREEN INITIATE", "SMOKE STACK", "EMBER ENTHUSIAST", "RESIN RECLUSE", "VIBE ARCHITECT", "CELESTIAL SMOKER", "DIAMOND DRIPPER", "ZENITH CONNOISSEUR", "ETERNAL HIGH", 
            "ISLAND ARRIVAL", "BEACHCOMBER", "CANOE DRIFTER", "TROPICAL BLAZER", "COCONUT O.G.", "OCEAN MASTER", "SHELL SEEKER",
            "PRESTIGE I", "PRESTIGE II", "PRESTIGE III", "PRESTIGE IV", "PRESTIGE V"
        ]
        
        # Determine starting index for tiers
        if required_role_name and required_role_name.upper() in tier_roles:
            start_index = tier_roles.index(required_role_name.upper())
        elif required_role_name is None:
            start_index = 0 # Default access
        else:
            # If a staff role name is passed, standard members should NOT have access
            start_index = 999 
        
        # VERIFIED ACCESS PROTOCOL: Grant verified users access to non-level-locked channels
        verified_keys = ["〔 🔞 〕VERIFIED 18+", "〔 🍺 〕VERIFIED 21+", "〔 👤 〕VERIFIED MEMBER"]
        base_tiers = ["NEW BUD", "RECENTLY DEPARTED", "NEW ARRIVAL", "LATE ARRIVAL", "VERIFIED MEMBER", "NEW HARVEST", "ISLAND ARRIVAL"]
        is_level_locked = required_role_name and required_role_name.upper() not in base_tiers

        for i, tier_name in enumerate(tier_roles):
            role = None
            for r_name, r_obj in roles.items():
                if tier_name.upper() in r_name:
                    role = r_obj
                    break
            
            if role:
                has_access = i >= start_index
                if role in overwrites: continue
                
                can_speak = True
                if is_movie and is_voice: can_speak = False

                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=has_access, 
                    send_messages=has_access if not is_read_only else False, 
                    connect=has_access, 
                    speak=has_access if can_speak else False, 
                    stream=has_access, 
                    read_message_history=has_access, 
                    embed_links=has_access, 
                    attach_files=has_access, 
                    use_application_commands=True
                )

        # Apply Verified permissions if NOT level locked
        if not is_level_locked:
            for name, role in roles.items():
                if any(v in name for v in verified_keys):
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True, use_application_commands=True)

        return overwrites

    @app_commands.command(name="setup", description="Deploy server architecture")
    @app_commands.describe(template="The template to deploy", mode="Full = Wipe & Rebuild, Infra = Channels Only")
    @app_commands.choices(template=[
        app_commands.Choice(name="Elite Elysium", value="elysium"), 
        app_commands.Choice(name="The High Society (High-End Stoner)", value="highsociety"),
        app_commands.Choice(name="Stoner Paradise (Island Theme)", value="paradise"),
        app_commands.Choice(name="The Velvet Underworld (21+ NSFW)", value="velvet"),
        app_commands.Choice(name="Support Hub", value="support"), 
        app_commands.Choice(name="The Chronic Crypt", value="crypt"), 
        app_commands.Choice(name="The Vibe Lounge", value="vibe"), 
        app_commands.Choice(name="Elite Afterdark 18+", value="afterdark")
    ], mode=[
        app_commands.Choice(name="Full Reset (Destructive)", value="full"), 
        app_commands.Choice(name="Infrastructure Only (Keep Roles)", value="infra")
    ])
    @staff_or_owner("administrator")
    async def setup(self, interaction: discord.Interaction, template: str, mode: str = "full"):
        await self._initiate_setup(interaction, template, mode)

    @app_commands.command(name="setup_crypt", description="TOTAL REDO: THE CHRONIC CRYPT")
    @staff_or_owner("administrator")
    async def setup_crypt(self, interaction: discord.Interaction): await self._initiate_setup(interaction, template="crypt", mode="full")
    @app_commands.command(name="setup_vibe", description="TOTAL REDO: THE VIBE LOUNGE")
    @staff_or_owner("administrator")
    async def setup_vibe(self, interaction: discord.Interaction): await self._initiate_setup(interaction, template="vibe", mode="full")
    @app_commands.command(name="setup_afterdark", description="TOTAL REDO: ELITE AFTERDARK 18+")
    @staff_or_owner("administrator")
    async def setup_afterdark(self, interaction: discord.Interaction): await self._initiate_setup(interaction, template="afterdark", mode="full")

    async def _initiate_setup(self, interaction: discord.Interaction, template: str, mode: str):
        overview_embed = discord.Embed(title="🛰️ SERVER ARCHITECTURE PROTOCOL", description=f"Deploying Template: **{template.upper()}**\nMode: **{mode.upper()}**\n\n◈ **PURGE:** Channels wiped.\n◈ **ROLES:** {'Replaced.' if mode == 'full' else 'Preserved.'}\n◈ **INFRA:** Districts deployed.", color=0x00FFCC)
        class ConfirmView(discord.ui.View):
            def __init__(self, interaction_orig):
                super().__init__(timeout=60)
                self.interaction_orig, self.confirmed = interaction_orig, False
            @discord.ui.button(label="AUTHORIZE", style=discord.ButtonStyle.danger)
            async def confirm(self, bi: discord.Interaction, button: discord.ui.Button):
                if bi.user.id != self.interaction_orig.user.id: return
                self.confirmed = True
                await bi.response.edit_message(content="⚙️ **Initializing...**", embed=None, view=None)
                self.stop()
            @discord.ui.button(label="ABORT", style=discord.ButtonStyle.secondary)
            async def cancel(self, bi: discord.Interaction, button: discord.ui.Button):
                await bi.response.edit_message(content="❌ **Aborted.**", embed=None, view=None)
                self.stop()
        view = ConfirmView(interaction)
        if interaction.response.is_done(): await interaction.followup.send(embed=overview_embed, view=view, ephemeral=True)
        else: await interaction.response.send_message(embed=overview_embed, view=view, ephemeral=True)
        await view.wait()
        if not view.confirmed: return
        await self.execute_setup(interaction, template, mode)

    async def execute_setup(self, interaction, template, mode):
        guild, protected_channel = interaction.guild, interaction.channel
        terminal_embed = discord.Embed(title="[ 🛰️ ] SYSTEM TERMINAL", description="```access\n> INITIALIZING...\n```", color=0x00FFCC)
        terminal_msg = await interaction.channel.send(embed=terminal_embed)
        async def update_terminal(log_line):
            current = terminal_embed.description.replace("```access\n", "").replace("\n```", "")
            terminal_embed.description = f"```access\n{current}\n> {log_line}\n```"
            await terminal_msg.edit(embed=terminal_embed)

        if mode == "full":
            await update_terminal("REBRANDING SECTOR...")
            names = {"crypt": "THE CHRONIC CRYPT", "vibe": "THE VIBE LOUNGE", "elysium": "ELITE ELYSIUM", "afterdark": "ELITE AFTERDARK 18+", "support": "HAZE BOT SUPPORT", "highsociety": "THE HIGH SOCIETY", "paradise": "STONER PARADISE", "velvet": "THE VELVET UNDERWORLD"}
            try: await guild.edit(name=names.get(template, "ELITE ELYSIUM"))
            except: pass
            await update_terminal("PURGING CHANNELS...")
            for c in guild.channels:
                if c.id != protected_channel.id:
                    if isinstance(c, (discord.VoiceChannel, discord.StageChannel)) and len(c.members) > 0: continue
                    if isinstance(c, discord.CategoryChannel) and any(len(child.members) > 0 for child in c.channels if hasattr(child, "members")): continue
                    try: await c.delete()
                    except: pass
            await update_terminal("PURGING ROLES...")
            for r in guild.roles:
                if not r.is_default() and not r.managed and r < guild.me.top_role:
                    try: await r.delete()
                    except: pass
        
        await asyncio.sleep(1)

        if mode == "full":
            await update_terminal("DEPLOYING HIERARCHY...")
            # HIERARCHY FIX: Create in correct order (Staff FIRST so they end up at the TOP after Member tiers push them up)
            # Actually, standard logic: Staff (top of list) -> Tiers -> Identity (bottom of list)
            identity_roles = [
                ("〔 🍃 〕INDICA", 0x2ecc71, False), ("〔 ⚡ 〕SATIVA", 0xf1c40f, False), ("〔 ☯️ 〕HYBRID", 0x9b59b6, False),
                ("〔 ✧ 〕OBSIDIAN", 0x000000, False), ("〔 ✧ 〕DIAMOND", 0xffffff, False), ("〔 ✧ 〕NEON VIOLET", 0xb103fc, False),
                ("〔 ✧ 〕ELECTRIC BLUE", 0x03dbfc, False), ("〔 ✧ 〕LIQUID GOLD", 0xfcc203, False), ("〔 ✧ 〕RUBY RED", 0xe74c3c, False),
                ("〔 ✧ 〕EMERALD", 0x2ecc71, False), ("〔 ✧ 〕SAPPHIRE", 0x3498db, False), ("〔 ✧ 〕ROSE", 0xff69b4, False),
                ("〔 ✧ 〕SILVER", 0xbdc3c7, False), ("〔 🔔 〕SESH PINGS", 0x00ff00, False), ("〔 💀 〕CRYPT SUMMONS", 0x8b0000, False),
                ("「 💎 」ELITE CONNOISSEUR", 0xadd8e6, True)
            ]
            verification_roles = [("〔 🔞 〕VERIFIED 18+", 0xe74c3c, False), ("〔 🍺 〕VERIFIED 21+", 0xf1c40f, False)]
            
            if template == "elysium":
                roles_config = [
                    ("「 ⟡ 」THE HIGH ARCHITECT", 0xffffff, True), ("「 ⚖️ 」THE CHRONIC ARBITER", 0xc8c8c8, True), ("「 💾 」SYSTEM HASH", 0x505050, False),
                    ("〔 👑 〕SOVEREIGN KING", 0x00bfff, False), ("〔 👸 〕SOVEREIGN QUEEN", 0xff69b4, False), ("〔 Ω 〕ETERNAL O.G.", 0xffffff, False),
                    ("〔 🧪 〕LABORATORY LAB RAT", 0x9b59b6, False), ("〔 Ψ 〕MYSTIC HERB", 0xdcdcdc, False), ("〔 Φ 〕SYNDICATE KUSH", 0xb4b4b4, False),
                    ("〔 Σ 〕TITAN BUD", 0x8c8c8c, False), ("〔 Δ 〕ELITE SMOKER", 0x646464, False), ("〔 Λ 〕NOBLE BLAZER", 0x464646, False),
                    ("〔 Ζ 〕CITIZEN STONER", 0x2d2d2f, False), ("〔 ⟡ 〕NEW BUD", 0x1e1e1e, False)
                ] + verification_roles + identity_roles
            elif template == "highsociety":
                roles_config = [
                    ("「 👑 」 THE SUPREME ARCHITECT", 0xffffff, True), ("「 ⚖️ 」 THE HIGH COUNCIL", 0x9b59b6, True), ("「 🛠️ 」 THE CONCIERGE", 0x3498db, False),
                    ("「 💎 」 VIP: THE ILLUMINATI", 0xf1c40f, False), 
                    ("〔 💎 〕 PRESTIGE V: ASCENDANT", 0x00bfff, False), ("〔 🏆 〕 PRESTIGE IV: SOVEREIGN", 0xffd700, False),
                    ("〔 🥇 〕 PRESTIGE III: ROYAL SMOKER", 0xc0c0c0, False), ("〔 🏅 〕 PRESTIGE II: CHRONIC LEGEND", 0xcd7f32, False), ("〔 🎖️ 〕 PRESTIGE I: VIBE ELITE", 0xffffff, False),
                    ("〔 🔱 〕 ZENITH O.G.", 0xadd8e6, False), ("〔 🥂 〕 GOLD LABEL", 0xffffff, False),
                    ("〔 🏛️ 〕 ESTATE MEMBER", 0x95a5a6, False), ("〔 🍃 〕 BOTANIST", 0x2ecc71, False), ("〔 💨 〕 SOCIALITE", 0xbdc3c7, False),
                    ("〔 ⟡ 〕 THE UNREFINED", 0x1abc9c, False)
                ] + verification_roles + identity_roles
            elif template == "paradise":
                roles_config = [
                    ("「 🗿 」THE TROPICAL GOD", 0x00FFCC, True), ("「 ⚖️ 」THE REEF ARBITER", 0x9b59b6, True), ("「 🛠️ 」LAGOON SUPPORT", 0x3498db, False),
                    ("「 🐚 」LAGOON ELITE", 0xf1c40f, False), ("〔 🌊 〕OCEAN MASTER", 0x00bfff, False), ("〔 🥥 〕COCONUT O.G.", 0xffffff, False),
                    ("〔 🍹 〕TROPICAL BLAZER", 0xe74c3c, False), ("〔 🛶 〕CANOE DRIFTER", 0x95a5a6, False), ("〔 🏖️ 〕BEACHCOMBER", 0x2ecc71, False),
                    ("〔 ⟡ 〕ISLAND ARRIVAL", 0x1abc9c, False)
                ] + verification_roles + identity_roles
            elif template == "crypt":
                roles_config = [
                    ("「 💀 」THE CRYPT KEEPER", 0x000000, True), ("「 🔮 」KUSH NECROMANCER", 0x9b59b6, True), ("「 ⛏️ 」GRAVE DIGGER", 0x646464, False),
                    ("〔 💀 〕CRYPT KING", 0x460000, False), ("〔 🕯️ 〕CRYPT QUEEN", 0xff0000, False), ("〔 🏺 〕ANCIENT ASH", 0xffffff, False),
                    ("〔 ⚰️ 〕TOMB SMOKER", 0xc8c8c8, False), ("〔 👻 〕CRYPT GHOUL", 0x969696, False), ("〔 👤 〕SHADOW HAZER", 0x505050, False),
                    ("〔 🧟 〕REVENANT BUD", 0x323232, False), ("〔 ⟡ 〕CRYPT MEMBER", 0x282828, False), ("〔 🌑 〕RECENTLY DEPARTED", 0x1e1e1e, False)
                ] + verification_roles + identity_roles
            elif template == "vibe":
                roles_config = [
                    ("「 🌿 」THE HIGH MASTER", 0x2ecc71, True), ("「 ⚖️ 」CHRONIC ARBITER", 0x9b59b6, True), ("「 🛠️ 」LOUNGE SUPPORT", 0x3498db, False),
                    ("〔 👑 〕LOUNGE KING", 0x00bfff, False), ("〔 👸 〕LOUNGE QUEEN", 0xff69b4, False), ("〔 🧬 〕LOUNGE LEGEND", 0xf1c40f, False),
                    ("〔 ✨ 〕HIGH ROLLER", 0xe67e22, False), ("〔 💨 〕CLOUD CHASER", 0x95a5a6, False), ("〔 🔥 〕EMBER ENTHUSIAST", 0xe74c3c, False),
                    ("〔 🍃 〕VIBE CITIZEN", 0x27ae60, False), ("〔 ⟡ 〕NEW ARRIVAL", 0x1abc9c, False)
                ] + verification_roles + identity_roles
            elif template == "afterdark":
                roles_config = [
                    ("「 🌑 」THE NOCTURNAL ARCHITECT", 0xffffff, True), ("「 ⚖️ 」VELVET OVERSEER", 0x282828, True), ("「 🖤 」SHADOW ARBITER", 0x0a0a0a, True),
                    ("「 🛠️ 」NOCTURNAL SUPPORT", 0x3c3c3c, False), ("「 💎 」OBSIDIAN ELITE", 0xf1c40f, False), ("〔 🔞 〕NOCTURNAL MYSTIC", 0x9b59b6, False),
                    ("〔 🌙 〕SHADOW SYNDICATE", 0x000000, False), ("〔 🩸 〕CRIMSON BLAZER", 0x8b0000, False), ("〔 🌑 〕MIDNIGHT O.G.", 0x1e1e1e, False),
                    ("〔 👤 〕SINNER", 0x3c3c3c, False), ("〔 ⟡ 〕LATE ARRIVAL", 0x1e1e1e, False)
                ] + verification_roles + identity_roles
            elif template == "velvet":
                roles_config = [
                    ("「 🍷 」UNDERWORLD DEITY", 0xffffff, True), ("「 ⚖️ 」VELVET ARBITER", 0x282828, True), ("「 🖤 」SIN ARCHITECT", 0x0a0a0a, True),
                    ("「 🛠️ 」COVEN SUPPORT", 0x3c3c3c, False), ("「 💎 」VELVET ROGUE", 0xf1c40f, False), ("〔 🔞 〕ELITE COURTESAN", 0x9b59b6, False),
                    ("〔 🍷 〕VINTAGE SINNER", 0x8b0000, False), ("〔 🕯️ 〕CLANDESTINE O.G.", 0x1e1e1e, False), ("〔 👤 〕SINNER", 0x3c3c3c, False),
                    ("〔 ⟡ 〕INITIATE", 0x1e1e1e, False)
                ] + verification_roles + identity_roles
            elif template == "support":
                roles_config = [
                    ("「 🛰️ 」SYSTEM OVERSEER", 0xffffff, True), ("「 💻 」HAZE DEVELOPER", 0x00FFCC, True), ("「 ⚖️ 」SUPPORT LEAD", 0x9b59b6, True), 
                    ("「 🛠️ 」SUPPORT AGENT", 0x3498db, False), ("「 💎 」PREMIUM SUPPORTER", 0xf1c40f, False), ("〔 👤 〕VERIFIED MEMBER", 0x2ecc71, False),
                    ("〔 ⟡ 〕NEW ARRIVAL", 0x1abc9c, False)
                ] + verification_roles + identity_roles
            else: roles_config = [("「 ⟡ 」THE HIGH ARCHITECT", 0xffffff, True)] + identity_roles
            
            top_role = None
            for name, color, admin in roles_config:
                p = discord.Permissions.all() if admin else discord.Permissions(view_channel=True, send_messages=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, read_message_history=True, connect=True, speak=True, stream=True, use_voice_activation=True, change_nickname=True, use_application_commands=True)
                try:
                    role = await guild.create_role(name=name, color=discord.Color(color), permissions=p, hoist=True)
                    if not top_role: top_role = role # In this order, Staff role ends up as top_role
                    await update_terminal(f"DEPLOYED: {name}")
                except Exception as e: await update_terminal(f"ERROR {name}: {str(e)[:20]}")
                await asyncio.sleep(0.1)
            if top_role and guild.owner:
                try: await guild.owner.add_roles(top_role); await update_terminal(f"ELEVATED: {guild.owner.name}")
                except: pass

        await update_terminal("CONSTRUCTING DISTRICTS...")
        if template == "elysium":
            structure = [("◌ [ INITIALIZATION ]", [("synapse", True, "NEW BUD", False, False), ("protocol", True, "NEW BUD", False, False), ("directory", True, "NEW BUD", False, False), ("partnerships", True, "NEW BUD", False, False), ("ascension-terminal", True, "NEW BUD", False, False), ("sponsor-hub", True, "NEW BUD", False, True)]), ("◌ [ SOCIAL DISTRICT ]", [("the-lounge", False, "NEW BUD", False, False), ("gallery", False, "CITIZEN STONER", False, False), ("media-sharing", False, "NOBLE BLAZER", False, False)]), ("◌ [ THE EXCHANGE ]", [("influence-exchange", False, "NEW BUD", False, False), ("cultivation", False, "CITIZEN STONER", False, False), ("the-boutique", False, "ELITE SMOKER", False, False), ("trading-floor", False, "TITAN BUD", False, False), ("global-auctions", False, "SYNDICATE", False, False), ("black-market", False, "MYSTIC", False, False)]), ("◌ [ GAMING SECTOR ]", [("slots-parlor", False, "NEW BUD", False, False), ("coinflip-arena", False, "CITIZEN STONER", False, False), ("the-roulette-wheel", False, "NOBLE BLAZER", False, False), ("card-battles", False, "ELITE SMOKER", False, False), ("underground-fights", False, "TITAN BUD", False, False), ("high-stakes-vault", False, "SYNDICATE", False, False)]), ("◌ [ AUDIO DISTRICT ]", [("lounge-vc", False, "NEW BUD", True, False), ("gaming-vc", False, "CITIZEN STONER", True, False), ("high-stakes-vc", False, "ELITE SMOKER", True, False), ("sanctum-vc", False, "TITAN BUD", True, False), ("eternal-zenith", False, "ETERNAL O.G.", True, False)]), ("◌ [ UNRESTRICTED SECTOR ]", [("unfiltered-frequency", False, "UNRESTRICTED ACCESS", False, False)]), ("◌ [ SYSTEM HASH ]", [("overseer-comms", False, "CHRONIC ARBITER", False, False), ("terminal-logs", True, "CHRONIC ARBITER", False, False)])]
        elif template == "crypt":
            structure = [
                ("◌ [ THE ENTRANCE ]", [("the-tomb", True, "RECENTLY DEPARTED", False, False), ("crypt-protocol", True, "RECENTLY DEPARTED", False, False), ("alliances", True, "RECENTLY DEPARTED", False, False), ("ascension-terminal", True, "RECENTLY DEPARTED", False, False), ("tomb-sponsors", True, "RECENTLY DEPARTED", False, True)]),
                ("◌ [ THE CATACOMBS ]", [("general-rot", False, "RECENTLY DEPARTED", False, False), ("shadow-gallery", False, "REVENANT BUD", False, False), ("lost-frequencies", False, "SHADOW HAZER", False, False)]),
                ("◌ [ THE KING'S COURT ]", [
                    ("high-council", False, "RECENTLY DEPARTED", False, False, "MALE"),
                    ("gentlemans-den", False, "RECENTLY DEPARTED", False, False, "MALE"),
                    ("kings-voice-link", False, "RECENTLY DEPARTED", True, False, "MALE")
                ]),
                ("◌ [ THE QUEEN'S COVEN ]", [
                    ("royal-parlor", False, "RECENTLY DEPARTED", False, False, "FEMALE"),
                    ("ladies-sanctum", False, "RECENTLY DEPARTED", False, False, "FEMALE"),
                    ("queens-voice-link", False, "RECENTLY DEPARTED", True, False, "FEMALE")
                ]),
                ("◌ [ THE VAULT ]", [("bone-exchange", False, "RECENTLY DEPARTED", False, False), ("reaper-slots", False, "RECENTLY DEPARTED", False, False), ("undead-cultivation", False, "REVENANT BUD", False, False), ("soul-flip", False, "REVENANT BUD", False, False), ("damnation-roulette", False, "SHADOW HAZER", False, False), ("relic-boutique", False, "CRYPT GHOUL", False, False), ("phantom-battles", False, "CRYPT GHOUL", False, False), ("forbidden-market", False, "TOMB SMOKER", False, False)]),
                ("◌ [ THE SHADOW CINEMA ]", [("cinema-chat", False, "RECENTLY DEPARTED", False, False), ("screening-room", False, "RECENTLY DEPARTED", True, False, None, True)]),
                ("◌ [ THE ABYSS ]", [("lounge-of-lost-souls", False, "RECENTLY DEPARTED", True, False), ("warrior-grave-vc", False, "REVENANT BUD", True, False), ("eternal-void-vc", False, "ANCIENT ASH", True, False)]),
                ("◌ [ THE OSSUARY ]", [("keeper-comms", False, "KUSH NECROMANCER", False, False), ("grave-logs", True, "KUSH NECROMANCER", False, False)])
            ]
        elif template == "vibe":
            structure = [("◌ [ THE FOYER ]", [("lounge-auras", True, "NEW ARRIVAL", False, False), ("lounge-rules", True, "NEW ARRIVAL", False, False), ("partnerships", True, "NEW ARRIVAL", False, False), ("ascension-terminal", True, "NEW ARRIVAL", False, False), ("sponsor-hub", True, "NEW ARRIVAL", False, True)]), ("◌ [ SOCIAL LOUNGE ]", [("the-couch", False, "NEW ARRIVAL", False, False), ("smoke-circle", False, "NEW ARRIVAL", False, False), ("media-waves", False, "NEW ARRIVAL", False, False)]), ("◌ [ THE DISPENSARY ]", [("market", False, "NEW ARRIVAL", False, False), ("cultivation-corner", False, "NEW ARRIVAL", False, False), ("boutique", False, "NEW ARRIVAL", False, False)]), ("◌ [ GAMING DECK ]", [("blackjack", False, "NEW ARRIVAL", False, False), ("slots", False, "NEW ARRIVAL", False, False), ("vibe-roulette", False, "NEW ARRIVAL", False, False), ("high-stakes", False, "NEW ARRIVAL", False, False)]), ("◌ [ AUDIO WAVES ]", [("chill-vc", False, "NEW ARRIVAL", True, False), ("sesh-vc", False, "NEW ARRIVAL", True, False), ("legend-vc", False, "NEW ARRIVAL", True, False)]), ("◌ [ THE CINEMA ]", [("lounge-cinema-chat", False, "NEW ARRIVAL", False, False), ("lounge-screening-room", False, "NEW ARRIVAL", True, False, None, True)]), ("◌ [ BEHIND THE SCENES ]", [("management-lounge", False, "LOUNGE ARBITER", False, False)])]
        elif template == "afterdark":
            structure = [
                ("◌ [ THE VOID ]", [
                    ("arrival-hall", True, "LATE ARRIVAL", False, False), 
                    ("shadow-directory", True, "LATE ARRIVAL", False, False),
                    ("midnight-protocols", True, "LATE ARRIVAL", False, False),
                    ("verify-here", True, None, False, False)
                ]),
                ("◌ [ THE RED LIGHT DISTRICT ]", [
                    ("neon-lounge", False, "VERIFIED MEMBER", False, False), 
                    ("sensory-visuals", False, "DARK CITIZEN", False, False),
                    ("lust-and-liquor", False, "MIDNIGHT O.G.", False, False),
                    ("scarlet-vc", False, "DARK CITIZEN", True, False)
                ]),
                ("◌ [ THE PRIVATE SECTOR ]", [
                    ("velvet-sanctum", False, "CRIMSON BLAZER", False, False),
                    ("illicit-archives", False, "SHADOW SYNDICATE", False, False),
                    ("the-confessional", False, "NOCTURNAL MYSTIC", False, False),
                    ("obsidian-audio", False, "VELVET ROGUE", True, False)
                ]),
                ("◌ [ THE SINNERS CIRCLE ]", [
                    ("deity-lounge", False, "THE NOCTURNAL ARCHITECT", False, False),
                    ("overseer-comms", False, "VELVET OVERSEER", False, False),
                    ("the-black-gate", True, "THE NOCTURNAL ARCHITECT", False, False)
                ]),
                ("◌ [ THE DARK MARKET ]", [
                    ("black-market", False, "DARK CITIZEN", False, False), 
                    ("the-vault", False, "MIDNIGHT O.G.", False, False)
                ]),
                ("◌ [ SYSTEM SHADOWS ]", [
                    ("void-logs", True, "SHADOW ARBITER", False, False)
                ])
            ]
        elif template == "highsociety":
            structure = [
                ("◌ [ THE ARRIVAL GATE ]", [
                    ("arrival-hall", True, "NEW HARVEST", False, False),
                    ("the-manifesto", True, "NEW HARVEST", False, False),
                    ("sector-directory", True, "NEW HARVEST", False, False),
                    ("high-society-auras", True, "NEW HARVEST", False, False)
                ]),
                ("◌ [ THE VERIFICATION GATE ]", [
                    ("verify-here", True, None, False, False)
                ]),
                ("◌ [ THE GRAND HALL ]", [
                    ("society-lounge", False, "VERIFIED MEMBER", False, False),
                    ("connoisseur-media", False, "SMOKE STACK", False, False),
                    ("the-conservatory", False, "VIBE ARCHITECT", False, False),
                    ("luxury-vc", False, "ESTATE MEMBER", True, False)
                ]),
                ("◌ [ THE PRIVATE ESTATE ]", [
                    ("sovereign-vault", False, "SOVEREIGN ELITE", False, False),
                    ("zenith-library", True, "ZENITH CONNOISSEUR", False, False),
                    ("architect-study", False, "THE GRAND ARCHITECT", False, False),
                    ("royal-voice-link", False, "HIGH SOCIETY O.G.", True, False)
                ]),
                ("◌ [ THE BOTANICAL GARDEN ]", [
                    ("botany-chat", False, "NEW HARVEST", False, False),
                    ("the-greenhouse", False, "VIBE ARCHITECT", False, False)
                ]),
                ("◌ [ THE HIGH STAKES ]", [
                    ("gaming-parlor", False, "NEW HARVEST", False, False),
                    ("auction-house", False, "ESTATE MEMBER", False, False)
                ]),
                ("◌ [ SYSTEM HASH ]", [
                    ("council-comms", False, "THE CROWN COUNCIL", False, False),
                    ("void-logs", True, "THE CROWN COUNCIL", False, False)
                ])
            ]
        elif template == "paradise":
            structure = [
                ("🌴 [ THE TROPICAL SHORE ]", [
                    ("arrival-hall", True, "ISLAND ARRIVAL", False, False),
                    ("paradise-directory", True, "ISLAND ARRIVAL", False, False),
                    ("beach-rules", True, "ISLAND ARRIVAL", False, False),
                    ("island-auras", True, "ISLAND ARRIVAL", False, False)
                ]),
                ("🍃 [ THE JUNGLE CANOPY ]", [
                    ("island-chat", False, "ISLAND ARRIVAL", False, False),
                    ("media-gallery", False, "ISLAND ARRIVAL", False, False),
                    ("voice-lagoon", False, "ISLAND ARRIVAL", True, False)
                ]),
                ("🌺 [ THE BOTANICAL LAGOON ]", [
                    ("strain-tracking", False, "ISLAND ARRIVAL", False, False),
                    ("cultivation-beach", False, "ISLAND ARRIVAL", False, False)
                ]),
                ("🍹 [ THE TIKI PARLOR ]", [
                    ("slots", False, "ISLAND ARRIVAL", False, False),
                    ("coinflip", False, "ISLAND ARRIVAL", False, False),
                    ("island-games", False, "ISLAND ARRIVAL", False, False)
                ]),
                ("🐚 [ THE TRADING REEF ]", [
                    ("island-market", False, "ISLAND ARRIVAL", False, False),
                    ("auctions", False, "ISLAND ARRIVAL", False, False)
                ]),
                ("🔒 [ STAFF COVE ]", [
                    ("staff-chat", False, "PARADISE ARBITER", False, False),
                    ("bot-logs", True, "PARADISE ARBITER", False, False)
                ])
            ]
        elif template == "support":
            structure = [
                ("◌ [ INITIALIZATION ]", [
                    ("verify-here", True, "NEW ARRIVAL", False, False),
                    ("information", True, "NEW ARRIVAL", False, False),
                    ("announcements", True, "NEW ARRIVAL", False, False),
                    ("server-status", True, "NEW ARRIVAL", False, False)
                ]),
                ("◌ [ HAZE SUPPORT ]", [
                    ("open-a-ticket", True, "NEW ARRIVAL", False, False),
                    ("faq-knowledgebase", True, "NEW ARRIVAL", False, False),
                    ("suggestions", False, "NEW ARRIVAL", False, False)
                ]),
                ("◌ [ COMMUNITY ]", [
                    ("general-chat", False, "VERIFIED MEMBER", False, False),
                    ("bot-commands", False, "VERIFIED MEMBER", False, False),
                    ("voice-lounge", False, "VERIFIED MEMBER", True, False)
                ]),
                ("◌ [ STAFF HQ ]", [
                    ("staff-chat", False, "SUPPORT AGENT", False, False),
                    ("bot-alerts", True, "SUPPORT AGENT", False, False),
                    ("ticket-logs", True, "SUPPORT AGENT", False, False)
                ])
            ]
        else:
            structure = [
                ("◌ [ WELCOME WAGON ]", [
                    ("verify-entry", True, "NEW BUD", False, False),
                    ("welcome", True, "NEW BUD", False, False),
                    ("rules-info", True, "NEW BUD", False, False)
                ]),
                ("◌ [ ANNOUNCEMENTS ]", [
                    ("updates", True, "NEW BUD", False, False),
                    ("status-board", True, "NEW BUD", False, False),
                    ("sneak-peeks", True, "NEW BUD", False, False)
                ]),
                ("◌ [ SUPPORT CENTER ]", [
                    ("open-a-ticket", True, "NEW BUD", False, False),
                    ("faq-knowledgebase", True, "NEW BUD", False, False),
                    ("community-help", False, "NEW BUD", False, False)
                ]),
                ("◌ [ FEEDBACK & IDEAS ]", [
                    ("feature-requests", False, "NEW BUD", False, False),
                    ("bug-reports", False, "NEW BUD", False, False)
                ]),
                ("◌ [ COMMUNITY ]", [
                    ("general-chat", False, "NEW BUD", False, False),
                    ("bot-commands", False, "NEW BUD", False, False),
                    ("voice-lounge", False, "NEW BUD", True, False)
                ]),
                ("◌ [ STAFF HQ ]", [
                    ("staff-chat", False, "CHRONIC SUPPORT", False, False),
                    ("bot-alerts", True, "CHRONIC SUPPORT", False, False),
                    ("ticket-logs", True, "CHRONIC SUPPORT", False, False)
                ])
            ]

        for cat_name, channels in structure:
            category = await guild.create_category(cat_name)
            for ch_item in channels:
                ch_name, read_only, tier, is_vc = ch_item[0], ch_item[1], ch_item[2], ch_item[3]
                is_affiliate = ch_item[4] if len(ch_item) > 4 else False
                gender_gate = ch_item[5] if len(ch_item) > 5 else None
                is_movie = ch_item[6] if len(ch_item) > 6 else False
                overwrites = await self.get_sovereign_overwrites(guild, tier, read_only, is_vc, is_affiliate, gender_gate, is_movie)
                nsfw = "unfiltered" in ch_name or "sensory" in ch_name or "visuals" in ch_name or "unrestricted" in ch_name
                if is_vc: await guild.create_voice_channel(f"󠇲 ┇ ◌ {ch_name}", category=category, overwrites=overwrites)
                else: 
                    ch = await guild.create_text_channel(f"󠇲 ┇ ◌ {ch_name}", category=category, overwrites=overwrites, nsfw=nsfw)
                    if any(x in ch_name for x in ["synapse", "the-tomb", "lounge-auras", "afterdark-auras", "high-society-auras"]):
                        await ch.send(embed=discord.Embed(title="🎭 NEURAL AURA", description="Select your frequency.", color=0xFFFFFF), view=RoleView())
                        await ch.send(embed=discord.Embed(title="🎨 CHROMATIC SPECTRUM", description="Sync your visual aura.", color=0xFFFFFF), view=ColorView())
                        await ch.send(embed=discord.Embed(title="👑 ROYAL FREQUENCY", description="Confirm alignment.", color=0xFFFFFF), view=GenderView())
                    
                    if "verify-here" in ch_name:
                        verify_embed = discord.Embed(
                            title="🛡️ NEURAL VERIFICATION GATE",
                            description=(
                                "Welcome to the inner sanctum. To unlock the full potential of this sector, you must verify your identity.\n\n"
                                "**◈ PROTOCOL:** Use the `/verify` command and upload a clear photo of your ID.\n"
                                "**◈ UNLOCKED:** Access to the Private Sector, Social Club, and Exchange.\n\n"
                                "*Your data is protected by Haze Bot's privacy shield and is purged after review.*"
                            ),
                            color=0x00FFCC
                        )
                        await ch.send(embed=verify_embed)

                    if template == "highsociety":
                        descriptions = {
                            "arrival-hall": ("👋 WELCOME TO THE HIGH SOCIETY", "Step into the ultimate refined cannabis experience. Please read the manifesto and align your aura."),
                            "the-manifesto": ("📜 THE MANIFESTO", "1. Respect the Vibe.\n2. Connoisseur quality only.\n3. Privacy is paramount."),
                            "sector-directory": ("🗺️ SECTOR DIRECTORY", "**◌ [ THE ARRIVAL GATE ]**\nOnboarding and alignment.\n\n**◌ [ THE GRAND HALL ]**\nPublic social lounges and media.\n\n**◌ [ THE PRIVATE ESTATE ]**\nExclusive level-locked zones.\n\n**◌ [ THE BOTANICAL GARDEN ]**\nStrain tracking and botany chat.\n\n**◌ [ THE HIGH STAKES ]**\nPremium gaming and auctions."),
                            "society-lounge": ("🍸 THE GRAND LOUNGE", "A clean, high-end space for refined conversation among verified nodes."),
                            "connoisseur-media": ("💎 CONNOISSEUR MEDIA", "Share only the highest quality visuals and artistic snapshots."),
                            "the-conservatory": ("🌿 THE CONSERVATORY", "A peaceful botanical social hub for the Vibe Architects."),
                            "luxury-vc": ("🎙️ LUXURY VOICE-LINK", "High-fidelity audio channel for established Estate Members."),
                            "sovereign-vault": ("💰 SOVEREIGN VAULT", "The secure treasury of the Sovereign Elite. Trade high-value influence."),
                            "zenith-library": ("📚 ZENITH LIBRARY", "The master archive of premium strain knowledge and genetic records."),
                            "architect-study": ("🎨 ARCHITECT'S STUDY", "The private drafting room of the Grand Architect."),
                            "botany-chat": ("🌿 BOTANY CHAT", "Discuss cultivation, genetics, and growth with fellow enthusiasts."),
                            "the-greenhouse": ("🏡 THE GREENHOUSE", "A gallery of exceptional harvests and cultivation breakthroughs."),
                            "gaming-parlor": ("🎮 GAMING PARLOR", "High-stakes gaming and community leisure activities."),
                            "auction-house": ("🔨 AUCTION HOUSE", "Elite bidding for rare digital assets and influence."),
                        }
                        for key, (title, desc) in descriptions.items():
                            if key in ch_name:
                                await ch.send(embed=discord.Embed(title=title, description=desc, color=0x00FFCC))

                    if template == "afterdark":
                        descriptions = {
                            "arrival-hall": ("🌆 WELCOME TO ELITE AFTERDARK", "The sun has set. Step into the most exclusive 18+ night-time community. Please read the protocols."),
                            "shadow-directory": ("🗺️ SHADOW DIRECTORY", "**◌ [ THE VOID ]**\nOnboarding and verification.\n\n**◌ [ THE RED LIGHT DISTRICT ]**\nPublic social lounges and media.\n\n**◌ [ THE PRIVATE SECTOR ]**\nExclusive level-locked zones.\n\n**◌ [ THE SINNERS CIRCLE ]**\nHigh-tier staff and elite lounges.\n\n**◌ [ THE DARK MARKET ]**\nIllicit trade and high-stakes vaults."),
                            "midnight-protocols": ("📜 MIDNIGHT PROTOCOLS", "1. 18+ Identification Required.\n2. Respect the privacy of all nodes.\n3. Content remains in its designated sector.\n4. No logs leave the void."),
                            "neon-lounge": ("🍸 NEON LOUNGE", "A high-fidelity social space under the constant glow of neon."),
                            "sensory-visuals": ("🎭 SENSORY VISUALS", "Share your night-time visuals and provocative sensory experiences."),
                            "lust-and-liquor": ("🥃 LUST & LIQUOR", "The main social hub for the Midnight O.G.s. Leave your inhibitions at the door."),
                            "scarlet-vc": ("🎙️ SCARLET VOICE-LINK", "The public audio bridge for all verified nocturnal nodes."),
                            "velvet-sanctum": ("💎 VELVET SANCTUM", "An elite sanctuary for Crimson Blazers. Soft light, heavy vibes."),
                            "illicit-archives": ("🔥 ILLICIT ARCHIVES", "The unrestricted media feed for Shadow Syndicates. Pure, raw energy."),
                            "the-confessional": ("🤫 THE CONFESSIONAL", "A private space for Nocturnal Mystics to share their deepest secrets."),
                            "obsidian-audio": ("🎧 OBSIDIAN AUDIO", "The most exclusive high-fidelity voice-link in the void."),
                            "deity-lounge": ("🌑 DEITY LOUNGE", "The private sanctuary of the Nocturnal Architects."),
                            "the-black-gate": ("🔒 THE BLACK GATE", "The most secure transmission terminal in the singularity."),
                            "black-market": ("🏪 BLACK MARKET", "Trade influence and illicit assets under the radar."),
                            "the-vault": ("💰 THE VAULT", "The secure treasury for high-level nocturnal transactions."),
                        }
                        for key, (title, desc) in descriptions.items():
                            if key in ch_name:
                                await ch.send(embed=discord.Embed(title=title, description=desc, color=0x0a0a0a))

                    if template == "paradise":
                        descriptions = {
                            "arrival-hall": ("🏝️ WELCOME TO STONER PARADISE", "Kick off your shoes and enjoy the island vibes. Please read the beach rules and select your aura."),
                            "paradise-directory": ("🗺️ ISLAND DIRECTORY", "**🌴 [ THE TROPICAL SHORE ]**\nEntry and orientation.\n\n**🍃 [ THE JUNGLE CANOPY ]**\nSocializing and media sharing.\n\n**🌺 [ THE BOTANICAL LAGOON ]**\nCannabis tracking and chat.\n\n**🍹 [ THE TIKI PARLOR ]**\nGames and entertainment.\n\n**🐚 [ THE TRADING REEF ]**\nMarket and auctions."),
                            "beach-rules": ("📜 BEACH RULES", "1. Good vibes only.\n2. No harshing the mellow.\n3. Respect the island.\n4. Share the fire."),
                            "island-chat": ("💬 ISLAND CHAT", "The main social hub under the palms. Relax and talk story."),
                            "media-gallery": ("📸 MEDIA GALLERY", "Share your island views, beach sunsets, and sesh photos."),
                            "voice-lagoon": ("🎙️ LAGOON VOICE-LINK", "The main audio bridge for all island drifters."),
                            "strain-tracking": ("🌿 STRAIN TRACKING", "Keep a record of your favorite tropical strains and island cures."),
                            "cultivation-beach": ("🏖️ CULTIVATION BEACH", "Discuss growing in the sand and sun with fellow cultivators."),
                            "slots": ("🎰 TIKI SLOTS", "Try your luck at the tiki bar. Fortune favors the bold."),
                            "coinflip": ("🪙 SHELL FLIP", "A simple game of chance with island shells. Double or nothing."),
                            "island-games": ("🎮 ISLAND GAMES", "Community gaming on the reef. Low stress, high fun."),
                            "island-market": ("🏪 ISLAND MARKET", "Trade items and influence on the sun-soaked shore."),
                            "auctions": ("🔨 REEF AUCTIONS", "Bid on rare island treasures and tropical bounty."),
                        }
                        for key, (title, desc) in descriptions.items():
                            if key in ch_name:
                                await ch.send(embed=discord.Embed(title=title, description=desc, color=0x00FFCC))

                    if template == "velvet":
                        descriptions = {
                            "entry-hall": ("🍷 WELCOME TO THE VELVET UNDERWORLD", "The most exclusive 21+ NSFW community in the singularity. Step into the shadows and embrace the velvet."),
                            "underworld-manifesto": ("📜 UNDERWORLD MANIFESTO", "1. 21+ Identification Mandatory.\n2. Total Discretion.\n3. Respect the Sin.\n4. Consent is non-negotiable."),
                            "velvet-lounge": ("🍸 VELVET LOUNGE", "A high-end social hub for verified sinners. Soft light, hard drinks."),
                            "illicit-media": ("🔥 ILLICIT MEDIA", "The public NSFW media feed for all underworld nodes."),
                            "underworld-voice-link": ("🎙️ UNDERWORLD VOICE-LINK", "The primary audio bridge for the velvet district."),
                            "clandestine-boudoir": ("🕯️ CLANDESTINE BOUDOIR", "An elite, private lounge for the Clandestine O.G.s."),
                            "vintage-media": ("🎞️ VINTAGE MEDIA", "A collection of high-fidelity archival NSFW visuals."),
                            "boudoir-audio": ("🎧 BOUDOIR AUDIO", "The most intimate voice-link in the boudoir."),
                            "underground-market": ("🏪 UNDERGROUND MARKET", "Trade influence and illicit assets away from prying eyes."),
                            "sinners-vault": ("💰 SINNER'S VAULT", "The secure treasury of the Velvet Rogues."),
                            "deity-sanctum": ("🍷 DEITY SANCTUM", "The inner chamber of the Underworld Deities."),
                        }
                        for key, (title, desc) in descriptions.items():
                            if key in ch_name:
                                await ch.send(embed=discord.Embed(title=title, description=desc, color=0x8b0000))

                    if "directory" in ch_name:
                        dir_embed = discord.Embed(
                            title="🗺️ SECTOR DIRECTORY",
                            description="Welcome to the singularity. Here is your map to navigating the districts:\n\n**◌ [ THE ENTRANCE ]**\nAlign your aura and verify your age to unlock deeper access.\n\n**◌ [ THE KING'S COURT & QUEEN'S COVEN ]**\nExclusive gender-aligned social hubs.\n\n**◌ [ THE SHADOW VAULT ]**\nEconomy, influence trading, and high-stakes gambling.\n\n**◌ [ UNRESTRICTED SECTOR ]**\nNSFW frequencies (Requires 18+ Verification).",
                            color=0xFFFFFF
                        )
                        await ch.send(dir_embed)
                    if any(x in ch_name for x in ["partnerships", "alliances"]): db.set_partner_hub(guild.id, ch.id); await ch.send(embed=discord.Embed(title="🤝 ALLIANCES", description="Use `/partner apply`.", color=0x00FFCC))
                    if is_affiliate: db.set_affiliate_hub(guild.id, ch.id); await ch.send(embed=discord.Embed(title="💎 SPONSORS", description="Use `/sponsor post`.", color=0xFDB931))
            await update_terminal(f"DISTRICT {cat_name} DEPLOYED."); await asyncio.sleep(0.1)

        await update_terminal("FINALIZING...")
        try:
            hud_cat = await guild.create_category("📊 [ METRICS HUD ]", position=0)
            db.guilds.update_one({"guild_id": str(guild.id)}, {"$set": {"stats_channels": {"category": str(hud_cat.id)}}})
            await self.bot.get_cog("ServerStats").force_update_guild(guild)
        except: pass
        try: self.bot.tree.copy_global_to(guild=guild); await self.bot.tree.sync(guild=guild)
        except: pass
        
        await update_terminal("RESTORING COMMUNITY...")
        base = {"elysium": "〔 ⟡ 〕NEW BUD", "crypt": "〔 🌑 〕RECENTLY DEPARTED", "vibe": "〔 ⟡ 〕NEW ARRIVAL", "afterdark": "〔 ⟡ 〕LATE ARRIVAL", "support": "〔 ⟡ 〕NEW ARRIVAL", "highsociety": "〔 ⟡ 〕NEW HARVEST", "paradise": "〔 ⟡ 〕ISLAND ARRIVAL", "velvet": "〔 ⟡ 〕INITIATE"}.get(template)
        base_role = discord.utils.get(guild.roles, name=base)
        if base_role:
            for m in guild.members:
                if not m.bot and m.id != guild.owner_id:
                    try: await m.add_roles(base_role)
                    except: pass
        await update_terminal("DEPLOYMENT 100% COMPLETE.")
        await asyncio.sleep(5); await protected_channel.delete()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.owner:
            try: await guild.owner.send(embed=discord.Embed(title="🛰️ NEURAL LINK ESTABLISHED", description=f"Thank you for adding Haze Bot. Run `/setup` to initialize.", color=0x00FFCC))
            except: pass

async def setup(bot): await bot.add_cog(ServerSetup(bot))
