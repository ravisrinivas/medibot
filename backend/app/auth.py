"""
Minimal demo auth for the assignment. Not production security -- the point of
this project is RBAC-enforced retrieval, not building an auth system. Five
hardcoded demo users, one per role, and an in-memory token->role map.
"""
import secrets

from app.rbac.roles import known_role

# username -> (password, role)
DEMO_USERS = {
    "dr_patel": ("doctor123", "doctor"),
    "nurse_lee": ("nurse123", "nurse"),
    "billing_kim": ("billing123", "billing_executive"),
    "tech_ortiz": ("tech123", "technician"),
    "admin": ("admin123", "admin"),
}

# token -> role  (in-memory; resets on server restart)
_SESSIONS: dict[str, str] = {}


def authenticate(username: str, password: str) -> str | None:
    """Return a fresh session token if credentials are valid, else None."""
    record = DEMO_USERS.get(username)
    if not record:
        return None
    expected_password, role = record
    if password != expected_password:
        return None
    if not known_role(role):
        return None

    token = secrets.token_urlsafe(24)
    _SESSIONS[token] = role
    return token


def role_for_token(token: str) -> str | None:
    return _SESSIONS.get(token)
