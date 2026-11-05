"""Aceptación cruzada desde el muestreo hasta la presentación de cada resultado."""

import json

import pytest

from src.frontend.controladores.biseccion.contexto_biseccion import resumir_contexto_biseccion
from src.frontend.controladores.biseccion.controlador import calcular_presentacion
from src.frontend.controladores.biseccion.exploracion import presentar_candidato, resolver_exploracion
from src.frontend.controladores.biseccion.presentacion import construir_pasos, filas_tabla
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.controladores.biseccion.salidas_biseccion import texto_copia_biseccion
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa
from tests.comun_biseccion_criterios import captura_criterio


def _intervalo(captura, intervalo):
    inferior, superior = intervalo
    return {**captura, "extremo_izquierdo": inferior, "extremo_derecho": superior}


def _candidatos_aptos(exploracion):
    return [{"identificador": f"candidato-{indice}", "candidato": candidato}
            for indice, candidato in enumerate(exploracion["candidatos"], 1)
            if presentar_candidato(candidato)["seleccionable"]]


def _comprobar_presentacion(respuesta, estado, motivo):
    filas = respuesta["iteraciones"]
    pasos, _ = construir_pasos(respuesta)
    tabla = filas_tabla(respuesta, completo=True)
    contexto = resumir_contexto_biseccion(respuesta)
    copia = texto_copia_biseccion(respuesta, 4, examen=True)
    assert respuesta["estado"] == contexto["estado"] == estado
    assert respuesta["motivo_parada"] == contexto["motivo_parada"] == motivo
    assert len(tabla) == len(pasos) - 2 == contexto["total_iteraciones"] == len(filas)
    assert pasos[-2].cuerpo == filas[-1]
    ultima = contexto["ultima_fila_valida"]
    assert (ultima["a"], ultima["b"]) == (filas[-1]["extremo_izquierdo"], filas[-1]["extremo_derecho"])
    assert float(tabla[-1]["c"]) == ultima["c"] == respuesta["aproximacion"]
    assert ultima["accion"] == "detener" and ultima["motivo_parada"] == motivo
    assert contexto["titulo_estado"] in copia
    assert copia.splitlines()[-1].startswith(f"{ultima['i']}\t")
    assert "\tDetener." in copia.splitlines()[-1]
    json.dumps(contexto, allow_nan=False)


@pytest.mark.parametrize("tipo,parametro,estado,motivo", [
    ("relativo", .0001, "EXITO", "relativo_menor_que_porcentaje"),
    ("ancho", .0001, "EXITO", "ancho_menor_que_E"),
    ("decimales", 4, "EXITO", "ancho_menor_que_E"),
    ("residuo", .000001, "EXITO", "residuo_menor_que_delta"),
    ("iteraciones", 8, "ITERACIONES_COMPLETADAS", "iteraciones_completadas"),
])
def test_candidatos_en_grados_comparten_traza_y_muestreo(tipo, parametro, estado, motivo):
    """Cruza normalización, unidad, selección, lote, gráfica, tabla, pasos, copia y Glosa."""
    captura = {**captura_criterio(tipo, parametro), "expresion": "2sin(x) − 1", "unidad_angular": "grados"}
    exploracion = resolver_exploracion({**captura, "x_min": 0, "x_max": 180, "paso": 11})
    aptos = _candidatos_aptos(exploracion)
    lote = resolver_lote({"configuracion": captura, "candidatos": aptos})
    assert exploracion["estado"] == "EXITO" and lote["estado"] == "LOTE_COMPLETADO"
    assert len(aptos) == len(lote["resultados"]) == 2
    pares = zip(aptos, lote["resultados"], (30, 150), strict=True)
    for candidato, registro, raiz in pares:
        intervalo = candidato["candidato"]["intervalo"]
        individual = calcular_presentacion(_intervalo(captura, intervalo))
        previa = preparar_vista_previa({**captura, "x_min": intervalo[0], "x_max": intervalo[1]})
        respuesta = registro["respuesta"]
        assert registro["identificador"] == candidato["identificador"]
        assert respuesta == {clave: individual[clave] for clave in respuesta}
        assert individual["muestra"] == previa["muestra"] and not previa["muestra"]["huecos"]
        assert individual["unidad_angular"] == "grados"
        assert respuesta["aproximacion"] == pytest.approx(raiz, abs=.05 if tipo == "iteraciones" else .0001)
        _comprobar_presentacion(individual, estado, motivo)
        json.dumps((individual, previa), allow_nan=False)
    json.dumps((exploracion, lote), allow_nan=False)


def test_polo_en_grados_se_separa_de_un_cruce_resoluble():
    """La gráfica y la exploración aíslan el polo y el lote conserva el cruce real."""
    captura = {**captura_criterio(), "expresion": "tan(x)", "unidad_angular": "grados"}
    rango = {**captura, "x_min": 70, "x_max": 200, "paso": 11}
    previa = preparar_vista_previa(rango)
    exploracion = resolver_exploracion(rango)
    aptos = _candidatos_aptos(exploracion)
    lote = resolver_lote({"configuracion": captura, "candidatos": aptos})
    assert previa["estado"] == exploracion["estado"] == "EXITO" and previa["muestra"]["huecos"]
    polos = [candidato for candidato in exploracion["candidatos"] if candidato["tipo"] == "discontinuidad"]
    assert len(polos) == len(aptos) == len(lote["resultados"]) == 1
    polo = calcular_presentacion(_intervalo(captura, polos[0]["intervalo"]))
    assert polo["estado"] == "ERROR" and polo["codigo_diagnostico"] == "SINGULARIDAD_DETECTADA"
    assert polo["aproximacion"] is None and not polo["iteraciones"]
    assert polo["contexto_fallo"]["x_fallo"] is None
    respuesta = lote["resultados"][0]["respuesta"]
    assert respuesta["aproximacion"] == pytest.approx(180, abs=.0001)
    _comprobar_presentacion(respuesta, "EXITO", "ancho_menor_que_E")
    json.dumps((previa, exploracion, lote, polo), allow_nan=False)


def test_lote_conserva_dos_ceros_en_el_mismo_intervalo():
    """La abscisa seleccionada distingue candidatos con ambos extremos en cero."""
    captura = _intervalo({**captura_criterio(), "expresion": "x*(x-1)"}, (0, 1))
    exploracion = resolver_exploracion({**captura, "x_min": 0, "x_max": 1, "paso": 1})
    lote = resolver_lote({"configuracion": captura, "candidatos": _candidatos_aptos(exploracion)})
    respuestas = [registro["respuesta"] for registro in lote["resultados"]]
    assert lote["estado"] == "LOTE_COMPLETADO"
    assert [respuesta["aproximacion"] for respuesta in respuestas] == [0, 1]
    assert all(respuesta["codigo_diagnostico"] == "CERO_EVALUADO" and not respuesta["iteraciones"]
               for respuesta in respuestas)
    assert calcular_presentacion(captura)["aproximacion"] == 0
    json.dumps(lote, allow_nan=False)


def test_malla_incluye_un_extremo_que_coincide_por_redondeo():
    """Un paso de 0.3 llega a 1.5 sin duplicar el extremo ni rechazar el rango."""
    exploracion = resolver_exploracion({"expresion": "x-1.5", "x_min": 0, "x_max": 1.5, "paso": .3})
    assert exploracion["estado"] == "EXITO" and exploracion["evaluaciones"] == 6
    ceros = [registro["candidato"]["abscisa"] for registro in _candidatos_aptos(exploracion)]
    assert ceros == [1.5]
