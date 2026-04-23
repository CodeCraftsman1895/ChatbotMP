from pymongo import MongoClient
from app.config.settings import MONGO_URI, DB_NAME

if not MONGO_URI:
    raise RuntimeError(
        'MONGO_URI is not set. Add it to your environment or project `.env` (see `.env.example`).'
    )

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
spaces_col = db["spaces"]
contents_col = db["contents"]