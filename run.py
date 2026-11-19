#!/usr/bin/env python3
"""Lanzador de Cota: arranca el servidor local y abre la interfaz en el navegador."""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

# Permitir ejecutar `python run.py` directo tras clonar, incluso antes de `pip install -e .`
_SRC_DIR = Path(__file__).resolve().parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


def find_free_port(preferred: int = 8000, host: str = "127.0.0.1", attempts: int = 20) -> int:
    """Devuelve `preferred` si está libre, o el siguiente puerto disponible."""
    for offset in range(attempts):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _open_browser_when_ready(url: str, health_url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=0.5) as resp:
                if resp.status == 200:
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.15)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cota",
        description="Cota — Plataforma de análisis experimental, metrología GUM y ajuste de curvas.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Dirección de escucha (por defecto 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Puerto preferido (por defecto 8000)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir el navegador automáticamente")
    args = parser.parse_args(argv)

    port = find_free_port(preferred=args.port, host=args.host)
    url = f"http://{args.host}:{port}"
    print(f"\n  Cota está corriendo en: {url}\n  Presioná Ctrl+C para detener el servidor.\n")

    if not args.no_browser:
        t = threading.Thread(
            target=_open_browser_when_ready,
            args=(url, f"{url}/api/health"),
            daemon=True,
        )
        t.start()

    import uvicorn

    uvicorn.run(
        "cota.api:create_app",
        factory=True,
        host=args.host,
        port=port,
        ws="none",
        log_level="warning",
    )


if __name__ == "__main__":
    main()
