# Worth-It

A dedicated deal intelligence engine for Swiggy Instamart.

## Development

The simplest way to start the local development environment is using the launcher script:

```bash
./dev.sh
```

This will:
1. Start the FastAPI backend on http://127.0.0.1:8000
2. Start the Vite React frontend on http://localhost:5173
3. Handle live logs from both services.

To stop the services, press `Ctrl+C`.

### Prerequisites
- [uv](https://github.com/astral-sh/uv) (for the Python backend)
- [npm](https://www.npmjs.com/) (for the React frontend)

### Environment Variables
Copy the `backend/.env.example` file to `backend/.env` to configure your environment secrets (e.g. `TELEGRAM_BOT_TOKEN`).
Never commit secrets to the repository.
