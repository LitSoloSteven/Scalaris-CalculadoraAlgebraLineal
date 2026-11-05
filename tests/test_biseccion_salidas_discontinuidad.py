"""El estado provisional del motor se conserva en las salidas de bisección."""
import json

from nicegui import ui

from src.frontend.componentes.copia_resultado import texto_resultado_copiable
from src.frontend.controladores.biseccion import controlador
from src.frontend.controladores.biseccion.presentacion import construir_pasos, filas_tabla, motivo
from src.frontend.controladores.biseccion.presentacion_criterio import texto_resumen
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.vistas.biseccion.figura import crear_figura
from src.frontend.vistas.biseccion import resumen_criterio, resultados_multiples
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _captura():
    return {**captura_criterio(), "expresion": "1/(x*x-.2)", "extremo_izquierdo": 0, "extremo_derecho": 1}


def test_grafica_corta_intervalo_sin_cambiar_veredicto(monkeypatch):
    """Una malla sin huecos corta el segmento sospechoso y conserva los datos del motor."""
    original = {"x": [0, .25, .5, 1], "y": [-5, -7, 20, 1.25], "huecos": False}
    monkeypatch.setattr(controlador, "muestrear_funcion", lambda entrada: original)
    motor = controlador.resolver_captura(_captura())
    respuesta = controlador.calcular_presentacion(_captura())
    assert respuesta["estado"] == "CONTINUIDAD_NO_VERIFICADA"
    assert {clave: respuesta[clave] for clave in motor} == motor
    assert respuesta["muestra"]["y"] == [-5, -7, None, 1.25] and respuesta["muestra"]["huecos"]
    assert original["y"][2] == 20 and not original["huecos"]
    figura = crear_figura(respuesta, respuesta["muestra"])
    assert figura.data[0].connectgaps is False and figura.layout.hovermode is False
    assert figura.data[-1].name == "Muestra provisional"
    assert figura.data[-1].y[0] == respuesta["iteraciones"][-1]["f_c"]
    json.dumps(respuesta, allow_nan=False)


def test_copia_y_procedimiento_distinguen_motivo_y_sospecha():
    """La copia conserva el criterio y el procedimiento explica el punto provisional."""
    respuesta = controlador.calcular_presentacion({**_captura(), "criterio": {"tipo": "iteraciones", "parametro": 15}})
    texto = texto_resumen(respuesta, 4)
    assert "Posible discontinuidad" in texto and "Punto medio x" in texto
    assert "Intervalo sospechoso según la traza" in texto and "Menor residuo reciente" in texto
    assert respuesta["diagnostico"]["mensaje_parada"] == motivo(respuesta)
    pasos, _ = construir_pasos(respuesta)
    assert pasos[-1].descripcion == respuesta["mensaje"]
    assert motivo(respuesta) in pasos[-1].explicacion and "provisional" in pasos[-1].explicacion
    assert "última muestra" in pasos[-2].explicacion and len(filas_tabla(respuesta)) == 15


def _captura_lote():
    configuracion = {**_captura(), "expresion": "(x-.8)/(x*x-.2)"}
    candidatos = tuple({"identificador": nombre, "candidato": {"tipo": "cruce", "intervalo": intervalo}}
                       for nombre, intervalo in (("polo", (0, .6)), ("raiz", (.7, .9))))
    return {"configuracion": configuracion, "candidatos": candidatos}


def test_lote_conserva_diagnostico_individual_y_resultado_vecino():
    """El mismo motor separa una sospecha y una convergencia en intervalos distintos."""
    captura = _captura_lote()
    lote = resolver_lote(captura)
    polo, raiz = lote["resultados"]
    individual = controlador.resolver_captura({**captura["configuracion"], "extremo_derecho": .6})
    assert polo["respuesta"] == individual and polo["estado"] == "CONTINUIDAD_NO_VERIFICADA"
    assert raiz["estado"] == "EXITO" and raiz["respuesta"]["codigo_diagnostico"] == "CERO_EVALUADO"
    json.dumps(lote, allow_nan=False)


def test_vista_historial_y_glosa_comparten_estado_provisional(monkeypatch):
    """La vista vigente entrega a Glosa y recientes el diagnóstico publicado por el dominio."""
    async def comprobar(vista):
        """Resuelve desde el formulario y contrasta texto, contexto y registro reciente."""
        vista.cargar_captura(_captura())
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        contexto = vista.obtener_contexto_ia().resultado
        assert respuesta["estado"] == contexto["estado"] == vista.historial[0]["estado"] == "CONTINUIDAD_NO_VERIFICADA"
        assert contexto["diagnostico"] == respuesta["diagnostico"]
        assert contexto["motivo_parada"] == respuesta["motivo_parada"]
        botones = [elemento.text for elemento in vista.recientes.descendants() if isinstance(elemento, ui.button)]
        assert any("Provisional" in boton for boton in botones)
        assert "discontinuidad" in vista.estado.text and vista.reproductor_pasos is not None
    ejecutar_escenario(monkeypatch, comprobar)


def test_copia_individual_y_lote_rotulan_la_sospecha_como_resultado(monkeypatch):
    """El texto enviado al copiador identifica la sospecha como resultado provisional."""
    textos = []
    def registrar_copia(generar):
        """Captura el texto que construiría el componente compartido del portapapeles."""
        textos.append(texto_resultado_copiable(generar()))
    monkeypatch.setattr(resumen_criterio, "renderizar_copia_resultado", registrar_copia)
    monkeypatch.setattr(resultados_multiples, "renderizar_copia_resultado", registrar_copia)
    async def comprobar(vista):
        """Contrasta las cargas de copia emitidas por las dos vistas reales."""
        vista.cargar_captura(_captura())
        await vista.resolver()
        panel = vista.resolucion_multiple
        panel._publicar(resolver_lote(_captura_lote()))
        for boton in list(panel.contenedor_resultados.descendants()):
            if isinstance(boton, ui.button) and boton.text.startswith(("polo ·", "raiz ·")):
                next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")(None)
        assert textos[0].startswith("Resultado:\nPosible discontinuidad")
        assert textos[1].startswith("Resultado:\npolo\nPosible discontinuidad")
        assert textos[2].startswith("Solución:\nraiz\n")
    ejecutar_escenario(monkeypatch, comprobar)
