from nicegui import ui

class CalculatorPanel:
    def __init__(self):
        # Símbolos para modo Matriz: solo números y operadores básicos para fracciones/negativos
        self.symbols_matrix = [
            '7', '8', '9', '/',
            '4', '5', '6', '-',
            '1', '2', '3', '.',
            '+', '0', '±', 'C'
        ]
        
        # Símbolos para modo Ecuaciones: variables y operadores adicionales
        self.symbols_equations = [
            '7', '8', '9', '+', '-',
            '4', '5', '6', 'w', '/',
            '1', '2', '3', 'x', 'y',
            '0', '.', '=', 'z', 'C'
        ]

    def inject_scripts(self):
        ui.add_head_html('<script src="/assets/js/calculadora.js" defer></script>')

    def _keypad_matriz(self):
        with ui.grid(columns=4).classes('w-full gap-4'):
            for sym in self.symbols_matrix:
                if sym:
                    classes = 'btn-neo-calc w-full h-14 p-0 text-xl font-bold ' + ('text-main' if sym != 'C' else '')
                    btn = ui.button(sym, on_click=lambda s=sym: ui.run_javascript(f"if(window.scalaris && window.scalaris.calculadora) window.scalaris.calculadora.insertarSimbolo('{s}')"), color=None).classes(classes).props('ripple=false flat')
                    if sym == 'C': btn.style('color: var(--error) !important')
                else:
                    ui.label('').classes('w-full h-14') # Espacio en blanco

    def _keypad_ecuaciones(self):
        with ui.grid(columns=5).classes('w-full gap-3'):
            for sym in self.symbols_equations:
                if sym:
                    classes = 'btn-neo-calc w-full h-12 p-0 text-lg font-bold ' + ('text-main' if sym != 'C' else '')
                    btn = ui.button(sym, on_click=lambda s=sym: ui.run_javascript(f"if(window.scalaris && window.scalaris.calculadora) window.scalaris.calculadora.insertarSimbolo('{s}')"), color=None).classes(classes).props('ripple=false flat')
                    if sym == 'C': btn.style('color: var(--error) !important')
                else:
                    ui.label('').classes('w-full h-12')

    def build(self, mode_tabs=None):
        with ui.column().classes('w-full h-full p-6 flex flex-col justify-between panel-card'):
            ui.label('Calculadora').classes('text-main font-bold mb-4 text-center w-full text-lg')
            
            if mode_tabs is not None:
                with ui.tab_panels(mode_tabs, value='Matriz').classes('w-full flex-1 bg-transparent p-0 overflow-hidden').props('animated transition-prev="slide-right" transition-next="slide-left"'):
                    with ui.tab_panel('Matriz').classes('p-0 h-full flex flex-col justify-center'):
                        self._keypad_matriz()
                    with ui.tab_panel('Ecuaciones').classes('p-0 h-full flex flex-col justify-center'):
                        self._keypad_ecuaciones()
            else:
                with ui.column().classes('w-full flex-1 justify-center'):
                    self._keypad_matriz()

