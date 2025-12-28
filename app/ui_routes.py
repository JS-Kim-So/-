from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui_router = APIRouter()


def _render_page(filename: str) -> HTMLResponse:
    html = Path("templates") / filename
    return HTMLResponse(html.read_text(encoding="utf-8"))


@ui_router.get("/", response_class=HTMLResponse)
def dashboard_page():
    return _render_page("dashboard.html")


@ui_router.get("/ui/products", response_class=HTMLResponse)
def products_page():
    return _render_page("products.html")


@ui_router.get("/ui/lots", response_class=HTMLResponse)
def lots_page():
    return _render_page("lots.html")


@ui_router.get("/ui/inbound", response_class=HTMLResponse)
def inbound_page():
    return _render_page("inbound.html")


@ui_router.get("/ui/outbound", response_class=HTMLResponse)
def outbound_page():
    return _render_page("outbound.html")


@ui_router.get("/ui/transactions", response_class=HTMLResponse)
def transactions_page():
    return _render_page("transactions.html")
