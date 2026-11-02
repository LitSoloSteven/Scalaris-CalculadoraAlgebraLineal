"""Recorridos rectangulares entre rutas reales, con captura y cálculo posteriores."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from nicegui import ui

from src.frontend.componentes import transferencia
from src.frontend.vistas.sistemas_lineales._transferencia_sistemas import procesar_transferencia_matriz
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_transferencia_matriz import preparar_ruta_lu, leer_matriz, activar_boton, token_desde_url


@pytest.mark.parametrize("herramienta", ["factorizacion_lu", "sistemas", "matrices", "transformaciones"])
@pytest.mark.parametrize("filas,columnas", [(2, 3), (3, 2), (1, 8), (8, 1)])
def test_rutas_rectangulares_conservan_dimensiones_y_texto(monkeypatch, herramienta, filas, columnas):
    """Los paneles reciben filas y columnas sin completar un cuadrado ni calcular."""
    preparar_ruta_lu(monkeypatch)
    limpiar = Mock()
    monkeypatch.setattr(transferencia, "limpiar_url_transferencia", limpiar)
    datos = [[f"{fila * columnas + columna + 1}/1001" for columna in range(columnas)] for fila in range(filas)]
    token = transferencia.guardar_matriz("matrices", datos)

    async def comprobar(vista, cliente):
        """Comprueba los ejes visibles y el aviso con dimensiones rectangulares."""
        assert leer_matriz(vista, herramienta) == datos and vista.ultimo_resultado is None
        etiquetas = [elemento.text for elemento in vista.contenedor_transferencia.descendants()
                     if isinstance(elemento, ui.label)]
        assert any(f"{filas}×{columnas}" in texto for texto in etiquetas)
        limpiar.assert_called_once_with()
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, {"handoff": token}))


def test_matrices_rectangular_carga_solo_a_y_conserva_otras_ediciones(monkeypatch):
    """La recepción rectangular preserva B, C, la expresión y los ceros de A."""
    async def comprobar(vista, cliente):
        """Recibe A mediante el helper común sobre una colección ya editada."""
        panel = vista.panel_captura_matrices
        panel.cargar_datos({"A": [["1"]], "B": [["2", "3"]], "C": [["4"]]})
        panel.matrices["B"]["entradas"][0][1].set_value("-5/7")
        vista.entrada_expresion.set_value("A*B")
        datos = [["1/1001", "0", "-2/3"], ["4", "5.00", "6"]]
        token = transferencia.guardar_matriz("factorizacion_lu", datos)
        transferencia.recibir_matriz(token, "matrices", panel.cargar_matriz_a, vista.contenedor_transferencia)
        capturas = panel.obtener_datos_crudos()
        assert capturas["A"]["datos"] == datos
        assert capturas["B"]["datos"] == [["2", "-5/7"]] and capturas["C"]["datos"] == [["4"]]
        assert vista.entrada_expresion.value == "A*B"
    asyncio.run(construir_pagina(monkeypatch, "matrices", comprobar))


def test_sistemas_rectangular_deja_un_termino_vacio_por_fila(monkeypatch):
    """Salir de Ax=0 conserva la forma 3×2 y deja exactamente tres entradas para b."""
    async def comprobar(vista, cliente):
        """Recibe el rectángulo y resuelve un sistema compatible con la nueva captura."""
        vista.casilla_homogeneo.set_value(True)
        datos = [["1", "0"], ["0", "1"], ["1", "1"]]
        procesar_transferencia_matriz(vista, transferencia.guardar_matriz("matrices", datos))
        assert leer_matriz(vista, "sistemas") == datos
        assert not vista.casilla_homogeneo.value and not vista.cuadricula.modo_homogeneo
        assert [entrada.value for entrada in vista.cuadricula.entradas_independientes] == ["", "", ""]
        for entrada, valor in zip(vista.cuadricula.entradas_independientes, ["2", "3", "5"]):
            entrada.set_value(valor)
        await vista.resolver_sistema(ui.button("Resolver"))
        assert vista.ultimo_resultado["estado"] == "SOLUCION_UNICA"
        assert vista.ultimo_resultado["solucion"] == ["2", "3"]
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))


@pytest.mark.parametrize("destino", ["sistemas", "matrices", "transformaciones"])
def test_lu_rectangular_abre_otro_modulo_y_permite_calcular(monkeypatch, destino):
    """Un resultado LU 2×3 ofrece los destinos correctos y conserva su matriz al abrirlos."""
    preparar_ruta_lu(monkeypatch)
    navegaciones = []
    monkeypatch.setattr(ui.navigate, "to", navegaciones.append)
    datos = [["1", "0", "1/3"], ["0", "1", "-2/3"]]

    async def enviar(vista, cliente):
        """Calcula LU, verifica exclusiones y activa un destino rectangular real."""
        vista.panel_matriz.cargar_matriz(datos)
        await vista.calcular(SimpleNamespace(sender=ui.button("Calcular")))
        botones = {elemento._props["data-destino-matriz"]: elemento
                   for elemento in vista.contenedor_resultados.descendants() if "data-destino-matriz" in elemento._props}
        assert set(botones) == {"sistemas", "matrices", "transformaciones"}
        activar_boton(botones[destino])

    async def recibir(vista, cliente):
        """Comprueba captura y cálculo de la matriz transferida cuando aplica."""
        assert leer_matriz(vista, destino) == datos
        if destino == "matrices":
            vista.entrada_expresion.set_value("A")
            await vista.evaluar_expresion(ui.button("Evaluar"))
            assert vista.ultimo_resultado["matriz_resultado"]["datos"] == datos
        elif destino == "transformaciones":
            assert len(vista.entradas_variables) == 3
            await vista._analizar(ui.button("Analizar"))
            assert vista.ultimo_resultado["estado"] == "EXITO" and vista.ultimo_resultado["rango"] == 2
    asyncio.run(construir_pagina(monkeypatch, "factorizacion_lu", enviar))
    asyncio.run(construir_pagina(monkeypatch, destino, recibir, {"handoff": token_desde_url(navegaciones[0])}))
