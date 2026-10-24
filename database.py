import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
import pymongo
from bson import ObjectId

# Load from .env if present
ENV_FILE = Path(__file__).resolve().parent / ".env"
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass


def get_mongo_config():
    # 1. Try streamlit secrets if running inside streamlit
    try:
        import streamlit as st
        if "mongo" in st.secrets:
            return st.secrets["mongo"].get("uri"), st.secrets["mongo"].get("database", "mia_database")
    except Exception:
        pass

    # 2. Try environment variables
    uri = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://satyachikkaraju2016_db_user:2sNPz6PwIHjYrjst@mia.ed8ovhf.mongodb.net/?retryWrites=true&w=majority"
    )
    db_name = os.environ.get("MONGO_DB_NAME", "mia_database")
    return uri, db_name


_client = None


def get_db():
    global _client
    if _client is None:
        uri, db_name = get_mongo_config()
        _client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    _, db_name = get_mongo_config()
    return _client[db_name]


def init_db():
    try:
        db = get_db()
        # Create unique index on email
        db.users.create_index("email", unique=True)
        # Create index on user_id and session_id for fast queries
        db.conversations.create_index([("user_id", pymongo.ASCENDING), ("timestamp", pymongo.ASCENDING)])
        db.conversations.create_index([("session_id", pymongo.ASCENDING)])
    except Exception as e:
        print(f"MongoDB init warning: {e}")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + hashed.hex()


def verify_password(stored_password: str, provided_password: str) -> bool:
    try:
        salt_hex, hash_hex = stored_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100_000).hex()
        return hash_hex == expected_hash
    except Exception:
        return False


def validate_email(email: str) -> bool:
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email):
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    domain = parts[1]
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        return False
    tld = domain.split(".")[-1]
    if len(tld) < 2:
        return False
    return True


def register_user(name: str, email: str, password: str, confirm_password: str = None):
    name = (name or "").strip()
    email = (email or "").strip().lower()

    if not name:
        return False, "Please enter your name.", None
    if len(name) < 2:
        return False, "Name must be at least 2 characters long.", None

    if not email:
        return False, "Please enter your email address.", None
    if not validate_email(email):
        return False, "Please enter a valid email address (e.g. user@example.com).", None

    if not password:
        return False, "Please enter a password.", None
    if len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    if confirm_password is not None and password != confirm_password:
        return False, "Passwords do not match. Please re-enter.", None

    try:
        db = get_db()
        existing = db.users.find_one({"email": email})
        if existing:
            return False, "An account with this email already exists. Please log in.", None

        pw_hash = hash_password(password)
        doc = {
            "name": name,
            "email": email,
            "password_hash": pw_hash,
            "created_at": datetime.now()
        }
        res = db.users.insert_one(doc)
        user = {"id": str(res.inserted_id), "name": name, "email": email}
        return True, "Registration successful!", user
    except pymongo.errors.DuplicateKeyError:
        return False, "An account with this email already exists. Please log in.", None
    except Exception as e:
        return False, f"Database error: {str(e)}", None


def login_user(email: str, password: str):
    email = (email or "").strip().lower()
    if not email or not password:
        return False, "Please enter both email and password.", None

    if not validate_email(email):
        return False, "Please enter a valid email address.", None

    try:
        db = get_db()
        user_doc = db.users.find_one({"email": email})
        if not user_doc:
            return False, "No account found with this email. Please register.", None

        if not verify_password(user_doc["password_hash"], password):
            return False, "Incorrect password. Please try again.", None

        user = {
            "id": str(user_doc["_id"]),
            "name": user_doc["name"],
            "email": user_doc["email"]
        }
        return True, "Login successful!", user
    except Exception as e:
        return False, f"Login error: {str(e)}", None


def save_message(user_id: str, session_id: str, role: str, content: str, intent: str = None):
    try:
        db = get_db()
        doc = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "role": role,
            "content": content,
            "intent": intent,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        db.conversations.insert_one(doc)
    except Exception as e:
        print(f"Error saving message to MongoDB: {e}")


def archive_session(user_id: str, session_id: str, messages: list):
    """
    Saves non-welcome messages in a session to conversations if not already stored.
    """
    if not messages:
        return
    try:
        db = get_db()
        count = db.conversations.count_documents({"user_id": str(user_id), "session_id": str(session_id)})
        if count == 0:
            docs = []
            for msg in messages:
                docs.append({
                    "user_id": str(user_id),
                    "session_id": str(session_id),
                    "role": msg["role"],
                    "content": msg["content"],
                    "intent": msg.get("intent"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            if docs:
                db.conversations.insert_many(docs)
    except Exception as e:
        print(f"Error archiving session to MongoDB: {e}")


def get_user_history(user_id: str):
    """
    Returns list of sessions with their messages grouped together, newest session first.
    """
    try:
        db = get_db()
        cursor = db.conversations.find({"user_id": str(user_id)}).sort("timestamp", pymongo.ASCENDING)

        sessions = {}
        for r in cursor:
            sid = r["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "started_at": r.get("timestamp", "Previous Session"),
                    "messages": []
                }
            sessions[sid]["messages"].append({
                "role": r["role"],
                "content": r["content"],
                "intent": r.get("intent"),
                "timestamp": r.get("timestamp")
            })

        return list(reversed(list(sessions.values())))
    except Exception as e:
        print(f"Error retrieving history from MongoDB: {e}")
        return []


# Initialize database and indexes
init_db()
