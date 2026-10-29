"""KounOS API entrypoint (A01 scaffold)."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.routers import api_router

app = FastAPI(title="KounOS API")
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def read_health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Health route used by the web shell and CI smoke checks."""
    return {"status": "ok", "demo_mode": settings.demo_mode}
