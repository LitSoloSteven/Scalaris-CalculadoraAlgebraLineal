"""Reproductor interactivo reutilizable para secuencias didacticas."""

from __future__ import annotations

import html
import itertools
import json
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Any

from nicegui import ui

from src.frontend.componentes.reproductor_pasos.catalogo import (
    intervalo_lectura,
    html_sugerencia_tipo,
)
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.componentes.reproductor_pasos.vista import construir_vista
from .opciones import OpcionesReproductor
from .temporizacion import reiniciar_espera
from .textos import formatear_descripcion_html, limpiar_latex_plano


_CONTADOR_EXPLICACION = itertools.count()


class ReproductorPasos:
    """Gestiona navegacion, renderizado y reproduccion automatica de pasos."""

    sin_movimiento = False

    def __init__(self, pasos: Sequence[PasoReproductor], grupos: Sequence[GrupoReproductor], renderizar_cuerpo: Callable[[PasoReproductor, Any], None], identificador: str, opciones: OpcionesReproductor | None = None) -> None:
        """Guarda los pasos y acciones que controlan el reproductor."""
        configuracion = opciones if opciones is not None else {}
        titulo = configuracion.get('titulo', "Procedimiento paso a paso")
        lineas_ayuda = configuracion.get('lineas_ayuda', ())
        tipos_leyenda = configuracion.get('tipos_leyenda', ())
        al_explicar = configuracion.get('al_explicar', None)
        esta_ocupado = configuracion.get('esta_ocupado', lambda: False)
        self.pasos = tuple(pasos)
        self.grupos = tuple(grupos)
        self.renderizar_cuerpo = renderizar_cuerpo
        self.identificador = identificador
        self.id_tarjeta = f"pasos-tarjeta-{identificador}"
        self.titulo = titulo
        self.lineas_ayuda = tuple(lineas_ayuda)
        self.tipos_leyenda = tuple(tipos_leyenda)
        self.al_explicar = al_explicar
        self.esta_ocupado = esta_ocupado
        self.sin_movimiento = configuracion.get("sin_movimiento", False)
        self.indice_actual = 0
        self.velocidad = "Normal"
        self.temporizador = None
        self.deslizador = None
        self.boton_reproducir = None
        self.grupos_cargados: set[int] = set()
        self.tarjeta = None

    def construir(self) -> None:
        """Dibuja la ayuda, la tarjeta del paso y el indice por fases."""
        if not self.pasos:
            return
        self.detener()
        self.grupos_cargados.clear()
        construir_vista(self)

    def detener(self) -> None:
        """Detiene y elimina el temporizador asociado a esta secuencia."""
        if self.temporizador is not None:
            if not self.temporizador.is_deleted:
                self.temporizador.active = False
                self.temporizador.delete()
            self.temporizador = None
        if self.boton_reproducir is not None and not self.boton_reproducir.is_deleted:
            self.boton_reproducir.props('icon=play_arrow')

    def pausar(self) -> None:
        """Pausa la reproducción conservando el temporizador para poder reanudarla."""
        self._pausar_reproduccion()

    def ir_a(self, indice: int, *, autoreproduccion: bool = False) -> None:
        """Navega a un paso y actualiza sus metadatos, explicacion y cuerpo."""
        if not self.pasos or self.tarjeta is None or self.tarjeta.is_deleted:
            return
        self.indice_actual = max(0, min(indice, len(self.pasos) - 1))
        paso = self.pasos[self.indice_actual]
        self._actualizar_intervalo(reiniciar=not autoreproduccion)
        self._actualizar_encabezado(paso)
        self._actualizar_explicacion(paso, autoreproduccion)
        self._actualizar_glosa(paso)
        self.contenedor_cuerpo.clear()
        self.renderizar_cuerpo(paso, self.contenedor_cuerpo)
        if not self.sin_movimiento:
            ui.run_javascript(
                f"if(window.scalaris && window.scalaris.pasos) window.scalaris.pasos.destellar({json.dumps(self.id_tarjeta)});"
            )
        if autoreproduccion and self.indice_actual == len(self.pasos) - 1:
            self._pausar_reproduccion()

    def _actualizar_encabezado(self, paso: PasoReproductor) -> None:
        """Actualiza indice, chip, fase y barra de progreso."""
        self.etiqueta_indice.set_text(f"Paso {self.indice_actual + 1} de {len(self.pasos)}")
        self.etiqueta_tipo.set_content(html_sugerencia_tipo(paso.tipo, paso.etiqueta_tipo))
        if hasattr(self, "descripcion"):
            self.descripcion.set_content(formatear_descripcion_html(paso.descripcion))
        if 0 <= paso.indice_grupo < len(self.grupos):
            self.fase.set_text(self.grupos[paso.indice_grupo].titulo)
        else:
            self.fase.set_text("")
        self.progreso.set_value((self.indice_actual + 1) / len(self.pasos))
        if self.deslizador is not None and self.deslizador.value != self.indice_actual:
            self.deslizador.value = self.indice_actual

    def _actualizar_explicacion(self, paso: PasoReproductor, autoreproduccion: bool) -> None:
        """Muestra la explicacion, con escritura animada fuera de autoplay."""
        texto = paso.explicacion
        contenido = formatear_descripcion_html(texto)
        descripcion = formatear_descripcion_html(paso.descripcion)
        if " ".join(contenido.split()) == " ".join(descripcion.split()):
            contenido = texto = ""
        identificador = f"repro-expl-{next(_CONTADOR_EXPLICACION)}"
        if self.sin_movimiento or autoreproduccion or contenido != html.escape(texto):
            self.explicacion.set_content(
                f'<span class="texto-secundario text-sm leading-relaxed">{contenido}</span>'
            )
            return
        self.explicacion.set_content(
            f'<span id="{identificador}" class="texto-secundario text-sm leading-relaxed"></span>'
        )
        llamada = (
            f"if(window.scalaris && window.scalaris.pasos) window.scalaris.pasos.revelar({json.dumps(identificador)}, "
            f"{json.dumps(texto)});"
        )
        ui.run_javascript(llamada)

    def _actualizar_glosa(self, paso: PasoReproductor) -> None:
        """Renderiza el boton de Glosa si el paso tiene metadatos explicables."""
        self.contenedor_glosa.clear()
        if not self.al_explicar or not paso.meta_explicar:
            return
        from src.frontend.componentes.glosa_sugerencias import renderizar_boton_explicacion

        metadatos = dict(paso.meta_explicar)
        metadatos["operacion"] = limpiar_latex_plano(metadatos.get("operacion", paso.descripcion))
        paso_explicable = replace(paso, meta_explicar=metadatos)
        with self.contenedor_glosa:
            renderizar_boton_explicacion(
                self.indice_actual + 1,
                lambda indice: self.al_explicar(paso_explicable),
                esta_cargando=self.esta_ocupado(),
            )

    def _avanzar(self) -> None:
        """Avanza un paso o cancela el temporizador si la tarjeta ya fue eliminada."""
        if self.tarjeta is None or self.tarjeta.is_deleted:
            self.detener()
        elif self.indice_actual < len(self.pasos) - 1:
            self.ir_a(self.indice_actual + 1, autoreproduccion=True)
        else:
            self._pausar_reproduccion()

    def _alternar_reproduccion(self) -> None:
        """Inicia o pausa la secuencia y reinicia desde el principio al final."""
        if self.temporizador is None or self.temporizador.is_deleted:
            return
        if self.temporizador.active:
            self._pausar_reproduccion()
            return
        if self.indice_actual == len(self.pasos) - 1:
            self.ir_a(0, autoreproduccion=True)
        reiniciar_espera(self)
        self.boton_reproducir.props('icon=pause')

    def _pausar_reproduccion(self) -> None:
        """Pausa el temporizador conservando su instancia para una próxima reproducción."""
        if self.temporizador is not None and not self.temporizador.is_deleted:
            self.temporizador.active = False
        if self.boton_reproducir is not None and not self.boton_reproducir.is_deleted:
            self.boton_reproducir.props('icon=play_arrow')

    def _cambiar_velocidad(self, evento) -> None:
        """Actualiza el intervalo del temporizador con la velocidad seleccionada."""
        self.velocidad = evento.value
        self._actualizar_intervalo()

    def _actualizar_intervalo(self, *, reiniciar: bool = True) -> None:
        """Ajusta la lectura al paso vigente sin reactivar temporizadores retirados."""
        temporizador = getattr(self, "temporizador", None)
        if temporizador is not None and not temporizador.is_deleted and self.pasos:
            self.temporizador.interval = intervalo_lectura(
                self.pasos[self.indice_actual].explicacion, getattr(self, "velocidad", "Normal")
            )
            if reiniciar and temporizador.active:
                reiniciar_espera(self)

    def _cambiar_deslizador(self, evento) -> None:
        """Navega al paso elegido en el deslizador."""
        indice = int(evento.value)
        if indice != self.indice_actual:
            self.ir_a(indice)

    def _seleccionar_desde_indice(self, indice: int) -> None:
        """Navega desde el indice y desplaza el reproductor a la vista."""
        self.ir_a(indice)
        ui.run_javascript(
            "const elemento=document.getElementById(" + json.dumps(self.id_tarjeta) + ");"
            "if(elemento)elemento.scrollIntoView({behavior:window.scalaris?.movimiento?.permitido?.()?'smooth':'auto',block:'center'});"
        )
