from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
import discord

class ImageGenerator:
    def __init__(self):
        # Professional Palettes
        self.themes = {
            "obsidian": {
                "bg": (5, 5, 5),
                "accent": (253, 185, 49), # Gold
                "text": (255, 255, 255),
                "muted": (80, 80, 80)
            },
            "liquid_gold": {
                "bg": (253, 185, 49),
                "accent": (255, 255, 255),
                "text": (0, 0, 0),
                "muted": (153, 101, 21)
            },
            "neon_haze": {
                "bg": (18, 0, 36),
                "accent": (180, 0, 255), # Violet
                "text": (0, 255, 255), # Cyan
                "muted": (80, 0, 120)
            },
            "emerald": {
                "bg": (2, 20, 2),
                "accent": (46, 204, 113), # Green
                "text": (240, 240, 240),
                "muted": (20, 60, 20)
            }
        }

    async def generate_profile_card(self, user: discord.Member, stats: dict):
        """Generates a professional Digital Membership Card image with themes."""
        # 1. Determine Theme
        theme_key = stats.get("equipped_aura", "obsidian").lower()
        t = self.themes.get(theme_key, self.themes["obsidian"])
        
        # 2. Create base canvas
        card = Image.new('RGB', (800, 450), color=t["bg"])
        draw = ImageDraw.Draw(card)
        
        # 3. Add dynamic border
        draw.rectangle([10, 10, 790, 440], outline=t["accent"], width=2)
        
        # 4. Load & Process Avatar
        try:
            avatar_bytes = await user.display_avatar.read()
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar = avatar.resize((200, 200))
            
            # Circle crop
            mask = Image.new('L', (200, 200), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 200, 200), fill=255)
            avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
            avatar.putalpha(mask)
            
            card.paste(avatar, (50, 125), avatar)
        except: pass

        # 5. Text Drawing
        font = ImageFont.load_default() # Fallback

        # Header Info
        draw.text((300, 80), f"{user.name.upper()}", fill=t["text"], font=font)
        draw.text((300, 110), f"Sovereign Node #{user.discriminator if user.discriminator != '0' else user.id % 9999:04d}", fill=t["accent"])
        
        # Stats Block
        draw.text((300, 170), f"TIER: {stats.get('level', 1)}", fill=t["text"])
        draw.text((300, 200), f"INFLUENCE: {stats.get('hash_coins', 0):,}", fill=t["text"])
        draw.text((300, 230), f"PRESTIGE: {stats.get('prestige', 0)}", fill=t["text"])
        
        # 6. Synergy Progress
        synergy = stats.get('synergy', {'used_categories': []})
        syn_count = len(synergy['used_categories'])
        draw.text((300, 280), f"SYNERGY: {syn_count}/5", fill=t["accent"])
        
        # Visual Progress Bar
        draw.rectangle([300, 310, 600, 320], outline=t["muted"], width=1)
        bar_width = int((syn_count / 5) * 300)
        if bar_width > 0:
            draw.rectangle([300, 310, 300 + bar_width, 320], fill=t["accent"])

        # 7. Elite Badges (Simulated placement)
        if stats.get('premium_status'):
            draw.text((700, 30), "💎 PREMIUM", fill=t["accent"])

        # Footer
        draw.text((600, 410), "ELITE ELYSIUM PROTOCOL", fill=t["muted"])

        # 8. Save to buffer
        buffer = io.BytesIO()
        card.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    async def generate_server_banner(self, guild: discord.Guild, theme_name: str = "obsidian"):
        """Generates an ultra-vibrant High-Pop Server Banner with neon effects."""
        t = self.themes.get(theme_name.lower(), self.themes["obsidian"])
        
        # 1. Create Canvas
        banner = Image.new('RGB', (960, 540), color=(0,0,0)) # Pure black for maximum contrast
        draw = ImageDraw.Draw(banner)
        
        # 2. Deep Space Gradient
        for y in range(540):
            mix = y / 540
            # Stronger color shift for "Pop"
            r = int(t["bg"][0] * (1 - mix) + t["accent"][0] * (mix * 0.15))
            g = int(t["bg"][1] * (1 - mix) + t["accent"][1] * (mix * 0.15))
            b = int(t["bg"][2] * (1 - mix) + t["accent"][2] * (mix * 0.15))
            draw.line([(0, y), (960, y)], fill=(r, g, b))

        # 3. High-Pop Neural Grid + "Data Streams"
        for i in range(0, 960, 80):
            # Vertical streams with random "pulses"
            line_color = t["muted"] if i % 160 == 0 else (int(t["muted"][0]*0.5), int(t["muted"][1]*0.5), int(t["muted"][2]*0.5))
            draw.line([(i, 0), (i, 540)], fill=line_color, width=1)
            # Add "Pulse" blocks
            import random
            if random.random() > 0.7:
                py = random.randint(0, 500)
                draw.rectangle([i-2, py, i+2, py+40], fill=t["accent"])

        # 4. Triple-Layer Neon Border
        draw.rectangle([5, 5, 955, 535], outline=t["accent"], width=1) # Outer Glow
        draw.rectangle([12, 12, 948, 528], outline=t["accent"], width=3) # Main Neon
        draw.rectangle([20, 20, 940, 520], outline=t["text"], width=1) # Inner Highlight
        
        # 5. Load & Process Server Icon (Ultra Glow)
        if guild.icon:
            try:
                icon_bytes = await guild.icon.read()
                icon = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")
                icon = icon.resize((220, 220))
                
                mask = Image.new('L', (220, 220), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 220, 220), fill=255)
                icon = ImageOps.fit(icon, mask.size, centering=(0.5, 0.5))
                icon.putalpha(mask)
                
                # Multi-layer Halo for "Pop"
                for i in range(10, 0, -2):
                    draw.ellipse([370-i, 60-i, 590+i, 280+i], outline=t["accent"], width=1)
                
                banner.paste(icon, (370, 70), icon)
            except: pass

        # 6. Typography Synthesis (High Contrast)
        font = ImageFont.load_default()

        # Neon Glow Text Layer
        title = guild.name.upper()
        draw.text((482, 312), title, fill=t["accent"], font=font, anchor="mm") # Glow Shadow
        draw.text((480, 310), title, fill=t["text"], font=font, anchor="mm") # Main White
        
        # Tech Separator
        draw.rectangle([300, 340, 660, 343], fill=t["accent"])
        
        # Subtitle
        draw.text((480, 375), "NODE_STATUS: ONLINE // ENCRYPTED", fill=t["accent"], font=font, anchor="mm")
        
        # Stats Badges
        stats_text = f"USERS: {guild.member_count} | SECURITY: Lvl.{guild.premium_tier}"
        draw.rectangle([280, 410, 680, 445], outline=t["accent"], width=2)
        draw.text((480, 427), stats_text, fill=t["text"], font=font, anchor="mm")
        
        # Footer
        draw.text((480, 500), f"SYNTHESIZED BY HAZE BOT // ID: {guild.id}", fill=t["muted"], font=font, anchor="mm")

        # 7. Final Buffer Output
        buffer = io.BytesIO()
        banner.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

    async def generate_server_icon(self, guild: discord.Guild, theme_name: str = "obsidian"):
        """Generates an ultra-high contrast Cyber-Icon that 'Pops'."""
        t = self.themes.get(theme_name.lower(), self.themes["obsidian"])
        
        # 1. Canvas
        icon = Image.new('RGB', (512, 512), color=(0,0,0))
        draw = ImageDraw.Draw(icon)
        
        # 2. Concentric Neon Pulse Background
        for i in range(256, 0, -16):
            # Alternate colors for vibration
            color = t["bg"] if (i//16) % 2 == 0 else tuple(int(c * 0.3) for c in t["accent"])
            draw.ellipse([256-i*1.2, 256-i*1.2, 256+i*1.2, 256+i*1.2], outline=color, width=2)

        # 3. Floating Data Particles (Pixel Pop)
        import random
        for _ in range(30):
            px, py = random.randint(50, 460), random.randint(50, 460)
            draw.rectangle([px, py, px+4, py+4], fill=t["accent"])

        # 4. HUD Chassis (3D Look)
        draw.ellipse([35, 35, 477, 477], outline=(50,50,50), width=10) # Heavy Base
        draw.ellipse([40, 40, 472, 472], outline=t["accent"], width=3)  # Neon Rim
        
        # 5. Core Hexagon (Triple Layer Glow)
        points = []
        for i in range(6):
            import math
            angle_rad = math.radians(60 * i - 30)
            points.append((256 + 130 * math.cos(angle_rad), 256 + 130 * math.sin(angle_rad)))
        
        draw.polygon(points, outline=t["accent"], width=8) # Outer Glow
        draw.polygon(points, outline=t["text"], width=2)   # Inner Highlight

        # 6. Initials (Double Glow)
        font = ImageFont.load_default()
        initials = "".join([w[0] for w in guild.name.split() if w])[:3].upper()
        
        draw.text((258, 258), initials, fill=t["accent"], font=font, anchor="mm") # Strong shadow
        draw.text((256, 256), initials, fill=(255,255,255), font=font, anchor="mm") # Vivid White

        # 7. Corner "Sensors"
        s = 40
        draw.rectangle([0, 0, s, s], fill=t["accent"]) # TL
        draw.rectangle([512-s, 0, 512, s], fill=t["accent"]) # TR
        draw.rectangle([0, 512-s, s, 512], fill=t["accent"]) # BL
        draw.rectangle([512-s, 512-s, 512, 512], fill=t["accent"]) # BR

        # 8. Output
        buffer = io.BytesIO()
        icon.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
