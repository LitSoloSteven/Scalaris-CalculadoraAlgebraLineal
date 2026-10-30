"""Navegación, formato visible y tiempo de lectura del paso vigente."""
from types import SimpleNamespace
from unittest.mock import Mock

from src.frontend.componentes.reproductor_pasos import PasoReproductor, ReproductorPasos


def _crear_reproductor(monkeypatch):
    """Prepara controles sin transporte para observar cada actualización."""
    pasos = [PasoReproductor(0, "inicial", "Inicio", "a" * 100),
             PasoReproductor(1, "final", "AA^{-1}=I", "a" * 1000)]
    reproductor = ReproductorPasos(pasos, (), lambda paso, destino: None, "prueba")
    for nombre in ("etiqueta_indice", "etiqueta_tipo", "descripcion", "fase", "progreso",
                   "explicacion", "contenedor_glosa", "contenedor_cuerpo"):
        setattr(reproductor, nombre, Mock())
    reproductor.tarjeta = SimpleNamespace(is_deleted=False)
    reproductor.temporizador = SimpleNamespace(is_deleted=False, interval=0, active=False)
    monkeypatch.setattr("nicegui.ui.run_javascript", lambda codigo: None)
    return reproductor


def test_navegar_y_cambiar_velocidad_recalcula_intervalo(monkeypatch):
    """Lee el paso actual y conserva la velocidad seleccionada al navegar."""
    reproductor = _crear_reproductor(monkeypatch)
    reproductor.ir_a(0)
    assert reproductor.temporizador.interval == 9
    reproductor._cambiar_velocidad(SimpleNamespace(value="Lenta"))
    assert reproductor.temporizador.interval == 14.4
    reproductor.ir_a(1)
    assert reproductor.temporizador.interval == 24
    reproductor.descripcion.set_content.assert_called_with("A·A<sup>-1</sup>=I")
    assert not reproductor.temporizador.active


def test_explicacion_matematica_y_duplicados_no_muestran_latex_crudo(monkeypatch):
    """El HTML seguro conserva potencias y omite la explicación repetida normalizada."""
    reproductor = _crear_reproductor(monkeypatch)
    paso = PasoReproductor(0, "inicial", "Identidad", "AA^{-1}=I")
    reproductor._actualizar_explicacion(paso, False)
    assert "A·A<sup>-1</sup>=I" in reproductor.explicacion.set_content.call_args.args[0]
    paso = PasoReproductor(0, "inicial", "AA^{-1}=I", "  AA^{-1}=I  ")
    reproductor._actualizar_explicacion(paso, True)
    assert "A·A" not in reproductor.explicacion.set_content.call_args.args[0]


def test_temporizador_eliminado_no_se_actualiza(monkeypatch):
    """Los cambios de velocidad no reactivan recursos eliminados."""
    reproductor = _crear_reproductor(monkeypatch)
    reproductor.temporizador.is_deleted = True
    reproductor._cambiar_velocidad(SimpleNamespace(value="Rápida"))
    assert reproductor.temporizador.interval == 0
