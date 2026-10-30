"""Contratos de captura, controlador, vista previa e historial de LU."""
import asyncio
import pytest

from src.frontend.componentes.panel_matriz_rectangular import PanelMatrizRectangular
from src.frontend.componentes.portapapeles_matricial import parsear_texto_portapapeles, parsear_portapapeles_rectangular
from src.frontend.controladores.operaciones_matrices.controlador_factorizacion_lu import ControladorFactorizacionLU
from src.frontend.controladores.operaciones_matrices.vista_previa_factorizacion_lu import preparar_presentacion_factorizacion_lu
from src.frontend.controladores.sesion_matricial import describir_registro


@pytest.mark.parametrize("datos,rango", [
    ([["1", "2"], ["3", "4"]], 2),
    ([["1", "2", "3"], ["4", "5", "6"]], 2),
    ([["1", "2"], ["3", "4"], ["5", "6"]], 2),
    ([["1", "2"], ["2", "4"]], 1),
    ([["0", "0"], ["0", "0"]], 0),
    ([["1" if fila == columna else "0" for columna in range(10)] for fila in range(10)], 10),
])
def test_controlador_calcula(datos, rango):
    """Comprueba dimensiones, rango y verificación de distintas capturas."""
    resultado = ControladorFactorizacionLU.procesar_captura({"matriz_a": datos})
    assert resultado["estado"] == "EXITO"
    assert resultado["rango"] == rango
    assert (resultado["filas"], resultado["columnas"]) == (len(datos), len(datos[0]))
    assert resultado["comprobacion"]["coincide"]


def test_controlador_rechaza_celda_invalida_y_exceso():
    """Comprueba que se informan errores de celda y dimensiones excedidas."""
    error = ControladorFactorizacionLU.procesar_captura({"matriz_a": [["1", "mal"]]})
    assert error["estado"] == "ERROR"
    assert "1" in error["mensaje"] and "2" in error["mensaje"]
    assert ControladorFactorizacionLU.procesar_captura({"matriz_a": [["0"] * 11 for _ in range(11)]})["estado"] == "ERROR"


def test_previa_sanea_y_limita():
    """Comprueba la sanitización y el límite de presentación."""
    resultado = preparar_presentacion_factorizacion_lu([["1", "<script>"]], 2)
    formula = resultado["bloques"][0][1]
    assert formula.startswith(r"A = \begin{bmatrix}")
    assert "<script>" not in formula and r"\color{gray}{?}" in formula
    assert preparar_presentacion_factorizacion_lu([["0"] * 10], 10)["estado"] == "limite"


def test_historial_rectangular():
    """Comprueba la descripción rectangular y el rango del historial."""
    descripcion = describir_registro({"estado": "FACTORIZACION_LU_CALCULADA", "filas": 2, "columnas": 3, "rango": 2})
    assert descripcion["dimensiones"] == "2×3"
    assert descripcion["detalle"] == "rango 2"


def test_panel_carga_rectangular_y_preserva_ceros():
    """Comprueba la carga irregular, los ceros y la limpieza del panel."""
    panel = PanelMatrizRectangular()
    panel.cargar_matriz([["0", "2", "3"], ["4"]])
    assert (panel.filas, panel.columnas, panel.dimension) == (2, 3, 3)
    assert panel.obtener_datos_matriz() == [["0", "2", "3"], ["4", "0", "0"]]
    panel.cargar_matriz([["0"]])
    assert not panel.esta_vacio()
    panel.limpiar()
    assert panel.esta_vacio()


def test_portapapeles_comparte_comportamiento():
    """Comprueba ambos formatos de pegado y los límites rectangulares."""
    assert parsear_texto_portapapeles("1, 2\n3,4") == [["1", "2"], ["3", "4"]]
    filas, recortado = parsear_portapapeles_rectangular("1,,3\n4,5,6", 10)
    assert filas == [["1", "0", "3"], ["4", "5", "6"]] and not recortado
    filas, _ = parsear_portapapeles_rectangular("1\t2\n\t\n3\t4", 10)
    assert filas == [["1", "2"], ["0", "0"], ["3", "4"]]
    filas, recortado = parsear_portapapeles_rectangular("\n".join(["1"] * 10 + ["1,2,3"]), 10)
    assert len(filas) == 10 and recortado
    panel = PanelMatrizRectangular()
    panel.cargar_matriz([["1"]] * 10 + [["1", "2", "3"]])
    assert (panel.filas, panel.columnas) == (10, 1)


def test_pegado_pendiente_no_sobrescribe_edicion(monkeypatch):
    """Comprueba que una edición invalida una lectura pendiente del portapapeles."""
    async def comprobar():
        """Simula una lectura suspendida mientras se modifica la captura."""
        panel = PanelMatrizRectangular()
        respuesta = asyncio.Future()

        async def leer(_codigo):
            """Entrega el texto cuando se complete la lectura simulada."""
            return await respuesta

        monkeypatch.setattr("src.frontend.componentes.panel_matriz_rectangular_acciones.ui.run_javascript", leer)
        tarea = asyncio.create_task(panel.pegar_desde_portapapeles())
        await asyncio.sleep(0)
        panel.cargar_matriz([["7"]])
        respuesta.set_result("1,2")
        await tarea
        assert panel.obtener_datos_matriz() == [["7"]]

    asyncio.run(comprobar())
