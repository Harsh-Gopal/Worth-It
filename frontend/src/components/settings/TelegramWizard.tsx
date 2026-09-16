import React, { useState, useEffect } from "react";
import { Send, CheckCircle2, AlertCircle, Loader2, Trash2, Plus, User, Key, Bot } from "lucide-react";
import { api } from "../../lib/api";
import type { TelegramRecipient } from "../../lib/types";

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-input)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  color: "var(--text-primary)",
  fontSize: "14px",
  padding: "9px 12px",
  outline: "none",
  transition: "border-color 0.15s, box-shadow 0.15s",
  fontFamily: "inherit",
  boxSizing: "border-box",
};

const inputWithIconStyle: React.CSSProperties = {
  ...inputStyle,
  paddingLeft: "38px",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "12px",
  fontWeight: 600,
  color: "var(--text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  marginBottom: "6px",
};

const cardStyle: React.CSSProperties = {
  background: "var(--bg-surface)",
  border: "1px solid var(--border)",
  borderRadius: "10px",
  overflow: "hidden",
};

const cardHeaderStyle: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: "1px solid var(--border)",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "12px",
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: "var(--text-primary)",
  margin: 0,
};

export default function TelegramWizard() {
  const [botConfigured, setBotConfigured] = useState(false);
  const [botInfo, setBotInfo] = useState<{ username?: string; name?: string } | null>(null);
  const [botToken, setBotToken] = useState("");
  const [isVerifyingBot, setIsVerifyingBot] = useState(false);

  const [recipients, setRecipients] = useState<TelegramRecipient[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const [chatId, setChatId] = useState("");
  const [name, setName] = useState("");
  const [type, setType] = useState("private");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testStatus, setTestStatus] = useState<Record<string, "idle" | "loading" | "success" | "error">>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { checkStatus(); }, []);

  const checkStatus = async () => {
    try {
      const [statusRes, botStatusRes] = await Promise.all([
        api.get("/telegram/status"),
        api.get("/telegram/bot/status"),
      ]);
      setRecipients(statusRes.recipients || []);
      setBotConfigured(botStatusRes.configured || false);
      if (botStatusRes.configured) {
        setBotInfo({ username: botStatusRes.bot_username, name: botStatusRes.bot_name });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfigureBot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!botToken.trim()) return;
    setIsVerifyingBot(true);
    setError(null);
    try {
      const res = await api.post("/telegram/bot/configure", { bot_token: botToken.trim() });
      setBotConfigured(true);
      setBotInfo({ username: res.bot_username, name: res.bot_name });
      setBotToken("");
    } catch (err: any) {
      setError(err.message || "Failed to verify bot token");
    } finally {
      setIsVerifyingBot(false);
    }
  };

  const handleRemoveBot = async () => {
    if (!confirm("Remove bot token? Notifications will stop working.")) return;
    try {
      await api.delete("/telegram/bot");
      setBotConfigured(false);
      setBotInfo(null);
    } catch (err: any) {
      setError(err.message || "Failed to remove bot token");
    }
  };

  const handleAddRecipient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatId.trim() || !name.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api.post("/telegram/connect", { chat_id: chatId.trim(), name: name.trim(), type });
      setRecipients(res.recipients);
      setChatId("");
      setName("");
    } catch (err: any) {
      setError(err.message || "Failed to add recipient");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemoveRecipient = async (id: string) => {
    if (!confirm("Remove this recipient?")) return;
    try {
      const res = await api.delete(`/telegram/connect/${id}`);
      setRecipients(res.recipients);
    } catch (err: any) {
      setError(err.message || "Failed to remove recipient");
    }
  };

  const handleTest = async (id: string) => {
    setTestStatus(prev => ({ ...prev, [id]: "loading" }));
    try {
      await api.post("/telegram/test", { chat_id: id });
      setTestStatus(prev => ({ ...prev, [id]: "success" }));
      setTimeout(() => setTestStatus(prev => ({ ...prev, [id]: "idle" })), 3000);
    } catch (err: any) {
      setTestStatus(prev => ({ ...prev, [id]: "error" }));
      setError(err.message || "Failed to send test message");
    }
  };

  const onInputFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "var(--color-brand-green)";
    e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
  };
  const onInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "var(--border)";
    e.target.style.boxShadow = "none";
  };

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "24px" }}>
        <Loader2 className="w-5 h-5 animate-spin" style={{ color: "var(--color-brand-green)" }} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

      {/* ── Bot Setup ───────────────────────────────── */}
      <div style={cardStyle}>
        <div style={cardHeaderStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Bot className="w-4 h-4" style={{ color: "var(--color-brand-green)", flexShrink: 0 }} />
            <h3 style={sectionTitleStyle}>Telegram Bot</h3>
          </div>
          {botConfigured && (
            <span style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              fontSize: "11px",
              fontWeight: 700,
              color: "var(--color-brand-green)",
              background: "var(--ring-green)",
              border: "1px solid rgba(22,163,74,0.3)",
              borderRadius: "6px",
              padding: "2px 8px",
            }}>
              <CheckCircle2 className="w-3 h-3" /> Connected
            </span>
          )}
        </div>

        <div style={{ padding: "16px" }}>
          {botConfigured ? (
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 14px",
              background: "var(--ring-green)",
              border: "1px solid rgba(22,163,74,0.25)",
              borderRadius: "8px",
              gap: "12px",
              flexWrap: "wrap",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  background: "rgba(22,163,74,0.15)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}>
                  <Bot className="w-5 h-5" style={{ color: "var(--color-brand-green)" }} />
                </div>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>
                    {botInfo?.name || "Worth-It Bot"}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--color-brand-green)" }}>
                    @{botInfo?.username || "unknown_bot"}
                  </div>
                </div>
              </div>
              <button
                onClick={handleRemoveBot}
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "var(--color-brand-red)",
                  background: "transparent",
                  border: "1px solid var(--color-brand-red)",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  flexShrink: 0,
                }}
              >
                Disconnect
              </button>
            </div>
          ) : (
            <form onSubmit={handleConfigureBot}>
              <label style={labelStyle}>Bot API Token</label>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <div style={{ position: "relative", flex: 1, minWidth: 0 }}>
                  <Key className="w-4 h-4" style={{
                    position: "absolute",
                    left: "10px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "var(--text-muted)",
                    pointerEvents: "none",
                    flexShrink: 0,
                  }} />
                  <input
                    type="password"
                    placeholder="1234567890:AAH_XXXXXXXX..."
                    value={botToken}
                    onChange={e => setBotToken(e.target.value)}
                    style={{ ...inputWithIconStyle }}
                    onFocus={onInputFocus}
                    onBlur={onInputBlur}
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={isVerifyingBot || !botToken.trim()}
                  className="btn-primary"
                  style={{ flexShrink: 0, height: "40px" }}
                >
                  {isVerifyingBot ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify & Connect"}
                </button>
              </div>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "6px" }}>
                Create a bot using{" "}
                <a href="https://t.me/BotFather" target="_blank" rel="noreferrer"
                  style={{ color: "var(--color-brand-green)" }}>@BotFather</a>
                {" "}and paste the API token here.
              </p>
            </form>
          )}
        </div>
      </div>

      {/* ── Active Endpoints ────────────────────────── */}
      <div style={{ ...cardStyle, opacity: botConfigured ? 1 : 0.5, pointerEvents: botConfigured ? "auto" : "none" }}>
        <div style={cardHeaderStyle}>
          <h3 style={sectionTitleStyle}>Active Notification Endpoints</h3>
          {recipients.length > 0 && (
            <span style={{
              fontSize: "11px",
              fontWeight: 600,
              color: "var(--text-muted)",
              background: "var(--bg-muted)",
              border: "1px solid var(--border)",
              borderRadius: "6px",
              padding: "2px 8px",
            }}>
              {recipients.length} endpoint{recipients.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {recipients.length === 0 ? (
          <div style={{
            padding: "24px",
            textAlign: "center",
            color: "var(--text-muted)",
            fontSize: "13px",
          }}>
            No endpoints configured yet.
          </div>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {recipients.map(recipient => (
              <li
                key={recipient.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "12px",
                  padding: "12px 16px",
                  borderTop: "1px solid var(--border)",
                  flexWrap: "wrap",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
                  <div style={{
                    width: "32px",
                    height: "32px",
                    borderRadius: "50%",
                    background: "var(--ring-green)",
                    border: "1px solid rgba(22,163,74,0.25)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}>
                    <User className="w-4 h-4" style={{ color: "var(--color-brand-green)" }} />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {recipient.name}
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "1px" }}>
                      <span style={{ color: "var(--color-brand-green)", textTransform: "uppercase", fontWeight: 600 }}>{recipient.type}</span>
                      {" · "}
                      <span style={{ fontFamily: "monospace" }}>{recipient.id}</span>
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: "6px", flexShrink: 0 }}>
                  <button
                    onClick={() => handleTest(recipient.id)}
                    disabled={testStatus[recipient.id] === "loading"}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: testStatus[recipient.id] === "success" ? "var(--color-brand-green)" : "var(--text-primary)",
                      background: "var(--bg-muted)",
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                      padding: "5px 10px",
                      cursor: "pointer",
                      fontFamily: "inherit",
                    }}
                  >
                    {testStatus[recipient.id] === "loading" ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : testStatus[recipient.id] === "success" ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : (
                      <Send className="w-3 h-3" />
                    )}
                    {testStatus[recipient.id] === "success" ? "Sent!" : "Test"}
                  </button>
                  <button
                    onClick={() => handleRemoveRecipient(recipient.id)}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "var(--text-secondary)",
                      background: "var(--bg-muted)",
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                      padding: "5px 10px",
                      cursor: "pointer",
                      fontFamily: "inherit",
                      transition: "color 0.15s, border-color 0.15s",
                    }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.color = "var(--color-brand-red)";
                      (e.currentTarget as HTMLElement).style.borderColor = "var(--color-brand-red)";
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                      (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                    }}
                  >
                    <Trash2 className="w-3 h-3" /> Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── Add New Endpoint ────────────────────────── */}
      <div style={{ ...cardStyle, opacity: botConfigured ? 1 : 0.5, pointerEvents: botConfigured ? "auto" : "none" }}>
        <div style={cardHeaderStyle}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Plus className="w-4 h-4" style={{ color: "var(--color-brand-green)" }} />
            <h3 style={{ ...sectionTitleStyle, color: "var(--color-brand-green)" }}>Add Endpoint</h3>
          </div>
        </div>

        <form onSubmit={handleAddRecipient} style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "14px" }}>
          {!botConfigured && (
            <div style={{
              padding: "10px 12px",
              background: "var(--ring-red)",
              border: "1px solid rgba(220,38,38,0.25)",
              borderRadius: "8px",
            }}>
              <p style={{ fontSize: "12px", color: "var(--color-brand-red)", margin: 0 }}>
                Configure your Telegram Bot token above before adding endpoints.
              </p>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={labelStyle}>Display Name</label>
              <input
                type="text"
                placeholder="e.g. My Phone"
                value={name}
                onChange={e => setName(e.target.value)}
                style={inputStyle}
                onFocus={onInputFocus}
                onBlur={onInputBlur}
                required
                disabled={!botConfigured}
              />
            </div>
            <div>
              <label style={labelStyle}>Chat ID</label>
              <input
                type="text"
                placeholder="e.g. 123456789"
                value={chatId}
                onChange={e => setChatId(e.target.value)}
                style={{ ...inputStyle, fontFamily: "monospace" }}
                onFocus={onInputFocus}
                onBlur={onInputBlur}
                required
                disabled={!botConfigured}
              />
            </div>
          </div>

          <div>
            <label style={labelStyle}>Type</label>
            <div style={{ display: "flex", gap: "20px" }}>
              {[{ value: "private", label: "Private User" }, { value: "group", label: "Group Chat" }].map(opt => (
                <label key={opt.value} style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  cursor: botConfigured ? "pointer" : "not-allowed",
                  fontSize: "13px",
                  fontWeight: 500,
                  color: "var(--text-primary)",
                }}>
                  <input
                    type="radio"
                    name="endpoint-type"
                    value={opt.value}
                    checked={type === opt.value}
                    onChange={e => setType(e.target.value)}
                    disabled={!botConfigured}
                    style={{ accentColor: "var(--color-brand-green)" }}
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          </div>

          {error && (
            <div style={{
              display: "flex",
              gap: "8px",
              alignItems: "flex-start",
              padding: "10px 12px",
              background: "var(--ring-red)",
              border: "1px solid rgba(220,38,38,0.25)",
              borderRadius: "8px",
            }}>
              <AlertCircle className="w-4 h-4 shrink-0" style={{ color: "var(--color-brand-red)", marginTop: "1px" }} />
              <p style={{ fontSize: "12px", color: "var(--color-brand-red)", margin: 0 }}>{error}</p>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isSubmitting || !chatId.trim() || !name.trim() || !botConfigured}
              className="btn-primary"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Register Endpoint
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
