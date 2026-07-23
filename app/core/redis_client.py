# app/core/redis_client.py
import os
import redis
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)