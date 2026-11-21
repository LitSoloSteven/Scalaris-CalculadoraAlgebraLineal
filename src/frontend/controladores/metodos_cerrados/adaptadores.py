"""Contratos de presentación de Bisección y Regla falsa para una captura común."""
from src.backend.resolutores.raices.regla_falsa.contratos.contrato_regla_falsa import EntradaReglaFalsa
from src.frontend.controladores.raices.biseccion.captura.captura_criterio import texto_condicion
from src.frontend.controladores.raices.biseccion.captura.catalogo_criterios import CRITERIOS
from src.frontend.controladores.raices.biseccion.ejecucion.controlador import calcular_presentacion as calcular_biseccion
from src.frontend.controladores.regla_falsa.configuracion_ampliada import criterio_capturado
from src.frontend.controladores.regla_falsa.presentacion_grafica import calcular_presentacion as calcular_regla_falsa
from src.frontend.controladores.raices.biseccion.captura.catalogo_criterios import condicion_criterio

BISECCION = "biseccion"
REGLA_FALSA = "regla_falsa"
METODOS = {BISECCION: "Bisección", REGLA_FALSA: "Regla falsa"}


def criterio_inicial(metodo: str) -> str:
    """Devuelve la opción inicial del método indicado."""
    return "decimales" if metodo == BISECCION else "residuo"


def parametros_iniciales(metodo: str) -> dict[str, str]:
    """Devuelve un borrador independiente para cada criterio de parada."""
    parametros = {tipo: str(datos[2]) for tipo, datos in CRITERIOS.items()}
    if metodo == REGLA_FALSA:
        parametros["residuo"] = str(EntradaReglaFalsa.tolerancia)
    return parametros


def captura_del_metodo(captura: dict) -> dict:
    """Traduce el criterio visible al contrato de cada controlador sin validar números."""
    datos = {clave: valor for clave, valor in captura.items() if clave != "metodo"}
    criterio = datos["criterio"]
    if captura["metodo"] == BISECCION:
        datos["decimales"] = (criterio["parametro"] if criterio["tipo"] == "decimales"
                             else CRITERIOS["decimales"][2])
    elif criterio["tipo"] == "residuo":
        datos["tolerancia"] = datos.pop("criterio")["parametro"]
    return datos


def resolver_presentacion(captura: dict) -> dict:
    """Delega el cálculo vigente y reúne respuesta, curva y criterio sin cambiar el resultado."""
    metodo = captura["metodo"]
    datos = captura_del_metodo(captura)
    if metodo == BISECCION:
        resultado = calcular_biseccion(datos)
        salida = {"resultado": resultado, "muestra": resultado.get("muestra"),
                  "aviso_grafica": resultado.get("aviso_grafica", "")}
    else:
        salida = calcular_regla_falsa(datos)
    return {"metodo": metodo, **salida}


def guia_parada(captura: dict) -> str:
    """Describe el criterio activo con las mismas reglas que aplicará el controlador."""
    datos = captura_del_metodo(captura)
    if captura["metodo"] == BISECCION:
        return texto_condicion(datos)
    try:
        criterio = criterio_capturado({**datos, "criterio": captura["criterio"]})
    except ValueError as error:
        return str(error)
    return condicion_criterio(criterio.tipo, criterio.parametro)
