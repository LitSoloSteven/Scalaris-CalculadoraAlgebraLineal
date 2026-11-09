"""Contrato del ciclo de solicitud compartido sin un motor de producción simulado."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from nicegui import run

from src.ai.huellas import calcular_huella
from src.frontend.controladores.calculo_raices import ConfiguracionCalculoRaices, resolver_calculo_raices
from src.frontend.controladores.sesion_matricial import invalidar_resultado, notificar_edicion
from tests.comun import ejecutar_trabajador_simulado

_CONFIGURACION = ConfiguracionCalculoRaices(
    mensaje_carga="Calculando el ejercicio.", mensaje_error="Revisa el ejercicio.",
    mensaje_registro="No se pudo presentar el ejercicio",
)


def _crear_vista():
    vista = SimpleNamespace(
        ocupado=False, tarea_calculo=None, _revision_captura=0,
        contenedor_resultados=SimpleNamespace(is_deleted=False),
        boton_resolver=Mock(is_deleted=False), estado=Mock(is_deleted=False),
        capturar=lambda: {"ejercicio": "A"}, _publicar=Mock(),
    )
    vista._retirar_resultado = lambda: invalidar_resultado(vista)
    return vista


def test_publica_respuesta_y_huella_con_configuracion_explicita(monkeypatch):
    """El coordinador transmite los datos sin decidir matemáticas ni alterar la respuesta."""
    vista = _crear_vista()
    respuesta = {"estado": "prueba de transporte"}
    monkeypatch.setattr(run, "io_bound", ejecutar_trabajador_simulado)
    asyncio.run(resolver_calculo_raices(vista, lambda captura: respuesta, _CONFIGURACION, puntero=True))
    vista._publicar.assert_called_once_with(respuesta, calcular_huella(vista.capturar()), puntero=True)
    vista.estado.set_text.assert_called_once_with(_CONFIGURACION.mensaje_carga)
    assert not vista.ocupado and vista.tarea_calculo is None
    assert vista.boton_resolver.set_enabled.call_args.args == (True,)
    assert vista.boton_resolver.props.call_args.kwargs == {"remove": "loading"}


@pytest.mark.parametrize("cambio", ["edicion", "ida_y_vuelta", "limpieza", "desmontaje", "contenedor"])
def test_rechaza_respuestas_obsoletas_y_doble_envio(monkeypatch, cambio):
    """Cada revisión o contenedor revoca la publicación aunque el texto vuelva a ser A."""
    async def comprobar():
        vista, inicio, liberar = _crear_vista(), asyncio.Event(), asyncio.Event()
        captura, solicitudes = {"ejercicio": "A"}, []
        vista.capturar = lambda: dict(captura)

        async def trabajar(calcular, datos):
            solicitudes.append(datos)
            inicio.set()
            await liberar.wait()
            return calcular(datos)

        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(resolver_calculo_raices(vista, dict, _CONFIGURACION))
        await asyncio.wait_for(inicio.wait(), 2)
        _revocar(vista, captura, cambio)
        await resolver_calculo_raices(vista, dict, _CONFIGURACION)
        assert len(solicitudes) == 1 and vista.ocupado
        liberar.set()
        await asyncio.wait_for(tarea, 2)
        vista._publicar.assert_not_called()
        assert not vista.ocupado and vista.tarea_calculo is None
    asyncio.run(comprobar())


def _revocar(vista, captura, cambio):
    if cambio in {"edicion", "ida_y_vuelta"}:
        captura["ejercicio"] = "B"
        notificar_edicion(vista)
        if cambio == "ida_y_vuelta":
            captura["ejercicio"] = "A"
            notificar_edicion(vista)
    elif cambio == "limpieza":
        invalidar_resultado(vista)
    elif cambio == "desmontaje":
        vista.contenedor_resultados.is_deleted = True
        vista.boton_resolver.is_deleted = True
    else:
        vista.contenedor_resultados = SimpleNamespace(is_deleted=False)


@pytest.mark.parametrize("revocar", [False, True])
def test_error_inesperado_solo_anuncia_en_solicitud_vigente(monkeypatch, revocar):
    """Un fallo obsoleto se descarta y el vigente usa texto controlado."""
    vista = _crear_vista()

    async def fallar(calcular, captura):
        if revocar:
            notificar_edicion(vista)
        raise RuntimeError("detalle interno de prueba")

    monkeypatch.setattr(run, "io_bound", fallar)
    asyncio.run(resolver_calculo_raices(vista, dict, _CONFIGURACION))
    esperado = _CONFIGURACION.mensaje_carga if revocar else _CONFIGURACION.mensaje_error
    assert vista.estado.set_text.call_args.args == (esperado,)
    vista._publicar.assert_not_called()
    assert not vista.ocupado and vista.tarea_calculo is None


def test_cancelacion_libera_la_carga_sin_publicar(monkeypatch):
    """Cancelar una espera no convierte su resultado en éxito ni retiene el botón."""
    async def comprobar():
        vista, inicio = _crear_vista(), asyncio.Event()

        async def esperar(calcular, captura):
            inicio.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(run, "io_bound", esperar)
        tarea = asyncio.create_task(resolver_calculo_raices(vista, dict, _CONFIGURACION))
        await asyncio.wait_for(inicio.wait(), 2)
        tarea.cancel()
        await asyncio.wait_for(tarea, 2)
        vista._publicar.assert_not_called()
        assert not vista.ocupado and vista.tarea_calculo is None
        assert vista.boton_resolver.set_enabled.call_args.args == (True,)
    asyncio.run(comprobar())


def test_no_interfiere_con_una_tarea_que_reemplazo_la_solicitud(monkeypatch):
    """El finally antiguo no borra el estado de una solicitud con identidad diferente."""
    vista = _crear_vista()
    reemplazo = object()

    async def trabajar(calcular, captura):
        vista.tarea_calculo = reemplazo
        return calcular(captura)

    monkeypatch.setattr(run, "io_bound", trabajar)
    asyncio.run(resolver_calculo_raices(vista, dict, _CONFIGURACION))
    vista._publicar.assert_not_called()
    assert vista.tarea_calculo is reemplazo and vista.ocupado


@pytest.mark.parametrize("ocupado,eliminado", [(True, False), (False, True)])
def test_solicitud_no_disponible_no_ejecuta_controlador(ocupado, eliminado):
    """Una vista ocupada o desmontada rechaza el envío antes de retirar contenido."""
    vista, controlador = _crear_vista(), Mock()
    vista.ocupado = ocupado
    vista.contenedor_resultados.is_deleted = eliminado
    asyncio.run(resolver_calculo_raices(vista, controlador, _CONFIGURACION))
    controlador.assert_not_called()
    vista.estado.set_text.assert_not_called()
