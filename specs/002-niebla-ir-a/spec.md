# Especificación de capacidad: Niebla de guerra e «ir a»

**Capacidad**: 002 — `002-niebla-ir-a`

**Creada**: 2026-11-12

**Estado**: Borrador

**Fuentes**: P2 §3.3, §3.4, §5.3, §6.1, §6.3, §7.3 y Apéndice B («Niebla de guerra e ir a»).
Reglas heredadas de P1 (§2.3, §2.4, §2.7, §2.11, §4.2, §4.10, §4.11), de la capacidad 001 (costo de
las salidas, desempate del cazador), de la 003 (excepción del reporte de resolubilidad) y de la 004
(línea de tiempo y formato del archivo de partida).

**Entrada**: descripción del grupo en `/speckit-specify` (registrada en `PROMPTS_LLM.md`).

## Contexto: por qué existe esta capacidad

En la primera parte el jugador veía la cripta completa. Con esta capacidad solo conoce lo que ha
explorado: las salas en las que entró, lo que vio de sus puertas la última vez que pasó por ahí y,
como mucho, que existe algo detrás de una salida. El mapa que recuerda puede estar desactualizado:
una puerta que vio abierta pudo cerrarse. La antorcha, que en P1 no tenía efecto, ahora deja ver las
salas vecinas. Y como recorrer a mano una cripta grande es tedioso, el comando «ir a» lleva al
jugador a una sala ya explorada paso a paso, usando solo lo que conoce, y se detiene cuando pasa
algo que merece su atención.

### Glosario

- **Sala explorada**: sala en la que el jugador entró al menos una vez, o que reveló la antorcha.
  La sala inicial está explorada desde el instante 0. De ella el jugador conoce nombre, salidas,
  costo de cada salida y el estado de sus puertas según su última observación.
- **Sala avistada**: sala no explorada que es destino de una salida de una sala explorada. El
  jugador solo sabe que existe; se muestra por su id, sin nombre.
- **Sala desconocida**: ni explorada ni avistada. El jugador no sabe nada de ella.
- **Observar una salida**: registrar en el mapa del jugador el estado real (abierta o cerrada) de
  esa salida en ese instante. Los dos lados de una puerta son la misma puerta: observarla desde un
  lado actualiza lo que se recuerda de ella desde ambos.
- **Estado recordado**: el estado de una puerta según la última observación del jugador, aunque
  después haya cambiado.
- **Mapa conocido**: el conjunto de salas exploradas y avistadas con lo que el jugador recuerda de
  ellas. Es estado del juego.
- **Ruta conocida**: secuencia de salidas que el mapa recuerda abiertas, que va solo por salas
  exploradas. Su costo es la suma de los costos de sus salidas (capacidad 001).
- **Viaje**: la ejecución de un comando `ir a <sala>`: una serie de pasos, cada uno un movimiento
  ordinario del jugador.

## Aclaraciones

### Sesión 2026-11-12

- P: ¿Sobre qué pasos se mide el límite de 5 ms de «ir a»? → R: El p95 de todos los pasos de al
  menos 20 viajes completos (200 pasos o más) con el mapa conocido completo de 2 000 salas; el primer
  paso de cada viaje se reporta aparte y, si pasa de 5 ms, se documenta como límite en
  `DECISIONES.md`. Recalcular desde cero en cada paso no cumple, así que el plan debe reutilizar el
  cálculo mientras el mapa conocido no cambie (FR-234, SC-204, Supuestos).
- P: ¿La antorcha puede provocar solicitudes al servicio? → R: No: con y sin antorcha se hacen las
  mismas solicitudes; la precarga sigue siendo infraestructura (FR-214).
- P: ¿Qué responde `ir a` con un id de sala que no existe? → R: El mismo mensaje que con una sala no
  explorada, para no revelar qué salas existen (FR-216).
- P: ¿Dónde va el comentario de `ir a` en `partida.log`? → R: Antes de los `mover` de ese viaje
  (FR-222).
- P: Si durante un viaje un enemigo entra a la sala del jugador sin hacerle daño, ¿el viaje se
  detiene? → R: No. Solo lo detienen las condiciones de P2 §3.4 y las técnicas ya listadas; si el
  enemigo ataca, el daño lo detiene (FR-221, HU3-16).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 — Solo veo lo que he explorado (Prioridad 1)

Como jugador, quiero ver solo la parte de la cripta que he explorado, con las puertas como las vi la
última vez, y poder consultar ese mapa con el comando `mapa`.

**Por qué esta prioridad**: es la base de la capacidad; la antorcha, «ir a», la línea de tiempo y la
persistencia trabajan sobre el mapa conocido.

**Prueba independiente**: con una cripta sintética pequeña, se mueve al jugador por una secuencia
fija, se cambian puertas lejos de él y se compara el mapa conocido, la vista y la bitácora con lo
esperado.

**Escenarios de aceptación**:

1. **Dada** una partida recién iniciada en la sala 1, con salidas a las salas 2 y 3, **cuando** se
   consulta `mapa`, **entonces** la sala 1 aparece explorada (id, nombre y cada salida con
   dirección, sala destino, costo y estado recordado), las salas 2 y 3 aparecen avistadas (solo su
   id) y ninguna otra sala aparece. *(FR-201, FR-202, FR-203, FR-210)*
2. **Dado** el jugador que entra a la sala 2, **cuando** se consulta `mapa`, **entonces** la sala 2
   pasa a explorada y las salas destino de sus salidas que no estaban exploradas pasan a avistadas.
   *(FR-201, FR-202)*
3. **Dada** una puerta entre las salas 2 y 4 que el jugador vio abierta desde la sala 2, **cuando**
   se cierra mientras el jugador está en la sala 1, **entonces** el mapa la sigue recordando
   abierta; y **cuando** el jugador vuelve a la sala 2 o entra a la 4, **entonces** el mapa la
   recuerda cerrada desde ambos lados. *(FR-204, FR-205, FR-206)*
4. **Dada** una puerta de la sala actual que se cierra automáticamente mientras el jugador espera,
   **cuando** llega la siguiente decisión del jugador, **entonces** el mapa ya la recuerda cerrada.
   *(FR-204)*
5. **Dada** una salida sin vuelta de la sala 5 a la sala actual, **cuando** el jugador está en la
   sala actual, **entonces** esa salida no se observa ni aparece en el mapa desde aquí, y la sala 5
   no pasa a avistada por ella. *(FR-202, FR-205)*
6. **Dado** el jugador en la sala 1, **cuando** un enemigo se regenera en la sala 7, una trampa se
   rearma en la sala 8 o una puerta se cierra automáticamente en la sala 9, **entonces** la
   bitácora no dice nada de eso; y **cuando** lo mismo ocurre en la sala 1, **entonces** sí lo dice.
   *(FR-208)*
7. **Dado** el jugador en una sala, **cuando** se muestra la vista, **entonces** de cada salida de
   la sala actual se ve su costo y su estado recordado, y de las salas vecinas no exploradas solo su
   id. *(FR-207)*
8. **Cuando** el jugador escribe `mapa`, **entonces** no consume tiempo, no es acción, no se anota en
   `partida.log` y no hace solicitudes de red. *(FR-211)*
9. **Cuando** el jugador escribe `mapa 3`, **entonces** se trata como comando inválido, igual que en
   P1. *(FR-211)*
10. **Dado** que la precarga ya descargó el contenido de salas que el jugador no ha explorado,
    **cuando** se muestran la vista, `mapa` y la bitácora, **entonces** ninguno revela nada de esas
    salas más allá de lo que permite el mapa conocido. *(FR-209)*

---

### Historia de usuario 2 — La antorcha deja ver las salas vecinas (Prioridad 2)

Como jugador, con la antorcha encendida quiero que, al entrar a una sala, también queden exploradas
sus vecinas, sin despertar a nadie ni activar trampas.

**Por qué esta prioridad**: P2 §3.3 le da efecto a la antorcha de P1; depende de la historia 1.

**Prueba independiente**: se entra a una sala con y sin antorcha y se compara el mapa conocido, los
enemigos, las trampas y las solicitudes de red.

**Escenarios de aceptación**:

1. **Dado** el jugador con la antorcha encendida, **cuando** entra a la sala 2, con salidas abiertas
   y cerradas hacia las salas 3, 4 y 5, **entonces** las salas 3, 4 y 5 quedan exploradas (nombre y
   salidas, con sus puertas observadas en ese instante) y los destinos de sus salidas que no estaban
   explorados pasan a avistados. *(FR-212, FR-213)*
2. **Dadas** salas vecinas con enemigos dormidos y trampas armadas, **cuando** la antorcha las
   explora, **entonces** sus enemigos siguen dormidos, sus trampas no se activan y el jugador no ve su
   contenido; y la misma partida jugada con y sin antorcha hace exactamente las mismas solicitudes
   al servicio. *(FR-214)* — Apéndice B.
3. **Dado** el jugador sin antorcha encendida, **cuando** entra a la sala 2, **entonces** solo la
   sala 2 pasa a explorada. *(FR-212)*
4. **Dado** el jugador con la antorcha encendida, **cuando** la antorcha se apaga y después entra a
   otra sala, **entonces** solo esa sala pasa a explorada; lo explorado antes con la antorcha sigue
   explorado. *(FR-212, FR-215)*

---

### Historia de usuario 3 — Viajar a una sala explorada con «ir a» (Prioridad 3)

Como jugador, quiero escribir `ir a <sala>` y que el juego me lleve por la ruta más barata que
conozco, deteniéndose si pasa algo importante y diciéndome por qué.

**Por qué esta prioridad**: es la otra mitad de la capacidad (P2 §3.4, §7.3); depende de la
historia 1.

**Prueba independiente**: con criptas sintéticas armadas para cada caso, se ejecuta `ir a` y se
comprueba cada paso, el instante de cada acción, el motivo de parada y el `partida.log`.

**Escenarios de aceptación**:

1. **Dada** la sala 9 no explorada, **cuando** el jugador escribe `ir a 9`, **entonces** se rechaza
   con un mensaje y no consume tiempo; y `ir a 99999`, con una sala que no existe, da exactamente el
   mismo mensaje. *(FR-216)* — Apéndice B.
2. **Cuando** el jugador escribe `ir a` hacia la sala actual, o hacia una sala explorada sin ruta
   conocida desde la sala actual, **entonces** se rechaza con un mensaje y no consume tiempo.
   *(FR-216)*
3. **Cuando** el jugador escribe `ir a`, `ir a x` o `ir a 3 4`, **entonces** se trata como comando
   inválido, igual que en P1. *(FR-216)*
4. **Dadas** las salas 1, 2, 3 y 4 exploradas, con la salida 1–4 de costo 500 y la ruta 1–2–4 con
   salidas de costo 100, **cuando** el jugador en la sala 1 escribe `ir a 4`, **entonces** va por la
   sala 2 (costo 200). *(FR-217)*
5. **Dadas** dos rutas conocidas de igual costo mínimo desde la sala 1, una que empieza hacia la
   sala 5 y otra hacia la sala 3, **cuando** el jugador escribe `ir a`, **entonces** el primer paso
   es hacia la sala 3. *(FR-217)*
6. **Dada** una ruta más barata que pasa por una sala avistada (no explorada), **cuando** el jugador
   escribe `ir a`, **entonces** no la usa: va por la ruta más barata que solo pasa por salas
   exploradas. *(FR-217)*
7. **Dada** una ruta conocida que cruza una puerta que el mapa recuerda abierta pero que está
   cerrada, **cuando** el jugador llega a la sala de esa puerta, **entonces** la observa cerrada, el
   mapa se actualiza y el siguiente paso se calcula sin ella; si ya no hay ruta conocida, el viaje se
   detiene sin consumir tiempo adicional y la vista dice por qué. *(FR-204, FR-218, FR-221)*
   — Apéndice B.
8. **Dada** una ruta cuya única opción cruza una puerta cerrada que el jugador puede abrir con una
   llave que tiene, **cuando** escribe `ir a`, **entonces** el viaje no abre la puerta: se rechaza (o
   se detiene) por falta de ruta conocida. *(FR-219)*
9. **Dado** un viaje de 4 pasos con salidas de costo 100, 250, 100 y 300 y el jugador de velocidad
   100, **cuando** termina, **entonces** cada paso fue un movimiento ordinario con su propio
   intervalo (100, 250, 100, 300) y entre paso y paso corrieron los eventos del reloj. *(FR-220)*
10. **Dado** un viaje que entra a una sala con enemigos dormidos, **cuando** el jugador entra,
    **entonces** los enemigos se activan según P1 §2.4 y el viaje se detiene. *(FR-221)*
    — Apéndice B.
11. **Dado** un viaje en el que el jugador recibe daño (por un ataque, una trampa o un pulso de
    veneno), **cuando** ocurre, **entonces** el viaje se detiene después de ese paso y la vista dice
    por qué. *(FR-221)*
12. **Dado** un viaje cuyo siguiente paso no se puede hacer (sin presupuesto de solicitudes o sin
    conexión para cargar la sala destino), **cuando** llega ese paso, **entonces** el viaje se
    detiene sin hacer ese paso ni consumir su tiempo, y la vista dice por qué. *(FR-221)*
13. **Dado** un viaje durante el cual la partida termina (el jugador muere o escapa), **cuando**
    ocurre, **entonces** el viaje se detiene. *(FR-221)*
14. **Dado** un viaje de 3 pasos, **cuando** termina, **entonces** `partida.log` tiene una línea de
    comentario con la orden `ir a` seguida de tres líneas `mover` individuales; y **cuando** se reproduce con
    `--replay`, **entonces** da la misma partida. *(FR-222, FR-223)*
15. **Dado** un `partida.log` de la primera parte, **cuando** se reproduce, **entonces** da el mismo
    resultado que antes de esta capacidad. *(FR-223)*
16. **Dado** un viaje en curso, **cuando** un enemigo entra a la sala del jugador entre dos pasos sin
    atacarlo, **entonces** el viaje sigue; **y cuando** ese enemigo lo ataca y le hace daño,
    **entonces** el viaje se detiene. *(FR-221)*

---

### Historia de usuario 4 — El conocimiento es estado del juego (Prioridad 4)

Como jugador, quiero que el pergamino, el guardado y la línea de tiempo traten lo que conozco del
mapa como cualquier otro estado de la partida.

**Por qué esta prioridad**: P2 §3.3 lo exige; depende de las historias 1 a 3.

**Prueba independiente**: se juega, se usa el pergamino, se guarda y se carga, y se consulta la
historia, comparando el mapa conocido en cada caso.

**Escenarios de aceptación**:

1. **Dado** el jugador con la antorcha encendida que entra a una sala y explora 4 vecinas, **cuando**
   usa un pergamino, **entonces** esa sala y sus 4 vecinas vuelven exactamente al estado que tenían
   antes (explorada, avistada o desconocida), y también las puertas observadas. *(FR-224)*
   — Apéndice B.
2. **Dado** un viaje que ya hizo 3 pasos y se detuvo, **cuando** el jugador usa un pergamino,
   **entonces** se revierte solo el último paso y el viaje no se reanuda. *(FR-225)* — Apéndice B.
3. **Dada** una partida con 30 salas exploradas y puertas recordadas con estados distintos de los
   reales, **cuando** se guarda y se carga, **entonces** el mapa conocido es idéntico. *(FR-226)*
4. **Dado** un archivo de partida de un formato anterior (primera parte, 001 o sin mapa conocido),
   **cuando** se intenta cargar, **entonces** se rechaza como incompatible, igual que en la 004.
   *(FR-227)*
5. **Dada** una partida en la que el jugador observó una puerta abierta en el instante 300 y cerrada
   en el 900, **cuando** se consulta `historia 500`, **entonces** el resumen muestra el mapa conocido
   de ese momento, con la puerta recordada abierta. *(FR-228)*

---

### Historia de usuario 5 — Medición con `--bench` (Prioridad 5)

Como grupo, quiero medir las consultas al mapa conocido y el cálculo de un paso de «ir a», cada uno
frente a una alternativa descartada, para defender nuestras decisiones.

**Por qué esta prioridad**: no cambia el juego, pero es requisito de evaluación (P2 §5.3, §6.3) y
respalda los requisitos de rendimiento.

**Prueba independiente**: se ejecuta `--bench` dos veces con la misma semilla y se revisan sus
secciones y resultados.

**Escenarios de aceptación**:

1. **Dada** una semilla, **cuando** se ejecuta `--bench` dos veces, **entonces** las criptas
   sintéticas y los mapas conocidos generados son idénticos. *(FR-229)*
2. **Cuando** se ejecuta `--bench`, **entonces** mide las consultas al mapa conocido (estado de una
   sala, estado recordado de una puerta) y la exploración, frente a una alternativa descartada, y
   comprueba que ambas dan los mismos resultados. *(FR-230, FR-232)*
3. **Cuando** se ejecuta `--bench`, **entonces** mide el cálculo de un paso de «ir a» frente a una
   alternativa descartada y comprueba que ambas eligen el mismo paso. *(FR-231, FR-232)*
4. **Dado** el mapa conocido completo de una cripta sintética de 2 000 salas, **cuando** `--bench`
   mide todos los pasos de al menos 20 viajes completos (200 pasos o más) entre salas repartidas de
   forma determinista, **entonces** el p95 es menor que 5 ms, y el costo del primer paso de cada
   viaje se reporta aparte. *(FR-234)*
5. **Cuando** `--bench` mide consultas al mapa conocido con 200 y con 2 000 salas exploradas,
   **entonces** el tiempo medio por consulta con 2 000 no pasa de 2 veces el de 200. *(FR-235)*
6. **Cuando** `--bench` mide entradas con antorcha que revelan la misma cantidad de salas con mapas
   conocidos de 200 y de 2 000 salas, **entonces** el tiempo medio por entrada con 2 000 no pasa de
   2 veces el de 200; y revertir esas entradas cumple lo mismo. *(FR-236)*
7. **Cuando** se ejecuta `--bench`, **entonces** no instancia la vista ni hace solicitudes de red.
   *(FR-233)*

---

### Casos borde

- **Sala inicial**: explorada desde el instante 0, con sus salidas observadas (FR-201, FR-204).
- **Salida sin vuelta desde otra sala hacia la actual**: no se observa desde aquí y no hace avistada
  a su origen (FR-202, FR-205).
- **Puerta que cambia lejos del jugador**: el mapa conserva el último estado observado (FR-206).
- **Puerta de la sala actual que cambia entre dos decisiones**: se observa antes de la siguiente
  decisión (FR-204).
- **Sala explorada por la antorcha y después visitada**: al entrar se revela su contenido y se
  activan enemigos y trampas como en P1 (FR-214).
- **Antorcha que revela una sala ya explorada**: sigue explorada; sus salidas se observan de nuevo
  (FR-212, FR-213).
- **`ir a` a la sala actual, a una sala no explorada o sin ruta conocida**: rechazo sin consumir
  tiempo (FR-216).
- **`ir a` iniciado en una sala con enemigos**: se permite; las condiciones de parada se evalúan
  después de cada paso (FR-221).
- **Ruta que se queda sin opciones a mitad del viaje**: se detiene sin consumir tiempo adicional
  (FR-221).
- **Paso que no se puede hacer por red o presupuesto**: el viaje se detiene sin hacer el paso (FR-221).
- **Puerta cerrada con llave en el inventario**: «ir a» no la abre (FR-219).
- **Victoria durante un viaje** (por una puerta ya abierta hacia la salida): la partida termina y el
  viaje se detiene (FR-221).
- **Pergamino después de un viaje**: revierte solo el último paso; el viaje no continúa (FR-225).
- **Reporte de resolubilidad al iniciar**: muestra salas no exploradas como excepción declarada en
  la 003; no cambia el mapa conocido (FR-209).

## Requisitos *(obligatorio)*

Los identificadores son estables y no se renumeran (constitución, principio IX). Usan la serie 200
para no chocar con las otras capacidades.

### Requisitos funcionales — Mapa conocido

- **FR-201**: Una sala DEBE quedar explorada cuando el jugador entra en ella o cuando la revela la
  antorcha (FR-212). La sala inicial DEBE estar explorada desde el instante 0. Una sala explorada
  NUNCA vuelve a dejar de estarlo, salvo por un pergamino (FR-224).
- **FR-202**: Una sala no explorada DEBE estar avistada si es destino de alguna salida de una sala
  explorada, y desconocida en otro caso. Una salida sin vuelta que llega a una sala explorada desde
  otra NO la hace avistada.
- **FR-203**: De una sala explorada el jugador DEBE conocer su nombre, sus salidas (dirección y sala
  destino), el costo de cada salida y el estado recordado de sus puertas. De una avistada solo
  conoce su id. De una desconocida, nada.
- **FR-204**: Al entrar a una sala y antes de cada decisión del jugador, el jugador DEBE observar
  todas las salidas de la sala donde está: el mapa registra el estado real de cada una en ese
  instante.
- **FR-205**: Los dos lados de una puerta DEBEN tratarse como la misma puerta: observarla desde un
  lado actualiza su estado recordado desde ambos. Una salida sin vuelta que llega a la sala actual
  desde otra sala NO se observa desde la sala actual.
- **FR-206**: El mapa DEBE recordar el estado de cada puerta según su última observación, aunque
  después cambie.

### Requisitos funcionales — Lo que se muestra

- **FR-207**: Todo lo que muestra la vista DEBE salir solo del mapa conocido y de lo que hay en la
  sala del jugador: de las salidas de la sala actual, su dirección, destino, costo y estado
  recordado; de las salas no exploradas, a lo sumo su id.
- **FR-208**: La bitácora DEBE mostrar solo lo que pasa en la sala del jugador o le pasa al jugador.
  NO DEBE avisar de lo que ocurre en otras salas (por ejemplo, enemigos que se regeneran, trampas que
  se rearman, puertas que se cierran o enemigos que se mueven fuera de la sala del jugador).
- **FR-209**: El esqueleto completo y la precarga siguen siendo infraestructura y PUEDEN usar toda la
  cripta, pero nada de lo que obtienen DEBE llegar a la vista ni a «ir a» salvo a través del mapa
  conocido. La única excepción es el reporte de resolubilidad al iniciar (capacidad 003, FR-325), que
  no cambia el mapa conocido.
- **FR-210**: El comando `mapa` DEBE mostrar las salas exploradas (id, nombre y cada salida con
  dirección, sala destino, costo y estado recordado, en el orden N, S, E, O) y las salas avistadas
  (solo id), ambas listas ordenadas por id.
- **FR-211**: `mapa` NO DEBE consumir tiempo, NO DEBE ser una acción, NO DEBE anotarse en
  `partida.log` y NO DEBE hacer solicitudes de red. Con argumentos DEBE tratarse como comando
  inválido, igual que en P1.

### Requisitos funcionales — Antorcha

- **FR-212**: Con la antorcha encendida (P1 §2.7), al entrar a una sala DEBEN quedar exploradas
  también todas las salas a las que llevan sus salidas, abiertas o cerradas. Sin antorcha encendida,
  solo la sala a la que se entra.
- **FR-213**: Las salidas de las salas reveladas por la antorcha DEBEN contar como observadas en ese
  instante, y los destinos de esas salidas que no estén explorados pasan a avistados (FR-202).
- **FR-214**: Explorar una sala con la antorcha NO DEBE revelar su contenido, NO DEBE activar sus
  enemigos ni sus trampas y NO DEBE provocar ninguna solicitud al servicio: con y sin antorcha se
  hacen exactamente las mismas solicitudes (la precarga sigue siendo infraestructura y no depende de
  la antorcha, FR-209). Al entrar después a esa sala, su contenido, enemigos y trampas se comportan
  como en P1.
- **FR-215**: Lo explorado con la antorcha DEBE seguir explorado cuando la antorcha se apaga.

### Requisitos funcionales — «ir a»

- **FR-216**: El comando `ir a <sala>` DEBE aceptar solo el id de una sala explorada distinta de la
  actual y con una ruta conocida desde la sala actual. Hacia una sala no explorada, hacia la sala
  actual o sin ruta conocida, DEBE rechazarse con un mensaje y sin consumir tiempo. Un id de sala que
  no existe en la cripta DEBE rechazarse con el mismo mensaje que una sala no explorada, para no
  revelar qué salas existen. Un texto mal
  formado (sin sala, con una sala que no es un entero o con argumentos de más) DEBE tratarse como
  comando inválido, igual que en P1.
- **FR-217**: La ruta DEBE usar solo salas exploradas y salidas que el mapa recuerda abiertas, DEBE
  minimizar la suma de los costos de sus salidas y, si varias rutas empatan, el primer paso DEBE ir
  a la vecina de menor id entre las que inician una ruta de costo mínimo (igual que el cazador,
  capacidad 001 FR-017). DEBE calcularse solo con el mapa conocido.
- **FR-218**: Antes de cada paso, después de observar las salidas de la sala actual (FR-204), la
  ruta DEBE recalcularse con el mapa conocido vigente.
- **FR-219**: «ir a» NO DEBE abrir puertas, aunque el jugador tenga la llave.
- **FR-220**: Cada paso DEBE ser un movimiento ordinario completo del jugador: cuesta según el costo
  de la salida (capacidad 001), cuenta como acción del jugador y entre paso y paso ocurren
  normalmente los eventos del reloj.
- **FR-221**: El viaje DEBE detenerse cuando: el jugador llega al destino; entra a una sala con
  enemigos, activos o dormidos (los dormidos se activan según P1 §2.4); recibe daño (ataque, trampa
  o veneno); deja de existir una ruta conocida (sin consumir tiempo adicional); el siguiente paso no
  se puede hacer (por ejemplo, sin presupuesto de solicitudes o sin conexión para cargar la sala),
  sin hacer ese paso ni consumir su tiempo; o la partida termina. Ninguna otra cosa DEBE detenerlo:
  en particular, un enemigo que entra a la sala del jugador sin hacerle daño no lo detiene (si
  ataca, el daño sí). La vista DEBE decir por qué se detuvo.
- **FR-222**: En `partida.log`, cada paso DEBE anotarse como un `mover` individual, y la orden
  `ir a` como una línea de comentario que va antes de los `mover` de ese viaje.
- **FR-223**: La reproducción (`--replay`) DEBE ignorar las líneas de comentario; un `partida.log`
  con viajes DEBE reproducir la misma partida, y los de la primera parte DEBEN seguir reproduciéndose
  igual.

### Requisitos funcionales — Estado del juego

- **FR-224**: El mapa conocido DEBE ser estado del juego reversible: el pergamino de retroceso DEBE
  devolver las salas exploradas, avistadas y los estados recordados de las puertas exactamente a
  como estaban antes de la acción revertida, incluidas las salas reveladas por la antorcha.
- **FR-225**: El pergamino DEBE revertir solo el último paso de un viaje, como cualquier otra acción,
  y el viaje NO DEBE reanudarse.
- **FR-226**: Guardar y cargar una partida DEBE conservar el mapa conocido completo.
- **FR-227**: Un archivo de partida de un formato anterior DEBE rechazarse como incompatible, igual
  que en la capacidad 004 (FR-419); nunca se carga en silencio.
- **FR-228**: El mapa conocido DEBE formar parte de la línea de tiempo: el resumen de `historia` y de
  `--replay … --hasta` (capacidad 004, FR-406) DEBE mostrarlo como era en el estado consultado.

### Requisitos funcionales — Medición

- **FR-229**: `--bench` DEBE generar criptas sintéticas y mapas conocidos de forma determinista por
  semilla.
- **FR-230**: `--bench` DEBE medir las consultas al mapa conocido (estado de una sala, estado
  recordado de una puerta), la exploración y su reversión, frente a una alternativa descartada.
- **FR-231**: `--bench` DEBE medir el cálculo de un paso de «ir a» frente a una alternativa
  descartada.
- **FR-232**: `--bench` DEBE comprobar que cada alternativa da los mismos resultados que la elegida y
  reportar cualquier diferencia como error.
- **FR-233**: `--bench` DEBE ejecutarse sin instanciar la vista y sin red.

### Requisitos de rendimiento

Medidos en el equipo local, sin red ni vista (P2 §6.1; constitución, principio VI).

- **FR-234**: El p95 del cálculo de un paso de «ir a», medido sobre todos los pasos de al menos 20
  viajes completos (200 pasos o más) entre salas repartidas de forma determinista, DEBE ser menor
  que 5 ms con el mapa conocido completo de la cripta sintética de referencia de la 001 (2 000
  salas), y también con la cripta de referencia oficial cuando se publique. `--bench` DEBE reportar
  aparte el costo del primer paso de cada viaje (el que calcula la ruta entera); si pasa de 5 ms, se
  documenta como límite conocido en `DECISIONES.md`.
- **FR-235**: Consultar el estado de una sala o el estado recordado de una puerta NO DEBE depender
  del tamaño del mapa conocido: según `--bench`, el tiempo medio por consulta con 2 000 salas
  exploradas NO DEBE pasar de 2 veces el de 200.
- **FR-236**: Explorar DEBE costar en proporción a las salas reveladas, no al tamaño del mapa
  conocido, y registrar y deshacer esos cambios DEBE costar lo mismo en proporción: según `--bench`,
  con la misma cantidad de salas reveladas, el tiempo medio de una entrada con antorcha y el de su
  reversión con un mapa de 2 000 salas NO DEBEN pasar de 2 veces los de uno de 200.

### Entidades clave

- **Mapa conocido**: salas exploradas y avistadas, con lo que el jugador recuerda de ellas.
- **Conocimiento de una sala**: estado (explorada, avistada o desconocida); si está explorada,
  nombre, salidas y sus costos.
- **Puerta recordada**: estado de una puerta según la última observación del jugador; es el mismo
  desde sus dos lados.
- **Viaje**: destino, pasos hechos y motivo de parada.
- **Motivo de parada**: llegada, sala con enemigos, daño, sin ruta conocida, paso imposible (red o
  presupuesto) o fin de la partida.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-201**: El 100 % de los escenarios de aceptación de esta especificación, incluidos los seis
  casos de «Niebla de guerra e ir a» del Apéndice B, tienen una prueba automatizada que cita su FR y
  pasa.
- **SC-202**: En partidas sintéticas generadas por semilla (al menos 20, con antorcha, puertas que
  cambian y pergaminos), nada de lo que muestra la vista ni de lo que usa «ir a» se refiere a una sala
  desconocida, ni a una sala avistada más que por su id.
- **SC-203**: En esas partidas, cada paso de «ir a» coincide con el de un cálculo desde cero sobre el
  mapa conocido de ese instante.
- **SC-204**: Según `--bench`, el p95 de un paso de «ir a», sobre todos los pasos de al menos 20
  viajes completos (200 pasos o más), es menor que 5 ms con el mapa conocido completo de 2 000 salas;
  el costo del primer paso de cada viaje se reporta aparte.
- **SC-205**: Según `--bench`, las consultas al mapa conocido y la exploración con antorcha no llegan
  a costar el doble al pasar de 200 a 2 000 salas exploradas.
- **SC-206**: Los `partida.log` de la primera parte y de la 001 se reproducen con el mismo resultado,
  y los nuevos con viajes también.
- **SC-207**: Todas las pruebas de la primera parte, de la 001, de la 003 y de la 004 siguen pasando,
  salvo las que comprobaban que la vista o la bitácora mostraban información de salas no conocidas,
  que se ajustan a la niebla.

## Supuestos

- Esta capacidad no cambia al cazador: conoce el esqueleto completo y no le afecta la niebla
  (capacidad 001, FR-018).
- «ir a» desde una sala con enemigos se permite; las condiciones de parada se revisan después de
  cada paso.
- El mapa conocido y el formato del archivo de partida cambian también en la 004; el formato que se
  entrega es uno solo, y cualquier formato anterior se rechaza (FR-227).
- Los umbrales de FR-235 y FR-236 («no pasa de 2 veces de 200 a 2 000 salas») y el p95 de FR-234 son
  metas del grupo para hacer verificables las propiedades de P2 §5.3 y el límite de 5 ms de P2 §6.1,
  con el mismo criterio de p95 que la 001.
- Si el profesor publica la cripta de referencia o ajusta el límite de 5 ms por enmienda (P2 §2.7),
  se actualiza FR-234.
- Una búsqueda completa hasta un destino al azar en 2 000 salas tarda varios milisegundos (medido en
  otra máquina: media 6,4 ms y p95 11 ms), así que recalcular la ruta desde cero en cada paso no
  cumple FR-234. El plan debe reutilizar el cálculo entre pasos mientras el mapa conocido no cambie,
  sin cambiar el paso elegido (FR-217, FR-218; SC-203).
