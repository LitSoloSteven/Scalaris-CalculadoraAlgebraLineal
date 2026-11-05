"""Edición angular y descarte de respuestas tardías en cálculo y paneles reales."""
import asyncio

import pytest
from nicegui import run

from src.ai.huellas import calcular_huella
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


async def _preparar(vista):
    vista.cargar_captura({**captura_criterio(), "expresion": "sin(x)", "extremo_izquierdo": 170,
                         "extremo_derecho": 190, "unidad_angular": "grados"})
    panel = vista.exploracion
    panel.minimo.set_value("1")
    panel.maximo.set_value("550")
    panel.paso.set_value("7")
    await panel.explorar()


def _seleccionar_trabajo(vista, destino):
    if destino == "principal":
        return vista, vista.resolver, "calcular_presentacion"
    if destino == "previa":
        return vista.vista_previa, vista.vista_previa.actualizar, "preparar_vista_previa"
    if destino == "exploracion":
        return vista.exploracion, vista.exploracion.explorar, "resolver_exploracion"
    return vista.resolucion_multiple, vista.resolucion_multiple.resolver_todos, "resolver_lote"


@pytest.mark.parametrize("destino", ["principal", "previa", "exploracion", "lote"])
@pytest.mark.parametrize("restaurar", [False, True])
def test_unidad_editada_descarta_respuesta_tardia(monkeypatch, destino, restaurar):
    """Ni volver a la unidad original permite publicar datos de una revisión anterior."""
    async def comprobar(vista):
        """Retiene solo el trabajador objetivo y cambia la unidad desde su selector real."""
        await _preparar(vista)
        panel, ejecutar, nombre = _seleccionar_trabajo(vista, destino)
        inicio, liberar = asyncio.Event(), asyncio.Event()
        async def trabajar(calcular, captura):
            """Permite terminar una respuesta vieja aun después de cancelarse su espera."""
            if calcular.__name__ == nombre:
                inicio.set()
                try:
                    await liberar.wait()
                except asyncio.CancelledError:
                    await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(ejecutar())
        await asyncio.wait_for(inicio.wait(), 3)
        vista.unidad_angular.set_value("radianes")
        if restaurar:
            vista.unidad_angular.set_value("grados")
        liberar.set()
        await tarea
        assert vista.ultimo_resultado is None
        assert getattr(panel, "respuesta", None) is None
        assert not list(panel.contenedor_resultados.descendants())
    ejecutar_escenario(monkeypatch, comprobar)


def test_huellas_y_limpieza_de_resultados_al_cambiar_unidad(monkeypatch):
    """La unidad afecta todas las capturas vigentes y retira tabla, reproductor y candidatos del lote."""
    async def comprobar(vista):
        """Publica un cálculo y los paneles antes de comprobar la invalidación transversal."""
        await _preparar(vista)
        await vista.resolver()
        await vista.exploracion.explorar()
        await vista.resolucion_multiple.resolver_todos()
        await vista.vista_previa.actualizar()
        paneles = (vista, vista.exploracion, vista.vista_previa, vista.resolucion_multiple)
        huellas = tuple(calcular_huella(panel.capturar()) for panel in paneles)
        assert vista.ultimo_resultado is not None and vista.reproductor_pasos is not None
        assert vista.resolucion_multiple.respuesta["unidad_angular"] == "grados"
        vista.unidad_angular.set_value("radianes")
        assert all(calcular_huella(panel.capturar()) != huella for panel, huella in zip(paneles, huellas))
        assert vista.ultimo_resultado is None and vista.reproductor_pasos is None
        assert all(panel.respuesta is None for panel in paneles[1:])
        assert not vista.resolucion_multiple.candidatos and not vista.resolucion_multiple.boton_todos.enabled
        assert vista.obtener_contexto_ia().entrada["unidad_angular"] == "radianes"
    ejecutar_escenario(monkeypatch, comprobar)
