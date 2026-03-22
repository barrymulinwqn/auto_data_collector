from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import data, test

app = FastAPI(
    title="Auto Data Collector API",
    description="Backend API for auto data collection",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(test.router, prefix="/api/test", tags=["test"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
