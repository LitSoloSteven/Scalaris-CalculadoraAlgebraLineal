"""Lectura conjunta de los recursos de interacciones compartidos con producción."""
import json
from tests.comun import RAIZ


def leer_interacciones_cliente():
    """Conserva el alcance de comprobaciones que cubrían el módulo monolítico."""
    return _leer_codigo_catalogo("catalogo_interacciones.json")


def leer_captura_cliente(nombre_adaptador):
    """Incluye toda la lógica extraída que correspondía al adaptador monolítico."""
    return _leer_codigo_catalogo("catalogo_captura.json", [nombre_adaptador])


def _leer_codigo_catalogo(nombre_catalogo, adicionales=()):
    activos = RAIZ / "src" / "frontend" / "recursos"
    nombres = json.loads((activos / nombre_catalogo).read_text(encoding="utf-8"))
    return "\n".join((activos / "js" / nombre).read_text(encoding="utf-8")
                     for nombre in nombres + list(adicionales))
