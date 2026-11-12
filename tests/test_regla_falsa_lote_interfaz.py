"""Recorridos de selección, presupuesto, tabla y copia con controles NiceGUI reales."""
import pytest
from nicegui import ui

from src.backend.resolutores.raices.resolucion_multiple_regla_falsa import EVALUACIONES_EXTREMOS_REGLA_FALSA
from src.frontend.controladores.regla_falsa.tabla import filas_tabla
from src.frontend.vistas.regla_falsa import resultado
from src.frontend.vistas.regla_falsa.modos_captura import MODO_BUSQUEDA
from tests.comun_exploracion_biseccion import activar_accion
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


async def preparar_lote_vista(vista, expresion="x^3-x", **cambios):
    """Busca cruces con una malla que evita ceros exactos y devuelve el panel sin selección."""
    vista.cargar_captura(captura_regla_falsa(expresion=expresion, tolerancia="1e-13", **cambios))
    vista.modos.set_value(MODO_BUSQUEDA)
    exploracion = vista.exploracion
    exploracion.minimo.set_value("-1.51")
    exploracion.maximo.set_value("1.51")
    exploracion.paso.set_value(".23")
    await exploracion.enviar_busqueda()
    return vista.resolucion_multiple


def _botones_detalle(panel):
    return [elemento for elemento in panel.contenedor_resultados.descendants()
            if isinstance(elemento, ui.button) and elemento.text.startswith("Abrir candidato-")]


def test_seleccion_parcial_presenta_estados_y_presupuesto_sin_truncar(monkeypatch):
    """Selecciona tres cruces y admite dos sin transformar las reservas en consumo real."""
    async def comprobar(vista):
        """Comprueba los estados y acciones que resultan de una reserva parcial real."""
        panel = await preparar_lote_vista(vista)
        assert len(panel.candidatos) == 3 and not panel.selector.value and not panel.boton.enabled
        panel.selector.set_value(list(reversed(panel.candidatos)))
        reserva = int(vista.limite.value) + EVALUACIONES_EXTREMOS_REGLA_FALSA
        panel.presupuesto.set_value(str(2 * reserva))
        await panel.resolver()
        lote = panel.respuesta
        registros = lote["resultados"]
        assert [registro["identificador"] for registro in registros] == list(panel.candidatos)
        assert [registro["estado"] for registro in registros] == ["EXITO", "EXITO", "PRESUPUESTO_AGOTADO"]
        assert lote["estado"] == "LOTE_PARCIAL" and lote["evaluaciones_reservadas"] == 2 * reserva
        assert "Lote parcial" in panel.estado.text and len(_botones_detalle(panel)) == 2
        assert any("no un consumo medido" in elemento.text for elemento in panel.contenedor_resultados.descendants()
                   if isinstance(elemento, ui.label))
        panel.presupuesto.set_value("1.5")
        await panel.resolver()
        assert panel.respuesta["estado"] == "ERROR" and not _botones_detalle(panel)
    ejecutar_escenario(monkeypatch, comprobar)


def test_tabla_secante_copia_y_glosa_siguen_el_candidato_activo(monkeypatch):
    """Abre dos candidatos desde sus botones y compara sus datos y controles independientes."""
    generadores = []
    monkeypatch.setattr(resultado, "renderizar_copia_resultado", generadores.append)

    async def comprobar(vista):
        """Verifica las filas de la segunda página y descarta el reproductor anterior al cambiar."""
        panel = await preparar_lote_vista(vista, "x^2-2", criterio={"tipo": "iteraciones", "parametro": "18"})
        vista.exploracion.minimo.set_value("-4")
        vista.exploracion.maximo.set_value("4")
        vista.exploracion.paso.set_value("4")
        await vista.exploracion.enviar_busqueda()
        captura = vista.capturar()
        panel.selector.set_value(list(panel.candidatos))
        await panel.resolver()
        botones = _botones_detalle(panel)
        anterior = None
        for indice in (0, 1):
            activar_accion(botones[indice])
            if anterior is not None:
                assert anterior.tarjeta.is_deleted
            registro = panel.respuesta["resultados"][indice]
            _comprobar_detalle(vista, registro, generadores[-1])
            anterior = vista.reproductor_pasos
        assert vista.capturar() == captura and not vista.historial
        assert vista.ultimo_resultado["aproximacion"] == pytest.approx(2 ** .5, abs=.01)
    ejecutar_escenario(monkeypatch, comprobar)


def _comprobar_detalle(vista, registro, generar_copia):
    datos = registro["datos"]
    filas = datos["resultado"]["iteraciones"]
    assert len(filas) == 18
    paso = 16
    detalle = vista.detalle_procedimiento
    detalle.reproductor.ir_a(paso)
    assert detalle.tabla.tabla.rows == filas_tabla(filas[15:], False)
    fila = filas[paso - 1]
    secante = detalle._figura(fila, False)["data"][1]
    assert tuple(secante["x"]) == (fila["extremo_izquierdo"], fila["extremo_derecho"])
    contexto = vista.obtener_contexto_ia()
    assert contexto.entrada["identificador_candidato"] == registro["identificador"]
    assert contexto.foco.captura.detalle["iteracion"] is fila
    copia = next(iter(generar_copia().values()))
    assert copia.startswith(registro["identificador"] + "\nRegla falsa")
    assert f"x ≈ {datos['resultado']['aproximacion']:.4f}" in copia
