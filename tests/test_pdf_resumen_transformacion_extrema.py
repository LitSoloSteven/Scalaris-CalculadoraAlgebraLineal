"""Separación de la fórmula desplazable y las coordenadas exactas exportables."""
import asyncio

from nicegui import ui

from src.frontend.vistas.operaciones_matrices.carga_modelos import cargar_captura_modelo
from tests.comun_construccion_vistas import construir_pagina


def test_resumen_separa_formula_ancha_sin_ocultar_coordenadas(monkeypatch):
    """Un denominador extenso mantiene el resumen numérico independiente del ancho LaTeX."""
    async def comprobar(vista, cliente):
        """Calcula y examina las regiones reales que consume el exportador compartido."""
        fraccion = "1/" + "9" * 200
        cargar_captura_modelo(vista, {"matriz_transformacion": [["1", "0"], ["0", "1"]],
                                    "vector_original": [fraccion, "2"]})
        await vista._analizar(vista.boton_calcular)
        resumen = next(elemento for elemento in vista.contenedor_resultados.descendants()
                       if elemento._props.get("data-pdf-captura") == "transformaciones-resumen")
        excluidos = [elemento for elemento in resumen.descendants() if "data-pdf-excluir" in elemento._props]
        assert len(excluidos) == 1
        assert any(isinstance(elemento, ui.html) for elemento in excluidos[0].descendants())
        coordenadas = [elemento for elemento in resumen.descendants() if isinstance(elemento, ui.label)]
        assert sum(elemento.text == "1: " + fraccion for elemento in coordenadas) == 2
        assert set(coordenadas).isdisjoint(excluidos[0].descendants())
        assert all(paso.cuerpo.latex for paso in vista.reproductor_pasos.pasos)
        assert vista.actualizar_exportacion_pdf.__self__.enlace.entrada_documental()["vector_original"][0] == fraccion
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
