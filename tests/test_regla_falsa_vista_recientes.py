"""Restauración explícita y aislada de ejemplos y cálculos recientes reales."""
from copy import deepcopy

from nicegui import ui

from src.frontend.vistas.regla_falsa.ejemplos import EJEMPLOS
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_ejemplos_cargan_sin_ejecutar_y_respetan_el_contrato(monkeypatch):
    """Cada botón restaura el ejemplo correspondiente y deja el cálculo como acción explícita."""
    async def comprobar(vista):
        """Activa los manejadores reales de los seis ejemplos y luego calcula con su motor."""
        for etiqueta, captura in EJEMPLOS:
            boton = next(elemento for elemento in vista.contenedor_acciones.descendants()
                         if isinstance(elemento, ui.button) and elemento.text == etiqueta)
            evento = next(evento for evento in boton._event_listeners.values() if evento.type == "click")
            evento.handler(None)
            assert vista.capturar() == captura and vista.ultimo_resultado is None
            await vista.resolver()
            assert vista.ultimo_resultado["estado"] != "ERROR"
        assert len(vista.historial) == 5
        assert vista.historial[0]["estado"] == "LIMITE_ITERACIONES"
    ejecutar_escenario(monkeypatch, comprobar)


def test_reciente_restaura_preferencias_sin_recalcular(monkeypatch):
    """El historial conserva capturas independientes, incluida unidad angular y tolerancia."""
    async def comprobar(vista):
        """Calcula en grados, altera los campos y activa el botón del registro anterior."""
        captura = captura_regla_falsa(expresion="2sin(x)-1", extremo_izquierdo="0",
                                     extremo_derecho="60", unidad_angular="grados", tolerancia="1e-9")
        vista.cargar_captura(captura)
        await vista.resolver()
        registro = deepcopy(vista.historial[0])
        vista.cargar_captura(captura_regla_falsa())
        boton = next(elemento for elemento in vista.recientes.descendants() if isinstance(elemento, ui.button))
        evento = next(evento for evento in boton._event_listeners.values() if evento.type == "click")
        evento.handler(None)
        assert vista.capturar() == captura and vista.ultimo_resultado is None
        assert vista.historial[0] == registro
        vista.expresion.set_value("x")
        assert vista.historial[0]["captura"]["expresion"] == "2sin(x)-1"
    ejecutar_escenario(monkeypatch, comprobar)


def test_recientes_y_preferencias_son_independientes_por_cliente(monkeypatch):
    """Dos vistas montadas conservan historiales y resultados propios."""
    async def comprobar(vista):
        """Construye otra vista en el cliente y verifica ausencia de estado compartido."""
        otra = type(vista)()
        otra.construir()
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        assert len(vista.historial) == 1 and not otra.historial
        assert otra.ultimo_resultado is None and otra.esta_completamente_vacio()
        otra.limpiar_todo()
        assert vista.ultimo_resultado is not None
    ejecutar_escenario(monkeypatch, comprobar)


def test_limpiar_desde_la_confirmacion_reutilizada_retira_resultados(monkeypatch):
    """La acción de limpieza confirma y usa el mismo vaciado y preservación de preferencias."""
    async def comprobar(vista):
        """Ejecuta la confirmación real sin sustituir el controlador ni el cálculo."""
        vista.cargar_captura(captura_regla_falsa(tolerancia="1e-9"))
        await vista.resolver()
        await vista.limpieza.confirmar()
        assert vista.limpieza.dialogo is not None
        await vista.limpieza.ejecutar()
        assert vista.esta_completamente_vacio() and vista.ultimo_resultado is None
        assert vista.tolerancia.value == "1e-9" and len(vista.historial) == 1
    ejecutar_escenario(monkeypatch, comprobar)
