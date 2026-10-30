"""Montaje diferido y agrupación de detalles con controles NiceGUI reales."""
import asyncio
from unittest.mock import Mock

from nicegui import Client, core, ui

from src.frontend.componentes.desarrollo_comprobacion import mostrar_desarrollo
from src.frontend.componentes import desarrollo_comprobacion as desarrollo


def _producto(dimension):
    """Construye fórmulas de prueba sin ejecutar el cálculo del dominio."""
    celdas = [{"descripcion": f"Fila {fila}, columna {columna}",
               "explicacion": "Detalle", "detalle_latex": f"C_{{{fila},{columna}}}=1"}
              for fila in range(1, dimension + 1) for columna in range(1, dimension + 1)]
    return [{"descripcion": "Propiedad por comprobar: AA^{-1}=I", "detalle_latex": "AA^{-1}=I"},
            *celdas, {"descripcion": "Comprobacion exacta de AA^{-1}=I: coincide",
                      "detalle_latex": r"\begin{bmatrix}1\end{bmatrix}=I"}]


def test_producto_grande_difiere_celdas_y_compone_un_bloque_por_fila(monkeypatch):
    """Una traza de 2500 celdas monta dos fórmulas iniciales y una por fila abierta."""
    async def comprobar():
        """Abre y cierra expansiones para comprobar su carga única."""
        monkeypatch.setattr(core, "script_mode", False)
        monkeypatch.setattr(ui, "run_javascript", lambda codigo: None)
        cliente = Client(ui.page("/prueba_desarrollo"))
        try:
            with cliente:
                mostrar_desarrollo(_producto(50))
                assert len(_formulas(cliente)) == 2
                expansion = next(elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.expansion))
                expansion.set_value(True)
                filas = [elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.expansion) and elemento.text.startswith("Fila ")]
                assert len(filas) == 50 and len(_formulas(cliente)) == 2
                filas[0].set_value(True)
                assert len(_formulas(cliente)) == 3
                formula = _formulas(cliente)[-1].content
                assert r"\begin{array}{l}" in formula and formula.count("C_{1,") == 50
                filas[0].set_value(False)
                filas[0].set_value(True)
                assert len(_formulas(cliente)) == 3
        finally:
            cliente.delete()
    asyncio.run(comprobar())


def _formulas(cliente):
    """Devuelve únicamente los bloques MathJax montados en el cliente."""
    return [elemento for elemento in cliente.elements.values()
            if isinstance(elemento, ui.html) and "matematicas-desplazamiento" in elemento.content]


def test_producto_conserva_aclaracion_final_distinta(monkeypatch):
    """Una aclaración final del dominio sigue visible y escapada en el modo producto."""
    contenido = Mock()
    monkeypatch.setattr(ui, "html", contenido)
    monkeypatch.setattr(ui, "label", Mock())
    monkeypatch.setattr(desarrollo, "renderizar_latex", Mock())
    monkeypatch.setattr(desarrollo, "_crear_detalle_diferido", Mock())
    traza = _producto(1)
    traza[-1]["explicacion"] = "Por unicidad, (A^{-1})^T es la inversa. <script>"
    mostrar_desarrollo(traza)
    assert any("Por unicidad, (A<sup>-1</sup>)ᵀ es la inversa. &lt;script&gt;" == llamada.args[0]
               for llamada in contenido.call_args_list)


def test_modo_plano_normaliza_y_no_repite_explicacion(monkeypatch):
    """El resumen plano escapa datos y carga los pasos intermedios solo al abrirse."""
    async def comprobar():
        """Comprueba contenido seguro y diferido en una traza ajena a productos."""
        monkeypatch.setattr(core, "script_mode", False)
        monkeypatch.setattr(ui, "run_javascript", lambda codigo: None)
        cliente = Client(ui.page("/prueba_desarrollo_plano"))
        paso = {"descripcion": "A^{-1}", "explicacion": "  A^{-1}  ", "detalle_latex": "A"}
        try:
            with cliente:
                mostrar_desarrollo([paso, {"descripcion": "<script>intermedio</script>"}, paso])
                html = " ".join(elemento.content for elemento in cliente.elements.values() if isinstance(elemento, ui.html))
                assert html.count("<sup>-1</sup>") == 2 and "intermedio" not in html
                expansion = next(elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.expansion))
                expansion.set_value(True)
                html = " ".join(elemento.content for elemento in cliente.elements.values() if isinstance(elemento, ui.html))
                assert "&lt;script&gt;intermedio&lt;/script&gt;" in html and "<script>" not in html
        finally:
            cliente.delete()
    asyncio.run(comprobar())
