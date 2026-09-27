import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ErrorBoundary } from './components/ErrorBoundary'

const tgUser = (window as any).Telegram?.WebApp?.initDataUnsafe?.user;
const VITE_API_URL = import.meta.env.VITE_API_URL || "";

// Intercept fetch globally to add Telegram headers and prepend VITE_API_URL
const originalFetch = window.fetch;
window.fetch = async function(...args) {
  let [resource, config] = args;
  
  if (typeof resource === "string" && resource.startsWith("/api/")) {
    // Prepend API URL for cross-origin production deployments (like Vercel to Render)
    if (VITE_API_URL) {
      resource = `${VITE_API_URL}${resource}`;
      args[0] = resource;
    }

    if (tgUser) {
      config = config || {};
      config.headers = {
        ...config.headers,
        "x-telegram-user-id": String(tgUser.id)
      };
      args[1] = config;
    }
  }
  return originalFetch.apply(this, args);
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
