import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ErrorBoundary } from './components/ErrorBoundary'

const tgUser = (window as any).Telegram?.WebApp?.initDataUnsafe?.user;
if (tgUser) {
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    let [resource, config] = args;
    if (typeof resource === "string" && resource.startsWith("/api/")) {
      config = config || {};
      config.headers = {
        ...config.headers,
        "x-telegram-user-id": String(tgUser.id)
      };
      args[1] = config;
    }
    return originalFetch.apply(this, args);
  };
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
