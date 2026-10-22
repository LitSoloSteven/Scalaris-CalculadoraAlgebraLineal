"""Contratos de aislamiento y registro de los clientes de pruebas."""
from tests.comun_clientes import ClienteSimulado, PanelIASimulado
from tests.comun import limpiar_almacen_transferencia
from src.frontend.componentes.transferencia import _ALMACEN, guardar_matriz


def test_cliente_registra_contexto_y_javascript():
    """El cliente registra entrada, salida y código incluso al salir por excepción."""
    cliente = ClienteSimulado()
    try:
        with cliente:
            cliente.run_javascript("1 + 1", timeout=2)
            raise ValueError("salida de prueba")
    except ValueError:
        pass
    assert cliente.entradas == 1
    assert cliente.salidas == 1
    assert cliente.llamadas_js == ["1 + 1"]


def test_paneles_con_almacen_vacio_no_comparten_estado():
    """Cada panel respeta el almacén vacío explícito y mantiene su propio estado."""
    primer_almacen = {}
    segundo_almacen = {}
    primero = PanelIASimulado(almacen=primer_almacen)
    segundo = PanelIASimulado(almacen=segundo_almacen)
    primero._almacen["propio"] = 1
    assert primero._almacen is primer_almacen
    assert segundo._almacen is segundo_almacen
    assert primero._almacen["propio"] == 1
    assert segundo._almacen == {
        "ia_historial_chat": [], "ia_contexto_habilitado": True, "ia_panel_abierto": False,
    }


def test_limpieza_almacen_transferencia_es_repetible():
    """La limpieza elimina transferencias y admite un almacén ya vacío."""
    guardar_matriz("prueba", [["1"]])
    assert _ALMACEN
    limpiar_almacen_transferencia()
    assert _ALMACEN == {}
    limpiar_almacen_transferencia()
    assert _ALMACEN == {}
