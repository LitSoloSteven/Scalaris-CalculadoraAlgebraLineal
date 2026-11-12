"""Composición de la página pública con navegación y contexto de Glosa."""
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.navegacion import ruta_de
from .vista_regla_falsa import VistaReglaFalsa


def construir_pagina_regla_falsa() -> VistaReglaFalsa:
    """Monta la herramienta en la estructura común y devuelve su instancia por cliente."""
    vista = VistaReglaFalsa()
    vista.panel_ia = PanelIA(vista)
    crear_estructura_aplicacion(vista, ruta_activa=ruta_de("regla_falsa"))
    vista.construir()
    vista.panel_ia.construir()
    return vista
