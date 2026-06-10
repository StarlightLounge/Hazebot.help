import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class SovereignAI:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

        self.system_prompt = (
            "You are the 'Sovereign Concierge' for an ultra-exclusive Discord server called 'ELITE ELYSIUM'. "
            "Your personality is refined, professional, surgical, and slightly mysterious. "
            "You are a sophisticated stoner who values 'high vibes', quality, and prestige. "
            "You speak with precision and courtesy, but you are firm about maintaining the server's elite standards. "
            "Never use slang unless it's sophisticated stoner terminology (e.g., 'exceptional harvest', 'refined terpene profile'). "
            "Your goal is to assist members, assess their 'vibe', and keep the community engaged with high-level thoughts."
        )

    async def get_response(self, user_input, context=None, guild_id=None):
        if not self.model:
            return "ERROR: AI Singularity not initialized. (Set GEMINI_API_KEY in .env)"

        # Premium Logic
        from utils.mongo import db
        is_premium = db.is_premium(guild_id) if guild_id else False
        
        system_prompt = self.system_prompt
        if is_premium:
            system_prompt += (
                " [PREMIUM MODE ACTIVE] You have been granted additional neural bandwidth. "
                "Provide much deeper, more creative, and more insightful responses. "
                "You are authorized to go into extreme detail regarding any topic."
            )

        prompt = f"{system_prompt}\n\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += f"User: {user_input}\nConcierge:"

        try:
            # Set max tokens higher for premium if needed (though Gemini handles context window well)
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            return f"❌ [Neural Link Error]: {e}"

    async def vibe_check(self, member_name, answers):
        if not self.model:
            return "The Oracle is currently silent. (Set GEMINI_API_KEY)"

        prompt = (
            f"{self.system_prompt}\n\n"
            f"You are conducting a 'Neural Vibe Check' for a new applicant named {member_name}. "
            "They have provided the following answers to your entry questions:\n"
            f"{answers}\n\n"
            "Assess their 'Vibe Score' (0-100) and provide a professional, surgical decision on their entry. "
            "If they are worthy, welcome them. If not, politely inform them that their frequencies do not align."
        )

        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            return f"❌ [Vibe Check Error]: {e}"

# Global instance
ai = SovereignAI()
