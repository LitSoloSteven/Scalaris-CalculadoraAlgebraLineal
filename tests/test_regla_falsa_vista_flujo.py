"""Captura, publicación y preferencias de la vista con el motor real."""
import json
import math

import pytest

from src.ai.huellas import calcular_huella
from src.frontend.controladores.regla_falsa.controlador import resolver_captura
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario, textos_resultado


def test_vista_vacia_no_calcula_ni_inventa_recientes(monkeypatch):
    """La vista inicial conserva preferencias del contrato y expone entradas etiquetadas."""
    async def comprobar(vista):
        """Inspecciona el formulario real antes de cualquier envío."""
        assert vista.esta_completamente_vacio()
        assert vista.ultimo_resultado is None and not vista.historial and not vista.ocupado
        assert vista.obtener_contexto_ia().vacio
        assert vista.capturar()["tolerancia"] == "1e-06"
        assert all(campo._props.get("label") for campo in vista._campos_captura())
        assert vista.estado._props["aria-live"] == "polite"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambios,estado,filas", [
    ({}, "EXITO", 9),
    ({"expresion": "x", "extremo_izquierdo": "0"}, "EXITO", 0),
    ({"expresion": "x-1.5"}, "EXITO", 1),
    ({"expresion": "x^2+1"}, "SIN_CAMBIO_DE_SIGNO", 0),
    ({"expresion": "sqrt(x)", "extremo_izquierdo": "-1"}, "ERROR", 0),
    ({"expresion": "x+"}, "ERROR", 0),
    ({"limite_iteraciones": "1"}, "LIMITE_ITERACIONES", 1),
    ({"extremo_izquierdo": str(math.nextafter(math.sqrt(2), -math.inf)),
      "extremo_derecho": str(math.sqrt(2)), "tolerancia": "1e-30"}, "ESTANCAMIENTO", 1),
    ({"expresion": "2sin(x)-1", "extremo_izquierdo": "0", "extremo_derecho": "60",
      "unidad_angular": "grados"}, "EXITO", 7),
])
def test_vista_publica_estados_del_motor(monkeypatch, cambios, estado, filas):
    """La captura visible y su resultado mantienen el sobre del controlador real."""
    async def comprobar(vista):
        """Envía una captura y contrasta estado, filas, contexto y finitud."""
        captura = captura_regla_falsa(**cambios)
        vista.cargar_captura(captura)
        assert vista.ultimo_resultado is None and not vista.historial
        await vista.resolver()
        respuesta = vista.ultimo_resultado
        assert respuesta == resolver_captura(captura)
        assert respuesta["estado"] == estado and respuesta["iteraciones_totales"] == filas
        assert vista._huella_resultado == calcular_huella(vista.capturar())
        assert vista.obtener_contexto_ia().resultado["estado"] == estado
        assert len(vista.historial) == int(respuesta["aproximacion"] is not None or bool(respuesta["iteraciones"]))
        assert not vista.ocupado and vista.tarea_calculo is None
        json.dumps(respuesta, allow_nan=False)
        assert not any("Convergió" in texto for texto in textos_resultado(vista)) or estado == "EXITO"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("expresion", ["x^2-2", "x+", "sqrt(x-1.5)"])
def test_vista_refleja_intervalo_invertido_sin_invalidar_resultado(monkeypatch, expresion):
    """La normalización vigente se refleja también con entrada nula por sintaxis inválida."""
    async def comprobar(vista):
        """Verifica extremos, huella y advertencia tras publicar la respuesta normalizada."""
        vista.cargar_captura(captura_regla_falsa(
            expresion=expresion, extremo_izquierdo="2", extremo_derecho="1"))
        await vista.resolver()
        assert (float(vista.inferior.value), float(vista.superior.value)) == (1, 2)
        assert vista.ultimo_resultado is not None
        assert vista._huella_resultado == calcular_huella(vista.capturar())
        assert any("Se intercambiaron" in texto for texto in textos_resultado(vista))
    ejecutar_escenario(monkeypatch, comprobar)


def test_formato_visual_no_invalida_y_limpieza_conserva_preferencias(monkeypatch):
    """La precisión modifica solo el rótulo y limpiar conserva preferencias matemáticas y visuales."""
    async def comprobar(vista):
        """Cambia formato, valida una preferencia imposible y limpia la captura real."""
        vista.cargar_captura(captura_regla_falsa(tolerancia="1e-9", limite_iteraciones="40"))
        await vista.resolver()
        respuesta, huella = vista.ultimo_resultado, vista._huella_resultado
        vista.formato.set_value(8)
        assert vista.ultimo_resultado is respuesta and vista._huella_resultado == huella
        assert vista._precision_visual == 8 and vista.valor_aproximacion.text.endswith("1.41421356")
        vista.formato.set_value(16)
        assert vista.error_formato.text and vista._precision_visual == 8
        vista.limpiar_todo()
        assert vista.esta_completamente_vacio() and vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert vista.tolerancia.value == "1e-9" and vista.limite.value == "40"
        assert vista._precision_visual == 8 and len(vista.historial) == 1
    ejecutar_escenario(monkeypatch, comprobar)
