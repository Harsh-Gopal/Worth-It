import { useState, useEffect } from "react";
import TelegramWizard from "../components/settings/TelegramWizard";
import { Bell, BellOff, Settings as SettingsIcon } from "lucide-react";

export default function Settings() {
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>("default");

  useEffect(() => {
    if ("Notification" in window) {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  const requestPermission = async () => {
    if (!("Notification" in window)) {
      alert("This browser does not support desktop notification");
      return;
    }
    const permission = await Notification.requestPermission();
    setNotificationPermission(permission);
    if (permission === "granted") {
      new Notification("Worth-It Notifications Enabled!", {
        body: "You'll now receive alerts for new deals.",
      });
    }
  };

  return (
    <div style={{
      maxWidth: "680px",
      margin: "0 auto",
      width: "100%",
      padding: "32px 28px 48px",
    }}>

      {/* Page header */}
      <div style={{ marginBottom: "28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <div style={{
            width: "34px",
            height: "34px",
            borderRadius: "9px",
            background: "rgba(100,116,139,0.1)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--text-secondary)",
          }}>
            <SettingsIcon className="w-4 h-4" />
          </div>
          <h1 style={{
            fontSize: "22px",
            fontWeight: 800,
            color: "var(--text-primary)",
            margin: 0,
            letterSpacing: "-0.03em",
          }}>
            Settings
          </h1>
        </div>
        <p style={{
          fontSize: "13.5px",
          color: "var(--text-secondary)",
          margin: "0 0 0 44px",
          lineHeight: 1.5,
        }}>
          Manage integrations and notification preferences.
        </p>
        <div style={{ height: "1px", background: "var(--border)", marginTop: "20px" }} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>

        {/* Browser Notifications Card */}
        <div className="card" style={{ padding: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", flex: 1, minWidth: "220px" }}>
              <div style={{
                width: "38px",
                height: "38px",
                borderRadius: "10px",
                background: notificationPermission === "granted"
                  ? "rgba(22,163,74,0.1)"
                  : "var(--bg-muted)",
                border: `1px solid ${notificationPermission === "granted"
                  ? "rgba(22,163,74,0.2)"
                  : "var(--border)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}>
                {notificationPermission === "granted" ? (
                  <Bell className="w-4 h-4" style={{ color: "var(--color-brand-green)" }} />
                ) : (
                  <BellOff className="w-4 h-4" style={{ color: "var(--text-muted)" }} />
                )}
              </div>
              <div>
                <h2 style={{
                  fontSize: "14.5px",
                  fontWeight: 700,
                  color: "var(--text-primary)",
                  margin: "0 0 3px 0",
                  letterSpacing: "-0.01em",
                }}>
                  Browser Notifications
                </h2>
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
                  {notificationPermission === "granted"
                    ? "Enabled. You'll be alerted when new deals are found."
                    : notificationPermission === "denied"
                      ? "Blocked in browser settings. Please enable manually."
                      : "Enable browser push alerts without Telegram."}
                </p>
              </div>
            </div>

            <button
              onClick={requestPermission}
              disabled={notificationPermission === "granted" || notificationPermission === "denied"}
              className={
                notificationPermission === "granted"
                  ? "btn-secondary"
                  : notificationPermission === "denied"
                    ? "btn-secondary"
                    : "btn-primary"
              }
              style={{ padding: "8px 18px", fontSize: "13px" }}
            >
              {notificationPermission === "granted"
                ? "Enabled ✓"
                : notificationPermission === "denied"
                  ? "Blocked"
                  : "Enable"}
            </button>
          </div>
        </div>

        {/* Telegram Integration Card */}
        <div className="card" style={{ overflow: "hidden" }}>
          {/* Card header */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "18px 20px",
            borderBottom: "1px solid var(--border)",
          }}>
            <div style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              background: "rgba(0,136,204,0.08)",
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
                fontSize: "14.5px",
                fontWeight: 700,
                color: "var(--text-primary)",
                margin: "0 0 3px 0",
                letterSpacing: "-0.01em",
              }}>
                Telegram Integration
              </h2>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
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
