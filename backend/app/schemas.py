from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str


class ChatRequest(BaseModel):
    question: str


class SourceRef(BaseModel):
    source_document: str | None = None
    collection: str | None = None
    section_title: str | None = None


class ChatResponse(BaseModel):
    answer: str
    retrieval_type: str  # "sql" | "document" | "blocked"
    sources: list[SourceRef] = []
