import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI")
        self.connected = False
        
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.connected = True
            print("🔗 [Database] Neural Link Stable (MongoDB Connected)")
        except Exception as e:
            self.client = None
            print(f"❌ [Database] Neural Link FAILED: {e}")
            print("⚠️ BOT OPERATING IN OFFLINE MODE (Data will not save)")

        if self.client is not None:
            self.db = self.client["haze_bot"]
            self.users = self.db["users"]
            self.hazedex = self.db["hazedex"]
            self.guilds = self.db["guilds"]
            self.partners = self.db["partners"]
        else:
            self.db = self.users = self.hazedex = self.guilds = self.partners = None

    def set_partner_hub(self, guild_id, channel_id):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"partner_hub_id": str(channel_id) if channel_id else None}},
            upsert=True
        )

    def get_partner_hub(self, guild_id):
        if not self.connected: return None
        guild = self.guilds.find_one({"guild_id": str(guild_id)})
        return guild.get("partner_hub_id") if guild else None

    def set_affiliate_hub(self, guild_id, channel_id):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"affiliate_hub_id": str(channel_id) if channel_id else None}},
            upsert=True
        )

    def get_affiliate_hub(self, guild_id):
        if not self.connected: return None
        guild = self.guilds.find_one({"guild_id": str(guild_id)})
        return guild.get("affiliate_hub_id") if guild else None

    def add_partner(self, guild_id, name, invite, description):
        if not self.connected: return
        self.partners.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {
                "name": name,
                "invite": invite,
                "description": description,
                "status": "pending",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }},
            upsert=True
        )

    def update_partner_status(self, guild_id, status):
        if not self.connected: return
        self.partners.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"status": status}}
        )

    def get_partners(self, status="approved"):
        if not self.connected: return []
        return list(self.partners.find({"status": status}))

    def remove_partner(self, guild_id):
        if not self.connected: return
        self.partners.delete_one({"guild_id": str(guild_id)})

    def get_user(self, user_id, guild_id):
        if not self.connected:
            return {"user_id": str(user_id), "guild_id": str(guild_id), "hash_coins": 420, "xp": 0, "level": 1, "puff_count": 0, "inventory": [], "hazedex": []}
            
        user = self.users.find_one({"user_id": str(user_id), "guild_id": str(guild_id)})
        if not user:
            user = {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "hash_coins": 420,
                "xp": 0,
                "level": 1,
                "puff_count": 0,
                "pass_count": 0,
                "last_daily": None,
                "daily_streak": 0,
                "last_haze": None,
                "inventory": [],
                "hazedex": []
            }
            self.users.insert_one(user)
        return user

    def update_user(self, user_id, guild_id, data):
        if not self.connected: return
        self.users.update_one(
            {"user_id": str(user_id), "guild_id": str(guild_id)},
            {"$set": data}
        )

    def add_to_hazedex(self, user_id, guild_id, item_name):
        if not self.connected: return
        self.users.update_one(
            {"user_id": str(user_id), "guild_id": str(guild_id)},
            {"$addToSet": {"hazedex": item_name}}
        )

    def remove_from_hazedex(self, user_id, guild_id, item_name):
        if not self.connected: return
        self.users.update_one(
            {"user_id": str(user_id), "guild_id": str(guild_id)},
            {"$pull": {"hazedex": item_name}}
        )

    def set_autorole(self, guild_id, role_id):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"autorole_id": str(role_id) if role_id else None}},
            upsert=True
        )

    def get_autorole(self, guild_id):
        if not self.connected: return None
        guild = self.guilds.find_one({"guild_id": str(guild_id)})
        return guild.get("autorole_id") if guild else None

    def get_leaderboard(self, guild_id, sort_by="hash_coins", limit=10):
        if not self.connected: return []
        return list(self.users.find({"guild_id": str(guild_id)}).sort(sort_by, -1).limit(limit))

    def is_elite_enabled(self, guild_id):
        if not self.connected: return True # Default to enabled if DB is down
        guild = self.guilds.find_one({"guild_id": str(guild_id)})
        if not guild: return True
        return guild.get("elite_mode", True)

    def set_elite_mode(self, guild_id, status):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"elite_mode": status}},
            upsert=True
        )

    def is_premium(self, guild_id):
        if not self.connected: return False
        data = self.guilds.find_one({"guild_id": str(guild_id)})
        return data.get("premium_status", False) if data else False

    def set_premium(self, guild_id, status):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"premium_status": status}},
            upsert=True
        )

    def set_vc_hub(self, guild_id, channel_id):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"vc_hub_id": channel_id}},
            upsert=True
        )

    def get_vc_hub(self, guild_id):
        if not self.connected: return None
        data = self.guilds.find_one({"guild_id": str(guild_id)})
        return data.get("vc_hub_id") if data else None

    def set_stream_hub(self, guild_id, channel_id):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"stream_hub_id": str(channel_id) if channel_id else None}},
            upsert=True
        )

    def get_stream_hub(self, guild_id):
        if not self.connected: return None
        guild = self.guilds.find_one({"guild_id": str(guild_id)})
        return guild.get("stream_hub_id") if guild else None

    def update_stream_profile(self, user_id, guild_id, platform, link):
        if not self.connected: return
        self.users.update_one(
            {"user_id": str(user_id), "guild_id": str(guild_id)},
            {"$set": {"stream_profile": {"platform": platform, "link": link}}}
        )

    def add_warning(self, user_id, guild_id, moderator_id, reason):
        if not self.connected: return None
        import uuid
        warn_id = str(uuid.uuid4())[:8]
        warning = {
            "id": warn_id,
            "reason": reason,
            "moderator_id": str(moderator_id),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.users.update_one(
            {"user_id": str(user_id), "guild_id": str(guild_id)},
            {"$push": {"warnings": warning}},
            upsert=True
        )
        return warning

    def get_warnings(self, user_id, guild_id):
        if not self.connected: return []
        user = self.get_user(user_id, guild_id)
        return user.get("warnings", [])

    def remove_warning(self, user_id, guild_id, warn_id=None):
        if not self.connected: return False
        if warn_id:
            res = self.users.update_one(
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                {"$pull": {"warnings": {"id": warn_id}}}
            )
            return res.modified_count > 0
        else:
            res = self.users.update_one(
                {"user_id": str(user_id), "guild_id": str(guild_id)},
                {"$set": {"warnings": []}}
            )
            return res.modified_count > 0

    def set_welcome_config(self, guild_id, channel_id, text):
        if not self.connected: return
        self.guilds.update_one(
            {"guild_id": str(guild_id)},
            {"$set": {"welcome_channel": str(channel_id) if channel_id else None, "welcome_text": text}},
            upsert=True
        )

    def get_welcome_config(self, guild_id):
        if not self.connected: return None, None
        guild = self.guilds.find_one({"guild_id": str(guild_id)})
        if not guild: return None, None
        return guild.get("welcome_channel"), guild.get("welcome_text")

# Global database instance
db = Database()
