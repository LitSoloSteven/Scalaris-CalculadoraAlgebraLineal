"""Selección de recursos declarados según sus consumidores de página."""
import re
from functools import lru_cache

_INICIO = frozenset({"inicio"})
_NUMERICAS = frozenset({"bases", "romanos"})
_ALGEBRA = frozenset({"sistemas", "vectores", "matrices", "inversa", "determinantes", "factorizacion_lu",
                       "visualizador", "leontief", "transformaciones"})
_VISTAS = _INICIO | _NUMERICAS | _ALGEBRA
_POR_RECURSO = {
    "presentacion.css": _INICIO,
    "vistas_inicio_matriz.css": _INICIO,
    "vistas_inicio_ventanas_emergentes.css": _INICIO,
    "vistas_inicio_adaptable.css": _INICIO | frozenset({"sistemas", "inversa", "visualizador"}),
    "vistas_matrices.css": frozenset({"matrices"}),
    "vistas_vectores.css": frozenset({"vectores", "visualizador"}),
    "vistas_geometria.css": frozenset({"visualizador"}),
    "vistas_modelos.css": frozenset({"leontief", "transformaciones", "determinantes"}),
    "vistas_numericos.css": _NUMERICAS,
    "pasos_numericos.css": _NUMERICAS,
    "vistas_inversa.css": _ALGEBRA | _NUMERICAS,
    "inicio_entrada.js": _INICIO,
    "inicio.js": _INICIO,
    "sistemas_metodo.js": frozenset({"sistemas"}),
    "tema_graficos.js": frozenset({"visualizador"}),
    "sincronizacion_diseno.js": frozenset({"visualizador"}),
}
_ETIQUETAS = re.compile(
    r'<script\b[^>]*\bsrc="/assets/js/(?P<js>[^"/]+)"[^>]*>\s*</script>'
    r'|<link\b[^>]*\bhref="/assets/css/(?P<css>[^"/]+)"[^>]*>'
)


@lru_cache(maxsize=32)
def seleccionar_recursos(cabecera: str, vista: str) -> str:
    """Filtra etiquetas propias por vista; conserva el orden y las vistas desconocidas."""
    if vista not in _VISTAS:
        return cabecera

    def seleccionar(coincidencia: re.Match[str]) -> str:
        """Conserva la etiqueta cuando la página consume su recurso."""
        nombre = coincidencia.group("js") or coincidencia.group("css")
        permitidas = _POR_RECURSO.get(nombre, _VISTAS)
        return coincidencia.group() if vista in permitidas else ""

    return _ETIQUETAS.sub(seleccionar, cabecera)
