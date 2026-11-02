"""Secuencia documental completa e invalidación de exportaciones de Av."""
import asyncio

import pytest
from nicegui import ui

from src.frontend.componentes.exportacion_pdf import boton as modulo_boton
from src.frontend.componentes.exportacion_pdf.secuencia import preparar_secuencia
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_exportacion_pdf import PORTADA, crear_captura


@pytest.mark.parametrize("filas,columnas,graficas", [(2, 2, 1), (3, 2, 2), (1, 4, 0), (8, 8, 0)])
def test_documento_conserva_captura_pasos_y_comprobaciones_sin_mover_seleccion(monkeypatch, filas, columnas, graficas):
    """Exportar incluye cada componente y verificación sin navegar el reproductor."""
    async def comprobar(vista, cliente):
        """Monta el documento real y comprueba selección, elementos y fórmulas completas."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        vista._aplicar_dimension("filas", filas)
        vista._aplicar_dimension("columnas", columnas)
        vista.selector_tipo_objeto.set_value("punto")
        await vista._analizar(vista.boton_calcular)
        control = vista.actualizar_exportacion_pdf.__self__
        reproductor = vista.reproductor_aplicacion
        reproductor.ir_a(1)
        elementos = set(cliente.elements)
        aviso = next(elemento for elemento in vista.contenedor_resultados.descendants()
                     if "data-componente-actual" in elemento._props)
        texto = aviso.text
        assert control.enlace.entrada_documental()["tipo_objeto"] == "punto"
        assert len(control.enlace.entrada_documental()["vector_original"]) == columnas
        with preparar_secuencia("transformaciones", control.enlace) as temporal:
            regiones = [elemento for elemento in temporal.descendants() if "data-pdf-captura" in elemento._props]
            assert [elemento._props["data-pdf-captura"] for elemento in regiones] == [
                "transformaciones-entrada", "transformaciones-paso-1", "transformaciones-verificaciones"]
            formulas = [elemento.content for elemento in temporal.descendants() if isinstance(elemento, ui.html)]
            assert len(formulas) >= 2 * filas + 2
            assert reproductor.indice_actual == 1 and aviso.text == texto
            assert len(regiones) + 1 + graficas <= 12
        assert temporal.is_deleted and set(cliente.elements) == elementos
        assert control.enlace.vigente(vista.ultimo_resultado)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def _cambiar_captura(vista, control, cambio):
    if cambio == "vector":
        vista.entradas_vector_original[0].set_value("7")
    elif cambio == "tipo":
        vista.selector_tipo_objeto.set_value("punto")
    elif cambio == "modo":
        vista.selector_modo.set_value("analisis")
    elif cambio == "dimension":
        vista._aplicar_dimension("columnas", 3)
    elif cambio == "revision":
        vista._revision_captura += 1
    elif cambio == "cerrar":
        control.dialogo.dialogo.close()


@pytest.mark.parametrize("cambio", ["ninguno", "vector", "tipo", "modo", "dimension", "revision", "cerrar"])
@pytest.mark.parametrize("etapa", ["captura", "generacion"])
def test_exportacion_descarta_trabajo_tras_edicion_o_cierre(monkeypatch, cambio, etapa):
    """El PDF solo se descarga si tanto captura como generación conservan el testigo."""
    async def comprobar(vista, cliente):
        """Conserva el generador real y aísla las imágenes y la descarga de navegador."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        await vista._analizar(vista.boton_calcular)
        control = vista.actualizar_exportacion_pdf.__self__
        control.abrir()
        for clave, valor in PORTADA.items():
            control.dialogo.campos[clave].set_value(valor)
        descargas = []
        monkeypatch.setattr(ui, "download", lambda documento, **opciones: descargas.append(documento))

        async def capturar(identificador):
            """Reproduce una carrera de edición mientras se capturan regiones."""
            if etapa == "captura":
                _cambiar_captura(vista, control, cambio)
            return [crear_captura("transformaciones-resumen")]

        async def trabajar(funcion, *argumentos):
            """Reproduce una carrera durante la construcción del documento real."""
            if etapa == "generacion":
                _cambiar_captura(vista, control, cambio)
            return funcion(*argumentos)

        monkeypatch.setattr(modulo_boton, "capturar_regiones", capturar)
        monkeypatch.setattr(modulo_boton.run, "io_bound", trabajar)
        await control.generar()
        assert len(descargas) == int(cambio == "ninguno")
        assert all(documento.startswith(b"%PDF-") for documento in descargas)
        assert not control.ocupado
        assert not any("data-pdf-secuencia" in elemento._props for elemento in vista.contenedor_resultados.descendants())
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
