"""Registro de rutas y páginas canónicas de Scalaris."""
from __future__ import annotations
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui

from src.frontend import navegacion
from src.frontend.navegacion import (
    TITULO_PAGINA_INICIO,
    RUTA_INICIO,
    redirecciones_heredadas,
    ubicacion_redireccion,
    ruta_de,
    herramienta_por_identificador,
)
from src.frontend.tema import configurar_tema
from src.frontend.constantes import OPERACION_DETERMINANTE


def registrar_redirecciones_heredadas(aplicacion_destino: Any) -> None:
    """Registra los manejadores HTTP GET para las rutas heredadas de Scalaris."""
    for regla in redirecciones_heredadas():

        def _crear_manejador(regla_actual):
            async def _manejador(solicitud: Request) -> RedirectResponse:
                elementos_entrantes = solicitud.query_params.multi_items()
                url_destino = ubicacion_redireccion(regla_actual, elementos_entrantes)
                codigo_estado = 301 if regla_actual.permanente else 302
                return RedirectResponse(url_destino, status_code=codigo_estado)

            return _manejador

        aplicacion_destino.get(regla.ruta)(_crear_manejador(regla))


def _registrar_paginas_algebra() -> None:
    """Registra las páginas canónicas del pilar de álgebra lineal."""

    @ui.page(ruta_de("sistemas"), title=herramienta_por_identificador("sistemas").titulo_pagina)
    def pagina_sistemas(method: str = "gauss", handoff: str = ""):
        """Construye la página de sistemas con sus controles y contexto."""
        metodo = method if method in ("gauss", "gauss-jordan") else "gauss"
        from src.frontend.vistas.sistemas_lineales.vista_sistemas_lineales import VistaSistemasLineales

        configurar_tema("sistemas")
        VistaSistemasLineales(metodo_inicial=metodo).construir(token_transferencia=handoff)

    @ui.page(ruta_de("vectores"), title=herramienta_por_identificador("vectores").titulo_pagina)
    def pagina_vectores():
        """Construye la página de vectores con sus controles y contexto."""
        from src.frontend.vistas.operaciones_vectores.vista_operaciones_vectores import VistaOperacionesVectores

        configurar_tema("vectores")
        VistaOperacionesVectores().construir()

    @ui.page(ruta_de("matrices"), title=herramienta_por_identificador("matrices").titulo_pagina)
    def pagina_matrices(operacion: str = ""):
        """Construye la página de matrices con sus controles y contexto."""
        from src.frontend.vistas.operaciones_matrices.vista_operaciones_matrices import VistaOperacionesMatrices

        configurar_tema("determinantes" if operacion == OPERACION_DETERMINANTE else "matrices")
        if operacion == OPERACION_DETERMINANTE:
            from src.frontend.vistas.operaciones_matrices.vista_determinante import VistaDeterminante
            VistaDeterminante().construir()
            return
        VistaOperacionesMatrices().construir()

    @ui.page(ruta_de("inversa"), title=herramienta_por_identificador("inversa").titulo_pagina)
    def pagina_inversa(handoff: str = ""):
        """Construye la página de inversa con sus controles y contexto."""
        from src.frontend.vistas.operaciones_inversas.vista_operaciones_inversas import VistaOperacionesInversas

        configurar_tema("inversa")
        VistaOperacionesInversas().construir(token_transferencia=handoff)


def _registrar_paginas_avanzadas() -> None:
    """Registra las páginas de visualización y extensiones matriciales."""

    @ui.page(ruta_de("determinantes"), title=herramienta_por_identificador("determinantes").titulo_pagina)
    def pagina_determinantes():
        """Construye la captura pública de determinantes mediante triangulación LU."""
        from src.frontend.vistas.operaciones_matrices.vista_determinante import VistaDeterminante

        configurar_tema("determinantes")
        VistaDeterminante().construir()

    @ui.page(ruta_de("visualizador"), title=herramienta_por_identificador("visualizador").titulo_pagina)
    def pagina_geometria(escena: str = "rectas-planos", handoff: str = ""):
        """Construye la página de geometria con sus controles y contexto."""
        from src.frontend.vistas.geometria.vista_geometria import VistaGeometria

        configurar_tema("visualizador")
        VistaGeometria().construir(escena=escena, token_transferencia=handoff)

    @ui.page(ruta_de("leontief"), title=herramienta_por_identificador("leontief").titulo_pagina)
    def pagina_leontief():
        """Construye la página de leontief con sus controles y contexto."""
        from src.frontend.vistas.operaciones_matrices.vista_leontief import VistaLeontief

        configurar_tema("leontief")
        VistaLeontief().construir()

    @ui.page(ruta_de("transformaciones"), title=herramienta_por_identificador("transformaciones").titulo_pagina)
    def pagina_transformaciones():
        """Construye la página de transformaciones con sus controles y contexto."""
        from src.frontend.vistas.operaciones_matrices.vista_transformaciones import VistaTransformaciones

        configurar_tema("transformaciones")
        VistaTransformaciones().construir()


def _registrar_paginas_utilidades() -> None:
    """Registra las páginas del pilar de utilidades numéricas."""

    @ui.page(ruta_de("bases"), title=herramienta_por_identificador("bases").titulo_pagina)
    def pagina_bases():
        """Construye la página de bases con sus controles y contexto."""
        from src.frontend.vistas.sistemas_numericos.vista_sistemas_numericos import VistaSistemasNumericos

        configurar_tema("bases")
        VistaSistemasNumericos().construir()

    @ui.page(ruta_de("romanos"), title=herramienta_por_identificador("romanos").titulo_pagina)
    def pagina_romanos():
        """Construye la página de romanos con sus controles y contexto."""
        from src.frontend.vistas.sistemas_numericos.vista_calculadora_romana import VistaCalculadoraRomana

        configurar_tema("romanos")
        VistaCalculadoraRomana().construir()


def _registrar_pagina_inicio() -> None:
    """Registra la página de inicio (inicio) si está habilitada."""
    if not navegacion.INICIO_HABILITADO:
        return

    @ui.page(RUTA_INICIO, title=TITULO_PAGINA_INICIO)
    async def pagina_inicio(client: Client, glosa: str = ""):
        """Construye la página de inicio con sus controles y contexto."""
        from src.frontend.vistas.inicio.vista_inicio import VistaInicio

        configurar_tema("inicio")
        await VistaInicio(glosa_abierta=(glosa == "1")).construir(client)


def registrar_rutas() -> None:
    """Registra todas las redirecciones heredadas y páginas canónicas de la aplicación."""
    registrar_redirecciones_heredadas(app)
    _registrar_paginas_algebra()
    _registrar_paginas_avanzadas()
    _registrar_paginas_utilidades()
    _registrar_pagina_inicio()
