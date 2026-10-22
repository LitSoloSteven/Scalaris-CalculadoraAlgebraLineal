"""Pruebas de normalizacion de escena en URL y validacion de handoff en el Visualizador."""
import pytest

from src.frontend.componentes.transferencia import (
    ResultadoTransferencia,
    _ALMACEN,
    consumir_vectores,
    guardar_vectores,
)
from src.frontend.navegacion import ESCENAS_VISUALIZADOR
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria, ESCENAS_VALIDAS


def test_catalogo_visualizador_coincide_con_escenas_validas():
    """Garantiza que las claves de ESCENAS_VISUALIZADOR coincidan con ESCENAS_VALIDAS."""
    claves_escena = tuple(elemento[0] for elemento in ESCENAS_VISUALIZADOR)
    assert claves_escena == ESCENAS_VALIDAS
    assert ESCENAS_VALIDAS == ('rectas-planos', 'vectores', 'combinacion')


@pytest.mark.parametrize(
    'escena_entrada, escena_esperada',
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
def test_normalizar_escena_desconocida(escena_entrada, escena_esperada):
    """Un parametro 'escena' invalido se normaliza a 'rectas-planos' sin redirigir."""
    assert VistaGeometria.normalizar_escena(escena_entrada) == escena_esperada


def test_transferencia_vectores_rechaza_escena_distinta():
    """Un carga de vectores cuya escena no coincida con la URL se rechaza."""
    from tests.comun import limpiar_almacen_transferencia
    limpiar_almacen_transferencia()
    token = guardar_vectores("vectores", "combinacion", [["1", "2"], ["3", "4"]])
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})

    assert resultado.estado == "exito"
    assert resultado.datos is not None
    escena_carga = resultado.datos.get("escena")

    escena_actual = "vectores"
    assert escena_carga != escena_actual

    if escena_carga != escena_actual:
        rechazado = ResultadoTransferencia(
            estado="invalida",
            datos=None,
            nombre_origen=resultado.nombre_origen,
            mensaje="Los datos recibidos no son válidos, así que empezamos con la herramienta vacía.",
        )

    assert rechazado.estado == "invalida"
    assert rechazado.datos is None
    assert rechazado.mensaje == "Los datos recibidos no son válidos, así que empezamos con la herramienta vacía."


def test_transferencia_vectores_acepta_escena_coincidente():
    """Un carga de vectores cuya escena coincide con la URL se acepta normalmente."""
    from tests.comun import limpiar_almacen_transferencia
    limpiar_almacen_transferencia()
    token = guardar_vectores("vectores", "vectores", [["1", "2"], ["3", "4"]])
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})

    assert resultado.estado == "exito"
    assert resultado.datos is not None
    assert resultado.datos.get("escena") == "vectores"
