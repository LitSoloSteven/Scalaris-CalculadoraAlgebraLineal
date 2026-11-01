"""Integración y cancelación del procedimiento real de aplicación en NiceGUI."""
import asyncio

import pytest
from nicegui import ui

from src.frontend import textos_transformaciones as textos
from src.frontend.vistas.operaciones_matrices._ejemplos_aplicacion_transformacion import EJEMPLOS_APLICACION
from tests.comun_construccion_vistas import construir_pagina


def test_navegacion_actualiza_formula_y_componente_sin_recrear_graficas(monkeypatch):
    """Aplicación y comprobación navegan sobre las mismas escenas y no activan Glosa."""
    async def comprobar(vista, cliente):
        """Recorre cada paso e inspecciona cuerpo, aviso, gráficos y controles reales."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        await vista._analizar(vista.boton_calcular)
        reproductor = vista.reproductor_aplicacion
        graficas = [elemento for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.plotly)]
        assert reproductor is not None and vista.reproductor_pasos is reproductor
        assert reproductor.al_explicar is not None and len(vista.historial) == 1
        for indice in range(len(reproductor.pasos)):
            reproductor.ir_a(indice)
            assert reproductor.etiqueta_indice.text == f"Paso {indice + 1} de 7"
            assert not any(grafica.is_deleted for grafica in graficas)
            assert any(isinstance(elemento, ui.button) for elemento in reproductor.contenedor_glosa.descendants())
        reproductor.ir_a(1)
        etiquetas = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any("y_1 = 4/3" in texto for texto in etiquetas)
        assert vista.obtener_contexto_ia().resultado["verificacion"] is True
        assert reproductor.deslizador._props["aria-label"] == "Paso actual"
        assert reproductor.boton_reproducir._props["aria-label"] == "Reproducción automática"
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_sincronizacion_usa_region_unica_para_cada_resultado(monkeypatch):
    """Las órdenes tardías de una aplicación no encuentran la región de una aplicación nueva."""
    async def comprobar(vista, cliente):
        """Registra el transporte real y comprueba su destino después de montar y navegar."""
        llamadas, enviar = [], ui.run_javascript

        def registrar(codigo, **opciones):
            """Conserva el transporte simulado y registra las órdenes dirigidas al DOM."""
            llamadas.append(codigo)
            return enviar(codigo, **opciones)

        monkeypatch.setattr(ui, "run_javascript", registrar)
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        await vista._analizar(vista.boton_calcular)
        regiones = []
        for _ in range(2):
            vista.reproductor_aplicacion.ir_a(1)
            region = next(elemento for elemento in vista.contenedor_resultados.descendants()
                          if "data-procedimiento-aplicacion" in elemento._props)
            regiones.append(region)
            assert any(f'aplicacionTransformacion.actualizar("{region.html_id}", 0)' in llamada for llamada in llamadas)
            await vista._analizar(vista.boton_calcular)
        assert regiones[0].is_deleted and regiones[0].html_id != regiones[1].html_id
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_seleccionar_de_nuevo_el_paso_actual_no_reinicia_el_cuerpo(monkeypatch):
    """Un clic repetido en el índice conserva los elementos y el temporizador del paso."""
    async def comprobar(vista, cliente):
        """Repite el mismo destino y compara los elementos del cuerpo antes y después."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        await vista._analizar(vista.boton_calcular)
        reproductor = vista.reproductor_aplicacion
        reproductor.ir_a(1)
        anteriores = list(reproductor.contenedor_cuerpo.descendants())
        temporizador = reproductor.temporizador
        reproductor.ir_a(1)
        assert list(reproductor.contenedor_cuerpo.descendants()) == anteriores
        assert reproductor.temporizador is temporizador
        assert all(not elemento.is_deleted for elemento in anteriores)
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


@pytest.mark.parametrize("cambio", ["vector", "matriz", "modo", "tipo", "dimension", "limpieza", "cliente", "panel"])
def test_editar_y_desmontar_cancelan_reproduccion_inmediatamente(monkeypatch, cambio):
    """La reproducción activa pierde su temporizador y no publica un paso antiguo."""
    async def comprobar(vista, cliente):
        """Activa el reproductor real y ejerce las rutas de invalidación y desmontaje."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        await vista._analizar(vista.boton_calcular)
        reproductor = vista.reproductor_aplicacion
        reproductor._alternar_reproduccion()
        temporizador = reproductor.temporizador
        assert temporizador.active
        acciones = {
            "vector": lambda: vista.entradas_vector_original[0].set_value("7"),
            "matriz": lambda: vista.entradas_coeficientes[0][0].set_value("7"),
            "modo": lambda: vista.selector_modo.set_value(textos.MODO_ANALISIS),
            "tipo": lambda: vista.selector_tipo_objeto.set_value("punto"),
            "dimension": lambda: vista._aplicar_dimension("filas", 3),
            "limpieza": vista.limpiar_todo,
            "cliente": vista._desmontar_modelo,
            "panel": vista.contenedor_resultados.delete,
        }
        acciones[cambio]()
        assert temporizador.is_deleted
        if cambio != "panel":
            assert vista.reproductor_aplicacion is None
        anterior = reproductor.indice_actual
        if cambio != "cliente":
            reproductor._avanzar()
            assert reproductor.indice_actual == anterior
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


@pytest.mark.parametrize("dimension", [1, 4, 8])
def test_sin_grafica_conserva_desarrollo_completo_y_aviso_correcto(monkeypatch, dimension):
    """El reproductor sigue disponible sin prometer una cruz cuando no existe gráfica."""
    async def comprobar(vista, cliente):
        """Comprueba dimensiones no gráficas en el procedimiento de un resultado real."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[4])
        vista._aplicar_dimension("filas", dimension)
        await vista._analizar(vista.boton_calcular)
        reproductor = vista.reproductor_aplicacion
        reproductor.ir_a(1)
        assert len(reproductor.pasos) == 2 * dimension + 3
        etiquetas = [elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert any("fila resaltada" in texto for texto in etiquetas)
        assert not any("la cruz señala" in texto for texto in etiquetas)
        reproductor.ir_a(len(reproductor.pasos) - 1)
        assert "coincide" in reproductor.pasos[-1].descripcion
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_reproducir_termina_pausa_y_velocidad_no_dejan_temporizadores_huerfanos(monkeypatch):
    """Los controles comunes recorren la secuencia y cancelan cada espera sustituida."""
    async def comprobar(vista, cliente):
        """Simula ticks sin esperar segundos de lectura ni generar solicitudes de IA."""
        vista._cargar_ejemplo(EJEMPLOS_APLICACION[0])
        await vista._analizar(vista.boton_calcular)
        reproductor = vista.reproductor_aplicacion
        inicial = reproductor.temporizador
        reproductor.velocidad = "Rápida"
        reproductor._actualizar_intervalo()
        reproductor._alternar_reproduccion()
        temporizador = reproductor.temporizador
        assert inicial.is_deleted
        for _ in range(len(reproductor.pasos)):
            reproductor._avanzar()
        assert reproductor.temporizador is temporizador and not temporizador.active
        assert reproductor.indice_actual == len(reproductor.pasos) - 1
        reproductor._alternar_reproduccion()
        assert temporizador.is_deleted
        temporizador = reproductor.temporizador
        assert reproductor.indice_actual == 0 and temporizador.active
        reproductor.pausar()
        assert not temporizador.active
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
