import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import { askQuestion, getCollections } from "../lib/api";
import RoleBadge from "../components/RoleBadge";
import MessageBubble from "../components/MessageBubble";

export default function Chat() {
  const router = useRouter();
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);
  const [collections, setCollections] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    const t = window.localStorage.getItem("medibot_token");
    const r = window.localStorage.getItem("medibot_role");
    if (!t || !r) {
      router.replace("/login");
      return;
    }
    setToken(t);
    setRole(r);
    getCollections(r)
      .then((data) => setCollections(data.collections))
      .catch(() => setCollections([]));
  }, [router]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function logout() {
    window.localStorage.removeItem("medibot_token");
    window.localStorage.removeItem("medibot_role");
    router.push("/login");
  }

  async function handleSend(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || sending) return;

    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setSending(true);

    try {
      const result = await askQuestion(token, question);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: result.answer,
          retrievalType: result.retrieval_type,
          sources: result.sources,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Something went wrong: ${err.message}`, retrievalType: "blocked" },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (!token) return null;

  return (
    <div style={styles.page}>
      <aside style={styles.sidebar}>
        <div style={styles.mark}>MediBot</div>

        <div style={styles.sidebarSection}>
          <div style={styles.sidebarLabel}>Signed in as</div>
          <RoleBadge role={role} />
        </div>

        <div style={styles.sidebarSection}>
          <div style={styles.sidebarLabel}>You can access</div>
          <ul style={styles.collectionList}>
            {collections.map((c) => (
              <li key={c} style={styles.collectionItem}>
                {c}
              </li>
            ))}
          </ul>
        </div>

        <button style={styles.logout} onClick={logout}>
          Sign out
        </button>
      </aside>

      <main style={styles.main}>
        <div ref={scrollRef} style={styles.messages}>
          {messages.length === 0 && (
            <div style={styles.empty}>
              Ask a question about your accessible collections above &mdash; e.g.
              &ldquo;What is the standard dose for Amoxicillin?&rdquo;
            </div>
          )}
          {messages.map((m, i) => (
            <MessageBubble
              key={i}
              role={m.role}
              content={m.content}
              retrievalType={m.retrievalType}
              sources={m.sources}
            />
          ))}
          {sending && <div style={styles.typing}>MediBot is thinking&hellip;</div>}
        </div>

        <form onSubmit={handleSend} style={styles.inputBar}>
          <input
            style={styles.textInput}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask MediBot a question&hellip;"
            disabled={sending}
          />
          <button style={styles.sendButton} type="submit" disabled={sending || !input.trim()}>
            Send
          </button>
        </form>
      </main>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    minHeight: "100vh",
  },
  sidebar: {
    width: "240px",
    flexShrink: 0,
    borderRight: "1px solid var(--border)",
    background: "var(--surface)",
    padding: "24px 20px",
    display: "flex",
    flexDirection: "column",
    gap: "28px",
  },
  mark: {
    fontSize: "18px",
    fontWeight: 700,
    color: "var(--teal)",
  },
  sidebarSection: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  sidebarLabel: {
    fontSize: "11px",
    fontWeight: 600,
    color: "var(--ink-soft)",
    textTransform: "none",
  },
  collectionList: {
    listStyle: "none",
    margin: 0,
    padding: 0,
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  collectionItem: {
    fontSize: "13px",
    color: "var(--ink)",
    background: "var(--bg)",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    padding: "4px 8px",
  },
  logout: {
    marginTop: "auto",
    padding: "9px 12px",
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--ink-soft)",
    background: "transparent",
    border: "1px solid var(--border)",
    borderRadius: "8px",
    cursor: "pointer",
  },
  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    maxWidth: "760px",
    margin: "0 auto",
    width: "100%",
  },
  messages: {
    flex: 1,
    overflowY: "auto",
    padding: "28px 24px",
  },
  empty: {
    color: "var(--ink-soft)",
    fontSize: "14px",
    lineHeight: 1.6,
    marginTop: "40px",
  },
  typing: {
    fontSize: "13px",
    color: "var(--ink-soft)",
    fontStyle: "italic",
  },
  inputBar: {
    display: "flex",
    gap: "10px",
    padding: "16px 24px 24px",
    borderTop: "1px solid var(--border)",
  },
  textInput: {
    flex: 1,
    padding: "11px 14px",
    fontSize: "15px",
    fontFamily: "var(--font-sans)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    background: "var(--surface)",
    color: "var(--ink)",
  },
  sendButton: {
    padding: "11px 20px",
    fontSize: "15px",
    fontWeight: 600,
    color: "#fff",
    background: "var(--teal)",
    border: "none",
    borderRadius: "10px",
    cursor: "pointer",
  },
};
