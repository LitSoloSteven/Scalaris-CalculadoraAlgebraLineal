"""Retirada del árbol duplicado y consumo exclusivo del modelo matricial canónico."""

import ast
import inspect
import json
from fractions import Fraction

import pytest

from src.backend.excepciones import ErrorDiscrepanciaDimension, ErrorNumeroInvalido
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_numericos.calculadora_romana import ErrorNumeroRomano
from src.frontend.controladores.operaciones_matrices.codificador import CodificadorMatriz
from src.frontend.controladores.utilidades import serializar_matriz
from tests.comun import RAIZ

NOMBRES_RETIRADOS = {"solvers", "models", "utils", "constants", "exceptions"}


def test_arbol_retirado_no_tiene_archivos_ni_consumidores_python():
    """Los paquetes retirados no existen ni son importados por producción o pruebas."""
    for nombre in NOMBRES_RETIRADOS:
        assert not (RAIZ / "src/backend" / nombre).exists()
        assert not (RAIZ / "src/backend" / f"{nombre}.py").exists()
    for carpeta in ("src", "tests"):
        for ruta in (RAIZ / carpeta).rglob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                _comprobar_importacion(nodo)


def _comprobar_importacion(nodo):
    """Detecta importaciones directas y desde el paquete del backend mediante AST."""
    if isinstance(nodo, ast.Import):
        modulos = [nombre.name for nombre in nodo.names]
    elif isinstance(nodo, ast.ImportFrom):
        modulos = [nodo.module or ""]
        if nodo.module == "src.backend":
            assert not ({nombre.name for nombre in nodo.names} & NOMBRES_RETIRADOS)
    else:
        return
    for modulo in modulos:
        partes = modulo.split(".")
        if partes[:2] == ["src", "backend"] and len(partes) > 2:
            assert partes[2] not in NOMBRES_RETIRADOS


@pytest.mark.parametrize("objeto,nombres", [
    (Matriz(1, 1), ("rows", "cols", "data", "get", "set", "clone", "swap_rows", "add_scaled_row")),
    (ErrorDiscrepanciaDimension("suma", (1, 1), (1, 2)), ("operation", "shape_a", "shape_b")),
    (ErrorNumeroInvalido(0, 0, "x", "inválido"), ("row", "col", "raw_value", "reason")),
    (ErrorNumeroRomano("inválido", "SINTAXIS_INVALIDA"), ("code", "invalid_token", "to_dict")),
])
def test_objetos_solo_exponen_atributos_canonicos(objeto, nombres):
    """No se publican métodos ni atributos de compatibilidad en los objetos migrados."""
    assert not any(hasattr(objeto, nombre) for nombre in nombres)


@pytest.mark.parametrize("tipo,nombre", [
    (ResolutorGauss, "variable_names"), (ResolutorGauss, "num_rhs"),
    (ResolutorInversa.resolver, "build_step_latex"),
])
def test_firmas_sin_parametros_alternativos(tipo, nombre):
    """Cada opción tiene una única entrada española explícita."""
    firma = inspect.signature(tipo)
    assert nombre not in firma.parameters
    assert not any(parametro.kind == inspect.Parameter.VAR_KEYWORD for parametro in firma.parameters.values())


def test_serializadores_conservan_fracciones_y_dimensiones_sin_respaldos():
    """Los serializadores consumen la misma Matriz y mantienen las claves de transporte."""
    matriz = Matriz(1, 1, [[Fraction(1, 1001)]])
    esperado = {
                "filas": 1, "columnas": 1, "datos": [["1/1001"]]}
    assert serializar_matriz(matriz) == esperado
    assert json.loads(json.dumps(matriz, cls=CodificadorMatriz)) == esperado


@pytest.mark.parametrize("columnas_independientes", [True, False, 0, -1, 1.5])
def test_bloque_independiente_rechaza_booleanos_y_valores_invalidos(columnas_independientes):
    """La reducción exige una cantidad entera positiva sin interpretar booleanos como uno."""
    with pytest.raises(ValueError, match="numero_terminos_independientes"):
        ResolutorGauss(Matriz(1, 2, [[1, 1]]), numero_terminos_independientes=columnas_independientes)


def test_verificacion_producto_no_confunde_aproximacion_con_identidad(monkeypatch):
    """Una desviación racional menor que epsilon sigue siendo distinta de la identidad exacta."""
    resolutor = ResolutorInversa()
    producto = Matriz(1, 1, [[Fraction(10000000001, 10000000000)]])
    monkeypatch.setattr(resolutor.resolutor_operaciones_matrices, "multiplicar",
                        lambda izquierda, derecha: {"matriz_resultado": producto})
    resultado = resolutor._verificar_producto(Matriz(1, 1, [[1]]), Matriz(1, 1, [[1]]), 1, False)
    assert resultado["coincide"] is False
    assert resultado["se_cumple"] is False
