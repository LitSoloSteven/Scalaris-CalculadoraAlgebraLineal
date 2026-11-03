"""Regresión del recorrido de precisión y sus adaptadores de presentación."""
import asyncio
import json
import math

import pytest
from nicegui import Client, core, run, ui

from src.frontend.controladores.biseccion.controlador import calcular_presentacion, resolver_captura, texto_tolerancia
from src.frontend.controladores.biseccion.muestreo import muestrear_funcion
from src.frontend.controladores.biseccion.presentacion import construir_pasos, filas_tabla
from src.frontend.navegacion import ruta_de, pilar_de
from src.frontend.vistas.biseccion.vista_biseccion import VistaBiseccion
from src.frontend.vistas.biseccion.figura import crear_figura
from tests.comun_construccion_vistas import preparar_transporte, cerrar_cliente


def captura(expresion="x^2 - 2", decimales=4, intervalo=("1", "2"), limite=100):
    """Construye los valores crudos equivalentes a los campos de la interfaz."""
    return {"expresion": expresion, "extremo_izquierdo": intervalo[0], "extremo_derecho": intervalo[1],
            "decimales": decimales, "limite_iteraciones": limite}


@pytest.mark.parametrize("decimales", [0, 2, 4, 6])
def test_precision_efectiva_y_presentacion(decimales):
    """Comprueba tolerancia, encierro de la raíz y serialización de valores finitos."""
    respuesta = calcular_presentacion(captura(decimales=decimales))
    inferior, superior = respuesta["intervalo_final"]
    assert respuesta["estado"] == "EXITO"
    assert respuesta["tolerancia"] == 10 ** -decimales
    assert superior - inferior < respuesta["tolerancia"]
    assert inferior <= math.sqrt(2) <= superior
    assert respuesta["cota"] == (superior - inferior) / 2
    json.dumps(respuesta, allow_nan=False)


def test_aumentar_precision_cambia_convergencia():
    """Verifica que d modifica iteraciones además del texto presentado."""
    respuestas = [resolver_captura(captura(decimales=valor)) for valor in [2, 4, 6]]
    assert [len(respuesta["iteraciones"]) for respuesta in respuestas] == [8, 15, 21]
    assert "0.01" in texto_tolerancia(2)
    assert "0.000001" in texto_tolerancia(6)


@pytest.mark.parametrize("datos, estado", [
    (captura("x", intervalo=("0", "2")), "EXITO"),
    (captura("x", intervalo=("-1", "1")), "EXITO"),
    (captura("x^2+1", intervalo=("-1", "1")), "SIN_CAMBIO_DE_SIGNO"),
    (captura("1/x", intervalo=("-1", "1")), "ERROR"),
    (captura("sqrt(x)", intervalo=("-1", "1")), "ERROR"),
    (captura("sin()"), "ERROR"),
    (captura("(-1)**0.5"), "ERROR"),
    (captura("__import__('os')"), "ERROR"),
    (captura(decimales=2.5), "ERROR"),
    (captura(decimales=16), "ERROR"),
    (captura(intervalo=("2", "1")), "ERROR"),
    (captura(limite=501), "ERROR"),
    (captura(decimales=6, limite=2), "PRECISION_NO_ALCANZADA"),
    (captura("x - 10000000000000002", 15, ("10000000000000000", "10000000000000004")), "EXITO"),
])
def test_estados_controlados(datos, estado):
    """Verifica errores de captura, evaluador y límite sin excepciones en la vista."""
    respuesta = resolver_captura(datos)
    assert respuesta["estado"] == estado
    if respuesta.get("motivo_parada") == "raiz_exacta":
        assert "aritmética aproximada" in respuesta["aviso"]


def test_traza_tabla_y_reproductor_comparten_valores():
    """Compara las magnitudes del motor con la tabla y la secuencia didáctica."""
    respuesta = resolver_captura(captura())
    pasos, grupos = construir_pasos(respuesta)
    assert len(pasos) == len(respuesta["iteraciones"]) + 2
    assert pasos[1].cuerpo == respuesta["iteraciones"][0]
    assert "Se devuelve el punto medio" in pasos[-2].explicacion
    assert filas_tabla(respuesta)[0]["error_relativo"] == "No aplica"
    assert filas_tabla(respuesta, True)[0]["c"] == "1.5"
    assert grupos[-1].indices_pasos == (len(pasos) - 1,)


def test_raiz_en_extremo_tiene_planteamiento_y_cierre():
    """Conserva un procedimiento explicable cuando no se requieren particiones."""
    respuesta = resolver_captura(captura("x", intervalo=("0", "2")))
    pasos, _ = construir_pasos(respuesta)
    assert len(pasos) == 2
    assert respuesta["aproximacion"] == 0


def test_grafica_no_une_evaluaciones_invalidas():
    """Mantiene un hueco explícito en la singularidad de la función muestreada."""
    muestra = muestrear_funcion({"expresion": "1/x", "extremo_izquierdo": -1, "extremo_derecho": 1})
    assert muestra["huecos"]
    assert muestra["x"][200] == 0
    assert muestra["y"][200] is None


def test_ejemplos_reproducibles_del_curso():
    """Recalcula las primeras filas del libro y la potencia décima de referencia."""
    polinomio = resolver_captura(captura("x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10", intervalo=("0.6", "1")))
    assert [fila["c"] for fila in polinomio["iteraciones"][:3]] == pytest.approx([0.8, 0.7, 0.75])
    assert polinomio["aproximacion"] == pytest.approx(0.763916015625)
    potencia = resolver_captura(captura("x^10-1", intervalo=("0", "1.3")))
    assert potencia["aproximacion"] == pytest.approx(1, abs=1e-4)


def test_ruta_y_categoria():
    """Comprueba la ubicación canónica de la herramienta numérica."""
    assert ruta_de("biseccion") == "/utilidades/biseccion"
    assert pilar_de("biseccion").identificador == "utilidades"


def test_salto_sospechoso_deja_resultado_provisional():
    """No anuncia una raíz cuando el muestreo observa un posible polo entre muestras."""
    respuesta = calcular_presentacion(captura("1/(x-0.1234)", intervalo=("-1", "1")))
    assert respuesta["estado"] == "CONTINUIDAD_NO_VERIFICADA"
    assert respuesta["muestra"]["huecos"]


def test_errores_de_captura_en_castellano():
    """Orienta sobre el campo incorrecto sin exponer errores de conversión de Python."""
    respuesta = resolver_captura(captura(intervalo=("texto", "2")))
    assert "extremo inferior a debe ser un número real" in respuesta["mensaje"]
    assert "precisión debe ser un entero" in resolver_captura(captura(decimales=None))["mensaje"]
    assert "no es real" in resolver_captura(captura("sqrt(x)", intervalo=("-1", "1")))["mensaje"]


def test_estancamiento_no_se_presenta_como_exito():
    """Conserva el estado provisional cuando la representación impide reducir el intervalo."""
    respuesta = resolver_captura(captura("sin(x)", 15, ("1e16", "10000000000000004")))
    assert respuesta["estado"] == "PRECISION_NO_ALCANZADA"
    assert respuesta["intervalo_final"][1] - respuesta["intervalo_final"][0] > respuesta["tolerancia"]


def test_figura_del_planteamiento_y_particion():
    """Comprueba intervalo inicial, punto medio y huecos sin unir en el gráfico."""
    respuesta = calcular_presentacion(captura())
    figura = crear_figura(respuesta, respuesta["muestra"], inicial=True)
    assert list(figura.data[1].x) == [1, 2]
    assert len(figura.data) == 2
    figura = crear_figura(respuesta, respuesta["muestra"], respuesta["iteraciones"][0])
    assert list(figura.data[2].x) == [1.5]
    assert figura.data[0].connectgaps is False


def test_recorrido_edicion_y_resultados_obsoletos(monkeypatch):
    """Ejercita cálculo, edición, limpieza y carrera dentro de un cliente NiceGUI."""
    async def comprobar():
        """Construye la vista y comprueba su contrato de vigencia sin red."""
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/prueba_biseccion"))
        preparar_transporte(monkeypatch, cliente)
        vista = VistaBiseccion()
        try:
            with cliente:
                vista.construir()
                vista.cargar_captura(captura())
                await vista.resolver()
                assert vista.ultimo_resultado["estado"] == "EXITO"
                assert vista.reproductor_pasos is not None
                assert vista.obtener_contexto_ia().resultado is not None
                vista.expresion.set_value("x^2 - 3")
                vista._editar()
                assert vista.ultimo_resultado is None
                assert vista.reproductor_pasos is None
                assert vista.obtener_contexto_ia().resultado is None
                await _comprobar_carrera(monkeypatch, vista)
                vista.limpiar_todo()
                assert vista.esta_completamente_vacio()
        finally:
            await cerrar_cliente(cliente, [vista])
    asyncio.run(comprobar())


async def _comprobar_carrera(monkeypatch, vista):
    async def editar_durante_calculo(funcion, datos):
        """Simula una captura nueva mientras se resuelve la petición anterior."""
        respuesta = funcion(datos)
        vista.decimales.set_value(6)
        vista._editar()
        return respuesta
    monkeypatch.setattr(run, "io_bound", editar_durante_calculo)
    await vista.resolver()
    assert vista.ultimo_resultado is None
    assert vista.obtener_contexto_ia().resultado is None
