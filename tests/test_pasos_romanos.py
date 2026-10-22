"""Pruebas del reproductor interactivo de pasos para la Calculadora de Números Romanos."""

import ast
import re
from pathlib import Path

from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    CalculadoraRomana,
    ErrorNumeroRomano,
    desglosar_pasos_canonicos,
)
from src.frontend.vistas.sistemas_numericos.pasos_romanos import (
    construir_pasos_romanos,
)
from src.frontend.vistas.sistemas_numericos.vista_calculadora_romana import (
    VistaCalculadoraRomana,
)


def test_suma_xiv_mas_ix():
    """Suma XIV + IX genera 3 grupos: decodificación, operación y construcción canónica."""
    res = CalculadoraRomana.sumar("XIV", "IX")
    pasos, grupos = construir_pasos_romanos(res, "suma")

    assert len(grupos) == 3
    assert grupos[0].titulo == "Decodificación de operandos a decimal"
    assert grupos[0].tipo == "decodificacion"
    assert len(grupos[0].indices_pasos) == 2

    assert pasos[0].tipo == "decodificacion"
    assert "XIV = 14" in pasos[0].descripcion

    assert pasos[1].tipo == "decodificacion"
    assert "IX = 9" in pasos[1].descripcion

    # Grupo 1: Operación suma (1 paso)
    assert grupos[1].tipo == "operacion"
    assert len(grupos[1].indices_pasos) == 1
    indice_operacion = grupos[1].indices_pasos[0]
    assert pasos[indice_operacion].tipo == "operacion"
    assert "14 + 9 = 23" in pasos[indice_operacion].descripcion

    # Grupo 2: Construcción canónica (23 = XXIII: 10, 10, 1, 1, 1 -> 5 pasos + 1 resultado)
    assert grupos[2].tipo == "construccion"
    assert len(grupos[2].indices_pasos) == 6
    for indice in grupos[2].indices_pasos[:-1]:
        assert pasos[indice].tipo == "construccion"
    paso_res = pasos[grupos[2].indices_pasos[-1]]
    assert paso_res.tipo == "resultado"
    assert "XXIII" in paso_res.descripcion
    assert "23" in paso_res.descripcion

    # Metadatos Glosa
    for i, p in enumerate(pasos):
        assert p.meta_explicar["indice"] == i + 1
        assert p.meta_explicar["total"] == len(pasos)


def test_resta_xx_menos_viii():
    """Resta XX − VIII incluye validación A > B, resta y construcción canónica de 12 (XII)."""
    res = CalculadoraRomana.restar("XX", "VIII")
    pasos, grupos = construir_pasos_romanos(res, "resta")

    assert len(grupos) == 3
    # Grupo 0: Decodificación
    assert len(grupos[0].indices_pasos) == 2

    # Grupo 1: Operación resta (validación + resta)
    assert grupos[1].tipo == "operacion"
    assert len(grupos[1].indices_pasos) == 2
    indice_valor, indice_operacion = grupos[1].indices_pasos
    assert pasos[indice_valor].tipo == "validacion"
    assert "20 > 8" in pasos[indice_valor].descripcion
    assert pasos[indice_operacion].tipo == "operacion"
    assert "20 − 8 = 12" in pasos[indice_operacion].descripcion

    # Grupo 2: Construcción (12 = XII: 10, 1, 1 -> 3 pasos + 1 resultado = 4)
    assert grupos[2].tipo == "construccion"
    assert len(grupos[2].indices_pasos) == 4
    paso_final = pasos[grupos[2].indices_pasos[-1]]
    assert paso_final.tipo == "resultado"
    assert "XII" in paso_final.descripcion


def test_multiplicacion_iii_por_iv_iteraciones_exactas():
    """Multiplicación III × IV genera exactamente 4 pasos de iteración acumulada."""
    res = CalculadoraRomana.multiplicar_un_digito("III", "IV")
    pasos, grupos = construir_pasos_romanos(res, "multiplicacion")

    assert len(grupos) == 3
    grp_mult = grupos[1]
    assert grp_mult.tipo == "multiplicacion"
    assert grp_mult.titulo == "Multiplicación mediante sumas sucesivas"

    pasos_mult = [pasos[indice] for indice in grp_mult.indices_pasos]
    # 1 definición + 4 iteraciones + 1 producto final = 6 pasos
    assert len(pasos_mult) == 6

    # Paso de definición
    assert pasos_mult[0].tipo == "definicion"
    assert "sumar 3, 4 veces" in pasos_mult[0].descripcion

    # 4 iteraciones exactas
    iteraciones = [p for p in pasos_mult if p.tipo == "iteracion"]
    assert len(iteraciones) == 4
    assert iteraciones[0].descripcion == "Paso 1: acumulado = 3"
    assert iteraciones[1].descripcion == "Paso 2: acumulado = 6"
    assert iteraciones[2].descripcion == "Paso 3: acumulado = 9"
    assert iteraciones[3].descripcion == "Paso 4: acumulado = 12"

    # Paso de producto
    assert pasos_mult[-1].tipo == "producto"
    assert "3 × 4 = 12" in pasos_mult[-1].descripcion


def test_desglose_canonico_3999():
    """3999 (MMMCMXCIX) se desglosa vorazmente en exactamente 6 sustracciones canónicas."""
    pasos_can = desglosar_pasos_canonicos(3999)
    assert len(pasos_can) == 6

    glifos = [p["simbolo"] for p in pasos_can]
    assert glifos == ["M", "M", "M", "CM", "XC", "IX"]
    assert "".join(glifos) == "MMMCMXCIX"
    assert pasos_can[-1]["restante"] == 0


def test_clasificacion_errores_no_genera_pasos():
    """Clasificación de errores conserva compatibilidad y entradas inválidas no generan pasos."""
    # Clasificación de errores estructurados
    error_cero = ErrorNumeroRomano("No existe el número cero en el sistema romano.", codigo="CERO_NO_REPRESENTABLE")
    assert VistaCalculadoraRomana.clasificar_error_romano(error_cero) == "error_resta_cero"

    error_negativo = ErrorNumeroRomano("No existen los números negativos en el sistema romano.", codigo="NEGATIVO_NO_REPRESENTABLE")
    assert VistaCalculadoraRomana.clasificar_error_romano(error_negativo) == "error_resta_negativa"

    error_sintaxis = ErrorNumeroRomano("No es sintaxis válida", codigo="SINTAXIS_INVALIDA")
    assert VistaCalculadoraRomana.clasificar_error_romano(error_sintaxis) == "error_sintaxis"

    # Errores por fallback de mensaje
    mensaje_error_cero = ValueError("no existe el número cero")
    assert VistaCalculadoraRomana.clasificar_error_romano(mensaje_error_cero) == "error_resta_cero"

    # Resultado nulo o fallido no produce pasos
    pasos, grupos = construir_pasos_romanos(None, "suma")
    assert pasos == ()
    assert grupos == ()


def test_sin_raya_larga_ni_voseo_en_textos_romanos():
    """Garantiza puntuación sobria y tuteo en los módulos de números romanos."""
    archivos = [
        Path("src/frontend/vistas/sistemas_numericos/pasos_romanos.py"),
        Path("src/frontend/vistas/sistemas_numericos/mixin_resultado_romano.py"),
        Path("src/frontend/vistas/sistemas_numericos/vista_calculadora_romana.py"),
    ]

    patrones_voseo = [
        re.compile(r"\b(mirá|hacé|tenés|ingresá|probá|andá|decí|podés)\b", re.IGNORECASE),
    ]

    for archivo in archivos:
        contenido = archivo.read_text(encoding="utf-8")
        assert "—" not in contenido, f"Encontrado guión largo '—' en {archivo}"

        for patron in patrones_voseo:
            coincidencias = patron.findall(contenido)
            assert not coincidencias, f"Encontrado voseo {coincidencias} en {archivo}"

    res_mult = CalculadoraRomana.multiplicar_un_digito("III", "IV")
    pasos, grupos = construir_pasos_romanos(res_mult, "multiplicacion")
    for p in pasos:
        assert "—" not in p.descripcion
        assert "—" not in p.explicacion
        for patron in patrones_voseo:
            assert not patron.findall(p.descripcion)
            assert not patron.findall(p.explicacion)
