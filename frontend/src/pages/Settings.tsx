import TelegramWizard from "../components/settings/TelegramWizard";

export default function Settings() {
  return (
    <div style={{ maxWidth: "720px", margin: "0 auto", width: "100%" }}>
      {/* Page header */}
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{
          fontSize: "22px",
          fontWeight: 700,
          color: "var(--text-primary)",
          margin: 0,
          marginBottom: "4px",
        }}>
          Settings
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0 }}>
          Manage integrations and notification preferences.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {/* Telegram Integration Card */}
        <div style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          overflow: "hidden",
        }}>
          {/* Card header */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "18px 20px",
            borderBottom: "1px solid var(--border)",
          }}>
            <div style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "rgba(0,136,204,0.1)",
              border: "1px solid rgba(0,136,204,0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}>
              <svg viewBox="0 0 24 24" fill="#0088cc" width="18" height="18">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.888-.662 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
              </svg>
            </div>
            <div>
              <h2 style={{
                fontSize: "15px",
                fontWeight: 600,
                color: "var(--text-primary)",
                margin: 0,
                marginBottom: "2px",
              }}>
                Telegram Integration
              </h2>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0 }}>
                Connect a Chat ID to receive instant deal alerts.
              </p>
            </div>
          </div>

          <div style={{ padding: "20px" }}>
            <TelegramWizard />
          </div>
        </div>
      </div>
    </div>
  );
}
