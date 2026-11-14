# Contrato: secciones de la línea de tiempo en `--bench` (FR-427 a FR-434)

Módulo `crypta/bench/bench_linea.py`, llamado desde `crypta/bench/bench.py`. Sin vista ni red
(FR-431): fuente que falla si se le pide algo y vista muda. Cada sección imprime una tabla con
`medicion.tabla` y «¿cumple?» cuando hay límite. La memoria se mide con `tracemalloc` (biblioteca
estándar).

## Partidas sintéticas (FR-427)

`partida_linea(cripta, semilla, acciones)` → (partida viva, línea, comandos). Todo el azar sale de
un `random.Random(semilla)` propio.

- **(a) Cripta del tamaño de la de referencia**:
  - si la copia local de cripta-06 tiene contenidos, se usa cripta-06;
  - si no (hoy no los tiene: `cache/cripta-06.json` solo trae el esqueleto), una sintética de 300
    salas en cuadrícula con costos variables, puertas abiertas, cerradas y con llave, objetos
    (armas, armaduras, pociones), pergaminos de retroceso en algunas salas y unos 20 enemigos
    repartidos y activos.
- **(b) Escala**: 2 000 salas con 50 cazadores activos (`partida_con_cazadores` de la 001), con los
  mismos objetos y pergaminos y **1 000 acciones** netas. Con 5 000 acciones serían unos 227 puntos
  de 9,5 MB, ≈ 2,2 GB; con 1 000 son ≈ 45 puntos, ≈ 430 MB.
- **Jugador**: vida de sobra (`vida_max = 10**9`), para que la partida no termine.
- **Acciones**: mezcla determinista de `mover` (la mayoría), `atacar` si hay enemigos, `recoger` y
  `usar` si hay objetos, `equipar`, `avanzar`/`retroceder`, `recoger_pergamino` y, de vez en cuando,
  `pergamino`. Al menos 5 000 acciones netas en (a) y 1 000 en (b); las que el juego rechaza no
  cuentan.
- **Huella** (HU5-5): los comandos, el reloj final y el estado serializado al final. Dos ejecuciones
  con la misma semilla dan la misma huella.
- **Consultas**: al menos 200, repartidas por toda la partida con la semilla. La mitad son `#k` y la
  mitad `t`; de estas, algunas caen en un instante entre dos decisiones.

## Secciones

| # | Sección | Configuración | Reporta | Límite |
|---|---|---|---|---|
| L1 | Consulta por K (FR-428, FR-432, SC-404, SC-406) | (a): K = 10, 16, 22, 32 y 64 y la alternativa sin puntos de control (solo el punto 0, con 20 consultas); la línea de cada K se libera antes de armar la siguiente, así solo hay una en memoria a la vez. (b): solo el K por defecto, con 1 000 acciones | por K: media, p95 y máximo de la consulta; memoria de la línea; tiempo total de crear los puntos | (a) con el K por defecto: p95 < 50 ms. (b): sin límite; si pasa de 50 ms, se anota para Límites |
| L2 | Hacia adelante frente a hacia atrás (FR-429) | (a), K por defecto | media y p95 de la consulta de cada una; costo de crear un punto en cada una (la de atrás re-ejecuta el tramo, research D2); memoria de los cambios guardados | — |
| L3 | Igualdad de resúmenes (FR-430) | (a) con todos los K de L1, hacia atrás y sin puntos de control; oráculo: resúmenes tomados de la partida viva en cada decisión y en instantes intermedios mientras se jugaba | consultas comparadas y diferencias | 0 diferencias; si no, ERROR y `--bench` con código distinto de 0 |
| L4 | Ciclo con la línea activa (FR-433, SC-405) | escenario B7 de la 001 (2 000 salas, 50 cazadores) con la línea y el K por defecto; al menos 500 acciones medidas, para que la fracción de copias sea 1/K | media, p95 y máximo del ciclo, con línea y sin línea; ciclos que copiaron | p95 < 20 ms |
| L5 | Memoria (FR-424, FR-434, SC-409) | (a); 2 500 y 5 000 acciones, mismo K; K por defecto frente a la copia por acción (estimada: acciones × tamaño medido de una copia; no se materializa) | MB de cada una, cociente 5 000/2 500, cociente línea/copia por acción | ≤ 2,5 y < 1/3 |
| L6 | Puntos examinados (FR-425) | (a); 2 500 y 5 000 acciones, mismo K | puntos de control examinados por consulta (contador) | no crece con la cantidad de puntos |
| L7 | Cómo se copia un punto (research D3) | (a) y (b) | tiempo y memoria de: `deepcopy` sin ganchos, `deepcopy` que comparte lo inmutable (la elegida) y recorrido de `EstadoPartida` (escribir y armar) | — |
| L8 | Guardar y cargar (FR-417, research D11) | (a), 5 000 acciones, K por defecto | tamaño del archivo y tiempo de guardar y de cargar, en formato binario | — |

Cada medición se repite y se reporta la media. Las consultas reportan también p95 y máximo, con el
mismo percentil que usa `Medicion.percentil` en la 001. Cada fila de L1 indica la cripta usada:
«cripta-06» o «sintética 300 salas».
