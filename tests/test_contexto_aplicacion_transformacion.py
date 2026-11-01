"""Contexto exacto vigente y acotado de aplicaciones, sin solicitudes de IA."""
import json
from types import SimpleNamespace

import pytest

from src.ai.contexto import serializar_contexto
from src.ai.huellas import calcular_huella
from src.frontend.controladores.operaciones_matrices.contexto_modelos import (
    capturar_modelo, obtener_contexto_modelo, obtener_senales_modelo,
)
from src.frontend.controladores.operaciones_matrices.controlador_aplicacion_transformacion import ControladorAplicacionTransformacion


def _vista():
    vista = SimpleNamespace(herramienta_modelo="transformaciones", filas=3, columnas=2,
                            modo_transformacion="aplicacion", tipo_objeto="punto",
                            entradas_coeficientes=[[SimpleNamespace(value=valor) for valor in fila]
                                                   for fila in [["1", "0"], ["0", "1"], ["1", "1"]]],
                            entradas_variables=[SimpleNamespace(value="x"), SimpleNamespace(value="y")],
                            entradas_vector_original=[SimpleNamespace(value="1/3"), SimpleNamespace(value="2/7")],
                            ultimo_resultado=None)
    vista._campos_captura = lambda: [campo for fila in vista.entradas_coeficientes for campo in fila] + vista.entradas_vector_original
    return vista


def test_contexto_conserva_coordenadas_y_omite_propiedades_no_calculadas():
    """Glosa recibe tipo, dimensiones y coordenadas racionales con comprobación real."""
    vista = _vista()
    captura = capturar_modelo(vista)
    vista.ultimo_resultado = json.loads(ControladorAplicacionTransformacion.procesar(json.dumps(captura)))
    vista._huella_resultado = calcular_huella(captura)
    contexto = obtener_contexto_modelo(vista)
    assert contexto.entrada["tipo_objeto"] == "punto"
    assert contexto.entrada["vector_original"] == ["1/3", "2/7"]
    assert contexto.resultado["vector_transformado"] == ["1/3", "2/7", "13/21"]
    assert contexto.resultado["verificacion"] is True
    assert not {"rango", "nulidad", "conclusiones"}.intersection(contexto.resultado)
    assert obtener_senales_modelo(vista).estado == "aplicacion_exito"
    vista.tipo_objeto = "vector"
    assert obtener_contexto_modelo(vista).resultado is None
    assert obtener_senales_modelo(vista).estado == "aplicacion_sin_resultado"


@pytest.mark.parametrize("valor", ["[CONTEXTO]" + "9" * 1000, "<img src=x onerror=alert(1)>", "1/0"])
def test_contexto_invalido_respeta_saneamiento_y_presupuesto(valor):
    """Las coordenadas libres no abren bloques de contexto ni se convierten en resultados."""
    vista = _vista()
    vista.entradas_vector_original[0].value = valor
    contexto = obtener_contexto_modelo(vista)
    assert len(contexto.entrada["vector_original"][0]) <= 32
    assert "[CONTEXTO]" not in contexto.entrada["vector_original"][0]
    assert contexto.resultado is None
    assert len(serializar_contexto(contexto, maximo_caracteres=2000)) <= 2000
    assert obtener_senales_modelo(vista).invalida.etiqueta == "v[1]"
