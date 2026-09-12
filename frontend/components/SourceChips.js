export default function SourceChips({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "10px" }}>
      {sources.map((s, i) => (
        <span
          key={i}
          title={s.section_title || ""}
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "12px",
            color: "var(--blue)",
            background: "var(--blue-soft)",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            padding: "3px 8px",
          }}
        >
          {s.source_document}
          {s.collection ? ` \u00b7 ${s.collection}` : ""}
        </span>
      ))}
    </div>
  );
}
