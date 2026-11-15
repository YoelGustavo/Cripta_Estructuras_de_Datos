# Investigación (fase 0): Niebla de guerra e «ir a»

**Capacidad**: 002 — `002-niebla-ir-a` | **Fecha**: 2026-11-15 | **Spec**: [spec.md](spec.md)

Decisiones D1–D14 con su razón y las alternativas. Son **provisionales** hasta tener la evidencia
de `--bench`. Si una medición las cambia, `DECISIONES.md` §5.3 lo dirá (constitución X).

## Lo que encontramos en el código actual

- `Mapa` (`crypta/Modelo/Mapa.py`) ya da a cada sala un **índice denso** 0..V−1 en orden de id
  (`sala.indice`, `Mapa.sala_por_indice`) y sus **entradas** (`sala.entradas`: pares
  `(puerta, origen)`). Los dos lados de una salida comparten un `EstadoPuerta`
  (`Puerta.compartir_estado_con`), con sus `extremos`.
- `EstadoPuerta` tiene un único `observador` (el `Perseguidor` de la 001), que recibe
  `puerta_cambio` cuando `cerrada` cambia de valor. `__deepcopy__` lo deja en `None` (004, D3).
- `DistanciasLimitadas` (`crypta/estructuras`) es un Dijkstra perezoso y reanudable, **genérico**:
  recibe `entradas(nodo)` y calcula distancias **hacia** un origen. `reiniciar` es O(1) gracias a las
  marcas. `RutaPorCazador` es la búsqueda hacia adelante, con el desempate por primer paso, que sirve
  de verificador independiente.
- El historial de P1 (`Historial`, `RegistroAccion`, `Cambio`) deshace cambios de atributo y de
  operación. `Historial.registrar_cambio` no hace nada si no hay una acción abierta (así el estado
  inicial no se registra).
- La 004 copia la `Partida` en cada punto de control con `deepcopy` (excluye `_perseguidor`,
  `_fichas`, `al_ejecutar_evento`), y reconstruye re-ejecutando comandos y deshaciendo con el
  historial. El archivo de partida está en el **formato 3** (`FORMATO_GUARDADO = 3`,
  `FORMATO_JSON = 3`), y los puntos de control se guardan con `escribir_general` y `escribir_sala`.
- La bitácora avisa hoy de cosas que pasan en cualquier sala: `_cerrar_puerta` («Una puerta se
  cierra automáticamente»), `_regenerar` («… regenera vida») y `_rearmar_trampa` («Una trampa
  vuelve a estar armada»). Los demás avisos ya son de la sala del jugador o del jugador
  (`_mover_enemigo` ya filtra).
- La vista (`VistaConsola.mostrar_estado`) muestra el estado **real** de las puertas de la sala
  actual.
- `RegistroPartida` está en el formato de registro 1. `leer_registro` encola cada línea no vacía
  después de `---`. Ningún comando empieza con `#`.
- `Resumen` (004) tiene `mapa_conocido = None`, y `FormatoResumen` imprime la línea fija «Mapa
  conocido: no disponible (capacidad 002)» (T057 pendiente).
- `cache/cripta-06.json` (la copia local más grande) trae el **esqueleto de 300 salas** sin
  contenidos. Para «ir a» basta el esqueleto.

## D1. Estado de cada sala: `Vector` por índice denso

**Decisión**: `MapaConocido` guarda un `Vector` de V enteros, uno por sala en el índice denso de la
001: 0 desconocida, 1 avistada, 2 explorada. Consultar es `estados.obtener(sala.indice)`, O(1)
(FR-235). Lleva además dos contadores, `exploradas` y `avistadas`, para el resumen.

**Razón**:

- Toda consulta frecuente llega con un objeto `Sala` (la vista recorre las salidas de la sala
  actual, la ruta recorre `sala.entradas`, la antorcha recorre `puerta.sala_destino_ref`), así que
  el índice está a mano. Solo `ir a <id>` parte de un id: `Mapa.obtener_sala(id)` (árbol, O(log V))
  una vez por orden, no por paso.
- «Avistada» es monótona entre pergaminos: una sala explorada nunca deja de estarlo (FR-201), así
  que una sala que es destino de una salida de una sala explorada lo sigue siendo. Basta guardar el
  estado y marcarlo al explorar; no hay que contar cuántas salidas exploradas llegan a cada sala.
- Reservar el `Vector` cuesta O(V) una vez por `Partida`, igual que las marcas de
  `DistanciasLimitadas`.

**Alternativas**:

- `ArbolBusqueda` por id con las salas conocidas: O(log n) por consulta y por cambio. Se mide en N1
  como la alternativa descartada (FR-230). El árbol no se balancea solo e insertar en orden lo
  degenera, así que en N1 se arma con `ArbolBusqueda.desde_ordenados`. Así armado, también puede
  cumplir el cociente ≤ 2 de FR-235: crece como log n (log 2 000 / log 200 ≈ 1,4). Se descarta por el
  costo de cada consulta (varias comparaciones y saltos de nodo contra un acceso al `Vector`) y
  porque las puertas recordadas por (sala, dirección) obligan a escribir los dos lados en cada
  observación (D2).
- Guardar el estado en la propia `Sala`: también O(1), pero mezcla conocimiento con esqueleto y
  obliga a recorrer todas las salas para guardar o resumir. El `Vector` se recorre en orden de id
  sin ordenar (FR-210).
- `dict` o `set`: prohibidos (constitución I).

## D2. Estado recordado de una puerta: en su `EstadoPuerta` compartido

**Decisión**: `EstadoPuerta` gana el atributo `recordada`: `None` (nunca observada), `ABIERTA` o
`CERRADA`. Como los dos lados comparten el `EstadoPuerta`, observar desde un lado actualiza ambos
sin trabajo extra (FR-205). Consultar es O(1) (FR-235).

**Razón**: es la forma más directa de cumplir FR-205 y no exige numerar las puertas. Se copia con
la `Partida` en los puntos de control (la copia de `EstadoPuerta` copia todo menos `observador`) y
se guarda con cada salida en `escribir_sala` (D9).

**Alternativas**:

- `Vector` aparte por número de puerta: exige numerar los `EstadoPuerta` al cargar el mapa. Da lo
  mismo con más código.
- `ArbolBusqueda` con clave (sala, dirección), lado por lado, armado con `desde_ordenados`: O(log n)
  y hay que escribir los dos lados en cada observación. Es la alternativa de N1 (ver D1).

## D3. Toda la modificación pasa por `MapaConocido`, con un `Cambio` solo si el valor cambia

**Decisión**: `MapaConocido` es el único que cambia el conocimiento:

- `explorar(sala)`: si no estaba explorada, la marca; observa sus salidas (`observar`); y marca como
  avistado cada destino desconocido de sus salidas.
- `observar(sala)`: para cada salida de la sala, `recordada ← ABIERTA/CERRADA` según el estado real.
- `avistar(sala)`: desconocida → avistada.

Cada escritura que **cambia** el valor anota un `Cambio.de_operacion("conocimiento", mapa_conocido,
"restaurar_sala" | "restaurar_puerta", (objetivo, valor_anterior))`. Una escritura con el mismo
valor no anota nada. Deshacer llama al mismo `MapaConocido`, que también avisa a su observador
(D7).

**Con qué se anota**: `MapaConocido` recibe y guarda **`partida._anotar`**, el método de la
`Partida` que busca `self.estado.historial` en cada llamada. Nunca guarda
`historial.registrar_cambio` (el método ligado a un historial concreto). Razón: `leer_linea` le pone a
cada punto de control un historial nuevo **por asignación** (`partida.estado.historial =
Historial(limite=None)`, `crypta/Adaptadores/EstadoPartida.py`). Con el método del historial viejo,
`historia` sobre una partida cargada anotaría los cambios de conocimiento en un historial que nadie
deshace: la reconstrucción no desharía el conocimiento y el punto de control quedaría dañado para la
consulta siguiente. Con `partida._anotar`, la anotación siempre llega al historial vigente. En la
copia de la 004 (`deepcopy`), el método ligado se copia ligado a la `Partida` copia, porque `copy`
copia `__self__` con el mismo `memo`, así que se reubica solo. En el bench, sin `Partida`,
`MapaConocido` recibe la función de anotar que corresponda (la de un `RegistroAccion` de prueba, o
una que no hace nada).

Prueba (FR-224, FR-228): guardar con línea de tiempo, cargar, consultar dos veces el mismo instante
→ el mismo resumen, y el conocimiento del punto de control (estados y `recordada`) igual antes y
después de las consultas.

**Razón**:

- Memoria y tiempo de registrar y deshacer: O(cambios reales) (FR-236; constitución VII). Una
  entrada con antorcha revela a lo sumo 4 salas con 4 salidas cada una, así que cuesta O(1) cambios
  sin importar el tamaño del mapa conocido.
- El pergamino ya deshace todo lo de la acción, y la línea de tiempo de la 004 lo trae sin cambios:
  la reconstrucción deshace con el mismo historial, y la copia del punto de control incluye el
  `Vector` y los `recordada` (T057 sin cambios en el sello).
- Pasar por `MapaConocido` incluso al deshacer, en lugar de un `setattr` sobre el `EstadoPuerta`,
  permite avisar a la ruta de «ir a» en los dos sentidos.

**Alternativas**: un `Cambio.de_atributo` directo sobre `EstadoPuerta.recordada` (no avisa a la
ruta al deshacer); copiar el mapa conocido por acción (prohibido por VII; N2 lo mide solo para
mostrar que crece con el mapa).

## D4. Cuándo se observa y se explora (FR-201, FR-204, FR-212 a FR-215)

**Decisión**, dentro de `Partida`:

1. `iniciar`: `explorar(sala inicial)` antes de programar el primer turno. No hay acción abierta, así
   que no se registra: es el estado inicial (FR-201).
2. `_poner_jugador_en(sala)` (lo usan `iniciar` y `mover`): `explorar(sala)`; si la antorcha está
   encendida, `explorar` también cada `puerta.sala_destino_ref` de sus salidas, abiertas o
   cerradas (FR-212, FR-213). Explorar solo usa el esqueleto: no lee el contenido, no activa
   enemigos ni trampas y no pide nada a la red (FR-214).
3. `_correr_hasta_el_jugador`: al sacar el evento `TURNO_JUGADOR`, **antes del `return`**,
   `observar(sala actual)` (FR-204, HU1-4). Queda dentro de la acción que termina, así que el
   pergamino lo revierte junto con ella. Con `tope_tiempo` (reconstrucción de la 004) pasa lo mismo:
   si el turno del jugador cae dentro del tope, se observa; si no, no, igual que en la partida viva.

Una salida sin vuelta que llega a la sala actual no está en `sala.puertas()`, así que no se observa
(FR-205) y no hace avistada a su origen (FR-202).

**Decidido por el grupo**: una salida hacia una sala que no existe (`sala_destino_ref is None`) no
avista nada (no hay índice). La vista sigue mostrando su id, como en P1.

Lo explorado con antorcha sigue explorado al apagarse (FR-215): apagar no toca el conocimiento.

## D5. «ir a»: distancias **desde el destino** con `DistanciasLimitadas`, compartida con la 001

**Decisión**: `RutaConocida` (Modelo) usa una `DistanciasLimitadas` con origen en el **destino** y
`entradas(y)` = las entradas `(puerta, origen)` de y con `origen` explorado y
`puerta.estado.recordada == ABIERTA` (y está explorada porque solo se llega a ella desde el destino,
que lo está). Así `distancia(x)` es el costo mínimo de x al destino por la ruta conocida (FR-217).

Paso desde la sala actual u: `extender_hasta(∞, objetivo=u.indice)`. Si u no queda asentada, no
hay ruta conocida. Si no, entre las salidas de u con `recordada == ABIERTA`, destino v explorado y
`costo + dist(v) == dist(u)`, la de menor id de v; con dos salidas a la misma v, la primera en N, S,
E, O. Es la regla de `Perseguidor._decidir_con` (FR-017), con «abierta» leído del mapa conocido.
Toda candidata tiene `dist(v) < dist(u)` y ya está asentada.

**Por qué desde el destino**: después de un paso, el destino no cambia, así que las distancias
asentadas siguen valiendo y el paso siguiente es O(grado de la sala), sin buscar. Una búsqueda hacia
adelante (`RutaPorCazador`) tiene origen en la sala actual, que cambia en cada paso, y habría que
empezar de nuevo siempre.

**Compartir o separar con el cazador** (P2 §5.3, último punto): se **comparte la estructura**
(`DistanciasLimitadas`, genérica sobre nodos y `entradas`) y se **separan las reglas**:
`Perseguidor` lee el estado real de las puertas y busca desde la sala del jugador; `RutaConocida`
lee el mapa conocido y busca desde el destino. Son instancias distintas: la del cazador se reinicia
cada vez que el jugador se mueve, y compartirla destruiría la de «ir a» en cada paso.

**Alternativas**:

- Recalcular desde cero en cada paso (`reiniciar` siempre): según la medición del grupo, media de
  6,4 ms y p95 de 11 ms en otra máquina con 2 000 salas. En este equipo (1,7 a 3 veces más lento,
  plan de la 004) serían de 11 a 33 ms. No cumple FR-234. Se mide en N3.
- `RutaPorCazador` hacia adelante en cada paso: mismo costo, sin reutilización posible. Se usa
  como **verificador independiente** (SC-203, N4).
- Árbol de rutas completo precalculado al iniciar el viaje y seguido sin mirar: no cumple FR-218 si
  el conocimiento cambia.

## D6. Reutilización entre pasos e invalidación selectiva

**Decisión**: `RutaConocida` es una por `Partida` (se crea la primera vez, como el `Perseguidor`).
Guarda la búsqueda vigente y su destino. En cada paso:

- si el destino es otro o la búsqueda no está vigente: `reiniciar(destino)`;
- si no: se reutiliza y se extiende si hace falta.

`MapaConocido.observador` es la `RutaConocida`. Recibe:

- `puerta_recordada(estado)` cuando `recordada` cambia de valor (al observar o al deshacer):
  invalida si alguno de los `extremos` está asentado;
- `sala_explorada(sala)` cuando una sala pasa a explorada o deja de estarlo (al deshacer): invalida
  si la sala o el otro extremo de alguna de sus salidas o entradas está asentado.

Además, `Partida.usar_pergamino` llama a `invalidar()`, como hace con el `Perseguidor`.

**Demostración** (la misma de la 001, research D4, sobre el grafo conocido): la búsqueda solo
relaja la arista x→y al asentar y, y solo asienta salas exploradas. Si ningún extremo de una arista
que aparece o desaparece está asentado, nunca se relajó, y por la monotonía de Dijkstra (costos
≥ 1) toda sala no asentada tiene distancia ≥ la de cualquier asentada. Una arista nueva x→y con y
no asentada da a x un costo ≥ dist(y) + 1 > ρ ≥ cualquier distancia asentada; quitar una arista no
relajada no cambia nada asentado. Explorar una sala r agrega a r y sus aristas con salas
exploradas: r no estaba asentada (no era nodo), así que solo importa si el otro extremo lo está. Por
lo tanto, las distancias asentadas y el paso elegido son los mismos que daría un cálculo desde cero
(constitución II, FR-218). SC-203 lo comprueba en cada paso, y N4 en el bench.

**Cuánto se ahorra** (estimación que N3 debe confirmar): con el mapa conocido completo y sin
cambios, solo el primer paso busca; los demás cuestan O(grado). Una ruta típica en la cuadrícula de
2 000 salas (50 × 40) entre salas tomadas al azar tiene unos 30 pasos o más, así que los pasos que
buscan son ≈ 3 % del total.

**Riesgo de FR-234 (aceptado por el grupo)**: el p95 se toma sobre **todos** los pasos, incluido
el primero. Si los pasos que buscan pasan del 5 % de los pasos, el p95 los ve. Con 2 000 salas, en
este equipo el primer paso puede tardar de 11 a 33 ms. N3 reporta la cantidad de pasos por viaje, la
fracción de pasos que buscaron y el primer paso aparte. El grupo acepta el riesgo: si el p95 no
cumple, primero se prueba la optimización de D12 y, si aun así no cumple, va a Límites de
`DECISIONES.md` §5.3 con los números de N3 (FR-234).

**Alternativas**: invalidación total (cualquier cambio de conocimiento invalida): más simple y
correcta; se mide en N3 con conocimiento que cambia. Recalcular siempre: N3.

## D7. Lo de «ir a» no es estado del juego

**Decisión**: la `RutaConocida`, su búsqueda y el `Viaje` no se guardan, no se revierten y no van a
los puntos de control. `Partida.__deepcopy__` agrega `_ruta_conocida` a `_NO_SE_COPIAN` y la copia
la deja en `None`; `MapaConocido.__deepcopy__` deja `observador = None`. Una partida cargada o una
copia crean la suya si hace falta. El viaje vive dentro de una orden `ir a`; el pergamino lo corta
(FR-225), porque cada paso es una acción y la orden ya terminó.

## D8. La orden `ir a`: dónde vive cada parte

**Decisión**:

- **Modelo** `Viaje` (`crypta/Modelo/Viaje.py`): destino, pasos hechos y motivo de parada. Sabe
  validar (FR-216), pedir el siguiente paso a la `RutaConocida` y evaluar las paradas después de un
  paso (FR-221). No sabe de red ni de log.
- **Controlador** `Controlador._ejecutar_comando_jugador(comando)`: método nuevo que separa lo que
  hoy hace `procesar_comando` con un comando escrito a mano, en el mismo orden: `_asegurar_linea`;
  `ejecutar_comando(partida, comando, garantizar_sala=gestor_contenido.garantizar_sala)`; si se
  ejecutó, `linea.registrar`, `registro.anotar(comando)`, `_actualizar_fichas_en_uso` y, si la
  partida no terminó, `precargar_async(sala del jugador)`. Lo usan **los dos caminos**: el comando
  escrito a mano y cada paso de `ir a`. Así un paso hace exactamente lo mismo que un `mover` escrito
  a mano, incluidas las solicitudes a la red (principio V).
- **Controlador** `Comandos.ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar_sala=None,
  anotar_comentario=None)`: el bucle. Recibe `ejecutar_paso(comando)` como función por paso (en el
  `Controlador`, `_ejecutar_comando_jugador`; en las pruebas y en las partidas sintéticas, una función
  equivalente con `ejecutar_y_registrar`). Por cada paso: pide la dirección, llama a
  `garantizar_sala` del destino, escribe el comentario antes del primer paso, llama a
  `ejecutar_paso("mover <d>")` y evalúa las paradas. No usa la vista.
- **Controlador** `Controlador.procesar_comando`: reconoce `ir a`, llama a `ejecutar_ir_a` con
  `_ejecutar_comando_jugador` y `registro.anotar_comentario`, y muestra el motivo de parada.

`garantizar_sala` se llama dos veces por paso (en `ejecutar_ir_a` y en `_cargar_destino` dentro de
`ejecutar_comando`), pero la segunda encuentra la sala cargada y no pide nada: las solicitudes son
las de un `mover` escrito a mano. Un error que salga de `ejecutar_paso` sale de `ejecutar_ir_a` y lo
atiende `procesar_comando` como a cualquier comando; los pasos ya hechos quedan hechos y anotados.

Prueba (principio V): en la misma partida, un viaje de 3 pasos y los 3 `mover` escritos a mano dan
la misma secuencia de llamadas a `garantizar_sala` y `precargar_async` (registrada por un gestor de
contenido espía) y las mismas solicitudes por operación según `FuenteContadora`. No se compara el
orden de las solicitudes: `FuenteContadora` no lo guarda y la precarga corre en otro hilo.

**Paradas** (FR-221), evaluadas por `Viaje` después de cada paso:

| Motivo | Cómo se detecta |
|---|---|
| Llegada | `sala actual == destino` |
| Sala con enemigos | `Partida.enemigos_al_entrar > 0`: lo fija `mover` en el instante de entrar, antes de activar a los dormidos, con los enemigos vivos de la sala (activos o dormidos). Así un enemigo que entra **después** no detiene el viaje (HU3-16) |
| Daño | la vida del jugador bajó durante el paso. Durante un viaje nada cura al jugador (curar es una acción suya), así que bajar la vida es exactamente haber recibido daño (ataque, trampa o veneno) |
| Fin de la partida | `partida.terminada` |
| Sin ruta conocida | antes del paso, la ruta no encuentra camino: no se mueve ni consume tiempo |
| Paso imposible | **solo** un `RuntimeError` (incluye `PresupuestoAgotado`) de `garantizar_sala`, que `ejecutar_ir_a` llama **antes** de `ejecutar_paso`: el paso no se hace ni consume tiempo. Un error que salga de dentro del `mover` no se convierte en parada: se propaga como con cualquier comando (es un defecto, no una condición del viaje) |

`enemigos_al_entrar` es un entero transitorio de la `Partida` (no es estado del juego, no se guarda,
no se revierte). La alternativa, mirar el contenido de la sala destino antes del paso, haría que «ir
a» leyera algo que no viene del mapa conocido (FR-209).

**Rechazos** (FR-216) sin consumir tiempo ni anotar nada: id no explorado o inexistente (mismo
mensaje), la sala actual, sin ruta conocida. El texto mal formado es `ComandoInvalido`.

## D9. Guardado: formato 4 con el conocimiento

**Decisión**: `FORMATO_GUARDADO = 4` y `FORMATO_JSON = 4`. Se agregan, con los mismos métodos del
escritor abstracto:

- en cada salida de `escribir_sala`: `recordada` (entero: 0 nunca observada, 1 abierta,
  2 cerrada). Los dos lados escriben lo mismo;
- en `escribir_general`: el grupo `conocimiento` con la lista de las salas no desconocidas
  (`sala`, `estado`) en orden de índice.

Al leer, `Puerta.compartir_estado_con` exige que los dos lados digan lo mismo (si no,
`DatosInvalidos` → `ErrorGuardado`), y `MapaConocido.restaurar` fija los estados y llama a
`MapaConocido.validar()`, que comprueba en O(V + E) las reglas de FR-201 a FR-204 (sala inicial
explorada, avistadas = destinos no explorados de salidas exploradas, salidas de salas exploradas
observadas). `validar()` es un método aparte porque también lo usa la prueba de equivalencia
(T041) después de cada comando. Como la 004 guarda sus puntos de control con `escribir_general` y `escribir_sala`, los
puntos llevan el conocimiento sin código nuevo.

Los formatos 1, 2 y 3 se rechazan con el mensaje que ya existe (FR-227, igual que FR-419). Nunca se
migra. Las firmas de `guardar_partida` y `cargar_partida` no cambian.

**Alternativas**: estado de la sala dentro de su registro (exige pasar el `MapaConocido` a
`escribir_sala` y cambiar sus llamadas); migrar el formato 3 inventando un conocimiento (prohibido:
se carga en silencio algo que no existía).

## D10. `partida.log`: comentario antes de los `mover`

**Decisión**: `RegistroPartida.anotar_comentario(texto)` escribe `# <texto>`. `ejecutar_ir_a`
escribe `# ir a <id>` justo antes del **primer** `mover` del viaje; si el viaje no da ningún paso,
no se escribe nada. `leer_registro` ignora las líneas que empiezan con `#` después de `---`. El
formato del registro sigue siendo 1: los logs de P1 y de la 001 no tienen comentarios y se leen
igual (FR-223, SC-206).

**Alternativas**: subir el formato de registro a 2 (obligaría a aceptar 1 y 2 para no romper los
logs de P1, sin ganar nada); anotar la orden aunque no dé pasos (un comentario sin movimientos solo
confunde al depurar).

## D11. Bitácora, vista y comando `mapa`

**Decisión**:

- Bitácora (FR-208): `_cerrar_puerta` avisa solo si la puerta es una **salida de la sala del
  jugador**: alguna salida de `sala_actual()` comparte su `EstadoPuerta` (O(4)). No basta con que la
  sala del jugador sea uno de sus `extremos`: una salida sin vuelta que llega a la sala del jugador
  tiene esa sala como extremo, pero el jugador no la observa (FR-205), así que no avisa; `_regenerar`, solo si el enemigo está en la sala del jugador; `_rearmar_trampa`, solo
  si la trampa está en la sala del jugador (se busca entre las trampas de esa sala, O(trampas de la
  sala)). Los demás avisos no cambian.
- Vista (FR-207): `mostrar_estado` lee el estado de cada salida de la sala actual de
  `recordada`. El texto no cambia («N: sala 3 (Cerrada, necesita itm_llave, costo 100)»), así que
  las pruebas de la 001 siguen valiendo. **Decidido por el grupo**: la llave de una puerta cerrada de
  la sala actual se sigue mostrando, porque es parte de la sala del jugador (FR-207).
- `mapa` (FR-210, FR-211): texto puro en `crypta/Vista/FormatoMapa.py` (contracts/vista.md), que se
  arma recorriendo el `Vector` en orden de índice (orden de id, sin ordenar). El `Controlador` lo
  atiende antes de traducir, como `historia`: no es acción, no consume tiempo, no va al log ni a la
  red. `mapa` con argumentos sigue el camino de los comandos desconocidos, como en P1.
- Resumen de la 004 (T057, FR-228): `Resumen.mapa_conocido` pasa a ser un `MapaResumido` (salas
  exploradas con sus salidas y salas avistadas), y `FormatoResumen` imprime «Mapa conocido: E
  exploradas, A avistadas» seguido de las mismas líneas de `FormatoMapa`.

## D12. Entradas conocidas sin generadores lentos

**Decisión provisional**: el `entradas(y)` de `RutaConocida` recorre `sala.entradas` y filtra con
dos consultas O(1) (D1, D2). Si N3 muestra que el costo de la primera búsqueda domina el p95, se
mide una variante que recorre el `Vector` de entradas sin generador (devuelve un `Vector` de pares
reutilizable). Es una optimización interna; no cambia el resultado (N4).

## D13. Bench: criptas, viajes y alternativas

**Decisión** (detalle en [contracts/bench.md](contracts/bench.md)):

- Criptas: la sintética de la 001 (`CriptaSintetica`, 2 000 salas, costos de 1 a 500, puertas), y
  una del tamaño de la de referencia: la **copia local más grande** si existe (hoy cripta-06, 300
  salas; solo hace falta el esqueleto; el id no se escribe en el código, principio IV), o una
  sintética de 300 salas si no hay copia. La carpeta de copias es un **parámetro** (por omisión,
  la de la aplicación); las pruebas pasan una carpeta vacía y usan la sintética de 300 salas, así
  nunca leen `cache/`.
- `MapaConocido` recibe la función de anotar que corresponda (D3): en N2, la de un `RegistroAccion`
  propio de cada entrada; en N1 y N3, una que no hace nada.
- Mapa conocido completo: todas las salas exploradas y cada puerta recordada con su estado real.
- Viajes: pares (origen, destino) tomados con `random.Random(semilla)` entre salas con ruta
  conocida, hasta tener al menos 20 viajes y 200 pasos (FR-234).
- Variantes: reutilizar con invalidación selectiva (la elegida), invalidación total y recalcular en
  cada paso; con conocimiento estable y con conocimiento desactualizado (una fracción de puertas
  recordadas abiertas que en realidad están cerradas, que el viaje descubre al observar).

## D14. Puntos que decidió el grupo

Estaban abiertos en la primera versión de este plan y el grupo los decidió en `/speckit-plan`:

1. **Llave en la vista** (D11): se sigue mostrando «necesita <llave>» en las puertas cerradas de la
   sala actual. Es parte de la sala del jugador (FR-207).
2. **Riesgo de FR-234** (D6): se acepta. Si el p95 o el primer paso no cumplen 5 ms en este equipo,
   van a Límites de `DECISIONES.md` §5.3 con los números de N3.
3. **Salidas hacia salas que no existen** (D4): no avistan nada. La vista sigue mostrando su id, como
   en P1.
