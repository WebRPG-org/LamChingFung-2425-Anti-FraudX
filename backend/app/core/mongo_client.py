import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_agent_db")

if "localhost:27017" in MONGO_CONNECTION_STRING and os.getenv("DOCKER_ENV"):
    MONGO_CONNECTION_STRING = MONGO_CONNECTION_STRING.replace("localhost:27017", "mongo:27017")
    print(f"Fixed MongoDB connection string for Docker: {MONGO_CONNECTION_STRING}")
elif "mongo:27017" in MONGO_CONNECTION_STRING and not os.getenv("DOCKER_ENV"):
    MONGO_CONNECTION_STRING = MONGO_CONNECTION_STRING.replace("mongo:27017", "localhost:27017")
    print(f"Fixed MongoDB connection string for local: {MONGO_CONNECTION_STRING}")

print(f"MongoDB Connection String: {MONGO_CONNECTION_STRING}")
print(f"MongoDB Database Name: {MONGO_DB_NAME}")

class MongoClient:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
        self.db = self.client[MONGO_DB_NAME]
    def get_db(self):
        return self.db
mongo_client = MongoClient()