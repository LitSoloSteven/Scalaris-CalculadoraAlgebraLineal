"""Coordinación de transiciones de dimensión y composición de la familia vectorial."""
from functools import partial
from src.backend.constantes import DIMENSION_MAXIMA_VECTORES, DIMENSION_MINIMA
from .cuadricula_base import (
    ejecutar_transicion_cuadricula, selectores_cambio_dimension,
    actualizar_estados_botones_dimension, purgar_cache_unidimensional,
    indice_cambio_dimension,
)


class MixinTransicionVectores:
    """Aplica la transición compartida a componentes y vectores del panel de captura."""

    def _botones_transicion_vectores(self) -> tuple:
        botones = [self.boton_reducir_dimension, self.boton_aumentar_dimension, getattr(self, 'boton_agregar_vector', None)]
        botones.extend(self._botones_eliminar_vectores.values())
        botones.extend(vector.get('boton_orientacion') for vector in self.vectores.values())
        return tuple(boton for boton in botones if boton and not boton.is_deleted)

    def _actualizar_botones_vectores(self) -> None:
        actualizar_estados_botones_dimension(self.boton_reducir_dimension, self.boton_aumentar_dimension,
                                            self.dimension, DIMENSION_MINIMA, DIMENSION_MAXIMA_VECTORES)
        boton_agregar = getattr(self, 'boton_agregar_vector', None)
        if boton_agregar and not boton_agregar.is_deleted:
            boton_agregar.set_enabled(len(self.vectores) < self.maximo_vectores)
        for nombre, vector in self.vectores.items():
            boton = self._botones_eliminar_vectores.get(nombre)
            if boton and not boton.is_deleted:
                boton.set_enabled(len(self.vectores) > self.minimo_vectores)
            orientacion = vector.get('boton_orientacion')
            if orientacion and not orientacion.is_deleted:
                orientacion.enable()
        if vars(self).get('_transicion_activa'):
            for boton in self._botones_transicion_vectores():
                boton.disable()

    async def ajustar_dimension(self, delta: int = 0) -> None:
        """Anima las componentes afectadas y conserva la intersección de sus valores."""
        nueva_dimension = self.dimension + delta
        if not (DIMENSION_MINIMA <= nueva_dimension <= DIMENSION_MAXIMA_VECTORES):
            return
        indice = indice_cambio_dimension(self.dimension, nueva_dimension)
        selector = f"#{self.contenedor.html_id} input[data-geometria-indice='{indice}']" if self.contenedor else ""
        await ejecutar_transicion_cuadricula(
            vars(self), selectores_cambio_dimension(selector, delta), partial(self._aplicar_dimension_vectorial, nueva_dimension),
            self._botones_transicion_vectores(), self._actualizar_botones_vectores,
        )

    def _aplicar_dimension_vectorial(self, dimension: int) -> None:
        self.dimension = dimension
        for vector in self.vectores.values():
            vector['celdas'] = purgar_cache_unidimensional(vector['celdas'], dimension)
        if self.etiqueta_dimension:
            self.etiqueta_dimension.set_text(str(dimension))
        for nombre in self.vectores:
            self.renderizar_cuadricula_vector(nombre)
        if self.al_cambiar_datos:
            self.al_cambiar_datos()

    async def _agregar_vector_animado(self) -> None:
        if len(self.vectores) >= self.maximo_vectores:
            return
        nombre = self.obtener_siguiente_nombre_disponible()
        await self._transicion_vector(nombre, 1)

    async def _eliminar_vector_animado(self, nombre: str) -> None:
        if nombre not in self.vectores or nombre == self.etiqueta_fija_primer_vector or len(self.vectores) <= self.minimo_vectores:
            return
        await self._transicion_vector(nombre, -1)

    async def _transicion_vector(self, nombre: str, incremento: int) -> None:
        selector = f"#{self.contenedor.html_id} input[data-matriz-identificador='{nombre}']"
        aplicar = self.agregar_vector if incremento > 0 else partial(self.eliminar_vector, nombre)
        await ejecutar_transicion_cuadricula(
            vars(self), selectores_cambio_dimension(selector, incremento), aplicar,
            self._botones_transicion_vectores(), self._actualizar_botones_vectores,
        )
