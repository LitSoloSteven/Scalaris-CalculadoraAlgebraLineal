"""Contrato español, aislamiento y recorte del contexto pedagógico de Glosa."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import inspect
import json
from types import SimpleNamespace

import pytest
from nicegui import ui

from src.ai.contexto import (
    CapturaPaso, ContextoIA, EstadoContexto, ReferenciaPaso,
    describir_matriz, serializar_contexto,
)
from src.ai.estrategias_recorte import construir_contexto_minimo
from src.backend.modelos.matriz import Matriz
from src.frontend.componentes.glosa_pie import renderizar_pildora_contexto


def _leer_datos(serializado):
    return json.loads(serializado[len("[CONTEXTO]\n"):-len("\n[/CONTEXTO]")])


def test_constructores_agrupan_datos_sin_alias_ingleses():
    """Las firmas tienen hasta cinco entradas y los datos solo exponen nombres españoles."""
    contexto = ContextoIA()
    referencia = ReferenciaPaso()
    assert all(len(inspect.signature(tipo).parameters) <= 5 for tipo in (
        ContextoIA, EstadoContexto, ReferenciaPaso, CapturaPaso,
    ))
    assert contexto.entrada == {} and not contexto.vacio and contexto.resultado is None
    assert not any(hasattr(contexto, nombre) for nombre in (
        "tool", "view", "label", "input", "result", "focus", "window_note", "stale", "empty",
    ))
    assert not any(hasattr(referencia, nombre) for nombre in (
        "index", "kind", "op", "rows_before", "rows_after", "cols", "detail",
    ))
    assert ContextoIA(entrada=None).entrada == {}


def test_estado_y_capturas_predeterminadas_son_independientes():
    """Mutar un contexto o una captura no afecta los valores por defecto de otro."""
    primero, segundo = ContextoIA(), ContextoIA()
    primero.resultado = {"estado": "EXITO"}
    primero.desactualizado = True
    primero.foco = ReferenciaPaso()
    primero.foco.captura.filas_antes["1"] = ["2"]
    assert segundo.resultado is None and not segundo.desactualizado
    assert ReferenciaPaso().captura.filas_antes == {}
    assert primero.estado.resultado is primero.resultado
    assert primero.estado.foco is primero.foco


def test_referencia_inmutable_permite_reemplazar_captura():
    """La captura se sustituye con dataclasses sin alterar la referencia original."""
    referencia = ReferenciaPaso(1, 2, "pivote", "Fila 1", CapturaPaso(columnas=(1, 12)))
    sustituta = replace(referencia, captura=replace(referencia.captura, columnas=None))
    assert referencia.captura.columnas == (1, 12)
    assert sustituta.captura.columnas is None
    assert sustituta.indice == referencia.indice and sustituta.operacion == referencia.operacion
    with pytest.raises(FrozenInstanceError):
        referencia.indice = 3


def test_serializacion_conserva_fracciones_dimensiones_y_foco():
    """El esquema español conserva todos los datos de un ejercicio sin recorte."""
    captura = CapturaPaso({"1": ["1/3"]}, {"1": ["2/3"]}, (1, 1), {"ejemplo": "Fila 1"})
    contexto = ContextoIA(
        "matrices", "Matrices", "Matriz A", {"A": describir_matriz([["1/3"]])},
        EstadoContexto(
            resultado={"matriz": Matriz(1, 1, [[Fraction(1, 3)]]), "fraccion": Fraction(2, 3)},
            foco=ReferenciaPaso(1, 2, "normalizacion", "Dividir", captura),
            desactualizado=True,
        ),
    )
    datos = _leer_datos(serializar_contexto(contexto))
    assert set(datos) == {"version", "herramienta", "vista", "entrada", "resultado", "foco", "metadatos"}
    assert datos["entrada"]["A"] == {"filas": 1, "columnas": 1, "datos": [["1/3"]]}
    assert datos["resultado"] == {"matriz": "[      1/3 ]", "fraccion": "2/3"}
    assert datos["foco"] == {
        "indice": 1, "total": 2, "tipo": "normalizacion", "operacion": "Dividir",
        "filas_antes": {"1": ["1/3"]}, "filas_despues": {"1": ["2/3"]},
        "columnas": [1, 1], "detalle": {"ejemplo": "Fila 1"},
    }
    assert datos["metadatos"] == {"desactualizado": True}


def test_cascada_no_muta_datos_ni_captura_del_contexto():
    """La reducción trabaja sobre una copia incluso al retirar detalle, filas y columnas."""
    filas = {str(indice): ["123456789/987654321"] * 12 for indice in range(1, 4)}
    contexto = ContextoIA(
        "sistemas", "Sistemas", "Paso", {"M": describir_matriz([["1/3"] * 50 for _ in range(50)])},
        EstadoContexto(foco=ReferenciaPaso(1, 10, "pivote", "Fila", CapturaPaso(
            filas, deepcopy(filas), (1, 12), {"detalle": "Información" * 100},
        ))),
    )
    copia = deepcopy(contexto)
    serializado = serializar_contexto(contexto, maximo_caracteres=400)
    assert len(serializado) <= 400
    assert contexto == copia
    assert _leer_datos(serializado)["metadatos"]["truncado"] is True


@pytest.mark.parametrize("nombre", ['"\\\n' * 20, "A" * 120, "Álgebra" * 20])
@pytest.mark.parametrize("limite", [120, 180, 400])
def test_contexto_minimo_respeta_limite_del_bloque_completo(nombre, limite):
    """El contexto de emergencia sigue siendo JSON válido dentro del presupuesto total."""
    serializado = construir_contexto_minimo(nombre, nombre, limite)
    assert len(serializado) <= limite
    assert _leer_datos(serializado)["metadatos"] == {"truncado": True}


@pytest.mark.parametrize("limite", [-1, 0, 24, 80])
def test_limite_incapaz_de_alojar_esquema_minimo_se_rechaza(limite):
    """Un presupuesto imposible produce un error explícito y no un bloque fuera de límite."""
    with pytest.raises(ValueError, match="bloque mínimo"):
        construir_contexto_minimo("sistemas", "Sistemas", limite)


@pytest.mark.parametrize("estado,etiqueta", [
    (EstadoContexto(), "Viendo: Ejercicio"),
    (EstadoContexto(nota_ventana="ventana 6×6 de 50×50"), "Viendo: Ejercicio (ventana 6×6 de 50×50)"),
    (EstadoContexto(desactualizado=True, nota_ventana="ventana"), "Los datos cambiaron desde el último cálculo"),
    (EstadoContexto(vacio=True), "Sin contexto del ejercicio"),
])
def test_pildora_real_conserva_textos_y_prioridad_del_estado(estado, etiqueta):
    """NiceGUI presenta vacío, recorte y obsolescencia mediante los campos canónicos."""
    contexto = ContextoIA(etiqueta="Ejercicio", estado=estado)
    instancia = SimpleNamespace(
        _storage={"ai_ctx_enabled": True},
        active_ui=SimpleNamespace(obtener_contexto_ia=lambda: contexto),
        _toggle_ctx=lambda evento: None,
    )
    contenedor = ui.row()
    try:
        with contenedor:
            renderizar_pildora_contexto(instancia)
        etiquetas = [elemento.text for elemento in contenedor.descendants() if isinstance(elemento, ui.label)]
        assert etiquetas == [etiqueta]
    finally:
        contenedor.delete()
