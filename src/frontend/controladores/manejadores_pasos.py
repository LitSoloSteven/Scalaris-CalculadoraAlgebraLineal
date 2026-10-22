"""Manejadores atómicos y constructores pedagógicos para pasos de eliminación."""
from dataclasses import dataclass

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import formatear_fraccion_texto


@dataclass(frozen=True)
class ContextoPasos:
    """Parámetros de contexto para el procesamiento de pasos de eliminación."""

    contexto: str
    columnas_izquierda: int
    es_gauss: bool
    estado_resp: str | None = None


def obtener_valor_pivote(matriz: Matriz, fila: int, columna: int) -> str:
    """Extrae y formatea el valor fraccionario de una celda de pivote."""
    if matriz is None:
        return ""
    return formatear_fraccion_texto(matriz.obtener(fila, columna))


def manejar_inicial(
    indice: int,
    contexto_pasos: ContextoPasos,
    grupos_crudos: list[dict],
) -> tuple[dict, int]:
    """Genera el grupo y metadatos pedagógicos para la matriz inicial."""
    if contexto_pasos.contexto == "inversa":
        explicacion = (
            "Construimos la matriz aumentada [A | I]: A a la izquierda y la "
            "identidad I a la derecha. Meta: aplicar operaciones elementales "
            "de fila hasta obtener [I | A⁻¹]."
        )
        titulo = "Matriz inicial [A | I]"
    elif contexto_pasos.es_gauss:
        explicacion = (
            "Escribimos la matriz aumentada [A | b]: los coeficientes a la izquierda "
            "y el vector b a la derecha. Meta: aplicar operaciones elementales de fila "
            "hasta obtener la forma escalonada."
        )
        titulo = "Matriz inicial [A | b]"
    else:
        explicacion = (
            "Escribimos la matriz aumentada [A | b]: los coeficientes a la izquierda "
            "y el vector b a la derecha. Meta: aplicar operaciones elementales de fila "
            "hasta obtener la forma escalonada reducida."
        )
        titulo = "Matriz inicial [A | b]"

    grupos_crudos.append({"tipo": "inicial", "titulo": titulo, "indices_pasos": [indice]})
    datos_paso = {
        "pivote": None,
        "filas_cambiadas": [],
        "filas_intercambiadas": None,
        "explicacion": explicacion,
    }
    return datos_paso, len(grupos_crudos) - 1


def manejar_intercambio(
    indice: int,
    analisis_paso: dict,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Genera el grupo de columna y metadatos pedagógicos para intercambio de filas."""
    f1 = analisis_paso["fila_origen"] + 1
    f2 = analisis_paso["fila_destino"] + 1
    explicacion = (
        f"Intercambiamos la fila {f1} con la fila {f2} para que el pivote "
        f"sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). "
        f"Intercambiar filas no altera el resultado."
    )
    grupo_columna = {
        "tipo": "columna",
        "titulo": "",
        "indices_pasos": [indice],
        "hay_intercambio": True,
        "fila_pivote": None,
        "columna_pivote": None,
        "valor_pivote": None,
    }
    grupos_crudos.append(grupo_columna)
    estado["columna"] = grupo_columna
    datos_paso = {
        "pivote": None,
        "filas_cambiadas": [f1 - 1, f2 - 1],
        "filas_intercambiadas": (f1 - 1, f2 - 1),
        "explicacion": explicacion,
    }
    return datos_paso, len(grupos_crudos) - 1


def _explicacion_pivote(fila: int, columna: int, valor_pivote: str, contexto_pasos: ContextoPasos) -> str:
    """Genera la explicación pedagógica del paso de selección de pivote."""
    if contexto_pasos.contexto == "inversa":
        return f"Pivote: fila {fila}, columna {columna} (valor {valor_pivote}). Usaremos esta fila para anular el resto de la columna {columna}."
    if contexto_pasos.es_gauss:
        return f"Pivote: fila {fila}, columna {columna} (valor {valor_pivote}). Usaremos esta fila para eliminar las entradas debajo del pivote en la columna {columna}."
    return f"Pivote: fila {fila}, columna {columna} (valor {valor_pivote}). Usaremos esta fila para anular las entradas por encima y por debajo del pivote en la columna {columna}."


def _registrar_grupo_pivote(
    indice: int,
    coordenadas_pivote: tuple[int, int, str],
    estado_grupos: tuple[list[dict], dict],
) -> int:
    """Actualiza o crea el grupo de columna para el pivote actual."""
    grupos_crudos, estado = estado_grupos
    r, c, valor_pivote = coordenadas_pivote
    grupo_columna = estado.get("columna")
    if grupo_columna is not None and grupo_columna.get("fila_pivote") is None:
        grupo_columna["fila_pivote"] = r - 1
        grupo_columna["columna_pivote"] = c - 1
        grupo_columna["valor_pivote"] = valor_pivote
        grupo_columna["indices_pasos"].append(indice)
        return grupos_crudos.index(grupo_columna)

    grupo_columna = {
        "tipo": "columna",
        "titulo": "",
        "indices_pasos": [indice],
        "hay_intercambio": False,
        "fila_pivote": r - 1,
        "columna_pivote": c - 1,
        "valor_pivote": valor_pivote,
    }
    grupos_crudos.append(grupo_columna)
    estado["columna"] = grupo_columna
    return len(grupos_crudos) - 1


def manejar_pivote(
    indice: int,
    analisis_paso: dict,
    matriz: Matriz,
    contexto_pasos: ContextoPasos,
    estado_grupos: tuple[list[dict], dict],
) -> tuple[dict, int]:
    """Genera metadatos para la selección de un nuevo pivote."""
    r = analisis_paso["fila_origen"] + 1
    c = analisis_paso["columna"] + 1
    valor_pivote = obtener_valor_pivote(matriz, r - 1, c - 1)
    explicacion = _explicacion_pivote(r, c, valor_pivote, contexto_pasos)
    indice_grupo = _registrar_grupo_pivote(indice, (r, c, valor_pivote), estado_grupos)
    datos_paso = {
        "pivote": (r - 1, c - 1),
        "filas_cambiadas": [],
        "filas_intercambiadas": None,
        "explicacion": explicacion,
    }
    return datos_paso, indice_grupo


def _explicacion_eliminacion(fila_anulada: int, factor_texto: str, fila_pivote: int, columna_pivote: int, contexto: str) -> str:
    """Genera la explicación para la operación de eliminación entre filas."""
    if contexto == "inversa":
        return (
            f"Hacemos 0 la entrada de la fila {fila_anulada} en la columna {columna_pivote + 1}: "
            f"Fila {fila_anulada} = Fila {fila_anulada} − ({factor_texto}) · Fila {fila_pivote}. La operación afecta la "
            f"fila completa, es decir, los dos bloques a la vez."
        )
    return (
        f"Hacemos 0 la entrada de la fila {fila_anulada} en la columna {columna_pivote + 1}: "
        f"Fila {fila_anulada} = Fila {fila_anulada} − ({factor_texto}) · Fila {fila_pivote}. La operación afecta a toda la fila de [A | b]."
    )


def _asociar_grupo_eliminacion(indice: int, grupos_crudos: list[dict], estado: dict) -> int:
    """Asocia el paso de eliminación al grupo de columna o al grupo residual."""
    grupo_columna = estado.get("columna")
    if grupo_columna is not None:
        grupo_columna["indices_pasos"].append(indice)
        return grupos_crudos.index(grupo_columna)
    return _asociar_grupo_residual(indice, grupos_crudos, estado)


def _asociar_grupo_residual(indice: int, grupos_crudos: list[dict], estado: dict) -> int:
    """Crea el grupo residual o agrega el paso a su grupo existente."""
    if estado.get("otro") is None:
        grupo_residual = {"tipo": "otros", "titulo": "Otras operaciones", "indices_pasos": [indice]}
        grupos_crudos.append(grupo_residual)
        estado["otro"] = grupo_residual
        return len(grupos_crudos) - 1
    estado["otro"]["indices_pasos"].append(indice)
    return grupos_crudos.index(estado["otro"])


def manejar_eliminacion(
    indice: int,
    analisis_paso: dict,
    contexto_pasos: ContextoPasos,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Genera metadatos para operaciones de anulación por filas."""
    fila_anulada = analisis_paso["fila_origen"] + 1
    factor_texto = analisis_paso["texto_valor"]
    fila_pivote = analisis_paso["fila_destino"] + 1
    grupo_columna = estado.get("columna")
    columna_pivote = grupo_columna["columna_pivote"] if (grupo_columna and grupo_columna.get("columna_pivote") is not None) else (fila_pivote - 1)
    explicacion = _explicacion_eliminacion(fila_anulada, factor_texto, fila_pivote, columna_pivote, contexto_pasos.contexto)
    indice_grupo = _asociar_grupo_eliminacion(indice, grupos_crudos, estado)
    datos = {
        "pivote": (fila_pivote - 1, columna_pivote),
        "filas_cambiadas": [fila_anulada - 1],
        "filas_intercambiadas": None,
        "explicacion": explicacion,
    }
    return datos, indice_grupo


def manejar_normalizacion(
    indice: int,
    analisis_paso: dict,
    contexto_pasos: ContextoPasos,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Genera metadatos para operaciones de escalado de pivote a 1."""
    r = analisis_paso["fila_origen"] + 1
    texto_valor = analisis_paso["texto_valor"]
    pivote = (r - 1, r - 1) if (r - 1 < contexto_pasos.columnas_izquierda) else None
    if contexto_pasos.contexto == "inversa":
        explicacion = (
            f"Dividimos la fila {r} entre {texto_valor} para que su pivote valga 1 "
            f"y la diagonal del bloque izquierdo quede igual a la identidad."
        )
    else:
        explicacion = f"Dividimos la fila {r} entre {texto_valor} para que su pivote valga 1."

    grupo_normalizacion = estado.get("normalizacion")
    if grupo_normalizacion is None:
        grupo_normalizacion = {
            "tipo": "normalizacion",
            "titulo": "Normalización: cada pivote pasa a 1",
            "indices_pasos": [indice],
        }
        grupos_crudos.append(grupo_normalizacion)
        estado["normalizacion"] = grupo_normalizacion
        indice_grupo = len(grupos_crudos) - 1
    else:
        grupo_normalizacion["indices_pasos"].append(indice)
        indice_grupo = grupos_crudos.index(grupo_normalizacion)

    datos = {
        "pivote": pivote,
        "filas_cambiadas": [r - 1],
        "filas_intercambiadas": None,
        "explicacion": explicacion,
    }
    return datos, indice_grupo


def manejar_otro(
    indice: int,
    descripcion: str,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Asocia pasos no clasificados al grupo activo o a un grupo de operaciones varias."""
    if estado.get("columna") is not None:
        estado["columna"]["indices_pasos"].append(indice)
        indice_grupo = grupos_crudos.index(estado["columna"])
    elif estado.get("normalizacion") is not None:
        estado["normalizacion"]["indices_pasos"].append(indice)
        indice_grupo = grupos_crudos.index(estado["normalizacion"])
    else:
        indice_grupo = _asociar_grupo_residual(indice, grupos_crudos, estado)

    datos = {
        "pivote": None,
        "filas_cambiadas": [],
        "filas_intercambiadas": None,
        "explicacion": descripcion,
    }
    return datos, indice_grupo


def construir_titulo_columna(grupo: dict) -> str:
    """Genera el título descriptivo para una etapa de pivoteo por columna."""
    c = grupo.get("columna_pivote")
    r = grupo.get("fila_pivote")
    valor = grupo.get("valor_pivote")
    hay_intercambio = grupo.get("hay_intercambio", False)
    if c is not None and r is not None and valor is not None:
        titulo = f"Columna {c + 1} · pivote {valor} en fila {r + 1}"
        if hay_intercambio:
            titulo += " · con intercambio"
        return titulo
    if c is not None:
        return f"Columna {c + 1}"
    return "Columna"
