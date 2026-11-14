# Contrato: secciones de resolubilidad en `--bench` (FR-330 a FR-335)

Módulo `crypta/bench/bench_resolubilidad.py`, llamado desde `crypta/bench/bench.py`. Sin vista ni
red (FR-333). Cada sección imprime una tabla con `medicion.tabla` y «¿cumple?» cuando hay límite.

## Generador de criptas sintéticas (FR-330)

`generar_cripta_llaves(semilla, salas, llaves, resoluble=True)` → (datos generales, esqueleto JSON,
respuesta de llaves). Todo el azar sale de un `random.Random(semilla)` propio.

- La cripta es una cadena de `llaves + 1` **zonas** de tamaño parecido (salas / (llaves + 1) cada
  una). Cada zona es una cuadrícula pequeña con salidas abiertas y algunas cerradas sin llave, y
  algunas salidas sin vuelta.
- La zona i+1 se une a la zona i por una puerta cerrada que pide `itm_llave_<i>` (ids con ceros a la
  izquierda, en secuencia); esa llave está en una sala al azar de la zona i (a veces con un
  `enemigo`). La última puerta pide `llave_salida` y lleva a `sala_salida`. Así cada llave abre una
  región entera y hay una ronda por llave: el peor caso de la alternativa ingenua.
- Además, puertas «distractoras» entre zonas que piden llaves de zonas anteriores, y llaves que
  ninguna puerta pide, para que haya rondas con varias llaves y empates de orden.
- `resoluble=False` rompe la cadena en una zona elegida con la semilla: la llave de la puerta queda
  detrás de sí misma o en un ciclo de dos o tres llaves, y algunas llaves sin ubicación.
- La respuesta de llaves se entrega en dos órdenes: ordenada por id (caso adverso para la
  numeración (b)) y barajada con la semilla.

Huella para la repetibilidad (HU5-1): salas, salidas (dirección, destino, cerrada, llave, sin
vuelta) y ubicaciones serializadas en orden; dos generaciones con la misma semilla dan la misma
huella.

## Secciones

| # | Sección | Configuración | Reporta | Límite |
|---|---|---|---|---|
| R1 | Incremental frente a ingenua (FR-331) | resolubles y no resolubles; (salas, llaves) = (500, 125), (1 000, 250), (2 000, 500) | tiempo medio de cada alternativa y cociente ingenua / incremental; la ingenua de 2 000 salas se mide con **una sola repetición** | — |
| R2 | Límite de la verificación (FR-334, SC-303) | 2 000 salas, 500 llaves encadenadas, resoluble y no resoluble; con la cripta publicada más grande si está en la copia local | media, p95 y máximo de la verificación completa, desde el esqueleto ya cargado (`Mapa`) y la ubicación de las llaves en memoria hasta el texto (FR-334); aparte, el tiempo de cargar el `Mapa`, sin límite | < 200 ms |
| R3 | Crecimiento (FR-335, SC-304) | incremental con 500, 1 000, 2 000, 4 000 y 8 000 salas (llaves proporcionales: 125 a 2 000); ingenua con 500, 1 000 y 2 000 salas (con más tardaría minutos) | tiempo de cada alternativa y su cociente al duplicar, en la misma tabla; en 500 → 1 000 → 2 000 los cocientes de las dos se comparan fila a fila | incremental ≤ 3 en cada cociente; la ingenua se reporta (se espera ≈ 4) |
| R4 | Igualdad de resultados (FR-332) | las criptas de los tamaños de R1 (500, 1 000 y 2 000 salas) y 50 criptas pequeñas variadas por semilla; las de 4 000 y 8 000 salas de R3 no se comparan (la ingenua tardaría minutos) | criptas comparadas y diferencias (texto completo, contracts/reporte.md) | 0 diferencias; cualquier diferencia se imprime como ERROR y el `--bench` sale con código distinto de 0 |
| R5 | Numeración de llaves (research D1) | K = 500, 2 000 y 8 000 ids; E + L búsquedas | tiempo de construir + buscar y altura del árbol con: `ArbolBusqueda` con `insertar` e ids barajados; ídem con ids ordenados; ordenar + `desde_ordenados`. La tabla hash no se mide (research D1) | — |

Cada medición se repite (con `medicion.medir`) y se reporta la media; R2 reporta también p95 y
máximo. Excepción: la ingenua de 2 000 salas de R1 (y su uso en R3) se mide una sola vez.
