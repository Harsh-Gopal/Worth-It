# Worth-It

A modern, production-ready, multi-platform quick-commerce deal discovery and price-monitoring engine.

## Features

Worth-It continuously monitors quick-commerce platforms and alerts you to extreme discounts.

- **Multi-Platform Monitoring:** Scans Swiggy Instamart, Zepto, Blinkit, and Flipkart Minutes simultaneously.
- **Location Modes:** Supports tracking Deals in your Current Pincode, explicitly configured Multiple Pincodes, or dynamically expanding Nearby Areas.
- **Keyword & Category Tracking:** Track specific search keywords (e.g., "Butter", "Eggs") and categories.
- **Wishlist Tracking:** Copy/paste direct product URLs to track specific items across platforms.
- **Rules Engine:** Set minimum discount thresholds, deal exclusions, and keyword requirements.
- **Price History:** Tracks the price of items over time locally to ensure discounts are genuine.
- **Alert Engine:** Intelligent deduplication, cooldowns, and Telegram notifications when deals are found.
- **Real-Time Dashboard (SSE):** Watch the scanner work live from your browser.
- **Continuous Background Scheduler:** Runs automatically in the background at your chosen intervals.
- **PIN Security:** Secure your settings and configurations with an administrative PIN.

## Architecture

Worth-It is split into a reactive frontend and a highly-concurrent backend:

```text
Browser
   ↓
Vercel Frontend (React + Vite)
   ↓ (API calls via VITE_API_URL)
Render Backend (FastAPI + Python)
   ↓
Platform Integrations (Instamart, Zepto, Blinkit, Minutes)
   ↓
Persistence / Price History (SQLite)
   ↓
Deal Engine & Alert Engine
   ↓
Telegram Alerts
```

## Project Structure

```
Worth-It/
├── frontend/             # React SPA (Vite, TailwindCSS)
│   ├── src/              # Source code for components, hooks, pages
│   ├── package.json      
│   └── vercel.json       # Production SPA routing for Vercel
│
└── backend/              # FastAPI Application
    ├── app/              # Core API, domain logic, platforms, and workers
    ├── data/             # Local SQLite databases for persistence
    ├── tests/            # Unit & Integration tests
    ├── Dockerfile        # Render backend deployment definition
    └── pyproject.toml    # Python dependencies (managed by uv)
```

## Local Development

Worth-It provides a `dev.sh` script to run both frontend and backend locally with hot-reloading.

### Prerequisites
- Node.js & npm
- Python 3.12+ and `uv` package manager

### Setup

```bash
# Start the entire stack locally
./dev.sh
```
Alternatively, you can run them separately:

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Backend:**
```bash
cd backend
uv sync
uv run uvicorn main:app --reload
```

## Environment Variables

### Frontend Variables (`frontend/.env`)
- `VITE_API_URL`: The URL to your backend API. (e.g., `http://localhost:8000` for local dev, or `https://your-backend.onrender.com` for production). If not set, it defaults to relative `/api`.

### Backend Variables (`backend/.env` or Server config)
*These must NEVER be exposed to the frontend.*
- `WORTH_IT_ADMIN_PIN`: Admin PIN to secure the settings page (Required for Production).
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot token. (Can also be configured via the UI securely).
- `TELEGRAM_CHAT_ID`: Your default chat ID.

## Deployment

### Frontend (Vercel)
Deploy the `frontend/` directory to Vercel. 
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- Ensure you set the `VITE_API_URL` environment variable in the Vercel dashboard to point to your backend.

### Backend (Render)
Deploy the `backend/` directory as a Web Service on Render using Docker.
- Render will use the `backend/Dockerfile` to build the Python environment.
- Set the `WORTH_IT_ADMIN_PIN` environment variable to secure your endpoints.

## Telegram Setup

To receive push notifications:
1. Message `@BotFather` on Telegram and send `/newbot`.
2. Copy the **Bot Token**.
3. Open the Worth-It Settings page, unlock it with your PIN, and securely enter the Bot Token. The token is never exposed back to the browser.
4. Message `@userinfobot` to get your personal Chat ID and use it when creating monitoring rules.

## Security

Worth-It implements an Administrative PIN (`WORTH_IT_ADMIN_PIN`). 
- **Localhost:** You can opt-out of security if the PIN is not set. 
- **Production:** The PIN is mandatory and must be provided via the server environment variable. The backend uses HTTP-only session cookies and robust API checks to protect configuration and Telegram secrets.

## API Architecture

Key API routers (located in `backend/app/api/routers/`):
- `/api/alerts`: Manage scanning rules, run immediate scans, and stop background runners.
- `/api/history`: Access historical deals and clear old data.
- `/api/location`: Proxy for geographic autocompletion (Nominatim).
- `/api/product`: Wishlist URL parsing and platform lookup.
- `/api/telegram`: Securely configure Telegram integration and trigger test alerts.
- `/api/auth`: Validate administrative PIN and provision sessions.

## Testing

Run the Python test suite using pytest:
```bash
cd backend
uv run python -m pytest tests/unit
```

## License

MIT License
