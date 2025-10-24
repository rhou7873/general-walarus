from bw_secrets import ARCHIVE_DATE_ID, MONGO_CONN_STRING
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId
import os

db = MongoClient(MONGO_CONN_STRING).general_walarus


def log(discord_server, collection, data): return collection.update_one(
    {"_id": discord_server.id}, {"$set": data}, upsert=True).upserted_id != None


DATE_ID = ObjectId(ARCHIVE_DATE_ID)
