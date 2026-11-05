"""Contrasta la acción registrada con los intervalos y cierres efectivos del motor."""
import json

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.frontend.controladores.biseccion.controlador import serializar_resultado


@pytest.mark.parametrize("escala", ["1e-300", "1", "1e300", "-1e300"])
def test_signo_y_reemplazos_coinciden_con_la_siguiente_fila(escala):
    """Conserva signos aunque el producto desborde o se redondee a cero."""
    entrada = EntradaBiseccion(f"{escala}*(x-.375)", 0, 1, 4)
    primera, segunda, ultima = biseccion(entrada).iteraciones
    assert (primera.signo_producto, primera.accion, primera.motivo_parada) == (-1, "reemplazar_b", "")
    assert (segunda.extremo_izquierdo, segunda.extremo_derecho, segunda.f_b) == (0, primera.c, primera.f_c)
    assert (segunda.signo_producto, segunda.accion, segunda.motivo_parada) == (1, "reemplazar_a", "")
    assert (ultima.extremo_izquierdo, ultima.extremo_derecho, ultima.f_a) == (segunda.c, primera.c, segunda.f_c)
    assert (ultima.signo_producto, ultima.accion, ultima.motivo_parada) == (0, "detener", "raiz_exacta")


@pytest.mark.parametrize("tipo,parametro,limite,motivo", [
    ("decimales", 4, 100, "ancho_menor_que_E"),
    ("ancho", .5, 100, "ancho_menor_que_E"),
    ("relativo", 1, 100, "relativo_menor_que_porcentaje"),
    ("residuo", .5, 100, "residuo_menor_que_delta"),
    ("iteraciones", 1, 1, "iteraciones_completadas"),
    ("decimales", 15, 1, "limite_iteraciones"),
])
def test_cierres_con_signo_no_registran_otra_particion(tipo, parametro, limite, motivo):
    """Publica el motivo efectivo aunque el signo permita elegir un extremo."""
    entrada = EntradaBiseccion("x*x-2", 1, 2, 4, limite, criterio=CriterioParada(tipo, parametro))
    resultado = biseccion(entrada)
    respuesta = serializar_resultado(entrada, resultado)
    ultima = respuesta["iteraciones"][-1]
    assert ultima["signo_producto"] in {-1, 1}
    assert ultima["accion"] == "detener" and ultima["motivo_parada"] == resultado.motivo_parada == motivo
    assert "Se conserva [" not in ultima["explicacion"]
    assert resultado.intervalo_final == (ultima["extremo_izquierdo"], ultima["extremo_derecho"])
    json.dumps(respuesta, allow_nan=False)


def test_estancamiento_registra_detencion_y_cero_extremo_no_inventa_fila():
    """Distingue el límite de representación de un cero evaluado antes de iterar."""
    estancado = biseccion(EntradaBiseccion("sin(x)", 1e16, 1e16 + 4, 15))
    ultima = estancado.iteraciones[-1]
    assert (ultima.accion, ultima.motivo_parada) == ("detener", "estancamiento")
    assert ultima.c in (ultima.extremo_izquierdo, ultima.extremo_derecho)
    assert ultima.explicacion == estancado.mensaje
    extremo = biseccion(EntradaBiseccion("x", 0, 1, 4))
    assert extremo.motivo_parada == "raiz_exacta" and extremo.iteraciones == ()


def test_sospecha_conserva_la_detencion_por_ancho():
    """El diagnóstico provisional conserva la causa original de la parada."""
    resultado = biseccion(EntradaBiseccion("1/(x*x-.2)", 0, 1, 4))
    ultima = resultado.iteraciones[-1]
    assert resultado.estado == "CONTINUIDAD_NO_VERIFICADA"
    assert (ultima.accion, ultima.motivo_parada) == ("detener", resultado.motivo_parada)
    assert ultima.motivo_parada == "ancho_menor_que_E"


def test_fallo_posterior_conserva_la_particion_ya_ejecutada():
    """Un punto inválido conserva el intervalo producido por la última fila válida."""
    resultado = biseccion(EntradaBiseccion("1/(x*x-.0625)", 0, 1, 4))
    assert resultado.estado == "ERROR" and resultado.motivo_parada == "evaluacion_invalida"
    ultima, = resultado.iteraciones
    assert (ultima.signo_producto, ultima.accion, ultima.motivo_parada) == (-1, "reemplazar_b", "")
    assert resultado.contexto_fallo["x_fallo"] == .25
    assert resultado.intervalo_final == (ultima.extremo_izquierdo, ultima.c)
