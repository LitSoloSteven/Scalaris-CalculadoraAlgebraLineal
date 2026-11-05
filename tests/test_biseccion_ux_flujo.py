"""Flujo de rango, selección por teclado y paginación de la vista de bisección."""
import asyncio

from nicegui import run, ui

from src.frontend.controladores.biseccion.controlador import calcular_presentacion
from src.frontend.vistas.biseccion.modos_captura import MODO_BUSQUEDA, MODO_INTERVALO
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def test_rango_compartido_y_un_solo_nodo_grafico(monkeypatch):
    """Rango y tarea cambian sin reemplazar Plotly ni modificar la captura matemática."""
    async def comprobar(vista):
        """Compara la identidad de Plotly después de editar, calcular y navegar."""
        vista.cargar_captura(captura_criterio())
        panel = vista.vista_previa
        grafico = panel.grafica
        vista.modos.set_value(MODO_BUSQUEDA)
        vista.exploracion.minimo.set_value("-2")
        vista.exploracion.maximo.set_value("4")
        await panel.tarea
        assert (panel.minimo.value, panel.maximo.value) == ("-2", "4")
        assert (vista.inferior.value, vista.superior.value) == ("1", "2")
        vista.modos.set_value(MODO_INTERVALO)
        await vista.resolver()
        vista.reproductor_pasos.ir_a(2)
        assert panel.grafica is grafico
        assert [elemento for elemento in grafico.client.elements.values() if isinstance(elemento, ui.plotly)] == [grafico]

    ejecutar_escenario(monkeypatch, comprobar)


def test_borrador_manual_carga_solo_al_confirmar(monkeypatch):
    """La alternativa de teclado deja intactos los extremos hasta confirmar."""
    async def comprobar(vista):
        """Verifica la captura antes y después de confirmar el par manual."""
        vista.cargar_captura(captura_criterio())
        vista.modos.set_value(MODO_BUSQUEDA)
        seleccion = vista.seleccion_grafico
        seleccion.iniciar()
        seleccion.campos[0].set_value("0")
        seleccion.campos[1].set_value("3")
        assert (vista.inferior.value, vista.superior.value) == ("1", "2")
        seleccion.confirmar()
        assert vista.modos.value == MODO_INTERVALO
        assert (float(vista.inferior.value), float(vista.superior.value)) == (0, 3)
        assert vista.ultimo_resultado is None

    ejecutar_escenario(monkeypatch, comprobar)


def test_tabla_serializa_hasta_quince_filas(monkeypatch):
    """La navegación solicita una sola porción de la traza y conserva el total."""
    async def comprobar(vista):
        """Activa Siguiente y verifica el primer registro de la segunda página."""
        vista.cargar_captura(captura_criterio("iteraciones", 40))
        await vista.resolver()
        elementos = list(vista.contenedor_resultados.descendants())
        tabla = next(elemento for elemento in elementos if isinstance(elemento, ui.table))
        siguiente = next(elemento for elemento in elementos if isinstance(elemento, ui.button) and elemento.text == "Siguiente")
        assert len(tabla.rows) == 15 and tabla.rows[0]["i"] == "1"
        evento = next(evento for evento in siguiente._event_listeners.values() if evento.type == "click")
        evento.handler(None)
        assert len(tabla.rows) == 15 and tabla.rows[0]["i"] == "16"

    ejecutar_escenario(monkeypatch, comprobar)


def test_editar_no_admite_otro_trabajador_individual(monkeypatch):
    """Revocar la publicación no libera el presupuesto de un trabajador en curso."""
    async def comprobar(vista):
        """Retiene una solicitud y comprueba el rechazo de otro envío."""
        inicio, liberar = asyncio.Event(), asyncio.Event()
        solicitudes = []

        async def trabajar(calcular, captura):
            """Registra exclusivamente los trabajos individuales."""
            if calcular is calcular_presentacion:
                solicitudes.append(captura)
                inicio.set()
                await liberar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", trabajar)
        vista.cargar_captura(captura_criterio())
        primera = asyncio.create_task(vista.resolver())
        await asyncio.wait_for(inicio.wait(), 2)
        vista.superior.set_value("3")
        await asyncio.wait_for(vista.resolver(), 2)
        assert len(solicitudes) == 1 and vista.ocupado
        liberar.set()
        await primera
        assert vista.ultimo_resultado is None and not vista.ocupado

    ejecutar_escenario(monkeypatch, comprobar)


def test_limpiar_conserva_velocidad_del_procedimiento(monkeypatch):
    """El ejercicio siguiente hereda la velocidad elegida en el procedimiento anterior."""
    async def comprobar(vista):
        """Cambia la velocidad desde su selector y monta otro resultado."""
        captura = captura_criterio()
        vista.cargar_captura(captura)
        await vista.resolver()
        selector = next(elemento for elemento in vista.contenedor_resultados.descendants()
                        if isinstance(elemento, ui.select) and "Rápida" in elemento.options)
        selector.set_value("Rápida")
        vista.limpiar_todo()
        vista.cargar_captura(captura)
        await vista.resolver()
        assert vista.reproductor_pasos.velocidad == "Rápida"

    ejecutar_escenario(monkeypatch, comprobar)
