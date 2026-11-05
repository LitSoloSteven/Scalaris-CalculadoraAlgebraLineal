"""Unidad angular consistente en motor, análisis, adaptadores, lotes y restauración."""
import json
import math
from dataclasses import asdict, replace

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion, validar_entrada
from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion, validar_exploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion, EntradaResolucionMultiple
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.resolucion_multiple import resolver_candidatos
from src.frontend.controladores.biseccion.controlador import calcular_presentacion, resolver_captura
from src.frontend.controladores.biseccion.exploracion import resolver_exploracion
from src.frontend.controladores.biseccion.presentacion import construir_pasos
from src.frontend.controladores.biseccion.presentacion_criterio import metricas_resumen, texto_resumen
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _captura_grados():
    return {**captura_criterio(), "expresion": "sin(x)-.5", "extremo_izquierdo": 20,
            "extremo_derecho": 40, "unidad_angular": "grados"}


@pytest.mark.parametrize("criterio", [CriterioParada("relativo", 1), CriterioParada("ancho", .01),
    CriterioParada("decimales", 4), CriterioParada("residuo", .01), CriterioParada("iteraciones", 3)])
def test_cinco_criterios_preservan_unidad_y_traza(criterio):
    """La unidad afecta la función, mientras cada criterio mantiene su contrato independiente."""
    entrada = EntradaBiseccion("sin(x)-.5", 20, 40, 4, criterio=criterio, unidad_angular="grados")
    resultado = biseccion(entrada)
    respuesta = resolver_captura({**_captura_grados(), "criterio": asdict(criterio)})
    assert respuesta["iteraciones"] == asdict(resultado)["iteraciones"]
    assert resultado.unidad_angular == respuesta["unidad_angular"] == "grados"
    assert resultado.criterio_solicitado == criterio and resultado.aproximacion is not None
    for fila in resultado.iteraciones:
        assert fila.f_c == math.sin(math.radians(fila.c)) - .5
    assert respuesta["entrada"]["unidad_angular"] == "grados"
    json.dumps(respuesta, allow_nan=False)


def test_grados_en_grafica_resultado_copia_y_pasos():
    """Las dos gráficas usan idénticas muestras y las salidas identifican su unidad matemática."""
    respuesta = calcular_presentacion(_captura_grados())
    previa = preparar_vista_previa({"expresion": "sin(x)-.5", "x_min": 20, "x_max": 40, "unidad_angular": "grados"})
    assert respuesta["muestra"] == previa["muestra"]
    assert previa["muestra"]["x"][200] == 30
    assert previa["muestra"]["y"][200] == pytest.approx(0, abs=1e-15)
    assert respuesta["aproximacion"] == pytest.approx(30, abs=1e-4)
    assert ("Unidad trigonométrica", "grados") in metricas_resumen(respuesta)
    assert "Unidad trigonométrica: grados" in texto_resumen(respuesta, 4)
    pasos, _ = construir_pasos(respuesta)
    assert "Unidad trigonométrica: grados" in pasos[0].explicacion
    json.dumps((respuesta, previa), allow_nan=False)


def test_explorar_y_resolver_tres_candidatos_en_grados():
    """Sin encuentra candidatos próximos a 180, 360 y 540, con lotes iguales al motor individual."""
    exploracion = explorar_intervalos(EntradaExploracion("sin(x)", 1, 550, 7, unidad_angular="grados"))
    candidatos = tuple(CandidatoResolucion(str(indice), candidato) for indice, candidato in enumerate(exploracion.candidatos)
                       if candidato.tipo in ("cruce", "cero_evaluado"))
    entrada = EntradaResolucionMultiple(EntradaBiseccion("sin(x)", 1, 550, 4, unidad_angular="grados"),
                                        candidatos, unidad_angular="grados")
    lote = resolver_candidatos(entrada)
    assert exploracion.unidad_angular == lote.unidad_angular == "grados" and len(candidatos) == 3
    assert [registro.resultado.aproximacion for registro in lote.resultados] == pytest.approx([180, 360, 540], abs=1e-4)
    assert all(registro.resultado == biseccion(registro.entrada) for registro in lote.resultados)
    respuesta = resolver_exploracion({"expresion": "sin(x)", "x_min": 1, "x_max": 550, "paso": 7, "unidad_angular": "grados"})
    assert respuesta["candidatos"] == asdict(exploracion)["candidatos"]
    serializada = resolver_lote({"configuracion": {**_captura_grados(), "expresion": "sin(x)"},
                               "candidatos": [asdict(candidato) for candidato in candidatos]})
    assert serializada["estado"] == "LOTE_COMPLETADO" and serializada["unidad_angular"] == "grados"
    assert all(registro["respuesta"]["unidad_angular"] == "grados" for registro in serializada["resultados"])
    json.dumps((respuesta, serializada), allow_nan=False)


def test_lote_con_unidades_contradictorias_no_evalua(monkeypatch):
    """Una discrepancia explícita se rechaza antes de compilar o consumir presupuesto de evaluaciones."""
    from importlib import import_module
    modulo = import_module("src.backend.resolutores.raices.resolucion_multiple")
    exploracion = explorar_intervalos(EntradaExploracion("sin(x)", 170, 190, 3, unidad_angular="grados"))
    candidato = CandidatoResolucion("primero", exploracion.candidatos[0])
    entrada = EntradaResolucionMultiple(EntradaBiseccion("sin(x)", 170, 190, 4, unidad_angular="grados"),
                                        (candidato,), unidad_angular="radianes")
    llamadas = []
    monkeypatch.setattr(modulo, "compilar", lambda *argumentos, **opciones: llamadas.append(argumentos))
    with pytest.raises(ValueError, match="coincidir"):
        resolver_candidatos(entrada)
    assert llamadas == []


@pytest.mark.parametrize("unidad", [None, True, 3, {}, [], "deg", "GRADOS", ""])
def test_contratos_y_adaptadores_rechazan_unidades_ajenas(unidad):
    """Motor, exploración y previa no silencian unidades inválidas con radianes por defecto."""
    entrada = EntradaBiseccion("x", -1, 1, 4, unidad_angular=unidad)
    with pytest.raises(ValueError):
        validar_entrada(asdict(entrada))
    with pytest.raises(ValueError):
        validar_exploracion(EntradaExploracion("x", -1, 1, .1, unidad_angular=unidad))
    assert biseccion(entrada).codigo_diagnostico == "ENTRADA_INVALIDA"
    respuesta = resolver_captura({**_captura_grados(), "unidad_angular": unidad})
    exploracion = resolver_exploracion({"expresion": "x", "x_min": -1, "x_max": 1, "paso": .1, "unidad_angular": unidad})
    previa = preparar_vista_previa({"expresion": "x", "x_min": -1, "x_max": 1, "unidad_angular": unidad})
    assert respuesta["estado"] == exploracion["estado"] == previa["estado"] == "ERROR"
    json.dumps((respuesta, exploracion, previa), allow_nan=False)


def test_sugerencia_y_fallos_conservan_unidad_de_evaluacion():
    """La sugerencia sqrt se verifica en grados y los fallos de dominio conservan unidad y contexto."""
    entrada = EntradaBiseccion("sqrt(x)+log(cos(x))", -1, 9, 4, unidad_angular="grados")
    resultado = biseccion(entrada)
    assert resultado.unidad_angular == "grados" and resultado.sugerencias[0]["intervalo"] == (0, 9)
    assert resultado.contexto_fallo["x_fallo"] == -1
    assert biseccion(replace(entrada, unidad_angular="radianes")).sugerencias == ()
    for expresion in ("sin()", "1/(x-30)", "asin(2)"):
        respuesta = resolver_captura({**_captura_grados(), "expresion": expresion})
        assert respuesta["estado"] == "ERROR" and respuesta["unidad_angular"] == "grados"
        json.dumps(respuesta, allow_nan=False)


def test_historial_contexto_restauracion_antigua_y_cargas_parciales(monkeypatch):
    """La captura completa conserva unidad, mientras registros antiguos usan radianes y ejemplos retienen preferencia."""
    async def comprobar(vista):
        """Resuelve, restaura y edita controles reales sin convertir valores desde la vista."""
        vista.cargar_captura(_captura_grados())
        await vista.resolver()
        guardada = vista.historial[0]["captura"]
        assert guardada["unidad_angular"] == "grados"
        contexto = vista.obtener_contexto_ia()
        assert contexto.entrada["unidad_angular"] == contexto.resultado["unidad_angular"] == "grados"
        vista.unidad_angular.set_value("radianes")
        assert vista.ultimo_resultado is None and vista.obtener_contexto_ia().resultado is None
        vista.cargar_captura(guardada)
        assert vista.unidad_angular.value == "grados" and vista.ultimo_resultado is None
        vista.cargar_captura({"extremo_izquierdo": 10, "extremo_derecho": 50})
        vista.cargar_captura({"expresion": "2x-3"})
        vista.cargar_captura({"criterio": {"tipo": "ancho", "parametro": ".01"}})
        assert vista.unidad_angular.value == "grados"
        vista.cargar_captura(captura_criterio())
        assert vista.unidad_angular.value == "radianes"
        assert vista.unidad_angular._props["label"] == "Unidad trigonométrica"
    ejecutar_escenario(monkeypatch, comprobar)
