"""Integración de captura, resultado vigente y PDF con el verificador polinómico."""
import asyncio

import pytest
from nicegui import run, ui

from src.backend.resolutores.operaciones_vectores.espacios_vectoriales import limites_espacio_vectorial
from src.frontend.componentes.exportacion_pdf.montaje.secuencia import preparar_secuencia
from src.frontend.controladores.algebra.operaciones_vectores.ejemplos_espacio_vectorial import EJEMPLOS_OPERACIONES
from src.frontend.controladores.exportacion_pdf.documento.documento import generar_pdf
from src.frontend.nucleo.textos.textos_espacio_vectorial import MODO_PERSONALIZADO
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina
from tests.comun_exportacion_pdf import PORTADA, crear_captura

_HERRAMIENTA = "espacios_subespacios"


@pytest.fixture
def _abrir_vista(monkeypatch):
    monkeypatch.setitem(VISTAS_RUTAS, _HERRAMIENTA, (
        "algebra.operaciones_vectores.vista_espacios_subespacios", "VistaEspaciosSubespacios",
    ))

    def _comprobar(escenario):
        asyncio.run(construir_pagina(monkeypatch, _HERRAMIENTA, escenario, {"modo": MODO_PERSONALIZADO}))

    return _comprobar


def _cargar(vista, indice):
    vista.captura._selector_ejemplo.set_value(tuple(EJEMPLOS_OPERACIONES)[indice])
    vista.captura.cargar_ejemplo()


@pytest.mark.parametrize(("indice", "codigo", "cantidad"), [
    (0, "ESPACIO_VECTORIAL", 10),
    (1, "ESPACIO_VECTORIAL", 10),
    (2, "NO_ESPACIO_VECTORIAL", 10),
    (3, "NO_ESPACIO_VECTORIAL", 10),
    (4, "CONJUNTO_VACIO", 0),
])
def test_ejemplos_personalizados(_abrir_vista, indice, codigo, cantidad):
    """Analiza cada ejemplo desde la ruta y conserva el veredicto al alternar el formato lineal."""
    async def _comprobar(vista, _cliente):
        _cargar(vista, indice)
        await vista.analizar()
        resultado = vista.ultimo_resultado
        assert resultado["codigo"] == codigo
        assert len(resultado["comprobaciones"]) == cantidad
        assert vista.obtener_contexto_ia().resultado["codigo"] == codigo
        assert "es_subespacio" not in resultado
        if indice == 1:
            vista.captura.conjunto.selector.set_value("matriz")
            await vista.analizar()
            assert vista.ultimo_resultado == resultado

    _abrir_vista(_comprobar)


def test_localiza_termino_invalido_y_reintenta(_abrir_vista):
    """Retiene el borrador inválido y permite corregir la posición señalada."""
    async def _comprobar(vista, _cliente):
        _cargar(vista, 0)
        coeficiente, exponentes = vista.captura.campos_entrada()[1:3]
        exponentes.set_value("9 1")
        await vista.analizar()
        diagnostico = vista.ultimo_resultado["diagnostico"]
        assert (diagnostico["campo"], diagnostico["coordenada"], diagnostico["termino"]) == ("suma", 1, 1)
        assert coeficiente.props.get("aria-invalid") == "true"
        assert exponentes.value == "9 1"
        assert vista.actualizar_exportacion_pdf is None
        exponentes.set_value("1 0")
        await vista.analizar()
        assert vista.ultimo_resultado["es_espacio_vectorial"] is True
        assert not coeficiente.props.get("aria-invalid")

    _abrir_vista(_comprobar)


def test_limite_y_reintento_mantienen_estados_distintos(monkeypatch, _abrir_vista):
    """Distingue los axiomas sin verificar de una violación certificada."""
    async def _comprobar(vista, _cliente):
        _cargar(vista, 3)
        with monkeypatch.context() as presupuesto:
            presupuesto.setattr(limites_espacio_vectorial, "MAXIMO_OPERACIONES", 0)
            await vista.analizar()
        assert vista.ultimo_resultado["codigo"] == "LIMITE_ARITMETICO"
        assert any(paso.etiqueta_tipo == "No verificado" for paso in vista.reproductor_pasos.pasos)
        await vista.analizar()
        assert vista.ultimo_resultado["codigo"] == "NO_ESPACIO_VECTORIAL"
        paso = vista.reproductor_pasos.pasos[2]
        assert paso.etiqueta_tipo == "No cumple"
        assert "residuo" in paso.meta_explicar["detalle"].lower()

    _abrir_vista(_comprobar)


def test_cambio_de_modo_descarta_el_calculo_y_conserva_el_borrador(monkeypatch, _abrir_vista):
    """Descarta una respuesta antigua incluso al volver a la misma captura."""
    async def _comprobar(vista, _cliente):
        _cargar(vista, 1)
        borrador = vista.captura.obtener()
        inicio, liberar = asyncio.Event(), asyncio.Event()

        async def _ejecutar(calcular, captura):
            inicio.set()
            await liberar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", _ejecutar)
        tarea = asyncio.create_task(vista.analizar())
        await inicio.wait()
        vista.selector_modo.set_value("generadores")
        vista.selector_modo.set_value(MODO_PERSONALIZADO)
        liberar.set()
        await tarea
        assert vista.ultimo_resultado is None
        assert vista.captura.obtener() == borrador
        await vista.analizar()
        assert vista.ultimo_resultado["vector_cero"] == (0, 1)

    _abrir_vista(_comprobar)


def test_pdf_personalizado_exporta_pruebas_sin_mover_el_reproductor(_abrir_vista):
    """Monta certificados para PDF y conserva el paso visible del reproductor."""
    async def _comprobar(vista, _cliente):
        _cargar(vista, 3)
        await vista.analizar()
        reproductor = vista.reproductor_pasos
        reproductor.ir_a(2)
        control = vista.actualizar_exportacion_pdf.__self__
        claves = [f"{_HERRAMIENTA}-resumen", f"{_HERRAMIENTA}-axiomas"]
        with preparar_secuencia(_HERRAMIENTA, control.enlace) as temporal:
            claves.extend(region._props["data-pdf-captura"] for region in temporal)
            textos = [elemento.text for elemento in temporal.descendants() if isinstance(elemento, ui.label)]
            assert any(texto.startswith("Residuo 1 = ") and texto != "Residuo 1 = 0" for texto in textos)
        assert f"{_HERRAMIENTA}-pruebas" in claves
        assert reproductor.indice_actual == 2
        capturas = [crear_captura(clave) for clave in claves]
        documento, _ = generar_pdf(_HERRAMIENTA, PORTADA, control.resultado, capturas)
        assert documento.startswith(b"%PDF")

    _abrir_vista(_comprobar)
