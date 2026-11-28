"""Pruebas de Configuración global, accesibilidad común y piloto Sistemas."""
import asyncio
import json
import subprocess
from pathlib import Path

import pytest
from nicegui import Client, core, ui

from src.frontend.componentes.aplicacion.base.simbolos import renderizar_boton_simbolos
from src.frontend.componentes.aplicacion.controles.barra_navegacion import crear_barra_navegacion
from src.frontend.componentes.captura.ecuaciones.limpieza_captura import LimpiezaCaptura
from src.frontend.componentes.exportacion_pdf.piezas.dialogo import DialogoPortada
from src.frontend.componentes.reproductor_pasos.interfaz.reproductor import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor
from tests.comun import RAIZ
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("contextual", [True, False])
def test_configuracion_global_en_ambas_navegaciones_y_sin_sonido_en_inicio(monkeypatch, contextual):
    """La barra monta Configuración con temas y sonido en ambas variantes."""
    monkeypatch.setenv("SCALARIS_NAV", "1" if contextual else "0")
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-configuracion-global"))
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa="/algebra-lineal/sistemas")
        elementos = list(cliente.elements.values())
        _comprobar_dialogo_configuracion(elementos)
        opciones = [e for e in elementos if "data-tema-opcion" in e._props]
        assert [e._props["data-tema-opcion"] for e in opciones] == ["papel", "marea", "medianoche"]
        sonidos = [e for e in elementos if "data-sonido-control" in e._props]
        assert len(sonidos) == 1
    finally:
        cliente.delete()


def _comprobar_dialogo_configuracion(elementos):
    disparadores = [e for e in elementos if "data-configuracion-abrir" in e._props]
    assert len(disparadores) == 1
    assert disparadores[0]._props["aria-label"] == "Configuración"
    assert disparadores[0]._props["aria-haspopup"] == "dialog"
    dialogos = [e for e in elementos if isinstance(e, ui.dialog)]
    assert len(dialogos) == 1
    assert dialogos[0]._props["aria-labelledby"] == "configuracion-titulo"
    cierres = [e for e in elementos if e._props.get("aria-label") == "Cerrar configuración"]
    assert len(cierres) == 1


def test_reproductor_deshabilita_botones_en_extremos(monkeypatch):
    """El reproductor deshabilita retroceso en el primer paso y avance en el último."""
    monkeypatch.setattr(core, "script_mode", False)
    pasos = (
        PasoReproductor(0, "inicial", "Inicio", "Primer paso", 0),
        PasoReproductor(1, "eliminacion", "Mitad", "Paso medio", 0),
        PasoReproductor(2, "final", "Final", "Último paso", 0),
    )
    grupos = (GrupoReproductor("Fase", "", "inicial", (0, 1, 2)),)
    cliente = Client(ui.page("/prueba-reproductor-extremos"))
    try:
        with cliente:
            reproductor = ReproductorPasos(pasos, grupos, lambda _p, _c: None, "extremos", {"sin_movimiento": True})
            reproductor.construir()
        assert reproductor.boton_primero.enabled is False
        assert reproductor.boton_anterior.enabled is False
        assert reproductor.boton_siguiente.enabled is True
        assert reproductor.boton_ultimo.enabled is True

        reproductor.ir_a(1)
        assert reproductor.boton_primero.enabled is True
        assert reproductor.boton_anterior.enabled is True
        assert reproductor.boton_siguiente.enabled is True
        assert reproductor.boton_ultimo.enabled is True

        reproductor.ir_a(2)
        assert reproductor.boton_primero.enabled is True
        assert reproductor.boton_anterior.enabled is True
        assert reproductor.boton_siguiente.enabled is False
        assert reproductor.boton_ultimo.enabled is False
        reproductor.detener()
    finally:
        cliente.delete()


def test_dialogo_portada_cierre_sin_etiquetas_duplicadas_y_foco_dos_px(monkeypatch):
    """El diálogo PDF evita <label for> duplicado, incluye cierre y usa contorno de 2 px."""
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-dialogo-portada"))
    try:
        with cliente:
            activador = ui.button("Exportar PDF")
            portada = DialogoPortada(lambda: None, activador)
        elementos = list(cliente.elements.values())
        htmls = [e.content for e in elementos if isinstance(e, ui.html)]
        assert not any("<label for=" in contenido for contenido in htmls)
        assert any(e._props.get("aria-label") == "Cerrar diálogo de portada" for e in elementos)
        assert "no-caps" in portada.cancelar._props
        assert "no-caps" in portada.confirmar._props
        assert portada.dialogo._props.get("transition-show") == "scale"
    finally:
        cliente.delete()

    css_pdf = (RAIZ / "src/frontend/recursos/css/utilidades/exportacion_pdf.css").read_text(encoding="utf-8")
    assert "outline: 2px solid var(--focus-ring);" in css_pdf
    assert "outline: var(--space-1)" not in css_pdf


def test_boton_simbolos_y_limpieza_con_texto_en_piloto_sistemas(monkeypatch):
    """El piloto Sistemas usa disposición unificada, Limpiar con texto y botón Símbolos."""
    async def comprobar(_vista, cliente):
        """Comprueba contenedores de disposición y acciones accesibles del piloto."""
        elementos = list(cliente.elements.values())
        assert any("disposicion-captura-fila" in e.classes for e in elementos)
        assert any("disposicion-resultados" in e.classes for e in elementos)
        boton_limpiar, = (e for e in elementos if e._props.get("id") == "boton-limpiar-principal")
        assert boton_limpiar.text == "Limpiar"
        assert "no-caps" in boton_limpiar._props
        simbolos = [e for e in elementos if "data-abrir-simbolos" in e._props]
        assert len(simbolos) == 1
        assert simbolos[0]._props["aria-label"] == "Abrir selector de símbolos"

    asyncio.run(construir_pagina(monkeypatch, "sistemas", comprobar))

    with ui.column() as contenedor:
        try:
            boton = renderizar_boton_simbolos(campo_objetivo="campo-demo")
            assert boton._props.get("data-campo-simbolos") == "campo-demo"
            assert LimpiezaCaptura is not None
        finally:
            contenedor.delete()


def test_scripts_cliente_glosa_sonido_y_rechazo_numerico():
    """Comprueba inicialización de Glosa en inicio, destruir(), aria-label y rechazo accesible."""
    script = (RAIZ / "tests" / "comun_configuracion_cliente.js").read_text(encoding="utf-8")
    resultado = subprocess.run(
        ["node", "-e", script],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert resultado.returncode == 0, resultado.stderr
