"""Pruebas de regresión de Fase 5 para Bases, Romanos, Métodos cerrados y Métodos abiertos."""
import asyncio

from nicegui import ui

from src.frontend.controladores.raices.compartido.exploracion.exploracion_raices import presentar_candidato
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from src.frontend.controladores.raices.regla_falsa.presentacion.presentacion_ampliada import datos_criterio
from src.frontend.presentacion.sugerencias import sugerir
from tests.comun_construccion_vistas import construir_pagina
from tests.test_metodos_cerrados_calculo import montar_vista


def _verificar_estructura_y_h1(cliente) -> None:
    encabezados = [el for el in cliente.elements.values() if el._props.get("tag") == "h1"]
    assert len(encabezados) == 1
    clases = " ".join(" ".join(el._classes) for el in cliente.elements.values())
    assert "disposicion-herramienta" in clases
    assert "disposicion-captura-fila" in clases
    assert "disposicion-resultados" in clases


def test_cuatro_utilidades_tienen_h1_y_disposicion_debajo_de_captura(monkeypatch):
    """Bases, Romanos, Métodos cerrados y Abiertos usan h1 real y filas de captura/resultados."""
    for herramienta in ("bases", "romanos", "metodos_abiertos"):
        async def _comprobar(_, cliente):
            _verificar_estructura_y_h1(cliente)

        asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))

    async def _comprobar_cerrados():
        async with montar_vista(monkeypatch, BISECCION) as (_, cliente):
            _verificar_estructura_y_h1(cliente)

    asyncio.run(_comprobar_cerrados())


def test_bases_rotulos_referencia_botones_y_portapapeles(monkeypatch):
    """Bases muestra Base origen/destino, dígitos válidos, botones 44 px y errores de portapapeles."""
    async def _comprobar(vista, cliente):
        etiquetas = [el.text for el in cliente.elements.values() if isinstance(el, ui.label)]
        assert "Base origen" in etiquetas
        assert "Base destino" in etiquetas
        assert "0–9" in vista.etiqueta_referencia_digitos.text
        vista.pestanas_origen.set_value("hexadecimal")
        assert "A–F" in vista.etiqueta_referencia_digitos.text

        botones_tarjeta = [
            el for el in cliente.elements.values()
            if isinstance(el, ui.button) and el._props.get("aria-label") in ("Usar como entrada", "Copiar")
        ]
        assert len(botones_tarjeta) == 8
        assert all("boton-icono" in el._classes and "w-8" not in el._classes for el in botones_tarjeta)

        async def _js_denegado(_codigo, **_kwargs):
            return {"estado": "error"}

        monkeypatch.setattr(ui, "run_javascript", _js_denegado)
        monkeypatch.setattr(ui, "notify", lambda *_a, **_k: None)
        await vista._pegar_portapapeles()
        assert "portapapeles" in vista.etiqueta_error.text.lower()

    asyncio.run(construir_pagina(monkeypatch, "bases", _comprobar))


def test_romanos_error_unico_y_controles_sin_mayusculas_forzadas(monkeypatch):
    """Romanos señala el campo con aria-describedby sin duplicar error-message."""
    async def _comprobar(vista, cliente):
        vista.entrada_a.set_value("IIII")
        vista.entrada_b.set_value("I")
        await vista._operar_desde_control()
        assert vista.etiqueta_error.text
        assert vista.entrada_a._props.get("error") is True
        assert "error-message" not in vista.entrada_a._props
        assert vista.entrada_a._props.get("aria-describedby") == vista.etiqueta_error.html_id

        etiquetas = [el for el in cliente.elements.values() if isinstance(el, ui.label)]
        assert not any("uppercase" in el._classes for el in etiquetas)

    asyncio.run(construir_pagina(monkeypatch, "romanos", _comprobar))


def test_metodos_cerrados_candidatos_raiz_exacta_alerta_y_glosa(monkeypatch):
    """Candidatos evitan ruido binario, raíz exacta se distingue y Glosa recibe señales."""
    presentado = presentar_candidato({
        "tipo": "cruce", "intervalo": (0.90000000000000058, 1.1),
        "abscisa": None, "valor": None,
    })
    assert presentado["intervalo"] == "[0.9, 1.1]"

    criterio = dict(datos_criterio(
        {"criterio": {"tipo": "residuo", "parametro": 1e-6}, "umbral": 1e-6,
         "metrica_final": 0.0, "cumplimiento": "NO_CUMPLIDO"},
        {"estado": "EXITO", "motivo_parada": "raiz_exacta"},
    ))
    assert criterio["Cumplimiento"] == "Raíz exacta evaluada (residuo 0)"

    async def _comprobar():
        async with montar_vista(monkeypatch, BISECCION) as (vista, _):
            senales = vista.obtener_senales_ia()
            assert senales.herramienta == "biseccion"
            assert sugerir(senales, limite=3)

    asyncio.run(_comprobar())


def test_regla_falsa_error_expone_role_alert(monkeypatch):
    """Cuando Regla falsa falla en la evaluación, el mensaje lleva role=alert."""
    async def _comprobar():
        async with montar_vista(monkeypatch, REGLA_FALSA) as (vista, _):
            vista.cargar_captura({"expresion": "x^2 + 1", "extremo_izquierdo": "1", "extremo_derecho": "2"})
            await vista.resolver()
            alertas = [
                el for el in vista.contenedor_resultados.descendants()
                if isinstance(el, ui.label) and el._props.get("role") == "alert"
            ]
            assert alertas

    asyncio.run(_comprobar())


def test_metodos_abiertos_paginacion_espanol_ejemplos_titulo_y_glosa(monkeypatch):
    """Métodos abiertos localiza paginación, reinicia Ejemplos, cambia título y conecta Glosa."""
    async def _comprobar(vista, _):
        assert vista.panel_ia is not None
        assert vista.obtener_contexto_ia().herramienta == "metodos_abiertos"
        assert sugerir(vista.obtener_senales_ia(), limite=3)

        vista.selector_ejemplos.set_value("n1")
        assert vista.expresion.value == "x^3 - x - 2"
        vista.metodo.set_value("secante")
        assert vista.selector_ejemplos.value is None

        vista.x0.set_value("1")
        vista.x1.set_value("2")
        vista.calcular()
        assert vista.previa.titulo.text == "Gráfica del resultado"
        assert vista.tabla_iteraciones._props.get("rows-per-page-label") == "Filas por página:"
        assert "filas seleccionadas" in vista.tabla_iteraciones._props.get(":selected-rows-label", "")

        vista.invalidar_resultado()
        assert vista.previa.titulo.text == "Gráfica previa"

    asyncio.run(construir_pagina(monkeypatch, "metodos_abiertos", _comprobar))
