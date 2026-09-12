"""
Routes an incoming question to SQL RAG (analytical/statistical questions
over claims or maintenance_tickets) or hybrid document retrieval.

Keyword heuristic for now -- reliable, fast, no extra LLM call. Swap in an
LLM-based classifier later if the keyword list stops covering real traffic.
"""
import re

_ANALYTICAL_PATTERNS = [
    r"\bhow many\b",
    r"\bcount\b",
    r"\btotal\b",
    r"\baverage\b",
    r"\bmost common\b",
    r"\bpercentage\b",
    r"\bbreakdown\b",
    r"\bresolved vs\b",
    r"\bescalated\b",
    r"\bper (category|department|campus|status)\b",
]

_ANALYTICAL_RE = re.compile("|".join(_ANALYTICAL_PATTERNS), re.IGNORECASE)


def is_analytical(question: str) -> bool:
    return bool(_ANALYTICAL_RE.search(question))
