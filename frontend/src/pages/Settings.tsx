
import TelegramWizard from '../components/settings/TelegramWizard';

export default function Settings() {
  return (
    <div className="max-w-4xl mx-auto py-8 w-full px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">System Config</h1>
        <p className="text-[var(--color-text-muted)] mt-1 font-mono text-sm uppercase tracking-wider">Manage integrations and telemetry preferences.</p>
      </div>

      <div className="space-y-6">
        {/* Telegram Integration Card */}
        <div className="glass-panel overflow-hidden border-[var(--color-radar-border)]">
          <div className="p-6 border-b border-[var(--color-radar-border)] bg-[var(--color-radar-bg)] relative">
            {/* Background glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-[#0088cc] opacity-5 blur-3xl rounded-full"></div>
            
            <h2 className="text-lg font-bold text-white flex items-center gap-3 relative z-10">
              <div className="bg-[#0088cc]/20 p-2 rounded-lg border border-[#0088cc]/30 shadow-[0_0_10px_rgba(0,136,204,0.2)]">
                <svg className="w-5 h-5 text-[#0088cc]" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.888-.662 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
              </div>
              Telegram Integration
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mt-2 max-w-2xl relative z-10">
              Connect a Telegram Chat ID to receive instant priority alerts when deals matching your active subroutines are detected.
            </p>
          </div>
          
          <div className="p-6">
            <TelegramWizard />
          </div>
        </div>
      </div>
    </div>
  );
}
