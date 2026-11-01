"""Muestreo del procedimiento y orden editorial de las figuras exportadas."""
from collections.abc import Sequence

from src.frontend import constantes, textos


def seleccionar_intermedios(pasos: Sequence) -> tuple:
    """Devuelve hasta tres pasos interiores repartidos, sin repetir entrada ni cierre."""
    cierre = next((indice for indice, paso in enumerate(pasos)
                   if paso.tipo in ('resultado', 'final')), len(pasos) - 1)
    candidatos = tuple(paso for paso in pasos[:cierre] if paso.tipo not in (
        'inicial', 'entrada', 'planteamiento', 'resultado', 'final', 'comprobacion', 'verificacion'))
    cantidad = min(constantes.PDF_PASOS_INTERMEDIOS, len(candidatos))
    if cantidad == 0:
        return ()
    if cantidad == 1:
        return (candidatos[len(candidatos) // 2],)
    return tuple(candidatos[round(indice * (len(candidatos) - 1) / (cantidad - 1))]
                 for indice in range(cantidad))


def registro_secuencia(herramienta: str) -> dict:
    """Registra entrada, pasos, resultados y comprobaciones, con claves acotadas."""
    anteriores = textos.PDF_REGIONES_POR_HERRAMIENTA[herramienta]
    registro = {f'{herramienta}-entrada': textos.PDF_ENTRADA}
    for numero in range(1, constantes.PDF_PASOS_INTERMEDIOS + 1):
        titulo, descripcion = textos.PDF_PASO_INTERMEDIO
        registro[f'{herramienta}-paso-{numero}'] = (titulo.format(numero=numero), descripcion)
    registro.update({clave: valor for clave, valor in anteriores.items()
                     if not clave.endswith(('-procedimiento', '-comprobaciones'))})
    registro.update({clave: valor for clave, valor in anteriores.items()
                     if clave.endswith('-comprobaciones')})
    registro[f'{herramienta}-verificaciones'] = textos.PDF_VERIFICACIONES
    return registro


def seleccionar_comprobaciones(pasos: Sequence) -> tuple:
    """Recupera las verificaciones explícitas entregadas por el procedimiento."""
    return tuple(paso for paso in pasos if paso.tipo in ('comprobacion', 'verificacion'))
