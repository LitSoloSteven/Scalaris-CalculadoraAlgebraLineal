"""Contexto del ejercicio vectorial y señales para las sugerencias del asistente."""
from src.ai.contexto import ContextoIA, EstadoContexto, describir_matriz, sanear_cadena_usuario
from src.ai.huellas import esta_desactualizado
from src.frontend.suggestions import Signals, first_invalid_cell


def entrada_actual(vista):
    """Copia el estado efectivo de la captura para identificar resultados obsoletos."""
    return {"operacion": vista.operacion_activa, "vectores": vista._capturar(),
            "escalar": vista.valor_escalar, "suma_resta": vista.operacion_suma_resta,
            "estricto": vista.orientacion_estricta}


def _describir_vectores(vectores):
    datos = {}
    for nombre, vector in vectores.items():
        celdas = [[sanear_cadena_usuario(str(valor), 32)] for valor in vector["data"]]
        datos[nombre] = describir_matriz(celdas)
        datos[nombre]["orientacion"] = {"column": "columna", "row": "fila"}[vector["orientation"]]
    return datos


def _describir_resultado(resultado):
    datos = {"estado": resultado.get("status", "ERROR"), "mensaje": resultado.get("message", "")}
    if resultado.get("matriz_resultado"):
        datos["vector_resultado"] = resultado["matriz_resultado"]
    if resultado.get("es_combinacion_lineal") is not None:
        datos["es_combinacion_lineal"] = resultado["es_combinacion_lineal"]
    return datos


def obtener_contexto(vista):
    """Describe la captura sin sustituir entradas inválidas por números ni exponer resultados obsoletos."""
    vectores = vista._capturar()
    datos = _describir_vectores(vectores)
    datos["opciones"] = _opciones_contexto(vista)
    contexto = ContextoIA("operaciones_vectores", "Vectores", f"Operación: {vista.operacion_activa}",
                         datos, estado=EstadoContexto(vacio=not vectores))
    contexto.desactualizado = esta_desactualizado(entrada_actual(vista), vista._huella_resultado)
    if vista.resultado_actual and not contexto.desactualizado:
        contexto.resultado = _describir_resultado(vista.resultado_actual)
    return contexto


def _opciones_contexto(vista):
    if vista.operacion_activa == "escalar":
        return {"escalar": sanear_cadena_usuario(vista.valor_escalar, 32)}
    if vista.operacion_activa == "suma_resta":
        return {"operacion": vista.operacion_suma_resta, "estricto": vista.orientacion_estricta}
    return {"objetivo": vista.panel_combinacion.first_vector_fixed_label}


def _celdas_capturadas(panel):
    return [(f"{nombre}[{indice + 1}]", vector["cache"].get(indice, ""), (posicion, indice))
            for posicion, (nombre, vector) in enumerate(panel.vectors.items())
            for indice in range(panel.dim)]


def obtener_senales(vista):
    """Localiza la primera entrada inválida y clasifica el resultado vigente."""
    orientaciones = {vector["orientation"] for vector in vista.panel_vectorial.vectors.values()}
    banderas = set()
    if {"row", "column"}.issubset(orientaciones):
        banderas.add("orient_mix")
    if vista.operacion_activa == "escalar" and vista.valor_escalar.strip().startswith("-"):
        banderas.add("neg_scalar")
    estado = "none"
    if vista.resultado_actual and not obtener_contexto(vista).desactualizado:
        estado = {"UNIQUE": "unique", "INFINITE": "infinite", "NO_SOLUTION": "no_solution"}.get(
            vista.resultado_actual.get("status"), "none")
    return Signals(tool="vectores", state=estado, flags=frozenset(banderas),
                   invalid=first_invalid_cell(_celdas_capturadas(vista.panel_vectorial)))
