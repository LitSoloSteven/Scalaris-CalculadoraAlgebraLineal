"""Presentación de coordenadas exactas de una transformación aplicada."""
from nicegui import ui
from src.frontend.componentes.reproductor_pasos import ReproductorPasos

from src.frontend import textos_transformaciones as textos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.controladores.operaciones_matrices.vista_previa_modelos import preparar_vista_previa_aplicacion
from ._estados_modelos import mostrar_estado
from .grafica_aplicacion_transformacion import renderizar_grafica_aplicacion
from .procedimiento_aplicacion_transformacion import montar_procedimiento_aplicacion


def renderizar_resultado_aplicacion(contenedor, resultado: dict, captura: dict) -> ReproductorPasos | None:
    """Muestra original y transformado; informa errores sin certificar una discrepancia."""
    if resultado.get("estado") == "ERROR":
        mostrar_estado(contenedor, resultado["mensaje"], "ERROR")
        return
    if resultado.get("verificacion") is not True:
        mostrar_estado(contenedor, textos.ERROR_COMPROBACION, "ERROR")
        return
    with contenedor, ui.column().classes("w-full min-w-0 gap-4") as region:
        region.props.update({"data-procedimiento-aplicacion": "", "data-componente-activa": "-1"})
        ui.label(textos.RESULTADO_TITULO).classes("font-bold texto-principal text-xl").props('role="status"')
        ui.label(f"T: R^{resultado['dimension_dominio']} → R^{resultado['dimension_codominio']}").classes("texto-secundario")
        renderizar_latex(preparar_vista_previa_aplicacion(captura))
        titulos = textos.TITULOS_COORDENADAS[captura["tipo_objeto"]]
        with ui.row().classes("w-full gap-4 items-start flex-wrap"):
            _mostrar_coordenadas(titulos[0], resultado["vector_original"]["exacta"])
            _mostrar_coordenadas(titulos[1], resultado["vector_transformado"]["exacta"], resultado=True)
        ui.label(textos.COORDENADAS_EXACTAS).classes("texto-secundario text-sm")
        renderizar_grafica_aplicacion(resultado, captura["tipo_objeto"])
        return montar_procedimiento_aplicacion(resultado, captura, region)


def _mostrar_coordenadas(titulo: str, componentes: list[str], *, resultado: bool = False) -> None:
    with ui.column().classes("flex-1 min-w-0 gap-2"):
        ui.label(titulo).classes("font-bold texto-principal")
        for indice, valor in enumerate(componentes):
            etiqueta = ui.label(f"{indice + 1}: {valor}").classes("determinante-valor texto-principal w-full")
            if resultado:
                etiqueta.props["data-componente-resultado"] = str(indice)
