# Plan de implementación: Terreno y cazador

**Rama**: `001-terreno-cazador` | **Fecha**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Entrada**: especificación `specs/001-terreno-cazador/spec.md` (con las aclaraciones de la sesión
2026-11-07) y la propuesta del grupo registrada en `PROMPTS_LLM.md`.

**Artefactos**: [research.md](research.md) (decisiones D1–D12 y alternativas) ·
[data-model.md](data-model.md) · [contracts/](contracts/) · [quickstart.md](quickstart.md)

Este plan es el borrador de las secciones P2 §5.1 y §5.2 de `DECISIONES.md` (P2 §7.1). Las decisiones
son **provisionales** hasta tener la evidencia de `--bench`; si una medición las cambia,
`DECISIONES.md` lo dirá.

## Resumen

Las salidas pasan a tener costo (100 si no se declara) y todo movimiento, de cualquier actor, tarda
`max(1, costo * 100 // velocidad)`. Aparece el cazador, que ataca si comparte sala, espera si no
tiene ruta o la ruta más barata supera su rango, y si no da un paso hacia la vecina de menor id entre
las que inician una ruta de costo mínimo.

Enfoque técnico (evalúa la propuesta del grupo; detalle en research.md):

1. **Ruta más barata** (D1): Dijkstra con nuestro `MonticuloMin`, con inserción perezosa,
   **reanudable** y que se detiene al pasar lo que el cazador necesita: cuesta según la región
   dentro del rango (FR-036). Se acepta la propuesta 1 y se le agrega que sea reanudable.
2. **Cálculo compartido** (D2, D3): una búsqueda desde la sala del jugador para todos los cazadores.
   Se acepta la propuesta 2 con un ajuste: se recorren las salidas **invertidas** (las que llegan a
   cada sala), porque P2 no garantiza que toda salida tenga vuelta y dist(v, jugador) solo es igual a
   dist(jugador, v) si la tiene. Tampoco se limita de entrada al mayor rango: se extiende a demanda
   hasta min(rango, dist del cazador). La alternativa por cazador, con etiqueta (distancia, primer
   paso), se implementa para medirla (FR-031).
3. **Reutilización** (D4): se acepta la propuesta 3. La búsqueda vale mientras no cambie la sala del
   jugador ni una puerta con un extremo asentado. Un cambio de puerta con **ambos** extremos fuera
   de la región asentada se puede ignorar: la demostración está en research D4. Se miden tres
   variantes: recalcular siempre, invalidación total e invalidación selectiva.
4. **Dónde guardar las distancias** (D5): ninguna de las dos opciones propuestas. Se usan `Vector`
   por **índice denso** de sala con **marca** de cálculo, propios de cada búsqueda. El campo en
   `Sala` admite un solo cálculo a la vez, y el verificador, la alternativa por cazador y la
   compartida necesitan varios simultáneos. `ArbolBusqueda` es O(log n) y no se autobalancea.
5. **No es estado del juego** (D6): se acepta la propuesta 5. Las búsquedas no van al historial ni al
   archivo; el pergamino y la carga solo invalidan.

## Contexto técnico

**Lenguaje/versión**: Python 3.11 o superior.

**Dependencias**: biblioteca estándar, `requests` y `struct`. No se agrega ninguna (principio I).

**Almacenamiento**: copia local del esqueleto y del catálogo validada por versión (sin cambios de
mecanismo); archivo binario de partida, que pasa a la versión de formato 2.

**Pruebas**: `unittest` (`python -m unittest`), en `tests/`.

**Plataforma**: equipo local del grupo (Windows 11; también debe correr en el equipo de revisión).

**Tipo de proyecto**: juego de consola en un solo proyecto con MVC (`crypta/Modelo`,
`crypta/Vista`, `crypta/Controlador`, `crypta/Adaptadores`, `crypta/estructuras`, `crypta/bench`).

**Metas de rendimiento**: p95 del ciclo < 20 ms con 50 cazadores en 2 000 salas sobre ≥ 60
acciones (FR-035). Tiempo por decisión con rango pequeño: cociente 20 000 / 2 000 salas < 2
(FR-036). Tiempo por cazador con 100 cazadores ≤ 2 × el de 10 (FR-037).

**Restricciones**: prohibidos `heapq`, `bisect`, `collections`, `networkx`, `dict`/`set` como
estructura, y `sorted`/`list.sort` en ordenamientos evaluados (principio I, P2 §6.2). Nada de
costos ni rangos escritos en el código; la única constante es el 100 por omisión (principio IV).
Determinismo total (principio II).

**Escala**: criptas sintéticas de 2 000 y 20 000 salas; hasta 100 cazadores activos.

No quedan puntos «NEEDS CLARIFICATION».

## Revisión de la constitución (antes de la fase 0)

| Principio | Cumple | Cómo |
|---|---|---|
| I. Estructuras propias | Sí | `MonticuloMin`, `Vector` y estructuras nuevas en `crypta/estructuras`. Sin `heapq`, `dict`, `set`, `collections`, `bisect` ni bibliotecas de grafos. Los `dict` de `json` solo se leen. Se usan tuplas `(dist, nodo)` como elementos del montículo, que no son una estructura prohibida. |
| II. Determinismo | Sí | La decisión no usa el azar; empates por menor id (FR-017); el orden de empates del montículo no afecta las distancias (D1). La reutilización está demostrada equivalente (D4) y se verifica (FR-033). |
| III. MVC | Sí | Reglas y búsquedas en Modelo/estructuras; validación de datos en Modelo; el Controlador solo atrapa `DatosInvalidos`; `--bench` sin vista ni red. |
| IV. Nada quemado | Sí | Costos del esqueleto, rangos del catálogo. Los valores del `--bench` (2 000 salas, 50 cazadores…) son parámetros de medición, no datos de una cripta. |
| V. Red y presupuesto | Sí | Sin solicitudes nuevas (D11, FR-027); el cazador no consulta la red. |
| VI. Rendimiento medido | Sí | Secciones B1–B9 del `--bench`, con las alternativas descartadas medidas (contracts/bench.md). |
| VII. Reversibilidad | Sí | Los movimientos del cazador usan los `Cambio` existentes; las búsquedas no son estado (D6). |
| VIII. Primero la especificación | Sí | spec.md con las aclaraciones confirmado en Git (commit `09b61d0`); el ajuste de `costo` null se confirma en un commit propio antes que este plan. Este plan no agrega reglas. |
| IX. Trazabilidad | Sí | Lista de pruebas por FR abajo; cada escenario tiene prueba. |
| X. Documentación | Pendiente en tareas | `DECISIONES.md` (secciones §5.1 y §5.2 a partir de research.md), README y `PROMPTS_LLM.md`. |
| XI. Compatibilidad con P1 | Sí | Formato de guardado 2: un archivo de formato 1 se rechaza con mensaje, nunca en silencio. El ciclo con cazadores deja evidencia para §5.6 (D12). |
## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/001-terreno-cazador/
├── spec.md
├── plan.md              # este archivo
├── research.md          # decisiones D1–D12
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── datos-servicio.md
│   ├── vista.md
│   ├── guardado.md
│   └── bench.md
├── checklists/requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Código fuente: módulos afectados

```text
crypta/
├── estructuras/
│   ├── DistanciasLimitadas.py   # NUEVO: Dijkstra perezoso y reanudable con Vector + marca (D1, D5)
│   └── RutaPorCazador.py        # NUEVO: Dijkstra (dist, primer paso) por cazador, alternativa medida (D2)
├── Modelo/
│   ├── DatosInvalidos.py        # NUEVO: excepción propia, no hereda de ValueError (D7, D8)
│   ├── Perseguidor.py           # NUEVO: decisión del cazador, invalidación, observador de puertas (D3, D4)
│   ├── Puerta.py                # CAMBIA: costo en EstadoPuerta, unión de costos, extremos, aviso al cambiar
│   ├── Sala.py                  # CAMBIA: lee y valida costo; índice denso; entradas
│   ├── Mapa.py                  # CAMBIA: asigna índices, arma entradas y extremos, valida al compartir
│   ├── Enemigo.py               # CAMBIA: rango desde la ficha, validado al activar
│   └── Partida.py               # CAMBIA: mover con puerta.costo; _turno_enemigo con costo de la acción;
│                                #         errante/rastreador devuelven la puerta; rama del cazador;
│                                #         invalidar al usar pergamino
├── Controlador/
│   ├── RepositorioFichas.py     # CAMBIA: valida la ficha del cazador al entrar (red o disco)
│   └── Controlador.py           # CAMBIA: atrapa DatosInvalidos y termina la sesión de forma controlada
├── Adaptadores/
│   ├── EstadoPartida.py         # CAMBIA: escribe y lee el costo de cada puerta
│   ├── GuardadoBinario.py       # CAMBIA: FORMATO_GUARDADO = 2
│   └── GuardadoJSON.py          # CAMBIA: FORMATO_JSON sube una versión
├── Vista/
│   └── VistaConsola.py          # CAMBIA: costo de cada salida y etiqueta [cazador]
├── bench/
│   ├── bench_cazador.py         # NUEVO: generador con costos y secciones B1–B6, B8, B9
│   ├── bench_ciclo.py           # CAMBIA: escenario B7 con 50 cazadores
│   └── bench.py                 # CAMBIA: llama a las secciones nuevas
└── main.py                      # CAMBIA: muestra DatosInvalidos y no inicia la partida

tests/
├── test_terreno.py                  # NUEVO
├── test_cazador.py                  # NUEVO
├── test_equivalencia_cazador.py     # NUEVO
├── test_distancias_limitadas.py     # NUEVO
├── test_persistencia.py             # CAMBIA: costos y cazadores en el guardado; formato 2
├── test_controlador.py              # CAMBIA: datos inválidos antes y durante la partida
├── test_bench.py                    # CAMBIA: determinismo y secciones nuevas
└── datos/                           # NUEVO: datos fijos de la primera parte para FR-008
    ├── p1_partida.log               #   partida de P1 grabada antes de los cambios
    ├── p1_cripta-01.json            #   copia fija de la cripta (esqueleto y contenidos) de P1
    └── p1_catalogo.json             #   copia fija del catálogo de P1
```

**Decisión de estructura**: se mantiene la estructura actual de un solo proyecto; solo se agregan
módulos.

## Estructuras y complejidad de las operaciones más frecuentes

| Operación | Frecuencia | Estructura | Complejidad |
|---|---|---|---|
| Intervalo de un movimiento | cada movimiento | `EstadoPuerta.costo` | O(1) |
| Decisión de un cazador con la búsqueda vigente | cada turno de cazador | `DistanciasLimitadas` (vectores + marca) | O(4) |
| Extender la búsqueda compartida | cuando un cazador necesita más radio | `MonticuloMin` perezoso | O((ΔV + ΔE) log E_r) amortizado; total por estado O((V_r + E_r) log E_r) |
| Reiniciar la búsqueda (cambia la sala del jugador o una puerta asentada) | ~1 por acción del jugador que se mueve | id de cálculo + montículo vacío | O(1) |
| Aviso de cambio de puerta | cada apertura o cierre | marcas de los 2 extremos | O(1) |
| Trabajo por ciclo con H cazadores | cada ciclo | — | O(H + (V_r + E_r) log E_r) |
| Alternativa por cazador | cada turno de cazador (solo en bench) | `RutaPorCazador` | O((V_r + E_r) log E_r) por turno → O(H (V_r + E_r) log E_r) por ciclo |
| Armar índices, entradas y extremos | una vez al cargar el mapa | `Vector` | O(V + E) |

Memoria: 3 `Vector` de V enteros por búsqueda y a lo sumo E_r entradas en el montículo. Hay una
búsqueda compartida por partida; el verificador y la alternativa existen solo en pruebas y en bench.

## Alternativas descartadas (resumen; detalle y razones en research.md)

- Recorrido por anchura: ignora los costos (D1).
- Montículo indexado con «bajar clave», cubetas de Dial, Bellman-Ford, A*, Floyd-Warshall,
  búsqueda dinámica incremental (D1).
- Búsqueda desde el jugador por salidas de ida (supone simetría que P2 no garantiza) y búsqueda
  limitada siempre al mayor rango (paga por los cazadores de rango grande aunque no decidan) (D2).
- Campo de distancia en `Sala`, `ArbolBusqueda` por id, limpiar arreglos en cada cálculo, tabla hash
  propia (D5).
- Guardar el rango en el archivo de partida (duplica el catálogo) y guardar las búsquedas (D6, D10).

## Mediciones planificadas (FR-028 a FR-037)

Detalle en [contracts/bench.md](contracts/bench.md). Resumen:

| FR | Sección | Valores fijados en Aclaraciones | Criterio |
|---|---|---|---|
| FR-028, SC-006 | generador | semilla fija; dos ejecuciones | huella de criptas idéntica |
| FR-029 | B1 | 1 frente a 50 cazadores repartidos dentro de su rango, ninguno en la sala del jugador, 2 000 salas | se reporta |
| FR-030 | B2, B3 | rango ≈ 100 salas frente a rango grande; 2 000 y 20 000 salas | se reporta |
| FR-036, SC-005 | B3 | rango ≈ 100 salas; 2 000 → 20 000 salas | tiempo medio por decisión: cociente < 2 |
| FR-031 | B4 | compartido frente a por cazador con 1, 10 y 50 cazadores, puertas estables e inestables | se reporta y se dice cuándo gana cada uno |
| FR-032 | B5 | recalcular siempre, invalidación total, invalidación selectiva; puertas casi estables e inestables | tiempo, búsquedas y salas asentadas |
| FR-033 | B6 | todas las decisiones de B4 y B5 | 0 diferencias; cualquier diferencia es ERROR |
| FR-034 | todas | — | sin vista ni red (prueba con fuente que falla si se la llama) |
| FR-035, SC-004 | B7 | 50 cazadores, 2 000 salas, ≥ 60 acciones del jugador | p95 < 20 ms |
| FR-037, SC-008 | B8 | 10, 25, 50 y 100 cazadores | tiempo por cazador con 100 ≤ 2 × el de 10 |
| D5 | B9 | vectores con marca frente a `ArbolBusqueda` | se reporta |

## Impacto en el guardado

- Cambia el formato: cada puerta guarda su `costo`. `FORMATO_GUARDADO` 1 → 2 y `FORMATO_JSON` sube
  una versión. Un archivo de formato 1 se rechaza con el mensaje que ya existe.
- Los cazadores se guardan como cualquier enemigo; el rango sale de la ficha (misma versión de
  catálogo exigida al cargar).
- Las búsquedas no se guardan; al cargar se crea una búsqueda nueva.
- Detalle en [contracts/guardado.md](contracts/guardado.md).

## Pruebas por FR

Cada prueba cita su FR en el nombre del método o en el docstring (principio IX). «HUx-n» es el
escenario n de la historia x.

| FR | Prueba (archivo · caso) | Escenarios |
|---|---|---|
| FR-001 | `test_terreno` · sin costo → 100; solo un lado declara → vale en ambos | HU1-2, HU1-13 |
| FR-002 | `test_terreno` · 3→7 y 7→3 cuestan 250 | HU1-3 |
| FR-003 | `test_terreno` · costo 250 con velocidad 100 → instante 250; costo 1 con velocidad 150 → 1 | HU1-1, HU1-4 |
| FR-004 | `test_terreno` · jugador, errante, rastreador y cazador usan el costo | HU1-6, HU2-11 |
| FR-005 | `test_terreno` · atacar, esperar, usar, equipar, recoger, soltar y abrir conservan su costo en una sala con salidas caras | HU1-7 |
| FR-006 | `test_terreno` · errante y rastreador: mismo destino y mismas llamadas al azar (se compara el estado del `random.Random`) con y sin costos | HU1-6 |
| FR-007 | `test_terreno` · cambio de velocidad de 100 a 200 en el instante 100 tras salida de costo 300 → instante 200, secuencia nueva | HU1-5 |
| FR-008 | `test_terreno.TestCompatibilidadP1` · repetir `tests/datos/p1_partida.log` en modo sin red sobre la copia fija `tests/datos/p1_cripta-01.json` y `p1_catalogo.json` (copiada a una carpeta temporal para el `AlmacenDisco`; nunca usa `cache/`): mismos instantes, eventos, azar y resultado | HU1-8 |
| FR-009 | `test_controlador` · la vista muestra el costo de salidas abiertas y cerradas | HU1-9 |
| FR-010 | `test_terreno` · costo 0, 2,5, `true`, texto; lados 200 y 300 → `DatosInvalidos` y no inicia | HU1-12 |
| FR-011 | `test_cazador` · rango 600 frente a 800; sin rango, negativo, no entero → rechazo antes; `test_controlador` · ficha inválida por precarga → sesión termina y `partida.log` existe; rango 0 | HU2-13, HU2-14, HU2-15 |
| FR-012 | `test_cazador` · se activa al entrar el jugador, base 100, orden por id de instancia | HU2-10 |
| FR-013 | `test_cazador` · misma sala → ataca con costo 100 sin moverse | HU2-1 |
| FR-014 | `test_cazador` · ruta 1–3–4–2 (300) frente a 1–2 (500); puerta cerrada no se usa | HU2-5, HU2-8 |
| FR-015 | `test_cazador` · sin ruta → espera; d = 700 > 600 → espera; d = 600 → avanza | HU2-2, HU2-3, HU2-4 |
| FR-016 | `test_cazador` · el paso cuesta la salida: velocidad 120, costo 250 → 208 | HU2-5, HU2-11 |
| FR-017 | `test_cazador` · vecinas 5 y 3 → 3; cuadrícula con muchas rutas iguales comparada con `RutaPorCazador` | HU2-6, HU2-7 |
| FR-018 | `test_cazador` · salas sin contenido en la ruta: misma decisión y 0 solicitudes; no abre puertas | HU2-8, HU2-9 |
| FR-019 | `test_equivalencia_cazador` · cierre de puerta en la ruta, apertura que crea ruta, el jugador se mueve, otros actores mueren/se mueven/cambian velocidad; partida sintética de ≥ 1 000 turnos de cazador con puertas que cambian seguido, comparada con el verificador (SC-002) | HU3-1, HU3-2, HU3-3, HU3-5 |
| FR-020 | `test_equivalencia_cazador` · pergamino tras moverse un cazador: sala, vida y evento anteriores; decisiones siguientes iguales al verificador | HU3-6 |
| FR-021 | `test_equivalencia_cazador` · `--replay` repite las decisiones; la decisión no consume el azar | HU3-7 |
| FR-022 | `test_controlador` · `[cazador]` aparece solo en cazadores | HU2-12 |
| FR-023 | `test_equivalencia_cazador` · varios cazadores en el mismo instante, cada uno con el estado vigente | HU3-4 |
| FR-024 | `test_terreno` · dos criptas iguales salvo costos dan instantes distintos; `git grep` de constantes en la revisión | HU1-10 |
| FR-025 | `test_persistencia` · copia de P1 con otra versión se invalida, se descarga el esqueleto nuevo y se guarda con su versión | HU1-11 |
| FR-026 | `test_persistencia` · guardar y cargar conserva costos y cazadores; formato 1 rechazado | HU3-8 |
| FR-027 | `test_cazador` · fuente que cuenta solicitudes: decidir no agrega ninguna | HU2-9 |
| FR-028 | `test_bench` · dos generaciones con la misma semilla → misma huella | HU4-1 |
| FR-029 a FR-032 | `test_bench` · las secciones B1–B5 existen y corren en modo rápido | HU4-2 a HU4-5 |
| FR-033 | `test_bench` · B6 reporta 0 diferencias; una variante saboteada a propósito produce ERROR | HU4-6 |
| FR-034 | `test_bench` · fuente que falla si se la llama y vista que falla si se instancia | HU4-7 |
| FR-035 a FR-037 | `--bench` (B7, B8, B3); `test_bench` solo comprueba que se calculan y reportan | HU4-8 a HU4-10 |
| Estructuras | `test_distancias_limitadas` · distancias contra un cálculo sin límite en grafos pequeños; corte por límite; reanudar = calcular de una vez; marca sin limpiar; salidas sin vuelta | — |

## Revisión de la constitución (después del diseño)

Sin cambios respecto a la revisión anterior: ninguna estructura nueva usa construcciones prohibidas,
no hay dependencias nuevas, no hay constantes de cripta, y lo calculado no entra en el estado
reversible. No hay violaciones que justificar.

## Seguimiento de complejidad

No aplica: no hay violaciones de la constitución.
