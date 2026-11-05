"""Acciones de sugerencia explícitas con controles reales y vigencia de respuesta."""
import pytest
from nicegui import ui

from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _captura_dominio():
    return {**captura_criterio(), "expresion": "sqrt(x)-2", "extremo_izquierdo": "-1", "extremo_derecho": "9"}


def _accion(vista, etiqueta):
    botones = [elemento for elemento in vista.contenedor_resultados.descendants()
               if isinstance(elemento, ui.button) and elemento.text == etiqueta]
    assert len(botones) == 1
    manejador = next(evento.handler for evento in botones[0]._event_listeners.values() if evento.type == "click")
    return lambda: manejador(None)


def test_intervalo_sugerido_solo_se_carga_al_pulsar_y_no_resuelve(monkeypatch):
    """La propuesta conserva el fallo original hasta una acción; después exige otro cálculo."""
    async def comprobar(vista):
        """Carga [0,9] mediante el manejador real y comprueba la invalidación del contexto."""
        vista.cargar_captura(_captura_dominio())
        await vista.resolver()
        resultado = vista.ultimo_resultado
        assert resultado["estado"] == "ERROR"
        assert (vista.inferior.value, vista.superior.value) == ("-1", "9")
        assert vista.obtener_contexto_ia().resultado["sugerencias"] == resultado["sugerencias"]
        _accion(vista, "Cargar intervalo [0, 9]")()
        assert (float(vista.inferior.value), float(vista.superior.value)) == (0, 9)
        assert vista.expresion.value == "sqrt(x)-2"
        assert vista.criterio.value == "decimales"
        assert vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert not vista.historial
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
        assert abs(vista.ultimo_resultado["aproximacion"] - 4) < .001
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("tolerancia", ["0.123", "", "nan"])
def test_accion_absoluta_conserva_tolerancia_sin_calcular(monkeypatch, tolerancia):
    """Elegir ancho no inventa un umbral ni ejecuta otro método automáticamente."""
    async def comprobar(vista):
        """Agota el relativo y activa el valor absoluto previo, incluso si requiere corrección."""
        captura = {**captura_criterio("relativo", "1"), "expresion": "x",
                   "extremo_izquierdo": "-1", "extremo_derecho": "2"}
        vista.cargar_captura(captura)
        vista.parametros_criterio["ancho"].set_value(tolerancia)
        await vista.resolver()
        assert len(vista.ultimo_resultado["iteraciones"]) == 100
        assert vista.criterio.value == "relativo"
        historial = len(vista.historial)
        _accion(vista, "Elegir ancho absoluto")()
        assert vista.criterio.value == "ancho"
        assert vista.parametros_criterio["ancho"].value == tolerancia
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
        assert len(vista.historial) == historial
        assert vista.obtener_contexto_ia().resultado is None
        assert vista.expresion.value == "x"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("situacion", ["editar", "restaurar", "desconectar", "ocupado"])
def test_accion_obsoleta_o_durante_trabajo_no_modifica_campos(monkeypatch, situacion):
    """Un manejador antiguo no aplica propuestas después de invalidar o mientras se calcula."""
    async def comprobar(vista):
        """Conserva la acción y reproduce cambios de estado antes de intentar reutilizarla."""
        vista.cargar_captura(_captura_dominio())
        await vista.resolver()
        accion = _accion(vista, "Cargar intervalo [0, 9]")
        if situacion == "ocupado":
            vista.ocupado = True
        elif situacion == "desconectar":
            vista._desconectar()
        else:
            vista.inferior.set_value("-2")
            if situacion == "restaurar":
                vista.inferior.set_value("-1")
        captura = vista.capturar()
        accion()
        assert vista.capturar() == captura
    ejecutar_escenario(monkeypatch, comprobar)
