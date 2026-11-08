# Especificación de capacidad: Terreno y cazador

**Capacidad**: 001 — `001-terreno-cazador`

**Creada**: 2026-11-07

**Estado**: Borrador

**Fuentes**: P2 §3.1, §3.2, §4.1, §5.1, §5.2, §6.1, §6.3, §7.3, Apéndice A y Apéndice B («Terreno y
cazador»). Reglas heredadas de P1 (§2.3, §2.4, §2.5, §2.8, §2.11, §4.10, §4.11, §5.2).

**Entrada**: descripción del grupo en `/speckit-specify` (registrada en `PROMPTS_LLM.md`).

## Contexto: por qué existe esta capacidad

En la primera parte moverse siempre costaba 100 y ningún enemigo buscaba rutas: el rastreador solo
miraba sus salas vecinas. Con esta capacidad el terreno hace que unos caminos tarden más que otros y
aparece un enemigo nuevo, el cazador, que persigue al jugador por el camino más barato. El jugador
tiene que pensar por dónde se mueve: un atajo caro puede dar tiempo al cazador, y un rodeo barato
puede ser más rápido que la ruta con menos salas.

### Glosario

- **Costo de una salida**: entero que indica cuánto cuesta atravesarla, en las mismas unidades que
  el costo base de las acciones de P1 §2.3.
- **Salida abierta**: salida sin puerta, o cuya puerta está abierta en el instante considerado.
- **Ruta**: secuencia de salidas abiertas que lleva de una sala a otra. Su costo es la suma de los
  costos de sus salidas.
- **dist(x, y)**: costo mínimo entre todas las rutas de la sala x a la sala y en el instante
  considerado; no existe si no hay ruta.
- **Rango**: entero del catálogo, en unidades de costo, que limita hasta dónde persigue un cazador.
- **Cálculo desde cero**: la decisión que se obtendría en ese instante usando solo el esqueleto, los
  costos y el estado actual de las puertas, sin ningún resultado de turnos anteriores.

## Aclaraciones

### Sesión 2026-11-07

- P: Si un costo del esqueleto es inválido (menor que 1, no entero) o una misma salida declara
  costos distintos en cada sentido, ¿qué hace el programa? → R: Rechaza la cripta con un mensaje
  que indica la salida y el problema, y no inicia la partida. Excepción: si solo un lado de la
  salida declara costo, ese costo vale en ambos sentidos y no cuenta como asimétrico.
- P: Si la ficha de un cazador en el catálogo no trae rango, ¿qué hace el programa? → R: Rechaza el
  catálogo con un mensaje que indica la ficha y no inicia la partida; lo mismo si el rango es
  negativo o no es entero. El rango 0 es válido. Si la ficha inválida llega con la partida ya
  empezada (por ejemplo, por la precarga), la partida se detiene de forma controlada con ese mismo
  mensaje y `partida.log` queda guardado.
- P: Mientras el profesor no publique la cripta de referencia, ¿con cuántos cazadores activos y qué
  tamaño de cripta mide `--bench` el límite de 20 ms? → R: 50 cazadores activos en una cripta
  sintética de 2 000 salas, y además la cripta oficial cuando se publique. Los cazadores se reparten
  a distintas distancias del jugador, todas dentro de su rango (ninguno empieza en la sala del
  jugador), para que de verdad calculen rutas. Lo que debe quedar por debajo de 20 ms es el p95 de al
  menos 60 acciones del jugador, como en la medición de la primera parte.
- P: Para medir que un cazador de rango pequeño no depende del tamaño total de la cripta, ¿qué
  tamaños usa `--bench`? → R: Una región de unas 100 salas dentro del rango del cazador, en criptas
  de 2 000 salas y de 20 000 salas.
- P: ¿Con qué criterio verifica `--bench` que el trabajo por ciclo crece a lo sumo linealmente con la
  cantidad de cazadores activos? → R: Se mide con 10, 25, 50 y 100 cazadores; el tiempo por cazador
  (ciclo ÷ cantidad) con 100 no debe pasar de 2 veces el de 10.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 — Terreno con costo (Prioridad 1)

Como jugador, al moverme por una salida tardo según el costo de esa salida, y veo el costo de cada
salida de mi sala actual, para poder elegir por dónde moverme.

**Por qué esta prioridad**: el costo de las salidas es la base de todo lo demás. Sin él no hay
«ruta más barata» y el cazador no tiene sentido. Por sí solo ya cambia el juego, porque cambia
cuánto tiempo tienen los enemigos para actuar mientras el jugador se mueve.

**Prueba independiente**: con una cripta sintética con salidas de distintos costos y sin cazadores,
se mueve al jugador y a enemigos errantes y rastreadores, y se comprueba el instante de su siguiente
acción y lo que muestra la vista.

**Escenarios de aceptación**:

1. **Dado** un jugador de velocidad 100 en el instante 0 y una salida de costo 250, **cuando** se
   mueve por ella, **entonces** aparece en la sala destino y su siguiente acción queda en el
   instante 250. *(FR-001, FR-003)*
2. **Dada** una salida sin campo costo, **cuando** un actor de velocidad 100 la atraviesa,
   **entonces** su siguiente acción queda 100 unidades después, como en P1. *(FR-001, FR-003)*
3. **Dada** una salida de costo 250 entre las salas 3 y 7, **cuando** un actor la atraviesa de 3 a
   7 y otro de 7 a 3, **entonces** ambos movimientos cuestan 250. *(FR-002, FR-003)*
4. **Dado** un actor de velocidad 150, **cuando** atraviesa una salida de costo 1, **entonces** su
   intervalo es 1 (no 0): max(1, 1 * 100 // 150) = 1. *(FR-003, FR-004)* — Apéndice B.
5. **Dado** un actor de velocidad 100 que en el instante 0 atraviesa una salida de costo 300 y
   queda programado para el instante 300, **cuando** en el instante 100 su velocidad pasa a 200,
   **entonces** su siguiente acción se reprograma al instante 100 + max(1, (300 − 100) * 100 // 200)
   = 200, con un número de secuencia nuevo. *(FR-007)* — Apéndice B.
6. **Dado** un errante y un rastreador en salas con salidas de distintos costos, **cuando** se
   mueven, **entonces** eligen su destino exactamente como en P1 (mismas opciones y mismas llamadas
   al generador aleatorio) y solo cambia el instante de su siguiente acción. *(FR-004, FR-006)*
7. **Dado** un actor que ataca, espera, usa, equipa, recoge, suelta o abre una puerta, **cuando**
   ejecuta la acción, **entonces** su costo es el de P1 §2.3, sin importar los costos de las salidas
   de su sala. *(FR-005)*
8. **Dada** una cripta sin ningún campo costo, **cuando** se juega con la misma semilla y los mismos
   comandos que en la primera parte, **entonces** la partida es idéntica: mismos instantes, mismos
   eventos, mismo resultado y mismo `partida.log`. *(FR-008)*
9. **Dado** el jugador en una sala con varias salidas, abiertas y cerradas, **cuando** se muestra la
   vista, **entonces** aparece el costo de cada salida de la sala actual. *(FR-009)*
10. **Dadas** dos criptas sintéticas idénticas salvo los costos de sus salidas, **cuando** se juegan
    con el mismo programa, la misma semilla y los mismos comandos, **entonces** los instantes de las
    acciones difieren según los costos de cada cripta: ningún costo está escrito en el código.
    *(FR-024)*
11. **Dada** una copia local del esqueleto guardada por la primera parte con otra versión de cripta,
    **cuando** se inicia la cripta de la segunda parte, **entonces** la validación de versión
    invalida esa copia sin borrar archivos a mano, se descarga el esqueleto nuevo con sus costos y se
    persiste junto con su versión. *(FR-025)*
12. **Dado** un esqueleto con una salida de costo 0, otra de costo 2,5, u otra cuyos dos lados
    declaran costos 200 y 300, **cuando** se carga la cripta, **entonces** se rechaza con un mensaje
    que indica la salida y el problema, y no se inicia la partida. *(FR-010)*
13. **Dada** una salida entre las salas 3 y 7 en la que solo el lado de la sala 3 declara costo 250,
    **cuando** un actor la atraviesa de 7 a 3, **entonces** el movimiento cuesta 250 y la cripta no
    se rechaza. *(FR-001, FR-010)*

---

### Historia de usuario 2 — El cazador persigue por la ruta más barata (Prioridad 2)

Como jugador, me enfrento a un enemigo que viene hacia mí por la ruta más barata si estoy dentro de
su rango, y que espera si no puede llegar.

**Por qué esta prioridad**: es el enemigo nuevo y la razón por la que el terreno importa. Depende de
la historia 1.

**Prueba independiente**: con criptas sintéticas pequeñas, armadas para cada caso, se coloca un
cazador activo y al jugador en salas conocidas y se comprueba la acción del cazador en su turno,
su sala resultante y el instante de su siguiente acción.

**Escenarios de aceptación**:

1. **Dado** un cazador activo en la misma sala que el jugador, **cuando** llega su turno,
   **entonces** ataca (P1 §2.6) con costo 100 y no se mueve. *(FR-013)*
2. **Dado** un cazador sin ninguna ruta de salidas abiertas hasta la sala del jugador, **cuando**
   llega su turno, **entonces** espera con costo 100. *(FR-014, FR-015)* — Apéndice B.
3. **Dado** un cazador de rango 600 cuya ruta más barata hasta el jugador cuesta 700, **cuando**
   llega su turno, **entonces** espera con costo 100. *(FR-015)* — Apéndice B.
4. **Dado** un cazador de rango 600 cuya ruta más barata hasta el jugador cuesta exactamente 600,
   **cuando** llega su turno, **entonces** avanza un paso (solo espera si d > rango). *(FR-015,
   FR-016)*
5. **Dado** un cazador de rango 1000 en la sala 1 y el jugador en la sala 2, con la salida 1–2 de
   costo 500 y la ruta 1–3–4–2 con salidas de costo 100 cada una, **cuando** llega su turno, **entonces** se mueve
   a la sala 3 (ruta de costo 300, aunque tenga más salas) y esa acción cuesta 100. *(FR-014,
   FR-016)* — Apéndice B.
6. **Dado** un cazador de rango 1000 en la sala 1 con vecinas 5 y 3, ambas al inicio de rutas de
   costo mínimo d ≤ 1000 hasta el jugador, **cuando** llega su turno, **entonces** se mueve a la sala 3. *(FR-017)* — Apéndice B.
7. **Dado** un cazador de rango 1000 y muchas rutas de igual costo mínimo d ≤ 1000 hasta el jugador
   que se cruzan entre sí, **cuando** llega el turno del cazador, **entonces** su primer paso es hacia la vecina de menor id entre las que
   cumplen costo(u, v) + dist(v, jugador) = d. *(FR-017)*
8. **Dado** un cazador de rango 1000 en la sala 1 y el jugador en la sala 2, con la salida 1–2 de
   costo 100 cerrada y la ruta 1–3–2 de costo 400 abierta, **cuando** llega su turno, **entonces** se mueve a
   la sala 3; nunca usa ni abre la puerta cerrada. *(FR-014, FR-018)*
9. **Dado** un cazador de rango 1000 cuya ruta más barata hasta el jugador (de costo d ≤ 1000) pasa
   por salas cuyo contenido todavía no se ha descargado, **cuando**
   llega su turno, **entonces** decide igual que si todo estuviera descargado, y esa decisión no
   genera solicitudes al servicio. *(FR-018, FR-027)*
10. **Dado** un cazador dormido en una sala que el jugador nunca visitó, **cuando** el jugador entra
    a esa sala, **entonces** se activa según P1 §2.4 (primera acción con base de costo 100 desde el
    reloj actual). *(FR-012)*
11. **Dado** un cazador de velocidad 120 y rango 1000 que se mueve por una salida de costo 250 (con
    d ≤ 1000), **cuando** termina
    la acción, **entonces** su siguiente acción queda max(1, 250 * 100 // 120) = 208 unidades
    después. *(FR-003, FR-016)*
12. **Dado** el jugador en una sala con un cazador y otros enemigos, **cuando** se muestra la vista,
    **entonces** el cazador se distingue a simple vista de los demás enemigos. *(FR-022)*
13. **Dada** una misma cripta con el jugador a costo 700 de un cazador, **cuando** el catálogo trae
    para ese cazador rango 600, **entonces** espera con costo 100; y **cuando** el catálogo trae para
    él rango 800, **entonces** avanza un paso. El rango aplicado es siempre el de su ficha del
    catálogo. *(FR-011)*
14. **Dado** un catálogo en el que la ficha de un cazador no trae rango, o trae un rango negativo o
    no entero, **cuando** se carga antes de la partida, **entonces** se rechaza con un mensaje que
    indica la ficha y no se inicia la partida; y **cuando** esa ficha llega con la partida ya empezada
    (por ejemplo, por la precarga), **entonces** la partida se detiene de forma controlada con el
    mismo mensaje y `partida.log` queda guardado. *(FR-011)*
15. **Dado** un cazador de rango 0 que no comparte sala con el jugador, **cuando** llega su turno,
    **entonces** espera con costo 100; y si comparte sala, ataca. *(FR-011, FR-013, FR-015)*

---

### Historia de usuario 3 — La decisión del cazador siempre es correcta (Prioridad 3)

Como jugador, aunque se abran o cierren puertas, yo me mueva, otros actores mueran o cambien de sala,
o cambien velocidades, el cazador decide en cada turno lo mismo que decidiría calculando desde cero.

**Por qué esta prioridad**: el grupo puede reutilizar cálculos para cumplir el rendimiento; esta
historia garantiza que eso nunca cambie el juego. Depende de la historia 2.

**Prueba independiente**: se juega una partida sintética con muchos cambios de puertas, movimientos
y cambios de velocidad, y en cada turno de cada cazador se compara su decisión con la de un cálculo
desde cero en ese instante; deben coincidir siempre.

**Escenarios de aceptación**:

1. **Dado** un cazador de rango 1000 cuya ruta más barata cruza una puerta, **cuando** esa puerta se cierra entre
   dos de sus turnos (por cierre automático o por cualquier evento), **entonces** en el turno
   siguiente decide lo mismo que un cálculo desde cero: toma la siguiente ruta más barata, o espera
   si ya no hay ruta o cuesta más que su rango. *(FR-019)* — Apéndice B.
2. **Dado** un cazador de rango 1000 que esperaba porque no tenía ruta, **cuando** se abre una
   puerta que crea una ruta de costo no mayor que 1000, **entonces** en su siguiente turno avanza por ella.
   *(FR-019)*
3. **Dado** un cazador de rango 1000 que perseguía al jugador, **cuando** el jugador se mueve entre
   dos turnos del cazador a una sala a costo no mayor que 1000, **entonces** el cazador decide hacia la nueva sala del jugador, como un cálculo desde
   cero. *(FR-014, FR-019)*
4. **Dados** varios cazadores de rango 1000 con turno en el mismo instante, **cuando** el primero se mueve,
   **entonces** cada uno decide con el estado vigente en su propio turno, en el orden de la agenda de
   P1 §2.3. *(FR-019, FR-023)*
5. **Dado** un cazador de rango 1000 y otros actores que mueren, cambian de sala o cambian de velocidad entre sus
   turnos, **cuando** llega su turno, **entonces** su decisión coincide con la de un cálculo desde
   cero. *(FR-019)*
6. **Dado** que el jugador usa un pergamino de retroceso después de que un cazador se movió,
   **cuando** se revierte, **entonces** el cazador vuelve a su sala, vida y próxima acción anteriores,
   y sus decisiones siguientes coinciden con un cálculo desde cero. *(FR-019, FR-020)*
7. **Dada** una partida con cazadores, **cuando** se reproduce con `--replay` con la misma semilla y
   los mismos comandos, **entonces** cada cazador toma las mismas decisiones en los mismos instantes.
   *(FR-021)*
8. **Dada** una partida con cazadores guardada en disco, **cuando** se carga, **entonces** los costos
   de las salidas y el estado de los cazadores son los mismos y la partida continúa igual que sin
   guardar. *(FR-026)*

---

### Historia de usuario 4 — Medición con `--bench` (Prioridad 4)

Como grupo, quiero medir con `--bench` cuánto cuestan las rutas del cazador y cuánto se ahorra al
reutilizar cálculos, para defender nuestras decisiones con datos.

**Por qué esta prioridad**: no cambia el juego, pero es requisito de evaluación (P2 §6.3) y
respalda los requisitos de rendimiento.

**Prueba independiente**: se ejecuta `--bench` dos veces con la misma semilla y se comprueba que
genera las mismas criptas, que incluye todos los escenarios pedidos y que no instancia la vista.

**Escenarios de aceptación**:

1. **Dada** una semilla, **cuando** se ejecuta `--bench` dos veces, **entonces** las criptas
   sintéticas generadas (salas, salidas, costos, puertas, cazadores) son idénticas. *(FR-028)*
2. **Cuando** se ejecuta `--bench`, **entonces** reporta tiempos con un cazador y con muchos
   cazadores. *(FR-029)*
3. **Cuando** se ejecuta `--bench`, **entonces** reporta tiempos con rango pequeño y con rango grande,
   y con criptas de distinto tamaño. *(FR-030)*
4. **Cuando** se ejecuta `--bench`, **entonces** compara un cálculo compartido por todos los
   cazadores con un cálculo por cazador. *(FR-031)*
5. **Cuando** se ejecuta `--bench`, **entonces** compara reutilizar cálculos con recalcular siempre,
   en un escenario con puertas que casi nunca cambian y en otro con puertas que cambian seguido.
   *(FR-032)*
6. **Cuando** se ejecuta `--bench` con reutilización, **entonces** verifica que todas las decisiones
   coinciden con las de recalcular siempre y reporta cualquier diferencia como error. *(FR-033)*
7. **Cuando** se ejecuta `--bench`, **entonces** no instancia la vista ni hace solicitudes de red.
   *(FR-034)*
8. **Dada** una cripta sintética de 2 000 salas con 50 cazadores activos repartidos a distintas
   distancias del jugador, todas dentro de su rango, **cuando** `--bench` mide el ciclo de eventos
   entre dos decisiones del jugador durante al menos 60 acciones del jugador, **entonces** el p95 de
   esos ciclos es menor que 20 ms. *(FR-035)*
9. **Dado** un cazador de rango pequeño, con unas 100 salas dentro de su rango, **cuando**
   `--bench` pasa de una cripta de 2 000 salas a una de 20 000 sin cambiar esa región, **entonces**
   el tiempo medio por decisión no llega a duplicarse. *(FR-030, FR-036)*
10. **Cuando** `--bench` mide el ciclo con 10, 25, 50 y 100 cazadores activos, **entonces** el
    tiempo por cazador (ciclo ÷ cantidad) con 100 no pasa de 2 veces el de 10. *(FR-037)*

---

### Casos borde

- **Cazador en la misma sala que el jugador**: ataca; no calcula ruta (FR-013).
- **d igual al rango**: avanza; solo espera si d > rango (FR-015).
- **La única ruta barata cruza una puerta cerrada**: no se usa; se toma la siguiente ruta abierta o
  se espera (FR-014, FR-018).
- **La puerta se cierra en el mismo instante que el turno del cazador**: decide con el estado que
  resulta de los eventos ya ejecutados según el orden de la agenda (FR-019, FR-023).
- **Cazador activo que entra a una sala nunca visitada por el jugador**: sigue activo (P1 §2.4) y su
  decisión no requiere el contenido de esa sala (FR-018).
- **Velocidad alta y costo bajo**: el intervalo nunca baja de 1 (FR-003).
- **Cambio de velocidad mientras se atraviesa una salida costosa**: el restante se reescala con la
  fórmula de P1 §2.3 sobre el intervalo derivado del costo (FR-007).
- **Muchas rutas de igual costo**: el desempate por menor id de vecina se cumple siempre (FR-017).
- **Cazador derrotado**: deja de actuar y deja de contar para el trabajo por ciclo (P1, FR-019).
- **Costo inválido o asimétrico en los datos**: se rechaza la cripta con un mensaje y no se inicia
  la partida (FR-010).
- **Solo un lado de la salida declara costo**: ese costo vale en ambos sentidos; no es asimetría
  (FR-001, FR-010). Un lado con costo null cuenta como no declarado: vale el costo del otro lado, o
  100 si tampoco lo declara.
- **Cazador sin rango, o con rango negativo o no entero, en el catálogo**: se rechaza el catálogo y
  no se inicia la partida; si llega con la partida empezada, la partida se detiene de forma
  controlada con el mismo mensaje y `partida.log` queda guardado (FR-011).
- **Cazador de rango 0**: es válido; solo ataca si comparte sala con el jugador, y si no, espera
  (FR-011, FR-013, FR-015).

## Requisitos *(obligatorio)*

Los identificadores son estables y no se renumeran (constitución, principio IX).

### Requisitos funcionales — Terreno

- **FR-001**: Cada salida del esqueleto PUEDE declarar un campo costo, entero mayor o igual que 1. Si
  ninguno de los dos lados de la salida lo declara, su costo DEBE ser 100. Si solo uno de los dos
  lados lo declara, ese costo DEBE valer en ambos sentidos. Un campo costo con valor null cuenta como
  no declarado.
- **FR-002**: El costo de una salida DEBE ser el mismo en ambos sentidos.
- **FR-003**: Moverse por una salida DEBE ser una acción cuyo costo base es el costo de esa salida,
  en lugar del 100 fijo de P1. El intervalo DEBE calcularse como
  `max(1, costo_salida * 100 // velocidad)`.
- **FR-004**: FR-003 DEBE aplicarse a todos los actores que se mueven: jugador, errantes,
  rastreadores y cazadores.
- **FR-005**: Atacar, esperar, usar, equipar, recoger, soltar y abrir una puerta DEBEN conservar el
  costo de P1 §2.3.
- **FR-006**: Errantes y rastreadores DEBEN conservar su comportamiento de P1 §2.8 y §2.9: el costo
  de las salidas no cambia qué salidas consideran, cuál eligen ni las llamadas al generador
  aleatorio; solo cambia cuánto tarda su movimiento.
- **FR-007**: Si cambia la velocidad de un actor que tiene programada su siguiente acción después de
  atravesar una salida (de cualquier costo), el tiempo restante DEBE reescalarse con la fórmula de
  P1 §2.3 (`restante_nuevo = max(1, (tiempo_siguiente − t) * velocidad_anterior // velocidad_nueva)`)
  y la reprogramación DEBE recibir un número de secuencia nuevo.
- **FR-008**: Una cripta sin ningún campo costo DEBE jugarse exactamente igual que en la primera
  parte: mismos instantes, mismos eventos, mismas llamadas al generador aleatorio y mismo resultado.
- **FR-009**: La vista DEBE mostrar el costo de cada salida de la sala actual, esté abierta o cerrada.
- **FR-010**: Si un costo del esqueleto es menor que 1 o no es entero, o si los dos lados de una
  misma salida declaran costos distintos, el programa DEBE rechazar la cripta con un mensaje que
  indique la salida y el problema, y NO DEBE iniciar la partida. Un float (aunque tenga valor
  entero, como 250.0), un bool o un texto no son enteros. Que solo un lado declare costo no es
  asimetría, y un costo null cuenta como no declarado (FR-001).

### Requisitos funcionales — Cazador

- **FR-011**: DEBE existir un cuarto comportamiento de enemigo, «cazador», cuya ficha de catálogo
  incluye el campo rango, un entero mayor o igual que 0 en unidades de costo (con rango 0 el cazador
  solo ataca si comparte sala; si no, espera). Si la ficha de un cazador no trae rango, o el rango es
  negativo o no es entero, el programa DEBE rechazar el catálogo con un mensaje que indique la ficha
  y NO DEBE iniciar la partida. Si esa ficha llega con la partida ya empezada (por ejemplo, por la
  precarga), la partida DEBE detenerse de forma controlada con ese mismo mensaje, y `partida.log`
  DEBE quedar guardado.
- **FR-012**: Un cazador DEBE activarse como cualquier enemigo (P1 §2.4): dormido hasta que el
  jugador entra a su sala, con su primera acción programada desde el reloj actual con base de costo
  100, y en orden ascendente de id de instancia si se activan varios en el mismo instante.
- **FR-013**: En su turno, si el cazador comparte sala con el jugador, DEBE atacar (P1 §2.6, §2.8)
  con costo 100 y no moverse.
- **FR-014**: Si no comparte sala, el cazador DEBE considerar d, el costo mínimo de llegar desde su
  sala hasta la sala actual del jugador, sumando el costo de cada salida recorrida y usando
  únicamente las salidas abiertas en ese instante.
- **FR-015**: Si no existe ruta, o si d > rango, el cazador DEBE esperar con costo 100.
- **FR-016**: Si existe ruta y d ≤ rango, el cazador DEBE moverse un paso por una ruta de costo d.
  El costo de esa acción DEBE ser el costo de la salida que atraviesa (FR-003).
- **FR-017**: Siendo u la sala del cazador, entre las vecinas v unidas a u por una salida abierta y
  tales que costo(u, v) + dist(v, jugador) = d, el cazador DEBE moverse a la de menor id. Esto DEBE
  cumplirse siempre, aunque haya muchas rutas del mismo costo.
- **FR-018**: El cazador DEBE conocer el esqueleto completo, con los costos, y el estado actual de
  todas las puertas. No le afecta la niebla de guerra del jugador. NO DEBE abrir puertas cerradas ni
  atravesarlas. Su decisión NO DEBE depender de si el contenido de alguna sala ya se descargó.
- **FR-019**: La decisión del cazador en cada turno DEBE ser idéntica a la de un cálculo desde cero
  en ese instante, sin importar lo ocurrido desde su turno anterior: aperturas y cierres de puertas,
  movimientos del jugador, muertes o cambios de sala de otros actores, cambios de velocidad o
  retrocesos. Se PUEDEN reutilizar cálculos anteriores solo si no cambian la decisión.
- **FR-020**: Las acciones del cazador (atacar, moverse, esperar) y todo lo que cambian DEBEN
  revertirse con el pergamino de retroceso como cualquier otra acción enemiga (P1 §2.11).
- **FR-021**: La decisión del cazador (atacar, esperar o a qué vecina moverse) DEBE ser determinista
  y NO DEBE usar el generador aleatorio. El daño de su ataque sí lo usa, como cualquier ataque
  (P1 §2.6). La misma versión de cripta, la misma semilla y los mismos comandos DEBEN reproducir sus decisiones,
  también con `--replay` (P1 §4.11).
- **FR-022**: La vista DEBE distinguir a los cazadores de los demás enemigos.
- **FR-023**: Cuando varios cazadores tienen turno en el mismo instante, DEBEN actuar en el orden de
  la agenda (menor tiempo y luego menor número de secuencia, P1 §2.3), y cada uno DEBE decidir con el
  estado vigente en su propio turno.

### Requisitos funcionales — Datos y persistencia

- **FR-024**: El costo de cada salida DEBE obtenerse del esqueleto y el comportamiento y el rango
  del catálogo (P2 §4.1). Ningún costo ni rango puede estar escrito en el código; la única constante
  permitida es el 100 por omisión de FR-001.
- **FR-025**: Los costos y los rangos DEBEN persistirse localmente junto con la versión de la cripta
  y la versión global del catálogo de las que provienen (P2 Apéndice A). Lo persistido por la primera
  parte DEBE invalidarse mediante la validación de versión, nunca borrando archivos a mano.
- **FR-026**: Guardar y cargar una partida DEBE conservar los costos de las salidas y el estado de
  los cazadores (sala, vida, rango y próxima acción programada).
- **FR-027**: Obtener costos y rangos NO DEBE requerir solicitudes adicionales a las del esqueleto y
  el catálogo, y la decisión del cazador NO DEBE generar solicitudes al servicio.

### Requisitos funcionales — Medición

- **FR-028**: `--bench` DEBE usar criptas sintéticas con costos variables, generadas de forma
  determinista por semilla.
- **FR-029**: `--bench` DEBE medir la decisión de los cazadores con un cazador y con muchos (al menos
  50) persiguiendo al mismo jugador, repartidos a distintas distancias de él y todos dentro de su
  rango, sin ninguno en la sala del jugador al empezar.
- **FR-030**: `--bench` DEBE medir rango pequeño frente a rango grande, y el efecto de aumentar el
  tamaño de la cripta manteniendo igual la región que queda dentro del rango. «Rango pequeño» es un
  rango que deja unas 100 salas dentro de él; el tamaño de la cripta pasa de 2 000 a 20 000 salas.
- **FR-031**: `--bench` DEBE comparar un cálculo compartido por todos los cazadores frente a un
  cálculo por cazador, e indicar bajo qué condiciones conviene cada uno.
- **FR-032**: `--bench` DEBE comparar reutilizar cálculos anteriores frente a recalcular siempre, con
  un escenario de puertas que casi nunca cambian y otro de puertas que cambian seguido.
- **FR-033**: En las mediciones con reutilización, `--bench` DEBE comprobar que cada decisión coincide
  con la de recalcular desde cero y reportar cualquier diferencia como error.
- **FR-034**: `--bench` DEBE ejecutarse sin instanciar la vista y sin red.

### Requisitos de rendimiento

Medidos en el equipo local, sin red ni renderizado (P2 §6.1; constitución, principio VI).

- **FR-035**: El p95 del ciclo de eventos entre dos decisiones del jugador, medido sobre al menos 60
  acciones del jugador, DEBE ser menor que 20 ms en una cripta sintética de 2 000 salas con 50
  cazadores activos (repartidos como en FR-029), y también en la cripta de referencia oficial cuando
  se publique.
- **FR-036**: La decisión de un cazador con rango pequeño DEBE costar en proporción a la región de la
  cripta que queda dentro de su rango, no al tamaño total de la cripta.
- **FR-037**: Con varios cazadores, el trabajo total por ciclo NO DEBE crecer más que linealmente con
  la cantidad de cazadores activos. Se verifica con `--bench` midiendo con 10, 25, 50 y 100
  cazadores: el tiempo por cazador (ciclo ÷ cantidad) con 100 NO DEBE pasar de 2 veces el de 10.

### Entidades clave

- **Salida**: une dos salas; tiene un costo (FR-001, FR-002) y, si tiene puerta, un estado abierta o
  cerrada, una llave y quizá un cierre automático (P1).
- **Ficha de cazador**: entrada del catálogo con comportamiento «cazador», estadísticas de P1 y
  rango (FR-011).
- **Instancia de cazador**: enemigo concreto en la partida: sala actual, vida, velocidad vigente,
  estado dormido o activo y próxima acción programada.
- **Decisión del cazador**: resultado de un turno: atacar, esperar o moverse a una sala vecina
  concreta, con su costo.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: El 100 % de los escenarios de aceptación de esta especificación, incluidos los siete
  casos de «Terreno y cazador» del Apéndice B, tienen una prueba automatizada que cita su FR y pasa.
- **SC-002**: En una partida sintética de al menos 1 000 turnos de cazador con puertas que cambian
  seguido, el 100 % de las decisiones coinciden con las de un cálculo desde cero.
- **SC-003**: Todas las pruebas de la primera parte siguen pasando, y una cripta sin costos produce
  el mismo `partida.log` y el mismo resultado que en la primera parte.
- **SC-004**: El p95 del ciclo de eventos entre dos decisiones del jugador, sobre al menos 60
  acciones, es menor que 20 ms con 50 cazadores activos en una cripta sintética de 2 000 salas (y en
  la cripta oficial cuando se publique), según `--bench`.
- **SC-005**: Para un cazador de rango pequeño (unas 100 salas dentro de su rango), al pasar de una
  cripta de 2 000 salas a una de 20 000 sin cambiar esa región, el tiempo medio por decisión no llega
  a duplicarse, según `--bench`.
- **SC-006**: Dos ejecuciones de `--bench` con la misma semilla generan criptas idénticas y cubren
  los cuatro grupos de medición de FR-029 a FR-032.
- **SC-007**: En una partida, el jugador puede ver el costo de cada salida de su sala y reconocer qué
  enemigos son cazadores sin consultar nada adicional.
- **SC-008**: Según `--bench`, con 10, 25, 50 y 100 cazadores activos, el tiempo por cazador
  (ciclo ÷ cantidad) con 100 no pasa de 2 veces el de 10.

## Supuestos

- Esta especificación no cubre la niebla de guerra, «ir a», la resolubilidad ni la línea de tiempo;
  cada una tiene su propia especificación. El cazador ignora la niebla (FR-018) sin depender de que
  esta exista.
- El formato del archivo binario de partida cambia con la línea de tiempo; la detección de archivos
  de la primera parte como incompatibles (P2 §3.6) se especifica allí. Aquí solo se exige que los
  costos y los cazadores se conserven (FR-026).
- La presencia de otros actores en una sala no bloquea el paso ni cambia el costo de una salida
  (P1 no define bloqueo); solo el estado de las puertas limita las rutas.
- Un movimiento se aplica al ejecutarse la acción (P1 §2.5): el actor aparece en la sala destino y el
  costo de la salida determina cuándo vuelve a actuar. «Atravesar una salida costosa» significa
  estar a la espera de esa siguiente acción.
- La cripta de referencia oficial la publica el profesor; mientras tanto se mide con la cripta
  sintética de FR-035. Si la cripta oficial trae otra cantidad de cazadores, o si se ajusta el
  límite de 20 ms por enmienda (P2 §2.7), se actualiza FR-035.
- El umbral de SC-005 («no llega a duplicarse») es una meta del grupo para hacer verificable FR-036.
