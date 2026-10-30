"""Route stubs for the KounOS API (A03).

Every handler raises 501 until its implementing task lands. The detail
names that task so a 501 in the UI is traceable, not mysterious.
"""

from fastapi import APIRouter

from app.routers import decisions, events, notices, orders, quotes, solicitations

api_router = APIRouter()
api_router.include_router(solicitations.router)
api_router.include_router(quotes.router)
api_router.include_router(decisions.router)
api_router.include_router(orders.router)
api_router.include_router(orders.demo_router)
api_router.include_router(notices.router)
api_router.include_router(events.router)
