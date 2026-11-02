"""Adaptación de la aplicación y su comprobación al reproductor compartido."""
from src.frontend import textos_transformaciones as textos
from src.frontend.componentes.presentacion_analisis import adaptar_analisis
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor
from src.frontend.controladores.operaciones_matrices.vista_previa_modelos import preparar_vista_previa_aplicacion


def adaptar_pasos_aplicacion(resultado: dict, captura: dict) -> tuple:
    """Conserva las fórmulas del dominio y devuelve pasos, fases y componentes asociadas."""
    if resultado.get("estado") != "EXITO" or resultado.get("verificacion") is not True:
        return (), (), ()
    planteamiento = [{"tipo": "planteamiento", "descripcion": textos.PASO_PLANTEAMIENTO,
                      "explicacion": textos.PASO_CONVENCION,
                      "detalle_latex": preparar_vista_previa_aplicacion(captura)}]
    aplicacion = [dict(paso, tipo="componente") for paso in resultado["pasos"]]
    comprobacion = resultado["traza_comprobacion"]
    fuentes = (planteamiento, aplicacion, comprobacion)
    pasos, grupos, componentes = [], [], []
    for fase, fuente in enumerate(fuentes):
        inicio = len(pasos)
        adaptados, _ = adaptar_analisis({"traza": fuente}, (inicio, fase))
        pasos.extend(adaptados)
        grupos.append(GrupoReproductor(textos.FASES_APLICACION[fase], f"{len(fuente)} pasos", "operacion",
                                      tuple(range(inicio, len(pasos)))))
        componentes.extend(_componentes_fase(fase, len(fuente)))
    return tuple(pasos), tuple(grupos), tuple(componentes)


def _componentes_fase(fase: int, cantidad: int) -> list:
    if fase == 1:
        return list(range(cantidad))
    if fase == 2:
        return [None, *range(cantidad - 2), None]
    return [None] * cantidad
