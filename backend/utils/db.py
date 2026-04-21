93% of storage used … If you run out, you can't create, edit and upload files. Share 100 GB of storage with your family members for ₹59 for 1 month ₹130.
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
BASE_DIR = Path(__file__).resolve().parents[1]
LOCAL_DB_PATH = BASE_DIR / "data" / "local_db.json"


class LocalCollection:
    def __init__(self, path, collection_name):
        self.path = Path(path)
        self.collection_name = collection_name
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"users": [], "results": []}, indent=2), encoding="utf-8")

    def _read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data):
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def find_one(self, query):
        records = self._read().get(self.collection_name, [])
        for record in records:
            if all(record.get(key) == value for key, value in query.items()):
                return record
        return None

    def insert_one(self, document):
        data = self._read()
        data.setdefault(self.collection_name, []).append(document)
        self._write(data)
        return {"inserted_id": len(data[self.collection_name]) - 1}


def _mongo_collections():
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is not defined in environment variables")

    from pymongo import MongoClient

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    client.admin.command("ping")
    db = client["emotion_app"]
    return db["users"], db["results"]


try:
    users, results = _mongo_collections()
except Exception as exc:
    print(f"Using local JSON storage because MongoDB is unavailable: {exc}")
    users = LocalCollection(LOCAL_DB_PATH, "users")
    results = LocalCollection(LOCAL_DB_PATH, "results")