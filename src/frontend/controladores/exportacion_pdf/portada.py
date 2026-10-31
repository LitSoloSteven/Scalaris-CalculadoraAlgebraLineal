"""Validación efímera de la portada y nombres seguros de descarga."""
import re
import unicodedata
from datetime import date

from src.frontend import constantes as limites, textos
from .glifos import texto_admitido

_LIMITES = {'nombre': limites.PDF_MAXIMO_NOMBRE, 'docente': limites.PDF_MAXIMO_DOCENTE,
            'grupo': limites.PDF_MAXIMO_GRUPO}


def validar_portada(datos: dict) -> tuple[dict[str, str], dict[str, str]]:
    """Devuelve datos normalizados y errores por campo sin conservar información personal."""
    portada, errores = {}, {}
    for campo, limite in _LIMITES.items():
        valor = datos.get(campo, '')
        valor = valor.strip() if isinstance(valor, str) else ''
        portada[campo] = valor
        error = _error_texto(campo, valor, limite)
        if error:
            errores[campo] = error
    fecha = datos.get('fecha', '')
    try:
        if not isinstance(fecha, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fecha):
            raise ValueError
        portada['fecha'] = date.fromisoformat(fecha).isoformat()
    except ValueError:
        errores['fecha'] = textos.PDF_ERROR_FECHA
    return portada, errores


def _error_texto(campo: str, valor: str, limite: int) -> str | None:
    if not valor:
        return textos.PDF_ERROR_CAMPO.format(campo=textos.PDF_ERRORES_VACIOS[campo])
    if len(valor) > limite:
        return textos.PDF_ERROR_LONGITUD.format(limite=limite)
    if not texto_admitido(valor):
        return textos.PDF_ERROR_CARACTERES
    if campo == 'grupo' and not re.fullmatch(r'[A-Za-z0-9]+', valor):
        return textos.PDF_ERROR_GRUPO
    return None


def fecha_espanola(fecha_iso: str) -> str:
    """Convierte una fecha ISO válida a español sin depender del locale; lanza ValueError."""
    fecha = date.fromisoformat(fecha_iso)
    return textos.PDF_FECHA.format(dia=fecha.day, mes=textos.PDF_MESES[fecha.month - 1], anio=fecha.year)


def nombre_archivo(herramienta: str, fecha_iso: str) -> str:
    """Devuelve un nombre ASCII sin rutas para una fecha ISO válida; lanza ValueError."""
    fecha = date.fromisoformat(fecha_iso).isoformat()
    nombre = unicodedata.normalize('NFKD', herramienta).encode('ascii', 'ignore').decode('ascii')
    nombre = re.sub(r'[^A-Za-z0-9]+', '_', nombre).strip('_')
    nombre = nombre[:limites.PDF_MAXIMO_IDENTIFICADOR_ARCHIVO] or 'resultado'
    return f'Scalaris_{nombre}_{fecha}.pdf'
