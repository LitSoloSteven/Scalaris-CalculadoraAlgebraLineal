"""Contratos únicos, dominio delegado y entradas desfavorables de bases y romanos."""

import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.backend.resolutores.sistemas_numericos import calculadora_romana as romanos
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.backend.resolutores.sistemas_numericos.pasos_didacticos import (
    calcular_subtotal_expansion, desglosar_sumas_sucesivas,
)
from src.backend.utilidades.reglas_dominio import BASES_NUMERICAS, validar_entrada_base
from src.frontend.sugerencias import Senales, generar_candidatas
from src.frontend.vistas.sistemas_numericos._pasos_bases import construir_pasos_bases
from src.frontend.vistas.sistemas_numericos._plantillas_numericas import renderizar_plantilla
from src.frontend.vistas.sistemas_numericos.mixin_contexto_romanos import _primera_entrada_invalida
from src.frontend.vistas.sistemas_numericos.vista_sistemas_numericos import VistaSistemasNumericos
from src.frontend.vistas.sistemas_numericos.vista_calculadora_romana import VistaCalculadoraRomana
from src.frontend.vistas.sistemas_numericos.pasos_romanos import construir_pasos_romanos


def test_codigos_romanos_y_error_sin_alias():
    """Los ocho códigos y las cuatro claves del error usan un único esquema español."""
    assert (romanos.ERROR_TIPO_INVALIDO, romanos.ERROR_ENTRADA_VACIA,
            romanos.ERROR_SINTAXIS_INVALIDA, romanos.ERROR_NO_CANONICO,
            romanos.ERROR_FUERA_DE_RANGO, romanos.ERROR_CERO_NO_REPRESENTABLE,
            romanos.ERROR_NEGATIVO_NO_REPRESENTABLE, romanos.ERROR_OPERANDO_NO_UN_DIGITO) == (
        "TIPO_INVALIDO", "ENTRADA_VACIA", "SINTAXIS_INVALIDA", "NO_CANONICO",
        "FUERA_DE_RANGO", "CERO_NO_REPRESENTABLE", "NEGATIVO_NO_REPRESENTABLE", "OPERANDO_NO_UN_DIGITO",
    )
    error = romanos.ErrorNumeroRomano("mensaje", "SINTAXIS_INVALIDA", "IIII")
    assert error.a_diccionario() == {
        "estado": "ERROR", "codigo_error": "SINTAXIS_INVALIDA", "mensaje": "mensaje", "token": "IIII",
    }
    assert all(not hasattr(error, nombre) for nombre in ("code", "invalid_token", "to_dict"))


@pytest.mark.parametrize("base,entrada,decimal", [
    ("decimal", "12345", "12345"), ("decimal", "-12345", "-12345"),
    ("decimal", "0", "0"), ("hexadecimal", "0x1A2B3C", "1715004"),
    ("binario", "1" * 50, str(2**50 - 1)), ("binario", "+0b1_010", "10"),
    ("octal", "-0o377", "-255"), ("hexadecimal", " +0xF_F ", "255"),
])
def test_entradas_desfavorables_comparten_validacion_y_conversion(base, entrada, decimal):
    """La orientación y conversión aceptan signos, prefijos y números largos exactos."""
    assert validar_entrada_base(entrada, BASES_NUMERICAS[base]) == (True, "Entrada válida.")
    resultado = getattr(ConversorBases(), f"{base}_a_todo")(entrada)
    assert resultado["estado"] == "EXITO"
    assert resultado["decimal"] == decimal
    assert "error" not in resultado and "error_code" not in resultado
    original = deepcopy(resultado)
    pasos, grupos = construir_pasos_bases(resultado)
    assert resultado == original
    assert pasos and grupos
    assert all("style=" not in str(paso.cuerpo) for paso in pasos)
    if base == "binario":
        assert len(resultado["pasos"][0]["terminos"]) == len(entrada.replace("+0b", "").replace("_", ""))


@pytest.mark.parametrize("base,entrada", [
    ("decimal", ""), ("binario", "102"), ("octal", "89"), ("hexadecimal", "0x"),
    ("hexadecimal", "<script>"), ("hexadecimal", "0x0xFF"), ("binario", "--1"),
    ("decimal", "--1"), ("decimal", "+-1"), ("decimal", "-+1"), ("decimal", "++1"),
    ("decimal", "-\t-1"), ("decimal", "+\t-1"), ("decimal", "-\n-1"), ("decimal", "+\t+1"),
])
def test_errores_de_bases_comparten_mensaje_sin_clave_alternativa(base, entrada):
    """Un rechazo entrega exactamente el mensaje del único validador de dominio."""
    valido, mensaje = validar_entrada_base(entrada, BASES_NUMERICAS[base])
    assert not valido
    assert getattr(ConversorBases(), f"{base}_a_todo")(entrada) == {"estado": "ERROR", "mensaje": mensaje}


@pytest.mark.parametrize("entrada", [0, -1, 4000, 12345])
def test_romanos_rechazan_cero_negativo_y_enteros_fuera_del_rango(entrada):
    """La conversión mantiene el rango tradicional sin reinterpretar números inválidos."""
    with pytest.raises(romanos.ErrorNumeroRomano) as captura:
        romanos.entero_a_romano(entrada)
    assert captura.value.codigo == "FUERA_DE_RANGO"
    assert captura.value.token_invalido == str(entrada)


@pytest.mark.parametrize("entrada", ["12345", "-I", "0", "MMMM", "IIII", "<img src=x onerror=alert(1)>"])
def test_orientacion_romana_usa_conversion_canonica(entrada):
    """Las entradas desfavorables son rechazadas por backend y orientación de la vista."""
    with pytest.raises(romanos.ErrorNumeroRomano):
        romanos.romano_a_entero(entrada)
    assert _primera_entrada_invalida(entrada, "I").etiqueta == "Operando A"
    assert _primera_entrada_invalida("I", entrada).etiqueta == "Operando B"
    assert _primera_entrada_invalida(" xiv ", "ix") is None


@pytest.mark.parametrize("codigo,bandera,identificador", [
    ("CERO_NO_REPRESENTABLE", "error_resta_cero", "romanos.error.cero"),
    ("NEGATIVO_NO_REPRESENTABLE", "error_resta_negativa", "romanos.error.negativo"),
    ("SINTAXIS_INVALIDA", "error_sintaxis", "romanos.error.sintaxis"),
    ("NO_CANONICO", "error_sintaxis", "romanos.error.sintaxis"),
    ("ENTRADA_VACIA", "error_sintaxis", "romanos.error.sintaxis"),
])
def test_codigo_romano_llega_a_sugerencia_real(codigo, bandera, identificador):
    """El clasificador alimenta el catálogo real sin depender del texto del error."""
    error = romanos.ErrorNumeroRomano("mensaje sin pistas", codigo)
    assert VistaCalculadoraRomana.clasificar_error_romano(error) == bandera
    sugerencias = generar_candidatas(Senales(herramienta="romanos", estado="error", banderas=frozenset({bandera})))
    assert identificador in {sugerencia.identificador for sugerencia in sugerencias}


def test_plantillas_escapan_todos_los_campos_romanos():
    """Cada cuerpo de operación escapa texto de operandos/resultados sin estilos en línea."""
    malicioso = '<img src=x onerror="alert(1)">'
    resultado = romanos.CalculadoraRomana.multiplicar_un_digito("III", "IV")
    resultado = replace(resultado, operando_a_romano=malicioso, operando_b_romano=malicioso,
                        resultado_romano=malicioso)
    for operacion in ("suma", "resta", "multiplicacion"):
        pasos, _ = construir_pasos_romanos(resultado, operacion)
        assert all("<img" not in str(paso.cuerpo) for paso in pasos)
        assert all("style=" not in str(paso.cuerpo) for paso in pasos)
        assert any("&lt;img" in str(paso.cuerpo) for paso in pasos)


def test_plantillas_escapan_tambien_etiquetas_y_valores_numericos():
    """Una plantilla jamás interpreta valores como etiquetas o atributos HTML."""
    malicioso = '<script>"&</script>'
    contenido = renderizar_plantilla("operacion", {
        "decimal_a": malicioso, "decimal_b": malicioso, "simbolo": malicioso, "resultado": malicioso,
    })
    assert contenido.count("&lt;script&gt;&quot;&amp;&lt;/script&gt;") == 4
    assert "<script>" not in contenido


def test_calculos_didacticos_exactos_sin_mutar_entrada():
    """Subtotal, sumas y construcción canónica residen en backend y conservan magnitudes."""
    terminos = [{"producto": 240}, {"producto": 15}]
    assert calcular_subtotal_expansion(terminos, 0) == 240
    assert calcular_subtotal_expansion(terminos, 1) == 255
    assert terminos == [{"producto": 240}, {"producto": 15}]
    assert desglosar_sumas_sucesivas(3, 4) == [
        {"indice": 1, "acumulado": 3}, {"indice": 2, "acumulado": 6},
        {"indice": 3, "acumulado": 9}, {"indice": 4, "acumulado": 12},
    ]
    assert "".join(paso["simbolo"] for paso in romanos.desglosar_pasos_canonicos(3999)) == "MMMCMXCIX"


def test_vistas_sin_regex_de_dominio_y_renderizadores_sin_html_largo():
    """Las vistas delegan dominio y los reproductores cargan plantillas separadas."""
    carpeta = Path("src/frontend/vistas/sistemas_numericos")
    for nombre in ("vista_sistemas_numericos.py", "mixin_interaccion.py", "mixin_contexto_romanos.py"):
        arbol = ast.parse((carpeta / nombre).read_text(encoding="utf-8"))
        assert not any(isinstance(nodo, ast.Import) and any(alias.name == "re" for alias in nodo.names)
                       for nodo in ast.walk(arbol))
    assert not hasattr(VistaSistemasNumericos(), "regex_bases")
    for nombre in ("pasos_romanos.py", "_pasos_bases.py"):
        texto = (carpeta / nombre).read_text(encoding="utf-8")
        assert "<table" not in texto and "<div" not in texto and "<span" not in texto


@pytest.mark.anyio
async def test_entrada_invalida_actualiza_mensaje_y_desincroniza_resultado():
    """Un error de dominio orienta y marca el resultado previo sin atenuarlo."""
    vista = VistaSistemasNumericos()
    vista.base_activa = "binario"
    vista.entrada_valor = SimpleNamespace(value="102")
    vista.etiqueta_error = SimpleNamespace(text="")
    vista.tiene_resultado = True
    tarjeta = SimpleNamespace(classes=Mock(), style=Mock())
    vista.tarjetas = {"decimal": tarjeta}
    vista.etiqueta_estado = SimpleNamespace(text="")
    await vista._al_cambiar_entrada(None)
    assert vista.etiqueta_error.text == validar_entrada_base("102", 2)[1]
    tarjeta.classes.assert_called_once_with(add="sesion-obsoleta")
    tarjeta.style.assert_not_called()
    assert "Resultado anterior" in vista.etiqueta_estado.text


def test_operando_romano_vacio_limpia_resultado_y_muestra_error_del_backend():
    """La operación incompleta reemplaza el estado anterior con el error de dominio."""
    vista = VistaCalculadoraRomana()
    vista.entrada_a = SimpleNamespace(value="")
    vista.entrada_b = SimpleNamespace(value="I")
    vista.pestanas_operacion = SimpleNamespace(value="suma")
    vista.etiqueta_error = SimpleNamespace(text="")
    vista.contenedor_resultado = SimpleNamespace(clear=lambda: None)
    vista.ultimo_resultado = romanos.CalculadoraRomana.sumar("I", "I")
    vista.operar_romanos()
    assert vista.ultimo_resultado is None
    assert vista.ultimo_error.codigo == "ENTRADA_VACIA"
    assert vista.etiqueta_error.text == str(vista.ultimo_error)


@pytest.mark.anyio
async def test_conversion_vacia_orienta_con_mensaje_backend(monkeypatch):
    """El botón usa también el mensaje del validador único para la entrada vacía."""
    from src.frontend.vistas.sistemas_numericos import mixin_interaccion
    avisos = []
    monkeypatch.setattr(mixin_interaccion.ui, "notify", lambda mensaje, **opciones: avisos.append(mensaje))
    vista = VistaSistemasNumericos()
    vista.entrada_valor = SimpleNamespace(value="")
    vista.etiqueta_error = SimpleNamespace(text="")
    await vista._convertir_boton()
    mensaje = validar_entrada_base("", 10)[1]
    assert vista.etiqueta_error.text == mensaje
    assert avisos == [mensaje]
