"""Adaptación de la captura vectorial al contrato de los resolutores existentes."""
import json

from src.backend.geometria.transferencia import preparar_vectores_visualizador
from .controlador_operaciones_vectores import ControladorOperacionesVectores


def capturar_vectores(vectores: dict, dimension: int) -> dict:
    """Devuelve orientación y celdas crudas; el dominio valida sus valores."""
    return {
        nombre: {"orientation": vector["orientation"],
                 "data": [vector["cache"].get(indice, "").strip() or "0" for indice in range(dimension)]}
        for nombre, vector in vectores.items()
    }


def resolver_captura(operacion: str, opciones: dict, vectores: dict) -> str:
    """Delega una operación capturada y devuelve su JSON sin modificar las entradas."""
    valores = list(vectores.values())
    if operacion == "suma_resta" and len(valores) == 2:
        carga = {"operation": {"suma": "add", "resta": "subtract"}[opciones["operacion"]],
                 "v1": valores[0], "v2": valores[1], "strict": opciones["estricto"]}
        return ControladorOperacionesVectores.procesar_suma_resta(json.dumps(carga))
    if operacion == "escalar" and len(valores) == 1:
        carga = {"scalar": opciones["escalar"], "v": valores[0]}
        return ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(carga))
    if operacion == "combinacion_lineal" and opciones["objetivo"] in vectores:
        objetivo = opciones["objetivo"]
        carga = {"b": vectores[objetivo], "vectors": [valor for nombre, valor in vectores.items() if nombre != objetivo]}
        return ControladorOperacionesVectores.procesar_combinacion_lineal(json.dumps(carga))
    return json.dumps({"status": "ERROR", "message": "No se encontraron los vectores necesarios para la operación."})


def preparar_transferencia(operacion: str, vectores: dict) -> tuple[list, str]:
    """Delega al dominio las restricciones de escena para la captura recibida."""
    return preparar_vectores_visualizador(operacion, vectores)
