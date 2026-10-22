"""Contexto y señales del asistente para la vista de matrices."""
from src.frontend.controladores.operaciones_matrices import ControladorOperacionesMatrices
from src.frontend.controladores.captura_contexto import capturar_matrices


def _estado_sugerencias(resultado: dict, banderas: set) -> str:
    """Adapta las banderas calculadas por el backend al contrato vigente de sugerencias."""
    if resultado.get("contiene_producto"):
        banderas.add("contiene_producto")
    if resultado.get("error_dimensiones"):
        return "error_dimensiones"
    return {"EXITO": "exito", "ERROR": "error"}.get(resultado.get("estado"), "sin_resultado")


class MixinContextoMatrices:
    """Describe la entrada y el resultado vigente para el asistente."""

    def _extraer_datos_matrices_ia(self, matrices: dict) -> tuple[dict, list]:
        """Extrae matrices sanitizadas y descripciones de texto para IA."""
        from src.ai.contexto import describir_matriz, sanear_cadena_usuario
        datos_entrada = {}
        descripciones = []
        for nombre, matriz in matrices.items():
            datos = [[sanear_cadena_usuario(valor, 32) for valor in fila] for fila in matriz["datos"]]
            descripcion = describir_matriz(datos)
            datos_entrada[nombre] = descripcion
            descripciones.append(descripcion)
        return datos_entrada, descripciones

    def obtener_contexto_ia(self):
        """Proporciona el contexto serializado al asistente Glosa."""
        from src.ai.contexto import ContextoIA, EstadoContexto, sanear_cadena_usuario, generar_nota_ventana
        from src.ai.huellas import esta_desactualizado
        try:
            matrices = ControladorOperacionesMatrices.obtener_matrices_serializadas(
                self.panel_captura_matrices.obtener_datos_crudos()
            )
        except Exception:
            matrices = {}

        valor_expresion = self.entrada_expresion.value if hasattr(self, 'entrada_expresion') and self.entrada_expresion else ""
        if not matrices and not valor_expresion:
            return ContextoIA("matrices", "Matrices", "Operaciones", {}, estado=EstadoContexto(vacio=True))

        datos_entrada, descripciones = self._extraer_datos_matrices_ia(matrices)
        if valor_expresion:
            datos_entrada["expresion"] = sanear_cadena_usuario(valor_expresion, 200)

        contexto = ContextoIA("matrices", "Matrices", "Matrices y Expresión", datos_entrada)
        contexto.nota_ventana = generar_nota_ventana(*descripciones)

        entrada_actual = capturar_matrices(self.panel_captura_matrices.matrices, valor_expresion)
        contexto.desactualizado = esta_desactualizado(entrada_actual, getattr(self, '_huella_resultado', None))

        contexto.resultado = self._resultado_vigente(contexto.desactualizado)

        return contexto

    def obtener_senales_ia(self):
        """Calcula señales heurísticas para sugerencias proactivas."""
        from src.frontend.sugerencias import Senales, primera_celda_invalida
        try:
            estado = "sin_resultado"
            banderas = set()
            expresion = (
                self.entrada_expresion.value.strip()
                if hasattr(self, 'entrada_expresion') and self.entrada_expresion and self.entrada_expresion.value
                else ""
            )

            tiene_valores_no_nulos, elementos = self._celdas_para_senales()

            if not tiene_valores_no_nulos and not expresion:
                estado = "vacio"

            invalida = primera_celda_invalida(elementos)
            resultado = getattr(self, 'ultimo_resultado', None)
            if resultado and not getattr(self.obtener_contexto_ia(), 'desactualizado', True):
                estado = _estado_sugerencias(resultado, banderas)

            return Senales(herramienta="matrices", estado=estado, banderas=frozenset(banderas), invalida=invalida)
        except Exception:
            return None


    def _celdas_para_senales(self):
        """Recoge celdas y detecta datos no nulos para las sugerencias."""
        tiene_datos = False
        elementos = []
        for nombre, matriz in self.panel_captura_matrices.matrices.items():
            for (fila, columna), valor in matriz.get('cache', {}).items():
                cadena = str(valor).strip()
                if cadena and cadena not in ('0', '0.0'):
                    tiene_datos = True
                elementos.append((f"{nombre}[{fila+1},{columna+1}]", valor))
        return tiene_datos, elementos

    def _resultado_vigente(self, desactualizado):
        """Resume el resultado cuando corresponde a las entradas actuales."""
        resultado = getattr(self, 'ultimo_resultado', None)
        if not resultado or desactualizado:
            return None
        resumen = {"estado": resultado.get("estado", "ERROR"), "mensaje": resultado.get("mensaje", "")}
        if resultado.get("variable_final"):
            resumen["variable_final"] = resultado["variable_final"]
        return resumen
