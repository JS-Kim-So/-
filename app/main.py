from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.ui_routes import ui_router

app = FastAPI(title="Inventory MVP-1")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(ui_router)
app.include_router(router)
