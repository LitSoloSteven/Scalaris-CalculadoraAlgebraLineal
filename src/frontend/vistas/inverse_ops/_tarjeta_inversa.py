"""Renderizado detallado de la tarjeta de matriz inversa calculada exitosamente."""
from __future__ import annotations

import html
import json
from nicegui import ui

from src.backend.constants import INVERSE_LATEX_MAX_DIMENSION
from src.backend.utilidades.formateadores import formatear_fraccion_str
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_matriz


def sanitizar_valor_latex(val: str) -> str:
    """Sanitiza o marca celda inválida para representación LaTeX."""
    if not val or val == '0':
        return '0'
    ok, _, _ = ValidadorMatriz.parsear_numero_exacto(val)
    if not ok:
        return r"\color{gray}{?}"
    return val


def generar_latex_vista_previa(
    data: list[list[str]], n: int
) -> tuple[str, str | None, list[str]]:
    """Construye las cadenas LaTeX de A y [A | I] para la vista previa."""
    latex_rows = [" & ".join(sanitizar_valor_latex(v) for v in row) for row in data]
    matrix_a_tex = html.escape(
        r"\begin{bmatrix} " + r" \\ ".join(latex_rows) + r" \end{bmatrix}"
    )
    typeset_ids = ['preview-a']
    aug_tex = None

    if n <= 6:
        aug_rows = []
        for i, row in enumerate(data):
            left_str = " & ".join(sanitizar_valor_latex(v) for v in row)
            right_str = " & ".join('1' if i == j else '0' for j in range(n))
            aug_rows.append(f"{left_str} & {right_str}")
        spec = "c" * n + "|" + "c" * n
        aug_tex = html.escape(
            rf"\left[ \begin{{array}}{{{spec}}} "
            + r" \\ ".join(aug_rows)
            + r" \end{array} \right]"
        )
        typeset_ids.append('preview-aug')

    return matrix_a_tex, aug_tex, typeset_ids


def renderizar_resultado_error(vista, result: dict) -> None:
    """Renderiza el mensaje de error y resalta celdas si aplica."""
    with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
        ui.icon('error', size='sm')
        ui.label(result.get('message', 'Error en los datos ingresados.')).classes('font-bold')
    if result.get('error_cell'):
        r, c = result['error_cell']
        vista.square_panel.flash_cell(r, c)
        ui.notify(result.get('message', 'Celda inválida'), type='negative')


def renderizar_resultado_singular(vista, result: dict, n: int) -> None:
    """Renderiza la información de matriz singular y pasos si los hay."""
    with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
        ui.icon('warning', size='sm')
        ui.label('Matriz singular: no tiene inversa').classes('font-bold')

    with ui.column().classes('panel-card p-6 w-full mb-6 gap-3'):
        ui.label('Matriz Singular (det = 0)').classes('text-lg font-bold text-main')
        ui.label(
            'Una matriz cuadrada tiene inversa si y solo si det(A) ≠ 0. '
            'Aquí det(A) = 0, por lo tanto no es posible obtener un pivote en cada columna.'
        ).classes('text-sm text-sec')

        ui.label('Matriz evaluada A:').classes('text-sm font-semibold text-main mt-2')
        if n <= INVERSE_LATEX_MAX_DIMENSION and result.get('matrix_a_latex'):
            ui.html(
                f'<div class="math-scroll-container math-label text-base">$$ A = {result["matrix_a_latex"]} $$</div>'
            )
        elif result.get('matrix_a'):
            ui.html(html_tabla_matriz(result['matrix_a']))

    if getattr(vista, 'ai_panel', None):
        vista.ai_panel.renderizar_sugerencias_en_linea()

    if result.get('steps'):
        vista._render_steps_section(result)


def renderizar_resultado_exitoso(vista, result: dict, n: int) -> None:
    """Renderiza chips, matrices, acciones y comprobaciones de la inversa."""
    badge_id = f"badge-inv-{next(vista._uid_counter)}"
    with ui.row().classes('items-center gap-2 px-4 py-2 badge-success mb-4 w-fit'):
        ui.icon('check_circle', size='sm')
        ui.html(f'<span id="{badge_id}"></span>').classes('font-bold')
    ui.run_javascript(f"typewriterEffect('{badge_id}', 'Matriz invertible', 20);")

    with ui.row().classes('panel-card px-4 py-2 fs-small items-center gap-4 flex-wrap mb-6 w-full'):
        ui.label(f"{n} × {n}").classes('font-bold text-main')
        ui.label(f"det(A) = {result['determinant_str']} ≠ 0").classes('font-semibold text-main')
        ui.label(f"{result['stats']['total']} pasos").classes('text-sec')
        ui.label(f"{result['stats']['intercambios']} intercambios").classes('text-sec')
        ui.label(f"calculado en {result['elapsed_s']:.2f} s").classes('text-sec')

    if getattr(vista, 'ai_panel', None):
        vista.ai_panel.renderizar_sugerencias_en_linea()

    _renderizar_tarjeta_matriz(result, n)
    _renderizar_comprobaciones(result, n)
    vista._render_steps_section(result)
    _renderizar_interpretacion()


def _renderizar_tarjeta_matriz(result: dict, n: int) -> None:
    """Dibuja la tarjeta con la representacion de A y A^-1 y botones de accion."""
    with ui.column().classes('panel-card p-6 w-full mb-6'):
        ui.label('Resultado: A⁻¹').classes('text-lg font-bold text-main mb-4')

        if n <= INVERSE_LATEX_MAX_DIMENSION:
            with ui.row().classes('items-center justify-center gap-6 flex-wrap w-full my-4'):
                ui.html(
                    f'<div class="math-scroll-container math-label text-base">$$ A = {result["matrix_a_latex"]} $$</div>'
                )
                ui.icon('arrow_forward', size='md').classes('text-sec')
                ui.html(
                    f'<div class="math-scroll-container math-label text-base">$$ A^{{-1}} = {result["inverse_latex"]} $$</div>'
                )
        else:
            with ui.row().classes('items-start justify-center gap-8 flex-wrap w-full my-4'):
                with ui.column().classes('items-center layout-fit'):
                    ui.label('A').classes('font-bold text-main mb-2')
                    ui.html(html_tabla_matriz(result['matrix_a']))
                with ui.column().classes('items-center layout-fit'):
                    ui.label('A⁻¹').classes('font-bold text-main mb-2')
                    ui.html(html_tabla_matriz(result['inverse']))

        _agregar_botones_acciones(result, n)

        with ui.expansion('Ver A⁻¹ en decimales (≈4 cifras)', icon='numbers').classes(
            'w-full mt-3 panel-card'
        ).props('header-class="font-bold text-main text-sm"'):
            ui.html(html_tabla_matriz(result['inverse'], decimales=True))

        ui.label(
            'Cada columna j de A⁻¹ es la solución x de A·x = eⱼ (eⱼ = columna j de la identidad).'
        ).classes('text-sec fs-small mt-3')


def _agregar_botones_acciones(result: dict, n: int) -> None:
    """Botones para copiar A^-1 y enviar al solver de sistemas."""
    def copiar_inversa():
        inv = result.get('inverse')
        if not inv:
            return
        lineas = []
        for i in range(n):
            lineas.append("\t".join(formatear_fraccion_str(inv.get(i, j)) for j in range(n)))
        ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(chr(10).join(lineas))});")
        ui.notify('A⁻¹ copiada al portapapeles', type='positive')

    def ir_a_sistemas():
        if n > 10:
            ui.notify(f"Sistemas de ecuaciones admite hasta 10×10; tu matriz es de {n}×{n}.", type='warning')
            return
        data = [[formatear_fraccion_str(result['inverse'].get(r, c)) for c in range(n)] for r in range(n)]
        from src.frontend.componentes.handoff import guardar_matriz, url_handoff
        from src.frontend.navigation import route_of
        token = guardar_matriz('inversa', data)
        ui.navigate.to(url_handoff(route_of('sistemas'), token))

    with ui.row().classes('w-full justify-between items-center mt-4 flex-wrap gap-2'):
        with ui.row().classes('gap-2'):
            ui.button('Copiar A⁻¹', icon='content_copy', on_click=copiar_inversa, color=None).classes('btn-ghost text-xs').props('ripple=false')
            ui.button('Resolver A·x = b con esta A', on_click=ir_a_sistemas, color=None).classes('btn-ghost text-xs').props('ripple=false')


def _renderizar_comprobaciones(result: dict, n: int) -> None:
    """Muestra comprobaciones formales como expansion."""
    with ui.expansion('Comprobaciones formales', icon='verified').classes(
        'w-full mb-6 panel-card'
    ).props('default-opened header-class="font-bold text-main"'):
        with ui.column().classes('w-full gap-4 p-2'):
            for v in result.get('verifications', []):
                with ui.row().classes('w-full justify-between items-center gap-4 flex-wrap'):
                    ui.label(v['title']).classes('font-bold text-main text-sm')
                    badge_cls = 'badge-success' if v['coincide'] else 'badge-error'
                    badge_txt = 'Correcto' if v['coincide'] else 'Incorrecto'
                    ui.badge(badge_txt, color=None).classes(badge_cls)
                if v.get('detail_latex'):
                    ui.html(f'<div class="math-scroll-container math-label text-sm my-1">$$ {v["detail_latex"]} $$</div>')
            if n > INVERSE_LATEX_MAX_DIMENSION:
                ui.label('Verificado con aritmética exacta (fracciones).').classes(
                    'text-sec fs-small italic mt-2'
                )


def _renderizar_interpretacion() -> None:
    """Bloque explicativo didactico."""
    with ui.expansion('¿Cómo interpretar este resultado?', icon='help_outline').classes(
        'w-full mt-6 panel-card'
    ).props('header-class="font-bold text-main"'):
        ui.label(
            'A⁻¹ cumple A·A⁻¹ = A⁻¹·A = I. Existe solo si det(A) ≠ 0. '
            'Todos los valores son exactos (fracciones). (Aᵀ)⁻¹ = (A⁻¹)ᵀ.'
        ).classes('text-sec text-sm p-3')
