"""Banderas de evaluación y preparación de transferencias matriciales."""
import re
from src.backend.constantes import DIMENSION_MAXIMA_MATRICES


def calcular_banderas_resultado(resultado: dict, expresion: str) -> dict[str, bool]:
    """Devuelve señales de producto y dimensiones conservando la clasificación vigente."""
    mensaje = resultado.get("mensaje", "").lower()
    return {
        "contiene_producto": resultado.get("estado") == "EXITO" and bool(
            re.search(r'[A-Z)]\s*\*?\s*[A-Z(]', expresion)
        ),
        "error_dimensiones": resultado.get("estado") == "ERROR" and (
            "dimensi" in mensaje or "tamaño" in mensaje
        ),
    }


def preparar_transferencia_inversa(nombre: str, datos_matriz: dict) -> dict:
    """Valida la derivación a inversa y devuelve datos crudos o mensaje de orientación."""
    filas, columnas = datos_matriz["filas"], datos_matriz["columnas"]
    if filas != columnas:
        return {"mensaje": f"La matriz {nombre} debe ser cuadrada para invertirla."}
    if filas > DIMENSION_MAXIMA_MATRICES:
        return {"mensaje": (
            f"La herramienta de inversa admite hasta {DIMENSION_MAXIMA_MATRICES}x{DIMENSION_MAXIMA_MATRICES}. "
            f"La matriz {nombre} es de {filas}x{columnas}."
        )}
    datos = [[str(valor).strip() or "0" for valor in fila] for fila in datos_matriz["datos"]]
    return {"datos": datos}
