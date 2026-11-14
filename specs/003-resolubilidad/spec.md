# Especificación de capacidad: Verificación de resolubilidad

**Capacidad**: 003 — `003-resolubilidad`

**Creada**: 2026-11-12

**Estado**: Borrador

**Fuentes**: P2 §3.5, §4.2, §4.3, §5.4, §6.1, §6.3, §7.3, Apéndice A y Apéndice B («Resolubilidad»).
Reglas heredadas de P1 (§2.11, §3, §4.10, §4.11, §5.1) y de la capacidad 001 (rechazo de datos
inválidos).

**Entrada**: descripción del grupo en `/speckit-specify` (registrada en `PROMPTS_LLM.md`).

## Contexto: por qué existe esta capacidad

El servicio publica criptas que no se pueden ganar: la llave de salida puede estar encerrada detrás
de la puerta que ella misma abre, o una cadena de llaves puede depender de sí misma. Sin esta
capacidad el jugador lo descubre después de explorar media cripta. Con ella, antes de empezar, el
programa dice si la cripta se puede ganar; si se puede, en qué orden conviene conseguir las llaves,
y si no, qué llaves faltan, qué puertas lo bloquean, dónde están esas llaves y qué ciclo de
dependencias lo impide.

### Glosario

- **Ubicación de las llaves**: lista que entrega el servicio (P2 §4.2) con, para cada llave, la sala
  donde está y, si la suelta un enemigo, el id de ese enemigo. Una misma llave puede aparecer en
  varias ubicaciones.
- **Llaves de la cripta**: toda llave que aparece en la ubicación de las llaves, como llave de alguna
  salida cerrada del esqueleto o como `llave_salida`.
- **Salida cruzable**: bajo los supuestos de la verificación, una salida abierta, una salida cerrada
  sin llave, o una salida cerrada cuya llave ya se obtuvo. Una salida sin vuelta solo se cruza en su
  sentido.
- **Región alcanzable**: salas a las que se llega desde `sala_inicial` cruzando solo salidas
  cruzables, sabiendo que toda llave ubicada en una sala alcanzable se obtiene. Se supone que el
  jugador puede volver a cualquier sala de la región (FR-303).
- **Llave obtenible**: llave con al menos una ubicación en la región alcanzable.
- **Puerta bloqueada**: salida cerrada que pide una llave no obtenible.
- **Frontera bloqueada**: puertas bloqueadas que salen de una sala de la región alcanzable hacia una
  sala que no es de la región alcanzable.
- **Dependencia de una llave no obtenible**: ver FR-314.
- **Ciclo de dependencia**: cadena de llaves A → B → … → A en la que cada una depende de la
  siguiente.
- **Verificación**: el cálculo completo de esta capacidad sobre una cripta; su resultado es el orden
  de llaves (si es resoluble) o el reporte (si no lo es).

## Aclaraciones

### Sesión 2026-11-12

- P: Con salidas sin vuelta, ¿la región alcanzable supone que el jugador puede volver a cualquiera
  de sus salas? → R: Sí. La región es todo lo que se alcanza desde `sala_inicial` y se supone que el
  jugador puede volver a cualquier sala de ella, como pide el enunciado; el posible falso
  «resoluble» queda como límite conocido en Supuestos (FR-303).
- P: ¿Con qué cripta sintética se mide el límite de 200 ms mientras no se publique la más grande?
  → R: 2 000 salas (el tamaño de referencia de la 001) con 500 llaves encadenadas (FR-334, SC-303).
- P: ¿Qué umbral hace verificable el «aproximadamente lineal»? → R: Al duplicar el tamaño, el tiempo
  no pasa de 3 veces el anterior; lo lineal da cerca de 2 y repetir el recorrido por llave cerca de
  4 (FR-335, SC-304).
- P: ¿Qué pasa con las pruebas existentes que inician una partida sin conexión? → R: Se agrega la
  ubicación de las llaves a sus datos de prueba (FR-324); no cambia lo que comprueban (SC-307).
- P: ¿El reporte se muestra completo al iniciar, aunque revele salas que el jugador no ha explorado?
  → R: Sí, como excepción declarada a la niebla de guerra (P2 §3.5 y §7.3 lo exigen): el reporte y
  el orden de llaves se muestran completos al iniciar y no cambian el mapa conocido; ninguna sala
  pasa a explorada ni a avistada (FR-325).
- P: ¿Con qué código termina una partida normal que no inicia? → R: Los mismos de `--verificar`:
  2 si la cripta no es resoluble; 1 si no se pudo verificar (sin la ubicación de las llaves, falla
  de red o datos inválidos) (FR-325, FR-329).
- P: ¿El orden de llaves lleva solo ids o también dónde se obtiene cada llave? → R: Solo los ids,
  en orden y agrupados por ronda; sin ubicaciones (FR-306).

## Escenarios de usuario y pruebas *(obligatorio)*

En los escenarios, «la sala 1 es la inicial» y «la sala 4 es `sala_salida`» describen la cripta;
`a`, `b`, `c`, `x` y `salida` abrevian ids de llaves (`itm_llave_a`, …, `itm_llave_salida`), y las
direcciones son N, S, E, O como en P1.

### Historia de usuario 1 — Saber si la cripta se puede ganar y en qué orden conseguir las llaves (Prioridad 1)

Como jugador, antes de empezar quiero saber si la cripta se puede ganar y, si se puede, un orden de
llaves que me lleve a la salida.

**Por qué esta prioridad**: es el núcleo de la capacidad; el reporte de lo que falla y la integración
con el inicio de partida se construyen sobre esta respuesta.

**Prueba independiente**: con criptas sintéticas pequeñas (esqueleto y ubicación de llaves armados
para cada caso, sin red), se verifica y se compara el resultado y el orden con lo esperado.

**Escenarios de aceptación**:

1. **Dada** una cripta con sala 1 inicial, sala 4 de salida, `c` en la sala 1, `a` en la sala 2, la
   salida 1–2 abierta, la 2–3 cerrada pidiendo `a`, `b` y `salida` en la sala 3 y la 3–4 cerrada
   pidiendo `salida`, **cuando** se verifica, **entonces** es resoluble y el orden es `a`, `c`, `b`,
   `salida`: primero, por id, las que se obtienen sin llaves; luego, por id, las que se vuelven
   obtenibles con ellas. Se muestra como dos rondas, la primera `a`, `c` y la segunda `b`,
   `salida`, solo con ids. *(FR-301, FR-305, FR-306, FR-308)*
2. **Dada** una cripta con varios órdenes válidos de obtención de llaves, **cuando** se verifica dos
   veces, **entonces** ambas ejecuciones dan exactamente el mismo orden; y lo mismo si la ubicación
   de las llaves llega en otro orden. *(FR-308, FR-320)* — Apéndice B.
3. **Dada** una llave que está en el campo `suelta` de un enemigo errante que inicia en la sala 5,
   con `{ "id": "itm_llave_a", "sala": 5, "enemigo": "e-501" }` en la ubicación, **cuando** se
   verifica, **entonces** la llave se considera obtenible en la sala 5 (la sala donde inicia el
   enemigo, aunque sea un errante que después se mueva) y la verificación no pide el contenido de
   ninguna sala. *(FR-303, FR-304, FR-321)* — Apéndice B.
4. **Dada** una salida cerrada sin llave entre la región alcanzable y la sala donde está
   `salida`, **cuando** se verifica, **entonces** esa salida se cruza y la llave es obtenible.
   *(FR-303)*
5. **Dada** una cripta cuyas salidas tienen trampas o cierre automático, **cuando** se verifica,
   **entonces** el resultado es el mismo que sin trampas ni cierres automáticos; y los costos de las
   salidas no cambian el resultado. *(FR-303)*
6. **Dada** la sala 1 inicial, una salida sin vuelta de la sala 2 a la sala 1 como única conexión
   entre ambas y la llave `salida` solo en la sala 2, **cuando** se verifica, **entonces** `salida`
   no es obtenible y la cripta no es resoluble: la salida sin vuelta solo se cruza de 2 a 1.
   *(FR-303, FR-305)*
7. **Dada** una llave que aparece en dos ubicaciones, una alcanzable y otra no, **cuando** se
   verifica, **entonces** la llave es obtenible. *(FR-304)*
8. **Dada** una llave que está en la ubicación pero que ninguna puerta pide, alcanzable desde la
   sala inicial, **cuando** la cripta es resoluble, **entonces** esa llave aparece también en el
   orden. *(FR-306)*
9. **Dada** una cripta en la que `sala_salida` se alcanza solo por una salida abierta, aunque
   `salida` sea obtenible, **cuando** se verifica, **entonces** no es resoluble (no se llega a
   través de una puerta que pida `llave_salida`). *(FR-305, FR-317)*

---

### Historia de usuario 2 — Entender por qué la cripta no se puede ganar (Prioridad 2)

Como jugador, si la cripta no se puede ganar quiero un reporte que diga qué llaves faltan, qué
puertas lo bloquean, dónde están esas llaves y qué ciclo de llaves lo impide.

**Por qué esta prioridad**: el enunciado exige explicar el porqué; depende de la historia 1 y sale
del mismo recorrido.

**Prueba independiente**: con criptas sintéticas no resolubles armadas para cada caso, se compara
cada parte del reporte con lo esperado.

**Escenarios de aceptación**:

1. **Dada** una cripta con sala 1 inicial, sala 2 de salida, la salida E de 1 a 2 cerrada pidiendo
   `salida` y `salida` ubicada en la sala 2, **cuando** se verifica, **entonces** no es resoluble y
   el reporte dice: llave no obtenible `salida`; frontera: sala 1, E, sala 2, llave `salida`;
   `salida` está en la sala 2; ciclo `salida` → `salida`. *(FR-309, FR-310, FR-311, FR-312,
   FR-314, FR-315)* — Apéndice B.
2. **Dada** una cripta con sala 1 inicial, la salida N de 1 a 2 cerrada pidiendo `b`, la salida S de
   1 a 3 cerrada pidiendo `a`, `a` en la sala 2 y `b` en la sala 3, **cuando** se verifica,
   **entonces** el reporte muestra `a` depende de `b`, `b` depende de `a` y un único ciclo
   `a` → `b` → `a`, que empieza por la llave de menor id. *(FR-314, FR-315)*
3. **Dada** una puerta de la frontera que pide la llave `x`, que no aparece en la ubicación de las
   llaves, **cuando** se verifica, **entonces** el reporte dice que `x` no está en la cripta y que no
   depende de ninguna llave. *(FR-311, FR-312, FR-314)*
4. **Dada** una llave no obtenible ubicada en una sala a la que no se llega ni abriendo todas las
   puertas (solo hay salidas sin vuelta que salen de ella), **cuando** se verifica, **entonces** el
   reporte dice que esa llave no depende de ninguna porque su sala no se alcanza ni abriendo todas
   las puertas, y no forma parte de ningún ciclo. *(FR-314)*
5. **Dada** una llave `c` ubicada en la sala 7, a la que se llega por un camino que cruza una sola
   puerta bloqueada (pide `b`) y por otro que cruza dos (la primera pide `a`), **cuando** se
   verifica, **entonces** `c` depende de `b`. *(FR-314)*
6. **Dada** una llave `c` a la que se llega por dos caminos que cruzan una sola puerta bloqueada
   cada uno, una que pide `e` y otra que pide `d`, **cuando** se verifica, **entonces** `c` depende
   de `d` (empate: la de menor id). *(FR-314)*
7. **Dada** una llave `c` que depende de `a`, en una cripta donde `a` → `b` → `a` es un ciclo,
   **cuando** se verifica, **entonces** el reporte muestra la dependencia de `c` pero el ciclo
   reportado es solo `a` → `b` → `a`. *(FR-314, FR-315)*
8. **Dada** una cripta en la que `salida` es obtenible pero ninguna puerta que la pide lleva a
   `sala_salida` desde la región alcanzable, **cuando** se verifica, **entonces** el reporte lo dice
   expresamente. *(FR-317)*
9. **Dada** una cripta que no define `sala_salida` o no define `llave_salida`, **cuando** se
   verifica, **entonces** no es resoluble y el reporte dice cuál de los dos falta. *(FR-302, FR-318)*
10. **Dada** una puerta cerrada que pide una llave no obtenible pero que une dos salas de la región
    alcanzable, **cuando** se verifica, **entonces** esa puerta no aparece en la frontera. *(FR-310)*
11. **Dada** una cripta no resoluble, **cuando** se verifica dos veces, o con la ubicación de las
    llaves o las páginas del esqueleto en otro orden, **entonces** el reporte es idéntico, en
    contenido y en orden. *(FR-316, FR-320)*

---

### Historia de usuario 3 — La verificación al iniciar una partida (Prioridad 3)

Como jugador, al iniciar una partida veo el resultado de la verificación: si se puede ganar, el
orden de llaves; si no, el reporte, y la partida no empieza salvo que lo fuerce.

**Por qué esta prioridad**: es como el jugador usa la capacidad en el juego (P2 §3.5, §7.3);
depende de las historias 1 y 2.

**Prueba independiente**: se inicia la partida con criptas resolubles y no resolubles, en línea y sin
conexión, con y sin `--forzar`, y se comprueba qué se muestra, si la partida inicia, qué solicitudes
se hacen y qué queda en disco.

**Escenarios de aceptación**:

1. **Dada** una cripta no resoluble, **cuando** se inicia la partida sin `--forzar`, **entonces** se
   muestra el reporte, la partida no inicia, no se crea `partida.log` y el programa termina con
   código 2. *(FR-325)* — Apéndice B.
2. **Dada** una cripta no resoluble, **cuando** se inicia con `--forzar`, **entonces** se muestra el
   reporte y la partida inicia normalmente. *(FR-325)*
3. **Dada** una cripta resoluble, **cuando** se inicia la partida, **entonces** se muestra el orden
   de llaves y la partida inicia. *(FR-325)*
4. **Dada** una cripta sin copia local de la ubicación de las llaves, **cuando** se inicia en línea,
   **entonces** se hace una solicitud de ubicación de llaves, se cuenta en el presupuesto de
   solicitudes y se guarda con la copia local de la cripta junto con su versión. *(FR-322, FR-323)*
5. **Dada** una copia local de la ubicación de las llaves con la misma versión de la cripta,
   **cuando** se vuelve a iniciar, **entonces** no se vuelve a pedir; **y dada** una copia con otra
   versión, **entonces** se invalida por la validación de versión y se pide de nuevo. *(FR-323)*
6. **Dado** el modo sin conexión con la ubicación de las llaves en la copia local, **cuando** se
   inicia, **entonces** se verifica sin ninguna solicitud. **Dado** el modo sin conexión (o una
   falla de red) sin esa ubicación, **cuando** se inicia, **entonces** se avisa que no se pudo
   verificar, se trata como no resoluble y la partida solo inicia con `--forzar`; sin `--forzar`, el
   programa termina con código 1. *(FR-324, FR-325)*
7. **Dada** una ubicación de llaves con una llave en una sala que no existe en el esqueleto,
   **cuando** se inicia, **entonces** se rechaza la cripta como dato inválido con un mensaje que
   indica la llave y la sala, no se inicia la partida, aun con `--forzar`, y el programa termina con
   código 1. *(FR-319, FR-325)*
8. **Dada** una verificación en cualquier modo, **cuando** termina, **entonces** no se pidió el
   contenido de ninguna sala. *(FR-321)*
9. **Dado** un `partida.log` de una partida iniciada con `--forzar` sobre una cripta no resoluble,
   **cuando** se reproduce con `--replay`, **entonces** no se verifica, no se muestra el reporte y la
   reproducción da la misma partida. *(FR-326)*
10. **Dada** una partida en curso, **cuando** se guarda y se carga o se usa el pergamino de
    retroceso, **entonces** el resultado de la verificación no forma parte del estado guardado ni
    del revertido, y cargar una partida guardada no vuelve a verificar. *(FR-326, FR-327)*
11. **Dada** una cripta no resoluble cuyo reporte nombra salas que el jugador no ha explorado,
    **cuando** se inicia con `--forzar`, **entonces** el reporte se muestra completo y, ya en la
    partida, esas salas siguen desconocidas en el mapa conocido (salvo que lo cambie la exploración
    normal). *(FR-325)*

---

### Historia de usuario 4 — Verificar sin jugar con `--verificar` (Prioridad 4)

Como grupo (y como profesor en la revisión), quiero verificar una cripta desde la línea de comandos
sin jugar, y que el código de salida diga el resultado.

**Por qué esta prioridad**: es el modo que exige P2 §3.5; reutiliza las historias 1 y 2.

**Prueba independiente**: se ejecuta `--verificar` con criptas resolubles, no resolubles e inválidas
y se comprueba la salida, el código de salida y que no se crea nada de la partida.

**Escenarios de aceptación**:

1. **Dada** una cripta resoluble, **cuando** se ejecuta `--verificar <cripta>`, **entonces** imprime
   que es resoluble y el orden de llaves, y termina con código 0. *(FR-328, FR-329)*
2. **Dada** una cripta no resoluble, **cuando** se ejecuta `--verificar <cripta>`, **entonces**
   imprime el reporte y termina con código 2. *(FR-328, FR-329)*
3. **Dada** una falla de red, una cripta con datos inválidos, o el modo sin conexión sin la ubicación
   de las llaves en la copia local, **cuando** se ejecuta `--verificar <cripta>`, **entonces**
   imprime el motivo y termina con código 1. *(FR-329)*
4. **Cuando** se ejecuta `--verificar <cripta>`, **entonces** no se instancia la vista, no se crea
   ninguna partida ni `partida.log`. *(FR-328)*
5. **Cuando** se ejecuta `--verificar <cripta>` en línea, **entonces** las solicitudes que hace
   (esqueleto si no está en la copia local, ubicación de las llaves) cuentan en el presupuesto y lo
   descargado se guarda en la copia local como en un inicio normal. *(FR-322, FR-323, FR-328)*
6. **Cuando** se ejecuta `--verificar <cripta>` junto con `--replay` o con `--bench`, **entonces**
   el programa termina con código 1 sin verificar; **y cuando** se agrega `--forzar` a
   `--verificar` o a `--replay`, **entonces** el resultado es el mismo que sin `--forzar`.
   *(FR-336)*

---

### Historia de usuario 5 — Medición con `--bench` (Prioridad 5)

Como grupo, quiero medir con `--bench` el recorrido incremental frente a repetir el recorrido por
cada llave, para defender la decisión con datos.

**Por qué esta prioridad**: no cambia el juego, pero es requisito de evaluación (P2 §5.4, §6.3) y
respalda los requisitos de rendimiento.

**Prueba independiente**: se ejecuta `--bench` dos veces con la misma semilla y se comprueba que
genera las mismas criptas, que incluye ambas alternativas, que coinciden en el resultado y que no
instancia la vista ni usa la red.

**Escenarios de aceptación**:

1. **Dada** una semilla, **cuando** se ejecuta `--bench` dos veces, **entonces** las criptas
   sintéticas de resolubilidad (salas, salidas, puertas, llaves y ubicaciones) son idénticas.
   *(FR-330)*
2. **Cuando** se ejecuta `--bench`, **entonces** reporta el tiempo del recorrido incremental y el de
   repetir el recorrido por cada llave obtenida, en criptas con muchas llaves encadenadas y de
   varios tamaños. *(FR-331)*
3. **Cuando** se ejecuta `--bench`, **entonces** comprueba que ambas alternativas dan el mismo
   resultado (resoluble o no, orden y reporte) y reporta cualquier diferencia como error. *(FR-332)*
4. **Dada** una cripta sintética de 2 000 salas con 500 llaves encadenadas, **cuando** `--bench`
   mide la verificación, **entonces** tarda menos de 200 ms. *(FR-334)*
5. **Cuando** `--bench` mide la verificación incremental con criptas de tamaño n, 2n y 4n,
   **entonces** al duplicar el tamaño el tiempo no pasa de 3 veces el anterior. *(FR-335)*
6. **Cuando** se ejecuta `--bench`, **entonces** no instancia la vista ni hace solicitudes de red.
   *(FR-333)*

---

### Casos borde

- **Llave obtenible ubicada detrás de su propia puerta pero también en otra ubicación alcanzable**:
  es obtenible (FR-304).
- **`sala_inicial` es `sala_salida`**: igual hay que llegar a ella cruzando una puerta que pida
  `llave_salida` (FR-305).
- **Puerta hacia `sala_salida` que pide otra llave, obtenible**: no cuenta para ganar; si es la
  única, no es resoluble y aplica FR-317 cuando `llave_salida` es obtenible (FR-305, FR-317).
- **Llave sin ninguna ubicación**: no obtenible; si está en la frontera, el reporte dice que no está
  en la cripta; no depende de ninguna (FR-311, FR-314).
- **Llave de la ubicación que ninguna puerta pide**: si es obtenible entra en el orden; si no, en la
  lista de no obtenibles (FR-306, FR-309).
- **Puerta cerrada que pide una llave no obtenible y une dos salas alcanzables**: no es frontera
  (FR-310).
- **Llave ubicada en una sala inexistente**: dato inválido; se rechaza la cripta y no se inicia la
  partida, ni siquiera con `--forzar` (FR-319).
- **Respuesta de ubicación de llaves mal formada** (sin id o sin sala, sala no entera): dato
  inválido, igual que el caso anterior (FR-319).
- **Sin conexión y sin ubicación de llaves local**: aviso, no resoluble, solo inicia con `--forzar`;
  en `--verificar`, código 1 (FR-324, FR-329).
- **Presupuesto de solicitudes agotado antes de pedir la ubicación de las llaves**: igual que sin
  conexión: aviso, no resoluble (FR-322, FR-324).
- **Ciclos y cadenas que llegan a un ciclo**: solo se reporta el ciclo, una vez, desde su llave de
  menor id; las llaves que llegan a él muestran su dependencia pero no se reportan como ciclo
  (FR-315).
- **Llave cuya sala no se alcanza ni abriendo todas las puertas** (por salidas sin vuelta): no
  depende de ninguna y el reporte lo dice (FR-314).

## Requisitos *(obligatorio)*

Los identificadores son estables y no se renumeran (constitución, principio IX). Usan la serie 300
para no chocar con las otras capacidades.

### Requisitos funcionales — Reglas de la verificación

- **FR-301**: Antes de iniciar una partida, el programa DEBE determinar si la cripta es resoluble
  usando únicamente el esqueleto y la ubicación de las llaves (P2 §3.5, §4.2).
- **FR-302**: Una cripta que no define `sala_salida` o no define `llave_salida` NO DEBE considerarse
  resoluble (tampoco se puede ganar según P1).
- **FR-303**: La verificación DEBE suponer que: se cruza toda salida abierta, toda salida cerrada sin
  llave y toda salida cerrada cuya llave ya se obtuvo; las llaves no se consumen; todo enemigo se
  puede derrotar; las trampas y los cierres automáticos no bloquean. Una salida sin vuelta DEBE
  cruzarse solo en su sentido. Los costos de las salidas NO DEBEN influir en el resultado. La
  región alcanzable DEBE ser todo lo que se alcanza desde `sala_inicial` bajo estos supuestos, y se
  DEBE suponer que el jugador puede volver a cualquier sala de la región, aunque haya cruzado una
  salida sin vuelta (límite documentado en Supuestos).
- **FR-304**: Una llave DEBE considerarse obtenible si al menos una de sus ubicaciones está en la
  región alcanzable. Una llave que suelta un enemigo DEBE considerarse ubicada en la sala donde ese
  enemigo inicia, según la ubicación de las llaves.
- **FR-305**: Una cripta DEBE ser resoluble si, partiendo de `sala_inicial` y bajo los supuestos de
  FR-303, `llave_salida` es obtenible y existe una salida cerrada que pide `llave_salida`, sale de
  una sala de la región alcanzable y lleva a `sala_salida`. En cualquier otro caso NO es resoluble.

### Requisitos funcionales — Orden de llaves

- **FR-306**: Si la cripta es resoluble, la verificación DEBE dar un orden con todas las llaves
  obtenibles, cada una una sola vez. El orden DEBE mostrarse solo con los ids de las llaves,
  agrupados por ronda (FR-308) en el orden de las rondas, sin sus ubicaciones.
- **FR-307**: En el orden, cada llave DEBE aparecer después de todas las llaves necesarias para
  alcanzar alguna de sus ubicaciones.
- **FR-308**: El orden DEBE construirse por rondas: primero, ordenadas por id, las llaves que se
  obtienen sin ninguna llave; luego, ordenadas por id, las que se vuelven obtenibles con las llaves
  de las rondas anteriores; y así hasta que ninguna llave nueva se vuelva obtenible. Los ids se
  comparan como texto, carácter por carácter.

### Requisitos funcionales — Reporte de una cripta no resoluble

- **FR-309**: Si la cripta no es resoluble, el reporte DEBE listar, ordenadas por id, todas las
  llaves de la cripta que no son obtenibles.
- **FR-310**: El reporte DEBE listar la frontera bloqueada: cada salida cerrada que sale de una sala
  de la región alcanzable hacia una sala que no es de ella y pide una llave no obtenible, con sala
  de origen, dirección, sala destino y llave. El orden DEBE ser por id de sala de origen y luego por
  dirección en el orden N, S, E, O.
- **FR-311**: Para cada llave distinta que pide alguna puerta de la frontera, ordenadas por id, el
  reporte DEBE indicar todas sus ubicaciones (sala, y enemigo si la suelta uno), ordenadas por sala y
  luego por id de enemigo, o que la llave no está en la cripta si no tiene ninguna ubicación. Dentro
  de la misma sala, primero la ubicación sin enemigo y después las que tienen enemigo, por id de
  enemigo.
- **FR-312**: El reporte DEBE indicar, para cada llave no obtenible, de qué llave depende según
  FR-314, o que no depende de ninguna y por qué (no está en la cripta, o su sala no se alcanza ni
  abriendo todas las puertas).
- **FR-313**: Toda la información del reporte (región alcanzable, llaves obtenibles, frontera,
  dependencias y ciclos) DEBE salir del mismo recorrido de la verificación, sin repetir el
  recorrido por cada llave.
- **FR-314**: Una llave no obtenible DEBE depender de la llave de la primera puerta bloqueada del
  camino que cruza menos puertas bloqueadas desde la región alcanzable hasta alguna de sus
  ubicaciones; si varios caminos empatan en esa cantidad, DEBE depender de la de menor id entre sus
  primeras puertas bloqueadas. Si ninguna de sus ubicaciones se alcanza ni abriendo todas las
  puertas (respetando el sentido de las salidas sin vuelta), o si no tiene ubicación, NO DEBE
  depender de ninguna.
- **FR-315**: El reporte DEBE listar cada ciclo de dependencia (A → B → … → A, incluido el de una
  llave que depende de sí misma) una sola vez, empezando por su llave de menor id y siguiendo las
  dependencias; los ciclos DEBEN listarse ordenados por esa primera llave. Las llaves que llegan a un
  ciclo sin pertenecer a él NO DEBEN reportarse como parte del ciclo.
- **FR-316**: El reporte DEBE presentar sus partes en este orden: resultado, llaves no obtenibles
  (FR-309), frontera (FR-310), ubicación de las llaves de la frontera (FR-311), dependencias
  (FR-312), ciclos (FR-315) y, si aplica, FR-317 o FR-318.
- **FR-317**: Si `llave_salida` es obtenible pero ninguna salida que la pide lleva a `sala_salida`
  desde la región alcanzable, el reporte DEBE decirlo expresamente.
- **FR-318**: Si la cripta no define `sala_salida` o `llave_salida`, el reporte DEBE decir cuál falta;
  el resto del reporte se calcula igual con lo que la cripta sí define.

### Requisitos funcionales — Datos y validación

- **FR-319**: Si la ubicación de las llaves trae una llave en una sala que no existe en el esqueleto,
  o una entrada mal formada (sin id, sin sala, o sala no entera), el programa DEBE rechazar la cripta
  como dato inválido, con un mensaje que indique la entrada y el problema, igual que la capacidad
  001 con los costos inválidos. Con datos inválidos la partida NO DEBE iniciar, aun con `--forzar`.
- **FR-320**: El resultado de la verificación (resoluble o no, orden y reporte completo) DEBE ser
  determinista: la misma versión de cripta y la misma ubicación de llaves DEBEN dar exactamente el
  mismo texto, sin importar el orden de la ubicación de las llaves ni el de las páginas o salidas
  del esqueleto.
- **FR-321**: La verificación NO DEBE pedir el contenido de ninguna sala.
- **FR-322**: La consulta de ubicación de llaves DEBE contar en `presupuesto_solicitudes`. Si no se
  puede hacer porque el presupuesto está agotado, se trata como en FR-324.
- **FR-323**: La ubicación de las llaves DEBE guardarse con la copia local de la cripta junto con su
  versión, reutilizarse sin nueva solicitud mientras coincida la versión, e invalidarse mediante la
  validación de versión cuando no coincida (P2 Apéndice A).
- **FR-324**: Si no se puede obtener la ubicación de las llaves (sin conexión, falla de red o
  presupuesto agotado) y no está en la copia local válida, el programa DEBE avisar que no pudo
  verificar y tratar la cripta como no resoluble.

### Requisitos funcionales — Inicio de partida y estado del juego

- **FR-325**: Al iniciar una partida: si la cripta es resoluble, DEBE mostrarse el orden de llaves y
  la partida inicia; si no lo es (incluido FR-324), DEBE mostrarse el reporte (o el aviso) y la
  partida NO DEBE iniciar ni crear `partida.log`, salvo con `--forzar`, en cuyo caso se muestra lo
  mismo y la partida inicia normalmente. Cuando la partida no inicia, el programa DEBE terminar con
  los mismos códigos que `--verificar` (FR-329): 2 si la cripta no es resoluble, y 1 si no se pudo
  verificar (sin la ubicación de las llaves, falla de red o datos inválidos, FR-319). El reporte DEBE mostrarse completo (con salas, direcciones y salas destino), como excepción
  declarada a la niebla de guerra (P2 §3.3); ni el reporte ni el orden de llaves DEBEN cambiar el mapa
  conocido del jugador: ninguna sala pasa a explorada ni a avistada por aparecer en ellos.
- **FR-326**: `--replay` NO DEBE verificar ni mostrar el reporte, y cargar una partida guardada NO
  DEBE volver a verificar: esas partidas ya empezaron (quizá con `--forzar`).
- **FR-327**: El resultado de la verificación NO DEBE ser estado del juego: no se guarda en el
  archivo de partida, no se registra en `partida.log` como acción y el pergamino de retroceso no lo
  modifica.

### Requisitos funcionales — Modo `--verificar`

- **FR-328**: `--verificar <cripta>` DEBE ejecutar solo la verificación e imprimir el resultado (el
  orden si es resoluble, el reporte si no), sin instanciar la vista, sin crear ninguna partida y sin
  crear `partida.log`.
- **FR-329**: `--verificar` DEBE terminar con código 0 si la cripta es resoluble, 2 si no lo es y 1
  si hubo un error que impidió verificar (red, datos inválidos o falta de la ubicación de las llaves
  sin conexión), imprimiendo el motivo.
- **FR-336**: `--verificar` junto con `--replay` o con `--bench` es un error de uso: el programa
  termina con código 1 sin verificar. `--forzar` no tiene efecto con `--verificar` ni con
  `--replay`.

### Requisitos funcionales — Medición

- **FR-330**: `--bench` DEBE generar criptas sintéticas de resolubilidad, con muchas llaves
  encadenadas, de forma determinista por semilla.
- **FR-331**: `--bench` DEBE medir el recorrido incremental frente a repetir el recorrido de la
  cripta por cada llave obtenida, en varios tamaños de cripta.
- **FR-332**: `--bench` DEBE comprobar que ambas alternativas dan el mismo resultado (resoluble o no,
  orden y reporte) y reportar cualquier diferencia como error.
- **FR-333**: `--bench` DEBE ejecutarse sin instanciar la vista y sin red.

### Requisitos de rendimiento

Medidos en el equipo local, sin red ni renderizado (P2 §6.1; constitución, principio VI).

- **FR-334**: La verificación completa (orden o reporte) DEBE tardar menos de 200 ms con la cripta
  publicada más grande; mientras no se publique, con una cripta sintética de 2 000 salas (el mismo
  tamaño de referencia de la capacidad 001) y 500 llaves encadenadas. La medición empieza con el
  esqueleto ya cargado y la ubicación de las llaves en memoria (cargar el esqueleto es de P1 y de la
  capacidad 001); `--bench` reporta la carga aparte, sin límite.
- **FR-335**: El costo total de la verificación DEBE crecer aproximadamente de forma lineal con salas
  + salidas + llaves, sin repetir el recorrido por cada llave obtenida. Se verifica con `--bench`
  midiendo tamaños n, 2n y 4n: al duplicar el tamaño, el tiempo no pasa de 3 veces el anterior
  (lo lineal da cerca de 2; repetir el recorrido por cada llave da cerca de 4).

### Entidades clave

- **Ubicación de una llave**: id de llave, sala y, opcionalmente, id del enemigo que la suelta.
  Proviene del servicio, vale mientras coincida la versión de la cripta.
- **Resultado de la verificación**: resoluble o no; si lo es, el orden de llaves; si no, el reporte.
- **Reporte**: llaves no obtenibles, frontera bloqueada, ubicación de las llaves de la frontera,
  dependencias, ciclos y avisos (FR-317, FR-318, FR-324).
- **Puerta de la frontera**: sala de origen, dirección, sala destino y llave que pide.
- **Dependencia**: par (llave no obtenible, llave de la que depende) o la indicación de que no
  depende de ninguna y por qué.
- **Ciclo de dependencia**: secuencia de llaves que empieza y termina en su llave de menor id.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-301**: El 100 % de los escenarios de aceptación de esta especificación, incluidos los cuatro
  casos de «Resolubilidad» del Apéndice B, tienen una prueba automatizada que cita su FR y pasa.
- **SC-302**: En criptas sintéticas generadas por semilla (al menos 200), el resultado incremental
  coincide al 100 % con el de repetir el recorrido por cada llave, y cada orden de llaves se puede
  seguir paso a paso: cada llave se alcanza con las anteriores.
- **SC-303**: La verificación de una cripta sintética de 2 000 salas y 500 llaves encadenadas (y de
  la cripta publicada más grande, cuando exista) tarda menos de 200 ms según `--bench`.
- **SC-304**: Según `--bench`, al duplicar el tamaño de la cripta el tiempo de la verificación
  incremental no pasa de 3 veces el anterior, mientras que la alternativa de repetir el recorrido
  por llave muestra su crecimiento mayor en la misma tabla.
- **SC-305**: Dos ejecuciones de la verificación sobre la misma cripta, con la ubicación de las
  llaves en cualquier orden, producen el mismo texto, byte por byte.
- **SC-306**: Ninguna verificación pide contenido de salas; iniciar dos veces la misma versión de una
  cripta hace como máximo una solicitud de ubicación de llaves.
- **SC-307**: Todas las pruebas de la primera parte y de la capacidad 001 siguen pasando, y
  `--replay` de partidas existentes da el mismo resultado. Las que inician una partida sin conexión
  necesitan la ubicación de las llaves en sus datos de prueba (FR-324): solo se ajustan esos datos,
  no lo que las pruebas comprueban. Única excepción: las pruebas en línea que cuentan las
  solicitudes exactas de una partida (o fijan el presupuesto justo para un escenario) suben en una,
  por la consulta de ubicación de llaves (FR-322).
- **SC-308**: En la revisión, con una cripta nueva no resoluble, cualquier integrante puede señalar
  en el reporte la llave que falta, la puerta que bloquea y el ciclo, sin consultar nada adicional.

## Supuestos

- Esta especificación no cubre la niebla de guerra, «ir a» ni la línea de tiempo. La verificación
  usa el esqueleto completo, que es infraestructura (P2 §3.3), y no depende del mapa conocido del
  jugador.
- La verificación confía en la ubicación de las llaves del servicio: no comprueba que el enemigo
  indicado exista ni que inicie en esa sala, porque eso exigiría pedir el contenido de la sala
  (FR-321).
- Validar el esqueleto (salas, salidas, `sala_inicial`) sigue siendo responsabilidad de P1 y de la
  capacidad 001; aquí solo se agrega la validación de la ubicación de las llaves (FR-319).
- Que una partida iniciada con `--forzar` quede reproducible no requiere nada nuevo: `--replay` no
  verifica (FR-326).
- El umbral de FR-335 y SC-304 («no pasa de 3 veces al duplicar») es una meta del grupo para hacer
  verificable el «aproximadamente lineal» de P2 §5.4.
- **Límite conocido (salidas sin vuelta)**: la verificación supone que el jugador puede volver a
  cualquier sala de la región alcanzable (FR-303). Con salidas sin vuelta, puede decir «resoluble»
  en una cripta donde el jugador queda atrapado (por ejemplo, cruza de la sala 1 a la 2 por una
  salida sin vuelta, toma la llave y ya no puede volver a la puerta que ella abre en la sala 1).
  Modelar dónde está el jugador obligaría a probar órdenes de obtención de llaves, que en el peor
  caso crece de forma exponencial, y rompería el costo lineal que exige P2 §5.4 (FR-335).
- Si el profesor publica la cripta más grande o ajusta el límite de 200 ms por enmienda (P2 §2.7), se
  actualiza FR-334.
