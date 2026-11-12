"""Construcción y cálculo básico de la página pública de métodos abiertos."""
import asyncio

from nicegui.elements.table import Table
from nicegui.elements.label import Label
import pytest

from src.frontend.controladores.metodos_abiertos import resolver_captura
from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from src.frontend.vistas.metodos_abiertos.figura import crear_figura_metodos_abiertos
from tests.comun_construccion_vistas import construir_pagina


def test_pagina_muestra_vista_previa_y_tabla_paginada(monkeypatch):
    """La página construye la gráfica y expone la traza Newton con 15 filas por página."""
    async def comprobar(vista, cliente):
        """Comprueba la configuración inicial y ejecuta un cálculo real en la vista."""
        assert vista.tolerancia.value == "1e-6"
        assert vista.limite.value == "100"
        assert not vista.x1.visible
        await vista.previa.actualizar()
        assert vista.previa.respuesta["estado"] == "EXITO"
        assert len(vista.grafica.figure.data) == 1
        vista.calcular()
        tablas = [elemento for elemento in cliente.elements.values() if isinstance(elemento, Table)]
        assert len(tablas) == 1
        assert tablas[0].pagination["rowsPerPage"] == 15
        assert vista.resultados.descendants()
        vista.reproductor.ir_a(1)
        assert any(traza.name == "Tangente de Newton" for traza in vista.grafica.figure.data)

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", comprobar))


def test_secante_publica_su_recta_al_recorrer_las_iteraciones(monkeypatch):
    """El reproductor enlaza cada fila secante con sus puntos y su recta de interpolación."""
    async def comprobar(vista, cliente):
        """Selecciona Secante y abre la primera iteración registrada."""
        vista.metodo.set_value("secante")
        vista.x0.set_value("1")
        vista.x1.set_value("2")
        vista.calcular()
        vista.reproductor.ir_a(1)
        nombres = [traza.name for traza in vista.grafica.figure.data]
        assert "Secante" in nombres
        assert "Puntos evaluados · iteración 1" in nombres

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", comprobar))


def test_grafica_muestra_puntos_iniciales_sin_iteraciones():
    """Los puntos capturados siguen visibles si el método termina en la entrada."""
    muestra = preparar_vista_previa({"expresion": "x^2 - 4", "x_min": -10, "x_max": 10})
    resultado = resolver_captura({
        "metodo": "secante", "expresion": "x^2 - 4", "x0": "2", "x1": "3",
    })

    figura = crear_figura_metodos_abiertos(muestra, resultado)
    traza = next(traza for traza in figura.data if traza.name == "Puntos iniciales")

    assert list(traza.text) == ["x₀", "x₁"]
    assert list(traza.x) == [2.0, 3.0]
    assert abs(traza.y[0]) < 1e-12
    assert abs(traza.y[1] - 5.0) < 0.02


def test_punto_inicial_aceptado_por_tolerancia_conserva_su_ordenada():
    """El punto inicial usa la curva cuando su residuo es pequeño, pero no cero."""
    muestra = preparar_vista_previa({"expresion": "x^2 - 2", "x_min": -10, "x_max": 10})
    resultado = resolver_captura({
        "metodo": "secante", "expresion": "x^2 - 2", "x0": "1.4", "x1": "2",
        "tolerancia": "0.5",
    })

    figura = crear_figura_metodos_abiertos(muestra, resultado)
    traza = next(traza for traza in figura.data if traza.name == "Puntos iniciales")

    assert resultado["estado"] == "EXITO"
    assert abs(traza.y[0] + 0.04) < 0.02


def test_vista_previa_antirrebota_y_publica_solo_la_expresion_vigente(monkeypatch):
    """La expresión más reciente reemplaza una solicitud anterior pendiente."""
    async def comprobar(vista, cliente):
        """Programa dos expresiones seguidas y espera únicamente la última tarea."""
        vista.expresion.value = "x^2 - 2"
        vista._editar_expresion(None)
        vista.expresion.value = "x^3 - 4"
        vista._editar_expresion(None)
        await vista.previa.tarea
        assert vista.previa.respuesta["estado"] == "EXITO"
        assert vista.previa.respuesta["entrada"]["expresion"] == "x**3-4"

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", comprobar))


def test_pagina_presenta_fallos_del_metodo_y_reemplaza_el_resultado(monkeypatch):
    """Derivada y denominador nulos quedan visibles sin acumular reproductores."""
    async def comprobar(vista, cliente):
        """Ejecuta ambos diagnósticos y comprueba el último estado renderizado."""
        vista.expresion.value = "x^2 + 1"
        vista.x0.value = "0"
        vista.calcular()
        assert vista.ultimo_resultado["estado"] == "DERIVADA_NULA"
        vista.metodo.set_value("secante")
        vista.expresion.value = "1"
        vista.x0.value = "1"
        vista.x1.value = "2"
        vista.calcular()
        assert vista.ultimo_resultado["estado"] == "DENOMINADOR_NULO"
        textos = [elemento.text for elemento in vista.resultados.descendants()
                  if isinstance(elemento, Label)]
        assert any("denominador" in texto.lower() for texto in textos)
        tarjetas = [elemento for elemento in cliente.elements.values()
                    if elemento._props.get("id") == vista.reproductor.id_tarjeta]
        assert len(tarjetas) == 1

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", comprobar))


@pytest.mark.parametrize("caso", [
    ("newton", "x^2 - 2", "1", "2", "1e-15", "1", "LIMITE_ITERACIONES"),
    ("newton", "ln(x)", "-1", "2", "1e-6", "100", "ERROR"),
    ("secante", "1/x", "1", "2", "1e-15", "100", "DIVERGENCIA"),
])
def test_pagina_muestra_limite_evaluacion_y_divergencia(monkeypatch, caso):
    """Los diagnósticos iterativos y de dominio se publican como texto en la página."""
    metodo, expresion, x0, x1, tolerancia, limite, estado = caso

    async def comprobar(vista, cliente):
        """Crea la captura solicitada y verifica el estado y el mensaje visible."""
        vista.metodo.set_value(metodo)
        vista.expresion.value = expresion
        vista.x0.value, vista.x1.value = x0, x1
        vista.tolerancia.value, vista.limite.value = tolerancia, limite
        vista.calcular()
        assert vista.ultimo_resultado["estado"] == estado
        textos = [elemento.text for elemento in vista.resultados.descendants()
                  if isinstance(elemento, Label)]
        assert textos and any(vista.ultimo_resultado["mensaje"] in texto for texto in textos)

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", comprobar))
