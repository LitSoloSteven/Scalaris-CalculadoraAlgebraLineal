import sys
import os
import unittest

# 1. Forzamos a Python a reconocer la carpeta raíz del proyecto
ruta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ruta_raiz)

# 2. Ahora sí importamos las clases de tu compañero de forma segura
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
class TestResolutorGauss(unittest.TestCase):

    """Agrupa las comprobaciones de resolutor gauss."""
    def test_caso_solucion_unica(self):
        """Evalúa el Caso 1: Sistema con Solución Única."""
        # Sistema: 
        # 2x + y = 5
        # x - y = 1
        datos = [
            [2.0, 1.0, 5.0],
            [1.0, -1.0, 1.0]
        ]
        # Se instancia el objeto Matriz requerido por el solver
        matriz_aumentada = Matriz(filas=2, columnas=3, datos=datos)
        resolutor = ResolutorGauss(matriz_aumentada)
        resultado = resolutor.resolver()
        
        self.assertEqual(resultado["estado"], "SOLUCION_UNICA")
        self.assertIsNotNone(resultado["solucion"])
        # Verifica que la solución calculada sea correcta (x=2, y=1)
        self.assertEqual(resultado["solucion"], ["2", "1"])

    def test_caso_infinitas_soluciones(self):
        """Evalúa el Caso 2: Sistema con Infinitas Soluciones."""
        # Sistema (fila 2 es múltiplo de la fila 1):
        # x + y = 2
        # 2x + 2y = 4
        datos = [
            [1.0, 1.0, 2.0],
            [2.0, 2.0, 4.0]
        ]
        matriz_aumentada = Matriz(filas=2, columnas=3, datos=datos)
        resolutor = ResolutorGauss(matriz_aumentada)
        resultado = resolutor.resolver()
        
        self.assertEqual(resultado["estado"], "SOLUCIONES_INFINITAS")
        self.assertIsNotNone(resultado["solucion"])
        # Sistema indeterminado: la solución se expresa en términos de
        # la variable libre t.
        self.assertTrue(any("t" in s for s in resultado["solucion"]))

    def test_caso_inconsistente(self):
        """Evalúa el Caso 3: Sistema Sin Solución (Inconsistente)."""
        # Sistema (rectas paralelas):
        # x + y = 2
        # x + y = 3
        datos = [
            [1.0, 1.0, 2.0],
            [1.0, 1.0, 3.0]
        ]
        matriz_aumentada = Matriz(filas=2, columnas=3, datos=datos)
        resolutor = ResolutorGauss(matriz_aumentada)
        resultado = resolutor.resolver()
        
        self.assertEqual(resultado["estado"], "SIN_SOLUCION")
        self.assertIsNone(resultado["solucion"])

if __name__ == '__main__':
    unittest.main()
