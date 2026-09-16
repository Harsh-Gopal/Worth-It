import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props { children?: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false, error: null };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex",
          height: "100vh",
          width: "100%",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-page, #f8fafc)",
          padding: "16px",
          fontFamily: "'Inter', sans-serif",
          color: "var(--text-primary, #0f172a)",
        }}>
          <div style={{
            maxWidth: "440px",
            width: "100%",
            background: "var(--bg-surface, #ffffff)",
            border: "1px solid rgba(220,38,38,0.2)",
            borderRadius: "16px",
            padding: "32px",
            textAlign: "center",
          }}>
            <div style={{
              width: "56px",
              height: "56px",
              background: "rgba(220,38,38,0.08)",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 20px",
            }}>
              <AlertTriangle className="w-7 h-7" style={{ color: "#dc2626" }} />
            </div>
            <h1 style={{ fontSize: "18px", fontWeight: 700, margin: "0 0 8px", color: "var(--text-primary, #0f172a)" }}>
              Something went wrong
            </h1>
            <p style={{
              fontSize: "14px",
              color: "var(--text-secondary, #475569)",
              margin: "0 0 24px",
              lineHeight: 1.6,
            }}>
              Worth-It encountered an unexpected error. Try reloading the page to resolve this.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <div style={{
                marginBottom: "20px",
                padding: "12px",
                background: "rgba(0,0,0,0.04)",
                borderRadius: "8px",
                border: "1px solid rgba(0,0,0,0.08)",
                textAlign: "left",
                overflow: "auto",
                maxHeight: "180px",
              }}>
                <p style={{
                  fontSize: "12px",
                  fontFamily: "monospace",
                  color: "#dc2626",
                  whiteSpace: "pre-wrap",
                  margin: 0,
                }}>
                  {this.state.error.message}
                </p>
              </div>
            )}

            <button
              onClick={() => window.location.reload()}
              className="btn-primary"
              style={{ width: "100%", justifyContent: "center" }}
            >
              <RefreshCw className="w-4 h-4" /> Reload Worth-It
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
