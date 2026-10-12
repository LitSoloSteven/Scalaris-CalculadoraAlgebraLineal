"""Orquestación de consultas HTTP a OpenRouter con cancelación y reintentos."""
import os
import threading
import time
import uuid

from dotenv import load_dotenv
import requests

from src.ai.cache_respuestas import calcular_hash_cache, guardar_en_cache, leer_cache
from src.ai.clasificador_respuestas import (
    ContextoIntento, clasificar_error_http, clasificar_excepcion_red,
    procesar_respuesta_exitosa,
)
from src.ai.constantes import (
    LIMITE_TIEMPO_TOTAL_SEGUNDOS, MODELO_PRIMARIO_DEFECTO,
    TIEMPO_ESPERA_REINTENTO_SEGUNDOS, TIEMPO_MINIMO_RESTANTE_SEGUNDOS,
    TIMEOUT_CONEXION_MAXIMO_SEGUNDOS, TIMEOUT_LECTURA_MAXIMO_SEGUNDOS, URL_OPENROUTER,
)
from src.ai.mensajes import construir_mensajes
from src.ai.respuestas import OpcionesConsulta, ResultadoIA, TipoErrorIA
from src.ai.textos import CONSULTA_CANCELADA, ERROR_SERVICIO

load_dotenv(".env")
load_dotenv("src/ai/.env")


class ClienteOpenRouter:
    """Consulta los modelos configurados conservando el plazo total de respuesta."""

    MODELO_PRIMARIO = os.getenv("OPENROUTER_PRIMARY_MODEL", MODELO_PRIMARIO_DEFECTO)
    MODELOS_RESERVA = [
        modelo.strip()
        for modelo in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",")
        if modelo.strip()
    ]
    _tiempo_monotonico = time.monotonic
    _tiempo_dormir = time.sleep
    _peticiones_post = staticmethod(requests.post)

    def __init__(self) -> None:
        """Carga las credenciales y crea un espacio privado para la caché."""
        self.clave_api = os.getenv("OPENROUTER_API_KEY")
        self.direccion_servicio = URL_OPENROUTER
        self._espacio_cache = uuid.uuid4().hex

    def _validar_precondiciones(self, cancelar: threading.Event | None) -> ResultadoIA | None:
        if cancelar and cancelar.is_set():
            return ResultadoIA(False, CONSULTA_CANCELADA, TipoErrorIA.CANCELADO)
        if not self.clave_api:
            mensaje = "Glosa no está configurada en este servidor. Avisa a quien administra Scalaris."
            return ResultadoIA(False, mensaje, TipoErrorIA.SIN_CLAVE)
        return None

    def _ejecutar_llamada_red(
        self, modelo: str, mensajes: list, tiempo_restante: float
    ) -> requests.Response:
        tiempo_conexion = min(TIMEOUT_CONEXION_MAXIMO_SEGUNDOS, tiempo_restante)
        tiempo_lectura = min(TIMEOUT_LECTURA_MAXIMO_SEGUNDOS, tiempo_restante)
        cabeceras = {
            "Authorization": f"Bearer {self.clave_api}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://calculadora-algebra-uam.local",
            "X-Title": "Calculadora Algebra Lineal UAM",
        }
        return self._peticiones_post(
            self.direccion_servicio, headers=cabeceras,
            json={"model": modelo, "messages": mensajes},
            timeout=(tiempo_conexion, tiempo_lectura),
        )

    def _procesar_respuesta_intento(
        self, respuesta: requests.Response, modelo: str, contexto: ContextoIntento
    ) -> tuple[ResultadoIA | None, str]:
        if respuesta.status_code == 200:
            return procesar_respuesta_exitosa(respuesta, modelo), "exito"
        return clasificar_error_http(respuesta.status_code, modelo, contexto)

    def _ejecutar_un_intento(
        self, modelo: str, mensajes: list, tiempo_restante: float,
        cancelar: threading.Event | None, contexto: ContextoIntento,
    ) -> tuple[ResultadoIA | None, str]:
        try:
            respuesta = self._ejecutar_llamada_red(modelo, mensajes, tiempo_restante)
            if cancelar and cancelar.is_set():
                return ResultadoIA(False, CONSULTA_CANCELADA, TipoErrorIA.CANCELADO), "terminar"
            return self._procesar_respuesta_intento(respuesta, modelo, contexto)
        except requests.exceptions.RequestException as error:
            resultado, terminar = clasificar_excepcion_red(
                error, modelo, contexto.indice_modelo, contexto.total_modelos
            )
            accion = "terminar" if (terminar or resultado) else "interrumpir"
            return resultado, accion

    def _intentar_modelo(
        self, modelo: str, mensajes: list, fecha_limite: float,
        cancelar: threading.Event | None, configuracion: tuple[int, int, int],
    ) -> tuple[ResultadoIA | None, bool]:
        maximo_intentos, indice_modelo, total_modelos = configuracion
        for intento in range(maximo_intentos):
            if cancelar and cancelar.is_set():
                return ResultadoIA(False, CONSULTA_CANCELADA, TipoErrorIA.CANCELADO), True
            tiempo_restante = fecha_limite - self._tiempo_monotonico()
            if tiempo_restante < TIEMPO_MINIMO_RESTANTE_SEGUNDOS:
                return None, True
            contexto = ContextoIntento(intento, indice_modelo, tiempo_restante, total_modelos)
            resultado, accion = self._ejecutar_un_intento(
                modelo, mensajes, tiempo_restante, cancelar, contexto
            )
            if accion in ("exito", "terminar"):
                return resultado, True
            if accion == "reintentar":
                self._tiempo_dormir(TIEMPO_ESPERA_REINTENTO_SEGUNDOS)
                continue
            break
        return None, False

    def _paso_cache(self, mensajes: list, modelos: list[str]) -> tuple[str, ResultadoIA | None]:
        clave = calcular_hash_cache(mensajes, modelos, self._espacio_cache)
        return clave, leer_cache(clave, self._tiempo_monotonico())

    def _paso_cascada_modelos(
        self, modelos: list[str], mensajes: list, cancelar: threading.Event | None,
        clave_cache: str,
    ) -> ResultadoIA:
        fecha_limite = self._tiempo_monotonico() + LIMITE_TIEMPO_TOTAL_SEGUNDOS
        for indice, modelo in enumerate(modelos):
            maximo_intentos = 2 if indice == 0 else 1
            resultado, terminar = self._intentar_modelo(
                modelo, mensajes, fecha_limite, cancelar, (maximo_intentos, indice, len(modelos))
            )
            if terminar and resultado:
                if resultado.exito and clave_cache:
                    guardar_en_cache(clave_cache, resultado, self._tiempo_monotonico())
                return resultado
        return ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)

    def preguntar(
        self, pregunta: str, historial: list | None = None, *, contexto: str | None = None,
        cancelar: threading.Event | None = None, opciones: OpcionesConsulta = OpcionesConsulta(),
    ) -> ResultadoIA:
        """Consulta Glosa con historial, contexto, cancelación y opciones de respuesta."""
        resultado_validacion = self._validar_precondiciones(cancelar)
        if resultado_validacion:
            return resultado_validacion
        modelos = [self.MODELO_PRIMARIO]
        if self.MODELOS_RESERVA:
            modelos.append(self.MODELOS_RESERVA[0])
        mensajes = construir_mensajes(
            historial or [], pregunta, contexto, respuesta_simple=opciones.respuesta_simple
        )
        clave_cache = ""
        if opciones.usar_cache:
            clave_cache, resultado_cache = self._paso_cache(mensajes, modelos)
            if resultado_cache:
                return resultado_cache
        return self._paso_cascada_modelos(modelos, mensajes, cancelar, clave_cache)
