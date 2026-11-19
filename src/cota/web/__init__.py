"""Interfaz web de Cota (SPA sin paso de compilación servida por FastAPI)."""

from pathlib import Path

STATIC_DIR: Path = Path(__file__).resolve().parent / "static"
