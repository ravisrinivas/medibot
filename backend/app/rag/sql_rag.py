"""
SQL RAG over mediassist.db (claims, maintenance_tickets tables) -- same
three-step pattern as advanced__RAG.ipynb: NL -> SQL -> execute -> NL answer.
Access to this module is gated by role at the API layer (main.py), not here.
"""
import os
import re

from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.config import GROQ_MODEL, MEDIASSIST_DATA_DIR

SYSTEM_PROMPT = """You are a MediAssist Health Network operations analytics assistant.
Given a user question and the SQL query result from our billing/maintenance database,
provide a clear, concise natural language answer.
Be specific with numbers and facts from the data."""

_db = None
_llm = None
_sql_query_chain = None


def clean_sql(raw: str) -> str:
    """Strip markdown fences and any preamble, leaving only the SQL statement."""
    raw = re.sub(r"```(?:sql)?", "", raw).strip("`").strip()
    if "SQLQuery:" in raw:
        raw = raw.split("SQLQuery:")[-1].strip()
    return raw


def _get_db() -> SQLDatabase:
    global _db
    if _db is None:
        db_path = os.path.join(MEDIASSIST_DATA_DIR, "db", "mediassist.db")
        _db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    return _db


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(model=GROQ_MODEL, temperature=0, max_retries=2)
    return _llm


def _get_sql_query_chain():
    global _sql_query_chain
    if _sql_query_chain is None:
        _sql_query_chain = create_sql_query_chain(_get_llm(), _get_db())
    return _sql_query_chain


def sql_rag_chain(question: str) -> str:
    db = _get_db()
    llm = _get_llm()

    # Step 1: NL question -> SQL
    raw_sql = _get_sql_query_chain().invoke({"question": question})
    sql = clean_sql(raw_sql)

    # Step 2: execute against the database
    result = db.run(sql)

    # Step 3: SQL result -> NL answer
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Question: {question}\nSQL Result: {result}\n\nAnswer:"),
        ]
    )
    response = answer_prompt | llm
    return response.invoke({"question": question, "result": result}).content
