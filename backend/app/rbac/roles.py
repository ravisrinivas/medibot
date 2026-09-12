"""
RBAC enforcement at the retrieval layer.

Every chunk stored in Qdrant carries an `access_roles` payload field (list[str]).
Every retrieval query MUST attach a Qdrant filter that matches the caller's role
against that field, so that restricted chunks are never fetched from the vector
store in the first place -- they never reach the LLM, so there is nothing to
leak via a clever prompt.
"""
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import ROLE_COLLECTIONS


def known_role(role: str) -> bool:
    return role in ROLE_COLLECTIONS


def build_role_filter(role: str) -> Filter:
    """
    Qdrant filter: only return points whose `access_roles` payload array
    contains this role. Qdrant matches a MatchValue against any element of an
    array-valued payload field, so this is equivalent to "role IN access_roles".
    """
    return Filter(
        must=[
            FieldCondition(
                # LangChain's QdrantVectorStore nests all Document metadata
                # under a top-level "metadata" key in the Qdrant payload, so
                # the field path here must be "metadata.access_roles", not
                # "access_roles".
                key="metadata.access_roles",
                match=MatchValue(value=role),
            )
        ]
    )


def allowed_collections(role: str) -> list[str]:
    return sorted(ROLE_COLLECTIONS.get(role, set()))
