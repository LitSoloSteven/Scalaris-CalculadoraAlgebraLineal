"""Autoridad del criterio activo entre captura, copia, procedimiento y contexto."""
import json

import pytest

from src.frontend.controladores.regla_falsa.configuracion_ampliada import preparar_configuracion
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion
from src.frontend.controladores.regla_falsa.presentacion_ampliada import datos_criterio
from src.frontend.controladores.regla_falsa.salidas_regla_falsa import datos_copia_configurada
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario, textos_resultado


@pytest.mark.parametrize("tipo,parametro", [("residuo", "1e-6"), ("ancho", ".7"), ("decimales", "0"),
                                             ("relativo", "1"), ("iteraciones", "1")])
def test_canal_ampliado_conserva_sobre_y_metricas_del_backend(tipo, parametro):
    """Contrasta el contrato separado y las métricas copiadas para cada criterio."""
    captura = captura_regla_falsa(criterio={"tipo": tipo, "parametro": parametro}, tolerancia="inactiva")
    configuracion = preparar_configuracion(captura)
    datos = calcular_presentacion(captura)
    assert datos["resultado"]["estado"] == "EXITO"
    assert "criterio" not in datos["resultado"]
    assert datos["ampliado"]["criterio"]["tipo"] == tipo
    assert configuracion.entrada.tolerancia == (1e-6 if tipo != "residuo" else float(parametro))
    json.dumps(datos, allow_nan=False)
    copia = next(iter(datos_copia_configurada(datos["resultado"], datos["ampliado"], 4, True).values()))
    for etiqueta, valor in datos_criterio(datos["ampliado"]):
        assert f"{etiqueta}: {valor}" in copia
    assert "Tolerancia de residuo:" not in copia


@pytest.mark.parametrize("tipo,parametro", [("ancho", ".7"), ("decimales", "0"),
                                             ("relativo", "1"), ("iteraciones", "1")])
def test_vista_usa_condicion_real_sin_validar_tolerancia_inactiva(monkeypatch, tipo, parametro):
    """La condición activa coincide en resumen, pasos, contexto y restauración."""
    async def comprobar(vista):
        """Ejecuta controles reales con tolerancia inactiva inválida y cambia el formato visual."""
        vista.cargar_captura(captura_regla_falsa(criterio={"tipo": tipo, "parametro": parametro}, tolerancia="nan"))
        assert vista.estados_entrada.validar()
        await vista.resolver()
        resultado = vista.ultimo_resultado
        ampliado = vista.ultimo_ampliado
        assert resultado["estado"] == "EXITO"
        assert vista.tolerancia.value == "nan" and vista.tolerancia.error is None
        contexto = vista.obtener_contexto_ia().estado.resultado
        assert contexto["configuracion_aplicada"]["criterio"] == ampliado["criterio"]
        pasos = vista.reproductor_pasos.pasos
        assert "tolerancia" not in pasos[0].descripcion
        assert datos_criterio(ampliado)[1][1] in pasos[0].descripcion
        assert all(ampliado["criterio"] == paso.meta_explicar["detalle"]["criterio_aplicado"] for paso in pasos)
        vista.reproductor_pasos.ir_a(1)
        assert vista._foco_procedimiento.captura.detalle["iteracion"] is resultado["iteraciones"][0]
        assert datos_criterio(ampliado)[1][1] in vista._foco_procedimiento.captura.detalle["explicacion"]
        assert "Criterio aplicado" in textos_resultado(vista)
        if tipo == "iteraciones":
            assert "Aproximación provisional" in textos_resultado(vista)
            assert ampliado["cumplimiento"] == "CONTEO_COMPLETADO"
        vista.formato.set_value(8)
        assert vista.ultimo_resultado is resultado
        captura = dict(vista.capturar())
        vista.cargar_captura(captura_regla_falsa())
        assert vista.criterio.value == "residuo"
        vista.cargar_captura(captura)
        assert vista.criterio.value == tipo
    ejecutar_escenario(monkeypatch, comprobar)


def test_parametro_visible_invalido_tiene_error_y_relativo_inicial_no_aplica(monkeypatch):
    """Orienta sobre el parámetro visible y distingue porcentaje ausente en la primera fila."""
    async def comprobar(vista):
        """Corrige un porcentaje inválido y comprueba el cierre con una sola iteración."""
        vista.cargar_captura(captura_regla_falsa(criterio={"tipo": "relativo", "parametro": "nan"}))
        assert not vista.estados_entrada.validar()
        assert vista.parametros_criterio["relativo"].error
        vista.parametros_criterio["relativo"].set_value("1")
        vista.limite.set_value("1")
        await vista.resolver()
        assert vista.ultimo_ampliado["metrica_final"] is None
        assert vista.ultimo_ampliado["cumplimiento"] == "NO_APLICA"
        assert any("No aplica" in texto for texto in textos_resultado(vista))
    ejecutar_escenario(monkeypatch, comprobar)
