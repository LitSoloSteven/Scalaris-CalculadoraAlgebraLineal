"""Integracion de comprobaciones calculadas en las capturas y vistas reales."""
import asyncio

import pytest
from nicegui import ui

from tests.comun_construccion_vistas import construir_pagina
from tests.comun_calculos_vistas import calcular_minimo


@pytest.mark.parametrize("herramienta", ["inversa", "leontief", "transformaciones"])
def test_resultado_visible_incluye_desarrollo_exactamente_desde_backend(monkeypatch, herramienta):
    """El calculo real monta identidad, sustitucion y explicacion en una expansion accesible."""
    async def comprobar(vista, cliente):
        """Ejecuta el calculo real y recorre los elementos matematicos montados."""
        await calcular_minimo(herramienta, vista)
        elementos = list(cliente.elements.values())
        expansiones = [elemento for elemento in elementos if isinstance(elemento, ui.expansion)]
        assert any(elemento.text == "Ver desarrollo de la comprobacion" for elemento in expansiones)
        etiquetas = [elemento.text for elemento in elementos if isinstance(elemento, ui.label)]
        assert any("Propiedad por comprobar" in etiqueta for etiqueta in etiquetas)
        contenido = "\n".join(elemento.content for elemento in elementos if isinstance(elemento, ui.html))
        assert "C_{1,1}" in contenido
        assert "\\begin{bmatrix}" in contenido
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_sistema_parametrico_incluye_comprobacion_en_reproductor(monkeypatch):
    """Se puede recorrer la sustitucion simbolica de ambas ecuaciones desde Sistemas."""
    async def comprobar(vista, cliente):
        """Comprueba la familia completa usando el reproductor de la vista."""
        vista.cuadricula.cargar_datos([["1/2", "1/3"], ["1", "2/3"]], ["1", "2"])
        await vista.resolver_sistema(ui.button("Resolver prueba"))
        respuesta = vista.ultimo_resultado
        assert respuesta["estado"] == "SOLUCIONES_INFINITAS"
        pasos = [paso for paso in vista.reproductor_pasos.pasos if paso.tipo == "verificacion"]
        assert len(pasos) == 2
        for paso in pasos:
            vista.reproductor_pasos.ir_a(paso.indice)
            assert "todos los parametros" in str(paso.cuerpo)
        assert respuesta["pasos_verificacion_latex"]
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))


@pytest.mark.parametrize("datos,objetivo", [({"u": ["1", "2"], "v": ["2", "4"]}, ["3", "6"]),
                                         ({"u": ["1", "0"], "v": ["0", "1"]}, ["1/2", "2/3"])])
def test_combinacion_muestra_comprobacion_por_componentes(monkeypatch, datos, objetivo):
    """Ambos tipos de representacion conectan el desarrollo nuevo al reproductor existente."""
    async def comprobar(vista, cliente):
        """Calcula con los vectores capturados y visita su comprobacion final."""
        vista.pestanas.set_value("combinacion_lineal")
        vista.panel_combinacion.cargar_datos({"b": objetivo, **datos})
        await vista.calcular()
        assert vista.resultado_actual["estado"] in ("UNICA", "INFINITA")
        pasos = vista.reproductor_pasos.pasos
        assert any(paso.tipo == "verificacion" for paso in pasos)
        assert any("Ac=b" in paso.descripcion for paso in pasos)
        assert all(paso.meta_explicar["total"] == len(pasos) for paso in pasos if paso.meta_explicar and "total" in paso.meta_explicar)
        vista.reproductor_pasos.ir_a(len(pasos) - 1)
    asyncio.run(construir_pagina(monkeypatch, "vectores", comprobar))


def test_inversa_singular_presenta_el_producto_diagonal_del_backend(monkeypatch):
    """La tarjeta de singularidad incluye el calculo que justifica la falta de inversa."""
    async def comprobar(vista, cliente):
        """Calcula una matriz dependiente y comprueba la expansion del determinante."""
        vista.panel_matriz_cuadrada.cargar_matriz([["1", "2"], ["2", "4"]])
        await vista.calcular(ui.button("Invertir prueba"))
        assert vista.ultimo_resultado["estado"] == "SINGULAR"
        assert vista.ultimo_resultado["comprobaciones"][0]["traza"]
        elementos = list(cliente.elements.values())
        assert any(isinstance(elemento, ui.expansion) and elemento.text == "Ver desarrollo de la comprobacion" for elemento in elementos)
        contenido = "\n".join(elemento.content for elemento in elementos if isinstance(elemento, ui.html))
        assert r"\det(A)=(-1)^" in contenido
    asyncio.run(construir_pagina(monkeypatch, "inversa", comprobar))
