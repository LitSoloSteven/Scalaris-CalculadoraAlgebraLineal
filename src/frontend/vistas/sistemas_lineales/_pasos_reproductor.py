"""Construcción de pasos y grupos didácticos para el reproductor en Sistemas Lineales."""

from __future__ import annotations

from src.frontend.controladores.sistemas_lineales.presentacion_solucion import preparar_matriz_paso
from src.frontend.componentes.reproductor_pasos.cuerpos import CuerpoLatex
from src.frontend.componentes.reproductor_pasos.textos import limpiar_latex_plano
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.ayudas import formatear_paso_mathjax


def _crear_paso_eliminacion(
    paso: dict,
    metadatos_pasos: list[dict],
    total_pasos: int,
    variables: list[str],
    numero_variables: int,
) -> PasoReproductor:
    """Crea una instancia de PasoReproductor para un paso de eliminación gaussiana."""
    indice = paso["indice"]
    datos_matriz = paso.get("matriz", {})
    matriz = preparar_matriz_paso(datos_matriz)
    pivote = tuple(paso["pivote"]) if paso.get("pivote") is not None else None
    cuerpo = html_tabla_aumentada(matriz, numero_variables, opciones={'filas_cambiadas': tuple(paso.get("filas_cambiadas") or ()), 'pivote': pivote, 'filas_intercambio': tuple(paso["filas_intercambiadas"]) if paso.get("filas_intercambiadas") is not None else (), 'bloque_resultado': False, 'etiquetas_izquierda': variables, 'etiquetas_derecha': ["b"]})
    meta = metadatos_pasos[indice] if indice < len(metadatos_pasos) else {
        "indice": indice + 1, "total": total_pasos, "tipo": paso.get("tipo", "otro"),
        "operacion": paso.get("descripcion", ""), "pivote": pivote,
        "filas_antes": {}, "filas_despues": {}, "columnas": None,
    }
    return PasoReproductor(
        indice=indice, tipo=paso.get("tipo", "otro"),
        descripcion=paso.get("descripcion", ""),
        explicacion=paso.get("explicacion", ""),
        indice_grupo=paso.get("indice_grupo", 0),
        cuerpo=cuerpo, meta_explicar=meta,
    )


def _construir_pasos_eliminacion(vista_pasos: list[dict], vista_grupos: list[dict], metadatos_pasos: list[dict], total_pasos: int, datos_variables: tuple) -> tuple[list[PasoReproductor], list[GrupoReproductor]]:
    """Genera pasos y grupos para las etapas de eliminación (matrices aumentadas)."""
    variables, numero_variables = datos_variables
    pasos = [
        _crear_paso_eliminacion(paso, metadatos_pasos, total_pasos, variables, numero_variables)
        for paso in vista_pasos
    ]
    grupos = [
        GrupoReproductor(
            titulo=grupo.get("titulo", ""), resumen=grupo.get("resumen", ""),
            tipo=grupo.get("tipo", "columna"), indices_pasos=tuple(grupo.get("indices_pasos", ())),
        )
        for grupo in vista_grupos
    ]
    return pasos, grupos


def _construir_pasos_latex(lineas: list[str], total: int, inicio: tuple[int, int], presentacion: dict) -> tuple[list[PasoReproductor], GrupoReproductor]:
    """Construye una secuencia didactica LaTeX y su grupo conservando texto y orden."""
    inicio_paso, inicio_grupo = inicio
    pasos = []
    indices = []
    for indice, linea in enumerate(lineas):
        posicion = inicio_paso + indice
        indices.append(posicion)
        texto_operacion = limpiar_latex_plano(linea)
        metadatos = {
            "indice": posicion + 1, "total": total, "tipo": presentacion["tipo"],
            "operacion": texto_operacion, "filas_antes": {}, "filas_despues": {}, "columnas": None,
        }
        pasos.append(PasoReproductor(
            indice=posicion, tipo=presentacion["tipo"], descripcion=texto_operacion,
            explicacion=presentacion["explicacion"], indice_grupo=inicio_grupo,
            cuerpo=CuerpoLatex(formatear_paso_mathjax(linea)), meta_explicar=metadatos,
        ))
    resumen = "1 operación" if len(indices) == 1 else f"{len(indices)} operaciones"
    grupo = GrupoReproductor(titulo=presentacion["titulo"], resumen=resumen, tipo=presentacion["tipo"], indices_pasos=tuple(indices))
    return pasos, grupo


def _construir_pasos_sustitucion(pasos_sustitucion: list[str], total_pasos: int, es_gauss_jordan: bool, inicio_paso: int, inicio_grupo: int) -> tuple[list[PasoReproductor], GrupoReproductor]:
    """Prepara la lectura o sustitucion y delega la construccion del grupo."""
    presentacion = {
        "tipo": "sustitucion",
        "titulo": "Solución final" if es_gauss_jordan else "Sustitución hacia atrás",
        "explicacion": (
            "Lectura del valor de la variable a partir de la forma escalonada reducida."
            if es_gauss_jordan
            else "Despejamos y sustituimos hacia atrás los valores conocidos para hallar la incógnita."
        ),
    }
    return _construir_pasos_latex(pasos_sustitucion, total_pasos, (inicio_paso, inicio_grupo), presentacion)


def _construir_pasos_verificacion(pasos_verificacion: list[str], total_pasos: int, inicio_paso: int, inicio_grupo: int) -> tuple[list[PasoReproductor], GrupoReproductor]:
    """Prepara la comprobacion y delega la construccion del grupo."""
    presentacion = {
        "tipo": "verificacion", "titulo": "Comprobación Ax = b",
        "explicacion": "Sustituimos la solución en la ecuación original para verificar que se cumple la igualdad.",
    }
    return _construir_pasos_latex(pasos_verificacion, total_pasos, (inicio_paso, inicio_grupo), presentacion)


def construir_pasos_reproductor(
    respuesta: dict,
    metodo: str | None = None,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos del reproductor a partir de la respuesta del solver."""
    vista_pasos = respuesta.get("vista_pasos", [])
    if not vista_pasos:
        return (), ()

    pasos_sustitucion = respuesta.get("pasos_sustitucion_regresiva") or []
    pasos_verificacion = respuesta.get("pasos_verificacion_latex") or []
    variables = respuesta.get("variables")
    numero_variables = respuesta.get("numero_variables", len(variables) if variables else 0)
    if not variables and numero_variables > 0:
        variables = [f"x{i+1}" for i in range(numero_variables)]

    total_pasos = len(vista_pasos) + len(pasos_sustitucion) + len(pasos_verificacion)
    pasos, grupos = _construir_pasos_eliminacion(vista_pasos, respuesta.get("grupos", []), respuesta.get("metadatos_pasos", []), total_pasos, (variables, numero_variables))

    es_gauss_jordan = metodo == "gauss-jordan"
    if pasos_sustitucion:
        pasos_sustitucion_construidos, grupo_sustitucion = _construir_pasos_sustitucion(
            pasos_sustitucion, total_pasos, es_gauss_jordan, len(pasos), len(grupos)
        )
        pasos.extend(pasos_sustitucion_construidos)
        grupos.append(grupo_sustitucion)

    if pasos_verificacion:
        pasos_verificacion_construidos, grupo_verificacion = _construir_pasos_verificacion(
            pasos_verificacion, total_pasos, len(pasos), len(grupos)
        )
        pasos.extend(pasos_verificacion_construidos)
        grupos.append(grupo_verificacion)

    return tuple(pasos), tuple(grupos)
