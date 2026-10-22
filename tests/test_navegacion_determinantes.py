"""Integración del catálogo, las rutas compatibles y el estado activo de Determinantes."""
import asyncio
from pathlib import Path
from unittest.mock import Mock

from src.frontend.navegacion import ruta_de
from tests.comun_construccion_vistas import construir_pagina, registrar_paginas


def test_determinantes_tiene_estado_activo_exclusivo(monkeypatch):
    """La captura LU marca su propio enlace y elimina el acceso de desbordamiento."""
    async def comprobar(vista, cliente):
        """Inspecciona la barra real montada por la ruta canónica."""
        enlaces = [elemento for elemento in cliente.elements.values()
                   if "navegacion-elemento" in elemento.classes]
        assert len(enlaces) == 5
        actuales = [elemento for elemento in enlaces if elemento._props.get("aria-current") == "page"]
        assert len(actuales) == 1
        assert actuales[0]._props["href"] == ruta_de("determinantes")
        textos = [str(getattr(elemento, "text", "")) for elemento in cliente.elements.values()]
        assert not any("Más álgebra" in texto for texto in textos)
        assert any("Cofactores" in texto for texto in textos)
        assert "Cofactores o eliminación con pivoteo, con aritmética exacta." in textos
    asyncio.run(construir_pagina(monkeypatch, "determinantes", comprobar))


def test_enlace_anterior_y_ruta_nueva_construyen_la_misma_captura(monkeypatch):
    """El parámetro histórico de matrices continúa abriendo la captura pública LU."""
    from src.frontend import rutas
    from src.frontend.vistas.operaciones_matrices import vista_determinante
    paginas = registrar_paginas(monkeypatch)
    constructor = Mock()
    monkeypatch.setattr(vista_determinante, "VistaDeterminante", constructor)
    monkeypatch.setattr(rutas, "configurar_tema", Mock())
    paginas[ruta_de("matrices")](operacion="determinante")
    paginas[ruta_de("determinantes")]()
    assert constructor.call_count == 2
    assert constructor.return_value.construir.call_count == 2


def test_componente_y_referencias_de_mas_algebra_retirados():
    """Ninguna vista conserva el componente ni las etiquetas del menú retirado."""
    raiz = Path("src/frontend")
    assert not (raiz / "componentes/accesos_algebra.py").exists()
    for ruta in raiz.rglob("*.py"):
        contenido = ruta.read_text(encoding="utf-8")
        assert "accesos_algebra" not in contenido
        assert "Más álgebra" not in contenido
        assert "Más herramientas de álgebra" not in contenido


def test_visita_directa_se_registra_al_conectar(monkeypatch):
    """La construcción previa al socket no pierde la herramienta del historial."""
    from nicegui import Client, core, ui
    from src.frontend.componentes.barra_navegacion import _registrar_navegacion_reciente
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba_historial_determinantes"))
    enviar = Mock()
    monkeypatch.setattr(cliente, "run_javascript", enviar)
    with cliente:
        _registrar_navegacion_reciente(ruta_de("determinantes"))
        enviar.assert_not_called()
        assert len(cliente.connect_handlers) == 1
        cliente.connect_handlers[0]()
        assert 'registrar?.("determinantes")' in enviar.call_args_list[0].args[0]
        assert "centrarActivo" in enviar.call_args_list[1].args[0]
    cliente.delete()
