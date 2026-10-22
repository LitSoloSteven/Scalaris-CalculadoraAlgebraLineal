"""Conversión de bases a grupos de pasos, precisión y saneamiento de contenido."""
import ast
import re
import time
from pathlib import Path

from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.frontend.vistas.sistemas_numericos._pasos_bases import construir_pasos_bases


def test_decimal_genera_grupos_y_pasos_esperados():
    """El decimal 255 genera tres grupos de división con su lectura final."""
    conversor = ConversorBases()
    resultado = conversor.decimal_a_todo("255", "todas")
    pasos, grupos = construir_pasos_bases(resultado)
    assert len(grupos) == 3
    assert [grupo.tipo for grupo in grupos] == ["division", "division", "division"]
    pasos_originales = resultado["pasos"]
    total_esperado = 0
    for k, grupo in enumerate(grupos):
        conversion = pasos_originales[k]
        filas = conversion["filas"]
        esperado_grupo = len(filas) + 1
        assert len(grupo.indices_pasos) == esperado_grupo
        total_esperado += esperado_grupo
        for indice in grupo.indices_pasos[:-1]:
            assert pasos[indice].tipo == "division"
            assert pasos[indice].etiqueta_tipo == "División"
        ultimo_indice = grupo.indices_pasos[-1]
        assert pasos[ultimo_indice].tipo == "lectura"
        assert pasos[ultimo_indice].etiqueta_tipo == "Lectura"
    assert len(pasos) == total_esperado
    assert len(pasos) == 16


def test_hexadecimal_comienza_con_expansion():
    """La expansión hexadecimal precede los dos grupos de división."""
    conversor = ConversorBases()
    resultado = conversor.hexadecimal_a_todo("2A", "todas")
    pasos, grupos = construir_pasos_bases(resultado)
    assert len(grupos) == 3
    expansion = grupos[0]
    assert expansion.tipo == "expansion"
    assert "Expansión Posicional desde Hexadecimal" in expansion.titulo
    terminos = resultado["pasos"][0]["terminos"]
    assert len(terminos) == 2
    assert len(expansion.indices_pasos) == 3
    for indice in expansion.indices_pasos[:-1]:
        assert pasos[indice].tipo == "expansion"
        assert pasos[indice].etiqueta_tipo == "Expansión"
    indice_resultado = expansion.indices_pasos[-1]
    assert pasos[indice_resultado].tipo == "resultado"
    assert pasos[indice_resultado].etiqueta_tipo == "Resultado"
    assert [grupo.tipo for grupo in grupos[1:]] == ["division", "division"]


def test_conversion_negativa_conserva_signo():
    """Los valores negativos mantienen su signo en resultados y explicaciones."""
    conversor = ConversorBases()
    resultado_decimal = conversor.decimal_a_todo("-42", "todas")
    pasos_decimal, grupos_decimal = construir_pasos_bases(resultado_decimal)
    assert len(grupos_decimal) == 3
    assert len(pasos_decimal) > 0
    resultado_hexadecimal = conversor.hexadecimal_a_todo("-2A", "todas")
    pasos_hexadecimal, grupos_hexadecimal = construir_pasos_bases(resultado_hexadecimal)
    assert len(grupos_hexadecimal) == 3
    resultado = pasos_hexadecimal[grupos_hexadecimal[0].indices_pasos[-1]]
    assert resultado.tipo == "resultado"
    assert "-42" in resultado.descripcion
    assert "negativo" in resultado.explicacion


def test_numero_de_doscientos_bits_genera_pasos_rapidamente():
    """Un número de doscientos bits genera pasos en menos de dos segundos."""
    conversor = ConversorBases()
    binario = "1" * 200
    inicio = time.perf_counter()
    resultado = conversor.binario_a_todo(binario, "todas")
    pasos, grupos = construir_pasos_bases(resultado)
    duracion = time.perf_counter() - inicio
    assert duracion < 2.0
    assert len(grupos) == 3
    assert len(pasos) > 200


def test_entrada_cero_genera_pasos():
    """El cero genera dos pasos para cada una de las tres bases de destino."""
    conversor = ConversorBases()
    resultado = conversor.decimal_a_todo("0", "todas")
    pasos, grupos = construir_pasos_bases(resultado)
    assert len(grupos) == 3
    assert len(pasos) == 6


def test_valores_html_escapados():
    """Los valores de los pasos se escapan antes de insertarlos en HTML."""
    paso_malicioso = {
        "tipo": "expansion_posicional", "base_origen": 16,
        "terminos": [{
            "digito": "<script>alert(1)</script>", "valor": 10,
            "potencia": 1, "peso": 16, "producto": 160,
        }],
        "total": "160", "es_negativo": False,
    }
    pasos, grupos = construir_pasos_bases([paso_malicioso])
    assert len(pasos) == 2
    cuerpo_html = str(pasos[0].cuerpo)
    assert "<script>" not in cuerpo_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in cuerpo_html


def test_textos_sin_raya_larga_ni_voseo():
    """Los módulos de conversión mantienen textos sobrios y tuteo."""
    archivos = [
        Path("src/frontend/vistas/sistemas_numericos/_pasos_bases.py"),
        Path("src/frontend/vistas/sistemas_numericos/mixin_procedimiento.py"),
        Path("src/frontend/vistas/sistemas_numericos/mixin_renderizado.py"),
    ]
    patron_voseo = re.compile(
        r"\b(ingresá|añadí|escribí|presioná|pegá|sumá|calculá|mostrá|revisá)\b", re.IGNORECASE,
    )
    for ruta in archivos:
        assert ruta.exists()
        texto = ruta.read_text(encoding="utf-8")
        assert "—" not in texto, f"Raya larga encontrada en {ruta}"
        assert "Oops" not in texto, f"Texto prohibido encontrado en {ruta}"
        arbol = ast.parse(texto, filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                cadena = nodo.value
                coincidencia = patron_voseo.search(cadena)
                assert coincidencia is None, f"Voseo '{coincidencia.group(0)}' en {ruta}: {cadena}"
