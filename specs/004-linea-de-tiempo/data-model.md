# Modelo de datos: Línea de tiempo

**Capacidad**: 004 — `004-linea-de-tiempo` | **Plan**: [plan.md](plan.md) | **Decisiones**:
[research.md](research.md)

Solo se usan estructuras del curso: `Vector`, `ListaDoble` (dentro del `Historial` de P1) y una
búsqueda binaria propia. No se usan `dict`, `set`, `bisect` ni `collections` (principio I).

## EntradaLinea (`crypta/Modelo/LineaDeTiempo.py`), decisiones D1 y D6

Un paso de la secuencia neta.

| Campo | Tipo | Regla |
|---|---|---|
| `tipo` | `ACCION`, `NO_ACCION` o `AJUSTE` | `ACCION` si el comando sumó una acción del jugador; `NO_ACCION` para `avanzar` y `retroceder`; `AJUSTE` lo agrega un pergamino |
| `comando` | `str` | texto ya traducido, el mismo que va a `partida.log`; vacío en `AJUSTE` |
| `reloj` | `int ≥ 0` | reloj de la partida al decidir el comando |
| `numero_accion` | `int ≥ 1` | k de la acción (en `ACCION`) o de la próxima acción (en los otros dos tipos) |
| `pergaminos_inventario`, `posicion_actual`, `pergaminos_sala` | `int` o `None` | solo en `AJUSTE`: los valores que el pergamino dejó fuera del historial |

## PuntoDeControl, decisiones D3 y D5

| Campo | Tipo | Regla |
|---|---|---|
| `ancla` | `int` | a₀ + j·K: acciones netas completas en ese estado (estado antes de la acción siguiente). a₀ = acciones de la partida al iniciar la línea: 0 en una partida nueva; las del estado cargado si el archivo traía un bloque `linea` vacío |
| `posicion` | `int` | índice de la primera entrada que va después del punto |
| `partida` | `Partida` | copia independiente (D3), con historial sin límite, bitácora propia, sin `Perseguidor`, compartiendo fichas y contenidos originales |

Invariantes:

- Hay a lo sumo un punto por cada a₀ + j·K (FR-422).
- Con a₀ > 0, `ubicar_*` rechaza lo anterior al estado cargado con el mensaje de rango de
  contracts/cli.md: la línea solo conoce la historia desde ahí. No ocurre con archivos guardados
  por el juego, que siempre traen la línea completa.
- El punto j está en la posición j del `Vector` de puntos.
- Todo punto con `ancla` mayor que el total neto de acciones se quita (FR-410).

## LineaDeTiempo

| Campo | Estructura | Uso | Costo |
|---|---|---|---|
| `k` | `int ≥ 1` | acciones entre puntos (FR-420) | — |
| `entradas` | `Vector` de `EntradaLinea` | secuencia neta | agregar y quitar el último: O(1) amortizado |
| `decisiones` | `Vector` de (reloj, posición de la entrada) | fila k − 1 = acción #k, ordenada por reloj | #k en O(1); t con búsqueda binaria en O(log n) |
| `puntos` | `Vector` de `PuntoDeControl` | punto j en la posición j | j = ⌊m/K⌋ en O(1) (FR-425) |

Operaciones:

| Operación | Qué hace | Costo |
|---|---|---|
| `iniciar(partida)` | crea el punto 0 tras `Partida.iniciar` | una copia |
| `registrar(partida, comando, acciones_antes, reloj_antes)` | D6: acción, no acción o pergamino; crea un punto si toca | O(1), más una copia cada K acciones |
| `revertir(partida)` | quita entradas y puntos hasta la última acción y agrega el ajuste | O(lo revertido) (FR-412) |
| `ubicar_instante(t, reloj_actual)` | → `Objetivo` o rechazo si t > reloj actual (FR-403) | O(log n) |
| `ubicar_accion(k)` | → `Objetivo` o rechazo si k ∉ [1, n + 1] (FR-404) | O(1) |
| `cantidad_acciones()` | n | O(1) |

## Objetivo

| Campo | Regla |
|---|---|
| `pedido` | texto del instante pedido: `t` o `#k` |
| `acciones_completas` | m: acciones que se re-ejecutan enteras |
| `tope` | `None` (antes de la acción #(m + 1)), o t para re-ejecutar la acción #(m + 1) solo hasta el instante t (D9) |
| `es_actual` | verdadero si el objetivo es el estado actual: se resume la partida viva |

## Reconstruccion (`crypta/Modelo/Reconstruccion.py`), decisiones D2, D7 y D8

`consultar(linea, objetivo, partida_viva, reejecutar)` → `Resumen`.

1. Si `es_actual` es verdadero, arma el resumen de la partida viva y termina.
2. Toma el punto j = ⌊m/K⌋ y su `Sello`.
3. Re-ejecuta las entradas desde `punto.posicion` con `reejecutar(copia, comando, garantizar)`:
   - `reejecutar` es `ejecutar_comando`; lo inyecta el controlador, así el Modelo no importa el
     Controlador;
   - `garantizar` carga el contenido desde el mapa vivo, sin red (D7);
   - las entradas `AJUSTE` fijan sus valores;
   - si hay tope, la última acción corre con `Partida.tope_tiempo = t` (D9).
4. Arma el resumen.
5. Deshace las acciones re-ejecutadas con `historial.deshacer_ultima` y restaura el `Sello`. Quita
   el tope.

Re-ejecuta y deshace a lo sumo K acciones (FR-423). La partida viva solo se lee (FR-407).

### Sello (D8)

`terminada`, `resultado`, `puerta_de_salida_abierta`, `enemigos_derrotados`, pergaminos del
inventario, nodo del objeto actual, largo de la bitácora, número de secuencia de la agenda
(`siguiente_secuencia`, que el pergamino de P1 no rebobina) y un `Vector` de (sala, pergaminos) con
las salas en que entra el jugador durante la re-ejecución.

**No** se restaura la carga de contenido: una sala que la re-simulación cargó en el punto **queda
cargada** después de deshacer (decisión del grupo, research D7). Las reglas solo miran
`contenido_cargado()` al mover y al iniciar, y P1 garantiza que el orden de los enemigos no depende
de cuándo llega el contenido. La prueba de D8 compara la serialización del punto antes y después
sin el contenido de esas salas, y comprueba que repetir una consulta da el mismo resumen.

## Resumen (`crypta/Modelo/Resumen.py`), decisión D10

Datos de FR-406: `pedido`, `reloj`, `proxima_accion`, `sala` (id y nombre), `vida`, `vida_max`,
`ataque`, `defensa`, `velocidad`, `inventario` (`Vector` de objetos en su orden real, equipados y
pergaminos), `efectos` (veneno, antorcha y velocidad, con hasta cuándo duran), `enemigos` (`Vector`
de (id de instancia, nombre, vida) de los activos y vivos de la sala) y `mapa_conocido` (de la 002;
mientras no exista, `None`). Más un aviso opcional para el caso de FR-415. El texto está en
[contracts/resumen.md](contracts/resumen.md).

## Cambios en clases existentes

| Clase | Cambio | Comportamiento sin línea de tiempo |
|---|---|---|
| `Historial` | `limite=None` = sin límite | igual: el valor por omisión sigue siendo 5 |
| `Partida` | atributo `tope_tiempo` (`None`); `_correr_hasta_el_jugador` usa `siguiente_si_corresponde(tope)` cuando hay tope. Callback opcional `al_ejecutar_evento(partida, evento)` (`None` por omisión): si existe, `_correr_hasta_el_jugador` lo llama después de ejecutar cada evento que no es el turno del jugador. Solo lo usa el oráculo (`crypta/bench/oraculo_linea.py`) y la copia no lo hereda (`None`). `__deepcopy__` comparte `_fichas` y deja nuevos el `Perseguidor` (`None`), la bitácora y el historial | igual (FR-426) |
| `Sala` | `__deepcopy__` comparte `contenido` | igual |
| `EstadoPuerta` (`crypta/Modelo/Puerta.py`) | `__deepcopy__` deja `observador = None` | igual |
| `Mapa` | `__deepcopy__` en dos pasadas: registra una copia vacía de cada sala en el `memo` y después las llena (`Sala.copia_vacia`, `Sala.llenar_copia`), para no pasar el límite de recursión (T010) | igual |

## Persistencia (formato 3), decisión D11

Detalle en [contracts/guardado.md](contracts/guardado.md). Los bloques existentes se mantienen y se
agrega un bloque `linea` con K, las entradas y, por cada punto, su ancla, su posición, su bloque
general y sus salas, escritos con el recorrido de `EstadoPartida`.

- `guardar_partida(partida, ruta, encabezado, linea=None)`: sin línea se escribe un bloque `linea`
  **vacío** (solo K, sin entradas ni puntos).
- `cargar_partida(fichas)` sigue devolviendo **solo la partida**. La línea leída queda en el
  atributo `linea` del objeto que lee el archivo (`ArchivoGuardado`, `ArchivoGuardadoJSON`), no en
  la `Partida` (D12). Si el bloque venía vacío, `linea` es `None`.
- El `Controlador` toma la línea del lector. Si es `None`, crea una `LineaDeTiempo(k)` nueva con el
  punto a₀ en el estado cargado.

## Oráculo (`crypta/bench/oraculo_linea.py`)

Lo usa la sección L3 del bench y lo reutilizan las pruebas; el bench no importa nada de `tests/`.

- `jugar_con_oraculo(partida, linea, comandos, garantizar)`: juega con `ejecutar_y_registrar`.
  Antes de cada comando guarda el texto del resumen `#k`; con `al_ejecutar_evento` guarda el resumen
  en el instante de cada evento. Devuelve un `Vector` de (pedido, texto).
- `serializar_estado(partida, omitir_salas=None)`: bytes de `escribir_general` y `escribir_sala`
  con `EscritorBinario`; omite el contenido de las salas cuyos ids estén en `omitir_salas` (D8).
