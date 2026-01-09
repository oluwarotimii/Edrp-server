from redis import asyncio as aioredis
from config import settings
import json
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        "Connect to Redis"
        try:
            self.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        "Disconnect from Redis"
        if self.redis:
            await self.redis.close()
    
    async def set(self, key: str, value: str, expire: int = None):
        "Set a key-value pair in Redis"
        try:
            if expire:
                await self.redis.setex(key, expire, value)
            else:
                await self.redis.set(key, value)
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")
    
    async def get(self, key: str):
        "Get a value from Redis"
        try:
            value = await self.redis.get(key)
            return value
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None
    
    async def delete(self, key: str):
        "Delete a key from Redis"
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")
    
    async def publish(self, channel: str, message: str):
        "Publish a message to a Redis channel"
        try:
            await self.redis.publish(channel, message)
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
    
    async def set_json(self, key: str, value: dict, expire: int = None):
        "Set a JSON object in Redis"
        try:
            json_value = json.dumps(value)
            await self.set(key, json_value, expire)
        except Exception as e:
            logger.error(f"Error setting JSON key {key} in Redis: {e}")
    
    async def get_json(self, key: str):
        "Get a JSON object from Redis"
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key} from Redis: {e}")
            return None

# Global Redis client instance
redis_client = RedisClient()
