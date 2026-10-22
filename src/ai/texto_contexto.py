"""Saneamiento y representación compacta de texto del contexto de IA."""
import re
from src.ai.constantes import LONGITUD_MAXIMA_CADENA_USUARIO, LONGITUD_MAXIMA_NUMERO


def recortar_texto(texto: str, longitud_maxima: int) -> str:
    """Acota una cadena y añade puntos suspensivos cuando excede la longitud."""
    cadena = str(texto)
    if len(cadena) <= longitud_maxima:
        return cadena
    return cadena[:longitud_maxima - 1] + "…"


def sanear_cadena_usuario(cadena: str, limite: int = LONGITUD_MAXIMA_CADENA_USUARIO) -> str:
    """Retira controles y delimitadores que podrían insertar otro bloque de contexto."""
    texto = str(cadena)
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)
    texto = re.sub(r"(?i)\[/?CONTEXTO\]", "", texto)
    return recortar_texto(texto, limite)


def compactar_numero(valor: str, longitud_maxima: int = LONGITUD_MAXIMA_NUMERO) -> str:
    """Conserva valores cortos y aproxima fracciones largas para su presentación."""
    cadena = str(valor).strip()
    if len(cadena) <= longitud_maxima:
        return cadena
    if "/" in cadena:
        try:
            numerador, denominador = cadena.split("/")
            aproximacion = f"≈{float(numerador) / float(denominador):.1f}"
            if len(aproximacion) <= longitud_maxima:
                return aproximacion
        except Exception:
            pass
    return recortar_texto(cadena, longitud_maxima)
