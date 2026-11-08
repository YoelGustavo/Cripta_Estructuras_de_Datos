# Investigación (fase 0): Terreno y cazador

**Capacidad**: 001 — `001-terreno-cazador` | **Fecha**: 2026-11-07 | **Spec**: [spec.md](spec.md) |
**Plan**: [plan.md](plan.md)

Este documento es el borrador de la sección «La ruta más barata del cazador» y «Rutas que dejan de
ser válidas» de `DECISIONES.md` (P2 §5.1, §5.2, §7.1). Cada decisión está marcada como
**provisional** hasta que `--bench` la respalde; si la medición la cambia, `DECISIONES.md` dirá qué
medición motivó el cambio.

Notación: V_r y E_r son las salas y salidas de la región con dist ≤ r alrededor del jugador
(r = rango); H es la cantidad de cazadores activos; V y E, las de toda la cripta. Cada sala tiene a
lo sumo 4 salidas (N, S, E, O), así que E ≤ 4V.

## Lo que encontramos en el código actual

- `crypta/Modelo/Partida.py`: `COSTO_MOVER = 100` en `mover` del jugador. `_turno_enemigo`
  reprograma a todo enemigo con `COSTO_ATACAR` (100) después de atacar, moverse o esperar;
  `_destino_errante` y `sala_con_rastro_mas_fresco` devuelven la **sala** destino, no la salida, así
  que hoy no se sabe qué salida se atravesó.
- `crypta/Modelo/Sala.py`: lee `sala`, `cerrada`, `llave` y `cierre_automatico` de cada salida; no
  lee `costo`. Las salidas se guardan en un `Vector` de 4 posiciones en orden N, S, E, O.
- `crypta/Modelo/Puerta.py`: las dos `Puerta` de una salida comparten un `EstadoPuerta`
  (`Mapa._compartir_puertas`). `cerrada` es una propiedad: el pergamino la restaura con `setattr`,
  así que todo cambio de una puerta (abrir, cierre automático, deshacer, carga) pasa por el setter.
- `crypta/Modelo/Agenda.py`: `reprogramar_por_velocidad` ya reescala el restante con la fórmula de
  P1 §2.3 y da secuencia nueva, sin importar de dónde salió el intervalo. FR-007 no requiere cambios
  de lógica, solo pruebas con costos distintos de 100.
- `crypta/Controlador/Controlador.py`: captura `ValueError` en `procesar_comando`, muestra el error
  y **sigue la partida**. Un dato inválido que llegue a mitad de partida no puede ser `ValueError`,
  o la partida seguiría (contradice FR-011).
- `crypta/Adaptadores/RegistroPartida.py`: `anotar` abre el archivo en modo `"a"` y lo cierra en
  cada comando, así que `partida.log` ya queda guardado si la partida se detiene.
- `crypta/Adaptadores/GuardadoBinario.py`: `FORMATO_GUARDADO = 1`; el lector rechaza otra versión
  con un mensaje. `EstadoPartida.escribir_sala` escribe las puertas sin costo.
- `crypta/bench/bench_ciclo.py` ya mide el p95 del ciclo sobre `ACCIONES = 60` acciones con
  criptas sintéticas por semilla; se extiende, no se reescribe.

## D1. Algoritmo de la ruta más barata

**Decisión (provisional)**: búsqueda de costo mínimo (Dijkstra) con nuestro `MonticuloMin`,
**perezosa y reanudable**, que se detiene en cuanto el siguiente valor del montículo supera lo que
el cazador necesita: `min(rango, dist(sala del cazador))`.

**Razón**:
- Los costos son enteros ≥ 1 y no uniformes: contar salas (recorrido por anchura) no sirve (P2
  §5.1). Con costos positivos, Dijkstra asienta cada sala con su distancia definitiva en orden no
  decreciente, así que detenerse al pasar r deja exactamente las salas con dist ≤ r y nada más:
  el trabajo es O((V_r + E_r) log E_r), no O(V log V) (FR-036).
- Montículo con **inserción perezosa** (se inserta de nuevo en vez de bajar la clave; al sacar una
  entrada vieja se descarta). Nuestro `MonticuloMin` no tiene «bajar clave» y, como E ≤ 4V, el
  montículo a lo sumo tiene 4 veces más entradas que salas.
- El orden de los empates dentro del montículo no cambia el resultado: las distancias de Dijkstra
  son únicas sea cual sea el orden en que se sacan los empates, y el desempate de FR-017 se aplica
  después, sobre esas distancias (ver D3). Por eso la decisión es determinista sin usar el azar
  (FR-021).

**Alternativas descartadas**:

| Alternativa | Por qué no |
|---|---|
| Recorrido por anchura (`Cola`) | Solo vale con costos uniformes; da la ruta con menos salas, que el Apéndice B («menos salas pero mayor costo») exige no seguir. |
| Montículo con «bajar clave» (montículo indexado) | Necesita la posición de cada sala en el montículo: otro arreglo por sala y más código en `MonticuloMin`. Con E ≤ 4V la inserción perezosa cuesta a lo sumo log(4V) ≈ log V + 2 por operación. Se puede medir si el perfil muestra que el montículo domina. |
| Cubetas por costo (Dial) o montículo de base | Funcionan con enteros pequeños y acotados; los costos de la cripta no tienen tope publicado. |
| Bellman-Ford | O(V·E); solo tiene sentido con costos negativos, que no existen. |
| A* | No hay una heurística admisible: las salas no tienen coordenadas en el esqueleto. |
| Todas las parejas (Floyd-Warshall) precalculado | O(V³) de tiempo y O(V²) de memoria (4·10⁸ celdas con 20 000 salas), y queda inválido con cada cambio de puerta. |
| Búsqueda dinámica incremental (actualizar distancias al cambiar una puerta, tipo Ramalingam-Reps) | Mucho código difícil de demostrar equivalente; la invalidación selectiva de D4 ya evita recalcular por los cambios que no afectan. Se deja como trabajo futuro si `--bench` muestra que los cambios dentro de la región dominan. |
| `heapq`, `networkx`, `dict`, `set`, `collections`, `bisect` | Prohibidos por la constitución (principio I) y P2 §6.2. |

## D2. Cálculo compartido frente a cálculo por cazador

**Decisión (provisional)**: **una sola búsqueda compartida desde la sala del jugador**, sobre las
salidas **invertidas** (para cada sala x, las salidas abiertas y→x que llegan a ella). Cada cazador
decide mirando solo las salidas de su sala. La alternativa por cazador se implementa igual para
medirla (FR-031).

**Razón**:
- Todos los cazadores persiguen al mismo jugador (P2 §5.1): dist(x, jugador) para toda x de la
  región sale de una sola búsqueda con origen en el jugador. Con H cazadores, la búsqueda se hace una
  vez por cada estado distinto (sala del jugador, puertas), no H veces.
- **Por qué se invierten las salidas en lugar de suponer simetría**: P2 §3.1 dice que el costo es el
  mismo en ambos sentidos, pero no garantiza que toda salida tenga una salida de vuelta en la sala
  destino (`Mapa._compartir_puertas` ya tolera que falte). Si se buscara por las salidas de ida desde
  el jugador se obtendría dist(jugador, x), que solo coincide con dist(x, jugador) si todas las
  salidas tienen vuelta. Buscar por las «entradas» de cada sala da dist(x, jugador) siempre. Si la
  cripta es simétrica, ambas cosas coinciden y el costo es el mismo. Las entradas se arman una sola
  vez al cargar el mapa: O(V + E).
- Con la búsqueda perezosa (D1), la búsqueda compartida solo avanza lo que pida el cazador que más
  necesite: el límite es max sobre los cazadores que deciden de min(rango, dist(su sala)), no el
  mayor rango de la cripta. Un cazador lejano y de rango grande no obliga a explorar si otro ya
  extendió lo suficiente, y uno de rango pequeño no paga por los grandes.

**Alternativa medida — búsqueda por cazador**: Dijkstra desde la sala u del cazador hacia el jugador,
con etiqueta (distancia, primer paso) comparada en orden lexicográfico: al relajar una salida con
igual distancia se conserva el menor id de primer paso. Como todos los costos son ≥ 1, todos los
predecesores de una sala en rutas mínimas se asientan antes que ella, así que el primer paso de la
sala del jugador es la vecina de menor id entre las que inician una ruta mínima. Es justo la
diferencia entre «encontró una ruta» y «encontró la que exige el desempate» (P2 §8). Se detiene al
asentar al jugador o al pasar el rango. Costo: O((V_r(u) + E_r(u)) log E_r(u)) por **turno de cada
cazador**.

**Cuándo conviene cada una (hipótesis que `--bench` debe confirmar o refutar)**:
- Compartida: muchos cazadores, o varios turnos de cazador entre dos cambios de la sala del jugador
  o de las puertas. Con H = 50 la por-cazador hace ~50 búsquedas por ciclo y la compartida ~1.
- Por cazador: un solo cazador cuyo rango es mucho menor que la distancia típica de los otros, o
  estados que cambian en cada turno (el jugador se mueve y las puertas cambian sin parar), donde
  la compartida no reutiliza nada y explora una región alrededor del jugador de radio parecido.

## D3. Decisión de un cazador sobre la búsqueda compartida (FR-013 a FR-017)

En el turno del cazador en la sala u, con la búsqueda vigente del jugador en la sala P:

1. Si u = P: ataca (FR-013). No se toca la búsqueda.
2. Se extiende la búsqueda mientras el mínimo del montículo sea ≤ rango y u no esté asentada.
3. Si u no quedó asentada: no hay ruta o d > rango → espera con costo 100 (FR-015).
4. Si u quedó asentada, d = dist(u) ≤ rango. Entre las salidas abiertas de u hacia v con
   costo(u, v) + dist(v) = d, se elige la v de menor id (FR-017). Toda candidata cumple
   dist(v) = d − costo < d, así que ya está asentada; una vecina no asentada tiene dist > lo
   explorado ≥ d y no puede cumplir la igualdad. El movimiento cuesta `costo(u, v)` (FR-016).
5. Si dos salidas de u llevan a la misma v y ambas cumplen la igualdad, tienen el mismo costo, así
   que el resultado observable es el mismo; se toma la primera en orden N, S, E, O.

Costo por cazador cuando la búsqueda ya alcanza: O(4). Por ciclo: O(H + trabajo de extensión), que
crece linealmente con H (FR-037).

## D4. Reutilización e invalidación (FR-019, FR-032)

**Qué determina la respuesta**: dist(x, jugador) depende solo de (a) la sala del jugador y (b) qué
salidas están abiertas (los costos no cambian durante la partida). La sala del cazador, la vida, la
velocidad, la muerte o el movimiento de otros actores y el contenido descargado **no** entran en el
cálculo (FR-018). Por eso, con los mismos (a) y (b), la búsqueda guardada es exactamente la que se
haría desde cero.

| Evento entre dos turnos | ¿Invalida? | Por qué |
|---|---|---|
| El jugador cambia de sala (mover, deshacer, cargar) | Sí, todo | Cambia el origen. Se detecta comparando la sala de origen guardada con la actual en cada consulta, así que también cubre el pergamino sin código especial. |
| Se abre o cierra una salida con algún extremo **asentado** | Sí, todo (provisional) | La relajación desde la sala asentada se hizo con el estado viejo de esa salida. |
| Se abre o cierra una salida con **ambos extremos sin asentar** | No | Ver la demostración abajo. |
| Otro actor se mueve, muere, cambia de velocidad; un cazador se activa | No | No entran en el cálculo. |
| Pergamino de retroceso | No hace falta, pero se invalida igual | Las puertas restauradas pasan por el setter (avisan) y la sala del jugador se compara en cada consulta. Se invalida igual por seguridad: ocurre como mucho 5 veces y cuesta una búsqueda. |
| Cargar una partida guardada | Sí | Es otra `Partida` con otro mapa: se crea una búsqueda nueva. |

**Demostración del caso «ambos extremos sin asentar»**. Sea ρ la mayor distancia asentada. Toda sala
sin asentar tiene dist ≥ ρ. (i) Las distancias asentadas no cambian: una ruta nueva que use la
salida (x, y) cuesta al menos min(dist(x), dist(y)) + costo ≥ ρ + 1 > ρ, y toda distancia
asentada es ≤ ρ. (ii) El montículo sigue siendo el que tendría un cálculo desde cero: sus entradas
salen solo de relajar salidas de salas asentadas; la salida (x, y) nunca se relajó porque ni x ni y
se asentaron, y cuando se asiente cualquiera de las dos, se leerá el estado vigente de la salida. Por
lo tanto, seguir extendiendo da las mismas distancias que una búsqueda nueva con el estado actual.

**Cómo se entera la búsqueda de un cambio de puerta**: `EstadoPuerta` guarda sus dos salas extremo y
avisa al observador (la búsqueda compartida) cuando `cerrada` cambia de valor. El aviso cuesta O(1):
mira si alguno de los dos extremos está asentado en el cálculo vigente.

**Variantes que mide `--bench` (FR-032)**: (1) recalcular siempre desde cero en cada turno de
cazador; (2) reutilizar e invalidar todo ante cualquier cambio de puerta; (3) reutilizar con la
invalidación selectiva de la tabla. Se reporta, en el escenario de puertas que casi nunca cambian y
en el de puertas que cambian seguido, el tiempo, la cantidad de búsquedas y de salas asentadas
(«cuánto trabajo se ahorra realmente», P2 §5.2). Si (3) no ahorra frente a (2), se adopta (2) por
simple y se documenta.

**Equivalencia comprobada**: un verificador con su propia búsqueda (otra instancia, siempre desde
cero) compara cada decisión en las pruebas de SC-002 y en `--bench` (FR-033).

## D5. Dónde se guardan las distancias sin `dict`

**Decisión (provisional)**: cada sala recibe al cargar el mapa un **índice denso** 0..V−1 (su
posición en el recorrido en orden del `ArbolBusqueda` del mapa). Cada búsqueda tiene sus propios
`Vector` de tamaño V: `dist`, `marca` (id del cálculo en que se tocó la sala) y `asentada` (id del
cálculo en que se asentó). Una sala tiene un valor válido solo si su marca es la del cálculo vigente;
empezar un cálculo nuevo es solo sumar 1 al id, O(1), sin limpiar los V valores.

| Alternativa | Acceso | Reinicio | Problema |
|---|---|---|---|
| **Vectores por índice denso + marca** (elegida) | O(1) | O(1) | O(V) de memoria por búsqueda, reservada una sola vez al cargar. |
| Campo en cada `Sala` + marca (propuesta del grupo) | O(1) | O(1) | Solo cabe **un** cálculo a la vez: el verificador desde cero (FR-033), la alternativa por cazador (FR-031) y la búsqueda compartida necesitan cálculos simultáneos e independientes. Además mete datos derivados en una entidad del juego que se guarda y se revierte. |
| `ArbolBusqueda` por id de sala, nuevo por cálculo | O(log V_r) (si queda balanceado; con inserciones en orden de distancia no hay garantía) | O(1) (árbol nuevo) | Más lento en la operación más frecuente; el árbol actual no se autobalancea. |
| Limpiar un arreglo de V posiciones por cálculo | O(1) | O(V) | Rompe FR-036: cada búsqueda pagaría el tamaño de toda la cripta. |
| Tabla hash propia | O(1) esperado | O(V_r) | Más código que la marca, sin ventaja cuando ya hay índices densos. |

El `--bench` incluye una medición corta de vectores con marca frente a `ArbolBusqueda`, sobre la
misma búsqueda, para respaldar la decisión con datos.

## D6. Lo calculado para las rutas no es estado del juego

Las búsquedas (vectores, montículo, id de cálculo) no se registran en el historial del pergamino ni
se escriben en el archivo de guardado: se pueden reconstruir desde el esqueleto y las puertas, y por
D4 nunca cambian una decisión. Esto respeta el principio VII (no se guarda más estado del necesario)
y hace que el pergamino y la carga solo necesiten invalidar.

## D7. Costo de las salidas y validación (FR-001, FR-002, FR-010)

- `Sala` lee el `costo` crudo de cada lado (`None` si no está). Si un lado declara un valor que no es
  un entero JSON (se rechazan `bool`, `float` aunque sea `250.0`, y texto) o es < 1, se rechaza la
  cripta.
- `Puerta.compartir_estado_con` junta los dos lados: si ambos declaran y difieren, se rechaza; si
  solo uno declara, ese vale para los dos (aclaración de la sesión 2026-11-07); si ninguno, queda
  `COSTO_POR_OMISION = 100` (única constante permitida, FR-024 y principio IV).
- El costo vive en el `EstadoPuerta` compartido, así que es el mismo en ambos sentidos por
  construcción (FR-002).
- El rechazo usa una excepción propia `DatosInvalidos` (no hereda de `ValueError`) con la sala, la
  dirección y el problema. `main.py` la muestra y no inicia la partida.

## D8. Rango del cazador y datos inválidos durante la partida (FR-011)

- La ficha con `comportamiento: "cazador"` debe traer `rango` entero (no `bool`), ≥ 0. Se valida al
  entrar la ficha al `RepositorioFichas` (respuesta de red o lectura de disco) y otra vez en
  `Enemigo.activar`, por defensa.
- Si falla antes de iniciar: `DatosInvalidos`, la partida no inicia.
- Si falla con la partida empezada (por ejemplo, la precarga trae la ficha): `DatosInvalidos` llega
  al `Controlador`, que **no** la trata como un `ValueError` de comando: muestra el mensaje y termina
  la sesión de forma controlada. `partida.log` ya está escrito, porque `RegistroPartida.anotar`
  cierra el archivo en cada comando; el plan agrega una prueba de eso.
- El rango 0 es válido y no necesita un caso especial: la búsqueda asienta solo la sala del jugador.

## D9. Movimiento con costo para todos los actores (FR-003 a FR-006)

- `Partida.mover` usa `puerta.costo` en lugar de `COSTO_MOVER` (la constante se elimina).
- `_turno_enemigo` pasa a programar el siguiente turno con el costo de la acción que hizo: 100 si
  atacó o esperó, el costo de la salida si se movió.
- `_destino_errante` y el rastreador devuelven la **puerta** elegida (y de ella, la sala). El orden de
  las opciones y la llamada a `_tirar_dado` no cambian, así que el generador recibe las mismas
  llamadas (FR-006, FR-008).
- Con todos los costos en 100, el intervalo, la agenda y el azar quedan idénticos a P1 (FR-008):
  se comprueba repitiendo un `partida.log` de la primera parte.

## D10. Guardado (FR-026)

- El archivo de partida escribe el costo de cada salida. Cambia el formato: `FORMATO_GUARDADO` sube
  de 1 a 2 (y `FORMATO_JSON` igual en el guardado JSON del `--bench`). Un archivo con formato 1 se
  rechaza con el mensaje existente; la migración explícita o el reporte final de incompatibilidad
  son de la especificación de la línea de tiempo (P2 §3.6), que puede volver a subir el formato.
- Los cazadores ya se guardan como cualquier enemigo (sala, vida, activo, evento pendiente). El rango
  **no** se escribe: sale de la ficha, y el guardado ya exige la misma versión de catálogo al cargar.
  Así el rango no se duplica ni puede contradecir al catálogo.
- No se guarda nada de las búsquedas (D6).

## D11. Persistencia local de costos y rangos (FR-025, FR-027)

No requiere código nuevo de red: el costo viene dentro del esqueleto que `GestorCripta` ya descarga y
guarda tal cual con la versión de la cripta, y el rango viene dentro de la ficha que
`RepositorioFichas` ya guarda con la versión del catálogo. Lo de la primera parte se invalida por la
validación de versión que ya existe. El plan agrega pruebas con una fuente falsa que cuenta
solicitudes para demostrar que no hay solicitudes nuevas.

## D12. Revisión de la primera parte (P2 §5.6)

No es requisito de esta especificación, pero los cazadores agregan eventos a la agenda. El
`--bench` del ciclo con cazadores deja evidencia para la sección §5.6 de `DECISIONES.md`; si la
agenda aparece como cuello de botella, se trata en esa sección.
