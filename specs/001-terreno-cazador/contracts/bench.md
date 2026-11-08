# Contrato: secciones nuevas de `--bench` (FR-028 a FR-037)

Todas las criptas son sintéticas y deterministas por semilla (FR-028); `--bench` no instancia la vista
ni usa la red (FR-034). Cada sección imprime una tabla con `medicion.tabla` y termina con
«¿cumple?» cuando hay un límite.

## Generador de criptas sintéticas con costos

- Cuadrícula de `ancho × alto` salas con salidas a las 4 vecinas (algunas quitadas para que haya
  rodeos).
- Costo y estado de cada salida derivados de (semilla, coordenadas) con su propio
  `random.Random`, para que **la región alrededor del jugador sea idéntica** en criptas de distinto
  tamaño (necesario para FR-030 y FR-036).
- Costos enteros en [1, 500]; una fracción de las salidas con puerta.
- Cazadores ubicados a distancias repartidas del jugador: se ordenan las salas por dist (calculada con
  el verificador) y se toman salas a intervalos regulares dentro del rango; ninguna es la sala del
  jugador.
- El rango «pequeño» es la distancia de la sala número 100 en ese orden (deja unas 100 salas dentro).

## Secciones y valores

| # | Sección | Configuración | Reporta | Límite |
|---|---|---|---|---|
| B1 | Un cazador frente a muchos (FR-029) | 2 000 salas; 1 y 50 cazadores | tiempo medio por decisión y por ciclo | — |
| B2 | Rango pequeño frente a grande (FR-030) | 2 000 salas; rango ≈ 100 salas frente a rango que cubre ~toda la cripta | tiempo medio por decisión, salas asentadas | — |
| B3 | Tamaño de cripta con la misma región (FR-030, FR-036, SC-005) | rango ≈ 100 salas; 2 000 frente a 20 000 salas | tiempo medio por decisión y cociente 20 000 / 2 000 | cociente < 2 |
| B4 | Compartido frente a por cazador (FR-031) | 2 000 salas; 1, 10, 50 cazadores; puertas estables y que cambian seguido | tiempo por ciclo de cada variante y cuál gana | — (se reporta en qué condiciones gana cada una) |
| B5 | Reutilizar frente a recalcular (FR-032) | 2 000 salas, 50 cazadores; escenario «puertas casi estables» (≈1 cambio cada 50 acciones) y «puertas inestables» (≥1 cambio por acción) | tiempo por ciclo, búsquedas iniciadas y salas asentadas de: recalcular siempre, invalidación total, invalidación selectiva | — |
| B6 | Equivalencia (FR-033) | en B4 y B5, cada decisión reutilizada contra un verificador desde cero | cantidad de decisiones comparadas y diferencias | 0 diferencias; cualquier diferencia se imprime como ERROR y el proceso sale con código distinto de 0 |
| B7 | Ciclo con cazadores (FR-035, SC-004) | 2 000 salas, 50 cazadores repartidos dentro de su rango; al menos 60 acciones del jugador (`ACCIONES = 60`), con calentamiento | media, p95 y máximo del ciclo | p95 < 20 ms |
| B8 | Escala en cantidad de cazadores (FR-037, SC-008) | 2 000 salas; 10, 25, 50 y 100 cazadores | tiempo por ciclo y por cazador; cociente (por cazador con 100) / (por cazador con 10) | cociente ≤ 2 |
| B9 | Dónde guardar distancias (research D5) | misma búsqueda; vectores con marca frente a `ArbolBusqueda` | tiempo por búsqueda | — |

Con `--bench` y la cripta oficial publicada, B7 se repite sobre ella (FR-035).

## Repetibilidad (SC-006)

Dos ejecuciones con la misma semilla generan las mismas criptas: la prueba compara una huella
(salas, salidas, costos, puertas y ubicación de cazadores serializados en orden) de cada cripta
generada.
