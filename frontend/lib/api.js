const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function login(username, password) {
  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Login failed");
  }
  return res.json(); // { token, role }
}

export async function getCollections(role) {
  const res = await fetch(`${API_URL}/collections/${role}`);
  if (!res.ok) throw new Error("Could not load collections");
  return res.json(); // { role, collections }
}

export async function askQuestion(token, question) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Request failed");
  }
  return res.json(); // { answer, retrieval_type, sources }
}
