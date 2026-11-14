# Plan de implementación: Línea de tiempo

**Rama**: `004-linea-de-tiempo` (se trabaja en `main`, como las otras capacidades) | **Fecha**:
2026-11-14 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación `specs/004-linea-de-tiempo/spec.md`, confirmada en los commits
`1785648` y `2fecb64` (este último: historia se mide con la cripta de referencia), y las
indicaciones del grupo en `/speckit-plan`, con sus mediciones.

**Artefactos**: [research.md](research.md) (decisiones D1–D13 y alternativas) ·
[data-model.md](data-model.md) · [contracts/](contracts/) · [quickstart.md](quickstart.md)

Este plan es el borrador de la sección P2 §5.5 de `DECISIONES.md` (P2 §7.1). Las decisiones son
**provisionales** hasta tener la evidencia de `--bench`; si una medición las cambia,
`DECISIONES.md` lo dirá.

## Resumen

Durante la partida, `historia <t>` y `historia #k` muestran cómo estaba la partida en ese momento,
sin tocar nada. `--replay … --hasta t` hace lo mismo con un log. Guardar y cargar conservan la
historia. La línea describe la partida tal como quedó después de los pergaminos.

Enfoque técnico (evalúa las indicaciones del grupo con sus números; detalle en research.md):

1. **Qué se guarda** (D1): la secuencia neta de comandos (unos 100 bytes por acción) y un punto de
   control cada K acciones. Los `RegistroAccion` de P1 no sirven fuera de la partida donde se
   registraron, porque referencian sus objetos.
2. **Cómo se reconstruye** (D2): **hacia adelante sobre el punto de control y deshacer después**.
   Copiar un punto en cada consulta cuesta 63 ms con 300 salas (36 ms en la otra máquina) y no cabe
   en 50 ms. Por eso la consulta re-ejecuta, sobre el punto anterior y con su propio historial sin
   límite, a lo sumo K acciones con `ejecutar_comando`. Después arma el resumen y las deshace con
   `Historial.deshacer_ultima`, el mecanismo del pergamino de P1. Deshacer cuesta un tercio de una
   acción (0,40 frente a 1,21 ms, medido). **Hacia atrás** (FR-429) cuesta lo mismo por consulta,
   pero exige re-ejecutar el tramo al crear cada punto y guardar todos sus cambios. Se mide y se
   descarta. Se acepta la indicación.
3. **La copia** (D3): `copy.deepcopy` con ganchos que **comparten** el contenido original de las
   salas y las fichas, y **dejan fuera** la búsqueda del cazador, la bitácora y el historial. Con 300
   salas: −10 % de tiempo y −17 % de memoria (57 ms y 0,85 MB). Compartir las fichas es
   obligatorio: son un método del repositorio, que tiene la fuente de red. Se acepta la indicación;
   la ganancia es modesta y se mide (L7).
4. **K por defecto = 22** (D4): consulta ≈ 0,95 K (a + u) ≈ 34 ms (< 50, FR-432); un punto en el
   4,5 % de las acciones (< 5 %, el p95 del ciclo no lo ve, FR-433); memoria ≈ 227 copias ≈ 193 a
   341 MB con 5 000 acciones, 1/22 de la copia por acción (< 1/3, FR-434). La ventana posible es
   21 ≤ K ≤ 32. Se acepta el equilibrio que propone el grupo.
5. **Salas sin contenido en el punto** (D7): al re-simular se cargan desde el mapa vivo, que ya las
   tiene porque el jugador entró en ellas. Sin red (FR-407). Se acepta la indicación.
6. **Reutilización de P1** (D12, D11): `Historial` y `Cambio` para deshacer, `ejecutar_comando` para
   re-ejecutar, `armar_partida` y el recorrido de `EstadoPartida` (`escribir_general`,
   `escribir_sala`) para guardar los puntos en el formato 3. Se acepta la indicación.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias**: biblioteca estándar (`copy`; `tracemalloc` solo en el bench), `requests` y
`struct`. No se agrega ninguna (principio I).

**Almacenamiento**: archivo de partida en **formato 3** (binario y JSON) con un bloque `linea`
(contracts/guardado.md). Los formatos 1 y 2 se rechazan. `partida.log` no cambia.

**Pruebas**: `unittest` (`python -m unittest`), en `tests/`.

**Plataforma**: equipo local del grupo (Windows 11), entre 1,7 y 3 veces más lento que el equipo
donde el grupo tomó sus medidas. También debe correr en el equipo de revisión.

**Tipo de proyecto**: juego de consola en un solo proyecto con MVC (`crypta/Modelo`,
`crypta/Vista`, `crypta/Controlador`, `crypta/Adaptadores`, `crypta/estructuras`, `crypta/bench`).

**Metas de rendimiento**:

- `historia`: p95 < 50 ms con 5 000 acciones en una cripta del tamaño de la de referencia (300
  salas) y K por defecto (FR-432).
- Ciclo de la 001 con la línea activa: p95 < 20 ms (FR-433).
- Memoria: ≤ 2,5 × al pasar de 2 500 a 5 000 acciones, y < 1/3 de la copia por acción (FR-434).
- La partida de escala (2 000 salas, 50 cazadores) se reporta sin límite.

**Restricciones**:

- Sin `dict`, `set`, `bisect` ni `collections` como estructura (principio I). El `memo` de
  `deepcopy` es interno de la biblioteca; no lo usamos como estructura propia.
- Determinismo total: la re-simulación usa el `random.Random` copiado del punto (principio II).
- Ninguna copia completa fuera de los puntos de control (principio VII).

**Escala**: partidas de 2 500 y 5 000 acciones con 300 salas; 1 000 acciones con 2 000 salas (solo el
K por defecto); K de 1 a 64.

No quedan puntos «NEEDS CLARIFICATION» técnicos. Hay tres puntos para el grupo al final de
research.md: la excepción de HU2-3 por los pergaminos (en un commit de spec aparte), la dependencia
de la 002 para el mapa conocido, y los límites de la escala.

## Revisión de la constitución (antes de la fase 0)

| Principio | Cumple | Cómo |
|---|---|---|
| I. Estructuras propias | Sí | `Vector` para entradas, decisiones y puntos; búsqueda binaria propia nueva en `crypta/estructuras/BusquedaBinaria.py`; `ListaDoble` dentro del `Historial` de P1. `copy` es biblioteca estándar y no reemplaza una estructura evaluada; su `memo` interno no se usa como índice nuestro. `tracemalloc`, solo en el bench. Sin dependencias nuevas. |
| II. Determinismo | Sí | Cada punto lleva su copia del `random.Random`. La re-simulación repite exactamente los mismos comandos y la misma secuencia de dados. La búsqueda del cazador se recrea, y la 001 demostró que da lo mismo que reutilizarla. Empates de reloj en `historia t`: la primera decisión. |
| III. MVC | Sí | `LineaDeTiempo`, `Reconstruccion` y `Resumen` en Modelo. `ejecutar_comando` se inyecta, así el Modelo no importa el Controlador. El texto es una función pura de Vista. `--replay … --hasta` y `--bench` no instancian la vista. |
| IV. Nada quemado | Sí | K por defecto es un parámetro de diseño del grupo, no un dato de cripta. Los tamaños del bench son parámetros de medición. cripta-06 se usa solo si está en la copia local. |
| V. Red y presupuesto | Sí | Las consultas nunca piden nada: el contenido sale del mapa vivo (D7). La prueba HU1-12 usa una fuente que falla y compara solicitudes y presupuesto. |
| VI. Rendimiento medido | Sí | Secciones L1–L8 de `--bench`, con los cinco K, la alternativa sin puntos de control, hacia atrás (FR-429) y las variantes de copia. |
| VII. Reversibilidad | Sí | Copias completas solo en los puntos de control, a lo sumo uno cada K acciones, con el estado del generador. Fuera de ellos, comandos. La consulta no consume tiempo, no va al log y no toca el historial vivo. |
| VIII. Primero la especificación | Sí | spec.md confirmada (`1785648`, `2fecb64`). Este plan no agrega reglas. La excepción de HU2-3 (pergaminos y posición del objeto actual, D6) va en spec.md en un commit propio antes de implementar. |
| IX. Trazabilidad | Sí | Lista de pruebas por FR abajo. Los seis casos del Apéndice B («Línea de tiempo») son HU1-2, HU1-3, HU1-8, HU2-1, HU3-2 y HU4-3. |
| X. Documentación | Pendiente en tareas | `DECISIONES.md` §5.5 desde research.md con la evidencia del bench; README con `--checkpoint-cada`, `--replay … --hasta`, `historia` y el K por defecto; `PROMPTS_LLM.md` con esta invocación. |
| XI. Compatibilidad con P1 | Sí | Los formatos 1 y 2 se rechazan (no se migran). El historial de retroceso de P1 se vuelve a medir con la carga nueva: deshacer cuesta 0,40 ms por acción con 300 salas, y L1 y L2 lo reportan. La agenda no cambia; L4 vuelve a medir el ciclo de la 001. |

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/004-linea-de-tiempo/
├── spec.md
├── plan.md              # este archivo
├── research.md          # decisiones D1–D13
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md           # historia, --checkpoint-cada, --replay … --hasta, códigos
│   ├── resumen.md       # texto exacto del resumen (FR-406)
│   ├── guardado.md      # formato 3 y rechazos
│   └── bench.md         # partidas sintéticas y secciones L1–L8
├── checklists/requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Código fuente: módulos afectados

```text
crypta/
├── estructuras/
│   └── BusquedaBinaria.py     # NUEVO: primera posición con clave ≥ valor en un Vector ordenado (D5)
├── Modelo/
│   ├── LineaDeTiempo.py       # NUEVO: EntradaLinea, PuntoDeControl, Objetivo, LineaDeTiempo (D1, D5, D6)
│   ├── Reconstruccion.py      # NUEVO: consulta hacia adelante + deshacer; Sello (D2, D7, D8)
│   ├── Resumen.py             # NUEVO: datos de FR-406 desde una Partida (D10)
│   ├── Historial.py           # CAMBIA: limite=None = sin límite
│   ├── Partida.py             # CAMBIA: tope_tiempo (D9); __deepcopy__ (D3)
│   ├── Sala.py                # CAMBIA: __deepcopy__ comparte el contenido original (D3)
│   └── Puerta.py              # CAMBIA: la copia del estado deja observador = None (D3)
├── Vista/
│   ├── FormatoResumen.py      # NUEVO: texto puro del resumen (contracts/resumen.md)
│   └── VistaConsola.py        # CAMBIA: mostrar_resumen; ayuda con historia
├── Controlador/
│   ├── Comandos.py            # CAMBIA: ejecutar_y_registrar; leer_historia (FR-405)
│   ├── Controlador.py         # CAMBIA: comando historia; línea al jugar, guardar y cargar; aviso de K
│   └── Reproductor.py         # CAMBIA: construye la línea al reproducir; Reproduccion.linea
├── Adaptadores/
│   ├── EstadoPartida.py       # CAMBIA: escribir_linea / leer_linea con el recorrido existente (D11)
│   ├── GuardadoBinario.py     # CAMBIA: formato 3, bloque linea
│   └── GuardadoJSON.py        # CAMBIA: formato 3, bloque linea
├── bench/
│   ├── bench_linea.py         # NUEVO: partidas sintéticas y secciones L1–L8
│   └── bench.py               # CAMBIA: llama a las secciones nuevas; código ≠ 0 si L3 falla
└── main.py                    # CAMBIA: --checkpoint-cada, --hasta, flujo de --replay … --hasta

tests/
├── test_linea_tiempo.py           # NUEVO: HU1, HU2, casos borde, sello y partida viva intactos
├── test_equivalencia_linea.py     # NUEVO: SC-402 (≥ 20 partidas por semilla, ≥ 3 K, con pergaminos)
├── test_replay_hasta.py           # NUEVO: HU3 y códigos
├── test_busqueda_binaria.py       # NUEVO: vacío, empates, fuera de rango
├── test_persistencia.py           # CAMBIA: formato 3, HU4, rechazo de los formatos 1 y 2
├── test_controlador.py            # CAMBIA: historia no va al log; argumentos
└── test_bench.py                  # CAMBIA: huella; L1–L8 en modo rápido; L3 saboteada da ERROR
```

**Decisión de estructura**: se mantiene el proyecto único. La línea de tiempo vive al lado de la
`Partida` (en el `Controlador` y en la `Reproduccion`), no dentro de ella. Si fuera parte de la
`Partida`, copiar un punto de control copiaría todos los demás.

## Estructuras y complejidad

n acciones netas, K acciones entre puntos, V salas, a y u costo de una acción y de deshacerla, c y s
costo y tamaño de una copia.

| Operación | Cuándo | Estructura | Complejidad |
|---|---|---|---|
| Registrar un comando | cada comando | `Vector` de entradas y de decisiones | O(1) amortizado |
| Crear un punto de control | cada K acciones | `deepcopy` con ganchos | O(estado): c = 57 ms con 300 salas y 454 ms con 2 000 |
| Pergamino | cada uso | quitar del final de los `Vector` | O(lo revertido) (FR-412) |
| Ubicar `#k` | consulta | `decisiones[k − 1]` | O(1) |
| Ubicar `t` | consulta | búsqueda binaria sobre `decisiones` | O(log n) |
| Ubicar el punto de control | consulta | j = ⌊m/K⌋ en `puntos` | O(1): se examina 1 punto (FR-425) |
| Reconstruir | consulta | re-ejecutar + deshacer sobre el punto | ≤ K (a + u) + O(K) del sello |
| Cargar el contenido de una sala al re-simular | si falta en el punto | `Mapa.obtener_sala` vivo | O(log V) |
| Resumen | consulta | — | O(inventario + enemigos de la sala + mapa conocido) |
| Memoria | — | — | (n/K) s + O(n) entradas |
| Guardar / cargar | a pedido | recorrido de `EstadoPartida` por punto | O((n/K) · estado + n) |
| Hacia atrás (descartada) | solo bench | B_j con los cambios del tramo | consulta del mismo orden; creación c + K a; memoria más todos los cambios |
| Sin puntos de control | solo bench | solo el punto 0 | O(n (a + u)) por consulta |

## Alternativas descartadas (resumen; detalle en research.md)

- Guardar todos los `RegistroAccion` o una copia por acción (D1).
- Copiar el punto en cada consulta; hacia atrás invirtiendo cambios; aplicar cambios registrados
  con valor nuevo (exige rediseñar `Cambio` y traducir referencias); deshacer y rehacer sobre la
  partida viva; sin puntos de control (D2).
- `deepcopy` sin ganchos; copia por el recorrido de `EstadoPartida`; copia incremental por salas
  (D3).
- K < 21 (FR-433) o K > 32 (FR-432) (D4).
- `ArbolBusqueda` por reloj (D5).
- Al guardar, reconstruir los puntos al cargar (D11).

## Mediciones planificadas (FR-427 a FR-434)

Detalle en [contracts/bench.md](contracts/bench.md).

| FR | Sección | Configuración | Criterio |
|---|---|---|---|
| FR-427, HU5-5 | generador | semilla fija, dos ejecuciones | huella idéntica |
| FR-428, FR-432, SC-404, SC-406, HU5-6, HU5-7 | L1 | (a) cripta del tamaño de la de referencia (cripta-06 si tiene contenidos; si no, sintética de 300 salas con unos 20 enemigos), ≥ 5 000 acciones, K = 10, 16, 22, 32, 64 y sin puntos de control, liberando la línea de cada K antes de armar la siguiente; (b) 2 000 salas con 50 cazadores, **1 000 acciones** y solo el K por defecto (con 5 000 serían ~2,2 GB de puntos) | (a) con el K por defecto: p95 < 50 ms (principio VI); (b) se reporta y, si pasa de 50 ms, va a Límites |
| FR-429 | L2 | (a), K por defecto | se reporta adelante frente a atrás: consulta, creación y memoria |
| FR-430 | L3 | todas las variantes contra el oráculo tomado de la partida viva | 0 diferencias; si no, ERROR y código ≠ 0 |
| FR-433, SC-405, HU5-8 | L4 | B7 de la 001 con la línea y el K por defecto, ≥ 500 acciones | p95 < 20 ms (principio VI) |
| FR-424, FR-434, SC-409, HU5-9 | L5 | (a), 2 500 y 5 000 acciones | ≤ 2,5 × y < 1/3 de la copia por acción |
| FR-425, HU5-10 | L6 | (a), 2 500 y 5 000 acciones | puntos examinados constantes |
| D3 | L7 | (a) y (b) | se reportan tres formas de copiar |
| FR-417, D11 | L8 | (a), 5 000 acciones | se reportan tamaño y tiempos |
| FR-431, HU5-12 | todas | — | sin vista ni red (fuente y vista que fallan) |

## Impacto en el guardado, el log y la copia local

- **Archivo de partida**: pasa al formato 3 con el bloque `linea` (contracts/guardado.md). Los
  formatos 1 y 2 se rechazan sin migrar (FR-419).
- **`partida.log`**: sin cambios. `historia` nunca se anota, así que una partida con consultas y la
  misma sin ellas dan el mismo log, byte por byte (SC-403).
- **Copia local de la cripta**: sin cambios.

## Pruebas por FR

Cada prueba cita su FR en el nombre del método o en el docstring (principio IX). «HUx-n» es el
escenario n de la historia x. «Oráculo» son los resúmenes tomados de la partida viva en cada
decisión y en instantes intermedios mientras se juega.

| FR | Prueba (archivo · caso) | Escenarios |
|---|---|---|
| FR-401 | `test_linea_tiempo` · tres eventos en 300 sin decisión; decisión en 300 con un evento posterior en la agenda; `historia 0`; t entre dos eventos; t = reloj | HU1-1, HU1-3, HU1-4, casos borde |
| FR-402, FR-404 | `test_linea_tiempo` · 40 acciones: #1, #20 y #41 contra el oráculo; #0 y #42 rechazados | HU1-5, HU1-6 |
| FR-403 | `test_linea_tiempo` · reloj 1 200: `historia 500` contra el oráculo; `historia 1500` rechazado | HU1-1, HU1-2 |
| FR-405 | `test_linea_tiempo` · `historia`, `abc`, `-5`, `2,5`, `#x` → `ComandoInvalido`; nada cambia | HU1-7 |
| FR-406 | `test_linea_tiempo` · texto completo contra contracts/resumen.md; igual en partida, replay y tras cargar | HU1-1, HU3-1, HU4-1 |
| FR-407 | `test_linea_tiempo` · 30 consultas: la serialización de la partida viva, el estado del generador, el historial, el log, las solicitudes y el presupuesto no cambian; fuente que falla; serialización del punto igual antes y después sin el contenido de las salas que la consulta cargó, y la misma consulta repetida da el mismo resumen (D7, D8) | HU1-8, HU1-12 |
| FR-408 | `test_linea_tiempo` · misma partida con y sin 30 consultas: mismo estado, log y resultado | HU1-9 |
| FR-409 | `test_linea_tiempo` · victoria y derrota → mensaje de `--replay … --hasta` | HU1-10 |
| FR-410, FR-411 | `test_linea_tiempo` · 30 acciones y 3 pergaminos: #28 = actual; ninguna consulta muestra lo revertido; igual a la partida sin esas acciones salvo pergaminos gastados, pergaminos de las salas y objeto actual (D6) | HU2-1, HU2-2, HU2-3 |
| FR-412 | `test_linea_tiempo` · el pergamino examina un número de entradas que no depende de n (contador); punto que cruza la frontera de un tramo | HU2-4, casos borde |
| FR-413, FR-414 | `test_replay_hasta` · `--hasta 500` da el mismo texto que `historia 500`; vista que falla; con pergamino | HU3-1, HU3-5 |
| FR-415 | `test_replay_hasta` · terminada antes de t; log que acaba antes de t; log ilegible → 1 | HU3-2, HU3-3 |
| FR-416 | `test_replay_hasta` · `--hasta` sin `--replay`; `-1`; `x` | HU3-4 |
| FR-417 | `test_persistencia` · guardar, cargar y comparar 50 consultas; la partida sigue igual | HU4-1 |
| FR-418 | `test_persistencia` · otro `--checkpoint-cada` al cargar → aviso y K guardado | HU4-2 |
| FR-419 | `test_persistencia` · archivos de formato 1 y 2 rechazados; la partida en curso no cambia | HU4-3, HU4-4 |
| FR-420 | `test_controlador` · `--checkpoint-cada 0`, `-3`, `x` → error de argumentos | HU5-4 |
| FR-421, SC-402 | `test_equivalencia_linea` · ≥ 20 partidas por semilla con pergaminos; K = 1, 10, 22 y sin puntos: todas las consultas iguales al oráculo | HU5-1 |
| FR-422, FR-424 | `test_linea_tiempo` · 5 000 acciones con K = 10: puntos en 0, 10, 20…; nada más que entradas entre ellos | HU5-3 |
| FR-423 | `test_linea_tiempo` · contador de acciones re-ejecutadas y deshechas ≤ K en cada consulta | HU5-2 |
| FR-425 | `test_linea_tiempo` · puntos examinados = 1 con 2 500 y 5 000 acciones | HU5-10 |
| FR-426 | `test_linea_tiempo` · log de la 001 reproducido con y sin línea: mismo estado final y resultado; `python -m unittest` completo | HU5-11 |
| FR-427 a FR-431 | `test_bench` · huella repetible; L1–L8 en modo rápido; L3 con una variante saboteada da ERROR; fuente y vista que fallan | HU5-5, HU5-6, HU5-12 |
| FR-432 a FR-434 | `--bench` (L1, L4, L5); `test_bench` solo comprueba que se calculan y reportan | HU5-7, HU5-8, HU5-9 |
| SC-403 | `test_linea_tiempo` · log con y sin consultas, igual byte por byte | — |
| SC-408 | `python -m unittest` completo; solo cambian las pruebas del formato del archivo de partida | — |
| Estructuras | `test_busqueda_binaria` · vacío, un elemento, empates (primera), valor mayor que todos | — |

## Revisión de la constitución (después del diseño)

Sin cambios respecto a la revisión anterior. La única estructura nueva (`BusquedaBinaria`) es
propia. La copia usa `copy` de la biblioteca estándar sin construir índices nuestros. No hay
dependencias nuevas ni constantes de cripta. Las únicas copias completas son los puntos de control,
y la consulta no toca la partida viva ni la red.

La excepción de HU2-3 (research D6) ya está en spec.md y se confirma en su propio commit antes de
implementar (principio VIII).

## Seguimiento de complejidad

No aplica: no hay violaciones de la constitución.

## Límites conocidos (para `DECISIONES.md` §5.5)

- **Escala** (2 000 salas, 50 cazadores): `historia` ≈ 100 a 210 ms con K = 22 (> 50 ms); una copia
  de 454 ms cada 22 acciones (el p95 no la ve, pero la media del ciclo sube unos 20 ms y el máximo
  llega a casi medio segundo); unos 2,2 GB de puntos con 5 000 acciones, por eso el bench de escala
  usa 1 000 acciones (≈ 45 puntos, ≈ 430 MB).
- Con 300 salas, crear un punto (57 ms) es una pausa imperceptible cada 22 acciones.
- El margen de FR-433 es estrecho (4,5 % frente a 5 %). Si el bench muestra que el p95 ve las
  copias, se sube K y se pierde margen en FR-432 (research D4).
