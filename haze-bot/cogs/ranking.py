import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
from utils.logic import sync_member_roles, elite_only

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show the top hazers in the server")
    @elite_only()
    async def leaderboard(self, interaction: discord.Interaction, sort_by: str = "hash_coins"):
        """Sort by: hash_coins, puff_count, level"""
        valid_sorts = ["hash_coins", "puff_count", "level"]
        if sort_by not in valid_sorts:
            return await interaction.response.send_message(f"❌ Invalid sort! Use: {', '.join(valid_sorts)}", ephemeral=True)

        users = db.get_leaderboard(interaction.guild_id, sort_by=sort_by)

        embed = discord.Embed(
            title=f"🏆 Server Leaderboard ({sort_by.replace('_', ' ').title()})",
            color=discord.Color.gold()
        )

        for i, user in enumerate(users, 1):
            member = interaction.guild.get_member(int(user["user_id"]))
            name = member.name if member else f"User {user['user_id']}"
            value = user.get(sort_by, 0)
            embed.add_field(name=f"{i}. {name}", value=f"`{value:,}`", inline=False)

        if not users:
            embed.description = "No one has been hazy yet."

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="prestige", description="Ascend to the next level of existence (Resets Level to 1)")
    @elite_only()
    async def prestige(self, interaction: discord.Interaction):
        """Ascends a user if they are at max level."""
        user = db.get_user(interaction.user.id, interaction.guild_id)
        current_level = user.get("level", 1)

        # Require Level 100 to Prestige
        if current_level < 100:
            return await interaction.response.send_message(
                f"❌ **Ascension Denied.** You are currently at Tier {current_level}. You must reach **Tier 100** to Prestige.",
                ephemeral=True
            )

        class PrestigeConfirm(discord.ui.View):
            def __init__(self, user_id):
                super().__init__(timeout=60)
                self.user_id = user_id
                self.confirmed = False

            @discord.ui.button(label="ASCEND", style=discord.ButtonStyle.danger)
            async def confirm(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != self.user_id: return
                self.confirmed = True
                await btn_interaction.response.edit_message(content="✨ **Initializing Ascension...**", embed=None, view=None)
                self.stop()

        view = PrestigeConfirm(interaction.user.id)
        await interaction.response.send_message(
            "⚠️ **ASCENSION WARNING**\n\n"
            "By prestiging, your **Tier will reset to 1**. In exchange, you will receive:\n"
            "◈ A permanent **Prestige Badge** on your profile.\n"
            "◈ A **1.5x Multiplier** on all Influence gains.\n"
            "◈ A higher standing in the **Sovereign Singularity**.\n\n"
            "Are you ready to transcend?",
            view=view,
            ephemeral=True
        )

        await view.wait()
        if not view.confirmed: return

        # Perform Prestige
        new_prestige = user.get("prestige", 0) + 1
        db.update_user(interaction.user.id, interaction.guild_id, {
            "level": 1,
            "xp": 0,
            "prestige": new_prestige
        })

        # Try to find and give a prestige role if one exists
        prestige_role_name = f"PRESTIGE {new_prestige}"
        role = discord.utils.get(interaction.guild.roles, name=prestige_role_name)
        if not role:
            try:
                role = await interaction.guild.create_role(
                    name=prestige_role_name, 
                    color=discord.Color.gold(), 
                    hoist=True,
                    reason="User Ascended"
                )
            except: pass

        if role:
            try: await interaction.user.add_roles(role)
            except: pass

        # Wipe the tiered roles
        await sync_member_roles(interaction.user, 1)

        embed = discord.Embed(
            title="✨ ASTRAL ASCENSION COMPLETE",
            description=(
                f"**{interaction.user.name}** has transcended to **Prestige {new_prestige}**.\n\n"
                "The Singularity pulses with their new-found frequency."
            ),
            color=discord.Color.from_rgb(255, 255, 255)
        )
        await interaction.followup.send(embed=embed)

    # --- STAFF COMMANDS ---

    @app_commands.command(name="set_level", description="STAFF: Manually set a user's Tier")
    @app_commands.describe(member="The subject to modify", level="The new Tier to assign")
    @app_commands.checks.has_permissions(administrator=True)
    @elite_only()
    async def set_level(self, interaction: discord.Interaction, member: discord.Member, level: int):
        if level < 1: level = 1

        db.update_user(member.id, interaction.guild_id, {"level": level, "xp": 0})
        await sync_member_roles(member, level)

        await interaction.response.send_message(
            f"✅ **Mandate Executed.** {member.mention} has been manually aligned to **Tier {level}**.",
            ephemeral=True
        )

    @app_commands.command(name="add_xp", description="STAFF: Inject XP into a user's neural core")
    @app_commands.describe(member="The subject to modify", xp="Amount of XP to grant")
    @app_commands.checks.has_permissions(administrator=True)
    @elite_only()
    async def add_xp(self, interaction: discord.Interaction, member: discord.Member, xp: int):
        user = db.get_user(member.id, interaction.guild_id)
        current_xp = user.get("xp", 0)
        current_level = user.get("level", 1)

        new_xp = current_xp + xp
        new_level = current_level

        # Level up loop
        while True:
            needed = new_level * 100
            if new_xp >= needed:
                new_xp -= needed
                new_level += 1
            else:
                break

        db.update_user(member.id, interaction.guild_id, {"level": new_level, "xp": new_xp})

        if new_level != current_level:
            await sync_member_roles(member, new_level)
            await interaction.response.send_message(
                f"⚡ **Neural Injection Complete.** {member.mention} gained {xp} XP and ascended to **Tier {new_level}**.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚡ **Neural Injection Complete.** {member.mention} gained {xp} XP.",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Ranking(bot))
