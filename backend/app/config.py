import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RERANK_MODEL = os.environ.get("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

MEDIASSIST_DATA_DIR = os.environ.get("MEDIASSIST_DATA_DIR", "./data/mediassist_data")
QDRANT_PATH = os.environ.get("QDRANT_PATH", "./qdrant_storage")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "medibot_hybrid")

# Chunking
CHUNK_MAX_TOKENS = 256

# Which collection folder each role can see.
# Source of truth: the Data Sources table in the assignment instructions.
ROLE_COLLECTIONS = {
    "doctor": {"general", "clinical", "nursing"},
    "nurse": {"general", "nursing"},
    "billing_executive": {"general", "billing"},
    "technician": {"general", "equipment"},
    "admin": {"general", "clinical", "nursing", "billing", "equipment"},
}

# Collections whose folder maps 1:1 onto a directory name under MEDIASSIST_DATA_DIR
COLLECTIONS = ["general", "clinical", "nursing", "billing", "equipment"]

# Roles allowed to use SQL RAG (billing/maintenance analytics)
SQL_RAG_ROLES = {"billing_executive", "admin"}
