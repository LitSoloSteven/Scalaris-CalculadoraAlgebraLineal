"""Revocación de solicitudes reales ante ediciones y cambios del ciclo de vida."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("cambio", ["edicion", "ida_y_vuelta", "limpieza", "cerrar", "contenedor"])
def test_resultado_pendiente_no_publica_tras_revocacion(monkeypatch, cambio):
    """Una solicitud revocada no normaliza campos, registra recientes ni adjunta contexto."""
    async def comprobar(vista):
        """Retiene la respuesta invertida mientras revoca su captura por diferentes vías."""
        inicio, liberar = asyncio.Event(), asyncio.Event()
        llamadas = []

        async def trabajar(calcular, captura):
            """Espera la revocación antes de ejecutar el controlador real."""
            llamadas.append(captura)
            inicio.set()
            await liberar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", trabajar)
        vista.cargar_captura(captura_regla_falsa(extremo_izquierdo="2", extremo_derecho="1"))
        tarea = asyncio.create_task(vista.resolver())
        await asyncio.wait_for(inicio.wait(), 2)
        assert vista.ocupado and not vista.boton_resolver.enabled
        _revocar(vista, cambio)
        await vista.resolver()
        assert len(llamadas) == 1
        liberar.set()
        await asyncio.wait_for(tarea, 2)
        assert vista.ultimo_resultado is None and not vista.historial
        assert vista.obtener_contexto_ia().resultado is None
        assert vista.superior.value != "2.0"
        assert not vista.ocupado and vista.tarea_calculo is None
    ejecutar_escenario(monkeypatch, comprobar)


def _revocar(vista, cambio):
    if cambio in {"edicion", "ida_y_vuelta"}:
        vista.inferior.set_value("3")
        if cambio == "ida_y_vuelta":
            vista.inferior.set_value("2")
    elif cambio == "limpieza":
        vista.limpiar_todo()
    elif cambio == "cerrar":
        vista.cerrar()
        vista.reabrir()
    else:
        vista.contenedor_resultados = ui.column()


@pytest.mark.parametrize("atributo,valor", [
    ("expresion", "x^2-3"), ("inferior", "0"), ("superior", "3"),
    ("tolerancia", "1e-9"), ("limite", "3"), ("unidad_angular", "grados"),
])
def test_editar_cualquier_campo_matematico_retira_resultado(monkeypatch, atributo, valor):
    """Las ediciones invalidan resultado, copia y contexto conservando los recientes ya calculados."""
    async def comprobar(vista):
        """Publica un cálculo real y edita un campo distinto en cada escenario."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        formato = vista.formato
        getattr(vista, atributo).set_value(valor)
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert formato.is_deleted and len(vista.historial) == 1
        assert not list(vista.contenedor_resultados)
    ejecutar_escenario(monkeypatch, comprobar)


def test_error_de_trabajador_no_deja_carga(monkeypatch):
    """El coordinador libera el botón ante fallo inesperado y no filtra detalles privados."""
    async def comprobar(vista):
        """Provoca un error del transporte y verifica la recuperación del formulario."""
        async def fallar(calcular, captura):
            """Interrumpe el transporte antes de recibir un resultado del motor."""
            raise RuntimeError("detalle privado del transporte")

        monkeypatch.setattr(run, "io_bound", fallar)
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        assert not vista.ocupado and vista.boton_resolver.enabled
        assert vista.ultimo_resultado is None and "privado" not in vista.estado.text
        assert "No se pudo completar" in vista.estado.text
    ejecutar_escenario(monkeypatch, comprobar)
