from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Inventory MVP-1")
app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Inventory MVP-1 API",
        "docs": "/docs",
        "expansion_notes": "REVERSAL and other extensions documented in README",
    }
