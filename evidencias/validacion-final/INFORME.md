# Validación final de Scalaris

Fecha: 18 de octubre de 2026. Repositorio: `C:\Users\stive\calculadora-algebra-uam`.

Se revisaron el README, `tests/test_cumplimiento_reglas.py`, el arranque real en
`src/main.py` y `src/frontend/aplicacion.py`, y el estado de trabajo de las etapas
anteriores. No se encontraron archivos AGENTS.md aplicables. El adjunto se trató
como material de referencia, sin ejecutar sus instrucciones.

## Correcciones de esta validación

| Fallo reproducido | Cambio | Verificación |
|---|---|---|
| La consola de Sistemas e Inversa mostraba `Anchor: target "#cNN" not found`. Las ayudas de Limpiar apuntaban al identificador generado, sustituido por el id público del botón. | Ambas ayudas se construyen explícitamente con `target="#boton-limpiar-principal"`. Se conserva el id usado por la animación de limpieza y su nombre accesible. | Dos nuevas pruebas con componentes reales; recorridos posteriores sin errores de consola, incluida transferencia y cálculo de inversa. |
| La descripción de Álgebra lineal se cortaba a dos líneas en móvil, aunque la tarjeta podía crecer. | Se retiró el recorte por líneas de los títulos y descripciones de las filas del inicio. | Comprobación de altura completa, ausencia de desbordamiento y capturas en los tres temas y las tres disposiciones. |

Archivos de aplicación corregidos en esta última etapa:

- `src/frontend/vistas/sistemas_lineales/vista_sistemas_lineales.py`
- `src/frontend/vistas/operaciones_inversas/vista_operaciones_inversas.py`
- `src/frontend/recursos/css/vistas_inicio_matriz.css`

Se añadió `tests/test_ayudas_limpieza.py`. En `tests/test_inicio_matriz_dialogos.py`
se reemplazó la exigencia anterior de recortar a dos líneas por una comprobación
que prohíbe ese recorte: la expectativa anterior contradecía el requisito aprobado
de mostrar los textos completos. No se quitaron verificaciones para encubrir fallos.
El README enlaza este informe.

La lista completa de cambios acumulados de las etapas anteriores, incluidos
archivos nuevos y la retirada de accesos_algebra.py, está en
[archivos-modificados.txt](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/archivos-modificados.txt).
La lista corresponde al estado del directorio de trabajo anterior a los commits de entrega.

## Pruebas ejecutadas

| Comprobación | Resultado final | Evidencia |
|---|---|---|
| Inicio, navegación, temas, capturas, determinantes, animaciones, ayudas y cumplimiento | 214 aprobadas | [Pruebas específicas](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/pruebas-especificas.txt) |
| Suite general de Python, después de corregir los fallos | 2183 aprobadas, 1 advertencia | [Suite general](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/pruebas-generales.txt) |
| Todos los tests de cliente JavaScript | 142 aprobados; 0 fallos, omisiones o cancelaciones | [JavaScript](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/pruebas-javascript.txt) |
| `git diff --check` | Sin errores de espacios | Git solo avisó sobre conversión futura LF/CRLF en archivos existentes. |

La advertencia de Python es `StarletteDeprecationWarning`: Starlette recomienda
httpx2 para su TestClient. No hubo fallos de pruebas por esa advertencia.

## Navegador y geometría

Se ejecutaron las comprobaciones en Chromium 156.0.8078.4, Windows, Node
v24.20.0, Python 3.14.7 y NiceGUI 3.16.0. Los datos exactos están en
[entorno.json](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/entorno.json).

| Disposición | Paletas | Comprobaciones |
|---|---|---|
| Escritorio, 1440 × 1000 CSS px | Papel, Marea, Medianoche | Portada, cinco herramientas, temas, foco, paneles de vectores y varias matrices. |
| Ventana estrecha, 390 × 1000 CSS px | Las tres | Mismos recorridos; solo las listas/cuadrículas que lo requieren desplazan localmente. |
| Zoom nativo del 200 %, ventana de 1440 × 1000 | Las tres | `chrome.tabs.getZoom()` devolvió 2; ancho interior de 709 CSS px y devicePixelRatio 2. Inicio y tema permanecen dentro de la ventana. |
| Dispositivo móvil emulado, 390 × 844, con eventos táctiles | Papel | Arrastre horizontal de la lista, rueda horizontal, apertura táctil de diálogo y visita a Matrices. |

El zoom se aplicó mediante una extensión de prueba en un perfil temporal de
Chromium. No es un escalado CSS ni una mera reducción de la ventana. Sus capturas
son de la ventana visible a escala nativa; los contenidos inferiores se alcanzan
con desplazamiento vertical. Se corrigió el método de captura para evitar el
recorte introducido por Playwright al combinar fullPage con zoom nativo.

Resultados registrados en
[disposicion-accesibilidad.json](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/disposicion-accesibilidad.json)
y [desplazamiento-tactil-trackpad.json](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/desplazamiento-tactil-trackpad.json).
El arrastre movió la lista 287 px y la rueda horizontal 503 px; la página conservó
scrollX igual a cero. Los gestos se emularon mediante eventos del navegador.

Se comprobaron el título Scalaris íntegro, logo y título hermanos, separación
respecto de las tarjetas, descripciones completas, cinco accesos de Álgebra lineal,
un único aria-current, foco visible tras entrada de teclado, selección exclusiva
de tema y etiquetas vectoriales sin superposición. Se activaron las tres operaciones
vectoriales con teclado. Inicio y el selector de tema permanecieron alcanzables.
No se encontraron controles accesibles llamados Más álgebra ni referencias en src.
Una sesión nueva mostró Empieza aquí; después de visitar una herramienta, Sigue aquí.

## Operaciones matriciales y LU

Los recorridos funcionales se ejecutaron en escritorio/Medianoche, móvil/Papel y
zoom 200 %/Marea. Los tres terminaron correctamente y sin errores de JavaScript:

- Captura con 1/3, ceros e identidad parcial; añadir B conserva A.
- Aumentar y reducir filas y columnas conserva las celdas correspondientes.
- Eliminar B conserva A y no deja controles de B.
- `A+A` muestra pasos y el resultado exacto con 2/3.
- `A+Z` muestra error y conserva todas las celdas.
- La flecha transfiere A a Inversa; después se calculó una matriz invertible.
- En Inversa el contrato actual representa ceros como celdas vacías. Se compararon
  sus valores matemáticos normalizados; 1/3 se conservó literalmente y sin aproximar.

| Caso de determinante en navegador | Resultado exacto |
|---|---|
| Matriz 1 × 1 con 7/11 | 7/11 |
| Identidad 3 × 3 | 1 |
| Singular [[1,2],[2,4]] | 0 |
| Intercambio de filas [[0,1],[1,0]] | -1 |
| [[1/2,1/3],[2/5,3/7]] | 17/210 |

La interfaz expuso únicamente triangulación LU, sin pestañas ni controles de
cofactores. Se abrió también el enlace anterior
`/algebra-lineal/matrices?operacion=determinante` y mantuvo la misma captura LU.

Para reproducir el descarte de respuestas tardías, el servidor de prueba añade
800 ms antes del controlador original de determinantes. No cambia el algoritmo.
Se inició el cálculo de [5], se editó a [9] mientras estaba pendiente y se comprobó
que el resultado anterior no apareciera. Recalcular mostró Determinante: 9.
La instrumentación está solo en `servidor_validacion.py`, fuera de la aplicación.

Evidencia: `funcionalidad-escritorio.json`, `funcionalidad-movil.json` y
`funcionalidad-zoom200.json`, junto con las capturas de cada caso.
Se verificó además una figura real de Plotly en los tres temas:
[graficos.json](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/graficos.json).

## Animaciones: evidencia temporal

[animaciones-temporales.json](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/animaciones-temporales.json)
contiene tiempos de inicio/fin, fotogramas, duraciones, retardos, estados de
reproducción y muestras del documento. Las capturas estáticas no se utilizan como
prueba de que la animación se ejecutó.

Se comprobó primera visita con sesión limpia en los tres temas, logotipo correcto,
entrada, anillo, nombre, UAM, pulso, barra y salida. La entrada del inicio esperó
la retirada de la presentación. La recarga no la repitió. Entrar directamente a
otra ruta y regresar a Inicio tampoco la reprodujo.

Se midieron expansiones de tema en las seis combinaciones, activación por teclado,
selecciones rápidas, navegación repetida, Atrás/Adelante y recarga. Las expansiones
registraron finalización y duraciones superiores a 400 ms, con configuración de
500 ms; no quedaron atributos de transición bloqueando el documento. Con movimiento
reducido la presentación usó su alternativa breve, y tema/navegación no crearon
círculos. La ausencia de API se simuló desactivando startViewTransition y el opt-in
de navegación: los enlaces y el tema siguieron funcionando.

En los recorridos finales no se registraron excepciones de página, errores de
consola ni rechazos de promesas sin manejar. Los diálogos conservaron foco, Escape
y devolución del foco. Los controles se activaron realmente durante los recorridos.

## Capturas y reproducción

Las 73 capturas PNG se enumeran en
[indice-capturas.txt](C:/Users/stive/calculadora-algebra-uam/evidencias/validacion-final/indice-capturas.txt).
Incluyen portada, navbar, menús de tema, vectores, tarjetas matriciales, expresión,
errores, transferencia, LU y presentación. Hay comprobación de dimensiones y de
imágenes no uniformes en `integridad-capturas.json`, además de revisión visual de
estados representativos.

Para repetir, desde la raíz del repositorio, usando el entorno ya validado:

```powershell
.\venv\Scripts\python.exe -m pytest -q
node --expose-internals --test tests/test_*.js
.\venv\Scripts\python.exe evidencias/validacion-final/servidor_validacion.py
```

Con el servidor abierto, en otra terminal:

```powershell
node evidencias/validacion-final/validar_disposicion.cjs
node evidencias/validacion-final/validar_animaciones.cjs
node evidencias/validacion-final/validar_graficos.cjs
node evidencias/validacion-final/validar_desplazamiento.cjs
$env:PERFIL_VALIDACION='escritorio' # repetir también con movil y zoom200
node evidencias/validacion-final/validar_funcionalidad.cjs
```

`comun_navegador.cjs` admite PLAYWRIGHT_CORE y CHROMIUM para localizar otra
instalación de Playwright y su ejecutable. Sus valores predeterminados son las
rutas efectivamente usadas en este equipo. No se añadieron dependencias al producto.
`actualizar_capturas_finales.cjs` regenera las capturas vectoriales al 200 % sin
transiciones de pestaña en curso.

## Limitaciones pendientes

- `requirements.txt` declara `nicegui>=1.4.0, <2.0.0`, mientras que el entorno
  instalado y probado contiene NiceGUI 3.16.0. No se ensayó una instalación limpia
  ni se verificó compatibilidad con 1.x. Estos resultados no certifican ese rango.
- No se ejecutó esta validación en Firefox, Safari, un móvil físico o un trackpad
  físico. La interacción táctil y la rueda horizontal se emularon en Chromium.
- Se mantiene la advertencia de deprecación de Starlette/httpx indicada arriba.

No quedan fallos funcionales observados en los recorridos registrados de este
entorno. Esto no equivale a declarar el proyecto listo para todos los entornos o
para el rango de dependencias pendiente de verificar.
