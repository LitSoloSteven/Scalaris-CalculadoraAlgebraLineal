"""Renderizado detallado de la tarjeta de matriz inversa calculada exitosamente."""
from __future__ import annotations

import json
from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS
from src.frontend.controladores.operaciones_inversas.presentacion import preparar_opciones_inversa
from src.backend.utilidades.formateadores import formatear_fraccion_texto
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_matriz


def renderizar_resultado_error(vista, resultado: dict) -> None:
    """Renderiza el mensaje de error y resalta celdas si aplica."""
    with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'):
        ui.icon('error', size='sm')
        ui.label(resultado.get('mensaje', 'Error en los datos ingresados.')).classes('font-bold')
    if resultado.get('celda_error'):
        r, c = resultado['celda_error']
        vista.enfocar_celda((r, c))
        ui.notify(resultado.get('mensaje', 'Celda inválida'), type='negative')


def renderizar_resultado_singular(vista, resultado: dict, dimension: int) -> None:
    """Renderiza la información de matriz singular y pasos si los hay."""
    with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'):
        ui.icon('warning', size='sm')
        ui.label('Matriz singular: no tiene inversa').classes('font-bold')

    with ui.column().classes('panel-tarjeta p-6 w-full mb-6 gap-3'):
        ui.label('Matriz Singular (det = 0)').classes('text-lg font-bold texto-principal')
        ui.label(
            'Una matriz cuadrada tiene inversa si y solo si det(A) ≠ 0. '
            'Aquí det(A) = 0, por lo tanto no es posible obtener un pivote en cada columna.'
        ).classes('text-sm texto-secundario')

        ui.label('Matriz evaluada A:').classes('text-sm font-semibold texto-principal mt-2')
        if preparar_opciones_inversa(dimension)['mostrar_latex'] and resultado.get('matriz_a_latex'):
            ui.html(
                f'<div class="matematicas-desplazamiento matematicas-etiqueta text-base">$$ A = {resultado["matriz_a_latex"]} $$</div>'
            )
        elif resultado.get('matriz_a'):
            ui.html(html_tabla_matriz(resultado['matriz_a']))

    if getattr(vista, 'panel_ia', None):
        vista.panel_ia.renderizar_sugerencias_en_linea()

    if resultado.get('pasos'):
        vista._renderizar_seccion_pasos(resultado)


def renderizar_resultado_exitoso(vista, resultado: dict, dimension: int) -> None:
    """Presenta estado, matrices, acciones y comprobaciones de la inversa recibida."""

    with ui.row().classes('items-center gap-2 px-4 py-2 distintivo-exito mb-4 w-fit'):
        ui.icon('check_circle', size='sm')
        ui.label('Matriz invertible').classes('font-bold')

    with ui.row().classes('panel-tarjeta px-4 py-2 fuente-pequena items-center gap-4 flex-wrap mb-6 w-full'):
        ui.label(f"{dimension} × {dimension}").classes('font-bold texto-principal')
        ui.label(f"det(A) = {resultado['determinante_texto']} ≠ 0").classes('font-semibold texto-principal')
        ui.label(f"{resultado['estadisticas']['total']} pasos").classes('texto-secundario')
        ui.label(f"{resultado['estadisticas']['intercambios']} intercambios").classes('texto-secundario')
        ui.label(f"calculado en {resultado['tiempo_transcurrido_segundos']:.2f} s").classes('texto-secundario')

    if getattr(vista, 'panel_ia', None):
        vista.panel_ia.renderizar_sugerencias_en_linea()

    _renderizar_tarjeta_matriz(resultado, dimension)
    _renderizar_comprobaciones(resultado, dimension)
    vista._renderizar_seccion_pasos(resultado)
    _renderizar_interpretacion()


def _renderizar_tarjeta_matriz(resultado: dict, dimension: int) -> None:
    """Dibuja la tarjeta con la representacion de A y A^-1 y botones de accion."""
    with ui.column().classes('panel-tarjeta p-6 w-full mb-6'):
        ui.label('Resultado: A⁻¹').classes('text-lg font-bold texto-principal mb-4')

        if preparar_opciones_inversa(dimension)['mostrar_latex']:
            with ui.row().classes('items-center justify-center gap-6 flex-wrap w-full my-4'):
                ui.html(
                    f'<div class="matematicas-desplazamiento matematicas-etiqueta text-base">$$ A = {resultado["matriz_a_latex"]} $$</div>'
                )
                ui.icon('arrow_forward', size='md').classes('texto-secundario')
                ui.html(
                    f'<div class="matematicas-desplazamiento matematicas-etiqueta text-base">$$ A^{{-1}} = {resultado["inversa_latex"]} $$</div>'
                )
        else:
            _renderizar_matrices_tabulares(resultado)

        _agregar_botones_acciones(resultado, dimension)

        with ui.expansion('Ver A⁻¹ en decimales (≈4 cifras)', icon='numbers').classes(
            'w-full mt-3 panel-tarjeta'
        ).props('header-class="font-bold texto-principal text-sm"'):
            ui.html(html_tabla_matriz(resultado['inversa'], decimales=True))

        ui.label(
            'Cada columna j de A⁻¹ es la solución x de A·x = eⱼ (eⱼ = columna j de la identidad).'
        ).classes('texto-secundario fuente-pequena mt-3')


def _renderizar_matrices_tabulares(resultado):
    """Presenta la matriz de entrada y su inversa mediante tablas desplazables."""
    with ui.row().classes('items-start justify-center gap-8 flex-wrap w-full my-4'):
        with ui.column().classes('items-center disposicion-ajustada'):
            ui.label('A').classes('font-bold texto-principal mb-2')
            ui.html(html_tabla_matriz(resultado['matriz_a']))
        with ui.column().classes('items-center disposicion-ajustada'):
            ui.label('A⁻¹').classes('font-bold texto-principal mb-2')
            ui.html(html_tabla_matriz(resultado['inversa']))


def _agregar_botones_acciones(resultado: dict, dimension: int) -> None:
    """Botones para copiar A^-1 y enviar al solver de sistemas."""
    def copiar_inversa():
        """Copia la inversa calculada al portapapeles como filas tabuladas."""
        inversa = resultado.get('inversa')
        if not inversa:
            return
        lineas = []
        for i in range(dimension):
            lineas.append("\t".join(formatear_fraccion_texto(inversa.obtener(i, j)) for j in range(dimension)))
        ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(chr(10).join(lineas))});")
        ui.notify('A⁻¹ copiada al portapapeles', type='positive')

    def ir_a_sistemas():
        """Transfiere la inversa calculada al editor de sistemas lineales."""
        if not preparar_opciones_inversa(dimension)['transferir_sistema']:
            ui.notify(f"Sistemas de ecuaciones admite hasta {DIMENSION_MAXIMA_SISTEMAS}×{DIMENSION_MAXIMA_SISTEMAS}; tu matriz es de {dimension}×{dimension}.", type='warning')
            return
        datos = [[formatear_fraccion_texto(resultado['inversa'].obtener(r, c)) for c in range(dimension)] for r in range(dimension)]
        from src.frontend.componentes.transferencia import guardar_matriz, url_transferencia
        from src.frontend.navegacion import ruta_de
        token = guardar_matriz('inversa', datos)
        ui.navigate.to(url_transferencia(ruta_de('sistemas'), token))

    with (
        ui.row().classes('w-full justify-between items-center mt-4 flex-wrap gap-2'),
        ui.row().classes('gap-2'),
    ):
        ui.button('Copiar A⁻¹', icon='content_copy', on_click=copiar_inversa, color=None).classes('boton-discreto text-xs').props('ripple=false')
        ui.button('Resolver A·x = b con esta A', on_click=ir_a_sistemas, color=None).classes('boton-discreto text-xs').props('ripple=false')


def _renderizar_comprobaciones(resultado: dict, dimension: int) -> None:
    """Muestra comprobaciones formales como expansion."""
    with (
        ui.expansion('Comprobaciones formales', icon='verified').classes(
        'w-full mb-6 panel-tarjeta'
    ).props('default-opened header-class="font-bold texto-principal"'),
        ui.column().classes('w-full gap-4 p-2'),
    ):
        for comprobacion in resultado.get('comprobaciones', []):
            with ui.row().classes('w-full justify-between items-center gap-4 flex-wrap'):
                ui.label(comprobacion['titulo']).classes('font-bold texto-principal text-sm')
                clase_distintivo = 'distintivo-exito' if comprobacion['coincide'] else 'distintivo-error'
                texto_distintivo = 'Correcto' if comprobacion['coincide'] else 'Incorrecto'
                ui.badge(texto_distintivo, color=None).classes(clase_distintivo)
            if comprobacion.get('detalle_latex'):
                ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta text-sm my-1">$$ {comprobacion["detalle_latex"]} $$</div>')
        if not preparar_opciones_inversa(dimension)['mostrar_latex']:
            ui.label('Verificado con aritmética exacta (fracciones).').classes(
                'texto-secundario fuente-pequena italic mt-2'
            )


def _renderizar_interpretacion() -> None:
    """Bloque explicativo didactico."""
    with ui.expansion('¿Cómo interpretar este resultado?', icon='help_outline').classes(
        'w-full mt-6 panel-tarjeta'
    ).props('header-class="font-bold texto-principal"'):
        ui.label(
            'A⁻¹ cumple A·A⁻¹ = A⁻¹·A = I. Existe solo si det(A) ≠ 0. '
            'Todos los valores son exactos (fracciones). (Aᵀ)⁻¹ = (A⁻¹)ᵀ.'
        ).classes('texto-secundario text-sm p-3')


def renderizar_resultado_inversa(vista, resultado: dict):
    """Presenta el resultado exitoso, singular o erróneo de la matriz inversa."""
    vista.contenedor_resultados.clear()
    vista.contenedor_resultados.classes(
        remove='items-center justify-center', add='items-start justify-start'
    )

    estado = resultado.get("estado", "ERROR")
    dimension = resultado.get("dimension", vista.panel_matriz_cuadrada.dimension)

    with vista.contenedor_resultados:
        if estado == "ERROR":
            renderizar_resultado_error(vista, resultado)
        elif estado == "SINGULAR":
            renderizar_resultado_singular(vista, resultado, dimension)
        else:
            renderizar_resultado_exitoso(vista, resultado, dimension)
