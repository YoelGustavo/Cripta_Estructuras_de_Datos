# Plan de implementación: Verificación de resolubilidad

**Rama**: `003-resolubilidad` (se trabaja en `main`, como las otras capacidades) | **Fecha**:
2026-11-13 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación `specs/003-resolubilidad/spec.md` (con las aclaraciones de la sesión
2026-11-12, confirmada en el commit `a9440b2`) y las indicaciones del grupo en `/speckit-plan`.

**Artefactos**: [research.md](research.md) (decisiones D1–D11 y alternativas) ·
[data-model.md](data-model.md) · [contracts/](contracts/) · [quickstart.md](quickstart.md)

Este plan es el borrador de la sección P2 §5.4 de `DECISIONES.md` (P2 §7.1). Las decisiones son
**provisionales** hasta tener la evidencia de `--bench`; si una medición las cambia,
`DECISIONES.md` lo dirá.

## Resumen

Antes de iniciar una partida, con solo el esqueleto y la ubicación de las llaves, el programa dice si
la cripta se puede ganar: si sí, el orden de llaves por rondas; si no, las llaves que faltan, la
frontera bloqueada, dónde están sus llaves, de qué llave depende cada una y los ciclos. Sin
`--forzar` la partida no inicia; `--verificar` hace solo esto.

Enfoque técnico (evalúa las indicaciones del grupo; detalle en research.md):

1. **Id de llave → número** (D1): se ordenan los ids con `ordenar`, se quitan repetidos y se arma un
   `ArbolBusqueda.desde_ordenados` (balanceado). El número es el **rango por id**, así que ordenar
   llaves es ordenar enteros y recorrer 0..K-1 ya da el orden por id. Se mide como alternativa
   `ArbolBusqueda` con `insertar`, que con ids en orden se degenera en una lista (P1 §4.4); una
   tabla hash propia queda como alternativa analizada, sin implementar ni medir.
2. **Un solo recorrido por oleadas** (D3): índice denso de sala, `Cola`, `Vector` de marcas. Las
   puertas cerradas cuya llave aún no se tiene se **estacionan** bajo esa llave y se liberan al
   cerrar la ronda en que se obtuvo. O(V + E + L) más ordenar las rondas. Se acepta la indicación.
3. **Dependencias por capas** (D4): si no es resoluble, el **mismo** recorrido sigue más allá de la
   frontera como recorrido 0-1 por niveles: cada capa cruza una puerta bloqueada más; dentro de una
   capa se inunda por origen ascendente, así cada sala recibe la menor (capa, primera llave) que pide
   FR-314. Las semillas de la primera capa son las puertas que quedaron estacionadas. Nunca un
   recorrido por llave. Se acepta la indicación.
4. **Ciclos** (D5): el grafo de dependencias tiene una salida por llave; se recorre una vez con
   marcas de tres estados y cada ciclo se rota a su menor id.
5. **Alternativa ingenua** (D8): repetir el recorrido completo por cada ronda (una por llave en
   criptas encadenadas) y un recorrido por llave para las dependencias. Sirve para el bench y como
   verificador en las pruebas. Se acepta la indicación.
6. **Integración** (D9): endpoint `/llaves` contado en el presupuesto, guardado en la copia local
   con la versión; la verificación va entre fijar el presupuesto y crear `partida.log`.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias**: biblioteca estándar, `requests` y `struct`. No se agrega ninguna (principio I).

**Almacenamiento**: copia local `cache/<cripta>.json` validada por versión, con un campo nuevo
`llaves`. El archivo de partida **no cambia** de formato.

**Pruebas**: `unittest` (`python -m unittest`), en `tests/`.

**Plataforma**: equipo local del grupo (Windows 11; también debe correr en el equipo de revisión).

**Tipo de proyecto**: juego de consola en un solo proyecto con MVC (`crypta/Modelo`,
`crypta/Vista`, `crypta/Controlador`, `crypta/Adaptadores`, `crypta/estructuras`, `crypta/bench`).

**Metas de rendimiento**: verificación completa < 200 ms con 2 000 salas y 500 llaves encadenadas
(FR-334); al duplicar el tamaño, el tiempo ≤ 3 × el anterior (FR-335).

**Restricciones**: sin `dict`, `set`, `heapq`, `bisect`, `collections` ni bibliotecas de grafos como
estructura; sin `sorted`/`list.sort` (principio I, P2 §6.2). Nada de ids de llaves ni de salas en el
código (principio IV). Determinismo total sin depender del orden de la respuesta (principio II).

**Escala**: criptas sintéticas de 500 a 8 000 salas y 125 a 2 000 llaves.

No quedan puntos «NEEDS CLARIFICATION».

## Revisión de la constitución (antes de la fase 0)

| Principio | Cumple | Cómo |
|---|---|---|
| I. Estructuras propias | Sí | `Vector`, `Cola`, `ArbolBusqueda`, `ordenar` de P1; nueva `NumeracionLlaves` en `crypta/estructuras`. Los `dict` de `json` solo se leen y se traducen a `UbicacionLlave` en un `Vector`. Las tuplas son elementos, no estructuras de búsqueda. |
| II. Determinismo | Sí | La verificación no usa azar. Todos los empates por id (D1: número = rango por id): rondas, frontera por (sala, N S E O), dependencias por (capa, menor id), ciclos desde su menor id. La respuesta se valida y se numera igual en cualquier orden (FR-320). El generador del bench usa su propio `random.Random(semilla)`. |
| III. MVC | Sí | Verificación en Modelo/estructuras, sin E/S; el texto en una función pura de Vista; red y disco detrás de `FuenteDatos`/`AlmacenDisco` (`obtener_llaves` en las tres fuentes, sin `if offline` en el modelo). `--verificar` y `--bench` no instancian la vista. |
| IV. Nada quemado | Sí | Ids, salas, `sala_salida` y `llave_salida` salen del servicio o de la copia local. Los tamaños del bench son parámetros de medición. |
| V. Red y presupuesto | Sí | `/llaves` pasa por `FuenteHTTP._get` (cuenta y respeta el presupuesto, también en 429); se pide después de `fijar_presupuesto`; una vez por versión (copia local). Sin solicitudes de contenido (FR-321). |
| VI. Rendimiento medido | Sí | Secciones R1–R5 del `--bench`, con la alternativa ingenua y la numeración por inserción medidas (contracts/bench.md). |
| VII. Reversibilidad | Sí (no aplica) | El resultado no es estado del juego: no entra en guardado, `partida.log` ni historial (FR-327). |
| VIII. Primero la especificación | Sí | spec.md confirmada en `a9440b2`, con el ajuste de FR-311 (orden de ubicaciones dentro de una sala) en un commit propio antes que este plan. Este plan no agrega reglas. |
| IX. Trazabilidad | Sí | Lista de pruebas por FR abajo; cada escenario HU1–HU5 tiene prueba, incluidos los 4 casos del Apéndice B. |
| X. Documentación | Pendiente en tareas | `DECISIONES.md` §5.4 desde research.md con la evidencia del bench; README con `--verificar` y `--forzar`; `PROMPTS_LLM.md` con esta invocación. |
| XI. Compatibilidad con P1 | Sí | Guardado sin cambios. Las copias locales de P1 se invalidan por versión. Las pruebas que inician una partida sin conexión solo agregan llaves a sus datos (SC-307). |

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/003-resolubilidad/
├── spec.md
├── plan.md              # este archivo
├── research.md          # decisiones D1–D11
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── datos-servicio.md   # /llaves, validación, copia local
│   ├── cli.md              # --verificar, --forzar, flujo y códigos
│   ├── reporte.md          # texto exacto del orden y del reporte
│   └── bench.md            # generador y secciones R1–R5
├── checklists/requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Código fuente: módulos afectados

```text
crypta/
├── estructuras/
│   ├── NumeracionLlaves.py      # NUEVO: ids ordenados + desde_ordenados; número = rango (D1);
│                                #        variante por inserción solo para el bench
├── Modelo/
│   ├── UbicacionLlaves.py       # NUEVO: lectura y validación de /llaves → Vector (D7, FR-319)
│   ├── Verificador.py           # NUEVO: oleadas con estacionadas, capas, ciclos, reporte (D3–D6)
│   ├── VerificadorIngenuo.py    # NUEVO: recorrido repetido por ronda y por llave (D8)
│   └── ResultadoVerificacion.py # NUEVO: Resultado, Reporte, PuertaFrontera, Dependencia, NoVerificable
├── Vista/
│   └── FormatoVerificacion.py   # NUEVO: texto puro del resultado (D10, contracts/reporte.md)
├── Adaptadores/
│   ├── FuenteDatos.py           # CAMBIA: obtener_llaves (por omisión LlavesNoDisponibles)
│   ├── FuenteHTTP.py            # CAMBIA: obtener_llaves → GET /criptas/<id>/llaves
│   ├── FuenteOffline.py         # CAMBIA: obtener_llaves desde la copia local
│   └── AlmacenDisco.py          # CAMBIA: guardar_cripta(…, llaves=None)
├── Controlador/
│   ├── GestorCripta.py          # CAMBIA: llaves de la copia local; cargar_llaves; persistir con llaves
│   └── Verificacion.py          # NUEVO: preparar_verificacion (llaves → validar → verificar → resultado
│                                #        o NoVerificable); lo usan el inicio y --verificar
├── bench/
│   ├── bench_resolubilidad.py   # NUEVO: generador y secciones R1–R5
│   └── bench.py                 # CAMBIA: llama a las secciones nuevas; código ≠ 0 si R4 falla
└── main.py                      # CAMBIA: --verificar, --forzar (FR-336); preparar_cripta nueva;
                                 #         crear_partida(args, preparada=None) con la misma firma y
                                 #         retorno, sin verificar; la verificación, solo en main y
                                 #         en --verificar; códigos 1 y 2

tests/
├── test_resolubilidad.py            # NUEVO: HU1 y HU2 con criptas armadas a mano
├── test_equivalencia_resolubilidad.py # NUEVO: ≥ 200 criptas por semilla contra la ingenua; orden seguible
├── test_numeracion_llaves.py        # NUEVO: rango = orden por id; repetidos; ids ausentes
├── test_verificacion_inicio.py      # NUEVO: HU3 y HU4 (main con fuente falsa y almacén temporal)
├── ayudas_cripta.py                 # CAMBIA: la fuente falsa acepta llaves; FuenteQueFalla.obtener_llaves
├── test_controlador.py              # CAMBIA: solo datos: llaves en las criptas que inician sin conexión
└── test_bench.py                    # CAMBIA: huella del generador, R1–R5 en modo rápido, R4 saboteada
```

**Decisión de estructura**: se mantiene el proyecto único; solo se agregan módulos y se separa
`preparar_cripta` de `crear_partida` en `main.py`, que conserva su firma y su retorno.

## Estructuras y complejidad

V salas, E salidas (≤ 4V), L entradas de ubicación, K llaves distintas, R rondas.

| Operación | Cuándo | Estructura | Complejidad |
|---|---|---|---|
| Validar la ubicación de las llaves | una vez | `Mapa.obtener_sala` (árbol balanceado) | O(L log V) |
| Numerar llaves | una vez | `ordenar` + `ArbolBusqueda.desde_ordenados` | O((E + L + 1) log K) para juntar, ordenar y armar; O(log K) por búsqueda |
| Llave de cada puerta y de cada ubicación → número | una vez por puerta y por ubicación | `NumeracionLlaves` | O((E + L) log K) |
| Ordenar ubicaciones por (llave, sala, enemigo) | una vez | `ordenar` | O(L log L) |
| Recorrido por oleadas | una vez | `Cola`, `Vector` de marcas, `estacionadas` por llave | O(V + E + L) + O(K log K) por ordenar rondas |
| Resoluble (FR-305) | una vez | `Sala.entradas` de `sala_salida` | O(grado) |
| Frontera (FR-310) | si no es resoluble | recorrido por índice denso y N S E O | O(V + E) |
| Dependencias por capas (FR-314) | si no es resoluble | `Cola`, `Vector` de etiquetas, semillas ordenadas por capa | O(V + E + L + E log E) |
| Ciclos (FR-315) | si no es resoluble | `Vector` de estado + pila en `Vector` | O(K log K) |
| Texto | una vez | — | O(tamaño del texto) |
| **Total** | | | **O(V + E + L + (E + L) log K + E log E)**: aproximadamente lineal |
| Alternativa ingenua | solo bench y pruebas | — | O(R (V + E)) para el orden + O(K · K_f · (V + E)) para dependencias (K_f llaves de la frontera) |

Memoria: unos 10 `Vector` de tamaño V o K y a lo sumo E puertas estacionadas o semillas.

## Alternativas descartadas (resumen; detalle en research.md)

- Numeración con tabla hash o `ArbolBusqueda` con `insertar` (D1); búsqueda binaria sobre el vector
  (equivalente, se prefiere la estructura ya probada).
- Repetir el recorrido por llave obtenida; liberar puertas antes de cerrar la ronda; volver a
  recorrer la región al obtener una llave; marcas en `ArbolBusqueda` por id (D3).
- Un recorrido por llave para las dependencias; Dijkstra con `MonticuloMin`; agrupar semillas con K
  listas por capa; inundación sin orden por origen (D4).
- Buscar ciclos sin marcas compartidas (D5).

## Mediciones planificadas (FR-330 a FR-335)

Detalle en [contracts/bench.md](contracts/bench.md).

| FR | Sección | Configuración | Criterio |
|---|---|---|---|
| FR-330, HU5-1 | generador | semilla fija, dos ejecuciones | huella idéntica |
| FR-331, HU5-2 | R1 | 500/125, 1 000/250, 2 000/500 salas/llaves; resolubles y no; la ingenua de 2 000 salas con una sola repetición | se reporta, con el cociente ingenua / incremental |
| FR-334, SC-303, HU5-4 | R2 | 2 000 salas, 500 llaves encadenadas (y la cripta publicada más grande, que T050 deja en la copia local con `--verificar`); desde el esqueleto cargado y la ubicación en memoria; la carga del esqueleto aparte, sin límite | < 200 ms (principio VI) |
| FR-335, SC-304, HU5-5 | R3 | incremental con 500 a 8 000 salas; ingenua con 500, 1 000 y 2 000; llaves proporcionales | cocientes de la incremental ≤ 3; los de la ingenua, en la misma tabla y los mismos tamaños |
| FR-332, HU5-3 | R4 | las criptas de los tamaños de R1 y 50 pequeñas (las de 4 000 y 8 000 salas no: la ingenua tardaría minutos) | 0 diferencias; si no, ERROR y código ≠ 0 |
| FR-333, HU5-6 | todas | — | sin vista ni red (prueba con fuente que falla y vista que falla) |
| D1 | R5 | K = 500, 2 000, 8 000; `insertar` con ids barajados y ordenados frente a ordenar + `desde_ordenados` | se reporta, con la altura de cada árbol |

## Impacto en el guardado y la copia local

- **Archivo de partida**: sin cambios de formato. El resultado de la verificación no se guarda
  (FR-327); cargar una partida no verifica (FR-326).
- **Copia local de la cripta**: campo nuevo `llaves` con la respuesta del servicio, bajo la misma
  `version` (FR-323). Una copia de P1 se invalida por la validación de versión existente.

## Pruebas por FR

Cada prueba cita su FR en el nombre del método o en el docstring (principio IX). «HUx-n» es el
escenario n de la historia x.

| FR | Prueba (archivo · caso) | Escenarios |
|---|---|---|
| FR-301 | `test_resolubilidad` · verificar con solo esqueleto + ubicación (fuente que falla si se pide contenido) | HU1-1, HU1-3 |
| FR-302, FR-318 | `test_resolubilidad` · sin `sala_salida`; sin `llave_salida` → no resoluble y el reporte dice cuál | HU2-9 |
| FR-303 | `test_resolubilidad` · cerrada sin llave se cruza; trampas, cierre automático y costos no cambian el resultado; salida sin vuelta solo en su sentido | HU1-4, HU1-5, HU1-6 |
| FR-304 | `test_resolubilidad` · llave de enemigo errante en su sala inicial; dos ubicaciones, una alcanzable | HU1-3, HU1-7 |
| FR-305 | `test_resolubilidad` · ejemplo de HU1-1; solo salida abierta a `sala_salida` → no; `sala_inicial = sala_salida` | HU1-1, HU1-9 |
| FR-306 | `test_resolubilidad` · llave que ninguna puerta pide entra en el orden; solo ids por ronda | HU1-1, HU1-8 |
| FR-307 | `test_equivalencia_resolubilidad` · cada orden se sigue paso a paso: cada llave se alcanza con las anteriores | SC-302 |
| FR-308 | `test_resolubilidad` · rondas `a, c` y `b, salida`; ids comparados como texto (mayúsculas y dígitos) | HU1-1, HU1-2 |
| FR-309 | `test_resolubilidad` · no obtenibles por id, incluidas las que solo pide una puerta | HU2-1, HU2-3 |
| FR-310 | `test_resolubilidad` · frontera por (sala, N S E O); puerta bloqueada entre dos salas de la región no aparece | HU2-1, HU2-10 |
| FR-311 | `test_resolubilidad` · ubicaciones ordenadas por sala y enemigo; «no está en la cripta» | HU2-1, HU2-3 |
| FR-312, FR-314 | `test_resolubilidad` · ciclo `a`↔`b`; `x` sin ubicación; sala inalcanzable por salidas sin vuelta; una puerta frente a dos; empate `d`/`e`; dependencia heredada de la primera puerta | HU2-2 a HU2-6 |
| FR-313 | `test_resolubilidad` · el verificador visita cada sala a lo sumo una vez (contador de visitas en una cripta de prueba) | — |
| FR-315 | `test_resolubilidad` · `salida -> salida`; `a -> b -> a` desde el menor; `c` que llega al ciclo no se reporta en él; varios ciclos ordenados | HU2-1, HU2-2, HU2-7 |
| FR-316 | `test_resolubilidad` · texto completo de HU2-1 contra contracts/reporte.md | HU2-1 |
| FR-317 | `test_resolubilidad` · `salida` obtenible sin puerta hacia `sala_salida` | HU2-8 |
| FR-319 | `test_resolubilidad` · sala inexistente, sin id, sin sala, sala `true`/`2.5`/texto, `enemigo` no texto → `DatosInvalidos`; `test_verificacion_inicio` · no inicia aun con `--forzar`, código 1 | HU3-7 |
| FR-320 | `test_resolubilidad` · misma cripta con la ubicación barajada y las páginas/salidas en otro orden → mismo texto | HU1-2, HU2-11 |
| FR-321 | `test_verificacion_inicio` · fuente que falla en `obtener_contenido` durante la verificación | HU3-8 |
| FR-322 | `test_verificacion_inicio` · la solicitud de llaves cuenta; presupuesto agotado → no verificable | HU3-4 |
| FR-323 | `test_verificacion_inicio` · se guarda con la versión; misma versión no vuelve a pedir; otra versión sí | HU3-4, HU3-5 |
| FR-324 | `test_verificacion_inicio` · sin conexión con y sin llaves en la copia; falla de red | HU3-6 |
| FR-325 | `test_verificacion_inicio` · no resoluble sin `--forzar`: reporte, sin `partida.log`, código 2; con `--forzar` inicia; resoluble muestra el orden; el mapa conocido no cambia | HU3-1, HU3-2, HU3-3, HU3-11 |
| FR-326 | `test_verificacion_inicio` · `--replay` de una partida forzada no verifica ni pide llaves; cargar partida no verifica | HU3-9, HU3-10 |
| FR-327 | `test_verificacion_inicio` · el archivo de partida y `partida.log` no contienen la verificación; el pergamino no la toca | HU3-10 |
| FR-328, FR-329 | `test_verificacion_inicio` · `--verificar` con resoluble (0), no resoluble (2), red/datos inválidos/sin llaves (1); sin vista ni `partida.log`; solicitudes contadas y copia guardada | HU4-1 a HU4-5 |
| FR-336 | `test_verificacion_inicio` · `--verificar` con `--replay` o `--bench` → código 1 sin pedir llaves; `--forzar` no cambia `--verificar` | HU4-6 |
| FR-330 a FR-333 | `test_bench` · huella repetible; R1–R5 corren en modo rápido; R4 con una variante saboteada da ERROR; fuente y vista que fallan | HU5-1 a HU5-3, HU5-6 |
| FR-334, FR-335 | `--bench` (R2, R3); `test_bench` solo comprueba que se calculan y reportan | HU5-4, HU5-5 |
| SC-302 | `test_equivalencia_resolubilidad` · ≥ 200 criptas por semilla (resolubles y no): texto igual al de la ingenua | — |
| SC-307 | `python -m unittest` completo; las pruebas que inician sin conexión solo agregan llaves a sus datos | — |
| Estructuras | `test_numeracion_llaves` · rango = orden por id, repetidos, id ausente → None, altura balanceada; variante por inserción da los mismos ids | — |

## Revisión de la constitución (después del diseño)

Sin cambios respecto a la revisión anterior: la estructura nueva (`NumeracionLlaves`) es propia y
no usa construcciones prohibidas; no hay dependencias nuevas ni constantes de cripta; la
verificación no es estado del juego y no pide contenido.

## Seguimiento de complejidad

No aplica: no hay violaciones de la constitución.
