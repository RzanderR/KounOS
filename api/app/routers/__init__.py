"""Every KounOS API router, mounted under one APIRouter."""

from fastapi import APIRouter

from app.routers import decisions, events, impact, notices, orders, quotes, solicitations

api_router = APIRouter()
api_router.include_router(solicitations.router)
api_router.include_router(quotes.router)
api_router.include_router(decisions.router)
api_router.include_router(orders.router)
api_router.include_router(orders.demo_router)
api_router.include_router(notices.router)
api_router.include_router(events.router)
api_router.include_router(impact.router)
