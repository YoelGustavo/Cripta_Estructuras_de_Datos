# Modelo de datos: Niebla de guerra e «ir a»

**Capacidad**: 002 | **Fuente**: [spec.md](spec.md), [research.md](research.md)

V = salas del mapa; E = salidas. Todas las estructuras son propias (`Vector`, `ArbolBusqueda`,
`MonticuloMin` de `crypta/estructuras`); no hay `dict`, `set`, `heapq`, `bisect` ni `collections`.

## Constantes (reglas de la spec, no datos de cripta)

| Nombre | Valor | Dónde |
|---|---|---|
| `DESCONOCIDA`, `AVISTADA`, `EXPLORADA` | 0, 1, 2 | `crypta/Modelo/MapaConocido.py` |
| `ABIERTA`, `CERRADA` | 1, 2 (`None` = nunca observada) | `crypta/Modelo/Puerta.py` |
| Motivos de parada | `LLEGADA`, `ENEMIGOS`, `DANIO`, `SIN_RUTA`, `PASO_IMPOSIBLE`, `FIN_PARTIDA` | `crypta/Modelo/Viaje.py` |

## EstadoPuerta (cambia)

Lo que comparten los dos lados de una salida (`crypta/Modelo/Puerta.py`).

| Campo | Tipo | Estado del juego | Nota |
|---|---|---|---|
| `recordada` | `None` / `ABIERTA` / `CERRADA` | **Sí** | NUEVO. Última observación del jugador (FR-204 a FR-206). Lo escribe solo `MapaConocido` |
| `cerrada`, `llave`, `cierre_automatico`, `costo_declarado` | — | Sí | Sin cambios |
| `extremos`, `observador` | — | No | Sin cambios. `observador` sigue siendo el `Perseguidor` |

- `Puerta(…, recordada=None)` acepta el valor leído de un guardado.
- `compartir_estado_con`: si los dos lados traen `recordada` distintos y ninguno es `None`,
  `DatosInvalidos` (al cargar, `ErrorGuardado`); si uno es `None`, se toma el otro.
- `__deepcopy__` copia `recordada` (ya copia todo menos `observador`).

## MapaConocido (nuevo, Modelo)

El conocimiento del jugador (`crypta/Modelo/MapaConocido.py`). Uno por `Partida`
(`partida.conocimiento`). Es estado del juego.

| Campo | Tipo | Estado del juego | Nota |
|---|---|---|---|
| `_mapa` | `Mapa` | — | Para `sala_por_indice` |
| `_estados` | `Vector` de V enteros | **Sí** | `DESCONOCIDA` / `AVISTADA` / `EXPLORADA` por `sala.indice` |
| `exploradas`, `avistadas` | int | Sí (derivados) | Contadores; se ajustan con cada cambio y al deshacer |
| `_anotar` | función(Cambio) | No | **`partida._anotar`**, que busca `estado.historial` en cada llamada. Nunca un `historial.registrar_cambio` guardado: `leer_linea` reemplaza por asignación el historial de cada punto de control (research D3). En la copia de la 004 el método ligado se reubica solo por el `memo`. En el bench, la función que corresponda |
| `observador` | `RutaConocida` o `None` | No | Recibe `sala_explorada` y `puerta_recordada` |

Operaciones:

| Operación | Qué hace | Complejidad |
|---|---|---|
| `estado(sala)` | `_estados[sala.indice]` | O(1) (FR-235) |
| `esta_explorada(sala)` | `estado(sala) == EXPLORADA` | O(1) |
| `recordada(puerta)` | `puerta.estado.recordada` | O(1) (FR-235) |
| `explorar(sala)` | explorada si no lo estaba; `observar(sala)`; `avistar` cada destino desconocido | O(salidas de la sala) |
| `observar(sala)` | `recordada` ← estado real de cada salida de la sala | O(4) |
| `avistar(sala)` | desconocida → avistada | O(1) |
| `restaurar_sala((indice, anterior))` | deshacer de `explorar`/`avistar`; avisa al observador | O(1) |
| `restaurar_puerta((estado, anterior))` | deshacer de `observar`; avisa al observador | O(1) |
| `restaurar(lista)` | al cargar: valida ids y estados de la lista, fija los estados y llama a `validar()` | O(V + E) |
| `validar(id_sala_inicial)` | `ValueError` si la sala inicial no está explorada (FR-201), si una sala es avistada sin ser destino de una salida explorada o un destino de una salida explorada quedó desconocido (FR-202), o si una salida de una sala explorada tiene `recordada is None` (FR-203, FR-204). La usan `restaurar` y la prueba de equivalencia (T041) | O(V + E) |
| `salas_conocidas()` | recorre `_estados` en orden de índice (= orden de id) | O(V) |

Reglas:

- Cada escritura que cambia el valor anota **un** `Cambio.de_operacion` con el valor anterior; si
  el valor no cambia, no anota (research D3). Sin acción abierta (al iniciar), `registrar_cambio`
  no hace nada.
- Explorada nunca vuelve a avistada ni a desconocida salvo al deshacer (FR-201).
- `__deepcopy__` copia `_estados` y los contadores, comparte el `_mapa` ya copiado (por el `memo`) y
  deja `observador = None`.

## Partida (cambia)

| Campo | Tipo | Estado del juego | Nota |
|---|---|---|---|
| `conocimiento` | `MapaConocido` | **Sí** | NUEVO. Se crea en `__init__` con todo desconocido |
| `_ruta_conocida` | `RutaConocida` o `None` | No | NUEVO. Se crea la primera vez (`ruta_conocida()`); está en `_NO_SE_COPIAN` |
| `enemigos_al_entrar` | int | No | NUEVO. Enemigos vivos de la sala al entrar en el último `mover`, antes de activar a los dormidos |

Cambios de comportamiento (research D4, D11):

- `iniciar` → `conocimiento.explorar(sala inicial)`.
- `_poner_jugador_en(sala)` → `explorar(sala)` y, con antorcha, `explorar` cada vecina.
- `_correr_hasta_el_jugador` → al sacar `TURNO_JUGADOR`, `observar(sala actual)` antes de volver.
- `usar_pergamino` → también `_ruta_conocida.invalidar()`.
- `_cerrar_puerta` → avisa solo si la puerta es una salida de la sala del jugador (alguna salida de
  `sala_actual()` comparte su `EstadoPuerta`, O(4)); una salida sin vuelta que llega a la sala del
  jugador no avisa (FR-205, FR-208).
- `_regenerar`, `_rearmar_trampa` → avisan solo si pasa en la sala del jugador.

## RutaConocida (nuevo, Modelo)

La ruta de «ir a» (`crypta/Modelo/RutaConocida.py`). No es estado del juego (research D7).

| Campo | Tipo | Nota |
|---|---|---|
| `_mapa`, `_conocimiento` | — | Lectura |
| `_distancias` | `DistanciasLimitadas(V, entradas_conocidas)` | Distancias al destino |
| `_vigente` | bool | Si la búsqueda sirve |
| `modo` | `SELECTIVA` / `TOTAL` / `RECALCULAR` | Para el bench; por omisión `SELECTIVA` |
| `busquedas`, `invalidaciones`, `pasos` | int | Contadores para el bench y las pruebas |
| `_desde_cero` | `RutaPorCazador` o `None` | Verificador (SC-203, N4) |

| Operación | Qué hace | Complejidad |
|---|---|---|
| `entradas_conocidas(y)` | pares `(origen.indice, costo)` de `sala.entradas` con origen explorado y `recordada == ABIERTA` | O(entradas de y) |
| `siguiente_paso(sala, destino)` | reinicia si hace falta; `extender_hasta(∞, objetivo)`; la `Puerta` elegida o `None` si no hay ruta | O(grado) si reutiliza; O((V + E) log V) si busca |
| `paso_desde_cero(sala, destino)` | `RutaPorCazador` hacia adelante por las salidas conocidas | O((V + E) log V) |
| `puerta_recordada(estado)` | invalida si un extremo está asentado (TOTAL: siempre) | O(1) |
| `sala_explorada(sala)` | invalida si la sala o el otro extremo de una de sus salidas o entradas está asentado | O(grado) |
| `invalidar()` | `_vigente = False` | O(1) |

Desempate (FR-217): entre las salidas abiertas en el mapa conocido de la sala actual hacia una v
explorada con `costo + dist(v) == dist(sala)`, la de menor id de v; con dos salidas a la misma v, la
primera en N, S, E, O.

## Viaje (nuevo, Modelo)

Una orden `ir a` en curso (`crypta/Modelo/Viaje.py`). No es estado del juego; vive lo que dura la
orden.

| Campo | Tipo | Nota |
|---|---|---|
| `destino` | `Sala` | Explorada, distinta de la actual |
| `pasos` | int | Pasos hechos |
| `motivo` | constante o `None` | Por qué se detuvo |

| Operación | Qué hace |
|---|---|
| `Viaje.validar(partida, id_destino)` | `AccionInvalida` si el id no existe o no está explorado (mismo mensaje), si es la sala actual o si no hay ruta conocida (FR-216). Si pasa, devuelve el `Viaje` |
| `siguiente_direccion(partida)` | la dirección del próximo paso, o fija `SIN_RUTA` y devuelve `None` |
| `despues_del_paso(partida, vida_antes)` | fija el motivo de FR-221 en este orden: `FIN_PARTIDA`, `LLEGADA`, `DANIO`, `ENEMIGOS`; o deja `None` |
| `detener(motivo)` | lo usa `ejecutar_ir_a` para `PASO_IMPOSIBLE` |

Transiciones: `en curso` → (paso) → `en curso` | `detenido(motivo)`. Antes de cada paso, sin ruta
→ `detenido(SIN_RUTA)` sin mover. Si `garantizar_sala`, llamada antes del `mover`, lanza
`RuntimeError` → `detenido(PASO_IMPOSIBLE)` sin mover. Un error que salga del `mover` no es una
parada: se propaga (research D8).

## Controlador (cambia)

| Operación | Qué hace |
|---|---|
| `_ejecutar_comando_jugador(comando)` | NUEVO. Lo que hoy hace `procesar_comando` con un comando escrito a mano: `_asegurar_linea`; `ejecutar_comando` con `garantizar_sala`; si se ejecutó, `linea.registrar`, `registro.anotar`, `_actualizar_fichas_en_uso` y `precargar_async` si la partida sigue. No atrapa errores. Lo usan el comando escrito a mano y cada paso de `ir a` |
| `Comandos.ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar_sala=None, anotar_comentario=None)` | NUEVO. El bucle del viaje; recibe la función por paso (research D8) |

Si varias condiciones se cumplen en el mismo paso, el motivo que se muestra sigue ese orden. El
viaje se detiene igual; el orden solo decide el texto.

## Resumen (cambia, 004; T057)

| Campo | Tipo | Nota |
|---|---|---|
| `mapa_conocido` | `MapaResumido` | Antes `None` |

`MapaResumido`: `exploradas` (`Vector` de `SalaResumida(id, nombre, salidas)`, con cada salida
`(direccion, destino, costo, recordada)` en N, S, E, O) y `avistadas` (`Vector` de ids), en orden de
id. Lo arma `armar_mapa_resumido(partida)` en O(V + salidas exploradas); lo usan el resumen de la
004 y el comando `mapa`.

## Archivo de partida (formato 4)

Ver [contracts/guardado.md](contracts/guardado.md). Agrega `recordada` por salida y el grupo
`conocimiento` en el bloque general.

## RegistroPartida (cambia)

- `anotar_comentario(texto)`: escribe `# <texto>`.
- `leer_registro`: ignora las líneas que empiezan con `#` después de `---`. `FORMATO_REGISTRO`
  sigue en 1.
