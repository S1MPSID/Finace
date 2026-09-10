from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import settings


_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=20000,
            socketTimeoutMS=120000,
            retryWrites=True,
            retryReads=True,
        )
        # Verify connection on first use
        _client.admin.command("ping")
    return _client


def get_db() -> Database:
    return get_client()[settings.mongo_db]


def get_collection(name: str) -> Collection:
    return get_db()[name]


# Convenience accessors
def documents() -> Collection:
    return get_collection("documents")


def chunks() -> Collection:
    return get_collection("chunks")


def users() -> Collection:
    return get_collection("users")


def reports() -> Collection:
    return get_collection("reports")
