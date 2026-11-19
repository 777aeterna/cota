"""Factoría principal de la aplicación FastAPI de Cota."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from cota import __version__
from cota.api.routes import data, fitting, metrology, propagation, units
from cota.api.schemas import HealthResponse
from cota.web import STATIC_DIR


def create_app() -> FastAPI:
    """Construye y configura la instancia principal de FastAPI."""
    app = FastAPI(
        title="Cota API",
        description="API REST de análisis experimental, metrología GUM y ajuste de curvas.",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.get("/api/health", response_model=HealthResponse, tags=["Sistema"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    app.include_router(metrology.router)
    app.include_router(units.router)
    app.include_router(propagation.router)
    app.include_router(fitting.router)
    app.include_router(data.router)

    # Interfaz web: estáticos en /static y la SPA en /
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})

    return app
