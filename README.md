<div align="center">
  <img src="frontend/public/worth-it-logo.png" alt="Worth-It Logo" width="120" style="border-radius: 20px; margin-bottom: 20px;" onerror="this.src='https://placehold.co/120x120/000000/FFFFFF.png?text=W'"/>
  
  <h1>Worth-It</h1>
  <p><strong>A deployable, multi-platform Quick-Commerce Deal Discovery & Price-Monitoring Engine</strong></p>

  <p>
    <a href="#features">Features</a> • 
    <a href="#architecture">Architecture</a> • 
    <a href="#installation">Installation</a> • 
    <a href="#usage">Usage</a>
  </p>
</div>

---

**Worth-It** is an automated deal-hunting and price-monitoring platform designed specifically for quick-commerce apps (Instamart, Zepto, Blinkit, Flipkart Minutes). It scans multiple platforms continuously, tracking product availability and finding extreme discounts in your local geographic radius.

Built with a philosophy of stability and isolation, Worth-It automatically navigates platform WAFs, dynamically resolves headless browser sessions, and pushes deals directly to you via an interactive dashboard and Telegram notifications.

---

## ✨ Features

- 🛒 **Multi-Platform Monitoring:** Scans Swiggy Instamart, Zepto, Blinkit, and Flipkart Minutes simultaneously.
- 📍 **Geographic Expansion (CartRadar Engine):** Intelligently expands search radius by mapping out local "dark stores" and querying them directly.
- 🎯 **Advanced Rules Engine:** Set rules like "Notify if price drops by 30%", "Notify if price is under ₹100", or "Notify only if it's a historical low".
- 📱 **Real-Time Dashboard (SSE):** Watch the scanner work live. See deals pop up on the geographic map the second they are found.
- 🔔 **Telegram Notifications:** Get instant alerts on your phone when high-value deals are discovered.
- 🛡️ **WAF & Rate Limit Resilience:** Leverages dynamic Playwright headless browser routing to safely bypass complex Cloudflare/Datadome protections (especially Zepto).
- 🔄 **Continuous Background Scheduler:** Runs entirely hands-off. Define your alerts and let the APScheduler backend scan at regular intervals.
- 🚀 **One-Click Launchers:** Deploy and run with zero terminal knowledge using OS-specific launchers (`Worth-It.command`, `Worth-It.bat`).

---

## 🏗️ Architecture

Worth-It is split into a highly-concurrent Python backend and a reactive React frontend:

- **Backend:** `FastAPI`, `Playwright` (Headless Firefox/Chromium), `SQLite`, `APScheduler`.
- **Frontend:** `React`, `Vite`, `TailwindCSS`, `React-Leaflet`.

The backend uses a **Platform Adapter Pattern** (`PlatformClient`). If one platform blocks the scanner or goes down, it **does not** impact the scanning of the others. All data is standardized into canonical `PlatformProduct` and `Store` domain models. 

For a deep dive into the architectural design and rules engine, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🚀 Installation

Worth-It comes with unified installation scripts designed to set up the entire environment (Python, Node, Docker) automatically.

### Prerequisites
- [Docker & Docker Compose](https://docs.docker.com/get-docker/) (Required for Playwright browser dependencies)
- Git

### Automated Install

1. Clone the repository:
   ```bash
   git clone https://github.com/Harsh-Gopal/Worth-It.git
   cd Worth-It
   ```

2. Run the installer for your OS:
   - **macOS / Linux:** Double-click `Worth-It Install.command` or run `./Worth-It\ Install.sh`
   - **Windows:** Double-click `Worth-It Install.bat`

This script will automatically create `.env` files, build the Docker containers, and provision the internal SQLite database.

---

## 🎮 Usage

### Starting the Application

Once installed, use the run launchers to start the full stack:

- **macOS / Linux:** Double-click `Worth-It.command`
- **Windows:** Double-click `Worth-It.bat`

The UI will automatically open at `http://localhost:5173`. The FastAPI backend runs on `http://localhost:8000`.

### Core Workflows

1. **Live Scanning:** Go to the **Live Monitor** tab, enter keywords (e.g. `Amul Butter`, `Eggs`), select your target platforms, set your minimum discount, and hit "Scan". Watch the map populate with dark stores.
2. **Wishlist Tracking:** Copy/paste direct product URLs from Instamart or Zepto into the Wishlist. The engine will extract the canonical product ID and scan for that exact item.
3. **Background Alerts:** Go to **Alerts**, create a new rule with your Telegram Chat ID. The backend scheduler will run this rule every 30 minutes.

### Setting up Telegram

To receive push notifications, you need a Telegram Bot:
1. Message `@BotFather` on Telegram and send `/newbot`.
2. Copy the **Bot Token** provided.
3. Edit the `backend/.env` file and set `TELEGRAM_BOT_TOKEN="your_token_here"`.
4. Message `@userinfobot` to get your personal Chat ID and use it when creating Alerts.

---

## 🛠️ Tech Stack & Dependencies

- **uv:** Ultra-fast Python package installer and resolver.
- **httpx / asyncio:** Core async HTTP engine for concurrent platform probing.
- **Playwright:** Headless browser automation (specifically tuned with Firefox for Zepto BFF interception).
- **SQLite (WAL mode):** High-concurrency local database for Price History, Stores, and Alerts.

---

*Built for the thrill of the deal.*
