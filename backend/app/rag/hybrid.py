"""
Hybrid (dense + BM25) retrieval with cross-encoder reranking, RBAC-filtered
at the vector store query level -- same techniques as advanced__RAG.ipynb,
wired up per-role instead of once globally.
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from app.config import (
    EMBED_MODEL,
    RERANK_MODEL,
    GROQ_MODEL,
    QDRANT_PATH,
    QDRANT_COLLECTION,
)
from app.rbac.roles import build_role_filter

SYSTEM_PROMPT = """You are MediBot, an internal assistant for MediAssist Health Network staff.
Answer the staff member's question using ONLY the information provided in the context below.
If the answer is not in the context, say "I don't have that information in the documents \
I have access to." Keep answers concise and professional.

Context:
{context}"""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
    ]
)

# Loaded lazily, once, and reused across requests.
_dense_embeddings = None
_sparse_embeddings = None
_vectorstore = None
_cross_encoder = None
_llm = None


def _get_vectorstore() -> QdrantVectorStore:
    global _dense_embeddings, _sparse_embeddings, _vectorstore
    if _vectorstore is None:
        _dense_embeddings = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        _sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25", batch_size=32)
        _vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=_dense_embeddings,
            sparse_embedding=_sparse_embeddings,
            path=QDRANT_PATH,
            collection_name=QDRANT_COLLECTION,
            retrieval_mode=RetrievalMode.HYBRID,
        )
    return _vectorstore


def _get_cross_encoder() -> HuggingFaceCrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        _cross_encoder = HuggingFaceCrossEncoder(model_name=RERANK_MODEL)
    return _cross_encoder


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0,
            max_tokens=None,
            reasoning_format="parsed",
            timeout=None,
            max_retries=2,
        )
    return _llm


def answer_document_question(question: str, role: str) -> dict:
    """
    Runs the RBAC-filtered hybrid retrieval + rerank + LLM answer pipeline
    for a single question, scoped to what `role` is permitted to see.
    Returns {"answer": str, "sources": [ {source_document, collection, section_title}, ... ]}
    """
    vectorstore = _get_vectorstore()
    role_filter = build_role_filter(role)

    # Broad retrieval (top-10) WITH the RBAC filter baked into the query --
    # restricted chunks are never fetched, not filtered out afterward.
    broad_retriever = vectorstore.as_retriever(
        search_kwargs={"k": 10, "filter": role_filter}
    )

    reranker = CrossEncoderReranker(model=_get_cross_encoder(), top_n=3)
    reranking_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=broad_retriever,
    )

    chain = create_retrieval_chain(
        reranking_retriever,
        create_stuff_documents_chain(_get_llm(), _prompt),
    )

    result = chain.invoke({"input": question})

    sources = [
        {
            "source_document": doc.metadata.get("source_document"),
            "collection": doc.metadata.get("collection"),
            "section_title": doc.metadata.get("section_title"),
        }
        for doc in result.get("context", [])
    ]

    return {"answer": result["answer"], "sources": sources}
