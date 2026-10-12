"""Registro de rutas y páginas canónicas de Scalaris."""
from __future__ import annotations
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui

from src.frontend import navigation
from src.frontend.navigation import (
    HUB_PAGE_TITLE,
    HUB_ROUTE,
    legacy_redirects,
    redirect_location,
    route_of,
    tool_by_id,
)
from src.frontend.tema import configurar_tema


def registrar_redirecciones_legacy(aplicacion_destino: Any) -> None:
    """Registra los manejadores HTTP GET para las rutas legacy de Scalaris."""
    for regla in legacy_redirects():

        def _crear_manejador(regla_actual):
            async def _manejador(request: Request) -> RedirectResponse:
                items_entrantes = request.query_params.multi_items()
                url_destino = redirect_location(regla_actual, items_entrantes)
                codigo_estado = 301 if regla_actual.permanent else 302
                return RedirectResponse(url_destino, status_code=codigo_estado)

            return _manejador

        aplicacion_destino.get(regla.path)(_crear_manejador(regla))


def _registrar_paginas_algebra() -> None:
    """Registra las páginas canónicas del pilar de álgebra lineal."""

    @ui.page(route_of("sistemas"), title=tool_by_id("sistemas").page_title)
    def pagina_sistemas(method: str = "gauss", handoff: str = ""):
        metodo = method if method in ("gauss", "gauss-jordan") else "gauss"
        from src.frontend.vistas.linear_systems.view_linear_systems import LinearSystemsUI

        configurar_tema()
        LinearSystemsUI(initial_method=metodo).build(handoff_token=handoff)

    @ui.page(route_of("vectores"), title=tool_by_id("vectores").page_title)
    def pagina_vectores():
        from src.frontend.vistas.operaciones_vectores.vista_operaciones_vectores import VistaOperacionesVectores

        configurar_tema()
        VistaOperacionesVectores().construir()

    @ui.page(route_of("matrices"), title=tool_by_id("matrices").page_title)
    def pagina_matrices():
        from src.frontend.vistas.matrix_ops.view_matrix_ops import MatrixOpsUI

        configurar_tema()
        MatrixOpsUI().build()

    @ui.page(route_of("inversa"), title=tool_by_id("inversa").page_title)
    def pagina_inversa(handoff: str = ""):
        from src.frontend.vistas.inverse_ops.view_inverse_ops import InverseOpsUI

        configurar_tema()
        InverseOpsUI().build(handoff_token=handoff)


def _registrar_paginas_avanzadas() -> None:
    """Registra las páginas de visualización y extensiones matriciales."""

    @ui.page(route_of("visualizador"), title=tool_by_id("visualizador").page_title)
    def pagina_geometria(escena: str = "rectas-planos", handoff: str = ""):
        from src.frontend.vistas.geometria.vista_geometria import VistaGeometria

        configurar_tema()
        VistaGeometria().construir(escena=escena, token_handoff=handoff)

    @ui.page(route_of("leontief"), title=tool_by_id("leontief").page_title)
    def pagina_leontief():
        from src.frontend.vistas.matrix_ops.view_matrix_ops import LeontiefUI

        configurar_tema()
        LeontiefUI().build()

    @ui.page(route_of("transformaciones"), title=tool_by_id("transformaciones").page_title)
    def pagina_transformaciones():
        from src.frontend.vistas.matrix_ops.view_transformaciones import TransformacionesUI

        configurar_tema()
        TransformacionesUI().build()


def _registrar_paginas_utilidades() -> None:
    """Registra las páginas del pilar de utilidades numéricas."""

    @ui.page(route_of("bases"), title=tool_by_id("bases").page_title)
    def pagina_bases():
        from src.frontend.vistas.numeric_systems.view_numeric_systems import NumericSystemsUI

        configurar_tema()
        NumericSystemsUI().build()

    @ui.page(route_of("romanos"), title=tool_by_id("romanos").page_title)
    def pagina_romanos():
        from src.frontend.vistas.numeric_systems.view_roman_calculator import RomanCalculatorUI

        configurar_tema()
        RomanCalculatorUI().build()


def _registrar_pagina_hub() -> None:
    """Registra la página de inicio (Hub) si está habilitada."""
    if not navigation.HUB_ENABLED:
        return

    @ui.page(HUB_ROUTE, title=HUB_PAGE_TITLE)
    async def pagina_inicio_hub(client: Client, glosa: str = ""):
        from src.frontend.vistas.hub.view_hub import HubUI

        configurar_tema()
        await HubUI(glosa_open=(glosa == "1")).build(client)


def registrar_rutas() -> None:
    """Registra todas las redirecciones legacy y páginas canónicas de la aplicación."""
    registrar_redirecciones_legacy(app)
    _registrar_paginas_algebra()
    _registrar_paginas_avanzadas()
    _registrar_paginas_utilidades()
    _registrar_pagina_hub()
