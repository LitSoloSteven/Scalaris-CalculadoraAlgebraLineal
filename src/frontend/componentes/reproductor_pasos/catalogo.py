"""Catálogo visual y velocidades disponibles para reproducir pasos."""
from __future__ import annotations

import html

CATALOGO_TIPOS = {
    "menor": {"etiqueta": "Menor", "icono": "grid_on"},
    "inicial": {"etiqueta": "Inicio", "icono": "grid_on"},
    "intercambio": {"etiqueta": "Intercambio", "icono": "swap_vert"},
    "pivote": {"etiqueta": "Pivote", "icono": "gps_fixed"},
    "eliminacion": {"etiqueta": "Eliminación", "icono": "exposure"},
    "normalizacion": {"etiqueta": "Normalización", "icono": "looks_one"},
    "otro": {"etiqueta": "Operación", "icono": "tune"},
    "final": {"etiqueta": "Resultado", "icono": "check_circle"},
    "planteamiento": {"etiqueta": "Planteamiento", "icono": "subject"},
    "sustitucion": {"etiqueta": "Sustitución", "icono": "swap_horiz"},
    "verificacion": {"etiqueta": "Verificación", "icono": "fact_check"},
    "operacion": {"etiqueta": "Operación", "icono": "tune"},
    "componente": {"etiqueta": "Componente", "icono": "call_split"},
    "ajuste": {"etiqueta": "Ajuste", "icono": "tune"},
    "expansion": {"etiqueta": "Expansión", "icono": "open_in_full"},
    "division": {"etiqueta": "División", "icono": "functions"},
    "lectura": {"etiqueta": "Lectura", "icono": "visibility"},
    "decodificacion": {"etiqueta": "Decodificación", "icono": "code"},
    "construccion": {"etiqueta": "Construcción", "icono": "build"},
    "resultado": {"etiqueta": "Resultado", "icono": "check_circle"},
}
VELOCIDADES_AUTOREPRODUCCION = {"Lenta": 1.2, "Normal": 0.7, "Rápida": 0.4}
MULTIPLICADORES_LECTURA = {"Lenta": 1.0, "Normal": 0.6, "Rápida": 0.35}
SEGUNDOS_BASE_LECTURA = 3.5
SEGUNDOS_POR_CARACTER = 0.055
INTERVALO_MINIMO_LECTURA = 4.0
INTERVALO_MAXIMO_LECTURA = 15.0
DIMENSION_MAXIMA_FRACCIONES_APILADAS = 6


def intervalo_lectura(explicacion: str, velocidad: str) -> float:
    """Devuelve segundos de lectura acotados antes de aplicar la velocidad indicada."""
    base = SEGUNDOS_BASE_LECTURA + SEGUNDOS_POR_CARACTER * len(explicacion)
    acotado = max(INTERVALO_MINIMO_LECTURA, min(base, INTERVALO_MAXIMO_LECTURA))
    return acotado * MULTIPLICADORES_LECTURA.get(velocidad, MULTIPLICADORES_LECTURA["Normal"])


def html_sugerencia_tipo(tipo: str, etiqueta: str | None = None) -> str:
    """Genera el HTML del chip con etiqueta escapada e icono del catálogo."""
    meta = CATALOGO_TIPOS.get(tipo, CATALOGO_TIPOS["otro"])
    clase = html.escape(tipo, quote=True)
    texto = html.escape(etiqueta if etiqueta is not None else meta["etiqueta"])
    return (
        f'<span class="pasos-distintivo-tipo pasos-etiqueta-{clase}">'
        f'<span class="material-icons">{meta["icono"]}</span>{texto}</span>'
    )
