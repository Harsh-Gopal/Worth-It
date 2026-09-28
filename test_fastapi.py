import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
app = FastAPI()
@app.get("/test", response_model=list[dict])
def test_route():
    return [{"time": datetime.now()}]

client = TestClient(app)
print(client.get("/test").json())
