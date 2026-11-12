"""Diagnóstico geométrico propio, política de dominio y descarte de publicaciones antiguas."""
import asyncio
import json

import pytest
from nicegui import run

from src.frontend.controladores.regla_falsa.continuidad_intervalo import consultar_continuidad
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("expresion,inferior,superior,estado", [
    ("x^2-2", "1", "2", "CONFIRMADA"),
    ("sin(x)", "1", "2", "NO_VERIFICADA"),
    ("1/(x-0.1234)", "0", "1", "RESTRICCION_DETECTADA"),
    ("sqrt(x)-1", "-1", "4", "RESTRICCION_DETECTADA"),
])
def test_diagnostico_sin_configuracion_de_parada(expresion, inferior, superior, estado):
    """Un borrador inválido de tolerancia o límite no altera continuidad ni sus evidencias."""
    captura = captura_regla_falsa(expresion=expresion, extremo_izquierdo=inferior,
                                 extremo_derecho=superior, tolerancia="nan", limite_iteraciones="")
    respuesta = consultar_continuidad(captura)
    assert respuesta["informe"]["estado"] == estado
    assert respuesta["informe"]["evidencia"]
    assert len(respuesta["evaluaciones"]) == 2
    assert set(respuesta) == {"informe", "evaluaciones", "restriccion", "fallo"}
    assert "arbol" not in respuesta and "funcion" not in respuesta
    json.dumps(respuesta, allow_nan=False)


@pytest.mark.parametrize("cambios", [{"expresion": "x+"}, {"extremo_izquierdo": "nan"},
                                     {"extremo_derecho": "1"}, {"expresion": ""}])
def test_consulta_invalida_no_inventa_continuidad(cambios):
    """La preparación conserva fallos sintácticos o devuelve orientación sin fingir confirmación."""
    respuesta = consultar_continuidad(captura_regla_falsa(**cambios))
    assert respuesta.get("mensaje") or respuesta["fallo"]["estado"] == "ERROR"
    json.dumps(respuesta, allow_nan=False)


def test_unidad_y_extremos_normalizados():
    """La evaluación usa grados y conserva la normalización real del dominio."""
    respuesta = consultar_continuidad(captura_regla_falsa(
        expresion="sin(x)", extremo_izquierdo="90", extremo_derecho="0", unidad_angular="grados"))
    assert respuesta["informe"]["intervalo"] == (0, 90)
    assert respuesta["evaluaciones"][-1]["valor"] == pytest.approx(1)


def test_cambio_de_parada_no_reconsulta_y_resultado_final_manda(monkeypatch):
    """Continuidad depende de geometría; el resultado mantiene autoridad después del cálculo."""
    async def comprobar(vista):
        """Contrasta identidades y preferencias sin recalcular la consulta previa."""
        vista.cargar_captura(captura_regla_falsa())
        panel = vista.continuidad
        await panel.tarea
        respuesta = panel.respuesta
        vista.tolerancia.set_value("inválida")
        assert panel.tarea is None and panel.respuesta is respuesta
        vista.tolerancia.set_value("1e-6")
        await vista.resolver()
        assert not panel.region.visible and vista.ultimo_resultado["estado"] == "EXITO"
        vista.formato.set_value(3)
        assert panel.respuesta is respuesta and not panel.region.visible
        vista.inferior.set_value("0")
        assert vista.ultimo_resultado is None and panel.region.visible
        await panel.tarea
        assert panel.respuesta["informe"]["intervalo"] == (0, 2)
    ejecutar_escenario(monkeypatch, comprobar)


def test_rafaga_desconexion_y_reconexion(monkeypatch):
    """Una consulta retenida no publica tras editar, cerrar o reconectar con nuevos extremos."""
    async def comprobar(vista):
        """Controla el trabajador con eventos para verificar una sola plaza y un borrador."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.vista_previa.tarea
        panel = vista.continuidad
        if panel.tarea is not None:
            await panel.tarea
        inicio, liberar = asyncio.Event(), asyncio.Event()
        async def trabajar(calcular, captura):
            """Retiene únicamente la consulta de continuidad de este escenario."""
            inicio.set()
            await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        vista.inferior.set_value("0")
        await inicio.wait()
        for indice in range(2, 12):
            vista.superior.set_value(str(indice))
            assert panel.coordinador.activos == 1
            assert panel.coordinador.pendientes <= 1
        vista.cerrar()
        liberar.set()
        await panel.coordinador.esperar_cierre()
        assert panel.respuesta is None
        vista.reabrir()
        await panel.tarea
        assert panel.respuesta["informe"]["intervalo"] == (0, 11)
    ejecutar_escenario(monkeypatch, comprobar)


def test_cero_numerico_restaurado_es_un_extremo_completo(monkeypatch):
    """Las capturas serializadas con cero numérico conservan diagnóstico y evaluaciones."""
    async def comprobar(vista):
        """Restaura valores numéricos, espera el panel y comprueba el cero original."""
        vista.cargar_captura(captura_regla_falsa(expresion="x", extremo_izquierdo=0, extremo_derecho=2))
        panel = vista.continuidad
        assert panel.tarea is not None
        await panel.tarea
        assert panel.respuesta["informe"]["intervalo"] == (0, 2)
        assert panel.respuesta["evaluaciones"][0]["valor"] == 0
        assert vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)
