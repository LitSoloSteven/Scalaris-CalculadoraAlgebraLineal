"""Montaje, independencia y carreras del lote con controles NiceGUI reales."""
import asyncio
import math

import pytest
from nicegui import run, ui

from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.controladores.biseccion.presentacion import filas_tabla
from tests.comun_biseccion_criterios import ejecutar_escenario
from tests.comun_exploracion_biseccion import activar_accion, preparar_exploracion


async def _preparar(vista, principal=False):
    exploracion = preparar_exploracion(vista, "sin(x)", ".1")
    vista.cargar_captura({"extremo_izquierdo": "3", "extremo_derecho": "4"})
    if principal:
        await vista.resolver()
    exploracion.minimo.set_value("1")
    exploracion.maximo.set_value("10")
    await exploracion.explorar()
    return vista.resolucion_multiple


def _estado_principal(vista):
    return (id(vista.ultimo_resultado), id(vista.reproductor_pasos), vista._huella_resultado,
            vista.capturar(), vista.obtener_contexto_ia().resultado, list(vista.historial))


def test_resolver_todos_y_uno_conserva_calculo_y_tablas_separadas(monkeypatch):
    """El lote no reemplaza resultado, contexto, historial, captura ni reproductor del cálculo principal."""
    async def comprobar(vista):
        """Compara respuestas y tablas del lote antes de pedir solo su segundo candidato."""
        panel = await _preparar(vista, principal=True)
        principal = _estado_principal(vista)
        await panel.resolver_todos()
        registros = panel.respuesta["resultados"]
        assert [registro["respuesta"]["aproximacion"] for registro in registros] == pytest.approx(
            [math.pi, 2 * math.pi, 3 * math.pi], abs=1e-4)
        botones = [elemento for elemento in panel.contenedor_resultados.descendants()
                   if isinstance(elemento, ui.button) and elemento.text.startswith("candidato-")]
        assert len(botones) == 3
        for boton, registro in zip(botones, registros, strict=True):
            activar_accion(boton)
            elementos = list(panel.contenedor_resultados.descendants())
            tablas = [elemento for elemento in elementos if isinstance(elemento, ui.table)]
            assert len(tablas) == 1 and tablas[0].rows == filas_tabla(registro["respuesta"])[:15]
            precision = next(elemento for elemento in elementos if isinstance(elemento, ui.switch))
            assert not precision.value
            precision.set_value(True)
            assert tablas[0].rows == filas_tabla(registro["respuesta"], True)[:15]
        vista.formato.set_value(8)
        vista.vista_previa.minimo.set_value("-2")
        assert panel.respuesta is None
        vista.exploracion.minimo.set_value("1")
        await vista.exploracion.explorar()
        panel.selector.set_value("candidato-2")
        await panel.resolver_uno()
        assert len(panel.respuesta["resultados"]) == 1
        assert panel.respuesta["resultados"][0]["identificador"] == "candidato-2"
        assert _estado_principal(vista) == principal
    ejecutar_escenario(monkeypatch, comprobar)


def test_vacio_no_aptos_error_y_reintento(monkeypatch):
    """El panel orienta sin candidatos y permite corregir un criterio inválido antes de resolver."""
    async def comprobar(vista):
        """Comprueba habilitación, fallo local y nueva exploración con el mismo cliente."""
        panel = vista.resolucion_multiple
        assert not panel.boton_uno.enabled and not panel.boton_todos.enabled
        exploracion = preparar_exploracion(vista, "(x-.1)^2", ".5")
        await exploracion.explorar()
        assert not panel.candidatos and not panel.boton_todos.enabled
        panel = await _preparar(vista)
        vista.decimales.set_value(None)
        await vista.exploracion.explorar()
        await panel.resolver_todos()
        assert panel.respuesta["estado"] == "ERROR" and panel.boton_todos.enabled
        vista.decimales.set_value(2)
        await vista.exploracion.explorar()
        await panel.resolver_todos()
        assert panel.respuesta["estado"] == "LOTE_COMPLETADO"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["funcion", "restaurar", "rango", "paso", "criterio", "limite", "limpiar", "desconectar", "selector", "fuente"])
def test_edicion_descarta_lote_tardio(monkeypatch, cambio):
    """Ninguna respuesta retenida revive después de editar/restaurar captura o fuente."""
    async def comprobar(vista):
        """Simula un trabajador que finaliza aun después de cancelarse su espera."""
        panel = await _preparar(vista)
        inicio, liberar = asyncio.Event(), asyncio.Event()
        async def trabajar(calcular, captura):
            """Retiene solo el lote para no bloquear la gráfica previa independiente."""
            if calcular is resolver_lote:
                inicio.set()
                try:
                    await liberar.wait()
                except asyncio.CancelledError:
                    await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(panel.resolver_todos())
        await inicio.wait()
        assert not panel.boton_todos.enabled
        _cambiar(vista, cambio)
        liberar.set()
        await tarea
        assert panel.respuesta is None and not list(panel.contenedor_resultados.descendants())
        assert "disponible" not in panel.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def _cambiar(vista, cambio):
    if cambio in ("funcion", "restaurar"):
        vista.expresion.set_value("x")
        if cambio == "restaurar":
            vista.expresion.set_value("sin(x)")
    elif cambio == "rango":
        vista.exploracion.minimo.set_value("0")
    elif cambio == "paso":
        vista.exploracion.paso.set_value(".2")
    elif cambio == "criterio":
        vista.criterio.set_value("ancho")
    elif cambio == "limite":
        vista.limite.set_value(50)
    elif cambio == "limpiar":
        vista.limpiar_todo()
    elif cambio == "desconectar":
        vista._desconectar()
    elif cambio == "selector":
        vista.resolucion_multiple.selector.set_value("candidato-2")
    else:
        vista.exploracion.respuesta = dict(vista.exploracion.respuesta)


@pytest.mark.parametrize("primera", ["antigua", "nueva"])
def test_solicitudes_fuera_de_orden_no_se_reemplazan(monkeypatch, primera):
    """La respuesta antigua no altera el resultado nuevo ni libera sus controles mientras trabaja."""
    async def comprobar(vista):
        """Controla por separado la finalización de dos selecciones consecutivas."""
        panel = await _preparar(vista)
        inicios, permisos = [asyncio.Event(), asyncio.Event()], [asyncio.Event(), asyncio.Event()]
        async def trabajar(calcular, captura):
            """Retrasa cada lote hasta liberar su selección, tolerando cancelación de la primera."""
            if calcular is resolver_lote:
                indice = int(captura["candidatos"][0]["identificador"] != "candidato-1")
                inicios[indice].set()
                try:
                    await permisos[indice].wait()
                except asyncio.CancelledError:
                    await permisos[indice].wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        antigua = asyncio.create_task(panel.resolver_uno())
        await inicios[0].wait()
        panel.selector.set_value("candidato-2")
        nueva = asyncio.create_task(panel.resolver_uno())
        await inicios[1].wait()
        if primera == "antigua":
            permisos[0].set()
            await antigua
            assert panel.tarea is nueva and not panel.boton_uno.enabled
        permisos[1].set()
        await nueva
        respuesta = panel.respuesta
        permisos[0].set()
        await antigua
        assert panel.respuesta is respuesta and respuesta["resultados"][0]["identificador"] == "candidato-2"
        assert panel.tarea is None and panel.boton_todos.enabled
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["eliminar", "sustituir", "error_antiguo", "error_actual"])
def test_destino_y_fallos_del_lote(monkeypatch, cambio):
    """Un destino retirado y un fallo obsoleto no reciben mensajes o resultados tardíos."""
    async def comprobar(vista):
        """Sustituye el destino o provoca errores después de editar desde el trabajador."""
        panel = await _preparar(vista)
        async def trabajar(calcular, captura):
            """Falla solo el lote; conserva los trabajadores de la previa."""
            if calcular is not resolver_lote:
                return calcular(captura)
            if cambio == "eliminar":
                panel.contenedor_resultados.delete()
            elif cambio == "sustituir":
                with vista.contenedor_resultados:
                    panel.contenedor_resultados = ui.column()
            elif cambio == "error_antiguo":
                panel.selector.set_value("candidato-2")
                raise RuntimeError("detalle anterior")
            else:
                raise RuntimeError("detalle privado")
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        await asyncio.gather(asyncio.create_task(panel.resolver_todos()), return_exceptions=True)
        assert panel.respuesta is None
        assert ("No se pudo completar" in panel.estado.text) == (cambio == "error_actual")
        assert "detalle" not in panel.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def test_reconexion_exige_otra_exploracion_y_eliminacion_cancela(monkeypatch):
    """Reconectar no restaura candidatos ni resultados antiguos; eliminar cancela la espera."""
    async def comprobar(vista):
        """Invoca los callbacks registrados y comprueba que solo otra exploración habilita acciones."""
        panel = await _preparar(vista)
        await panel.resolver_todos()
        vista._desconectar()
        vista._reconectar()
        assert panel.respuesta is None and not panel.candidatos and not panel.boton_uno.enabled
        await vista.exploracion.explorar()
        await panel.resolver_uno()
        assert panel.respuesta["estado"] == "LOTE_COMPLETADO"
        for manejador in panel.selector.client.delete_handlers:
            manejador()
        assert panel.respuesta is None and panel.tarea is None and not panel.candidatos
    ejecutar_escenario(monkeypatch, comprobar)
