"""Catálogo de iconos vectoriales SVG para la interfaz de Scalaris."""
from __future__ import annotations

# Catálogo declarativo de datos puros: mapea nombres a marcado vectorial interno.
CATALOGO_ICONOS: dict[str, str] = {
    "sonido": (
        '<path d="M11 5 6 9H3v6h3l5 4z"></path>'
        '<path d="M15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"></path>'
    ),
    "sonido_silenciado": (
        '<path d="M11 5 6 9H3v6h3l5 4z"></path>'
        '<path d="m16 9 6 6m0-6-6 6"></path>'
    ),
    "factorizacion_lu": (
        '<path d="M4 7v12h5"></path>'
        '<path d="M13 5v8a3.5 3.5 0 0 0 7 0V5"></path>'
    ),
    "determinantes": (
        '<path d="M5 4v16"></path>'
        '<path d="M19 4v16"></path>'
        '<path d="M9 9h.01m6 0h.01M9 15h.01m6 0h.01"></path>'
    ),
    "sistemas_lineales": (
        '<path d="m2 15 3-7 3 7m-5-2h4"></path>'
        '<path d="m10 11 3 4m0-4-3 4"></path>'
        '<path d="M15.5 11H18m-2.5 3H18"></path>'
        '<path d="M20 8v7h1a2 2 0 0 0 0-4h-1"></path>'
    ),
    "metodos_iterativos": (
        '<path d="M19 10a7 7 0 1 0 0 5"></path>'
        '<path d="M19 5v5h-5"></path>'
    ),
    "operaciones_matrices": (
        '<path d="M4 6H2v12h2m3 0h2V6H7M5.5 10h.01m-.01 4h.01"></path>'
        '<path d="M10.5 12h3m-1.5-1.5v3"></path>'
        '<path d="M17 6h-2v12h2m3 0h2V6h-2m-1.5 4h.01m-.01 4h.01"></path>'
    ),
    "conversor_bases": (
        '<rect x="3" y="4" width="3" height="5" rx="1"></rect>'
        '<line x1="8" y1="4" x2="8" y2="9"></line>'
        '<path d="M15 20l2.5-6 2.5 6"></path>'
        '<line x1="16" y1="18" x2="19" y2="18"></line>'
        '<path d="M12 3a9 9 0 0 1 8 5"></path>'
        '<polyline points="20,5 20,8 17,8"></polyline>'
        '<path d="M12 21a9 9 0 0 1-8-5"></path>'
        '<polyline points="4,19 4,16 7,16"></polyline>'
    ),
    "tutor_ia": (
        '<path d="M2 11l9-4 9 4-9 4-9-4z"></path>'
        '<path d="M5 12.3v3.7c0 1.5 3.1 2.7 7 2.7s7-1.2 7-2.7v-3.7"></path>'
        '<path d="M19 2l1 2 2 1-2 1-1 2-1-2-2-1 2-1z" fill="currentColor" stroke="none"></path>'
    ),
    "vectores": (
        '<path d="M5 7h14m-3-3 3 3-3 3"></path>'
        '<path d="m8 13 4 7 4-7"></path>'
    ),
    "temas": (
        '<circle cx="12" cy="12" r="8"></circle>'
        '<path d="M17.65 6.35A8 8 0 0 0 6.35 17.65Z" fill="currentColor" stroke="none"></path>'
    ),
    "matriz_inversa": (
        '<path d="m3 19 5-13 5 13m-8-4h6"></path>'
        '<path d="M14 7h3m2-1 2-2v6"></path>'
    ),
    "leontief": (
        '<path d="M2 6h5M4.5 6v12M2 18h5"></path>'
        '<path d="M10 12h4"></path>'
        '<path d="M21 7c-6-3-6 13 0 10"></path>'
    ),
    "transformaciones": (
        '<path d="M3 6h9m-4.5 0v12"></path>'
        '<path d="M13 12h8m-3-3 3 3-3 3"></path>'
    ),
    "metodos_cerrados": (
        '<path d="M4 12h16"></path>'
        '<path d="M4 8v8"></path>'
        '<path d="M20 8v8"></path>'
        '<circle cx="12" cy="12" r="1.8" fill="currentColor" stroke="none"></circle>'
    ),
    "metodos_abiertos": (
        '<path d="M3 19c8 0 12-4 17-14"></path>'
        '<path d="m10 21 10-16"></path>'
        '<circle cx="20" cy="5" r="1.8" fill="currentColor" stroke="none"></circle>'
        '<circle cx="10" cy="21" r="1.4" fill="currentColor" stroke="none"></circle>'
    ),
    "inicio": (
        '<path d="M4 11.5 12 5l8 6.5"></path>'
        '<path d="M6 10v9h12v-9"></path>'
        '<path d="M10 19v-5h4v5"></path>'
    ),
    "seccion-sistemas-lineales": (
        '<path d="M9 4H7a2 2 0 0 0-2 2v3c0 2-1 3-3 3 2 0 3 1 3 3v3a2 2 0 0 0 2 2h2"></path>'
        '<path d="M15 4h2a2 2 0 0 1 2 2v3c0 2 1 3 3 3-2 0-3 1-3 3v3a2 2 0 0 1-2 2h-2"></path>'
    ),
    "seccion-matrices": (
        '<path d="M8 4H5v16h3m1-12h.01M9 12h.01M9 16h.01"></path>'
        '<path d="M16 4h3v16h-3M15 8h.01M15 12h.01M15 16h.01"></path>'
    ),
    "seccion-vectores-geometria": (
        '<path d="M4 19 19 5m-8 0h8v8"></path>'
    ),
    "seccion-metodos-numericos": (
        '<path d="M3 14h18M4 20c8 0 9-8 16-15"></path>'
        '<circle cx="17" cy="8" r="1.8" fill="currentColor" stroke="none"></circle>'
    ),
    "seccion-sistemas-numeracion": (
        '<path d="M3 9h6v8H3z"></path>'
        '<path d="m14 11 4-3v9m-3 0h6"></path>'
    ),
    "algebra_lineal": (
        '<path d="M7 4H5v16h2"></path>'
        '<path d="M17 4h2v16h-2"></path>'
        '<circle cx="10" cy="9" r="1" fill="currentColor" stroke="none"></circle>'
        '<circle cx="14" cy="9" r="1" fill="currentColor" stroke="none"></circle>'
        '<circle cx="10" cy="15" r="1" fill="currentColor" stroke="none"></circle>'
        '<circle cx="14" cy="15" r="1" fill="currentColor" stroke="none"></circle>'
    ),
    "utilidades": (
        '<path d="M5 8h14"></path>'
        '<path d="M5 16h14"></path>'
        '<path d="M9 4 7 20"></path>'
        '<path d="M17 4l-2 16"></path>'
    ),
    "geometria": (
        '<path d="M12 3 4 7.5v9L12 21l8-4.5v-9z"></path>'
        '<path d="M12 12 4 7.5"></path>'
        '<path d="M12 12l8-4.5"></path>'
        '<path d="M12 12v9"></path>'
    ),
    "romanos": (
        '<path d="M3 6l6 12M9 6 3 18"></path>'
        '<path d="m12 6 3 12 3-12"></path>'
        '<path d="M21 6v12"></path>'
    ),
    "glosa": (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
        '<polyline points="14 2 14 8 20 8"></polyline>'
        '<line x1="16" y1="13" x2="8" y2="13"></line>'
        '<line x1="16" y1="17" x2="8" y2="17"></line>'
        '<line x1="4" y1="4" x2="4" y2="20"></line>'
    ),
    "explicar_paso": (
        '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>'
        '<line x1="12" y1="9" x2="12" y2="9.01"></line>'
        '<path d="M12 13v4"></path>'
    ),
    "escena_rectas_planos": (
        '<path d="m4 18 16-12"></path>'
        '<path d="m5 6 14 12"></path>'
    ),
    "escena_vectores": (
        '<path d="M4 19 10 5m-5 3 5-3 2 5"></path>'
        '<path d="m4 19 16-6m-6-2 6 2-3 5"></path>'
    ),
    "escena_combinacion": (
        '<path d="M4 19V6M2 8l2-2 2 2"></path>'
        '<path d="m10 19 11-8m-5 0h5v5"></path>'
        '<path d="M8 12h5m-2.5-2.5v5"></path>'
    ),
    "abrir": (
        '<polyline points="7 10 12 15 17 10"></polyline>'
    ),
    "cerrar": (
        '<line x1="6" y1="6" x2="18" y2="18"></line>'
        '<line x1="18" y1="6" x2="6" y2="18"></line>'
    ),
}

_BASE_INICIO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" '
    'class="icono-svg" aria-hidden="true">'
)


def icono_svg(nombre: str) -> str:
    """Devuelve el fragmento SVG correspondiente al nombre consultado."""
    cuerpo = CATALOGO_ICONOS.get(nombre)
    return f"{_BASE_INICIO}{cuerpo}</svg>" if cuerpo else ""
