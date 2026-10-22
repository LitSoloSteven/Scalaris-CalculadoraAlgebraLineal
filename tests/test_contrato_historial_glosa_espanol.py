"""Rechazo de historiales alternativos y conservación del contrato del proveedor."""
from copy import deepcopy
from dataclasses import asdict

import pytest

from src.ai.historial import limpiar_historial_almacenado
from src.ai.mensajes import construir_mensajes, recortar_historial
from src.frontend.catalogo_sugerencias import Seguimiento
from src.frontend.sugerencias import CeldaInvalida, Senales, Sugerencia
from tests.comun_clientes import PanelIASimulado


@pytest.mark.parametrize("antiguo", [
    {"text": "Pregunta", "sent": True},
    {"role": "user", "content": "Pregunta"},
    {"texto": "Pregunta", "enviado": True, "content": "Otra"},
    {"texto": "Pregunta", "enviado": True, "role": "assistant"},
    {"texto": "Pregunta", "enviado": "false"},
    "Pregunta", None,
])
def test_contratos_ajenos_se_descartan_sin_mutar(antiguo):
    """El mensaje ajeno no contamina al mensaje canónico vecino ni al original."""
    historial = [antiguo, {"texto": "Vigente", "enviado": False}]
    copia = deepcopy(historial)
    assert recortar_historial(historial) == [{"role": "assistant", "content": "Vigente"}]
    assert historial == copia
    assert limpiar_historial_almacenado(historial, 60) == [historial[1]]


def test_historial_espanol_produce_carga_externo_completo():
    """El proveedor recibe los roles externos y cada texto exactamente una vez."""
    historial = [
        {"texto": "Pregunta anterior", "enviado": True, "almacenable_en_cache": True},
        {"texto": "Respuesta anterior", "enviado": False, "animar": True},
        {"texto": "Fallo", "error": True, "reintentar": True},
    ]
    mensajes = construir_mensajes(historial, "Pregunta actual")
    assert mensajes[1:] == [
        {"role": "user", "content": "Pregunta anterior"},
        {"role": "assistant", "content": "Respuesta anterior"},
        {"role": "user", "content": "Pregunta actual"},
    ]
    assert all(set(mensaje) == {"role", "content"} for mensaje in mensajes)


@pytest.mark.parametrize("historial", [{"texto": "Raíz inválida"}, None, 1])
def test_almacen_descarta_raiz_ajena(historial):
    """La inicialización no interpreta objetos arbitrarios como historial."""
    panel = PanelIASimulado(almacen={"ia_historial_chat": historial})
    assert panel.historial_chat == []


def test_limpieza_sin_bucle_no_lanza_tareas():
    """Limpiar un panel sin montar mantiene el contrato sin requerir un bucle asíncrono."""
    panel = PanelIASimulado(almacen={})
    panel.historial_chat.append({"texto": "Pregunta", "enviado": True})
    panel.limpiar_chat()
    assert panel.historial_chat == []
    assert set(panel._almacen) == {"ia_historial_chat", "ia_panel_abierto", "ia_contexto_habilitado"}


def test_sugerencias_exponen_solo_campos_espanoles():
    """Señales, celdas, sugerencias y seguimientos no ofrecen campos duplicados."""
    assert set(asdict(Senales("matrices", "exito"))) == {"herramienta", "estado", "banderas", "invalida"}
    assert set(asdict(CeldaInvalida("A[1,1]"))) == {"etiqueta", "foco"}
    assert set(asdict(Sugerencia("matrices.producto", "Pregunta", "estado"))) == {"identificador", "texto", "rol", "foco"}
    assert set(asdict(Seguimiento("ejemplo", "Ejemplo", "Pregunta"))) == {"identificador", "etiqueta", "pregunta", "mas_simple"}
