"""Captura real y resultados de la aplicación de transformaciones en NiceGUI."""
import asyncio

import pytest
from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.controladores.operaciones_matrices.capturas_modelos import capturar_transformaciones
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina


def _etiquetas(contenedor):
    return [elemento.text for elemento in contenedor.descendants() if isinstance(elemento, ui.label)]


@pytest.mark.parametrize("indice,esperado", [
    (0, ["3", "2"]), (1, ["6", "6"]), (2, ["3", "-2"]), (3, ["-2", "3"]),
    (4, ["4/3", "3/2"]),
])
def test_ejemplo_aplica_y_muestra_coordenadas_exactas(monkeypatch, indice, esperado):
    """Cada ejemplo carga matriz y vector y muestra el resultado del dominio."""
    async def comprobar(vista, cliente):
        """Recorre la captura y el cálculo reales sin transporte de navegador."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[indice])
        assert vista.modo_transformacion == textos.MODO_APLICACION
        assert vista.boton_calcular.text == textos.APLICAR
        assert vista.boton_calcular._props["aria-label"] == textos.APLICAR
        assert vista.ultimo_resultado is None
        await vista._analizar(vista.boton_calcular)
        assert vista.ultimo_resultado["vector_transformado"]["exacta"] == esperado
        assert vista.ultimo_resultado["verificacion"] is True
        etiquetas = _etiquetas(vista.contenedor_resultados)
        assert "Vector original" in etiquetas and "Vector transformado" in etiquetas
        assert all(f"{indice + 1}: {valor}" in etiquetas for indice, valor in enumerate(esperado))
        assert not vista.historial and vista.reproductor_pasos is None
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_tipo_punto_invalida_y_conserva_convencion_lineal(monkeypatch):
    """Cambiar de vector a punto retira resultados y conserva las mismas coordenadas."""
    async def comprobar(vista, cliente):
        """Verifica la semántica de origen y las etiquetas del resultado de un punto."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        await vista._analizar(vista.boton_calcular)
        vista.selector_tipo_objeto.set_value("punto")
        assert vista.ultimo_resultado is None
        assert capturar_transformaciones(vista)["tipo_objeto"] == "punto"
        await vista._analizar(vista.boton_calcular)
        assert vista.ultimo_resultado["vector_transformado"]["exacta"] == ["3", "2"]
        assert "Punto transformado" in _etiquetas(vista.contenedor_resultados)
        assert any(isinstance(elemento, ui.label) and elemento.text == textos.CONVENCION
                   for elemento in cliente.elements.values())
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_dimension_preserva_datos_y_vector_depende_de_columnas(monkeypatch):
    """Cambiar m conserva el vector; cambiar n conserva sus componentes compatibles."""
    async def comprobar(vista, cliente):
        """Aplica una matriz 3×2 y recorre el crecimiento y reducción de n."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        vista._aplicar_dimension("filas", 3)
        assert [entrada.value for entrada in vista.entradas_vector_original] == ["1/2", "1/3"]
        assert vista.entradas_coeficientes[0][0].value == "2"
        await vista._analizar(vista.boton_calcular)
        assert vista.ultimo_resultado["vector_transformado"]["exacta"] == ["4/3", "3/2", "0"]
        vista._aplicar_dimension("columnas", 3)
        assert [entrada.value for entrada in vista.entradas_vector_original] == ["1/2", "1/3", ""]
        assert vista.ultimo_resultado is None
        vista._aplicar_dimension("columnas", 1)
        assert [entrada.value for entrada in vista.entradas_vector_original] == ["1/2"]
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


@pytest.mark.parametrize("valor", ["texto", "1/0", "9" * 257, "<img src=x onerror=alert(1)>"])
def test_error_de_coordenada_es_texto_y_tiene_ubicacion(monkeypatch, valor):
    """Entradas inválidas no se interpretan como HTML ni producen un falso resultado."""
    async def comprobar(vista, cliente):
        """Comprueba el mensaje y la liberación del botón del cálculo real."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        vista.entradas_vector_original[0].set_value(valor)
        await vista._analizar(vista.boton_calcular)
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert any("v[1,1]" in etiqueta for etiqueta in _etiquetas(vista.contenedor_resultados))
        assert not any(isinstance(elemento, ui.html) for elemento in vista.contenedor_resultados.descendants())
        assert not vista.boton_calcular._props.get("loading", False)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_cuadricula_vectorial_previa_y_aviso_academico(monkeypatch):
    """Las componentes usan atributos de teclado y pegado y la vista previa muestra Av."""
    async def comprobar(vista, cliente):
        """Inspecciona las entradas reales y espera la vista previa con antirrebote."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        for indice, entrada in enumerate(vista.entradas_vector_original):
            assert entrada._props["data-matriz-identificador"] == "v"
            assert entrada._props["data-matriz-fila"] == str(indice)
            assert entrada._props["data-matriz-columna"] == "0"
            assert entrada._props["aria-label"] == f"Componente original {indice + 1}"
        await vista.tarea_vista_previa
        formulas = [elemento.content for elemento in vista.contenedor_vista_previa.descendants()
                    if isinstance(elemento, ui.html)]
        assert any("T(v)=Av=" in formula for formula in formulas)
        assert any(isinstance(elemento, ui.label) and elemento.text == textos.AVISO_ACADEMICO
                   for elemento in cliente.elements.values())
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_limpieza_y_cambio_de_modo_no_recuperan_resultados_ocultos(monkeypatch):
    """Limpiar vacía campos de ambos modos y no conserva acciones de resultados viejos."""
    async def comprobar(vista, cliente):
        """Recorre análisis, aplicación, limpieza y retorno al análisis."""
        await vista._analizar(vista.boton_calcular)
        assert vista.historial and vista.reproductor_pasos is not None
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        assert vista.ultimo_resultado is None and vista.reproductor_pasos is None
        assert vista.obtener_contexto_ia() is None
        assert vista.obtener_senales_ia().estado == "sin_resultado"
        await vista._analizar(vista.boton_calcular)
        assert not any("data-pdf-captura" in elemento._props for elemento in vista.contenedor_resultados.descendants())
        vista.limpiar_todo()
        assert vista.esta_completamente_vacio() and vista.ultimo_resultado is None
        assert all(not entrada.value for entrada in vista.entradas_variables + vista.entradas_vector_original)
        vista.selector_modo.set_value(textos.MODO_ANALISIS)
        assert vista.boton_calcular.text == textos.ANALIZAR
        assert vista.boton_calcular._props["aria-label"] == textos.ANALIZAR
        await vista._analizar(vista.boton_calcular)
        assert "rango" in vista.ultimo_resultado
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
