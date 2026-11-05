"""Exploración desde controles reales, adaptación de errores y selección explícita."""
import json

import pytest
from nicegui import ui

from src.frontend.controladores.biseccion.exploracion import resolver_exploracion
from tests.comun_biseccion_criterios import ejecutar_escenario
from tests.comun_exploracion_biseccion import preparar_exploracion, acciones_exploracion, activar_accion


@pytest.mark.parametrize("indice", [0, 1])
def test_seleccionar_candidato_invalida_sin_resolver(monkeypatch, indice):
    """Seleccionar cada cero carga sus extremos, conserva criterio e invalida cálculo y contexto."""
    async def comprobar(vista):
        """Conserva un cálculo previo mientras explora y solo lo retira al seleccionar."""
        panel = preparar_exploracion(vista)
        vista.criterio.set_value("ancho")
        vista.parametros_criterio["ancho"].set_value(".01")
        await vista.resolver()
        resultado = vista.ultimo_resultado
        reproductor = vista.reproductor_pasos
        historial = len(vista.historial)
        await panel.explorar()
        assert vista.ultimo_resultado is resultado
        assert vista.reproductor_pasos is reproductor
        assert len(acciones_exploracion(panel)) == 2
        fuente = panel.respuesta
        intervalo = fuente["candidatos"][indice]["intervalo"]
        activar_accion(acciones_exploracion(panel)[indice])
        assert (float(vista.inferior.value), float(vista.superior.value)) == intervalo
        assert intervalo[0] < intervalo[1]
        assert vista.criterio.value == "ancho"
        assert vista.parametros_criterio["ancho"].value == ".01"
        assert vista.ultimo_resultado is None and vista.reproductor_pasos is None
        assert vista.obtener_contexto_ia().resultado is None
        assert len(vista.historial) == historial
        assert panel.respuesta is fuente and vista.region_intervalo.visible and not vista.region_busqueda.visible
        await vista.resolver()
        assert vista.ultimo_resultado["aproximacion"] == (-1, 1)[indice]
    ejecutar_escenario(monkeypatch, comprobar)


def test_rango_y_paso_no_invalidan_calculo(monkeypatch):
    """Las preferencias exploratorias conservan identidad del resultado, huella y contexto."""
    async def comprobar(vista):
        """Cambia rango/paso y copia el intervalo actual sin alterar los datos matemáticos."""
        panel = preparar_exploracion(vista)
        await vista.resolver()
        resultado, huella = vista.ultimo_resultado, vista._huella_resultado
        captura = vista.capturar()
        panel.minimo.set_value("-3")
        panel.maximo.set_value("3")
        panel.paso.set_value(".25")
        panel.usar_intervalo()
        assert (panel.minimo.value, panel.maximo.value) == (vista.inferior.value, vista.superior.value)
        assert vista.capturar() == captura
        assert vista.ultimo_resultado is resultado and vista._huella_resultado == huella
        assert vista.obtener_contexto_ia().resultado["estado"] == resultado["estado"]
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("expresion,tipo,acciones", [
    ("x^2-1", "cruce", 2), ("(x-.1)^2", "posible_contacto", 0),
    ("1/x", "segmento_invalido", 0), ("1/(x-.1)", "discontinuidad", 0),
])
def test_tipos_distintos_y_solo_aptos_seleccionables(monkeypatch, expresion, tipo, acciones):
    """Los contactos, huecos y polos se inspeccionan sin ofrecer una bisección improcedente."""
    async def comprobar(vista):
        """Explora sin necesitar un criterio válido y revisa las acciones reales."""
        panel = preparar_exploracion(vista, expresion, ".6" if tipo == "cruce" else ".5")
        vista.decimales.set_value(None)
        await panel.explorar()
        assert panel.respuesta["estado"] == "EXITO"
        assert any(candidato["tipo"] == tipo for candidato in panel.respuesta["candidatos"])
        assert len(acciones_exploracion(panel)) == acciones
        assert vista.ultimo_resultado is None and not vista.historial
    ejecutar_escenario(monkeypatch, comprobar)


def test_estado_vacio_y_errores_permiten_reintentar(monkeypatch):
    """La ausencia de candidatos no afirma inexistencia y un error no bloquea otra solicitud."""
    async def comprobar(vista):
        """Recorre error de paso, resultado vacío y dos ceros usando el mismo panel."""
        panel = preparar_exploracion(vista, "x^2+1", "0")
        await panel.explorar()
        assert panel.respuesta["estado"] == "ERROR"
        assert panel.boton.enabled and panel.tarea is None
        panel.paso.set_value(".5")
        await panel.explorar()
        assert panel.respuesta["candidatos"] == ()
        textos = [elemento.text for elemento in panel.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any("No se detectaron candidatos" in texto for texto in textos)
        vista.expresion.set_value("x^2-1")
        await panel.explorar()
        assert len(acciones_exploracion(panel)) == 2
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("situacion", ["editar", "restaurar", "cerrar", "ocupado", "ajeno"])
def test_accion_obsoleta_o_ajena_no_carga_intervalo(monkeypatch, situacion):
    """Los manejadores guardados no reviven tras editar/restaurar, desconectar o sustituir registro."""
    async def comprobar(vista):
        """Intenta seleccionar desde una respuesta antigua o durante cálculo principal."""
        panel = preparar_exploracion(vista)
        await panel.explorar()
        respuesta = panel.respuesta
        candidato = respuesta["candidatos"][0]
        if situacion == "ocupado":
            vista.ocupado = True
        elif situacion == "cerrar":
            vista._desconectar()
        elif situacion == "ajeno":
            candidato = dict(candidato)
        else:
            panel.paso.set_value(".25")
            if situacion == "restaurar":
                panel.paso.set_value(".5")
        captura = vista.capturar()
        panel.seleccionar(respuesta, candidato)
        assert vista.capturar() == captura
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("campo,valor", [("paso", ""), ("paso", "1e-999"), ("paso", True),
                                         ("x_min", "nan"), ("x_max", "inf"), ("x_max", "9" * 65),
                                         ("expresion", "x.real"), ("expresion", "__import__('os')")])
def test_adaptador_errores_y_json_estricto(campo, valor):
    """Los errores de captura y sintaxis son serializables y no se convierten en ceros."""
    captura = dict(expresion="x^2-1", x_min="-2", x_max="2", paso=".5")
    captura[campo] = valor
    respuesta = resolver_exploracion(captura)
    assert respuesta["estado"] == "ERROR" and respuesta["mensaje"]
    assert respuesta["candidatos"] == ()
    json.dumps(respuesta, allow_nan=False)
