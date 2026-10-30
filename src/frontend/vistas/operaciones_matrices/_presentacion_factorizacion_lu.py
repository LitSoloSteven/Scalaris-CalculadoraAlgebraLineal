"""Adaptación y reproductor de la traza de factorización LU."""
from dataclasses import replace

from src.frontend import textos
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.presentacion_analisis import adaptar_analisis
from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor

_FASES = {"planteamiento": 0, "inicial": 1, "pivote": 1, "intercambio": 1,
          "eliminacion": 1, "resultado": 2, "operacion": 3, "verificacion": 3}
_TIPOS_EXPLICACION = {"resultado": "factorizacion", "operacion": "verificacion"}


def adaptar_traza_factorizacion_lu(resultado: dict) -> tuple[tuple, tuple]:
    """Adapta la traza de resultado; devuelve pasos y cuatro grupos ordenados.

    Lanza KeyError si el dominio devuelve un tipo de paso desconocido.
    """
    pasos_originales, _ = adaptar_analisis(resultado)
    pasos = []
    indices = [[] for _ in textos.LU_FASES]
    for paso in pasos_originales:
        grupo = _FASES[paso.tipo]
        indices[grupo].append(paso.indice)
        meta = {**paso.meta_explicar, "tipo": _TIPOS_EXPLICACION.get(paso.tipo, paso.tipo)}
        pasos.append(replace(paso, indice_grupo=grupo, meta_explicar=meta))
    grupos = tuple(GrupoReproductor(titulo, textos.LU_CUENTA_PASOS.format(cantidad=len(indices[indice])), "operacion", tuple(indices[indice]))
                   for indice, titulo in enumerate(textos.LU_FASES))
    return tuple(pasos), grupos


def montar_reproductor_lu(resultado: dict, panel_ia) -> ReproductorPasos:
    """Monta el resultado con el panel de Glosa y devuelve su reproductor."""
    pasos, grupos = adaptar_traza_factorizacion_lu(resultado)
    reproductor = ReproductorPasos(pasos, grupos, _renderizar_cuerpo, "factorizacion-lu", opciones={
        "titulo": textos.LU_TITULO, "lineas_ayuda": textos.LU_AYUDA,
        "tipos_leyenda": ("planteamiento", "pivote", "intercambio", "eliminacion", "resultado", "verificacion"),
        "al_explicar": crear_accion_explicacion(panel_ia, pasos),
        "esta_ocupado": lambda: bool(getattr(panel_ia, "_esta_enviando", False)),
    })
    reproductor.construir()
    return reproductor


def _renderizar_cuerpo(paso, contenedor) -> None:
    with contenedor:
        paso.cuerpo()
