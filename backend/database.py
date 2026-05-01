import os
from pymongo import MongoClient
import gridfs
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['GenaiProject']
fs = gridfs.GridFS(db) # GridFS for file storage

# Collections
users_collection = db['users']
documents_collection = db['documents']
chunks_collection = db['chunks']
query_logs_collection = db['query_logs']
chats_collection = db['chats'] # NEW: Conversation storage
notes_collection = db['notes'] # NEW: Generated notes storage
quizzes_collection = db['quizzes'] # NEW: Generated quizzes storage

# Ensure Indexes (Optional but good for performance)
try:
    users_collection.create_index("email", unique=True)
    # Vector index must be created manually in Atlas UI
except:
    pass
