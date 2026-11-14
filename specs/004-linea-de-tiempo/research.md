# Investigación (fase 0): Línea de tiempo

**Capacidad**: 004 — `004-linea-de-tiempo` | **Fecha**: 2026-11-14 | **Plan**: [plan.md](plan.md)

Decisiones D1–D13 con sus alternativas. Todas son **provisionales** hasta tener la evidencia de
`--bench` (contracts/bench.md); si una medición cambia una decisión, `DECISIONES.md` §5.5 lo dirá.

## Datos de partida

**Medidos por el grupo en otra máquina** (indicaciones de `/speckit-plan`):

| Medida | 300 salas, 20 enemigos | 2 000 salas, 50 enemigos | 2 000 salas, 50 cazadores |
|---|---|---|---|
| Una acción del jugador | 0,47 ms | 1,4 ms | 2,7 ms |
| Una copia completa con `copy.deepcopy` | 36 ms, 1,5 MB | — | 234 ms, 9,5 MB |

**Medidos en nuestra máquina** (2026-11-14, script temporal fuera del repositorio, sin tocar el
código: `partida_de_carga` y `partida_con_cazadores` de `crypta/bench/bench_ciclo.py`, comandos con
`ejecutar_comando`, deshacer con `Historial.deshacer_ultima` sobre una copia con historial sin
límite, memoria con `tracemalloc`):

| Medida | 300 salas, 20 enemigos | 2 000 salas, 50 cazadores |
|---|---|---|
| Acción (media / p95) | 1,21 ms / 1,63 ms | 8,1 ms (media; recorrido al azar) |
| Deshacer una acción (media / p95) | 0,40 ms / 0,56 ms | 1,9 ms |
| Copia completa (`deepcopy`) | 63 ms, 1,03 MB | 454 ms |
| Copia que comparte lo inmutable (D3) | 57 ms, 0,85 MB | 484 ms (sin ganancia) |

Lo que sale de las mediciones:

- Nuestra máquina es entre 1,7 y 3 veces más lenta: se confirma el «cerca del doble». Los
  cálculos de abajo usan **nuestras** medidas, porque `--bench` corre aquí. Los 8,1 ms por acción
  con cazadores son pesimistas: el B7 de la 001 mide 3,04 ms de media en el mismo escenario con un
  recorrido fijo (`docs/resultados_bench_p2.txt`). Para la escala se usa el rango 3 a 8 ms.
- **Deshacer cuesta un tercio de una acción** (0,40 frente a 1,21 ms): no busca rutas ni decide
  enemigos, solo restaura valores. Con esto, a + u = 1,61 ms con 300 salas.
- La memoria de `tracemalloc` (1,03 MB) es menor que la del grupo (1,5 MB) porque mide otra cosa.
  Los cálculos de memoria dan las dos cifras.

Notación: **a** es el costo de una acción, **u** el de deshacerla, **c** el de una copia, **s** su
tamaño, **n** las acciones del jugador y **K** las acciones entre dos puntos de control.

## Lo que encontramos en el código actual

- `Cambio` (`crypta/Modelo/Cambio.py`) guarda **referencias a los objetos** sobre los que se
  registró (la sala, el enemigo, la agenda, el `Evento`, el `random.Random`, nodos de la
  `ListaDoble` del inventario) y solo el valor anterior: sabe deshacer, no rehacer.
- `Historial` guarda `RegistroAccion` en una `ListaDoble` con límite 5; `deshacer_ultima` deshace
  los cambios en orden inverso. El pergamino (`EstadoJuego.usar_pergamino_retroceso`) usa ese
  mecanismo.
- `Partida._tirar_dado` anota `azar.setstate` una vez por acción, así que deshacer también
  restaura el generador.
- **Fuera del historial** (no se deshacen): cantidad de pergaminos del inventario y de cada sala
  (`recoger_pergamino_de`, `soltar_pergamino_en`, `consumir_pergamino`, `apartar_pergaminos`), la
  posición del objeto actual del inventario (`avanzar` y `retroceder`), la carga del contenido de
  una sala (`asignar_contenido`), la bitácora, `terminada` y `resultado`, y la búsqueda del cazador
  (`Perseguidor`, que no es estado del juego: research D6 de la 001).
- El `Perseguidor` se registra como `observador` en el estado de cada puerta.
- `Partida._fichas` es el método `obtener_ficha` de `RepositorioFichas`, que tiene la fuente de red:
  un `deepcopy` de la partida copiaría el repositorio y la fuente.
- Las reglas solo miran `contenido_cargado()` en `iniciar` y `mover`: ningún enemigo depende de si
  otra sala tiene su contenido.
- `Agenda.siguiente_si_corresponde(tope)` saca el siguiente evento solo si su tiempo es ≤ tope.
- `Reproductor` repite los comandos del log con `ejecutar_comando`. El controlador anota en el log
  solo los comandos que se ejecutaron bien, `pergamino` incluido.
- El guardado (`GuardadoBinario`, `GuardadoJSON`, formato 2) escribe por el recorrido común de
  `EstadoPartida` (`escribir_general`, `escribir_sala`) sobre un escritor abstracto, y rechaza
  cualquier otro número de formato.
- La copia local de cripta-06 (`cache/cripta-06.json`) tiene esqueleto (300 salas), datos y llaves,
  **pero no contenidos**. Por eso el bench usa la sintética de 300 salas (FR-427 a).

## D1. Qué se guarda fuera de los puntos de control (FR-422, FR-424)

**Decisión**: la línea de tiempo guarda la **secuencia neta de entradas**: el texto de cada comando
que se ejecutó bien, sin los revertidos, con su tipo (acción del jugador, comando que no es acción,
ajuste por pergamino, D6), el reloj de la decisión y el número de acción. Con esa secuencia y el
punto de control anterior, re-simular da el mismo estado (principio II). Cada entrada ocupa unos
100 bytes: 5 000 acciones son menos de 1 MB.

**Alternativas**:

- *Guardar todos los `RegistroAccion` (historial sin límite en la partida viva)*: describen el
  cambio, pero referencian los objetos de la partida viva y no se pueden aplicar sobre una copia
  (D2). Además, el registro vivo pasaría de 5 acciones a n.
- *Copia por acción*: es lo que prohíbe el principio VII; FR-434 la usa como referencia.

## D2. Cómo se reconstruye un estado (FR-421, FR-423, FR-429, FR-432)

Copiar el punto de control en cada consulta no cabe en 50 ms: la copia sola cuesta 63 ms con 300
salas y 454 ms con 2 000. La consulta tiene que **trabajar sobre el punto de control y dejarlo
como estaba**.

**Decisión (elegida): hacia adelante sobre el punto de control y deshacer después.**

1. Se toma el punto de control C_j de la acción jK más cercana por debajo (D5). Es una `Partida`
   independiente con su propio `Historial` **sin límite**.
2. Se re-ejecutan sobre C_j, con `ejecutar_comando` de P1, las entradas desde jK hasta el objetivo:
   a lo sumo K − 1 acciones completas, y para un instante intermedio una más con tope de tiempo
   (D9). En total, como máximo K acciones (FR-423).
3. Se arma el `Resumen` (D10) de C_j.
4. Se deshacen con `Historial.deshacer_ultima` (el mecanismo del pergamino) todas las acciones
   re-ejecutadas, y se restaura lo que no está en el historial (D8). C_j queda idéntico.

La partida viva no se toca: ni su agenda, ni su generador, ni su historial, ni su log (FR-407).

**Costo**: m (a + u) con m ≤ K. Con objetivos repartidos de forma uniforme, el p95 está cerca de
0,95 K (a + u).

**Alternativa medida (FR-429): hacia atrás invirtiendo cambios.**

Los `Cambio` de P1 solo sirven sobre el grafo de objetos donde se registraron. La forma de tener
cambios aplicables a un punto de control es crear, para cada tramo, un punto **al final** del tramo
que traiga registrados sus propios cambios: B_j es una copia de C_j a la que se le re-ejecutan las K
acciones del tramo con historial sin límite. La consulta deshace desde (j + 1)K hasta el objetivo,
resume y vuelve al final re-ejecutando esas acciones, porque `Cambio` no sabe rehacer.

| | Hacia adelante (elegida) | Hacia atrás (descartada) |
|---|---|---|
| Consulta | m_f (a + u), con m_f = distancia al punto anterior | m_b (u + a), con m_b = K − m_f: **el mismo orden** |
| Crear un punto cada K acciones | c | c + K a, porque re-ejecuta el tramo: 22 × 1,21 ≈ 27 ms más con 300 salas y 22 × 3 a 8 ≈ 66 a 178 ms con 2 000 salas, dentro del ciclo (FR-433) |
| Memoria | puntos + entradas | puntos + **todos los cambios** del tramo, unos K `RegistroAccion` por punto |
| Último tramo, el que no ha terminado | se re-simula desde C_j como cualquier otro | no tiene B_j: habría que deshacer sobre la partida viva (riesgo para FR-407) o crear B_j en cada consulta |

Hacia atrás no gana en consulta y pierde en creación, memoria y riesgo. Usar los dos sentidos y
escoger el más cercano reduciría la distancia a K/2, pero con C_j y B_j por tramo: es lo mismo que
ir hacia adelante con K/2. Se descarta y se mide en el bench (contracts/bench.md, L2).

**Otras alternativas descartadas**:

- *Copiar el punto de control y re-simular sobre la copia*: c + m a ≥ 63 ms con 300 salas.
  Incumple FR-432 en cualquier K.
- *Aplicar cambios registrados hacia adelante (rehacer con el valor nuevo)*: un paso costaría u, no
  a, y se podría usar un K tres veces mayor. Pero exige que cada `Cambio` sepa rehacer (unas 40
  llamadas a `_anotar` en `Partida`, y las operaciones de agenda, inventario y enemigos) y que sus
  referencias se traduzcan al grafo de la copia: por id de sala con `ArbolBusqueda`, por número de
  secuencia de evento, por posición en el inventario. Es rediseñar el mecanismo de P1. Queda como
  mejora analizada, sin implementar ni medir.
- *Sin puntos de control (solo el estado inicial)*: n/2 (a + u) de media, unos 4 s con 5 000
  acciones. Es la alternativa de FR-428 y se mide con pocas consultas.
- *Deshacer y rehacer sobre la partida viva*: el costo crece con n − k y la consulta tocaría el
  estado vivo.

## D3. La copia del punto de control: compartir lo que nunca cambia

**Decisión**: `copy.deepcopy` (biblioteca estándar; no reemplaza una estructura evaluada) con
ganchos `__deepcopy__` en tres clases. La copia **comparte** lo que es de solo lectura y **no
copia** lo que no es estado del juego:

| Parte | En la copia | Por qué |
|---|---|---|
| Contenido original de cada sala (`Sala.contenido`, el JSON leído) | compartido | Nunca se modifica después de `asignar_contenido`. |
| `_fichas` (método de `RepositorioFichas`) | compartido | Copiarlo copiaría el repositorio y la fuente de red. Es **obligatorio**, no una optimización. |
| Nombres de sala, ids, costos y destinos de salidas | compartidos | Son `str` e `int`: `deepcopy` ya no los copia. |
| `Perseguidor` y `observador` de cada puerta | `None` | No es estado del juego. La copia crea su propia búsqueda en el primer turno de un cazador. Si se compartiera, las puertas de la copia avisarían a la búsqueda viva. |
| Bitácora | una vacía, propia | No es estado ni sale en el resumen. Compartida, la re-simulación escribiría mensajes en la bitácora viva. |
| `Historial` | uno nuevo, vacío y **sin límite** | Lo que necesita la consulta (D2). Copiar los 5 registros vivos no sirve. |
| Puertas, salas, enemigos, objetos, trampas, agenda, eventos, jugador, inventario, `random.Random` | copiados | Cambian. Las puertas compartidas entre dos salas siguen compartidas en la copia (memo de `deepcopy`). |

**Medido**: con 300 salas, la copia pasa de 63 ms y 1,03 MB a 57 ms y 0,85 MB (−10 % de tiempo,
−17 % de memoria). Con 2 000 salas sintéticas no hay ganancia, porque su contenido es casi vacío.
El tiempo apenas baja porque lo caro es recorrer el grafo de objetos que cambian, no los datos de
solo lectura. Lo importante es lo cualitativo: fichas, búsqueda y bitácora tienen que quedar fuera.

**Alternativas** (se miden en el bench, L7):

- *`deepcopy` sin ganchos*: copia la fuente de red y comparte observadores. Incorrecto.
- *Copia por el recorrido de `EstadoPartida`* (escribir a bytes con `EscritorBinario` y armar con
  `armar_partida`): bytes compactos y reutiliza código probado. Pero armar cuesta del orden de una
  copia y genera los mismos objetos. Se mide como alternativa de creación. Para guardar es la
  elegida (D11).
- *Copia incremental por salas* (compartir con el punto anterior las salas que no cambiaron): las
  salas se enlazan entre sí (`sala_destino_ref`, puertas compartidas, `entradas`) y los eventos
  apuntan a enemigos. Una sala compartida apuntaría a vecinas de otro punto de control. Descartada.

## D4. K por defecto (FR-420, FR-432, FR-433, FR-434)

Tres condiciones, con nuestras medidas en la cripta del tamaño de la de referencia (300 salas):

1. **Consulta** (FR-432): p95 ≈ 0,95 K (a + u) = 0,95 K × 1,61 ms < 50 ms → **K ≤ 32**. Si cada
   acción costara su p95 (1,63 + 0,56 = 2,19 ms): K ≤ 24.
2. **Ciclo** (FR-433): crear un punto cuesta c = 57 ms con 300 salas y 454 ms con 2 000. Cualquiera
   de los dos supera por sí solo los 20 ms. El p95 del ciclo no los ve solo si **menos del 5 %** de
   las acciones copian: 1/K < 0,05 → **K ≥ 21**. Con el percentil de `Medicion.percentil` y N
   acciones medidas, el p95 no cae en una copia si ⌊N/K⌋ ≤ N − ⌈0,95 N⌉. Con N = 500, K = 20 queda
   justo en el borde, así que se pide K ≥ 21 con margen.
3. **Memoria** (FR-434): ≈ (n/K) s más las entradas. La copia por acción ocupa n s, y FR-434 pide
   menos de un tercio: se cumple con cualquier K ≥ 4.

| K | p95 de consulta estimado (300 salas) | Acciones que copian | Memoria con 5 000 acciones (0,85 / 1,5 MB por copia) | ¿Cumple? |
|---|---|---|---|---|
| 10 | 15 ms | 10 % | 425 / 750 MB | no (FR-433) |
| 16 | 24 ms | 6,3 % | 266 / 469 MB | no (FR-433) |
| 20 | 31 ms | 5 % | 213 / 375 MB | en el borde |
| **22** | **34 ms** (46 ms si cada acción costara su p95) | **4,5 %** | **193 / 341 MB** | **sí** |
| 25 | 38 ms (52 ms en el caso pesimista) | 4 % | 170 / 300 MB | sí, con poco margen de consulta |
| 32 | 49 ms | 3,1 % | 133 / 234 MB | no (FR-432 sin margen) |

La copia por acción con 5 000 acciones ocuparía 4,25 GB (7,5 GB con la cifra del grupo). Con K = 22
la línea ocupa 1/22 de eso, muy por debajo de 1/3.

**Decisión provisional: K = 22.** Es el valor más bajo que cumple FR-433 con margen (4,5 % < 5 %) y
deja 16 ms de margen en la consulta (46 ms en el caso pesimista). El bench mide K = 10, 16, 22, 32
y 64 y la alternativa sin puntos de control (contracts/bench.md, L1). Si L4 muestra que el p95 del
ciclo ve las copias, se sube K. Si L1 da más de 50 ms con K = 22, se baja K y se revisa L4: si no
hay ninguna K que cumpla las dos, se documenta en `DECISIONES.md` antes de cambiar el diseño.

**Escala** (2 000 salas, 50 cazadores; se reporta sin límite):

- Consulta ≈ 0,95 × 22 × (3 a 8 + 1,9) ≈ 100 a 210 ms. Pasa de 50 ms: va a Límites.
- Una copia de 454 ms cada 22 acciones no cambia el p95 del ciclo, pero sube la media unos 20 ms y
  el máximo a casi medio segundo. Va a Límites.
- Memoria ≈ 227 × 9,5 MB ≈ 2,2 GB con 5 000 acciones. Cumple FR-434 (es 1/22 de la copia por
  acción), pero es mucha memoria. Va a Límites.

## D5. Ubicar el instante o la acción pedidos (FR-401 a FR-404, FR-425)

- `decisiones`: un `Vector` con una fila por acción neta k = 1..n: (reloj d_k de la decisión,
  posición de su entrada). El reloj nunca retrocede en la secuencia neta, porque el pergamino quita
  entradas del final, así que el `Vector` queda ordenado por d_k. d_(n+1) es el reloj actual.
- **`historia #k`**: fila k, en O(1).
- **`historia t`**: búsqueda binaria propia de la primera fila con d_k ≥ t, en O(log n)
  (`crypta/estructuras/BusquedaBinaria.py`). Si d_k = t, el objetivo es «antes de la acción #k». Si
  d_k > t, es «después de los eventos ≤ t que siguen a la acción #(k − 1)», con tope t (D9). **Dos
  decisiones nunca caen en el mismo reloj**: toda acción avanza el reloj al menos 1, porque
  `Actor.intervalo` devuelve `max(1, costo * 100 // velocidad)`. Así d_k es estrictamente
  creciente y la búsqueda devuelve una sola fila.
- **Punto de control**: hay uno por cada múltiplo de K (anclas 0, K, 2K…), en un `Vector` indexado
  por j. El índice es j = ⌊m/K⌋, con m las acciones completas que preceden al objetivo: **se
  calcula, no se busca** (FR-425). La consulta examina un solo punto de control, y el bench lo
  cuenta (L6).
- **Objetivo = estado actual** (#(n + 1), o t = reloj sin eventos pendientes en t): el resumen se
  arma directamente de la partida viva, sin modificarla. Las pruebas comprueban que da el mismo
  texto que la reconstrucción (FR-421).

**Alternativa**: `ArbolBusqueda` por reloj. Es O(log n) igual, con más memoria y sin ventaja, porque
las inserciones llegan siempre ordenadas.

## D6. El pergamino (FR-410 a FR-412)

`ejecutar_y_registrar` (D12) compara `acciones_jugador` antes y después de cada comando:

- **+1**: entrada de acción y fila en `decisiones`. Si el nuevo total es múltiplo de K y ese punto
  no existe, se crea (D3).
- **0** (`avanzar`, `retroceder`): entrada que no es acción.
- **−1** (pergamino): se quitan del final las entradas hasta la última acción incluida, con su fila
  de `decisiones`. Se quitan los puntos de control cuya ancla supera el nuevo total. Se agrega una
  **entrada de ajuste** con lo que el pergamino dejó fuera del historial: pergaminos del inventario,
  posición del objeto actual y pergaminos de la sala actual. Re-ejecutar el ajuste fija esos
  valores.
- **Costo**: O(entradas y puntos quitados), nunca O(n). Con el límite de 5 retrocesos, a lo sumo 5
  acciones por vez (FR-412).
- Un punto de control con ancla igual al nuevo total sigue valiendo: se tomó en ese mismo estado
  reversible, y el ajuste queda después de él en la secuencia.
- Las entradas que no son acción y venían después de la acción revertida se quitan: su efecto (la
  posición del objeto actual) queda en el ajuste.

**Regla que se aplica**: el pergamino se gasta en el punto de la secuencia neta donde se usó, es
decir, justo antes de la acción siguiente. Una consulta anterior muestra los pergaminos que había;
una posterior, los que quedaron. Así el estado actual (#(n + 1)) es el de la partida, como pide
HU1-5.

Es lo que dice HU2-3: el resumen es igual al de una partida que hizo directamente las acciones que
quedaron, «salvo los pergaminos gastados, los pergaminos de las salas y la posición del objeto
actual del inventario». Esos tres valores están fuera del historial (P1 §2.11; constitución VII) y
son justamente los que lleva la entrada de ajuste.

## D7. Salas sin contenido en el punto de control (FR-407)

Al re-simular, el jugador puede entrar en una sala que en C_j todavía no tenía contenido.
`ejecutar_comando` recibe, en lugar de `GestorContenido.garantizar_sala`, una función que:

1. busca la sala con el mismo id en el **mapa vivo** (`Mapa.obtener_sala`, O(log V));
2. llama a `asignar_contenido(sala_viva.contenido)` sobre la sala de C_j. El dict se comparte, de
   solo lectura (D3).

Esto nunca pide nada a la red: si el jugador entró en esa sala en la secuencia neta, la sala viva
ya tenía su contenido, porque cargar contenido no se deshace. Si no lo tuviera, sería un error de
programa (`RuntimeError`), no una solicitud. En `--replay … --hasta`, el «mapa vivo» es el de la
reproducción.

**Decisión del grupo**: se acepta que la sala **quede cargada** en C_j después de deshacer. Cargar
contenido no se deshace, y el sello (D8) no lo restaura. Es correcto por dos razones:

- las reglas solo miran `contenido_cargado()` al mover y al iniciar;
- P1 ya garantiza que el orden de los enemigos de una sala no depende de cuándo llega su contenido.

Después de deshacer, sus objetos, trampas y enemigos están como recién cargados, con los pergaminos
ya apartados. Es el mismo estado que daría cargarla en la próxima re-simulación. Por eso la prueba
de D8 compara la serialización **sin el contenido de esas salas** y además repite consultas.

## D8. Lo que el historial no restaura (FR-407, FR-421)

Antes de re-ejecutar, la consulta toma un **sello** de C_j:

- `terminada`, `resultado` y `puerta_de_salida_abierta`;
- `enemigos_derrotados`;
- pergaminos del inventario y posición del objeto actual;
- largo de la bitácora;
- número de secuencia de la agenda (`agenda.siguiente_secuencia`), que el pergamino de P1 no
  rebobina: sin restaurarlo, los eventos programados en la consulta siguiente tendrían otros
  números y la serialización cambiaría; se restaura con `Agenda.restaurar_secuencia`;
- (sala, pergaminos) de la sala del jugador cada vez que la re-simulación entra en una: a lo sumo
  K + 1 salas, en un `Vector`.

Después de deshacer, restaura el sello. Los campos que ya restaura el historial se restauran igual,
sin daño.

El sello **no** restaura la carga de contenido de las salas que la re-simulación cargó en C_j:
quedan cargadas (decisión del grupo, D7).

**Prueba**:

- C_j se serializa con el recorrido de `EstadoPartida` antes y después de 50 consultas al azar.
- Se comparan los bytes **sin el registro de contenido de las salas que estaban sin cargar antes y
  quedaron cargadas**. Esas salas se identifican por su id y se omiten de la comparación.
- Además, cada consulta se repite y tiene que dar exactamente el mismo resumen la primera y la
  segunda vez. Lo mismo con la partida viva, más reloj, generador,
historial, log y solicitudes.

## D9. Instantes entre dos decisiones (FR-401)

`Partida` recibe un **tope de tiempo** opcional (`None` por omisión: el juego no cambia, FR-426).
Con tope, `_correr_hasta_el_jugador` usa `agenda.siguiente_si_corresponde(tope)` y se detiene
cuando el siguiente evento es posterior al tope. Si el siguiente es el turno del jugador en t, se
detiene antes de esa decisión. Los eventos de t que vienen después de la decisión en la agenda no
llegan a ejecutarse (FR-401, HU1-3 y HU1-4). Los cambios de la acción a medias quedan en su
`RegistroAccion` y se deshacen igual (D2).

## D10. El resumen (FR-406)

- `Resumen` (`crypta/Modelo/Resumen.py`) es un objeto con datos, armado desde una `Partida`
  cualquiera (viva, punto de control o reproducción): instante pedido (t o #k), reloj del estado,
  número de la próxima acción, sala, vida, ataque, defensa, velocidad, inventario, efectos activos,
  enemigos activos y vivos de la sala con su vida, y mapa conocido.
- El texto lo arma `crypta/Vista/FormatoResumen.py`, una función pura (contracts/resumen.md). Lo
  usan `historia`, `--replay … --hasta` y las pruebas. El reloj actual, si la vista lo muestra, va
  fuera del texto.
- **Mapa conocido**: lo define la 002, que todavía no tiene plan. Mientras no exista, el resumen
  imprime una línea fija que dice que no está disponible. Las pruebas de HU1-11 dependen de la 002
  (lo dice el supuesto de la spec).

## D11. Guardado y carga (FR-417 a FR-419)

**Decisión**: **formato 3** del archivo binario y del JSON. Al bloque general y a los registros de
sala se agrega un bloque `linea`: K, las entradas y, por cada punto de control, su bloque general y
sus salas, escritos con **el mismo recorrido de `EstadoPartida`** (`escribir_general`,
`escribir_sala`) que usa la partida viva. Al cargar, cada punto se arma con `armar_partida` y
recibe las fichas del repositorio, un historial sin límite y una bitácora vacía.

- Los formatos 1 (P1) y 2 (001) ya se rechazan por el número de formato con «formato
  incompatible», sin cambiar la partida en curso (FR-419). Las pruebas se actualizan al formato 3
  (SC-408).
- K se guarda. Si `--checkpoint-cada` pide otro, se avisa y se usa el guardado (FR-418).
- Las firmas no cambian (contracts/guardado.md): `guardar_partida(…, linea=None)` y
  `cargar_partida` devuelve solo la partida; la línea queda en el objeto lector.

**Límites**: el archivo guardado de una partida con consultas **no es igual byte por byte** al de
la misma partida sin consultas: los puntos de control conservan cargadas las salas que cargó una
consulta (D7) y se guardan así. El estado, el log y el resultado sí son iguales (FR-408, SC-403), y
las consultas después de cargar dan lo mismo (FR-417).

**Alternativa**: guardar solo el estado inicial y las entradas, y reconstruir los puntos al cargar
re-simulando todo. El archivo es pequeño, pero cargar cuesta n a + (n/K) c ≈ 6 s + 13 s con 300
salas y 5 000 acciones. Se descarta. El bench reporta tamaño y tiempo de guardar y cargar con
5 000 acciones (L8).

## D12. Dónde se registra y cómo se reproduce (FR-408, FR-413 a FR-416, FR-426)

- `crypta/Controlador/Comandos.py` agrega
  `ejecutar_y_registrar(partida, linea, comando, garantizar_sala)`: llama a `ejecutar_comando` y
  después actualiza la línea (D6). Lo usan el controlador, el reproductor y el bench, así que la
  línea se construye igual jugando que reproduciendo un log (FR-413).
- La `LineaDeTiempo` **no es atributo de la `Partida`**: la tienen el `Controlador` y la
  `Reproduccion`. Si fuera atributo, la copia de un punto de control copiaría todos los demás
  puntos.
- `historia` se reconoce en `Controlador.procesar_comando` antes de traducir el comando. No pasa
  por `ejecutar_comando` ni por el log (FR-407). Un comando mal formado lanza `ComandoInvalido`,
  igual que en P1 (FR-405). Con la partida terminada, se responde con el mensaje de FR-409.
- `--replay log --hasta t`: el reproductor repite el log completo con `ejecutar_y_registrar` y
  consulta la línea en t. Si t es mayor que el reloj final, se muestra el último estado con su
  aviso (FR-415). Sin vista (FR-414).
- `--checkpoint-cada` y `--hasta` se validan en `main.py` (contracts/cli.md).

## D13. Rendimiento esperado (FR-432 a FR-434)

| Requisito | Estimación con K = 22 | Límite |
|---|---|---|
| FR-432, cripta del tamaño de la de referencia | p95 ≈ 34 ms (46 ms en el caso pesimista) | < 50 ms |
| FR-432, escala (2 000 salas, 50 cazadores) | p95 ≈ 100 a 210 ms | sin límite; a Límites |
| FR-433, ciclo de la 001 | p95 ≈ 7,6 ms de B7 más el registro de la entrada (µs); el 4,5 % de los ciclos copia | < 20 ms |
| FR-434, 2 500 → 5 000 acciones | ≈ 2,0 × (lineal en n/K más las entradas) | ≤ 2,5 × |
| FR-434, frente a la copia por acción | ≈ 1/22 | < 1/3 |
| FR-425, puntos examinados | 1, con cualquier cantidad | no crece |

## Puntos que no quedan abiertos

No quedan «NEEDS CLARIFICATION» técnicos. Quedan tres puntos para el grupo, que no bloquean el plan:

1. La excepción de HU2-3 (pergaminos y posición del objeto actual, D6) va en un commit de spec
   aparte, antes de implementar (principio VIII).
2. El mapa conocido del resumen depende de la 002 (D10).
3. La memoria y la pausa de las copias en la partida de escala van a Límites (D4).
