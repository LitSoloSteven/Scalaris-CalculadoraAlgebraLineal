"""Paridad con los controladores e invalidación desde la captura compartida."""
import asyncio
from contextlib import asynccontextmanager

from nicegui import Client, core, run, ui
import pytest

from src.frontend.controladores.biseccion.controlador import calcular_presentacion as biseccion
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion as regla_falsa
from src.frontend.vistas.metodos_cerrados.vista_metodos_cerrados import VistaMetodosCerrados
from tests.comun_construccion_vistas import cerrar_cliente, preparar_transporte

CASOS = (
    ("x^2 - 2", "1", "2", "radianes"),
    ("x", "0", "2", "radianes"),
    ("x^2 + 1", "-1", "1", "radianes"),
    ("1/x", "-1", "1", "radianes"),
    ("cos(x) - 0.5", "0", "90", "grados"),
    ("x^2 -", "1", "2", "radianes"),
)


@asynccontextmanager
async def montar_vista(monkeypatch, metodo=BISECCION):
    """Monta la vista interna con elementos reales y transporte simulado."""
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-metodos-cerrados"))
    preparar_transporte(monkeypatch, cliente)
    vista = VistaMetodosCerrados(metodo)
    try:
        with cliente:
            vista.construir()
            yield vista, cliente
    finally:
        vista.cerrar()
        await cerrar_cliente(cliente, [])


def captura_ejercicio(expresion, inferior, superior, unidad) -> dict:
    """Devuelve campos de un ejercicio con límites y unidad explícitos."""
    return {"expresion": expresion, "extremo_izquierdo": inferior, "extremo_derecho": superior,
            "unidad_angular": unidad, "limite_iteraciones": "100"}


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
@pytest.mark.parametrize("ejercicio", CASOS)
def test_calculo_individual_conserva_respuesta_del_controlador(monkeypatch, metodo, ejercicio):
    """Compara estado, raíz, diagnósticos e iteraciones con la herramienta existente."""
    async def comprobar():
        """Contrasta la respuesta visible con el controlador del método seleccionado."""
        datos = captura_ejercicio(*ejercicio)
        async with montar_vista(monkeypatch, metodo) as (vista, _):
            vista.cargar_captura(datos)
            await vista.resolver()
            if metodo == BISECCION:
                esperado = biseccion({**datos, "decimales": 4, "criterio": {"tipo": "decimales", "parametro": 4}})
            else:
                esperado = regla_falsa({**datos, "tolerancia": "1e-06"})["resultado"]
            assert vista.ultimo_resultado == esperado
            assert not vista.ocupado
    asyncio.run(comprobar())


def test_cambio_de_metodo_preserva_borradores_y_revoca_calculo(monkeypatch):
    """La nueva solicitud termina aunque el trabajador del otro método siga activo."""
    async def comprobar():
        """Entrega una respuesta obsoleta después de publicar la vigente."""
        async with montar_vista(monkeypatch) as (vista, _):
            vista.cargar_captura(captura_ejercicio("x^2 - 2", "1", "2", "radianes"))
            vista.captura.parametros_criterio["decimales"].set_value("6")
            vista.captura.limite.set_value("37")
            iniciado, liberar = asyncio.Event(), asyncio.Event()
            continuar = run.io_bound

            async def trabajador(funcion, captura):
                """Mantiene retenido solo el trabajo de Bisección."""
                if captura.get("metodo") != BISECCION:
                    return await continuar(funcion, captura)
                iniciado.set()
                try:
                    await asyncio.shield(liberar.wait())
                except asyncio.CancelledError:
                    await liberar.wait()
                return await continuar(funcion, captura)

            monkeypatch.setattr(run, "io_bound", trabajador)
            anterior = asyncio.create_task(vista.resolver())
            await iniciado.wait()
            assert vista.ocupado
            vista.captura.metodo.set_value(REGLA_FALSA)
            assert vista.capturar()["criterio"] == {"tipo": "residuo", "parametro": "1e-06"}
            assert vista.capturar()["expresion"] == "x^2 - 2"
            assert not vista.ocupado
            await vista.resolver()
            vigente = vista.ultimo_resultado
            liberar.set()
            await anterior
            assert vista.ultimo_resultado is vigente and vigente["estado"] == "EXITO"
            vista.captura.metodo.set_value(BISECCION)
            assert vista.ultimo_resultado is None
            assert vista.capturar()["criterio"] == {"tipo": "decimales", "parametro": "6"}
            assert vista.capturar()["limite_iteraciones"] == "37"
    asyncio.run(comprobar())


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
def test_ejemplo_criterio_activo_y_extremos_canonicos(monkeypatch, metodo):
    """Ejecuta una sola iteración y mantiene los extremos que normaliza el método."""
    async def comprobar():
        """Activa el manejador del formulario con extremos invertidos."""
        async with montar_vista(monkeypatch, metodo) as (vista, cliente):
            vista.captura.ejemplos.set_value("Raíz de 2")
            assert vista.capturar()["expresion"] == "x^2 - 2"
            assert vista.ultimo_resultado is None
            vista.cargar_captura({"extremo_izquierdo": "2", "extremo_derecho": "1",
                                  "criterio": {"tipo": "iteraciones", "parametro": "1"}})
            formularios = [elemento for elemento in cliente.elements.values() if elemento.tag == "form"]
            assert len(formularios) == 1
            evento = next(evento for evento in formularios[0]._event_listeners.values() if evento.type == "submit.prevent")
            await evento.handler()
            assert len(vista.ultimo_resultado["iteraciones"]) == 1
            assert vista.capturar()["extremo_izquierdo"] == "1.0"
            assert vista.capturar()["extremo_derecho"] == "2.0"
    asyncio.run(comprobar())
