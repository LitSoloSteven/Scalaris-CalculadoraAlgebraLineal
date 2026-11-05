"""Estados accesibles y coherencia entre recientes, Glosa y el examen del lote."""
import asyncio
import json

import pytest
from nicegui import ui

from src.ai.contexto import serializar_contexto
from src.frontend.componentes.copia_resultado import texto_resultado_copiable
from src.frontend.controladores.biseccion.presentacion_criterio import titulo_estado
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.controladores.biseccion.salidas_biseccion import datos_examen
from src.frontend.vistas.biseccion import resultados_multiples
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _pulsar(boton):
    manejador = next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")
    manejador(None)


@pytest.mark.parametrize("ejemplo,estado,filas,unidad", [
    ("Cero en un extremo", "EXITO", 0, "radianes"),
    ("Tres iteraciones", "ITERACIONES_COMPLETADAS", 3, "radianes"),
    ("Posible discontinuidad", "CONTINUIDAD_NO_VERIFICADA", 15, "radianes"),
    ("Seno en grados", "EXITO", 21, "grados"),
])
def test_ejemplos_y_recientes_conservan_el_estado_y_la_captura(monkeypatch, ejemplo, estado, filas, unidad):
    """Comprueba la carga explícita y el estado anunciado en el control de restauración."""
    async def comprobar(vista):
        """Usa los botones montados para cargar, resolver y restaurar el ejercicio."""
        boton = next(elemento for elemento in ui.context.client.elements.values()
                     if isinstance(elemento, ui.button) and elemento.text == ejemplo)
        _pulsar(boton)
        assert vista.ultimo_resultado is None and not vista.historial
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        contexto = vista.obtener_contexto_ia()
        assert respuesta["estado"] == contexto.resultado["estado"] == estado
        assert contexto.resultado["unidad_angular"] == unidad
        assert contexto.resultado["total_iteraciones"] == filas
        assert ("ultima_fila_valida" in contexto.resultado) == bool(filas)
        assert "iteraciones" not in contexto.resultado
        serializado = json.loads(serializar_contexto(contexto).splitlines()[1])["resultado"]
        assert serializado["titulo_estado"] == titulo_estado(respuesta)
        reciente = next(elemento for elemento in vista.recientes.descendants() if isinstance(elemento, ui.button))
        assert titulo_estado(respuesta) in reciente.text and unidad in reciente.text
        guardada = vista.capturar()
        vista.expresion.set_value("x")
        _pulsar(reciente)
        assert vista.capturar() == guardada and len(vista.historial) == 1
        assert vista.obtener_contexto_ia().resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_reciente_de_error_parcial_conserva_solo_la_ultima_accion_valida(monkeypatch):
    """Distingue un fallo de evaluación de la partición válida que lo precede."""
    async def comprobar(vista):
        """Compara el título y la acción de la traza con el contexto serializado."""
        vista.cargar_captura({**captura_criterio(), "expresion": "(x-.1)/(x*x-.25)",
                              "extremo_izquierdo": "-1", "extremo_derecho": "1"})
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        resultado = json.loads(serializar_contexto(vista.obtener_contexto_ia()).splitlines()[1])["resultado"]
        reciente = next(elemento for elemento in vista.recientes.descendants() if isinstance(elemento, ui.button))
        assert titulo_estado(respuesta) in reciente.text
        assert vista.historial[0]["estado"] == resultado["estado"] == "ERROR"
        assert resultado["aproximacion"] is None and resultado["contexto_fallo"]["x_fallo"] == -.5
        fila = resultado["ultima_fila_valida"]
        assert fila["accion"] == respuesta["iteraciones"][0]["accion"] == "reemplazar_b"
        assert fila["signo_producto"] == -1 and fila["motivo_parada"] == ""
    ejecutar_escenario(monkeypatch, comprobar)


def _captura_lote():
    return {"configuracion": {**captura_criterio(), "expresion": "(x-.8)/(x*x-.2)"},
            "candidatos": tuple({"identificador": nombre, "candidato": {"tipo": "cruce", "intervalo": intervalo}}
                                for nombre, intervalo in (("polo", (0, .6)), ("raiz", (.7, .9))))}


def _comprobar_traza(tabla, registro, copia):
    respuesta = registro["respuesta"]
    detalle = datos_examen(respuesta["iteraciones"][-1], respuesta["estado"])
    for clave, valor in detalle.items():
        assert tabla.rows[-1][clave] == valor
        assert valor in copia


def test_examen_del_lote_actualiza_tablas_y_copias_sin_cambiar_glosa(monkeypatch):
    """Comprueba la alternancia local y los textos de cada candidato."""
    textos = []
    monkeypatch.setattr(resultados_multiples, "renderizar_copia_resultado",
                        lambda generar: textos.append(texto_resultado_copiable(generar())))

    async def comprobar(vista):
        """Monta un lote mixto junto al resultado individual vigente."""
        vista.cargar_captura(captura_criterio("iteraciones", 3))
        await vista.resolver()
        contexto = vista.obtener_contexto_ia().resultado
        lote = resolver_lote(_captura_lote())
        panel = vista.resolucion_multiple
        panel._publicar(lote)
        for registro in lote["resultados"]:
            boton = next(elemento for elemento in panel.contenedor_resultados.descendants()
                         if isinstance(elemento, ui.button) and elemento.text.startswith(registro["identificador"] + " ·"))
            _pulsar(boton)
            elementos = list(panel.contenedor_resultados.descendants())
            examen = next(elemento for elemento in elementos if isinstance(elemento, ui.checkbox))
            tablas = [elemento for elemento in elementos if isinstance(elemento, ui.table)]
            assert examen.text == "Modo examen del lote" and not examen.value and len(tablas) == 1
            if registro["identificador"] == "polo":
                assert textos[-1].startswith("Resultado:\npolo\nPosible discontinuidad")
            assert "Modo examen" not in textos[-1]
            examen.set_value(True)
            await asyncio.sleep(0)
            _comprobar_traza(tablas[0], registro, textos[-1])
            examen.set_value(False)
            await asyncio.sleep(0)
            assert "accion_examen" not in tablas[0].rows[-1] and "Modo examen" not in textos[-1]
        assert vista.obtener_contexto_ia().resultado == contexto and not vista.modo_examen
    ejecutar_escenario(monkeypatch, comprobar)
