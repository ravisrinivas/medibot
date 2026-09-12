const ROLE_LABELS = {
  doctor: "Doctor",
  nurse: "Nurse",
  billing_executive: "Billing Executive",
  technician: "Technician",
  admin: "Admin",
};

export default function RoleBadge({ role }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "4px 10px",
        borderRadius: "999px",
        fontSize: "12px",
        fontWeight: 600,
        color: "var(--teal)",
        background: "var(--teal-soft)",
      }}
    >
      {ROLE_LABELS[role] || role}
    </span>
  );
}
