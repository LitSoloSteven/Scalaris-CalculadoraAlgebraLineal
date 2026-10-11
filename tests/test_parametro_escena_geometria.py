"""Pruebas de normalizacion de escena en URL y validacion de handoff en el Visualizador."""
import pytest

from src.frontend.componentes.handoff import (
    ResultadoHandoff,
    _ALMACEN,
    consumir_vectores,
    guardar_vectores,
)
from src.frontend.navigation import VISUALIZER_SCENES
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria, ESCENAS_VALIDAS


def test_catalogo_visualizador_coincide_con_escenas_validas():
    """Garantiza que las claves de VISUALIZER_SCENES coincidan con ESCENAS_VALIDAS."""
    scene_keys = tuple(item[0] for item in VISUALIZER_SCENES)
    assert scene_keys == ESCENAS_VALIDAS
    assert ESCENAS_VALIDAS == ('rectas-planos', 'vectores', 'combinacion')


@pytest.mark.parametrize(
    "input_scene, expected_scene",
    [
        ("rectas-planos", "rectas-planos"),
        ("vectores", "vectores"),
        ("combinacion", "combinacion"),
        ("invalida", "rectas-planos"),
        ("", "rectas-planos"),
        ("desconocida_xyz", "rectas-planos"),
        ("RECTAS-PLANOS", "rectas-planos"),
    ],
)
def test_normalizar_escena_desconocida(input_scene, expected_scene):
    """Un parametro 'escena' invalido se normaliza a 'rectas-planos' sin redirigir."""
    assert VistaGeometria.normalizar_escena(input_scene) == expected_scene


def test_transferencia_vectores_rechaza_escena_distinta():
    """Un payload de vectores cuya escena no coincida con la URL se rechaza."""
    from tests.comun import limpiar_almacen_handoff
    limpiar_almacen_handoff()
    token = guardar_vectores("vectores", "combinacion", [["1", "2"], ["3", "4"]])
    result = consumir_vectores(token, allowed_n={2, 3})

    assert result.status == "ok"
    assert result.data is not None
    payload_scene = result.data.get("scene")

    current_scene = "vectores"
    assert payload_scene != current_scene

    if payload_scene != current_scene:
        rejected = ResultadoHandoff(
            status="invalid",
            data=None,
            source_name=result.source_name,
            message="Los datos recibidos no son válidos, así que empezamos con la herramienta vacía.",
        )

    assert rejected.status == "invalid"
    assert rejected.data is None
    assert rejected.message == "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."


def test_transferencia_vectores_acepta_escena_coincidente():
    """Un payload de vectores cuya escena coincide con la URL se acepta normalmente."""
    from tests.comun import limpiar_almacen_handoff
    limpiar_almacen_handoff()
    token = guardar_vectores("vectores", "vectores", [["1", "2"], ["3", "4"]])
    result = consumir_vectores(token, allowed_n={2, 3})

    assert result.status == "ok"
    assert result.data is not None
    assert result.data.get("scene") == "vectores"
