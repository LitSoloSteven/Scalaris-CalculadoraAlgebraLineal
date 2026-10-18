"""Punto de composición y arranque del servidor web de Scalaris."""
import logging
import os
from pathlib import Path
from typing import Mapping
from nicegui import app, ui

from src.frontend.rutas import registrar_rutas
from src.frontend.textos import (
    MENSAJE_ERROR_PRODUCCION_SIN_SECRETO,
    MENSAJE_SECRETO_DESARROLLO_INSEGURO,
)

registro = logging.getLogger(__name__)

_INICIALIZADO: bool = False
DIRECTORIO_RECURSOS = Path(__file__).resolve().parent / "recursos"


def resolver_secreto_almacenamiento(variables_entorno: Mapping[str, str]) -> str:
    """Devuelve la clave de sesión de NiceGUI según las variables recibidas.
    En producción lanza SystemExit cuando falta STORAGE_SECRET."""
    entorno = variables_entorno.get("SCALARIS_ENV", "").strip().lower()
    secreto = variables_entorno.get("STORAGE_SECRET", "").strip()

    if entorno == "production":
        if not secreto:
            raise SystemExit(MENSAJE_ERROR_PRODUCCION_SIN_SECRETO)
        return secreto

    if not secreto:
        registro.warning(MENSAJE_SECRETO_DESARROLLO_INSEGURO)
        return "scalaris_dev_secret_key"

    return secreto


def inicializar_aplicacion() -> None:
    """Configura los archivos estáticos y registra las rutas de la aplicación."""
    global _INICIALIZADO
    if _INICIALIZADO:
        return

    entorno = os.environ.get("SCALARIS_ENV", "").strip().lower()
    max_edad_cache = 3600 if entorno == "production" else 0
    app.add_static_files("/assets", str(DIRECTORIO_RECURSOS), max_cache_age=max_edad_cache)
    registrar_rutas()
    _INICIALIZADO = True


def ejecutar() -> None:
    """Inicia el bucle principal de servicio de la interfaz web."""
    inicializar_aplicacion()
    secreto = resolver_secreto_almacenamiento(os.environ)
    ui.run(
        title="Scalaris",
        favicon=str(DIRECTORIO_RECURSOS / "LogoOscuro.png"),
        storage_secret=secreto,
    )


if __name__ in {"__main__", "__mp_main__"}:
    from dotenv import load_dotenv

    load_dotenv(".env")
    load_dotenv("src/ai/.env")
    ejecutar()
