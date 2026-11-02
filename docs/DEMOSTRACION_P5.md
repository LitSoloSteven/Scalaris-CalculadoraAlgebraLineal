# Demostración de operaciones matriciales, Leontief y transformaciones

Guion de integración de Scalaris para Roger. Los datos siguientes son ejemplos
didácticos, no observaciones de una economía real. La demostración utiliza los
controladores y el motor propios del proyecto; Glosa es opcional.

## Alcance académico

El calendario de P5 contempla operaciones matriciales, Leontief y transformaciones
gráficas. La matriz de evaluación menciona subespacios. Esta discrepancia sigue
pendiente de confirmación del docente: el análisis de núcleo e imagen disponible
no acredita por sí solo el criterio de pertenencia y cierre que pudiera exigirse.
La fecha interna del equipo no constituye una instrucción nueva del curso.

Referencias de alcance: [integración de P5, LIT-17](https://linear.app/literalmentesteven/issue/LIT-17/p5-integrar-operaciones-y-preparar-la-demostracion)
y [programa principal, LIT-8](https://linear.app/literalmentesteven/issue/LIT-8/p5-integrar-operaciones-matriciales-leontief-y-transformaciones).
Para explicar la exposición, contrastar los conceptos con el syllabus y las notas
del curso; este guion no añade requisitos ni atribuye decisiones al docente.

## Preparación

Desde la raíz y con las dependencias existentes, inicia `python -m src.main`.
Abre la dirección indicada por NiceGUI, normalmente `http://localhost:8080`.
Puedes trabajar sin credenciales de IA. No introduzcas ni muestres archivos `.env`
durante la exposición.

Cada bloque se puede ejecutar por separado. Si transfieres una matriz, hazlo en
la misma ejecución del servidor: el enlace temporal se consume una sola vez y
no reemplaza al historial de la herramienta.

## Bloque 1: operaciones y transferencia de la matriz capturada

1. Abre `/algebra-lineal/matrices` y deja únicamente la matriz A de tamaño 2×2.
2. Ingresa A por filas: `1/2, 1/3`; `2/5, -1/7`.
3. Evalúa `A+A` y recorre el detalle de la suma en el reproductor.
4. El resultado esperado es `[[1, 2/3], [4/5, -2/7]]`.
5. En las acciones de **Matriz A del cálculo**, elige **Transformaciones lineales**.

La transferencia lleva **A**, no el resultado de `A+A`. La pantalla de destino
debe recibir `[[1/2, 1/3], [2/5, -1/7]]`, mostrar el aviso de recepción y esperar
tu acción para calcular. Esta distinción permite comprobar la suma y reutilizar
los mismos coeficientes sin confundir ambas matrices.

En Transformaciones, selecciona **Aplicar matriz** y captura el vector columna
`v = (1/2, 1/3)`. Pulsa el botón **Aplicar matriz**. Debe resultar:

```text
T(v) = Av = (13/36, 16/105)
y1 = (1/2)(1/2) + (1/3)(1/3) = 1/4 + 1/9 = 13/36
y2 = (2/5)(1/2) - (1/7)(1/3) = 1/5 - 1/21 = 16/105
```

Comprueba las coordenadas exactas, el antes/después y las tres fases del
procedimiento: planteamiento, aplicación por componentes y comprobación exacta.
El original se identifica con un círculo abierto y el transformado con un rombo;
las etiquetas conservan las fracciones aunque las posiciones sean aproximadas.

Abre **Últimos cálculos de esta sesión**, modifica una coordenada y observa que se
retira el resultado anterior. Restaura la captura desde el historial y vuelve a
calcular: deben reaparecer `13/36` y `16/105`.

Variante rectangular: agrega a A la fila `(0, 1/11)` antes de evaluar y transferir.
La suma tendrá como tercera fila `(0, 2/11)` y `T(v)` tendrá tercera componente
`1/33`. Se mostrarán dominio R² y codominio R³ en escenas separadas, con la misma
escala, sin inventar una tercera coordenada para el original.

## Bloque 2: modelo de Leontief e interpretación económica

1. Abre `/algebra-lineal/leontief`.
2. Selecciona el ejemplo **2 Sectores (simple)** y pulsa **Calcular**.
3. Confirma los sectores Agricultura e Industria y estos datos:

```text
C = [[1/5, 3/10], [2/5, 1/10]]
d = [120, 80]
I-C = [[4/5, -3/10], [-2/5, 9/10]]
det(I-C) = 3/5
(I-C)^(-1) = [[3/2, 1/2], [2/3, 4/3]]
x = [220, 560/3]
```

El ejemplo carga `0.2`, `0.3`, `0.4`, `0.1` como texto decimal; el motor los
interpreta como racionales exactos. La producción de Industria es fraccionaria:
`560/3`, aproximadamente `186.6667`, no un entero ni una cantidad redondeada para
el cálculo.

Explica que `x` representa producción total y `d` demanda final. La diferencia
`x-Cx` debe cubrir exactamente esa demanda:

```text
Agricultura: (4/5)220 - (3/10)(560/3) = 176 - 56 = 120
Industria: -(2/5)220 + (9/10)(560/3) = -88 + 168 = 80
Cx = [100, 320/3]
x - Cx = [120, 80] = d
```

Abre **Ver desglose por sector** y comprueba producción, consumo intermedio y
demanda. Recorre **Comprobación del modelo** y **Ver desarrollo de la comprobacion**
para relacionar las igualdades con las entradas originales. Los menores iniciales
son `4/5` y `3/5`, positivos; en este ejemplo de coeficientes no negativos la
interfaz informa que se satisface Hawkins-Simon.

## Bloque 3: aplicación gráfica de una matriz y explicación por componentes

1. Abre `/algebra-lineal/transformaciones` y selecciona **Aplicar matriz**.
2. Carga el ejemplo **Fracciones** y pulsa **Aplicar matriz**.
3. Comprueba los datos y la solución exacta:

```text
A = [[2, 1], [1, 3]]
v = [1/2, 1/3]
T(v) = [4/3, 3/2]
y1 = 2(1/2) + 1(1/3) = 4/3
y2 = 1(1/2) + 3(1/3) = 3/2
```

Cada fila de A calcula una componente. La matriz combina escalamiento y mezcla
de componentes. El antes/después muestra el original `(1/2, 1/3)` y el transformado
`(4/3, 3/2)` respecto al mismo origen. Al avanzar por el procedimiento se destaca
la componente correspondiente; la gráfica es un apoyo aproximado y el resultado
racional aparece completo en las tarjetas.

Para mostrar un cambio geométrico inmediato, carga **Rotación de 90°**:
`A = [[0,-1],[1,0]]`, `v = [3,2]` y `T(v) = [-2,3]`. Es un giro antihorario.
Alternar **Vector** y **Punto** conserva el producto y cambia su representación;
esta aplicación lineal no incorpora traslaciones.

La comprobación de la interfaz utiliza el producto matricial común, no un
algoritmo independiente. Las igualdades manuales anteriores y las expectativas
fijas de las pruebas aportan un contraste externo al indicador de coincidencia.

## Contratos entre capas

Los métodos reciben JSON como texto y devuelven JSON como texto. Las matrices de
entrada se organizan por filas y sus celdas se transfieren como cadenas. Las vistas
capturan y muestran; los controladores adaptan y delegan; el backend valida y
calcula. No se añade una segunda implementación matemática al frontend.

| Operación | Entrada y método público | Salida consumida por la vista |
| --- | --- | --- |
| Expresiones | `ControladorOperacionesMatrices.procesar_expresion(expresion_texto, matrices_json)`; matrices con `datos`, `filas` y `columnas` | `estado`, `mensaje`, `matriz_resultado.datos`, `pasos_segmento` |
| Leontief | `ControladorLeontief.procesar(carga_json)`; `matriz_coeficientes`, `vector_demanda`, `nombres_sectores` | `estado`, `vector_produccion`, `vector_demanda`, `analisis_sectorial`, `hawkins_simon`, `traza_comprobacion` |
| Aplicación | `ControladorAplicacionTransformacion.procesar(carga_json)`; `matriz_transformacion`, `vector_original` | `estado`, `matriz_a`, `vector_original`, `vector_transformado`, `dimension_dominio`, `dimension_codominio`, `verificacion`, `pasos`, `traza_comprobacion` |
| Análisis | `ControladorTransformaciones.procesar(carga_json)`; `matriz_transformacion`, `nombres_variables` opcionales | `estado`, `rango`, `nulidad`, `base_nucleo`, `base_imagen`, `traza_comprobacion` |

En aplicación, cada vector de salida tiene `exacta` (cadenas racionales) y
`aproximado` (valores para dibujar). La gráfica consume `aproximado` y conserva
`exacta` para sus etiquetas. `tipo_objeto` pertenece a la captura de presentación
y al historial; no cambia el cálculo matemático. El núcleo usa `Fraction`; no se
convierte la captura transferida a punto flotante para hacer álgebra.

Las entradas inválidas devuelven `estado: ERROR` y un mensaje en castellano; los
consumidores no deben suponer campos de éxito ante ese estado. Los balances
singulares de Leontief tienen clasificación propia y no certifican un multiplicador.

## Evidencia automatizada reproducible

Desde la raíz, con el entorno activado:

```powershell
python -m pytest -q tests/test_demostracion_p5_modelos.py tests/test_demostracion_p5_transferencia.py
python -m pytest -q
python -m compileall -q src tests
```

- `test_demostracion_p5_modelos.py` monta Leontief desde su ruta real, carga el
  catálogo, verifica producciones y balance racional, consumo intermedio,
  historial, explicación y texto visible coherente con la solución fraccionaria.
- `test_demostracion_p5_transferencia.py` evalúa `A+A`, activa el manejador real de
  transferencia de A, consume el enlace en la ruta destino y comprueba el producto,
  los datos Plotly y la recuperación del historial para tamaños 2×2 y 3×2.
- El montaje automatizado simula el transporte del navegador y el despacho del
  trabajador; mantiene controles, captura, controladores y dominio reales. No
  certifica por sí solo la representación visual ni el transporte HTTP/WebSocket.

## Comprobación manual para la exposición

Recorre los tres bloques en Papel, Marea y Medianoche. Repite con 320 px de ancho
y con zoom del navegador al 200 %. Comprueba que fórmulas y tablas tengan su
desplazamiento propio, que puedas alcanzar los botones y leer las fracciones.

Usa Tab y Enter para cargar ejemplos y calcular; revisa el foco visible y la
navegación del reproductor. Activa movimiento reducido en el sistema y repite el
recorrido. Verifica error y recuperación cambiando una celda a `1/0`, calculando
y restaurando el ejemplo. No presentes una salida anterior como resultado vigente.

La revisión visual completa, las mediciones de fluidez con CPU limitada y la
exposición ante el docente se deben acreditar por separado de las pruebas Python.

## Entrega e integración del equipo

Los commits de esta tarea son locales. El usuario publica la rama, abre un PR con
base `develop` y obtiene revisión del equipo antes de integrar, según el
[GitFlow de Scalaris](https://linear.app/literalmentesteven/document/gitflow-y-control-de-versiones-scalaris-da823189703f).
El trabajo local y este guion no afirman que ese PR, la fusión, la exposición o la
confirmación académica ya hayan ocurrido.
