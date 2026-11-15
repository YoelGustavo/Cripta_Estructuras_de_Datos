# Plan de implementación: Niebla de guerra e «ir a»

**Rama**: `002-niebla-ir-a` (se trabaja en `main`, como las otras capacidades) | **Fecha**:
2026-11-15 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación `specs/002-niebla-ir-a/spec.md`, confirmada en el commit `3faa7a5`
(specify + clarify), y las indicaciones del grupo en `/speckit-plan`, con su medición (búsqueda
completa con 2 000 salas: media 6,4 ms y p95 11 ms en otra máquina).

**Artefactos**: [research.md](research.md) (decisiones D1–D14 y alternativas) ·
[data-model.md](data-model.md) · [contracts/](contracts/) · [quickstart.md](quickstart.md)

Este plan es el borrador de la sección P2 §5.3 de `DECISIONES.md` (P2 §7.1). Las decisiones son
**provisionales** hasta tener la evidencia de `--bench`; si una medición las cambia,
`DECISIONES.md` lo dirá.

## Resumen

El jugador solo ve lo que ha explorado: salas exploradas, avistadas y desconocidas, y cada puerta
como la vio la última vez. La antorcha explora las vecinas al entrar. `mapa` muestra lo conocido.
`ir a <sala>` lleva al jugador por la ruta conocida más barata, paso a paso, y se detiene si pasa
algo. El conocimiento es estado del juego: lo revierten el pergamino, el guardado y la línea de
tiempo.

Enfoque técnico (evalúa las indicaciones del grupo; detalle en research.md):

1. **Mapa conocido** (D1, D2): el estado de cada sala en un `Vector` por el índice denso de la 001, y
   el estado recordado de cada puerta en su `EstadoPuerta` compartido (un solo valor para los dos
   lados, FR-205). Consultar es O(1) (FR-235). Se acepta la indicación.
2. **Reversible** (D3): todo cambio pasa por `MapaConocido`, que anota un `Cambio` en el historial de
   P1 **solo si el valor cambia**, siempre con `partida._anotar` (busca el historial vigente en cada
   llamada; `leer_linea` reemplaza el historial de cada punto de control por asignación). El pergamino lo revierte (FR-224) y la línea de tiempo de la 004 lo
   trae sin cambios: la copia del punto de control incluye el `Vector` y los `recordada`, y la
   reconstrucción deshace con el mismo historial. Explorar y deshacer cuestan O(salas reveladas)
   (FR-236). Se acepta la indicación.
3. **Cuándo se observa** (D4): al entrar a una sala, con la antorcha también a sus vecinas, y al
   llegar el turno del jugador, antes de cada decisión (FR-204). Explorar solo usa el esqueleto: sin
   red, sin despertar a nadie (FR-214).
4. **Ruta de «ir a»** (D5, D6): distancias **desde el destino** con `DistanciasLimitadas` de la 001,
   por las entradas cuyo origen está explorado y cuya puerta se recuerda abierta. Después de un paso
   el destino no cambia y las distancias siguen valiendo: el paso siguiente cuesta O(grado). Se
   invalida, como en la 001, solo si cambia algo con un extremo asentado (demostración en D6). Se
   comparte la estructura con el cazador y se separan las reglas (P2 §5.3). Se acepta la indicación.
5. **Guardado** (D9): formato 4 con `recordada` por salida y la lista de salas conocidas; se
   rechazan los formatos 1, 2 y 3 (FR-227). Se acepta la indicación.
6. **`partida.log`** (D10): `# ir a <id>` antes del primer `mover` del viaje; `leer_registro` ignora
   los comentarios; el formato de registro sigue en 1, así que los logs de P1 se leen igual. Se
   acepta la indicación.
7. **Bitácora** (D11): solo lo de la sala del jugador o lo que le pasa al jugador. Cambian tres
   avisos: cierre automático, regeneración y rearme. Se acepta la indicación.
8. **T057 de la 004** (D11): la línea «Mapa conocido» del resumen y la prueba de HU1-11 se hacen
   aquí.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias**: biblioteca estándar, `requests` y `struct`. No se agrega ninguna (principio I).

**Almacenamiento**: archivo de partida en **formato 4** (binario y JSON), con el conocimiento
(contracts/guardado.md). `partida.log` sigue en el formato de registro 1, con comentarios.

**Pruebas**: `unittest` (`python -m unittest`), en `tests/`.

**Plataforma**: equipo local del grupo (Windows 11), entre 1,7 y 3 veces más lento que el equipo
donde el grupo tomó sus medidas (plan de la 004). También debe correr en el equipo de revisión.

**Tipo de proyecto**: juego de consola en un solo proyecto con MVC (`crypta/Modelo`,
`crypta/Vista`, `crypta/Controlador`, `crypta/Adaptadores`, `crypta/estructuras`, `crypta/bench`).

**Metas de rendimiento**:

- Paso de «ir a»: p95 < 5 ms sobre todos los pasos de ≥ 20 viajes (≥ 200 pasos) con el mapa conocido
  completo de 2 000 salas y de la cripta del tamaño de la de referencia (300 salas); primer paso
  aparte (FR-234).
- Consultas al mapa conocido: cociente 2 000/200 ≤ 2 (FR-235).
- Explorar con antorcha y deshacer: cociente 2 000/200 ≤ 2 con las mismas salas reveladas (FR-236).
- Sin regresión en el ciclo de la 001 (20 ms) ni en `historia` de la 004 (50 ms): la observación
  agrega O(4) por decisión y una copia de V enteros por punto de control.

**Restricciones**:

- Sin `dict`, `set`, `heapq`, `bisect` ni `collections` como estructura (principio I).
- El paso elegido es siempre el de un cálculo desde cero sobre el mapa conocido de ese instante
  (principio II, SC-203).
- Nada de lo que trae la precarga llega a la vista ni a «ir a» salvo por el mapa conocido (FR-209).

**Escala**: criptas de 300, 2 000 y 20 000 salas (esta última solo en N2); mapas conocidos de 200 y
2 000 salas.

No quedan puntos «NEEDS CLARIFICATION» técnicos. Los tres puntos que la primera versión dejaba
abiertos ya los decidió el grupo (research D14): la llave se sigue mostrando en las puertas de la
sala actual; el riesgo de FR-234 se acepta y, si no cumple, va a Límites con los números de N3; las
salidas hacia salas que no existen no avistan nada.

## Revisión de la constitución (antes de la fase 0)

| Principio | Cumple | Cómo |
|---|---|---|
| I. Estructuras propias | Sí | `Vector` para los estados; un campo en `EstadoPuerta`; `DistanciasLimitadas` y `MonticuloMin` de la 001 para la ruta; `RutaPorCazador` como verificador; `ArbolBusqueda` solo como alternativa del bench. Ningún `dict`, `set`, `heapq`, `bisect` ni `collections`. Sin dependencias nuevas. |
| II. Determinismo | Sí | Desempate de la ruta igual que el cazador (menor id, luego N, S, E, O). La reutilización se demuestra (D6) y se comprueba paso a paso contra un cálculo desde cero (SC-203, N4). «ir a» no usa el azar. Ni el tiempo real ni la red deciden nada: un paso imposible se detiene sin mover. |
| III. MVC | Sí | `MapaConocido`, `RutaConocida` y `Viaje` en Modelo, sin red ni archivos. El bucle de `ir a` en `Comandos.ejecutar_ir_a`, con `garantizar_sala` y la función por paso inyectadas. Textos en funciones puras de Vista. `--bench` y `--replay` sin vista. |
| IV. Nada quemado | Sí | Ningún id, costo ni tamaño de cripta. La cripta de referencia del bench es la copia local más grande, sin escribir su id. Las constantes son estados y motivos de la spec. |
| V. Red y presupuesto | Sí | La antorcha no pide nada (FR-214, prueba con fuente que cuenta solicitudes). `mapa` no pide nada. Cada paso de `ir a` pasa por `Controlador._ejecutar_comando_jugador`, el mismo camino que un comando escrito a mano (incluidos `precargar_async` y `garantizar_sala`); una prueba con fuente que cuenta compara un viaje de 3 pasos con los 3 `mover` escritos a mano. Sin presupuesto, el viaje se detiene sin mover. |
| VI. Rendimiento medido | Sí | N1 a N4 de `--bench`, con la alternativa descartada en cada una (FR-230, FR-231), la fila de la cripta del tamaño de la de referencia y el primer paso aparte. |
| VII. Reversibilidad | Sí | Cada cambio de conocimiento es un `Cambio` con el valor anterior, solo si el valor cambia. Ninguna copia completa: la única es la del punto de control de la 004. La ruta y el viaje no son estado del juego. |
| VIII. Primero la especificación | Sí | spec.md confirmada en `3faa7a5`. Este plan no agrega reglas: los textos de los mensajes, el orden en que se elige el texto del motivo y los formatos son decisiones de diseño. |
| IX. Trazabilidad | Sí | Lista de pruebas por FR abajo. Los seis casos del Apéndice B («Niebla de guerra e ir a») son HU2-2, HU3-1, HU3-7, HU3-10, HU4-1 y HU4-2. |
| X. Documentación | Pendiente en tareas | `DECISIONES.md` §5.3 desde research.md con la evidencia de N1 a N4; README con `mapa` e `ir a`; `PROMPTS_LLM.md` con esta invocación. |
| XI. Compatibilidad con P1 | Sí | Los logs de P1 y de la 001 se reproducen igual (formato de registro 1, sin comentarios). Los formatos de guardado 1 a 3 se rechazan sin migrar. El historial de P1 se vuelve a medir con la carga nueva: N2 mide registrar y deshacer los cambios de conocimiento. |

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/002-niebla-ir-a/
├── spec.md
├── plan.md              # este archivo
├── research.md          # decisiones D1–D14
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md           # mapa, ir a, mensajes de rechazo, partida.log
│   ├── vista.md         # vista, texto de mapa, motivos de parada, bitácora, línea del resumen
│   ├── guardado.md      # formato 4 y rechazos
│   └── bench.md         # criptas, mapas conocidos y secciones N1–N4
├── checklists/requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Código fuente: módulos afectados

```text
crypta/
├── Modelo/
│   ├── MapaConocido.py        # NUEVO: estados por índice, explorar/observar/avistar, restaurar (D1–D4);
│                              #        anota con partida._anotar (D3)
│   ├── RutaConocida.py        # NUEVO: distancias desde el destino, invalidación selectiva (D5, D6)
│   ├── Viaje.py               # NUEVO: validar, siguiente dirección, paradas (D8)
│   ├── Puerta.py              # CAMBIA: EstadoPuerta.recordada; Puerta(…, recordada); compartir_estado_con
│   ├── Partida.py             # CAMBIA: conocimiento, ruta_conocida(), enemigos_al_entrar; explorar al entrar
│   │                          #         y al iniciar; observar en el turno del jugador; antorcha;
│   │                          #         pergamino invalida la ruta; bitácora (FR-208); _NO_SE_COPIAN
│   └── Resumen.py             # CAMBIA: mapa_conocido = MapaResumido; armar_mapa_resumido (T057)
├── Vista/
│   ├── FormatoMapa.py         # NUEVO: formatear_mapa, texto_motivo (contracts/vista.md)
│   ├── FormatoResumen.py      # CAMBIA: línea «Mapa conocido» con las líneas de FormatoMapa (T057)
│   └── VistaConsola.py        # CAMBIA: salidas desde recordada; mostrar_mapa; ayuda
├── Controlador/
│   ├── Comandos.py            # CAMBIA: leer_ir_a; ejecutar_ir_a(partida, id, ejecutar_paso, …)
│   └── Controlador.py         # CAMBIA: _ejecutar_comando_jugador (lo usan el comando escrito a mano
│                              #         y cada paso de ir a); mapa (antes de traducir); ir a; motivo
├── Adaptadores/
│   ├── RegistroPartida.py     # CAMBIA: anotar_comentario; leer_registro ignora «#»
│   ├── EstadoPartida.py       # CAMBIA: recordada por salida; grupo conocimiento; armar_partida lo restaura
│   ├── GuardadoBinario.py     # CAMBIA: FORMATO_GUARDADO = 4
│   └── GuardadoJSON.py        # CAMBIA: FORMATO_JSON = 4
└── bench/
    ├── bench_niebla.py        # NUEVO: criptas, mapas conocidos, viajes y secciones N1–N4; carpeta de
    │                          #        copias como parámetro
    ├── bench_cazador.py       # CAMBIA: tamaño (300, 20, 15) en TAMANOS
    └── bench.py               # CAMBIA: registra niebla_n1 … niebla_n4; código ≠ 0 si N4 falla

tests/
├── test_niebla.py                 # NUEVO: HU1, HU2, casos borde, bitácora, mapa
├── test_ir_a.py                   # NUEVO: HU3, log y replay
├── test_equivalencia_niebla.py    # NUEVO: SC-202 y SC-203 (≥ 20 partidas por semilla)
├── test_mapa_conocido.py          # NUEVO: estructura (consultas, cambios, deshacer, restaurar)
├── test_persistencia.py           # CAMBIA: formato 4, HU4-3, rechazo de 1, 2 y 3
├── test_pergaminos.py             # CAMBIA: HU4-1, HU4-2
├── test_linea_tiempo.py           # CAMBIA: TestMapaConocidoEnHistoria (T057, HU1-11 de la 004) y HU4-5
├── test_resumen.py                # CAMBIA: la línea «Mapa conocido» deja de ser fija
├── test_controlador.py            # CAMBIA: mapa e ir a no van al log; argumentos
└── test_bench.py                  # CAMBIA: huella; N1–N4 en modo rápido; N4 saboteada da ERROR
```

**Decisión de estructura**: se mantiene el proyecto único. El conocimiento vive dentro de la
`Partida` (es estado del juego y debe ir en la copia del punto de control); la ruta de «ir a» vive
al lado, como el `Perseguidor`, porque no es estado del juego.

## Estructuras y complejidad

V salas, E salidas, n salas conocidas, g grado de una sala (≤ 4).

| Operación | Cuándo | Estructura | Complejidad |
|---|---|---|---|
| Estado de una sala | vista, ruta, antorcha | `Vector` por índice | O(1) (FR-235) |
| Estado recordado de una puerta | vista, ruta | `EstadoPuerta.recordada` | O(1) (FR-235) |
| Estado de una sala por id | `ir a <id>` | `Mapa.obtener_sala` + `Vector` | O(log V), una vez por orden |
| Entrar a una sala | cada `mover` | `explorar` | O(g) |
| Entrar con antorcha | cada `mover` con antorcha | `explorar` de la sala y de sus vecinas | O(g²) = O(1) (FR-236) |
| Observar antes de decidir | cada decisión | `observar` | O(g) |
| Registrar y deshacer | cada cambio real | `Cambio` en el historial de P1 | O(1) por cambio (FR-236) |
| Primer paso de un viaje | cada `ir a` | `DistanciasLimitadas` desde el destino | O((V + E) log V) en el peor caso; asienta solo las salas con distancia ≤ la de la sala actual |
| Paso siguiente sin cambios | cada paso | distancias asentadas | O(g) |
| Aviso de un cambio de conocimiento | al observar o explorar | extremos asentados | O(1) por puerta, O(g) por sala |
| `mapa` y resumen | a pedido | recorrido del `Vector` | O(V + salidas exploradas) |
| Guardar / cargar el conocimiento | a pedido | lista de salas conocidas y `recordada` por salida | O(V + E); validar en O(V + E) |
| Memoria | — | `Vector` de V enteros + un campo por `EstadoPuerta` + 3 `Vector` de V de la ruta | O(V + E) |

## Alternativas descartadas (resumen; detalle en research.md)

- `ArbolBusqueda` por id para las salas y por (sala, dirección) para las puertas (D1, D2; N1).
- Copiar el mapa conocido por acción para revertir (D3; prohibido por VII, N2 solo lo mide).
- Recalcular la ruta desde cero en cada paso; búsqueda hacia adelante desde la sala actual;
  invalidación total (D5, D6; N3).
- Una sola búsqueda compartida con el cazador (D5): el cazador la reinicia cada vez que el jugador se
  mueve.
- Mirar el contenido de la sala destino para la parada por enemigos (D8; violaría FR-209).
- Migrar el formato 3; subir el formato del registro (D9, D10).

## Mediciones planificadas (FR-229 a FR-236)

Detalle en [contracts/bench.md](contracts/bench.md).

| FR | Sección | Configuración | Criterio |
|---|---|---|---|
| FR-229, HU5-1 | huella | semilla fija, dos ejecuciones | huella idéntica |
| FR-230, FR-235, SC-205, HU5-2, HU5-5 | N1 | 2 000 salas con 200 y 2 000 exploradas; `Vector` + `EstadoPuerta` frente a `ArbolBusqueda` armado con `desde_ordenados` | elegida: cociente ≤ 2 (la alternativa también puede cumplirlo; se descarta por costo por consulta y por escribir los dos lados) |
| FR-230, FR-236, SC-205, HU5-6 | N2 | 20 000 salas con mapas de 200 y 2 000; mismas entradas con antorcha, a más de 2 pasos de la región de 2 000; frente a copia por acción | elegida: cociente ≤ 2 al explorar y al deshacer; ERROR si los cambios por entrada difieren entre los dos mapas |
| FR-231, FR-234, SC-204, HU5-3, HU5-4 | N3 | (a) 2 000 salas, mapa completo; (b) conocimiento desactualizado; (c) tamaño de la de referencia (copia más grande de la carpeta que recibe la sección, cripta-06 si está, 300 salas; las pruebas pasan una carpeta vacía); ≥ 20 viajes, ≥ 200 pasos; selectiva, total y recalcular | (a) y (c): p95 < 5 ms (principio VI); primer paso aparte, a Límites si pasa de 5 ms |
| FR-232, SC-203 | N4 | todos los pasos, consultas y entradas de N1 a N3 | 0 diferencias; si no, ERROR y código ≠ 0 |
| FR-233, HU5-7 | todas | — | sin vista ni red (fuente y vista que fallan) |

Además, se vuelven a correr B7 de la 001 y L1 y L4 de la 004 para comprobar que la observación y el
conocimiento no las sacan de sus límites (principio XI).

## Impacto en el guardado, el log y la copia local

- **Archivo de partida**: formato 4 (contracts/guardado.md). Los formatos 1, 2 y 3 se rechazan sin
  migrar (FR-227). Firmas sin cambios.
- **`partida.log`**: comentarios `# ir a <id>`; formato de registro 1. Los logs de P1 y de la 001 se
  reproducen igual (SC-206).
- **Línea de tiempo (004)**: sin cambios de código salvo el resumen (T057). El conocimiento entra en
  los puntos de control con la copia de la `Partida` y en el bloque `linea` con `escribir_general` y
  `escribir_sala`.
- **Copia local de la cripta**: sin cambios.

## Pruebas por FR

Cada prueba cita su FR en el nombre del método o en el docstring (principio IX). «HUx-n» es el
escenario n de la historia x. Criptas sintéticas pequeñas armadas para cada caso.

| FR | Prueba (archivo · caso) | Escenarios |
|---|---|---|
| FR-201, FR-202, FR-203 | `test_niebla` · partida nueva: inicial explorada, vecinas avistadas, nada más; entrar a la 2; salida sin vuelta no avista | HU1-1, HU1-2, HU1-5 |
| FR-204, FR-205, FR-206 | `test_niebla` · puerta 2–4 cerrada lejos: se recuerda abierta; al volver a 2 o entrar a 4, cerrada desde ambos lados; cierre automático mientras espera: cerrada en la siguiente decisión | HU1-3, HU1-4 |
| FR-207 | `test_niebla` · la vista toma el estado de `recordada`; vecinas no exploradas solo por id | HU1-7 |
| FR-208 | `test_niebla` · regeneración, rearme y cierre en otra sala: nada en la bitácora; en la sala del jugador: sí | HU1-6 |
| FR-209 | `test_niebla` · precarga con contenido de salas no exploradas: vista, `mapa` y bitácora no lo revelan; el reporte de resolubilidad no cambia el mapa | HU1-10 |
| FR-210, FR-211 | `test_niebla`, `test_controlador` · texto de `mapa` contra contracts/vista.md; no cambia reloj, log, red ni estado; `mapa 3` inválido | HU1-1, HU1-8, HU1-9 |
| FR-212, FR-213, FR-215 | `test_niebla` · con antorcha: vecinas exploradas y sus destinos avistados; sin antorcha, solo la sala; después de apagarse, solo la sala y lo anterior sigue | HU2-1, HU2-3, HU2-4 |
| FR-214 | `test_niebla` · enemigos dormidos y trampas armadas siguen igual; misma partida con y sin antorcha: mismas solicitudes (fuente que cuenta) | HU2-2 |
| FR-216 | `test_ir_a` · no explorada y 99999: mismo mensaje, sin tiempo; sala actual; sin ruta; `ir a`, `ir a x`, `ir a 3 4` inválidos | HU3-1, HU3-2, HU3-3 |
| FR-217 | `test_ir_a` · 1–4 costo 500 contra 1–2–4 de 200; empate hacia 3 y 5; ruta más barata por una avistada no se usa | HU3-4, HU3-5, HU3-6 |
| FR-218 | `test_ir_a` · puerta recordada abierta y cerrada en realidad: se observa al llegar y se evita; sin alternativa, se detiene sin tiempo | HU3-7 |
| FR-219 | `test_ir_a` · dos casos, con la llave en el inventario: (1) **rechazo al inicio**: la única ruta cruza una puerta recordada cerrada; (2) **parada a medio camino**: la puerta se recordaba abierta y se descubre cerrada al llegar. En los dos, la puerta sigue cerrada y no hay `abrir` en el log | HU3-8 |
| FR-220 | `test_ir_a` · 4 pasos de 100, 250, 100 y 300: intervalos y eventos entre pasos | HU3-9 |
| FR-221 | `test_ir_a` · enemigos dormidos: se activan y se detiene; daño por ataque, trampa y veneno; presupuesto agotado y sin conexión en `garantizar_sala`: `PASO_IMPOSIBLE`, sin el paso ni su tiempo; un error lanzado dentro del `mover` no es `PASO_IMPOSIBLE` (se propaga); muerte y victoria; enemigo que entra sin atacar: sigue; ataca: se detiene | HU3-10 a HU3-13, HU3-16 |
| FR-222, FR-223 | `test_ir_a` · `# ir a` y tres `mover`; `--replay` da la misma partida; log de P1 igual que antes | HU3-14, HU3-15 |
| FR-220, FR-222 (principio V) | `test_controlador` · con fuente que cuenta: un viaje de 3 pasos hace las mismas solicitudes, en el mismo orden, que los 3 `mover` escritos a mano; la línea de tiempo y el log quedan iguales en los dos caminos (salvo el comentario) | HU3-9, HU3-14 |
| FR-224, FR-225 | `test_pergaminos` · antorcha con 4 vecinas: pergamino devuelve sala, vecinas y puertas; viaje de 3 pasos: revierte solo el último y no se reanuda | HU4-1, HU4-2 |
| FR-226, FR-227 | `test_persistencia` · 30 exploradas con puertas recordadas distintas de las reales: idéntico tras guardar y cargar (binario y JSON); formatos 1, 2 y 3 rechazados; lados con `recordada` distinto → `ErrorGuardado` | HU4-3, HU4-4 |
| FR-228 | `test_linea_tiempo` · `TestMapaConocidoEnHistoria` (**T057 de la 004**, HU1-11): puerta observada abierta en 300 y cerrada en 900, `historia 500` la muestra abierta y coincide con el oráculo; también tras cargar y con `--replay … --hasta` | HU4-5; 004 HU1-11 |
| FR-224, FR-228 | `test_linea_tiempo` · guardar con línea de tiempo, cargar y consultar dos veces el mismo instante: el mismo resumen, y el conocimiento del punto de control (estados y `recordada`) igual antes y después (research D3: `partida._anotar` llega al historial que `leer_linea` puso por asignación) | HU4-5 |
| FR-229 a FR-233 | `test_bench` · huella repetible; N1–N4 en modo rápido con una carpeta de copias vacía (sintética de 300 salas; nunca `cache/`); N4 con una variante saboteada da ERROR; N2 con entradas que revelan distinto en los dos mapas da ERROR; fuente y vista que fallan | HU5-1 a HU5-3, HU5-7 |
| FR-234 a FR-236 | `--bench` (N1, N2, N3); `test_bench` solo comprueba que se calculan y reportan | HU5-4 a HU5-6 |
| SC-202, SC-203 | `test_equivalencia_niebla` · ≥ 20 partidas por semilla con antorcha, puertas que cambian, pergaminos y viajes: la vista y `mapa` no nombran salas desconocidas ni dan el nombre de una avistada; cada paso de `ir a` coincide con `paso_desde_cero` | — |
| SC-206, SC-207 | `python -m unittest` completo. Solo cambian: las pruebas del formato del guardado (3 → 4), la línea «Mapa conocido» del resumen y las que esperaban avisos de la bitácora sobre otras salas (FR-208). Cada prueba ajustada lleva un comentario que cita FR-208 (si aplica) y SC-207 | — |
| Estructura | `test_mapa_conocido` · consultas, un `Cambio` solo si cambia el valor, deshacer en orden inverso, contadores, `restaurar` con datos inválidos | — |

## Revisión de la constitución (después del diseño)

Sin cambios respecto a la revisión anterior. No hay estructuras ni dependencias nuevas fuera de
`crypta/estructuras` (se reutilizan `Vector`, `DistanciasLimitadas`, `MonticuloMin`,
`RutaPorCazador` y, solo en el bench, `ArbolBusqueda`). No hay constantes de cripta. Las únicas
copias completas siguen siendo los puntos de control de la 004. La ruta y el viaje no son estado del
juego, y su reutilización está demostrada (D6) y comprobada (SC-203, N4).

## Seguimiento de complejidad

No aplica: no hay violaciones de la constitución.

## Límites conocidos (para `DECISIONES.md` §5.3)

- **Primer paso con 2 000 salas**: busca casi todo el mapa. Con la medición del grupo (6,4 ms de media
  y 11 ms de p95 en otra máquina), en este equipo serían de 11 a 33 ms, más de 5 ms. FR-234 lo admite
  como límite documentado. El p95 de todos los pasos solo cumple si los pasos que buscan son menos del
  5 % (research D6); N3 lo reporta. El grupo acepta el riesgo (research D14): si no cumple, va aquí
  con los números de N3.
- **Conocimiento muy cambiante**: cada puerta observada distinta en la región asentada obliga a buscar
  de nuevo; N3 (b) mide cuánto.
- **`ir a <id>`** busca la sala por id en O(log V), una vez por orden.
- **`mapa` y el resumen** crecen con el mapa conocido (O(V + salidas exploradas)); no tienen límite
  de tiempo en la spec.
