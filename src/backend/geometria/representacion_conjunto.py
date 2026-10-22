"""Representación paramétrica y recorte del conjunto solución geométrico."""
from src.backend.geometria.conjunto_solucion import ConjuntoSolucion
from src.backend.geometria.coordenadas import a_flotante_seguro
from src.backend.geometria.planos import calcular_geometria_plano
from src.backend.geometria.recorte import recortar_recta_a_caja
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex


def representar_conjunto(conjunto: ConjuntoSolucion | None, parametros: dict | None, dimension: int, limite: float) -> dict | None:
    """Serializa un conjunto exacto y su recorte; recibe dimensión ambiente y límite."""
    if conjunto is None:
        return None
    punto = conjunto.punto
    espacio_completo = conjunto.dimension == dimension
    datos = {
        "tipo": conjunto.tipo.value,
        "etiqueta_tipo": "espacio_completo" if espacio_completo else conjunto.tipo.value,
        "dimension": conjunto.dimension, "espacio_completo": espacio_completo,
        "punto": [a_flotante_seguro(valor) for valor in punto] if punto else None,
        "punto_exacto": [str(valor) for valor in punto] if punto else None,
        "punto_latex": _columna_latex(punto, dimension) if punto else None,
    }
    if parametros:
        _agregar_parametrizacion(datos, conjunto, parametros, dimension, limite)
    return datos


def _columna_latex(coordenadas, dimension):
    return matriz_a_latex(Matriz(dimension, 1, [[valor] for valor in coordenadas]))


def _agregar_parametrizacion(datos, conjunto, parametros, dimension, limite):
    datos["direcciones"] = [[a_flotante_seguro(valor) for valor in direccion] for direccion in parametros["direcciones"]]
    datos["direcciones_exactas"] = [[str(valor) for valor in direccion] for direccion in parametros["direcciones"]]
    datos["nombres_parametros"] = parametros["nombres_parametros"]
    datos["variables_libres"] = [["x", "y", "z"][columna] for columna in parametros["columnas_libres"]]
    partes = [_columna_latex(parametros["particular"], dimension)]
    for indice, direccion in enumerate(parametros["direcciones"]):
        partes.append(f"{parametros['nombres_parametros'][indice]}{_columna_latex(direccion, dimension)}")
    datos["parametros_latex"] = r"\mathbf{x} = " + " + ".join(partes)
    datos["descripcion"] = _descripcion(dimension, conjunto.dimension, datos["punto_exacto"], datos["direcciones_exactas"])
    _recortar_geometria(datos, conjunto.dimension, parametros, dimension, limite)


def _recortar_geometria(datos, cantidad_direcciones, parametros, dimension, limite):
    if datos["espacio_completo"]:
        return
    if cantidad_direcciones == 1:
        _recortar_recta(datos, dimension, limite)
    elif cantidad_direcciones == 2 and dimension == 3:
        _representar_plano(datos, parametros)


def _descripcion(dimension, cantidad_direcciones, punto, direcciones):
    texto_punto = ", ".join(punto) if punto else ""
    if cantidad_direcciones == 1:
        return f"Las soluciones forman una recta que pasa por ({texto_punto}) con dirección ({', '.join(direcciones[0])})."
    if cantidad_direcciones == 2 and dimension == 3:
        return f"Las soluciones forman un plano que pasa por ({texto_punto}) generado por ({', '.join(direcciones[0])}) y ({', '.join(direcciones[1])})."
    return ""


def _recortar_recta(datos, dimension, limite):
    punto, direccion = datos["punto"], datos["direcciones"][0]
    if not (all(valor is not None for valor in punto) and all(valor is not None for valor in direccion)):
        return
    intervalo = recortar_recta_a_caja(punto, direccion, limite)
    if not intervalo:
        datos["segmento_visible"] = False
        return
    inicio, fin = intervalo
    datos["segmento"] = [
        [punto[i] + inicio * direccion[i] for i in range(dimension)],
        [punto[i] + fin * direccion[i] for i in range(dimension)],
    ]
    datos["segmento_visible"] = True


def _representar_plano(datos, parametros):
    normal, desplazamiento = calcular_geometria_plano(parametros["direcciones"], parametros["particular"])
    datos["normal_exacta"] = [str(valor) for valor in normal]
    datos["desplazamiento_exacto"] = str(desplazamiento)
    aproximados = [a_flotante_seguro(valor) for valor in normal]
    desplazamiento_aproximado = a_flotante_seguro(desplazamiento)
    if all(valor is not None for valor in aproximados) and desplazamiento_aproximado is not None:
        datos["normal"] = aproximados
        datos["desplazamiento"] = desplazamiento_aproximado
