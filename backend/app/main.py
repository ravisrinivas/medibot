from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth import authenticate, role_for_token
from app.rbac.roles import known_role, allowed_collections
from app.schemas import (
    LoginRequest,
    LoginResponse,
    ChatRequest,
    ChatResponse,
    SourceRef,
)
from app.rag.router import is_analytical
from app.rag.sql_rag import sql_rag_chain
from app.rag.hybrid import answer_document_question
from app.config import SQL_RAG_ROLES

app = FastAPI(title="MediBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def _role_from_auth_header(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    role = role_for_token(token)
    if not role:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return role


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    token = authenticate(body.username, body.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    role = role_for_token(token)
    return LoginResponse(token=token, role=role)


@app.get("/collections/{role}")
def collections_for_role(role: str):
    if not known_role(role):
        raise HTTPException(status_code=404, detail="Unknown role")
    return {"role": role, "collections": allowed_collections(role)}


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, authorization: str | None = Header(default=None)):
    role = _role_from_auth_header(authorization)
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    if is_analytical(question):
        if role not in SQL_RAG_ROLES:
            return ChatResponse(
                answer=(
                    "This looks like an analytics/reporting question over the billing or "
                    "maintenance database. Your role does not have access to that data -- "
                    "only billing_executive and admin can run these queries."
                ),
                retrieval_type="blocked",
                sources=[],
            )
        answer = sql_rag_chain(question)
        return ChatResponse(answer=answer, retrieval_type="sql", sources=[])

    result = answer_document_question(question, role)
    return ChatResponse(
        answer=result["answer"],
        retrieval_type="document",
        sources=[SourceRef(**s) for s in result["sources"]],
    )
