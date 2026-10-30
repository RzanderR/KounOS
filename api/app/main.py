"""KounOS API entrypoint (A01 scaffold)."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.routers import api_router

app = FastAPI(title="KounOS API")
app.include_router(api_router)

# Allowed origins come from CORS_ORIGINS (comma-separated) so the hosted
# web URL can be added later. Exposed PDF headers let hosted, cross-origin
# viewers use range requests.
_cors = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors.cors_origins.split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range", "Accept-Ranges"],
)


@app.get("/health")
def read_health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Health route used by the web shell and CI smoke checks."""
    return {"status": "ok", "demo_mode": settings.demo_mode}
