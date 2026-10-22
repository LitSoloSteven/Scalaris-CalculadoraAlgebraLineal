"""Captura y serialización del contexto pedagógico de un sistema lineal."""
from src.ai.contexto import (
    ContextoIA, EstadoContexto, describir_matriz, sanear_cadena_usuario, generar_nota_ventana,
)
from src.ai.huellas import esta_desactualizado
from src.frontend.sugerencias import Senales, primera_celda_invalida
from .estado_captura import modo_homogeneo_activo


def _contiene_coeficientes(matriz: list) -> bool:
    return any(valor for fila in matriz for valor in fila if str(valor).strip() not in ('0', '', '0.0'))


def construir_datos_entrada(vista) -> tuple:
    """Devuelve vacío, etiqueta, entrada didáctica y datos actuales para la huella."""
    vacio, etiqueta, datos = True, "Sistema Lineal", {}
    metodo = getattr(vista.pestanas_metodo, 'value', 'gauss')
    entrada = {"modo": vista.pestanas_modo.value, "metodo": metodo}
    if modo_homogeneo_activo(vista):
        entrada["homogeneo"] = True
    if vista.pestanas_modo.value == 'Ecuaciones':
        lineas = [sanear_cadena_usuario(campo.value, 120) for campo in vista.entradas_ecuaciones if campo.value]
        entrada["ecuaciones"] = [campo.value for campo in vista.entradas_ecuaciones]
        if lineas:
            vacio, etiqueta, datos = False, f"Sistema de {len(lineas)} ecuaciones", {"ecuaciones": lineas}
    else:
        coeficientes, independientes = vista.cuadricula.obtener_datos_matriz()
        entrada["A"], entrada["b"] = coeficientes, independientes
        if coeficientes and _contiene_coeficientes(coeficientes):
            vacio = False
            etiqueta = f"Sistema {len(coeficientes)}×{len(coeficientes[0])} (matriz)"
            datos = _describir_sistema(coeficientes, independientes)
    return vacio, etiqueta, datos, entrada


def _describir_sistema(coeficientes: list, independientes: list) -> dict:
    datos_a = [[sanear_cadena_usuario(valor, 32) for valor in fila] for fila in coeficientes]
    datos_b = [[sanear_cadena_usuario(valor, 32)] for valor in independientes]
    return {"A": describir_matriz(datos_a), "b": describir_matriz(datos_b)}


def obtener_contexto_sistema(vista):
    """Construye el contexto de Glosa y omite el resultado si la captura cambió."""
    vacio, etiqueta, datos, entrada = construir_datos_entrada(vista)
    if vacio:
        return ContextoIA("sistemas", "Sistemas de ecuaciones", etiqueta, {}, estado=EstadoContexto(vacio=True))
    contexto = ContextoIA("sistemas", "Sistemas de ecuaciones", etiqueta, datos)
    if "A" in datos and "b" in datos:
        contexto.nota_ventana = generar_nota_ventana(datos["A"], datos["b"])
    contexto.desactualizado = esta_desactualizado(entrada, getattr(vista, '_huella_resultado', None))
    if getattr(vista, 'ultimo_resultado', None) and not contexto.desactualizado:
        resultado = vista.ultimo_resultado
        contexto.resultado = {"estado": resultado.get("estado", "ERROR")}
        mensaje = resultado.get("clasificacion") or resultado.get("mensaje")
        if mensaje:
            contexto.resultado["mensaje"] = mensaje
        if resultado.get("homogeneo"):
            analisis = resultado["homogeneo"]
            contexto.resultado.update({clave: analisis[clave] for clave in ("rango", "nulidad", "solo_trivial", "formula_familia")})
    return contexto


def obtener_senales_sistema(vista) -> Senales:
    """Devuelve la celda invalida y las senales del resultado vigente del sistema."""
    estado = 'sin_resultado'
    banderas = set()
    invalida = None
    if vista.pestanas_modo.value == 'Matriz':
        elementos = [(f'A[{fila+1},{columna+1}]', valor)
                     for (fila, columna), valor in vista.cuadricula._cache_coeficientes.items()]
        elementos.extend((f'b[{fila+1}]', valor) for fila, valor in vista.cuadricula._cache_independientes.items())
        invalida = primera_celda_invalida(elementos)
    if vista.cuadricula.filas > vista.cuadricula.columnas:
        banderas.add('mas_ecuaciones_que_incognitas')
    resultado = getattr(vista, 'ultimo_resultado', None)
    if resultado and not vista.obtener_contexto_ia().desactualizado:
        estado = {'SOLUCION_UNICA': 'unica', 'SOLUCIONES_INFINITAS': 'infinita', 'SIN_SOLUCION': 'sin_solucion'}.get(resultado.get('estado'), estado)
        if any(paso.get('descripcion', '').startswith('Intercambio') for paso in resultado.get('pasos_intermedios_latex', [])):
            banderas.add('intercambio')
    return Senales(herramienta='sistemas', estado=estado, banderas=frozenset(banderas), invalida=invalida)
