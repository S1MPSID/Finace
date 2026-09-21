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
        options = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
            "socketTimeoutMS": 120000,
            "retryWrites": True,
            "retryReads": True,
        }
        try:
            _client = MongoClient(settings.mongo_uri, **options)
            _client.admin.command("ping")
        except Exception:
            if not settings.mongo_fallback_uri:
                raise
            _client = MongoClient(settings.mongo_fallback_uri, **options)
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
