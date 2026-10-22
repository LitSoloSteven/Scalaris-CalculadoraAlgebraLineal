"""Presentacion comun de analisis algebraicos calculados integramente en backend."""
from nicegui import ui

from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.cuerpos import CuerpoLatex, renderizar_latex
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor, GrupoReproductor


def adaptar_analisis(resultado: dict, inicio: tuple[int, int] = (0, 0)) -> tuple[tuple, tuple]:
    """Adapta textos y formulas del dominio al reproductor, sin calculos matematicos."""
    posicion, grupo = inicio
    pasos = tuple(PasoReproductor(
        indice=posicion + indice, tipo=paso["tipo"], descripcion=paso["descripcion"],
        explicacion=paso["explicacion"], indice_grupo=grupo,
        cuerpo=CuerpoLatex(paso["detalle_latex"]),
        meta_explicar={"tipo": paso["tipo"], "operacion": paso["descripcion"],
                       "detalle": {"formula": paso["detalle_latex"]}},
    ) for indice, paso in enumerate(resultado["traza"]))
    grupos = (GrupoReproductor("Analisis y comprobacion", f"{len(pasos)} pasos", "operacion",
                              tuple(paso.indice for paso in pasos)),)
    return pasos, grupos


def mostrar_resumen_analisis(resultado: dict) -> None:
    """Muestra mensaje, rango y expresiones finales preparados por el dominio."""
    error = resultado.get("estado") == "ERROR"
    ui.label(resultado.get("mensaje", "")).classes("distintivo-error" if error else "texto-principal").props(
        'role="alert"' if error else 'role="status" aria-live="polite"')
    if error:
        return
    if "rango" in resultado:
        ui.label(f"Rango: {resultado['rango']}").classes("texto-secundario")
    if "nulidad" in resultado:
        ui.label(f"Nulidad: {resultado['nulidad']}").classes("texto-secundario")
    if resultado.get("etiquetas"):
        nombres = ", ".join(f"v_{indice+1}: {nombre}" for indice, nombre in enumerate(resultado["etiquetas"]))
        ui.label(f"Orden de las columnas en las formulas: {nombres}").classes("texto-secundario")
    _mostrar_formulas_resultado(resultado)


def _mostrar_formulas_resultado(resultado: dict) -> None:
    formulas = list(resultado.get("formulas_resultado", []))
    if resultado.get("formula_familia"):
        formulas.append(resultado["formula_familia"])
    formulas.extend(relacion["formula"] for relacion in resultado.get("relaciones", []))
    for formula in formulas:
        renderizar_latex(formula)


def montar_analisis(resultado: dict, panel_ia, identificador: str) -> ReproductorPasos | None:
    """Monta un reproductor con Glosa para una respuesta exitosa; devuelve None ante error."""
    mostrar_resumen_analisis(resultado)
    if resultado.get("estado") == "ERROR":
        return None
    pasos, grupos = adaptar_analisis(resultado)
    reproductor = ReproductorPasos(pasos, grupos, _renderizar_cuerpo, identificador,
                                  opciones={"al_explicar": crear_accion_explicacion(panel_ia, pasos)})
    reproductor.construir()
    return reproductor


def _renderizar_cuerpo(paso: PasoReproductor, contenedor) -> None:
    with contenedor:
        paso.cuerpo()


def anexar_analisis(pasos: list, grupos: list, resultado: dict) -> tuple[tuple, tuple]:
    """Anade la interpretacion homogenea a la secuencia existente de sistemas."""
    if resultado.get("homogeneo"):
        adicionales, grupo = adaptar_analisis(resultado["homogeneo"], (len(pasos), len(grupos)))
        pasos.extend(adicionales)
        grupos.extend(grupo)
    return tuple(pasos), tuple(grupos)
