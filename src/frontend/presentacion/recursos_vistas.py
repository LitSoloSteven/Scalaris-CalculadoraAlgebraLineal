"""Selección de recursos declarados según sus consumidores de página."""
import re
from functools import lru_cache

_INICIO = frozenset({"inicio"})
_NUMERICAS = frozenset({"bases", "romanos"})
_BISECCION = frozenset({"biseccion"})
_REGLA_FALSA = frozenset({"regla_falsa"})
_METODOS_ABIERTOS = frozenset({"metodos_abiertos"})
_METODOS_CERRADOS = frozenset({"metodos_cerrados"})
_METODOS_ITERATIVOS = frozenset({"metodos_iterativos"})
_ESPACIOS_SUBESPACIOS = frozenset({"espacios_subespacios"})
_RAICES = _BISECCION | _REGLA_FALSA | _METODOS_ABIERTOS | _METODOS_CERRADOS
_ALGEBRA = frozenset({"sistemas", "vectores", "matrices", "inversa", "determinantes", "factorizacion_lu",
                       "visualizador", "leontief", "transformaciones"})
_VISTAS = _INICIO | _NUMERICAS | _ALGEBRA | _RAICES | _METODOS_ITERATIVOS | _ESPACIOS_SUBESPACIOS
_EXPORTACION_PDF = _ALGEBRA | _NUMERICAS | _METODOS_ITERATIVOS | _ESPACIOS_SUBESPACIOS
_POR_RECURSO = {
    "sonido/motor/catalogo_sonidos.js": _VISTAS,
    "sonido/motor/sintesis_sonora.js": _VISTAS,
    "sonido/motor/asignacion_sonora.js": _VISTAS,
    "sonido/eventos/eventos_sonoros.js": _VISTAS,
    "utilidades/exportacion_pdf.css": _EXPORTACION_PDF,
    "herramientas/documentos/clon_pdf.js": _EXPORTACION_PDF,
    "herramientas/documentos/captura_pdf.js": _EXPORTACION_PDF,
    "inicio/presentacion.css": _INICIO,
    "inicio/vistas_inicio_directorio.css": _INICIO,
    "inicio/vistas_inicio_ejemplos.css": _INICIO,
    "inicio/vistas_inicio_adaptable.css": frozenset({"sistemas", "inversa", "visualizador"}),
    "algebra/matrices/vistas_matrices.css": frozenset({"matrices"}),
    "algebra/espacios/vistas_vectores.css": frozenset({"vectores", "visualizador"}) | _ESPACIOS_SUBESPACIOS,
    "algebra/espacios/vistas_metodos_iterativos.css": _METODOS_ITERATIVOS,
    "algebra/espacios/vistas_subespacios.css": _ESPACIOS_SUBESPACIOS,
    "algebra/espacios/vistas_geometria.css": frozenset({"visualizador"}),
    "algebra/matrices/vistas_modelos.css": frozenset({"leontief", "transformaciones", "determinantes"}),
    "numericos/sistemas/vistas_numericos.css": _NUMERICAS,
    "numericos/sistemas/pasos_numericos.css": _NUMERICAS,
    "algebra/matrices/vistas_inversa.css": _ALGEBRA | _NUMERICAS | _RAICES | _METODOS_ITERATIVOS | _ESPACIOS_SUBESPACIOS,
    "numericos/raices/vistas_biseccion.css": _BISECCION,
    "numericos/raices/vistas_regla_falsa.css": _REGLA_FALSA,
    "numericos/raices/estructura_metodos_raices.css": _METODOS_ABIERTOS | _METODOS_CERRADOS,
    "numericos/raices/vistas_metodos_abiertos.css": _METODOS_ABIERTOS,
    "numericos/raices/vistas_metodos_cerrados.css": _METODOS_CERRADOS,
    "inicio/inicio_entrada.js": _INICIO,
    "inicio/inicio.js": _INICIO,
    "inicio/ejemplos_inicio.js": _INICIO,
    "herramientas/algebra/sistemas_metodo.js": frozenset({"sistemas"}),
    "herramientas/algebra/iterativos_historial.js": _METODOS_ITERATIVOS,
    "nucleo/tema/tema_graficos.js": frozenset({"visualizador"}) | _RAICES | _ESPACIOS_SUBESPACIOS,
    "herramientas/biseccion/grafico_biseccion.js": _BISECCION,
    "herramientas/biseccion/movimiento_biseccion.js": _BISECCION,
    "herramientas/biseccion/banda_biseccion.js": _BISECCION,
    "herramientas/biseccion/paso_biseccion.js": _BISECCION,
    "herramientas/algebra/sincronizacion_diseno.js": frozenset({"visualizador"}),
}
_ETIQUETAS = re.compile(
    r'<script\b[^>]*\bsrc="/assets/js/(?P<js>[^"]+)"[^>]*>\s*</script>'
    r'|<link\b[^>]*\bhref="/assets/css/(?P<css>[^"]+)"[^>]*>'
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
