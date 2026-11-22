"""Orquestación de consultas HTTP a OpenRouter con cancelación y reintentos."""
import os
import threading
import time
import uuid

from dotenv import load_dotenv
import requests

from src.ai.respuestas.cache_respuestas import calcular_hash_cache, guardar_en_cache, leer_cache
from src.ai.respuestas.clasificador_respuestas import (
    ContextoIntento, clasificar_excepcion_red, clasificar_respuesta,
)
from src.ai.constantes import (
    LIMITE_TIEMPO_TOTAL_SEGUNDOS, MODELO_PRIMARIO_DEFECTO,
    TIEMPO_ESPERA_REINTENTO_SEGUNDOS, TIEMPO_MINIMO_RESTANTE_SEGUNDOS,
    TIEMPO_MAXIMO_CONEXION_SEGUNDOS, TIEMPO_MAXIMO_LECTURA_SEGUNDOS, URL_OPENROUTER,
    TIEMPO_RESERVADO_POR_MODELO_SEGUNDOS,
)
from src.ai.cliente.mensajes import construir_mensajes
from src.ai.presupuesto.presupuesto_mensajes import validar_longitud_mensaje
from src.ai.respuestas.respuestas import OpcionesConsulta, ResultadoIA, TipoErrorIA
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
        tiempo_conexion = min(TIEMPO_MAXIMO_CONEXION_SEGUNDOS, tiempo_restante / 2)
        tiempo_lectura = min(TIEMPO_MAXIMO_LECTURA_SEGUNDOS, tiempo_restante - tiempo_conexion)
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

    def _ejecutar_un_intento(
        self, modelo: str, mensajes: list, tiempo_restante: float,
        cancelar: threading.Event | None, contexto: ContextoIntento,
    ) -> tuple[ResultadoIA | None, str]:
        try:
            respuesta = self._ejecutar_llamada_red(modelo, mensajes, tiempo_restante)
            if cancelar and cancelar.is_set():
                return ResultadoIA(False, CONSULTA_CANCELADA, TipoErrorIA.CANCELADO), "terminar"
            return clasificar_respuesta(respuesta, modelo, contexto)
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
            return resultado, False
        return None, False

    def _paso_cache(self, mensajes: list, modelos: list[str]) -> tuple[str, ResultadoIA | None]:
        clave = calcular_hash_cache(mensajes, modelos, self._espacio_cache)
        return clave, leer_cache(clave, self._tiempo_monotonico())

    def _plazo_modelo(self, fecha_limite: float, restantes: int) -> float:
        disponible = max(0.0, fecha_limite - self._tiempo_monotonico())
        cuota = min(TIEMPO_RESERVADO_POR_MODELO_SEGUNDOS, disponible / (restantes + 1))
        return fecha_limite - cuota * restantes

    def _paso_cascada_modelos(
        self, modelos: list[str], mensajes: list, cancelar: threading.Event | None,
        clave_cache: str,
    ) -> ResultadoIA:
        fecha_limite = self._tiempo_monotonico() + LIMITE_TIEMPO_TOTAL_SEGUNDOS
        ultimo_error = None
        for indice, modelo in enumerate(modelos):
            maximo_intentos = 2 if indice == 0 else 1
            plazo_modelo = self._plazo_modelo(fecha_limite, len(modelos) - indice - 1)
            resultado, terminar = self._intentar_modelo(
                modelo, mensajes, plazo_modelo, cancelar, (maximo_intentos, indice, len(modelos))
            )
            if terminar and resultado:
                if resultado.exito and clave_cache:
                    guardar_en_cache(clave_cache, resultado, self._tiempo_monotonico())
                return resultado
            ultimo_error = resultado or ultimo_error
        return ultimo_error or ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)

    def preguntar(
        self, pregunta: str, historial: list | None = None, *, contexto: str | None = None,
        cancelar: threading.Event | None = None, opciones: OpcionesConsulta = OpcionesConsulta(),
    ) -> ResultadoIA:
        """Consulta Glosa con historial, contexto, cancelación y opciones de respuesta."""
        try:
            validar_longitud_mensaje(pregunta)
        except ValueError as error:
            return ResultadoIA(False, str(error), TipoErrorIA.ENTRADA_INVALIDA)
        resultado_validacion = self._validar_precondiciones(cancelar)
        if resultado_validacion:
            return resultado_validacion
        modelos = list(dict.fromkeys([self.MODELO_PRIMARIO, *self.MODELOS_RESERVA]))
        mensajes = construir_mensajes(
            historial or [], pregunta, contexto, respuesta_simple=opciones.respuesta_simple
        )
        clave_cache = ""
        if opciones.usar_cache:
            clave_cache, resultado_cache = self._paso_cache(mensajes, modelos)
            if resultado_cache:
                return resultado_cache
        return self._paso_cascada_modelos(modelos, mensajes, cancelar, clave_cache)
