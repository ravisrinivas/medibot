"""
Diagnostic: run from backend/ with the venv active.
    python diagnose.py
Checks: how many points are in the collection, a sample payload, and
whether the RBAC filter for "doctor" actually returns anything.
"""
from qdrant_client import QdrantClient
from app.config import QDRANT_PATH, QDRANT_COLLECTION
from app.rbac.roles import build_role_filter

client = QdrantClient(path=QDRANT_PATH)

info = client.get_collection(QDRANT_COLLECTION)
print(f"Collection '{QDRANT_COLLECTION}' points_count: {info.points_count}")

sample = client.scroll(collection_name=QDRANT_COLLECTION, limit=3, with_payload=True)
print("\nSample payloads:")
for point in sample[0]:
    print(point.payload)

print("\n--- Testing RBAC filter for role='doctor' ---")
role_filter = build_role_filter("doctor")
filtered = client.scroll(
    collection_name=QDRANT_COLLECTION,
    scroll_filter=role_filter,
    limit=5,
    with_payload=True,
)
print(f"Points matching doctor filter: {len(filtered[0])}")
for point in filtered[0]:
    meta = point.payload.get("metadata", {})
    print(meta.get("collection"), meta.get("access_roles"))
