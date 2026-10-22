"""Límites, delegación de dominio y serialización de captura de sistemas."""
import ast
import asyncio
import json
from pathlib import Path

import pytest

from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.sistemas_lineales.captura import preparar_captura_ecuaciones, preparar_vista_previa
from src.frontend.sugerencias import primera_celda_invalida
from src.frontend.controladores.sistemas_lineales import ControladorGauss
from tests.comun_construccion_vistas import construir_pagina


def test_captura_ecuaciones_serializa_fracciones_y_mensajes():
    """La captura exacta entrega solo datos serializables para cargar la cuadrícula."""
    captura = preparar_captura_ecuaciones(["1/3x + y = 1/2", "x - y = 2"])
    assert captura == {"estado": "EXITO", "mensaje": "", "matriz_a": [["1/3", "1"], ["1", "-1"]], "vector_b": ["1/2", "2"], "variables": ["x", "y"]}
    assert json.loads(json.dumps(captura)) == captura
    assert preparar_captura_ecuaciones(["x inválido"])["mensaje"] == "Línea 1: Falta el signo '=' en la ecuación 'x inválido'."


@pytest.mark.parametrize("captura", [
    {"ecuaciones": ["x = 1/3"]}, {"ecuaciones": ["", " "]},
    {"ecuaciones": ["x = inválido"]}, {"matriz_a": [["1/2", "abc"]], "vector_b": ["3"]},
    {"matriz_a": [], "vector_b": []},
])
def test_vista_previa_es_serializable_en_todos_los_estados(captura):
    """Ni Fraction ni modelos de matriz atraviesan el contrato de vista previa."""
    resultado = preparar_vista_previa(captura)
    assert json.loads(json.dumps(resultado)) == resultado
    assert {"estado", "mensaje", "matriz_latex", "sistema_latex"} <= set(resultado)


def test_marcado_y_numero_original_de_ecuacion():
    """Conserva interrogantes, fracciones y número original de errores de vista previa."""
    matriz = preparar_vista_previa({"matriz_a": [["1/2", "abc"]], "vector_b": ["3"]})
    assert r"\frac{1}{2}" in matriz["matriz_latex"]
    assert r"\color{gray}{?}" in matriz["matriz_latex"]
    assert matriz["sistema_latex"] is None
    ecuaciones = preparar_vista_previa({"ecuaciones": ["x = 1", "", "y = abc"]})
    assert ecuaciones["mensaje"].startswith("Ecuación 3:")


@pytest.mark.parametrize("lineas", [["x = " + "1" * 2049], ["x = 1"] * 11, [" + ".join(f"x{indice}" for indice in range(11)) + " = 1"], ["\n".join(["x = 1"] * 11)], ["\u2028".join(["x = 1"] * 11)], ["\u2029".join(["x = 1"] * 11)]])
def test_resolucion_y_sincronizacion_rechazan_dimensiones_excesivas(lineas):
    """El límite se aplica antes de entregar una captura a la vista."""
    assert preparar_captura_ecuaciones(lineas)["estado"] == "ERROR"
    assert preparar_vista_previa({"ecuaciones": lineas})["estado"] == "error"


@pytest.mark.parametrize("matriz,vector", [(None, [1]), ([[1], None], [1, 2]), ([[1]], None), ([[1]] * 11, [1] * 11)])
def test_controlador_rechaza_estructuras_y_limites_sin_excepcion(matriz, vector):
    """Una estructura malformada produce un error de dominio serializado."""
    respuesta = json.loads(ControladorGauss.procesar_sistema(json.dumps({"matriz_a": matriz, "vector_b": vector})))
    assert respuesta["estado"] == "ERROR"


def test_sugerencias_delegan_la_validacion(monkeypatch):
    """El adaptador de sugerencias usa únicamente la decisión del validador canónico."""
    recibidas = []
    def localizar(celdas):
        """Registra la llamada y entrega un foco sin interpretar números."""
        recibidas.append(celdas)
        return {"etiqueta": "A[2,1]", "foco": (1, 0)}
    monkeypatch.setattr(ValidadorMatriz, "primera_celda_invalida", localizar)
    entradas = [("A[1,1]", "1", (0, 0))]
    resultado = primera_celda_invalida(entradas)
    assert recibidas == [entradas]
    assert resultado.etiqueta == "A[2,1]"
    assert resultado.foco == (1, 0)


def test_vistas_no_importan_ni_invocan_parseo_de_dominio():
    """Inspecciona las dos familias y rechaza parseadores o validadores en sus vistas."""
    raiz = Path(__file__).parents[1] / "src/frontend/vistas"
    prohibidos = {"AnalizadorSistema", "ValidadorMatriz", "Fraction", "parsear_sistema", "parsear_numero_exacto", "matriz_desde_celdas", "analizar_ecuaciones", "latex_matriz_aumentada", "latex_sistema"}
    for familia in ("sistemas_lineales", "operaciones_inversas"):
        for ruta in (raiz / familia).glob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            nombres = {nodo.id for nodo in ast.walk(arbol) if isinstance(nodo, ast.Name)}
            atributos = {nodo.attr for nodo in ast.walk(arbol) if isinstance(nodo, ast.Attribute)}
            assert not (nombres | atributos) & prohibidos, ruta.name


def test_ecuaciones_resolucion_y_sincronizacion_en_vista_real(monkeypatch):
    """Recorre ambos consumidores del análisis con controles NiceGUI montados."""
    async def comprobar(vista, cliente):
        """Resuelve desde Ecuaciones y sincroniza sus datos exactos a la matriz."""
        vista.pestanas_modo.set_value("Ecuaciones")
        vista.num_ecuaciones = 2
        vista.renderizar_ecuaciones()
        for entrada, valor in zip(vista.entradas_ecuaciones, ["1/3x + y = 1/2", "x - y = 2"]):
            entrada.set_value(valor)
        await vista._resolver_nucleo()
        assert vista.ultimo_resultado["estado"] == "SOLUCION_UNICA"
        assert vista.ultimo_resultado["solucion"] == ["15/8", "-1/8"]
        vista.sincronizar_desde_ecuaciones()
        assert vista.cuadricula.obtener_datos_matriz() == ([["1/3", "1"], ["1", "-1"]], ["1/2", "2"])
        vista._actualizar_previa_ecuaciones()
        assert not any("error inesperado" in getattr(elemento, "text", "").casefold() for elemento in cliente.elements.values())
    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))
