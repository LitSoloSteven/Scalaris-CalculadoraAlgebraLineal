"""Conversión estructural de candidatos exploratorios para los contratos de lote."""
from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion


def convertir_candidato(registro: dict, *, validar_forma: bool = True) -> CandidatoResolucion:
    """Convierte un registro con identidad; en modo tolerante deja la forma inválida al dominio."""
    if not isinstance(registro, dict):
        raise ValueError("El candidato no tiene la forma esperada.")
    datos = registro.get("candidato")
    if not isinstance(datos, dict):
        if validar_forma:
            raise ValueError("El candidato no tiene la forma esperada.")
        datos = {}
    intervalo = datos.get("intervalo")
    if not isinstance(intervalo, (tuple, list)) or len(intervalo) != 2:
        if validar_forma:
            raise ValueError("El candidato requiere dos extremos.")
        intervalo = ()
    candidato = CandidatoExploracion(datos.get("tipo"), tuple(intervalo), datos.get("abscisa"), datos.get("valor"))
    return CandidatoResolucion(registro.get("identificador"), candidato)
