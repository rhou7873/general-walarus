from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId
import os

CONNECTION_STRING: str = str(os.getenv("DB_CONN_STRING"))
db = MongoClient(CONNECTION_STRING).general_walarus


def log(discord_server, collection, data): return collection.update_one(
    {"_id": discord_server.id}, {"$set": data}, upsert=True).upserted_id != None


DATE_ID = ObjectId(os.getenv("ARCHIVE_DATE_ID"))
