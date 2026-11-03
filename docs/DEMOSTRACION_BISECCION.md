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

El contrato del motor admite d entero entre 0 y 15 y entre 1 y 500 iteraciones; la interfaz utiliza esos mismos límites. El valor inicial del límite es 100. Se usa punto flotante binario de Python, separado de la aritmética racional del núcleo algebraico. Los números intermedios no se redondean a d posiciones. La inspección presenta hasta 17 cifras significativas, incluido el campo numérico del error relativo; el texto con dos decimales se conserva por compatibilidad.

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

Antes de iterar, el motor busca ceros de denominadores afines y de sus productos, potencias positivas y valores absolutos; también comprueba bases afines de potencias negativas y restricciones afines de logaritmo, raíz cuadrada y potencias fraccionarias. Así se rechaza `1/(x-0.1234)` sin depender de un muestreo. No se certifican dominios generales ni todos los polos de funciones como tan o denominadores no afines.

La gráfica conserva 401 muestras. No une evaluaciones inválidas; interrumpe además cambios de signo de magnitud atípica como indicio conservador de un salto. Si aparecen huecos en un cálculo inicialmente exitoso, el adaptador lo presenta como **CONTINUIDAD_NO_VERIFICADA**, con aproximación provisional. Este muestreo puede omitir singularidades o marcar funciones continuas muy abruptas: **no demuestra ni refuta continuidad general**. La condición de continuidad sigue siendo necesaria incluso cuando el análisis estructural no detecta problemas.

No se añadió exportación PDF: su registro actual solo acepta las herramientas ya declaradas y requeriría ampliar contratos y regiones. No se muestra un botón que no pueda generar un documento válido. La gráfica permanece en el propio módulo porque representa una función real, fuera de las escenas lineales del visualizador.

## Verificación y revisión

- **VERIFICADO:** suite completa con `venv\Scripts\python.exe -m pytest -q`: **3936 passed, 1 warning in 79.78s**, con una advertencia existente de deprecación de httpx en Starlette. Incluye pruebas JavaScript y auditorías de tamaño, complejidad, docstrings, idioma y recursos. También se ejecutó `venv\Scripts\python.exe -m compileall -q src tests` y `git diff --check`.
- **VERIFICADO:** pruebas nuevas de d=0,2,4,6, raíces en extremo y cero, dominio, ausencia de cambio de signo, expresiones inválidas, límite, estancamiento sin éxito falso, salto sospechoso, ejemplos, figura inicial y descarte de resultados durante edición.
- **VERIFICADO en navegador:** captura y cálculo, edición de d=4 a d=6 con retirada del resultado, Enter, avance del reproductor y cambio de intervalo; tabla desplazable con ArrowRight; temas Papel, Marea y Medianoche, incluida conservación de colores al cambiar de paso.
- **VERIFICADO:** a 320 px, ancho del documento 305 px, sin desborde de página. La tabla conserva desplazamiento propio. Contrastes de texto principal/secundario/acento sobre panel: Papel 12.59/5.23/5.22; Marea 10.99/7.74/7.63; Medianoche 13.24/9.38/10.82.
- **VERIFICADO con alcance limitado:** ampliación mediante CSS `zoom:2` a viewport 1280 px, sin desborde. **NO PROBADO:** zoom nativo del navegador al 200%, lector de pantalla, recorrido exhaustivo de todos los controles, rendimiento con CPU limitada y envío real a OpenRouter.
- **VERIFICADO en navegador tras actualizar backend:** el polo `1/(x-0.1234)` y el subdesbordamiento `exp(-1000)` muestran error sin aproximación de raíz. Para `x^2-2`, d=4, la inspección revela el error relativo `0.0021579163160052651%` que la presentación normal redondea a `0.00%`.
- Revisión de seguridad, bugs y mantenibilidad: **NO DELEGADO**, tres pasadas de lectura y comprobación realizadas por el agente principal. Se revisaron aridad, tipos, límites de expresión, pérdida de representación, singularidades y coherencia de traza. Se separaron reglas para cumplir los límites de complejidad y se preservaron las excepciones numéricas del evaluador. No se añadieron dependencias. El usuario autorizó expresamente modificar backend para esta entrega.

Las primeras pruebas detectaron contratos fijados al catálogo anterior. Se actualizaron únicamente las listas/cantidades afectadas: dos a tres utilidades, trece a catorce elementos y tarjetas, y una hoja CSS adicional en el orden de carga. No se eliminó ni debilitó ninguna prueba. Las modificaciones constan en Git.

## Backend: requisitos implementados

Los seis requisitos antes pendientes se implementaron en el dominio y sus consumidores, con autorización expresa del usuario. Se mantienen las firmas públicas de `biseccion`, `compilar` y `evaluar`. El contrato añade `codigo_diagnostico: str`, `error_relativo_valor: float | None` y métricas tipadas; los campos existentes se conservan.

| Requisito | Comportamiento verificado |
| --- | --- |
| Estancamiento | `sin(x)` en [1e16,1e16+4], d=15, termina en 2 filas con `PRECISION_NO_ALCANZADA`, motivo `estancamiento` y diagnóstico `ESTANCAMIENTO`; la última explicación indica que no puede reducirse el intervalo. |
| Punto medio sin desbordar | `x-1.3e308` en [1e308,1.6e308] devuelve 1.3e308 sin sumar primero los extremos. Un ancho no representable produce `ERROR` con `ANCHO_NO_REPRESENTABLE`; el estancamiento de un intervalo representable conserva salida provisional. |
| Gramática y errores reales | Se validan constantes numéricas reales, nombres, operadores y un argumento por función, sin parámetros nombrados. `sin()`, `pi(1)`, `sin`, textos, booleanos y complejos se rechazan. Los fallos se expresan en castellano y sin TypeError/ZeroDivisionError crudos. |
| Cero y subdesbordamiento | `exp(-1000)`, literales como `1e-400` y operaciones no nulas que se redondean a cero producen `SUBDESBORDAMIENTO`. Los ceros evaluados conservan el motivo compatible `raiz_exacta`, pero añaden `CERO_EVALUADO` y un mensaje que no certifica exactitud simbólica. |
| Error relativo sin redondear | La traza conserva el porcentaje numérico además del texto compatible. La primera iteración y c=0 usan None/«No aplica». Un porcentaje no representable usa None/«No representable» y nunca infinito. Tabla y reproductor comparten el formato de inspección. |
| Singularidades verificables | `1/x`, `1/(x-0.1234)` y factores afines nulos dentro de denominadores se rechazan antes de evaluar extremos o aceptar raíces. Se documenta el alcance estructural sin afirmar continuidad general. |

La gramática está acotada a 512 caracteres, 256 nodos AST y 32 niveles de operaciones. El motor vuelve a validar las entradas construidas directamente y nunca publica valores numéricos no finitos. Se distingue `EXPRESION_INVALIDA`, `ENTRADA_INVALIDA`, `DOMINIO_INVALIDO`, `EVALUACION_NO_FINITA`, `SUBDESBORDAMIENTO`, `SINGULARIDAD_DETECTADA`, `ANCHO_NO_REPRESENTABLE`, `ESTANCAMIENTO`, `LIMITE_ITERACIONES`, `CERO_EVALUADO` y `CONVERGENCIA_POR_ANCHO` sin depender del texto de Python.

La aproximación, intervalo y residuo finales pertenecen a la última muestra trazada, incluso al agotar el límite. Las regresiones están en `tests/test_backend_biseccion_robusto.py`, `tests/test_evaluador_real_robusto.py` y `tests/test_integracion_backend_biseccion.py`. Se mantuvieron las pruebas originales del motor; la prueba de interfaz del polo cambió únicamente de advertencia por muestreo a exigir `ERROR` y `SINGULARIDAD_DETECTADA`, porque ahora el dominio puede verificarlo.

Commits locales de implementación y revisión del backend: `24ba63c`, `3b8a505`, `e1a6a1d`, `f3ee042`, `f261929`, `dece953`, `f381b22` y `99ab6ae`. El plan temporal de ejecución se eliminó al concluir esta verificación.

## Estado de entrega

Frontend, backend y recorrido integrados a `develop` mediante el [PR #95](https://github.com/LitSoloSteven/Scalaris-CalculadoraAlgebraLineal/pull/95), commit `4eb5794`. Se cerraron técnicamente LIT-21, LIT-22, LIT-23 y LIT-20 en Linear y sus equivalentes #88, #89, #90 y #87 en GitHub, conservando la evidencia de implementación y pruebas. El cotejo final de adjuntos originales, la aprobación docente de las sustituciones académicas y la exposición no se dan por realizados.

El ajuste posterior que desactiva las coordenadas al pasar el puntero por la gráfica está aislado en `feature/semana-12-biseccion-interaccion`, creada desde `develop` actualizado, commit `b9a6180`. Se verificaron 98 pruebas del motor, evaluador y recorrido en esta rama. Los planes temporales se eliminaron al entregar.
