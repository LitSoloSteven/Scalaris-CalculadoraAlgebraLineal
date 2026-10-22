"""Preguntas contextuales, seguimientos y reintentos del asistente Glosa."""
from typing import Any
from nicegui import ui

from src.ai.mensajes import construir_pregunta_explicar_paso
from src.frontend import banderas


class PreguntasGlosaMixin:
    """Convierte acciones didácticas del usuario en consultas al asistente."""

    def preguntar_sugerencia(self, sugerencia: Any, desde_teclado: bool = False) -> None:
        """Procesa el clic o seleccion de teclado de un chip de sugerencia."""
        if self._rechazar_si_ocupado():
            return

        if sugerencia.foco and hasattr(self.interfaz_activa, "enfocar_celda"):
            self.interfaz_activa.enfocar_celda(sugerencia.foco)

        if banderas.panel_lateral_habilitado() and not getattr(self, "esta_abierto", False):
            comando = "window.scalaris?.glosa?.abrir({instantaneo: true, origen: 'teclado'});" if desde_teclado else "window.scalaris?.glosa?.abrir();"
            ui.run_javascript(f"if(window.scalaris && window.scalaris.glosa) {comando}")

        if desde_teclado and getattr(self, "campo_entrada", None) and not sugerencia.foco:
            self._enfocar_entrada()

        self._lanzar_tarea(self._enviar_consulta(sugerencia.texto, almacenable_en_cache=True))

    def preguntar_seguimiento(self, seguimiento: Any, desde_teclado: bool = False) -> None:
        """Envia una pregunta de seguimiento seleccionada por el usuario."""
        if self._rechazar_si_ocupado():
            return

        if desde_teclado and getattr(self, "campo_entrada", None):
            self._enfocar_entrada()

        self._lanzar_tarea(self._enviar_consulta(seguimiento.pregunta, almacenable_en_cache=False, mas_simple=seguimiento.mas_simple))

    def disparar_explicacion_paso(self, meta_paso: dict[str, Any]) -> None:
        """Inicia la explicacion didactica de un paso procedimental."""
        if self._rechazar_si_ocupado():
            return

        if banderas.panel_lateral_habilitado() and not getattr(self, "esta_abierto", False):
            ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.abrir();")

        if hasattr(self, "establecer_foco_explicacion"):
            self.establecer_foco_explicacion(meta_paso)

        pregunta = construir_pregunta_explicar_paso(
            meta_paso.get("tipo", "otro"),
            meta_paso.get("indice", 1),
            meta_paso.get("total", 1),
            meta_paso.get("operacion", ""),
        )
        self._lanzar_tarea(self._enviar_consulta(pregunta, almacenable_en_cache=True, mas_simple=True))

    def _rechazar_si_ocupado(self) -> bool:
        if not getattr(self, "_esta_enviando", False):
            return False
        ui.notify("Glosa está respondiendo. Espera a que termine.", type="warning")
        return True

    def _enfocar_entrada(self) -> None:
        ui.run_javascript("setTimeout(() => { const entrada = document.querySelector('.glosa-entrada textarea'); if(entrada) entrada.focus(); }, 100);")

    def _reintentar_ultimo_mensaje(self) -> None:
        """Reintenta el ultimo mensaje enviado tras un fallo recuperable."""
        ultimo_usuario = next((mensaje for mensaje in reversed(self.historial_chat) if mensaje.get("enviado")), None)
        if self.historial_chat and self.historial_chat[-1].get("error"):
            self.historial_chat.pop()

        self.renderizar_chat_lateral()
        if ultimo_usuario:
            self._lanzar_tarea(self._enviar_consulta(
                ultimo_usuario.get("texto", ""),
                almacenable_en_cache=ultimo_usuario.get("almacenable_en_cache", False),
                mas_simple=ultimo_usuario.get("mas_simple", False),
                es_reintento=True,
            ))
