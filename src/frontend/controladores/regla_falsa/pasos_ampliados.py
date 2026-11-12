"""Procedimiento configurado que conserva las filas originales y su foco pedagógico."""
from dataclasses import replace

from .pasos import construir_pasos
from .presentacion_ampliada import datos_criterio, titulo_configurado


def construir_pasos_configurados(ampliado: dict) -> tuple:
    """Recibe el resultado ampliado completo y publica el criterio por un canal separado."""
    respuesta = ampliado["resultado"]
    pasos, grupos = construir_pasos(respuesta)
    condicion = " · ".join(f"{etiqueta}: {valor}" for etiqueta, valor in datos_criterio(ampliado))
    entrada = ampliado["configuracion"]["entrada"]
    nuevos = []
    for paso in pasos:
        descripcion = paso.descripcion
        if paso.tipo == "planteamiento":
            descripcion = f"f(x) = {entrada['expresion']} · {datos_criterio(ampliado)[1][1]}"
        elif paso.tipo == "final":
            descripcion = titulo_configurado(respuesta, ampliado)
        explicacion = paso.explicacion + " " + condicion
        nuevos.append(replace(paso, descripcion=descripcion, explicacion=explicacion,
                              meta_explicar={**paso.meta_explicar, "operacion": descripcion,
                                             "detalle": {"explicacion": explicacion, "iteracion": paso.cuerpo,
                                                         "criterio_aplicado": ampliado["criterio"]}}))
    grupos = (replace(grupos[0], resumen="Intervalo y criterio aplicado"), grupos[1],
              replace(grupos[2], resumen=titulo_configurado(respuesta, ampliado)))
    return tuple(nuevos), grupos
