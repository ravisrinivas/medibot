import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SourceChips from "./SourceChips";

const TYPE_LABEL = {
  sql: "From billing/maintenance records",
  document: "From documents",
  blocked: "Access restricted",
};

export default function MessageBubble({ role, content, retrievalType, sources }) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "14px" }}>
        <div
          style={{
            maxWidth: "70%",
            background: "var(--teal)",
            color: "#fff",
            padding: "10px 14px",
            borderRadius: "14px 14px 2px 14px",
            fontSize: "15px",
          }}
        >
          {content}
        </div>
      </div>
    );
  }

  const isBlocked = retrievalType === "blocked";

  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: "14px" }}>
      <div
        style={{
          maxWidth: "78%",
          background: isBlocked ? "var(--red-soft)" : "var(--surface)",
          border: isBlocked ? "1px solid var(--red)" : "1px solid var(--border)",
          borderRadius: "2px 14px 14px 14px",
          padding: "12px 14px",
        }}
      >
        {retrievalType && (
          <div
            style={{
              fontSize: "11px",
              fontWeight: 600,
              color: isBlocked ? "var(--red)" : "var(--ink-soft)",
              marginBottom: "6px",
            }}
          >
            {TYPE_LABEL[retrievalType]}
          </div>
        )}
        <div className="medibot-markdown" style={{ fontSize: "15px", color: "var(--ink)" }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
        {!isBlocked && <SourceChips sources={sources} />}
      </div>
    </div>
  );
}
