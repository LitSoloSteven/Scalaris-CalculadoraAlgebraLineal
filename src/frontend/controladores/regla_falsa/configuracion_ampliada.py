"""Conversión exclusiva del parámetro activo al contrato ampliado del dominio."""
from collections.abc import Mapping

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa
from src.backend.resolutores.raices.criterios_regla_falsa import validar_criterio_regla_falsa
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS
from src.frontend.controladores.captura_real import entero_capturado, real_capturado
from .captura import preparar_entrada


def criterio_capturado(captura: Mapping[str, object]):
    """Convierte solo la condición activa; lanza ValueError por estructura o campo inválido."""
    valor = captura.get("criterio", {"tipo": "residuo", "parametro": captura.get("tolerancia", EntradaReglaFalsa.tolerancia)})
    if not isinstance(valor, dict) or set(valor) != {"tipo", "parametro"}:
        raise ValueError("El criterio requiere solamente tipo y parametro.")
    tipo = valor["tipo"]
    if not isinstance(tipo, str) or tipo not in CRITERIOS:
        raise ValueError("Selecciona un criterio de parada permitido.")
    convertir = entero_capturado if tipo in ("decimales", "iteraciones") else real_capturado
    parametro = convertir(valor["parametro"], CRITERIOS[tipo][1])
    limite = entero_capturado(captura.get("limite_iteraciones", EntradaReglaFalsa.limite_iteraciones), "El límite")
    return validar_criterio_regla_falsa({"tipo": tipo, "parametro": parametro}, limite)


def preparar_configuracion(captura: Mapping[str, object]) -> ConfiguracionReglaFalsa:
    """Adapta borradores sin convertir tolerancias inactivas; propaga ValueError del dominio."""
    if not isinstance(captura, Mapping):
        raise ValueError("Introduce la función y la configuración de parada.")
    criterio = criterio_capturado(captura)
    datos = dict(captura)
    datos["tolerancia"] = criterio.parametro if criterio.tipo == "residuo" else EntradaReglaFalsa.tolerancia
    entrada = preparar_entrada(datos)
    cero = captura.get("cero_preferido")
    if cero is not None:
        cero = real_capturado(cero, "El cero elegido")
    return ConfiguracionReglaFalsa(entrada, criterio, cero)
