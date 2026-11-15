# Contrato: secciones de niebla e «ir a» en `--bench` (FR-229 a FR-236)

Módulo `crypta/bench/bench_niebla.py`, llamado desde `crypta/bench/bench.py`. Sin vista ni red
(FR-233): miden directamente sobre `Mapa`, `MapaConocido` y `RutaConocida`, sin `Partida` (como B1
a B6 de la 001), y las pruebas usan una fuente y una vista que fallan si se les pide algo. Cada
sección imprime una tabla con `medicion.tabla` y «¿cumple?» cuando hay límite. Se registran como
`niebla_n1` … `niebla_n4`, así se pueden correr solas:
`python -m crypta.bench.bench niebla_n1 niebla_n2 niebla_n3 niebla_n4 --guardar docs/resultados_bench_002.txt`.

## Criptas y mapas conocidos (FR-229)

- **2 000 salas**: `CriptaSintetica(2000, semilla)` de la 001 (cuadrícula 50 × 40, costos de 1 a
  500, 15 % de salidas con puerta, 30 % de ellas cerradas).
- **Tamaño de la de referencia**: el esqueleto de la **copia local más grande** de la carpeta de
  copias (hoy cripta-06, 300 salas; solo hace falta el esqueleto). El id no se escribe en el código
  (principio IV). Si no hay copias, una sintética de 300 salas (se agrega el tamaño (300, 20, 15) a
  `TAMANOS`). La fila dice cuál se usó: «<id de la copia> (300 salas)» o «sintética 300 salas».
  La **carpeta de copias es un parámetro** de la sección (por omisión, la de la aplicación). Las
  pruebas pasan una carpeta temporal vacía y usan la sintética de 300 salas: nunca leen `cache/`.
- **Anotar**: `MapaConocido` recibe la función de anotar que corresponda (research D3): en N2, la
  de un `RegistroAccion` propio de cada entrada, para poder deshacerla; en N1 y N3, una que no hace
  nada.
- **Mapa conocido completo**: todas las salas exploradas y cada puerta recordada con su estado
  real.
- **Mapa conocido parcial de n salas**: las n primeras salas en un recorrido en anchura desde el
  centro, exploradas con `MapaConocido.explorar`.
- **Conocimiento desactualizado**: sobre el completo, un 5 % de las puertas cerradas (elegidas con
  la semilla) quedan recordadas abiertas. El viaje las descubre al observar.
- **Huella** (HU5-1): salas, salidas, puertas cerradas, estados del mapa conocido, pares de viajes y
  pasos elegidos. Dos ejecuciones con la misma semilla dan la misma huella.

## Secciones

| # | Sección | Configuración | Reporta | Límite |
|---|---|---|---|---|
| N1 | Consultas al mapa conocido (FR-230, FR-235, SC-205) | 2 000 salas con 200 y con 2 000 exploradas; 100 000 consultas de `estado(sala)` y de `recordada(puerta)` sobre salas y salidas conocidas elegidas con la semilla | media por consulta de la elegida (`Vector` + `EstadoPuerta`) y de la alternativa (`ArbolBusqueda` por id y por (sala, dirección), **armados con `desde_ordenados`**: el árbol no se balancea solo e insertar en orden lo degenera); cociente 2 000/200 de cada una | elegida: cociente ≤ 2. La alternativa también puede cumplirlo (crece como log n); se descarta por el costo por consulta y por escribir los dos lados de cada puerta (research D1) |
| N2 | Exploración con antorcha y su reversión (FR-230, FR-236, SC-205) | `CriptaSintetica(20000)` con mapas conocidos parciales de 200 y de 2 000 salas alrededor del centro; 1 000 entradas con antorcha en las **mismas** salas, elegidas con la semilla entre las que están a **más de 2 pasos** de la región de 2 000 (que contiene a la de 200), así ni la sala ni sus vecinas ni los destinos de estas tocan ninguna de las dos regiones y cada entrada revela lo mismo en los dos mapas; cada entrada registra sus cambios en un `RegistroAccion` y se deshace antes de la siguiente | media de explorar y de deshacer, con la elegida y con la alternativa «copia del mapa conocido por acción» (prohibida por VII; solo para mostrar que crece); cambios registrados por entrada en cada mapa; cociente 2 000/200 | elegida: cociente ≤ 2 al explorar y al deshacer. Si los cambios registrados de una entrada no son iguales en los dos mapas, la sección da **ERROR** (la comparación no sería justa) y `--bench` termina con código distinto de 0 |
| N3 | Paso de «ir a» (FR-231, FR-234, SC-204) | (a) 2 000 salas, mapa completo, ≥ 20 viajes y ≥ 200 pasos; (b) lo mismo con conocimiento desactualizado; (c) tamaño de la de referencia (de la carpeta de copias que recibe la sección), mapa completo, ≥ 20 viajes. Pares (origen, destino) con la semilla, distintos y con ruta conocida | por variante (reutilizar con invalidación selectiva —la elegida—, invalidación total y recalcular en cada paso; en (a) y (c) solo selectiva y recalcular): media, p95 y máximo de **todos** los pasos; media, p95 y máximo del **primer paso** de cada viaje, aparte; pasos por viaje (mínimo, media, máximo); fracción de pasos que buscaron; búsquedas, invalidaciones y salas asentadas | (a) y (c), elegida: p95 < 5 ms. Si el primer paso pasa de 5 ms, se anota para Límites (FR-234) |
| N4 | Igualdad con la alternativa (FR-232, SC-203) | todos los pasos de N3 de todas las variantes; todas las consultas de N1; todas las entradas de N2 | pasos comparados con `paso_desde_cero` (`RutaPorCazador` hacia adelante sobre el grafo conocido) y entre variantes; consultas y estados comparados entre la elegida y la alternativa; diferencias | 0 diferencias; si no, ERROR y `--bench` con código distinto de 0 |

Detalles de medición:

- «Cálculo de un paso» es `RutaConocida.siguiente_paso(sala, destino)`, después de observar las
  salidas de la sala actual (lo que hace la `Partida` antes de cada decisión). La observación y el
  movimiento simulado no se cronometran.
- Antes de medir se hace un viaje de calentamiento que no se reporta. Se usa `time.perf_counter_ns`
  y el mismo percentil que `Medicion.percentil` de la 001.
- N4 compara fuera de lo cronometrado.
- La nota de N3 explica que el p95 incluye los pasos que buscan, y que el criterio se cumple si esos
  pasos son menos del 5 % del total (research D6).
