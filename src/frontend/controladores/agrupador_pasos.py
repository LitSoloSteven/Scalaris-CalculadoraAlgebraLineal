"""Agrupación y clasificación didáctica de pasos de eliminación por filas."""

from src.frontend.controladores.clasificador_pasos import clasificar_paso
from src.frontend.controladores.manejadores_pasos import (
    ContextoPasos,
    construir_titulo_columna,
    manejar_eliminacion,
    manejar_inicial,
    manejar_intercambio,
    manejar_normalizacion,
    manejar_otro,
    manejar_pivote,
)


def _formatear_grupos_finales(grupos_crudos: list[dict]) -> list[dict]:
    """Convierte los grupos acumulados al contrato estructurado para la interfaz."""
    grupos = []
    for grupo in grupos_crudos:
        cantidad = len(grupo["indices_pasos"])
        resumen = "1 operación" if cantidad == 1 else f"{cantidad} operaciones"
        tipo_grupo = grupo.get("tipo", "otro")
        titulo = construir_titulo_columna(grupo) if tipo_grupo == "columna" else grupo.get("titulo", "")
        grupos.append({
            "titulo": titulo,
            "resumen": resumen,
            "tipo": tipo_grupo,
            "indices_pasos": grupo["indices_pasos"],
        })
    return grupos


def _despachar_paso(
    indice: int,
    paso_fuente: dict,
    analisis_paso: dict,
    contexto_pasos: ContextoPasos,
    estado_grupos: tuple[list[dict], dict],
) -> tuple[dict, int]:
    """Despacha el paso según su tipo y actualiza los grupos de columna y normalización."""
    grupos_crudos, estado = estado_grupos
    tipo_paso = analisis_paso["tipo"]
    desc = paso_fuente.get("descripcion", "")
    matriz = paso_fuente.get("matriz")

    if tipo_paso == "inicial":
        estado["columna"], estado["normalizacion"], estado["otro"] = None, None, None
        return manejar_inicial(indice, contexto_pasos, grupos_crudos)
    if tipo_paso == "intercambio":
        estado["normalizacion"], estado["otro"] = None, None
        return manejar_intercambio(indice, analisis_paso, grupos_crudos, estado)
    if tipo_paso == "pivote":
        estado["normalizacion"], estado["otro"] = None, None
        return manejar_pivote(indice, analisis_paso, matriz, contexto_pasos, estado_grupos)
    if tipo_paso == "eliminacion":
        estado["normalizacion"] = None
        return manejar_eliminacion(indice, analisis_paso, contexto_pasos, grupos_crudos, estado)
    if tipo_paso == "normalizacion":
        estado["columna"], estado["otro"] = None, None
        return manejar_normalizacion(indice, analisis_paso, contexto_pasos, grupos_crudos, estado)
    return manejar_otro(indice, desc, grupos_crudos, estado)


def _ensamblar_paso(
    indice: int,
    paso_fuente: dict,
    datos_paso: tuple[dict, int],
    contexto_pasos: ContextoPasos,
    es_ultimo: bool,
) -> dict:
    """Construye el diccionario del paso individual con su explicación."""
    datos, indice_grupo = datos_paso
    desc = paso_fuente.get("descripcion", "")
    matriz = paso_fuente.get("matriz")
    explicacion = datos["explicacion"]
    if contexto_pasos.contexto == "inversa" and es_ultimo and contexto_pasos.estado_resp == "EXITO":
        explicacion = (
            "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque "
            "derecho es A⁻¹. " + explicacion
        )
    return {
        "indice": indice,
        "descripcion": desc,
        "tipo": paso_fuente.get("tipo", datos.get("tipo", "")),
        "indice_grupo": indice_grupo,
        "pivote": datos["pivote"],
        "filas_cambiadas": datos["filas_cambiadas"],
        "filas_intercambiadas": datos["filas_intercambiadas"],
        "explicacion": explicacion,
        "matriz": matriz,
    }


def agrupar_pasos_eliminacion(
    pasos_crudos: list[dict],
    columnas_izquierda: int,
    estado: str | None,
    *,
    contexto: str,
    metodo: str | None = None,
) -> tuple[list[dict], list[dict], dict]:
    """Clasifica los pasos de eliminación, asigna explicaciones y los agrupa por fases."""
    pasos: list[dict] = []
    grupos_crudos: list[dict] = []
    estado_grupos_actual: dict = {"columna": None, "normalizacion": None, "otro": None}
    estado_grupos = (grupos_crudos, estado_grupos_actual)
    contexto_pasos = ContextoPasos(
        contexto=contexto,
        columnas_izquierda=columnas_izquierda,
        es_gauss=(str(metodo).lower() == "gauss"),
        estado_resp=estado,
    )
    total = len(pasos_crudos)

    for indice, paso_fuente in enumerate(pasos_crudos):
        analisis_paso = clasificar_paso(paso_fuente.get("descripcion", ""))
        datos_paso = _despachar_paso(indice, paso_fuente, analisis_paso, contexto_pasos, estado_grupos)
        paso_con_tipo = {**paso_fuente, "tipo": analisis_paso["tipo"]}
        pasos.append(_ensamblar_paso(indice, paso_con_tipo, datos_paso, contexto_pasos, indice == total - 1))

    grupos = _formatear_grupos_finales(grupos_crudos)
    estadisticas = {
        "total": len(pasos),
        "pivotes": sum(1 for paso in pasos if paso["tipo"] == "pivote"),
        "intercambios": sum(1 for paso in pasos if paso["tipo"] == "intercambio"),
        "eliminaciones": sum(1 for paso in pasos if paso["tipo"] == "eliminacion"),
        "normalizaciones": sum(1 for paso in pasos if paso["tipo"] == "normalizacion"),
    }
    return pasos, grupos, estadisticas
