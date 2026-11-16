"""Secuencias de procedimiento para la interfaz de métodos abiertos."""
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor


def construir_secuencia(datos: dict) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Organiza captura, iteraciones registradas y estado final en grupos de lectura."""
    entrada = datos.get("entrada") or {}
    metodo = datos.get("metodo", "newton")
    etiqueta = "Newton-Raphson" if metodo == "newton" else "Secante"
    pasos = [PasoReproductor(
        0, "planteamiento", "Datos del problema",
        f"Se resolverá la función con {etiqueta}, tolerancia {entrada.get('tolerancia', 'sin dato')} "
        f"y máximo de {entrada.get('limite_iteraciones', 'sin dato')} iteraciones.",
        indice_grupo=0,
    )]
    for fila in datos.get("iteraciones", ()):
        indice = len(pasos)
        pasos.append(PasoReproductor(
            indice, "calculo", f"Iteración {fila['i']}",
            "Se sustituyen los valores actuales en la fórmula del método.",
            indice_grupo=1, cuerpo=fila,
        ))
    hay_iteraciones = bool(datos.get("iteraciones"))
    grupo_cierre = 2 if hay_iteraciones else 1
    cierre = len(pasos)
    pasos.append(PasoReproductor(
        cierre, "resultado", "Estado del cálculo",
        f"{datos.get('mensaje', '')} Raíz aproximada: {datos.get('raiz', 'no disponible')}; "
        f"residuo: {datos.get('residuo', 'no disponible')}.",
        indice_grupo=grupo_cierre,
    ))
    grupos = [
        GrupoReproductor("Planteamiento", "Función, método y criterios de cálculo", "planteamiento", (0,)),
    ]
    if hay_iteraciones:
        grupos.append(GrupoReproductor("Iteraciones", "Aproximaciones calculadas por el motor", "calculo",
                                       tuple(range(1, cierre))))
    grupos.append(GrupoReproductor("Resultado", "Criterio de parada y aproximación final", "resultado", (cierre,)))
    return tuple(pasos), tuple(grupos)
