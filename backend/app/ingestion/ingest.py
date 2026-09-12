"""
MediBot ingestion pipeline.

Reuses the exact parsing/chunking/embedding approach from advanced__RAG.ipynb
(Docling DocumentConverter + HybridChunker, HuggingFace dense embeddings,
FastEmbedSparse for BM25, QdrantVectorStore in HYBRID mode) but adds the
RBAC metadata schema required by this project:

    source_document, collection, access_roles, section_title, chunk_type

Run this once (or whenever the source documents change) with:
    python -m app.ingestion.ingest
"""
import os
import pathlib

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling_core.types.doc.labels import DocItemLabel
from transformers import AutoTokenizer
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode

from app.config import (
    EMBED_MODEL,
    MEDIASSIST_DATA_DIR,
    QDRANT_PATH,
    QDRANT_COLLECTION,
    CHUNK_MAX_TOKENS,
    COLLECTIONS,
    ROLE_COLLECTIONS,
)

# Docling item label -> our chunk_type. Everything not a table or a heading
# is treated as plain text (this dataset has no code blocks).
_TABLE_LABELS = {DocItemLabel.TABLE}
_HEADING_LABELS = {DocItemLabel.SECTION_HEADER, DocItemLabel.TITLE}


def collection_to_roles() -> dict[str, list[str]]:
    """Invert ROLE_COLLECTIONS: collection name -> list of roles that may see it."""
    mapping: dict[str, set[str]] = {c: set() for c in COLLECTIONS}
    for role, collections in ROLE_COLLECTIONS.items():
        for c in collections:
            mapping.setdefault(c, set()).add(role)
    return {c: sorted(roles) for c, roles in mapping.items()}


def chunk_type_for(chunk) -> str:
    """Majority-vote the Docling item labels backing this chunk."""
    labels = [item.label for item in chunk.meta.doc_items]
    if any(l in _TABLE_LABELS for l in labels):
        return "table"
    if labels and all(l in _HEADING_LABELS for l in labels):
        return "heading"
    return "text"


def section_title_for(chunk) -> str:
    headings = chunk.meta.headings or []
    return headings[-1] if headings else ""


def iter_source_files(data_dir: str):
    for collection in COLLECTIONS:
        folder = pathlib.Path(data_dir) / collection
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() in (".pdf", ".md"):
                yield collection, path


def build_documents(data_dir: str) -> list[Document]:
    tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL)
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=CHUNK_MAX_TOKENS,
        merge_peers=True,
    )
    converter = DocumentConverter()
    roles_by_collection = collection_to_roles()

    all_docs: list[Document] = []

    for collection, path in iter_source_files(data_dir):
        print(f"Parsing {path} (collection={collection}) ...")
        dl_doc = converter.convert(str(path)).document
        chunk_iter = chunker.chunk(dl_doc=dl_doc)

        source_document = path.stem  # filename WITHOUT extension, per spec

        n_chunks = 0
        for chunk in chunk_iter:
            all_docs.append(
                Document(
                    page_content=chunker.serialize(chunk=chunk),
                    metadata={
                        "source_document": source_document,
                        "collection": collection,
                        "access_roles": roles_by_collection[collection],
                        "section_title": section_title_for(chunk),
                        "chunk_type": chunk_type_for(chunk),
                    },
                )
            )
            n_chunks += 1
        print(f"  -> {n_chunks} chunks")

    return all_docs


def main():
    docs = build_documents(MEDIASSIST_DATA_DIR)
    print(f"\nTotal chunks to index: {len(docs)}")

    dense_embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25", batch_size=32)

    os.makedirs(QDRANT_PATH, exist_ok=True)

    QdrantVectorStore.from_documents(
        documents=docs,
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        path=QDRANT_PATH,
        collection_name=QDRANT_COLLECTION,
        retrieval_mode=RetrievalMode.HYBRID,
    )
    print(f"\nIndexed {len(docs)} chunks into Qdrant collection '{QDRANT_COLLECTION}' "
          f"at {QDRANT_PATH}")


if __name__ == "__main__":
    main()
