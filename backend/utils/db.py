from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise RuntimeError("MONGO_URI is not defined in environment variables")

# Connect to MongoDB
client = MongoClient(mongo_uri)

# Create database
db = client["emotion_app"]

# Collections
users = db["users"]
results = db["results"]