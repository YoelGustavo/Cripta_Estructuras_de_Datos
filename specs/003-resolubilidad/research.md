# Investigación (fase 0): Verificación de resolubilidad

**Capacidad**: 003 — `003-resolubilidad` | **Fecha**: 2026-11-13 | **Spec**: [spec.md](spec.md) |
**Plan**: [plan.md](plan.md)

Este documento es el borrador de la sección «Resolubilidad» de `DECISIONES.md` (P2 §5.4, §7.1).
Cada decisión es **provisional** hasta que `--bench` la respalde; si una medición la cambia,
`DECISIONES.md` dirá qué medición motivó el cambio.

Notación: V salas, E salidas (E ≤ 4V), L entradas de la ubicación de las llaves, K llaves distintas
de la cripta (las de la ubicación, las que piden las puertas cerradas y `llave_salida`), R rondas.

## Lo que encontramos en el código actual

- `crypta/Modelo/Mapa.py`: carga las salas en un `ArbolBusqueda` **balanceado** con
  `desde_ordenados` (ids ordenados con `ordenar`), y asigna a cada sala un **índice denso**
  `sala.indice` en 0..V-1 siguiendo el recorrido en orden, es decir, **en orden ascendente de id**.
  `sala_por_indice(i)` es O(1). Cada sala tiene `entradas` (pares `(Puerta, Sala origen)`), que
  incluyen las salidas sin vuelta.
- `crypta/Modelo/Sala.py`: las salidas están en un `Vector` de 4 posiciones en el orden N, S, E, O
  (`DIRECCIONES`); `obtener_puerta(d)` es O(1). Una salida sin vuelta solo existe como `Puerta` en
  la sala de origen, así que recorrer `puertas()` de cada sala ya respeta el sentido (FR-303).
- `crypta/Modelo/Puerta.py`: `cerrada`, `llave` y `sala_destino_ref` (None si la sala destino no
  existe). El estado inicial de las puertas es el del esqueleto mientras la partida no empiece.
- `crypta/estructuras/ordenamiento.py`: `ordenar(vector, clave)` elige inserción o mergesort
  (estable). Los `str` de Python se comparan carácter por carácter por punto de código, que es lo
  que pide FR-308.
- `crypta/estructuras/ArbolBusqueda.py`: ABB sin autobalanceo; `insertar` con claves en orden
  produce una lista enlazada (altura n), límite ya documentado en `DECISIONES.md` §4.4 de P1.
  `desde_ordenados` construye un árbol de altura ⌈log₂(n+1)⌉.
- `crypta/Controlador/GestorCripta.py` y `crypta/Adaptadores/AlmacenDisco.py`: la copia local de una
  cripta es un JSON con `version`, `esqueleto`, `contenidos` y `datos_generales`; `cargar_cripta`
  devuelve None si la versión no coincide (validación de versión de P1). `guardar_cripta` reescribe
  el archivo entero.
- `crypta/main.py`: `crear_partida` carga la cripta, **fija el presupuesto**, crea el repositorio
  de fichas, la partida y **`partida.log`** en una sola función. Para FR-325 la verificación tiene
  que ir entre fijar el presupuesto y crear `partida.log`.
- `crypta/Adaptadores/FuenteHTTP.py`: `_get` cuenta toda solicitud, incluidos los reintentos de un
  429, y lanza `PresupuestoAgotado` (un `RuntimeError`) sin enviar la solicitud.
- No existe ningún módulo de resolubilidad ni el endpoint `/llaves` en las fuentes.

## D1. Pasar del id de una llave a un número

**Problema**. El recorrido usa vectores indexados por llave (obtenida, ronda, puertas estacionadas,
dependencia). Hay que traducir cada id de texto a un número 0..K-1 una vez por puerta cerrada y una
vez por entrada de la ubicación: O(E + L) búsquedas.

**Alternativas** (pedidas por el grupo):

| | Construcción | Búsqueda | Peor caso | Orden por id |
|---|---|---|---|---|
| (a) Tabla hash propia (encadenamiento, función hash polinómica propia sobre los caracteres) | O(K) esperado | O(1) esperado | O(K) por búsqueda si todo colisiona | no: el número es el orden de llegada; ordenar cada ronda exige comparar textos |
| (b) `ArbolBusqueda` llenado con `insertar` en orden de llegada | O(K log K) esperado | O(log K) esperado | **O(K) por búsqueda, O(K²) total** si los ids llegan ordenados | no, mismo problema |
| (c) **Ordenar los ids con `ordenar`, quitar repetidos y `ArbolBusqueda.desde_ordenados`** | O(K log K) | O(log K) garantizado | O(log K) | **sí: el número es la posición en el orden por id** |

**Decisión (provisional): (c)**. El número de una llave es su rango en el orden por id. Eso da tres
cosas a la vez:

1. Búsqueda O(log K) garantizada, sin depender del orden en que el servicio entregue las llaves.
   El riesgo de (b) no es teórico: el servicio puede devolver las llaves ordenadas (como en P2 §4.2)
   y el generador del bench las nombra en secuencia (`itm_llave_0001`, …).
2. Comparar números es comparar ids (FR-308): ordenar las llaves de una ronda es ordenar enteros, y
   recorrer 0..K-1 ya da las llaves «ordenadas por id» para FR-309, FR-311, FR-312 y FR-315 sin
   ordenar nada más.
3. Determinismo sin depender de `hash()` de Python (que cambia por proceso con `PYTHONHASHSEED`).

(a) es la más rápida en búsquedas, pero el número no sirve para ordenar y obliga a ordenar textos en
cada ronda y en cada parte del reporte; además exige una función hash propia y una estructura nueva
que solo usaría esta capacidad. Con K ≤ unos miles, log₂ K ≈ 11 comparaciones por búsqueda y solo
O(E + L) búsquedas, la ventaja de (a) es pequeña frente al costo de ordenar textos. (b) se descarta
por el peor caso documentado en P1 §4.4.

Una búsqueda binaria sobre el `Vector` ordenado daría la misma complejidad que (c); se prefiere
`desde_ordenados` porque ya existe, está probado y es lo que usa `Mapa` para las salas.

**Medición**: sección R5 del bench (contracts/bench.md): construir la numeración y hacer E + L
búsquedas con (b) con ids en orden de llegada barajado, (b) con ids que llegan ordenados (con la
altura del árbol en ambos casos), y (c). **(a) queda como alternativa analizada, sin implementar ni
medir** (decisión del grupo): su ventaja en búsquedas no compensa una estructura nueva que solo
usaría el bench, y el análisis de arriba basta para descartarla.

## D2. Sala de una ubicación → índice denso

`Mapa.obtener_sala(id)` (árbol balanceado, O(log V)) y luego `sala.indice`. Se hace una vez por
entrada de la ubicación: O(L log V). Si la sala no existe → `DatosInvalidos` (FR-319). No hace falta
otra estructura.

## D3. Recorrido por oleadas con puertas estacionadas (región alcanzable y orden, FR-303 a FR-308)

**Decisión**: un solo recorrido por anchura que avanza por **rondas** (oleadas). Estructuras, todas
por índice denso o por número de llave:

- `ronda_sala`: `Vector` de V enteros; −1 = no visitada; r ≥ 0 = entró a la región en la ronda r.
- `ronda_llave`: `Vector` de K enteros; −1 = no obtenida todavía; r = obtenida en la ronda r.
- `abre`: `Vector` de K booleanos; la llave ya se puede usar para cruzar (se activa al **cerrar** la
  ronda en que se obtuvo, no antes).
- `llaves_en_sala`: `Vector` de V posiciones, cada una None o un `Vector` con los números de las
  llaves ubicadas en esa sala.
- `estacionadas`: `Vector` de K posiciones, cada una None o un `Vector` de puertas
  `(índice origen, dirección, índice destino)` que esperan esa llave.
- Una `Cola` para la ronda en curso y un `Vector` `nuevas` con las llaves obtenidas en ella.

Ronda r:

1. Se desencola una sala x. Para cada llave k de `llaves_en_sala[x]` con `ronda_llave[k] = −1`:
   `ronda_llave[k] = r` y k va a `nuevas`.
2. Para cada salida de x en orden N, S, E, O hacia una sala y existente:
   - si es cruzable (abierta, cerrada sin llave o cerrada con `abre[k]`): si `ronda_sala[y] = −1`,
     se marca con r y se encola;
   - si es cerrada con una llave k que todavía no abre: se **estaciona** en `estacionadas[k]`.
3. Cuando la cola se vacía, la ronda termina: se ordena `nuevas` con `ordenar` (enteros = orden por
   id, D1), se agrega como ronda r del orden, se activa `abre[k]` para cada una y se **liberan** sus
   puertas estacionadas: cada destino y con `ronda_sala[y] = −1` se marca con r+1 y se encola como
   semilla de la ronda r+1. Si `nuevas` está vacía, termina el recorrido.

Respuesta a la pregunta de P2 («Una llave abre una región con otras tres llaves. ¿Qué hace su
verificación con las puertas que encontró cerradas antes de tener esa llave?»): quedan estacionadas
bajo esa llave; al obtenerla se recorren solo esas puertas, sin volver a mirar el resto de la región.

**Por qué es correcto**. Invariante: al cerrar la ronda r, la región es exactamente el conjunto de
salas alcanzables desde `sala_inicial` usando las llaves de las rondas < r, y toda puerta cerrada
con llave sin `abre` que sale de la región está estacionada bajo su llave. Las llaves no se activan
dentro de la ronda en que se obtienen, así que la ronda r+1 contiene exactamente las llaves que se
vuelven obtenibles con las de las rondas ≤ r (FR-308). Como `abre` solo crece y la región solo
crece, la región final es el punto fijo de FR-303 y no depende del orden de la cola. El orden
cumple FR-307: cada llave de la ronda r+1 tiene una ubicación alcanzable usando solo llaves de rondas
≤ r. La cola solo decide en qué orden se visitan salas de una misma ronda, lo que no cambia ningún
resultado, y además su orden es determinista.

**Complejidad**. Cada sala se encola una vez; cada salida se examina una vez desde su origen y se
libera a lo sumo una vez; cada ubicación se mira una vez: O(V + E + L). Ordenar las rondas suma
O(K log K) en total. Con la numeración (D1): **O(V + E + (E + L) log K + K log K)**, aproximadamente
lineal (FR-335).

**Resoluble (FR-305)**. Después del recorrido: `llave_salida` tiene `ronda_llave ≥ 0` y alguna
entrada `(puerta, origen)` de `sala_salida` es una puerta cerrada que pide `llave_salida` con
`ronda_sala[origen] ≥ 0`. Es O(grado de entrada) con `Sala.entradas`. Cubre `sala_inicial =
sala_salida` y el caso de solo salida abierta (HU1-9).

**Alternativas descartadas**:

- **Repetir el recorrido completo** desde `sala_inicial` cada vez que se obtiene una llave (la
  alternativa ingenua del bench, D8): O(R · (V + E)); con llaves encadenadas R ≈ K, es decir
  O(K · (V + E)). Es lo que P2 §5.4 prohíbe; se implementa para medirla y como verificador.
- **Liberar las puertas apenas se obtiene la llave** (sin esperar al fin de la ronda): da la misma
  región pero mezcla rondas, y el orden dejaría de ser el de FR-308.
- **Recorrer de nuevo la región en busca de puertas** al obtener una llave: O(V + E) por ronda; es
  la alternativa ingenua con otro nombre.
- **Marcar visitadas con `ArbolBusqueda` por id de sala** (como `Mapa.obtener_cercanas`):
  O(log V) por consulta y peor constante; el índice denso da O(1).

## D4. Dependencias por capas más allá de la frontera (FR-314)

Solo si la cripta no es resoluble. **El mismo recorrido continúa**: mismas marcas, mismas
estructuras, nunca un recorrido por llave (FR-313, P2 §5.4).

Una puerta bloqueada (pide una llave no obtenible) cuesta 1; toda otra salida cruzable cuesta 0.
Para cada sala fuera de la región se calcula la etiqueta **(capa, origen)**: capa = mínimo de
puertas bloqueadas cruzadas desde la región; origen = la llave de **menor id** entre las primeras
puertas bloqueadas de los caminos con esa capa. La dependencia de una llave no obtenible es el
origen de la ubicación con menor (capa, origen).

Estructuras nuevas: `capa_sala` y `origen_sala` (`Vector` de V), `dependencia` (`Vector` de K, −1 =
ninguna), y un `Vector` de semillas de la capa siguiente.

1. **Capa 1**: las semillas son las puertas que siguen estacionadas al terminar las rondas (llaves
   nunca activadas) cuyo destino no está en la región. Son exactamente la frontera bloqueada (las
   que unen dos salas de la región se descartan, FR-310). Recorriendo `estacionadas` en orden de
   llave 0..K-1, las semillas ya salen agrupadas por origen ascendente; el origen de cada una es la
   llave que pide.
2. **Dentro de una capa**: se procesan los grupos de semillas por **origen ascendente**; cada grupo
   se expande por anchura con una `Cola` por salidas cruzables (costo 0), marcando `capa_sala` y
   `origen_sala`. Una sala ya marcada (en una capa anterior o con un origen menor en esta) no se
   vuelve a tocar. Las puertas bloqueadas que salen de salas de esta capa hacia salas sin marcar van
   a las semillas de la capa siguiente con el **origen heredado** de su sala (la dependencia es la
   llave de la *primera* puerta bloqueada, no la de la última).
3. **Capa siguiente**: se ordenan sus semillas por origen con `ordenar` (estable) y se repite. Se
   termina cuando no hay semillas.
4. Al marcar una sala, cada llave no obtenible ubicada en ella que aún no tenga dependencia recibe
   `origen_sala` (la primera marca es la mínima, porque las capas crecen y los orígenes crecen dentro
   de cada capa).

**Por qué es correcto**. Es un recorrido 0-1 por niveles. Que procesar los grupos de una capa por
origen ascendente da el mínimo: si una sala es alcanzable en la capa c desde semillas con orígenes
S, la inundación del menor de S la alcanza antes que cualquier otra, porque dentro de la capa todo
cuesta 0 y las únicas salas que la detienen ya están marcadas con una etiqueta menor o igual, y lo
que hay más allá de ellas también es alcanzable con esa etiqueta. Los caminos de capa mínima cuyo
primer bloqueo une dos salas de la región nunca son estrictamente mejores, así que basta sembrar con
la frontera.

**Sin dependencia** (FR-314): llave sin ubicación («no está en la cripta») o cuyas ubicaciones no se
marcaron al terminar las capas («su sala no se alcanza ni abriendo todas las puertas»). Las salidas
sin vuelta se respetan porque se recorren solo desde su origen.

**Complejidad**. Cada sala se marca una vez y cada salida se examina una vez desde su origen: O(V +
E + L). Ordenar semillas: cada puerta es semilla a lo sumo una vez, O(E log E) en total. Sumado al
recorrido por oleadas: **O(V + E + L + (E + L) log K + E log E)**.

**Alternativas descartadas**:

- **Un recorrido por llave no obtenible** (desde la región hasta sus ubicaciones): O(K · (V + E)).
  Prohibido por FR-313 y P2 §5.4. Se implementa en la alternativa ingenua para comparar (D8).
- **Dijkstra con `MonticuloMin` sobre (capa, origen)**: correcto, pero O((V + E) log E) en todo el
  recorrido y más trabajo que el 0-1 por niveles, que solo ordena las semillas de cada capa.
- **Agrupar semillas con un `Vector` de K listas por origen** en cada capa: evita ordenar, pero hay
  que recorrer las K listas en cada capa: O(K · capas), cuadrático con llaves encadenadas.
- **Inundación única con la cola en orden de llegada**: asigna el origen de la primera semilla que
  llega, no el menor; viola el desempate de FR-314 (HU2-6).

## D5. Ciclos de dependencia (FR-315)

El grafo «llave → llave de la que depende» tiene a lo sumo una salida por llave (grafo funcional),
así que cada componente tiene a lo sumo un ciclo. Con un `Vector` de estado por llave (0 sin ver, 1
en el camino actual, 2 terminada) y un `Vector` como pila del camino, se parte de cada llave no
obtenible en orden 0..K-1 y se sigue `dependencia` hasta llegar a −1, a una llave terminada o a una
llave del camino actual (estado 1): ese es un ciclo nuevo, que se extrae de la pila. Luego se
**rota** para que empiece en su llave de menor número (= menor id) y se agrega. Al final se ordenan
los ciclos por su primera llave con `ordenar`. Cada llave se visita una vez: O(K + K log K).

Las llaves que llegan a un ciclo sin pertenecer a él quedan en estado 2 sin aparecer en ningún ciclo
(FR-315, HU2-7). El ciclo de una llave que depende de sí misma tiene longitud 1 y se muestra
`a → a` (HU2-1).

Alternativa descartada: buscar ciclos con un recorrido desde cada llave sin marcas compartidas,
O(K²) con cadenas largas.

## D6. Partes del reporte sin ordenar textos (FR-309 a FR-312, FR-316)

- **Llaves no obtenibles** (FR-309): recorrer 0..K-1 con `ronda_llave = −1`.
- **Frontera** (FR-310): recorrer las salas de la región por índice 0..V-1 (= orden de id) y sus
  salidas en N, S, E, O; se toman las cerradas con llave no obtenible y destino fuera de la región.
  O(V + E), sin ordenar. Se marca en un `Vector` de K booleanos qué llaves pide la frontera.
- **Ubicación de las llaves de la frontera** (FR-311): las ubicaciones se ordenan **una vez** al
  cargarlas por (número de llave, id de sala, id de enemigo) con `ordenar`, y se guarda en un
  `Vector` de K+1 posiciones dónde empieza cada llave. Para la comparación, una ubicación sin
  enemigo usa la cadena vacía, así que va antes que las de la misma sala con enemigo, como pide
  FR-311.
- **Dependencias** (FR-312) y **ciclos** (FR-315): D4 y D5.

## D7. Validación de la ubicación de las llaves (FR-319)

Al leer la respuesta (de red o de disco), antes de verificar: la raíz debe tener `llaves` como lista;
cada entrada debe ser un objeto con `id` texto no vacío, `sala` entero (se rechaza `bool`, igual que
`leer_costo` de la 001) que exista en el esqueleto, y `enemigo` ausente, null o texto. Cualquier
falla lanza `DatosInvalidos` con la posición de la entrada, el id si lo tiene y el problema. Se
valida igual lo que viene de la copia local: un archivo editado a mano no se acepta en silencio. Es
O(L log V).

## D8. Alternativa ingenua (bench y verificador de pruebas)

`VerificadorIngenuo` calcula el mismo resultado sin ninguna de las ideas de D3–D4, para medirla
(FR-331) y para comprobar el resultado (FR-332, SC-302):

- **Orden**: repetir el recorrido completo desde `sala_inicial` con las llaves de las rondas
  anteriores; las llaves nuevas forman la ronda siguiente; parar cuando no aparece ninguna. Con
  llaves encadenadas, cada repetición obtiene una sola llave: «repetir el recorrido cada vez que se
  obtiene una llave». O(R · (V + E)).
- **Dependencias**: para cada llave no obtenible y para cada llave distinta de la frontera (en orden
  de id), un recorrido 0-1 desde los destinos de las puertas de la frontera que piden esa llave
  hasta las ubicaciones de la llave buscada; se elige el menor (capas, id). Es un recorrido por
  llave, deliberadamente independiente del truco de agrupar por origen de D4.
- **Frontera, ubicaciones y ciclos**: se calculan de nuevo por su cuenta, buscando sin las
  estructuras compartidas (búsqueda lineal en vectores).

Comparten solo la lectura validada y la numeración (D1), porque no son lo que se mide. Las dos
alternativas producen un `ResultadoVerificacion` y se comparan por su **texto** (el mismo que se
muestra), así la comparación cubre todo lo que ve el jugador.

## D9. Dónde y cuándo se verifica; red y copia local (FR-321 a FR-329)

- **Endpoint**: `GET /criptas/<id>/llaves` en `FuenteHTTP.obtener_llaves`, contado por `_get`
  (FR-322). Se pide **después** de `fijar_presupuesto`, como el resto. `PresupuestoAgotado` o
  `RuntimeError` de red → «no se pudo verificar» (FR-324).
- **Copia local** (FR-323): `AlmacenDisco.guardar_cripta` agrega el campo `llaves` (la respuesta tal
  cual) al JSON de la cripta, con la misma `version`. `GestorCripta.cargar_llaves` usa la copia
  local si la versión coincide y trae `llaves`; si no, la pide a la fuente. Una copia de la primera
  parte (otra versión) ya se invalida con la validación existente; una copia de la misma versión sin
  `llaves` (guardada antes de esta capacidad) solo pide las llaves, sin volver a pedir el esqueleto.
- **Sin conexión**: `FuenteOffline.obtener_llaves` lee el campo `llaves` de la copia local; si no
  está, lanza `LlavesNoDisponibles` (FR-324). `FuenteDatos.obtener_llaves` no es abstracto: por
  omisión lanza `LlavesNoDisponibles`, así las fuentes falsas de las pruebas actuales no se rompen.
- **Persistir**: cuando la partida no inicia y en `--verificar`, en línea, se guarda la copia local
  (esqueleto, contenidos ya cargados y llaves) antes de salir (FR-323, HU4-5). Cuando la partida
  inicia, `persistir` del final la guarda como hoy, ahora con las llaves.
- **No pide contenido** (FR-321): la verificación solo recibe el `Mapa` (esqueleto) y la ubicación;
  no tiene acceso a `GestorContenido`.
- **Inicio de partida**: `crear_partida` se divide en `preparar_cripta` (cargar, fijar presupuesto,
  llaves, verificar) y la creación de la partida. `partida.log` se crea solo si se decide iniciar
  (FR-325). El resultado se imprime antes de crear la vista; no toca el mapa conocido (FR-325) ni la
  partida (FR-327). `--replay` (`PreparadorReplay`) y la carga de una partida guardada no pasan por
  `preparar_cripta` (FR-326).
- **Códigos** (FR-325, FR-329): 0 resoluble; 2 no resoluble; 1 no verificable o datos inválidos.
  Los datos inválidos (FR-319) cortan antes de preguntar por `--forzar`.

## D10. Formato del texto

El texto del orden y del reporte es una función pura del `ResultadoVerificacion`
(`crypta/Vista/FormatoVerificacion.py`), sin estado ni E/S, usada por `--verificar`, por el inicio de
partida y por la comparación del bench. Al ser pura y recorrer solo vectores ya ordenados, el texto
es idéntico byte por byte entre ejecuciones (FR-320, SC-305). Formato exacto en
[contracts/reporte.md](contracts/reporte.md).

## D11. Rendimiento esperado (FR-334, FR-335)

Para 2 000 salas, ~8 000 salidas y 500 llaves, el recorrido completo son unas decenas de miles de
operaciones de `Vector`; con el costo medido en la 001 (búsqueda en 2 000 salas en pocos ms) se
espera muy por debajo de 200 ms. La alternativa ingenua con 500 llaves encadenadas repite ~500
recorridos de la cripta: se espera del orden de segundos, y su cociente al duplicar el tamaño cerca
de 4. Se mide en R1 y R3, solo hasta 2 000 salas (con 4 000 y 8 000 tardaría minutos).

La medición de FR-334 empieza con el `Mapa` ya cargado (cargar el esqueleto es P1 y 001) y la
respuesta de llaves en memoria, e incluye validación, numeración, recorrido, reporte y texto. El
bench reporta aparte el tiempo de cargar el `Mapa`.

## Puntos que no quedan abiertos

No hay «NEEDS CLARIFICATION».
