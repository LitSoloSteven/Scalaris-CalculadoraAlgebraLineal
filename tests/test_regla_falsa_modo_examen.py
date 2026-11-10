"""Modo didáctico y copia optativa sincronizados con la traza clásica."""
from copy import deepcopy

import pytest

from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from src.frontend.controladores.regla_falsa.presentacion_examen import datos_examen
from src.frontend.controladores.regla_falsa.salidas_regla_falsa import (
    texto_copia_examen_regla_falsa, texto_copia_regla_falsa,
)
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("accion,texto", [("reemplazar_a", "Se reemplaza a"),
    ("reemplazar_b", "Se reemplaza b"), ("raiz", "Ambos extremos pasan a c"),
    ("sin_cambio", "No se reemplaza ningún extremo")])
def test_catalogo_completo_de_acciones(accion, texto):
    """Las cuatro decisiones se explican explícitamente sin catálogo de punto medio."""
    respuesta = resolver_captura(captura_regla_falsa())
    fila = {**respuesta["iteraciones"][0], "accion": accion}
    original = deepcopy(fila)
    datos = dict(datos_examen(fila))
    assert texto in datos["Extremo reemplazado"]
    assert datos["Signo de f(a)·f(c)"] == "Positivo"
    assert "Continúa" in datos["Motivo de parada"]
    assert fila == original


@pytest.mark.parametrize("cambios", [{}, {"limite_iteraciones": "1"},
    {"expresion": "x", "extremo_izquierdo": "0"}, {"expresion": "x+"}])
def test_copia_nueva_preserva_contrato_clasico(cambios):
    """La copia clásica sigue idéntica; la nueva añade solo decisiones de filas existentes."""
    respuesta = resolver_captura(captura_regla_falsa(**cambios))
    original = deepcopy(respuesta)
    clasica = texto_copia_regla_falsa(respuesta, 6)
    examen = texto_copia_examen_regla_falsa(respuesta, 6)
    assert examen.startswith(clasica + "\n\n")
    for fila in respuesta["iteraciones"]:
        assert f"Iteración {fila['i']}" in examen
        assert all(f"{etiqueta}: {valor}" in examen for etiqueta, valor in datos_examen(fila))
    if not respuesta["iteraciones"]:
        assert "No hay iteraciones registradas" in examen
    assert respuesta == original and texto_copia_regla_falsa(respuesta, 6) == clasica


def test_examen_tabla_secante_y_foco_comparten_fila(monkeypatch):
    """Activar examen y cambiar formato conservan resultado, paso, nodo y contexto local."""
    async def comprobar(vista):
        """Recorre una fila y cambia preferencias sin enviar consultas de IA."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        respuesta, panel = vista.ultimo_resultado, vista.detalle_procedimiento
        panel.reproductor.ir_a(1)
        fila = respuesta["iteraciones"][0]
        grafica = panel.grafica
        vista.interruptor_examen.set_value(True)
        assert vista.modo_examen
        assert panel.fila_activa is fila and panel.tabla.fila_activa == str(fila["i"])
        assert vista.obtener_contexto_ia().foco.captura.detalle["iteracion"] == fila
        vista.formato.set_value(3)
        assert vista.ultimo_resultado is respuesta and panel.grafica is grafica
        panel.reproductor.ir_a(2)
        assert panel.fila_activa is respuesta["iteraciones"][1]
        vista.limpiar_todo()
        assert vista.modo_examen
    ejecutar_escenario(monkeypatch, comprobar)
