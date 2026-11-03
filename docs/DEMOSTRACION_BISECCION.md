# Bisección: demostración e integración

Implementación local de [LIT-22](https://linear.app/literalmentesteven/issue/LIT-22) y evidencia para [LIT-23](https://linear.app/literalmentesteven/issue/LIT-23), bajo [LIT-20](https://linear.app/literalmentesteven/issue/LIT-20). Fecha de revisión: 2 de noviembre de 2026, America/Managua.

## Recorrido de demostración

1. Ejecutar `venv\Scripts\python.exe src/main.py` y abrir `/utilidades/biseccion` desde Utilidades numéricas.
2. Cargar **Raíz de 2**. Introducir d=2 y observar E=0.01 antes del cálculo. Calcular; cambiar a d=6, comprobar que la salida anterior desaparece y recalcular con Enter.
3. Avanzar en el reproductor, volver, seleccionar una fase y probar reproducción, pausa y velocidad. Cada iteración muestra sus magnitudes y actualiza el intervalo y el punto medio en la gráfica. El planteamiento dibuja el intervalo original; el cierre, el intervalo final.
4. Activar **Inspeccionar valores internos**. Desplazarse por la tabla, también con Tab y flechas. La tabla contiene i, a, b, c, f(a), f(b), f(c), ancho, cota, residuo y error relativo.
5. Cargar **Polinomio del Excel** y **Potencia décima**. Los ejemplos no sobrescriben d. Restaurar una captura desde los cinco cálculos recientes de esta sesión. Copiar un resultado y abrir Glosa; el botón de explicación de cada paso incluye sus datos.
6. Probar `1/x` en [-1,1] y `x^2+1` en [-1,1]. Comprobar error de dominio o ausencia de cambio de signo. Usar d=6 y límite=2 con `x^2-2`: la aproximación queda expresamente provisional.
7. Limpiar mediante la acción compartida y confirmar. Se vacía el ejercicio y se retira el resultado, conservando la preferencia de precisión.

## Precisión y resultados reproducibles

La interfaz admite d entero entre 0 y 15, según el contrato del motor, y entre 1 y 500 iteraciones. El valor inicial del límite es 100. Se usa punto flotante binario de Python, separado de la aritmética racional del núcleo algebraico. Los números intermedios no se redondean a d posiciones. La inspección presenta hasta 17 cifras significativas; el error relativo llega del motor como texto con dos decimales.

E=10^(-d). Para d≥1, hay d−1 ceros decimales antes del 1 en E. El criterio es **b−a<E**, estrictamente. La cota geométrica en x es (b−a)/2 bajo continuidad y encierro de la raíz. El residuo |f(c)| y el error relativo porcentual no sustituyen el criterio. Que el motor evalúe f(c) como cero no certifica una raíz simbólica exacta; la interfaz lo advierte.

Resultados verificados para `x^2-2` en [1,2]:

| d | E | Iteraciones | Aproximación interna | Intervalo final | Cota |
| --- | --- | --- | --- | --- | --- |
| 0 | 1 | 2 | 1.25 | [1, 1.5] | 0.25 |
| 2 | 0.01 | 8 | 1.41796875 | [1.4140625, 1.421875] | 0.00390625 |
| 4 | 0.0001 | 15 | 1.414215087890625 | [1.4141845703125, 1.41424560546875] | 0.000030517578125 |
| 6 | 0.000001 | 21 | 1.4142136573791504 | [1.4142131805419922, 1.4142141342163086] | 0.000000476837158203125 |

En cada caso se verificaron b−a<E y la inclusión de sqrt(2) en el intervalo. El resultado visible usa d decimales, por lo que d=0 presenta `x ≈ 1`; ese redondeo no cambia el punto medio interno 1.25 ni su cota.

Para `x^4-5*x^3+0.5*x^2-11*x+10` en [0.6,1], d=4:

- Primeros puntos medios: 0.8, 0.7 y 0.75.
- Parada por ancho en 13 iteraciones; aproximación 0.763916015625.
- Intervalo final [0.7638671875, 0.76396484375], cota aproximada 0.000048828125.
- Residuo aproximado 0.0002754228065704467, mayor que E. Es compatible con cumplir el criterio geométrico.

Para `x^10-1` en [0,1.3], d=4: 15 iteraciones, aproximación 1.0000335693359377, intervalo [0.9999938964843751, 1.0000732421875] y cota aproximada 0.0000396728515625.

## Contraste con las fuentes del curso

Las referencias bibliográficas proceden del alcance registrado en LIT-20; los adjuntos originales no se encuentran en este checkout y no se ha realizado un nuevo cotejo visual de sus páginas.

- **Bisección.xlsx, Hoja1:** el issue documenta que H2:H16 usa ABS(f(c)), es decir, residuo. Su aproximación de 15 iteraciones no debe exigirse como salida de la parada por ancho. Las tres primeras filas del polinomio se han recalculado y probado.
- **guia-busqueda-raices.pdf, p. 1:** el issue registra discrepancias entre la expresión y su tabla. No se usan esas filas como oráculo; falta cotejar el original antes de explicar cada errata en la exposición.
- **MÉTODOS NUMERICOS.pptx**, diapositivas 3, 6 y 8, y **Búsqueda_Numérica_de_Raíces.pdf**, pp. 2–4 y 7: algoritmo, ejemplos e interpretación geométrica, según LIT-20.
- **Errores.pptx** y **Anatomía_de_la_Incertidumbre_Computacional.pdf:** límites de representación y distinción de métricas, según LIT-20.
- **Syllabus Grupo 1 Algebra Lineal_IIS-2026.docx**, sesión 26 del 17/11/2026: pide SymPy, NumPy y Matplotlib. Esta implementación usa AST restringido, tablas NiceGUI y Plotly, sin añadir dependencias. **La aprobación docente de esas sustituciones sigue pendiente.** No se ha generado evidencia con Matplotlib ni se afirma cumplimiento de ese requisito.

## Diseño y reutilización

Se conserva el catálogo de tres categorías y se añade bisección después de Bases y Romanos. Una captura compacta precede al resumen; gráfica y reproductor se muestran en paralelo cuando caben y en columna a ancho pequeño. La tabla tiene su propio desplazamiento enfocable. Se reutilizan estructura, navegación, tokens, temas, sincronización de Plotly, reproductor y sus controles, Glosa y foco de explicación, limpieza confirmada, copia de resultado, historial acotado y ejecución con vigencia.

La gráfica tiene 401 muestras. No une evaluaciones inválidas; interrumpe además cambios de signo de magnitud atípica como indicio conservador de un salto. Si aparecen huecos en un cálculo inicialmente exitoso, el adaptador lo presenta como **CONTINUIDAD_NO_VERIFICADA**, con aproximación provisional. Este muestreo puede omitir singularidades o marcar funciones continuas muy abruptas: **no demuestra ni refuta continuidad general**.

No se añadió exportación PDF: su registro actual solo acepta las herramientas ya declaradas y requeriría ampliar contratos y regiones. No se muestra un botón que no pueda generar un documento válido. La gráfica permanece en el propio módulo porque representa una función real, fuera de las escenas lineales del visualizador.

## Verificación y revisión

- **VERIFICADO:** suite completa con `venv\Scripts\python.exe -m pytest -q`: **3878 passed, 1 warning in 78.77s**. Incluye pruebas JavaScript y auditorías de tamaño, complejidad, docstrings, idioma y recursos. La advertencia existente corresponde a httpx en Starlette.
- **VERIFICADO:** pruebas nuevas de d=0,2,4,6, raíces en extremo y cero, dominio, ausencia de cambio de signo, expresiones inválidas, límite, estancamiento sin éxito falso, salto sospechoso, ejemplos, figura inicial y descarte de resultados durante edición.
- **VERIFICADO en navegador:** captura y cálculo, edición de d=4 a d=6 con retirada del resultado, Enter, avance del reproductor y cambio de intervalo; tabla desplazable con ArrowRight; temas Papel, Marea y Medianoche, incluida conservación de colores al cambiar de paso.
- **VERIFICADO:** a 320 px, ancho del documento 305 px, sin desborde de página. La tabla conserva desplazamiento propio. Contrastes de texto principal/secundario/acento sobre panel: Papel 12.59/5.23/5.22; Marea 10.99/7.74/7.63; Medianoche 13.24/9.38/10.82.
- **VERIFICADO con alcance limitado:** ampliación mediante CSS `zoom:2` a viewport 1280 px, sin desborde. **NO PROBADO:** zoom nativo del navegador al 200%, lector de pantalla, recorrido exhaustivo de todos los controles, rendimiento con CPU limitada y envío real a OpenRouter.
- Revisión de seguridad, bugs y mantenibilidad: **NO DELEGADO**, tres pasadas de lectura y comprobación realizadas por el agente principal. Se corrigieron figura inicial, sincronización de tema, desplazamiento de tabla, mensajes en castellano y complejidad. No se añadieron dependencias ni se modificó backend.

Las primeras pruebas detectaron contratos fijados al catálogo anterior. Se actualizaron únicamente las listas/cantidades afectadas: dos a tres utilidades, trece a catorce elementos y tarjetas, y una hoja CSS adicional en el orden de carga. No se eliminó ni debilitó ninguna prueba. Las modificaciones constan en Git.

### MANUAL DE REQUERIMIENTOS PARA BACKEND

Responsable del motor: Carlos, LIT-21. Estos pendientes no se han parcheado ni duplicado en frontend.

**Archivos:** `src/backend/resolutores/raices/biseccion.py`, `contrato_biseccion.py`, `evaluador_funcion.py`.

**Firmas que deben conservarse o endurecerse con tipos:**

```python
def biseccion(entrada: EntradaBiseccion) -> ResultadoBiseccion:
def compilar(expresion: str) -> Callable[[float], float]:
def evaluar(funcion: Callable[[float], float], valor: float) -> float:
```

La salida mantiene `estado: str`, `mensaje: str`, `aproximacion: float | None`, `intervalo_final: tuple[float, float] | None`, `error_absoluto: Fraction | None`, `cota: float | None`, `iteraciones: tuple[IteracionBiseccion, ...]`, `motivo_parada: str` y `metricas: dict`. Todo valor numérico publicado debe ser finito. Se propone tipar las métricas y añadir códigos estables de error para evitar depender del texto de Python.

Requisitos verificables:

1. Detectar `c == a` o `c == b` sin declarar convergencia cuando b−a≥E. Salida: `estado="PRECISION_NO_ALCANZADA"`, `motivo_parada="estancamiento"`, traza conservada. Caso mínimo: `sin(x)`, [1e16,1e16+4], d=15. Ahora agota el límite repitiendo filas.
2. Calcular el punto medio sin desbordar cuando sea representable. Caso: `x-1.3e308`, [1e308,1.6e308], d=0. No producir infinito por sumar extremos antes de dividir; si el ancho solicitado no es representable, devolver precisión no alcanzada.
3. Validar constantes reales, funciones llamables, aridad y uso de nombres antes de evaluar. `sin()`, `pi(1)`, `sin` y `(-1)**0.5` deben producir `ValueError` de captura o `ResultadoBiseccion(estado="ERROR", ...)`, con mensajes castellanos estables. Nunca propagar `TypeError` o `ZeroDivisionError` crudos. Excepciones del evaluador: `ValueError` por gramática/contrato; `ErrorDominio` por no real o singularidad; `ErrorNoFinito` por desbordamiento/no finito.
4. Distinguir cero evaluado en punto flotante de prueba de raíz exacta. `exp(-1000)` en [0,1] actualmente se interpreta como raíz de extremo por subdesbordamiento. Revisar el estado o añadir un diagnóstico numérico explícito, sin prometer exactitud simbólica.
5. Conservar el error relativo numérico sin redondear, adicional al texto compatible `error_relativo: str`. Campo propuesto: `error_relativo_valor: float | None`, donde None corresponde a la primera iteración o c=0. El texto actual `0.00%` no permite inspeccionar valores pequeños aunque se activen 17 cifras en frontend.
6. Documentar las singularidades que se pueden detectar de forma fiable; `1/x` en [-1,1] debe devolver ERROR. `1/(x-0.1234)` puede reducir el intervalo alrededor de un polo y el motor actual devuelve EXITO. La advertencia por muestreo del frontend es orientativa y no reemplaza una estrategia de dominio del motor.

## Estado de entrega

Frontend y recorrido local implementados. Rama local: `feature/semana-12-biseccion-interfaz-integracion`; sin push, PR ni fusión. El flujo del equipo continúa con publicación, PR hacia `develop`, revisión de otro integrante y Squash and merge desde GitHub. El plan temporal se eliminó tras la entrega; los pendientes de integración se conservan en este documento. Roger debe coordinar las correcciones matemáticas, cotejar originales y validar el encaje académico antes de cerrar LIT-23 o LIT-20. Los issues de Linear no se marcaron terminados.
