"""Adaptacion y renderizado de trazas de determinante sin operaciones matematicas."""
from nicegui import ui

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.componentes.glosa_foco import crear_accion_explicacion


def adaptar_traza(resultado: dict) -> tuple[tuple, tuple]:
    """Convierte pasos del backend a modelos del reproductor sin recalcular valores."""
    pasos = tuple(PasoReproductor(
        indice=indice, tipo=paso["tipo"], descripcion=paso["descripcion"],
        explicacion=paso["explicacion"], cuerpo=paso,
        etiqueta_tipo="Menor" if paso["tipo"] == "menor" else None,
        meta_explicar={"tipo": paso["tipo"], "operacion": paso["descripcion"],
                       "detalle": {"formula": paso.get("detalle_latex", ""),
                                   "explicacion": paso["explicacion"]}},
    ) for indice, paso in enumerate(resultado["traza"]))
    grupos = (GrupoReproductor("Calculo del determinante", f"{len(pasos)} pasos", "operacion",
                              tuple(range(len(pasos)))),)
    return pasos, grupos


def _opciones_resaltado(datos: dict) -> dict:
    opciones = {}
    if "fila_elegida" in datos:
        opciones["filas_cambiadas"] = [datos["fila_elegida"] - 1]
    if "elemento_actual" in datos:
        opciones["pivote"] = tuple(indice - 1 for indice in datos["elemento_actual"])
    operacion = datos.get("operacion", {})
    if datos["tipo"] == "pivote":
        opciones["pivote"] = (operacion["fila"], operacion["columna"])
    elif datos["tipo"] == "intercambio":
        opciones["filas_intercambio"] = (operacion["fila"], operacion["seleccionada"])
    elif datos["tipo"] == "eliminacion":
        opciones["filas_cambiadas"] = [operacion["fila"]]
    return opciones


def renderizar_cuerpo_determinante(paso: PasoReproductor, contenedor) -> None:
    """Presenta matriz, menor, correspondencia de indices y formulas del dominio."""
    datos = paso.cuerpo
    with contenedor:
        matriz = datos.get("matriz")
        if matriz is not None:
            ui.html(html_tabla_aumentada(matriz, matriz.columnas, _opciones_resaltado(datos)))
        menor = datos.get("menor")
        if menor:
            _mostrar_menor(menor)
        if datos.get("detalle_latex"):
            renderizar_latex(datos["detalle_latex"])


def _mostrar_menor(menor: dict) -> None:
    ui.label(f"Elimina F{menor['fila']} y C{menor['columna']}. El elemento activo aparece enmarcado.")
    filas = ", ".join(f"F{indice}" for indice in menor["filas_originales"])
    columnas = ", ".join(f"C{indice}" for indice in menor["columnas_originales"])
    ui.label(f"Filas del menor, en orden: {filas}. Columnas originales: {columnas}.").classes("texto-secundario")
    matriz = menor["matriz_menor"]
    opciones = {"etiquetas_izquierda": [f"C{indice}" for indice in menor["columnas_originales"]]}
    ui.html(html_tabla_aumentada(matriz, matriz.columnas, opciones))


def montar_reproductor(resultado: dict, panel_ia) -> ReproductorPasos:
    """Monta el reproductor existente con accion contextual de Glosa y devuelve su control."""
    pasos, grupos = adaptar_traza(resultado)
    reproductor = ReproductorPasos(
        pasos, grupos, renderizar_cuerpo_determinante, "determinante",
        opciones={"titulo": "Pasos del determinante", "al_explicar": crear_accion_explicacion(panel_ia, pasos),
                  "esta_ocupado": lambda: bool(getattr(panel_ia, "_esta_enviando", False))},
    )
    reproductor.construir()
    return reproductor
