"""Lectura compartida de texto tabular del portapapeles."""
from io import StringIO


def parsear_texto_portapapeles(texto: str) -> list[list[str]]:
    """Convierte texto separado por filas y tabuladores, comas o espacios en celdas."""
    lineas = [linea.strip() for linea in texto.strip().splitlines() if linea.strip()]
    resultado = []
    for linea in lineas:
        delimitador = "\t" if "\t" in linea else "," if "," in linea else " "
        celdas = [celda.strip() for celda in linea.split(delimitador) if celda.strip()]
        if celdas:
            resultado.append(celdas)
    return resultado


def parsear_portapapeles_rectangular(texto: str, limite: int) -> tuple[list[list[str]], bool]:
    """Lee hasta el límite de filas y columnas, conserva huecos e indica si hubo recorte."""
    resultado = []
    recortado = False
    for linea in StringIO(texto):
        linea = linea.strip("\r\n")
        if not linea.strip() and "\t" not in linea:
            continue
        if len(resultado) == limite:
            recortado = True
            break
        delimitador = "\t" if "\t" in linea else "," if "," in linea else None
        celdas = linea.split(delimitador, limite)
        recortado = recortado or len(celdas) > limite
        resultado.append([celda.strip() or "0" for celda in celdas[:limite]])
    return resultado, recortado
