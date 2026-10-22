"""Transmisión completa del foco del reproductor hacia el contexto didáctico."""
import json
from types import SimpleNamespace

import pytest

from src.ai.contexto import ContextoIA
from src.backend.modelos.matriz import Matriz
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.panel_ia import _recopilar_contexto_didactico
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor
from src.frontend.vistas.operaciones_inversas.mixin_pasos import MixinPasosOperacionesInversas


def _serializar_foco(herramienta, foco):
    contexto = ContextoIA(herramienta, herramienta, "Ejercicio", {"valor": "1/3"})
    interfaz = SimpleNamespace(obtener_contexto_ia=lambda: contexto)
    bloque = _recopilar_contexto_didactico(interfaz, foco)
    return json.loads(bloque[len("[CONTEXTO]\n"):-len("\n[/CONTEXTO]")])


@pytest.mark.parametrize("herramienta,tipo", [
    ("sistemas", "eliminacion"), ("matrices", "operacion"),
    ("vectores", "componente"), ("bases", "division"), ("romanos", "decodificacion"),
])
def test_foco_compartido_conserva_captura_y_posicion(herramienta, tipo):
    """Las familias compartidas transmiten captura, detalle y posición actual."""
    recibidos = []
    panel = SimpleNamespace(disparar_explicacion_paso=recibidos.append)
    captura = {"tipo": tipo, "operacion": "Operación 1/3", "filas_antes": {"1": ["1/3"]},
               "filas_despues": {"1": ["2/3"]}, "columnas": [1, 1], "detalle": {"datos": "3/4"}}
    paso = PasoReproductor(0, tipo, "Descripción", meta_explicar=captura)
    crear_accion_explicacion(panel, [paso])(paso)
    esperado = dict(captura, indice=1, total=1)
    assert recibidos == [esperado]
    datos = _serializar_foco(herramienta, recibidos[0])
    assert datos["herramienta"] == herramienta and datos["foco"] == esperado


def test_inversa_agrega_captura_real_del_controlador():
    """La quinta familia incluye las filas exactas antes y después de normalizar."""
    recibidos = []
    vista = SimpleNamespace(panel_ia=SimpleNamespace(disparar_explicacion_paso=recibidos.append))
    pasos = [
        {"matriz": Matriz(1, 2, [[2, 1]]), "descripcion": "Matriz inicial"},
        {"matriz": Matriz(1, 2, [[1, "1/2"]]), "descripcion": "F1 → F1 / 2", "filas_cambiadas": [0]},
    ]
    paso = PasoReproductor(1, "normalizacion", "Dividir", meta_explicar={"tipo": "normalizacion", "operacion": "F1 / 2"})
    MixinPasosOperacionesInversas._crear_accion_glosa(vista, pasos, 2)(paso)
    datos = _serializar_foco("inversa", recibidos[0])
    assert datos["foco"]["indice"] == datos["foco"]["total"] == 2
    assert datos["foco"]["filas_antes"] == {"1": ["2", "1"]}
    assert datos["foco"]["filas_despues"] == {"1": ["1", "1/2"]}
