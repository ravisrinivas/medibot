import { useState } from "react";
import { useRouter } from "next/router";
import { login } from "../lib/api";

export default function Login() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { token, role } = await login(username, password);
      window.localStorage.setItem("medibot_token", token);
      window.localStorage.setItem("medibot_role", role);
      router.push("/chat");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.panel}>
        <div style={styles.mark}>MediBot</div>
        <p style={styles.tagline}>
          Ask about clinical protocols, nursing procedures, billing, or
          equipment &mdash; scoped to what your role can see.
        </p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Staff ID
            <input
              style={styles.input}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label style={styles.label}>
            Password
            <input
              style={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error && <div style={styles.error}>{error}</div>}

          <button style={styles.button} disabled={loading} type="submit">
            {loading ? "Signing in\u2026" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
  },
  panel: {
    width: "100%",
    maxWidth: "380px",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
    padding: "36px 32px",
  },
  mark: {
    fontSize: "22px",
    fontWeight: 700,
    letterSpacing: "-0.01em",
    color: "var(--teal)",
    marginBottom: "8px",
  },
  tagline: {
    color: "var(--ink-soft)",
    fontSize: "14px",
    lineHeight: 1.5,
    marginBottom: "28px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    fontSize: "13px",
    fontWeight: 500,
    color: "var(--ink-soft)",
  },
  input: {
    padding: "10px 12px",
    fontSize: "15px",
    fontFamily: "var(--font-sans)",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    color: "var(--ink)",
    background: "var(--bg)",
  },
  button: {
    marginTop: "8px",
    padding: "11px 16px",
    fontSize: "15px",
    fontWeight: 600,
    color: "#fff",
    background: "var(--teal)",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  },
  error: {
    fontSize: "13px",
    color: "var(--red)",
    background: "var(--red-soft)",
    padding: "8px 10px",
    borderRadius: "6px",
  },
};
