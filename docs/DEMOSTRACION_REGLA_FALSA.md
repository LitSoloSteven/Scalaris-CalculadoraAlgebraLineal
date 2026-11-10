# Demostración de regla falsa

Semana 13. Verificación local completada el 10 de noviembre de 2026.
Responsabilidad de integración de Roger: [#106](https://github.com/LitSoloSteven/Scalaris-CalculadoraAlgebraLineal/issues/106).
Dependencias: [motor #104](https://github.com/LitSoloSteven/Scalaris-CalculadoraAlgebraLineal/issues/104)
y [interfaz #105](https://github.com/LitSoloSteven/Scalaris-CalculadoraAlgebraLineal/issues/105).

Base revisada: `e5fccae`; motor disponible desde `697745a`. Rama local:
`feature/semana-13-regla-falsa-integracion`. Código verificado: `53c947e`.
Commits de integración: `ad3f6e5`, `14210ee` y `53c947e`.
No se hizo push, PR, fusión ni cierre de issues. La exposición académica no se ha realizado.

## Entorno y arranque

Windows, Python 3.14.7, NiceGUI 3.16.0, Plotly 7.0.0, pytest 9.1.1 y Node 24.20.0.
Usar las dependencias ya instaladas en `venv`; no se añadió ningún paquete.
Arranque habitual desde la raíz del repositorio:

```powershell
.\venv\Scripts\python.exe -m src.main
```

Abrir [Regla falsa](http://127.0.0.1:8080/utilidades/regla-falsa).
El cálculo no requiere IA. Para la verificación se inició el servidor directamente,
sin cargar archivos de entorno ni enviar mensajes a Glosa:

```powershell
.\venv\Scripts\python.exe -u -c "from src.frontend.aplicacion import inicializar_aplicacion; from nicegui import ui; inicializar_aplicacion(); ui.run(host='127.0.0.1', port=8080, reload=False, show=False, storage_secret='verificacion-local-regla-falsa')"
```

Ese secreto público corresponde únicamente al servidor local de demostración.

## Método y significado de la tolerancia

Se usa falsa posición clásica: `c = (a*f(b) - b*f(a))/(f(b)-f(a))`.
El motor normaliza las magnitudes de las evaluaciones y calcula una combinación
convexa de los extremos para evitar productos que desborden. Las decisiones de
signo, actualización y parada pertenecen al dominio; la vista presenta sus filas.

La parada ordinaria exige `abs(f(c)) < tolerancia`, estrictamente y sin redondear.
El residuo mide la evaluación de la función. El cambio entre aproximaciones y el
error relativo mostrado son informativos; ninguno garantiza el error en x.
La garantía de encierro requiere continuidad; una curva muestreada y el cambio
de signo no prueban continuidad ni unicidad. Se conserva su diagnóstico.
La unidad angular se aplica al evaluador, la gráfica y el contexto pedagógico.

## Ejemplo principal observado

Capturar `x^2-2`, extremos `1` y `2`, tolerancia `1e-6`, límite `100`, radianes.
Pulsar **Calcular raíz**. También puede cargarse el ejemplo **Raíz de 2**.

| i | a antes de actualizar | b | c | f(c) | Intervalo siguiente |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2 | 1.3333333333333335 | -0.22222222222222188 | [1.3333333333333335, 2] |
| 2 | 1.3333333333333335 | 2 | 1.4000000000000001 | -0.03999999999999959 | [1.4000000000000001, 2] |
| 3 | 1.4000000000000001 | 2 | 1.411764705882353 | -0.006920415224913157 | [1.411764705882353, 2] |

Resultado real: `EXITO`, motivo `tolerancia_residuo`, 9 filas,
aproximación `1.4142134998513232`, residuo `1.7683827158165855e-7`.
Intervalo final `[1.4142134998513232, 2]`; continuidad `CONFIRMADA`.
La primera aproximación procede de la secante y difiere del punto medio 1.5.
La pantalla redondea la aproximación según **Decimales de presentación**;
**Mostrar 17 cifras** permite inspeccionar la tabla con más detalle.

## Casos reproducibles

Todos usan radianes. Salvo indicación, tolerancia `1e-6` y límite `100`.
Los ocho casos de esta tabla se ejecutaron en la interfaz real.

| Caso | Función; a; b; cambios | Resultado observado |
| --- | --- | --- |
| Interior | x^2-2; 1; 2 | EXITO, 9 filas y valores del ejemplo principal |
| Extremo | x-1; 1; 2 | EXITO/raiz_en_extremo, c=1, residuo 0, cero filas |
| Cero válido | x; 0; 2 | EXITO/raiz_en_extremo, c=0, residuo 0, cero filas |
| Sin signo | x^2+1; -1; 1 | SIN_CAMBIO_DE_SIGNO, sin aproximación ni filas |
| Dominio | sqrt(x); -1; 1 | ERROR/DOMINIO_INVALIDO, sin aproximación ni curva muestreada |
| Límite | x^2-2; 1; 2; tol=1e-12, límite=1 | LIMITE_ITERACIONES, c=1.3333333333333335, residuo 0.22222222222222188, intervalo posterior [c,2] |
| Estancamiento | x^2-2; 1.414213562373095; 1.4142135623730951; tol=1e-30 | ESTANCAMIENTO, una fila, residuo 4.4408920985006262e-16; aproximación provisional |
| Invertido | x^2-2; 2; 1 | Campos normalizados a 1.0 y 2.0, aviso visible y resultado vigente de 9 filas |

Los extremos del caso de estancamiento son flotantes adyacentes en este entorno.
No interpretar el cero flotante como una afirmación de exactitud simbólica.
Un extremo que permanece fijo en varias filas es normal en el método clásico.

## Evidencia de integración

| Verificación | Evidencia y alcance |
| --- | --- |
| Ruta y navegación | Apertura y recarga directa; navegación a bisección y regreso con captura vacía |
| Recursos | Recursos locales observados con HTTP 200; CSS propio versionado y sin scripts exclusivos de bisección |
| Tabla y procedimiento | Primera fila seleccionada mediante Paso siguiente; tabla, fórmula y secante del mismo c; todas las filas contrastadas automáticamente |
| Marcadores | Cruce (c,0) separado de evaluación (c,f(c)); intervalo posterior procede del motor |
| Copia real | Portapapeles leído tras Copiar resultado: estado, residuo, 9 filas, intervalo y aviso de normalización coincidentes |
| Glosa | Panel abierto sin enviar consultas; muestra Búsqueda de raíces y advertencia sobre residuo; contexto y foco contrastados por tests |
| Temas | Papel, Marea y Medianoche conservaron estado y coordenadas del paso seleccionado a 1036 px |
| Móvil | A 320x800, documento de 305 px sin desborde global; tabla de 1500 px con contenedor local de 241 px; captura visual inspeccionada |
| Teclado y movimiento reducido | Envío con Enter desde tolerancia, foco conservado y prefers-reduced-motion activo; no equivale a auditar todo el teclado |
| Vigencia | Pruebas con trabajador retardado y motor real: cambios de tolerancia, límite o unidad descartan respuesta anterior y permiten recalcular |
| Bisección | Ruta, cálculo de x^2-2 y regreso ejecutados; regresiones automatizadas incluidas en suite |

Captura local de evidencia, excluida de commits: `.playwright-mcp/regla-falsa-320.png`.
La imagen corresponde a Medianoche, intervalo normalizado y primera secante activa.

| Before | After | Why |
| --- | --- | --- |
| Plotly configurado con hovermode=closest y etiquetas automáticas | hovermode=False, comprobado en navegador y en cada paso de las pruebas nuevas | Cumplir el guion sin coordenadas emergentes; las cifras siguen accesibles en tabla y procedimiento |

## Pruebas y revisión

Se complementó la cobertura existente, sin modificar sus aserciones ni crear
archivos duplicados para contrato y recursos. El inventario previsto de #106
se satisface mediante estas responsabilidades:

| Responsabilidad | Archivos de pruebas |
| --- | --- |
| Contrato/motor/serialización | test_regla_falsa_controlador_interfaz.py, test_regla_falsa_contrato.py, test_regla_falsa_invariantes.py y test_regla_falsa_oraculos.py existentes |
| Ruta pública y casos adicionales | test_regla_falsa_recorrido.py nuevo; pagina_publica y vista_flujo existentes |
| Paridad de todas las filas | test_regla_falsa_paridad_salidas.py nuevo; salidas_interfaz e integracion_procedimiento existentes |
| Preferencias durante cálculo | test_regla_falsa_ciclo_vida_integrado.py nuevo; vista_vigencia, vista_recientes y vista_reconexion existentes |
| Registro, recursos y aislamiento | test_regla_falsa_registro_publico.py y test_regla_falsa_regresion_compartida.py existentes |

Comandos ejecutados desde la raíz:

```powershell
.\venv\Scripts\python.exe -u -m pytest -q tests/test_regla_falsa_paridad_salidas.py tests/test_regla_falsa_recorrido.py tests/test_regla_falsa_ciclo_vida_integrado.py
.\venv\Scripts\python.exe -u -m pytest -q tests/test_biseccion.py tests/test_backend_biseccion_robusto.py tests/test_evaluador_real_robusto.py tests/test_integracion_backend_biseccion.py tests/test_interfaz_biseccion.py
.\venv\Scripts\python.exe -u -m pytest -q
.\venv\Scripts\python.exe -m compileall -q src tests
git diff --check
```

Pruebas nuevas: **11 aprobadas**. Regresión dirigida: **98 aprobadas**.
Suite completa final: **5390 aprobadas**, una
advertencia de deprecación de Starlette/httpx, en 106.17 s. Compilación y diff-check:
sin errores. La suite incluye las pruebas de JavaScript existentes.
La primera ejecución con ocho pruebas nuevas produjo 5386 aprobadas; se informa
cada total observado y no se usa ese recuento para atribuir cobertura adicional.
En el sandbox, pytest y el servidor quedaron esperando; se interrumpieron esas
sesiones y las verificaciones se completaron con ejecución autorizada fuera de él.

Tres revisores independientes de seguridad, bugs y mantenibilidad examinaron el
diff y consumidores. Sin hallazgos nuevos; el detalle de hover se corrigió y volvió
a revisar. El grafo falló con Transport closed en la sesión principal; se leyeron
fuentes directamente. Algunos revisores recuperaron cobertura, sin atribuir al
índice las líneas nuevas o modificadas. No se tocaron dependencias ni backend.

## Límites y pendientes de comprobación

- **NO PROBADO:** auditoría completa de contraste AA, lector de pantalla, zoom
  real de navegador al 200 %, navegación íntegra con teclado, preservación de
  cámara tras zoom manual y traza de rendimiento con CPU limitada.
- Durante el recorrido se observaron dos errores de Plotly en consola:
  `<text> attribute y: Expected length, -Infinity` y
  `Resize must be passed a displayed plot div element`. El cálculo y la tabla
  siguieron disponibles. Su origen no se atribuyó a esta corrección; requieren
  reproducción aislada, especialmente con intervalos de flotantes adyacentes
  y retirada de gráficas. No se declara consola libre de errores.
- El contrato propuesto del issue describe calcular_presentacion en controlador;
  la implementación real lo expone en presentacion_grafica y devuelve
  `{resultado, muestra, aviso_grafica}`. Los consumidores y pruebas usan esa
  interfaz real existente; no se alteró la API durante la integración.
- Aritmética float, un intervalo por cálculo, sin Illinois, búsqueda múltiple
  ni PDF de raíces. Muestrear una curva no certifica continuidad.

## Guion breve para exponer

1. Abrir Regla falsa desde Utilidades, cargar Raíz de 2 y calcular.
2. Comparar las primeras tres secantes; seleccionar una fila y distinguir c de f(c).
3. Copiar el resultado y explicar residuo, tolerancia estricta y continuidad.
4. Ejecutar extremo, sin signo y límite=1; señalar las diferencias de estado.
5. Mostrar raíz cero y estancamiento; editar un campo para retirar el resultado.
6. Cambiar tema, consultar el contexto local de Glosa y volver desde bisección.

Aceptación local: #104 motor real disponible y probado; #105 captura, ruta y
salidas integradas; #106 recorridos exigidos ejecutados y demostración preparada.
Los pendientes visuales anteriores permanecen explícitos. Publicación y fusión
corresponden al usuario.
