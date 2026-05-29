import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.logic import elite_only

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent

    @discord.ui.button(label="Indica", style=discord.ButtonStyle.primary, custom_id="role_indica", emoji="💤")
    async def indica(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "Indica")

    @discord.ui.button(label="Sativa", style=discord.ButtonStyle.secondary, custom_id="role_sativa", emoji="⚡")
    async def sativa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "Sativa")

    @discord.ui.button(label="Hybrid", style=discord.ButtonStyle.success, custom_id="role_hybrid", emoji="☯️")
    async def hybrid(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, "Hybrid")

    async def toggle_role(self, interaction: discord.Interaction, role_name: str):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            return await interaction.response.send_message(f"❌ Role `{role_name}` not found. Contact an Overseer.", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🌬️ Removed the **{role_name}** aura.", ephemeral=True)
        else:
            for r_name in ["Indica", "Sativa", "Hybrid"]:
                r = discord.utils.get(interaction.guild.roles, name=r_name)
                if r and r in interaction.user.roles:
                    await interaction.user.remove_roles(r)
            
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✨ Granted the **{role_name}** aura.", ephemeral=True)

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

        if to_remove:
            await interaction.user.remove_roles(*to_remove)
        
        await interaction.user.add_roles(color_role)
        await interaction.response.send_message(f"🎨 Synced with the **{color_name}** spectrum.", ephemeral=True)

    @discord.ui.button(label="Obsidian", style=discord.ButtonStyle.secondary, custom_id="color_obsidian")
    async def obsidian(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_color(interaction, "OBSIDIAN")

    @discord.ui.button(label="Diamond", style=discord.ButtonStyle.secondary, custom_id="color_diamond")
    async def diamond(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_color(interaction, "DIAMOND")

    @discord.ui.button(label="Violet", style=discord.ButtonStyle.secondary, custom_id="color_violet")
    async def violet(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_color(interaction, "NEON VIOLET")

    @discord.ui.button(label="Electric", style=discord.ButtonStyle.secondary, custom_id="color_electric")
    async def electric(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_color(interaction, "ELECTRIC BLUE")

    @discord.ui.button(label="Gold", style=discord.ButtonStyle.secondary, custom_id="color_gold")
    async def gold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_color(interaction, "LIQUID GOLD")

class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_sovereign_overwrites(self, guild, required_role_name=None, is_read_only=False, is_voice=False):
        """Generates surgical permissions based on the Sovereign Permission Matrix."""
        roles = {r.name: r for r in guild.roles}
        
        # Base: Absolute Zero (Hidden from @everyone)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False)
        }

        # Staff: Supreme Access
        staff_keys = ["ARCHITECT", "ARBITER", "SYSTEM CORE"]
        for key in staff_keys:
            for name, role in roles.items():
                if key in name:
                    if is_voice:
                        overwrites[role] = discord.PermissionOverwrite(
                            view_channel=True, connect=True, speak=True, stream=True, 
                            mute_members=True, deafen_members=True, move_members=True, priority_speaker=True
                        )
                    else:
                        overwrites[role] = discord.PermissionOverwrite(
                            view_channel=True, send_messages=True, embed_links=True, 
                            attach_files=True, manage_messages=True, manage_channels=True
                        )

        # Members: Tiered Logic
        tier_roles = ["GUEST", "CITIZEN", "NOBLE", "ELITE", "TITAN", "ETERNAL"]
        
        # If no role specified, GUEST is the minimum for public areas
        min_tier = required_role_name if required_role_name else "GUEST"
        
        try:
            start_index = tier_roles.index(min_tier)
        except ValueError:
            start_index = 0 # Fallback to Guest
        
        for i, tier in enumerate(tier_roles):
            for name, role in roles.items():
                if f"〔 {tier}" in name or f"「 {tier}" in name: # Precise matching
                    has_access = i >= start_index
                    if is_voice:
                        overwrites[role] = discord.PermissionOverwrite(
                            view_channel=True, connect=has_access, speak=has_access, stream=has_access
                        )
                    else:
                        overwrites[role] = discord.PermissionOverwrite(
                            view_channel=has_access, send_messages=has_access if not is_read_only else False,
                            read_message_history=has_access, embed_links=has_access, attach_files=has_access
                        )

        # Sanctions
        for name, role in roles.items():
            if "SIGNAL LOST" in name:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, connect=False)

        return overwrites

    @app_commands.command(name="setup_elysium", description="One-Click REDO: Purge and rebuild the Elite Elysium protocol")
    @app_commands.checks.has_permissions(administrator=True)
    @elite_only()
    async def setup_elysium(self, interaction: discord.Interaction):
        """The definitive server transformation command."""
        
        overview_embed = discord.Embed(
            title="⚜️ ELITE ELYSIUM: Sovereign Singularity",
            description=(
                "**URGENT AUTHORIZATION REQUIRED**\n\n"
                "This command will **PURGE EVERYTHING** and rebuild the server with the **Elysium Sovereign Protocol**.\n\n"
                "**◈ INFRASTRUCTURE:** All Channels & Categories (Text/Voice) will be reset.\n"
                "**◈ HIERARCHY:** All Roles will be wiped and replaced with God-Tier status roles.\n"
                "**◈ PERMISSIONS:** Every channel will be surgically locked to its prestige tier.\n\n"
                "⚠️ **This action is destructive and irreversible.**"
            ),
            color=discord.Color.from_rgb(255, 255, 255)
        )

        class ConfirmView(discord.ui.View):
            def __init__(self, interaction_orig):
                super().__init__(timeout=60)
                self.interaction_orig = interaction_orig
                self.confirmed = False

            @discord.ui.button(label="AUTHORIZE REDO", style=discord.ButtonStyle.danger)
            async def confirm(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.interaction_orig.user.id:
                    return await btn_interaction.response.send_message("Only the Creator can authorize.", ephemeral=True)
                self.confirmed = True
                await btn_interaction.response.edit_message(content="⚙️ **Singularity Initialized. Wiping Reality...**", embed=None, view=None)
                self.stop()

            @discord.ui.button(label="ABORT", style=discord.ButtonStyle.secondary)
            async def cancel(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                await btn_interaction.response.edit_message(content="❌ **Protocol Aborted.**", embed=None, view=None)
                self.stop()

        view = ConfirmView(interaction)
        await interaction.response.send_message(embed=overview_embed, view=view, ephemeral=True)
        await view.wait()

        if not view.confirmed: return

        guild = interaction.guild
        protected_channel = interaction.channel

        # Create Terminal
        terminal_embed = discord.Embed(
            title="[ 🛰️ ] SOVEREIGN SYSTEM TERMINAL",
            description="```access\n> INITIALIZING REDO PROTOCOL...\n```",
            color=0
        )
        terminal_msg = await interaction.channel.send(embed=terminal_embed)
        
        async def update_terminal(log_line):
            current = terminal_embed.description.replace("```access\n", "").replace("\n```", "")
            terminal_embed.description = f"```access\n{current}\n> {log_line}\n```"
            await terminal_msg.edit(embed=terminal_embed)

        # 1. Surgical Wipe
        await update_terminal("PURGING CHANNELS...")
        for c in guild.channels:
            if c.id != protected_channel.id:
                try: await c.delete()
                except: pass
        
        await update_terminal("PURGING ROLES...")
        for r in guild.roles:
            if not r.is_default() and not r.managed:
                try: await r.delete()
                except: pass
        
        await asyncio.sleep(2)
        await update_terminal("SERVER PRISTINE. ARCHITECTING REALITY...")

        # 2. Architect Roles
        roles_config = [
            ("「 ⟡ 」THE ARCHITECT", discord.Color.from_rgb(255, 255, 255), True),
            ("「 ⚖️ 」THE ARBITER", discord.Color.from_rgb(200, 200, 200), True),
            ("「 💾 」SYSTEM CORE", discord.Color.from_rgb(80, 80, 80), False),
            ("〔 Ω 〕ETERNAL", discord.Color.from_rgb(255, 255, 255), False),
            ("〔 Ψ 〕MYSTIC", discord.Color.from_rgb(220, 220, 220), False),
            ("〔 Φ 〕SYNDICATE", discord.Color.from_rgb(180, 180, 180), False),
            ("〔 Σ 〕TITAN", discord.Color.from_rgb(140, 140, 140), False),
            ("〔 Δ 〕ELITE", discord.Color.from_rgb(100, 100, 100), False),
            ("〔 Λ 〕NOBLE", discord.Color.from_rgb(70, 70, 70), False),
            ("〔 Ζ 〕CITIZEN", discord.Color.from_rgb(45, 45, 47), False),
            ("〔 ⟡ 〕GUEST", discord.Color.from_rgb(30, 30, 30), False),
            ("🧬 GENETICIST", discord.Color.green(), False),
            ("💎 DIAMOND LUNGS", discord.Color.cyan(), False),
            ("🔥 SOLAR FLARE", discord.Color.gold(), False),
            ("🤝 THE CONNECT", discord.Color.red(), False),
            ("• Indigo Aura", discord.Color.blue(), False),
            ("• Solar Aura", discord.Color.gold(), False),
            ("• Harmonic Aura", discord.Color.green(), False),
            ("〔 ✧ 〕OBSIDIAN", discord.Color.from_rgb(10, 10, 10), False),
            ("〔 ✧ 〕DIAMOND", discord.Color.from_rgb(255, 255, 255), False),
            ("〔 ✧ 〕NEON VIOLET", discord.Color.from_rgb(180, 0, 255), False),
            ("〔 ✧ 〕ELECTRIC BLUE", discord.Color.from_rgb(0, 200, 255), False),
            ("〔 ✧ 〕LIQUID GOLD", discord.Color.from_rgb(255, 215, 0), False),
            ("[ SIGNAL LOST ]", discord.Color.from_rgb(40, 20, 20), False)
        ]

        for name, color, admin in roles_config:
            perms = discord.Permissions.all() if admin else discord.Permissions.general()
            await guild.create_role(name=name, color=color, permissions=perms, hoist=True)
            await asyncio.sleep(0.1)
        await update_terminal("GOD-TIER HIERARCHY DEPLOYED.")

        # 3. Architect Channels
        await update_terminal("CONSTRUCTING DISTRICTS...")
        structure = [
            ("◌ [ INITIALIZATION ]", [
                ("󠇲 ┇ ◌ synapse", True, "GUEST", False),
                ("󠇲 ┇ ◌ protocol", True, "GUEST", False),
                ("󠇲 ┇ ◌ directory", True, "GUEST", False)
            ]),
            ("◌ [ SOCIAL DISTRICT ]", [
                ("󠇲 ┇ ◌ the-lounge", False, "GUEST", False),
                ("󠇲 ┇ ◌ gallery", False, "GUEST", False),
                ("󠇲 ┇ ◌ soundstage", False, "GUEST", False)
            ]),
            ("◌ [ THE EXCHANGE ]", [
                ("󠇲 ┇ ◌ cultivation", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ the-boutique", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ trade-hub", False, "CITIZEN", False)
            ]),
            ("◌ [ HIGH-ROLLER DEN ]", [
                ("󠇲 ┇ ◌ the-slots", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ table-games", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ black-label", False, "ELITE", False)
            ]),
            ("◌ [ AUDIO DISTRICT ]", [
                ("󠇲 ┇ ◌ lounge-vc", False, "CITIZEN", True),
                ("󠇲 ┇ ◌ chill-sesh", False, "CITIZEN", True),
                ("󠇲 ┇ ◌ sanctum-vc", False, "ELITE", True)
            ]),
            ("◌ [ THE PRIVÉ ]", [
                ("󠇲 ┇ ◌ the-vault", False, "NOBLE", False),
                ("󠇲 ┇ ◌ the-penthouse", False, "TITAN", False)
            ]),
            ("◌ [ SYSTEM CORE ]", [
                ("󠇲 ┇ ◌ overseer-comms", False, "ARBITER", False),
                ("󠇲 ┇ ◌ terminal-logs", True, "ARBITER", False)
            ])
        ]

        for cat_name, channels in structure:
            category = await guild.create_category(cat_name)
            for ch_name, read_only, tier, is_vc in channels:
                overwrites = await self.get_sovereign_overwrites(guild, tier, read_only, is_vc)
                if is_vc:
                    ch = await guild.create_voice_channel(ch_name, category=category, overwrites=overwrites)
                else:
                    ch = await guild.create_text_channel(ch_name, category=category, overwrites=overwrites)
                    
                    if "synapse" in ch_name:
                        await ch.send(embed=discord.Embed(title="🎭 NEURAL AURA", description="Select your frequency.", color=0xFFFFFF), view=RoleView())
                        await ch.send(embed=discord.Embed(title="🎨 CHROMATIC SPECTRUM", description="Sync your visual aura.", color=0xFFFFFF), view=ColorView())
                    if "protocol" in ch_name:
                        await ch.send(embed=discord.Embed(title="📜 SOVEREIGN PROTOCOL", description="◈ RESPECT THE HIGH VIBE\n◈ QUALITY OVER QUANTITY", color=0xFFFFFF))
                    if "directory" in ch_name:
                        dir_embed = discord.Embed(
                            title="🗂️ SOVEREIGN DIRECTORY",
                            description="Mapping of frequencies and access levels within the Elysium.",
                            color=0xFFFFFF
                        )
                        dir_embed.add_field(name="〔 ⟡ 〕GUEST (LV 0+)", value="🔓 `INITIALIZATION`, `SOCIAL`", inline=False)
                        dir_embed.add_field(name="〔 Ζ 〕CITIZEN (LV 10+)", value="🔓 `THE EXCHANGE`, `HIGH-ROLLER`, `AUDIO` (Basic)", inline=False)
                        dir_embed.add_field(name="〔 Λ 〕NOBLE (LV 20+)", value="🔓 `#the-vault` (VIP Social)", inline=False)
                        dir_embed.add_field(name="〔 Δ 〕ELITE (LV 30+)", value="🔓 `#black-label`, `#sanctum-vc`", inline=False)
                        dir_embed.add_field(name="〔 Σ 〕TITAN (LV 40+)", value="🔓 `#the-penthouse` (Pinnacle Access)", inline=False)
                        dir_embed.add_field(name="〔 Φ 〕SYNDICATE (LV 50+)", value="◈ **High Society Status**", inline=False)
                        dir_embed.add_field(name="〔 Ω 〕ETERNAL (LV 100+)", value="◈ **Sovereign Singularity**", inline=False)
                        await ch.send(embed=dir_embed)

                await asyncio.sleep(0.1)

        await update_terminal("SINGULARITY ONLINE. REDO COMPLETE.")
        await asyncio.sleep(5)
        await protected_channel.delete()

    @app_commands.command(name="redo_infrastructure", description="Surgical REDO: Purge and rebuild all Channels & VCs (Preserves Roles)")
    @app_commands.checks.has_permissions(administrator=True)
    @elite_only()
    async def redo_infrastructure(self, interaction: discord.Interaction):
        """Resets only the channel architecture while keeping roles intact."""
        
        overview_embed = discord.Embed(
            title="🛰️ INFRASTRUCTURE REALIGNMENT PROTOCOL",
            description=(
                "**AUTHORIZATION REQUIRED**\n\n"
                "This command will **PURGE ALL CHANNELS** and rebuild the Sovereign HUD.\n"
                "◈ **ROLES:** Will be preserved.\n"
                "◈ **CHANNELS:** All Text and Voice frequencies will be reset.\n"
                "◈ **PERMISSIONS:** Will be re-synced to the Sovereign Matrix.\n\n"
                "⚠️ **This action will wipe all message history.**"
            ),
            color=discord.Color.from_rgb(0, 200, 255)
        )

        class ConfirmView(discord.ui.View):
            def __init__(self, interaction_orig):
                super().__init__(timeout=60)
                self.interaction_orig = interaction_orig
                self.confirmed = False

            @discord.ui.button(label="AUTHORIZE REALIGNMENT", style=discord.ButtonStyle.primary)
            async def confirm(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.interaction_orig.user.id: return
                self.confirmed = True
                await btn_interaction.response.edit_message(content="⚙️ **Realignment Initialized...**", embed=None, view=None)
                self.stop()

            @discord.ui.button(label="ABORT", style=discord.ButtonStyle.secondary)
            async def cancel(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                await btn_interaction.response.edit_message(content="❌ **Protocol Aborted.**", embed=None, view=None)
                self.stop()

        view = ConfirmView(interaction)
        await interaction.response.send_message(embed=overview_embed, view=view, ephemeral=True)
        await view.wait()

        if not view.confirmed: return

        guild = interaction.guild
        protected_channel = interaction.channel

        # Create Terminal
        terminal_embed = discord.Embed(
            title="[ 🛰️ ] INFRASTRUCTURE TERMINAL",
            description="```access\n> INITIATING REALIGNMENT...\n```",
            color=0
        )
        terminal_msg = await interaction.channel.send(embed=terminal_embed)
        
        async def update_terminal(log_line):
            current = terminal_embed.description.replace("```access\n", "").replace("\n```", "")
            terminal_embed.description = f"```access\n{current}\n> {log_line}\n```"
            await terminal_msg.edit(embed=terminal_embed)

        # 1. Purge Channels
        await update_terminal("DECONSTRUCTING EXISTING DISTRICTS...")
        for c in guild.channels:
            if c.id != protected_channel.id:
                try: await c.delete()
                except: pass
        
        await asyncio.sleep(1)
        await update_terminal("INFRASTRUCTURE PURGED. REBUILDING HUD...")

        # 2. Rebuild structure (Using the identical matrix from setup_elysium)
        structure = [
            ("◌ [ INITIALIZATION ]", [
                ("󠇲 ┇ ◌ synapse", True, "GUEST", False),
                ("󠇲 ┇ ◌ protocol", True, "GUEST", False),
                ("󠇲 ┇ ◌ directory", True, "GUEST", False)
            ]),
            ("◌ [ SOCIAL DISTRICT ]", [
                ("󠇲 ┇ ◌ the-lounge", False, "GUEST", False),
                ("󠇲 ┇ ◌ gallery", False, "GUEST", False),
                ("󠇲 ┇ ◌ soundstage", False, "GUEST", False)
            ]),
            ("◌ [ THE EXCHANGE ]", [
                ("󠇲 ┇ ◌ cultivation", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ the-boutique", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ trade-hub", False, "CITIZEN", False)
            ]),
            ("◌ [ HIGH-ROLLER DEN ]", [
                ("󠇲 ┇ ◌ the-slots", False, "GUEST", False),
                ("󠇲 ┇ ◌ table-games", False, "CITIZEN", False),
                ("󠇲 ┇ ◌ black-label", False, "ELITE", False)
            ]),
            ("◌ [ AUDIO DISTRICT ]", [
                ("󠇲 ┇ ◌ lounge-vc", False, "GUEST", True),
                ("󠇲 ┇ ◌ chill-sesh", False, "CITIZEN", True),
                ("󠇲 ┇ ◌ sanctum-vc", False, "ELITE", True)
            ]),
            ("◌ [ THE PRIVÉ ]", [
                ("󠇲 ┇ ◌ the-vault", False, "NOBLE", False),
                ("󠇲 ┇ ◌ the-penthouse", False, "TITAN", False)
            ]),
            ("◌ [ SYSTEM CORE ]", [
                ("󠇲 ┇ ◌ overseer-comms", False, "ARBITER", False),
                ("󠇲 ┇ ◌ terminal-logs", True, "ARBITER", False)
            ])
        ]

        for cat_name, channels in structure:
            category = await guild.create_category(cat_name)
            for ch_name, read_only, tier, is_vc in channels:
                overwrites = await self.get_sovereign_overwrites(guild, tier, read_only, is_vc)
                if is_vc:
                    await guild.create_voice_channel(ch_name, category=category, overwrites=overwrites)
                else:
                    ch = await guild.create_text_channel(ch_name, category=category, overwrites=overwrites)
                    # Redeply essential messages
                    if "synapse" in ch_name:
                        await ch.send(embed=discord.Embed(title="🎭 NEURAL AURA", description="Select your frequency.", color=0xFFFFFF), view=RoleView())
                        await ch.send(embed=discord.Embed(title="🎨 CHROMATIC SPECTRUM", description="Sync your visual aura.", color=0xFFFFFF), view=ColorView())
                    if "protocol" in ch_name:
                        await ch.send(embed=discord.Embed(title="📜 SOVEREIGN PROTOCOL", description="◈ RESPECT THE HIGH VIBE\n◈ QUALITY OVER QUANTITY", color=0xFFFFFF))
                    if "directory" in ch_name:
                        await ch.send(embed=discord.Embed(title="🗂️ DIRECTORY", description="LV 0: GUEST\nLV 10: CITIZEN\nLV 20: NOBLE\nLV 30: ELITE\nLV 50: TITAN", color=0xFFFFFF))
            
            await update_terminal(f"DISTRICT {cat_name} RESTORED.")
            await asyncio.sleep(0.2)

        await update_terminal("HUD REALIGNMENT COMPLETE.")
        await asyncio.sleep(5)
        await protected_channel.delete()

    @app_commands.command(name="role_all", description="SOVEREIGN MANDATE: Synchronize all subjects to a specific frequency")
    @app_commands.checks.has_permissions(administrator=True)
    @elite_only()
    async def role_all(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        
        if interaction.guild.me.top_role <= role:
            return await interaction.followup.send("❌ **Neural Link Failed.** Role frequency is too high for my current protocols.", ephemeral=True)
            
        members = [m for m in interaction.guild.members if not m.bot and role not in m.roles]
        count = 0
        for m in members:
            try: 
                await m.add_roles(role)
                count += 1
            except: pass
            
        await interaction.followup.send(f"✅ **Mandate Executed.** Frequency `{role.name}` stabilized for **{count}** subjects.", ephemeral=True)

    @app_commands.command(name="appoint_staff", description="SOVEREIGN MANDATE: Elevate a subject to the Staff Hierarchy")
    @app_commands.describe(member="The subject to elevate", position="Staff position to assign")
    @app_commands.choices(position=[
        app_commands.Choice(name="Architect (Supreme)", value="architect"),
        app_commands.Choice(name="Arbiter (Justice)", value="arbiter"),
        app_commands.Choice(name="System Core (Dev)", value="core")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    @elite_only()
    async def appoint_staff(self, interaction: discord.Interaction, member: discord.Member, position: str):
        valid = {
            "architect": "「 ⟡ 」THE ARCHITECT", 
            "arbiter": "「 ⚖️ 」THE ARBITER", 
            "core": "「 💾 」SYSTEM CORE"
        }
        role_name = valid.get(position)
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        
        if not role: 
            return await interaction.response.send_message("❌ **Neural Error.** Staff role not found in this sector.", ephemeral=True)
            
        await member.add_roles(role)
        
        embed = discord.Embed(
            title="⚜️ STAFF APPOINTMENT",
            description=f"Subject {member.mention} has been elevated to the rank of **{role_name}**.",
            color=role.color
        )
        embed.set_footer(text="Elysium Sovereignty Protocol")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="open_frequency", description="SOVEREIGN PROTOCOL: Establish a new localized voice frequency")
    @app_commands.describe(name="The name of the new frequency", tier="Required Access Tier (e.g. ELITE)")
    @app_commands.checks.has_permissions(manage_channels=True)
    @elite_only()
    async def open_frequency(self, interaction: discord.Interaction, name: str, tier: str = "GUEST"):
        valid_tiers = ["GUEST", "CITIZEN", "NOBLE", "ELITE", "TITAN", "SYNDICATE", "MYSTIC", "ETERNAL", "ARBITER"]
        if tier.upper() not in valid_tiers:
            return await interaction.response.send_message(f"❌ **Invalid Access Tier.** Choose from: `{', '.join(valid_tiers)}`", ephemeral=True)

        guild = interaction.guild
        overwrites = await self.get_sovereign_overwrites(guild, tier.upper(), False, True)
        
        # Try to find Audio category
        category = discord.utils.get(guild.categories, name="◌ [ AUDIO DISTRICT ]")
        
        ch = await guild.create_voice_channel(f"󠇲 ┇ ◌ {name.lower()}", category=category, overwrites=overwrites)
        await interaction.response.send_message(f"📡 **Frequency established:** {ch.mention}\nAccess Protocol: `{tier.upper()}+`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
