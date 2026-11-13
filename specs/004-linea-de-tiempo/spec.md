# Especificación de capacidad: Línea de tiempo

**Capacidad**: 004 — `004-linea-de-tiempo`

**Creada**: 2026-11-12

**Estado**: Borrador

**Fuentes**: P2 §3.6, §5.5, §6.1, §6.3, §7.2, §7.3 y Apéndice B («Línea de tiempo»). Reglas
heredadas de P1 (§2.3, §2.11, §4.6, §4.10, §4.11) y de la capacidad 001 (límite de 20 ms por ciclo).

**Entrada**: descripción del grupo en `/speckit-specify` (registrada en `PROMPTS_LLM.md`).

## Contexto: por qué existe esta capacidad

El pergamino de retroceso solo deshace las últimas 5 acciones y cambia la partida. La línea de
tiempo es otra cosa: permite mirar, sin tocar nada, cómo estaba la partida en cualquier instante
desde el inicio (dónde estaba el jugador, cuánta vida tenía, qué llevaba, qué enemigos tenía al
frente y qué conocía del mapa). Sirve al jugador para entender qué pasó y al grupo para depurar y
reportar errores, en la partida en curso o reproduciendo un `partida.log`.

### Glosario

- **Instante**: valor del reloj virtual de la partida (P1 §2.3), entero mayor o igual que 0.
- **Acción del jugador**: cada decisión del jugador que P1 cuenta como acción; las acciones
  deshechas con un pergamino dejan de contar, y usar el pergamino no es una acción (P1 §2.11: cada
  uso revierte una acción). La acción número k es la k-ésima de las que quedan.
- **Estado en el instante t**: el estado de la partida después de ejecutar todos los eventos con
  tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo
  antes de esa decisión: los eventos del mismo instante que en la agenda vienen después de la
  decisión no se incluyen.
- **Estado antes de la acción #k**: el estado justo antes de que el jugador tome su acción número k.
  El de #(n + 1), con n acciones del jugador, es el estado actual.
- **Línea de tiempo**: la historia de la partida tal como quedó, sin las acciones revertidas, que
  permite reconstruir el estado en cualquier instante desde 0 hasta el reloj actual.
- **Punto de control**: copia completa del estado de la partida en un momento dado, incluido el
  estado del generador aleatorio si la reconstrucción re-simula.
- **K**: cantidad mínima de acciones del jugador entre dos puntos de control consecutivos;
  se configura con `--checkpoint-cada K`.
- **Resumen**: lo que se muestra de un estado consultado (FR-406).

## Aclaraciones

### Sesión 2026-11-12

- P: ¿El resumen muestra el reloj actual de la partida o el del estado consultado? → R: El del estado
  consultado, junto con el instante consultado, para que `historia`, `--replay … --hasta` y una carga
  posterior den exactamente el mismo texto; si la vista muestra el reloj actual, va fuera del
  resumen (FR-406).
- P: ¿Una consulta puede hacer solicitudes de red? → R: No: no hace solicitudes ni gasta presupuesto
  de solicitudes (FR-407, HU1-12).
- P: ¿Con qué partida sintética mide `--bench` los 50 ms de `historia`? → R: La cripta de 2 000
  salas con 50 cazadores activos de la 001, con 5 000 acciones del jugador que mezclan movimientos,
  ataques, recoger y usar objetos y algunos pergaminos; el jugador tiene vida de sobra para que la
  partida no termine antes (como en el bench del ciclo de P1). La alternativa sin puntos de control
  se puede medir con menos consultas, porque cada una puede reconstruir toda la partida (FR-427,
  FR-428, FR-432).
- P: ¿Con qué código termina `--replay … --hasta t`? → R: 0 siempre que muestra un resumen, también
  si t es posterior al final del log (con su aviso); 1 si el log no se puede leer o reproducir,
  igual que `--replay` hoy (FR-415).
- P: ¿Con qué umbral se comprueba que la memoria crece con los cambios y no con acciones × tamaño del
  estado? → R: De 2 500 a 5 000 acciones con el mismo K, la memoria no pasa de 2,5 veces; y con el K
  por defecto es menor que un tercio de la de copiar el estado completo en cada acción (FR-434).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 — Consultar el pasado durante la partida (Prioridad 1)

Como jugador, durante la partida quiero escribir `historia <t>` o `historia #k` y ver cómo estaba
la partida en ese momento, sin que la consulta cambie nada.

**Por qué esta prioridad**: es la capacidad que pide el enunciado (P2 §3.6, §7.3); todo lo demás
(pergamino, persistencia, puntos de control) sirve para que esta consulta sea correcta y rápida.

**Prueba independiente**: se juega una partida sintética corta con comandos fijos, se consultan
varios instantes y acciones, y se compara cada resumen con el estado obtenido al reproducir la
misma partida desde el inicio hasta ese punto.

**Escenarios de aceptación**:

1. **Dada** una partida en curso con reloj 1 200, **cuando** el jugador escribe `historia 500`,
   **entonces** se muestra el resumen del estado en el instante 500: instante consultado, reloj de
   ese estado (no el 1 200 actual), número de acción, sala del jugador, vida, ataque, defensa,
   velocidad, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en
   ese momento. *(FR-401, FR-403, FR-406)*
2. **Dada** una partida con reloj 1 200, **cuando** el jugador escribe `historia 1500`,
   **entonces** la consulta se rechaza con un mensaje y no consume tiempo ni cambia nada.
   *(FR-403, FR-405)* — Apéndice B.
3. **Dados** tres eventos que ocurren en el instante 300 (por ejemplo, el ataque de un enemigo, el
   cierre automático de una puerta y el movimiento de un cazador) sin decisión del jugador en ese
   instante, **cuando** se consulta `historia 300`, **entonces** el resumen muestra el estado
   después de los tres. *(FR-401)* — Apéndice B.
4. **Dada** una decisión del jugador en el instante 300 y un evento del mismo instante que en la
   agenda viene después de esa decisión, **cuando** se consulta `historia 300`, **entonces** el
   resumen muestra el estado justo antes de la decisión, sin ese evento. *(FR-401)*
5. **Dada** una partida con 40 acciones del jugador, **cuando** se consulta `historia #1`,
   `historia #20` y `historia #41`, **entonces** se muestra el estado justo antes de la primera
   acción, justo antes de la vigésima y el estado actual, respectivamente. *(FR-402, FR-404)*
6. **Dada** una partida con 40 acciones del jugador, **cuando** se consulta `historia #0` o
   `historia #42`, **entonces** se rechaza con un mensaje y no consume tiempo ni cambia nada.
   *(FR-404, FR-405)*
7. **Cuando** el jugador escribe `historia`, `historia abc`, `historia -5`, `historia 2,5` o
   `historia #x`, **entonces** se trata como comando inválido, igual que en P1, y no cambia nada.
   *(FR-405)*
8. **Dada** una partida en curso, **cuando** el jugador hace varias consultas `historia`,
   **entonces** el reloj no avanza, la consulta no se anota en `partida.log`, no cuenta como
   acción, no cambia lo que el pergamino puede deshacer y no cambia el estado del generador
   aleatorio. *(FR-407)* — Apéndice B.
9. **Dadas** dos partidas con la misma cripta, semilla y acciones, una con 30 consultas `historia`
   intercaladas y otra sin ninguna, **cuando** terminan, **entonces** terminan idénticas: mismo
   estado final, mismo `partida.log` y mismo resultado. *(FR-407, FR-408)*
10. **Dada** una partida terminada (victoria o muerte), **cuando** se intenta `historia`, **entonces**
    no está disponible y se indica que para una partida terminada se usa `--replay … --hasta`.
    *(FR-409)*
11. **Dado** un instante en el que el jugador ya había explorado salas que después cambió de estado
    en su mapa (por ejemplo, una puerta recordada abierta que luego observó cerrada), **cuando** se
    consulta ese instante, **entonces** el mapa conocido que se muestra es el que tenía en ese
    instante, no el actual. *(FR-406)*
12. **Dada** una partida en línea con salas cuyo contenido todavía no se ha descargado, **cuando** el
    jugador hace consultas `historia` de instantes en los que estuvo en esas salas o cerca de ellas,
    **entonces** no se hace ninguna solicitud de red y el contador de solicitudes y el presupuesto
    restante son los mismos antes y después de las consultas. *(FR-407)*

---

### Historia de usuario 2 — La línea de tiempo respeta el pergamino (Prioridad 2)

Como jugador, después de usar un pergamino de retroceso quiero que la historia describa la partida
tal como quedó: lo revertido ya no existe.

**Por qué esta prioridad**: sin esto la consulta mostraría estados que ya no pertenecen a la
partida; depende de la historia 1.

**Prueba independiente**: se juega, se usa un pergamino y se comparan las consultas con las de una
partida idéntica en la que esas acciones nunca se hicieron.

**Escenarios de aceptación**:

1. **Dada** una partida con 30 acciones del jugador, **cuando** usa tres pergaminos seguidos (cada
   uno revierte una acción, P1 §2.11) y luego consulta, **entonces** ninguna consulta muestra
   estados de las 3 acciones revertidas, y `historia #k` se numera con las 27 que quedaron (#28 es
   el estado actual). *(FR-410, FR-411)* — Apéndice B.
2. **Dada** la partida del escenario anterior, **cuando** se consulta `historia <t>` con t mayor que
   el reloj que quedó después del pergamino, **entonces** se rechaza. *(FR-403, FR-410)*
3. **Dada** una partida que usó un pergamino y siguió con acciones nuevas, **cuando** se consulta
   cualquier instante o acción, **entonces** el resumen es igual al de una partida que hizo
   directamente las acciones que quedaron, sin las revertidas. *(FR-410, FR-411)*
4. **Dada** una partida larga, **cuando** se usa un pergamino, **entonces** el recorte de la línea
   de tiempo no recorre toda la historia: su costo no crece con la cantidad de acciones previas.
   *(FR-412)*

---

### Historia de usuario 3 — Consultar un `partida.log` sin jugar (Prioridad 3)

Como grupo (y como profesor en la revisión), quiero reproducir un `partida.log` hasta un instante y
ver el mismo resumen, sin abrir la vista.

**Por qué esta prioridad**: es la forma de inspeccionar una partida terminada o de reportar un error
(P2 §3.6); reutiliza el resumen de la historia 1.

**Prueba independiente**: se reproduce un `partida.log` conocido con distintos `--hasta` y se
compara la salida con el resumen que `historia` dio en la partida original.

**Escenarios de aceptación**:

1. **Dado** un `partida.log`, **cuando** se ejecuta `--replay partida.log --hasta 500`, **entonces**
   se reproduce hasta el instante 500 y se imprime exactamente el mismo texto que dio `historia 500`
   en esa partida, aunque allí el reloj actual fuera otro, sin instanciar la vista. *(FR-406,
   FR-413, FR-414)*
2. **Dado** un `partida.log` de una partida que terminó en el instante 2 000, **cuando** se ejecuta
   `--replay partida.log --hasta 9000`, **entonces** se muestra el estado final, se indica que la
   partida terminó antes de ese instante y el programa termina con código 0. *(FR-415)*
   — Apéndice B.
3. **Dado** un `partida.log` de una partida que no terminó (el log acaba en el instante 2 000),
   **cuando** se ejecuta `--replay partida.log --hasta 9000`, **entonces** se muestra el último
   estado, se indica que el log termina antes de ese instante y el programa termina con código 0.
   **Dado** un log que no se puede leer, **entonces** termina con código 1. *(FR-415)*
4. **Cuando** se ejecuta `--hasta 500` sin `--replay`, o `--hasta` con un valor que no es un entero
   mayor o igual que 0, **entonces** el programa termina con un error de argumentos, sin iniciar
   ninguna partida. *(FR-416)*
5. **Dado** un `partida.log` de una partida que usó un pergamino, **cuando** se reproduce con
   `--hasta`, **entonces** el resumen corresponde a la partida tal como quedó, sin las acciones
   revertidas. *(FR-410, FR-413)*

---

### Historia de usuario 4 — Guardar y cargar con la línea de tiempo (Prioridad 4)

Como jugador, al guardar y cargar quiero conservar toda la historia, y si intento cargar un archivo
viejo quiero que el programa me lo diga en vez de cargarlo mal.

**Por qué esta prioridad**: P2 §3.6 lo exige y el formato del archivo cambia; depende de las
historias 1 y 2.

**Prueba independiente**: se guarda una partida con historia, se carga y se comparan consultas
antes y después; se intenta cargar archivos de formatos anteriores.

**Escenarios de aceptación**:

1. **Dada** una partida con 200 acciones del jugador, **cuando** se guarda y se carga, **entonces**
   toda consulta `historia <t>` y `historia #k` da exactamente el mismo texto que antes de guardar,
   y la partida continúa igual que sin guardar. *(FR-406, FR-417)*
2. **Dada** una partida guardada con K = 10, **cuando** se carga con `--checkpoint-cada 50`,
   **entonces** se avisa que se usa el K guardado (10) y se usa ese. *(FR-418)*
3. **Dado** un archivo de partida guardado por la primera parte, **cuando** se intenta cargar,
   **entonces** se rechaza con un mensaje de formato incompatible y la partida en curso no cambia;
   nunca se carga en silencio. *(FR-419)* — Apéndice B.
4. **Dado** un archivo guardado con el formato anterior de la capacidad 001, **cuando** se intenta
   cargar, **entonces** se rechaza con el mismo tipo de mensaje de incompatibilidad. *(FR-419)*

---

### Historia de usuario 5 — Puntos de control y medición (Prioridad 5)

Como grupo, quiero configurar cada cuántas acciones se guarda un punto de control y medir con
`--bench` la memoria y el tiempo de consulta, para escoger y defender el valor por defecto.

**Por qué esta prioridad**: no cambia lo que el jugador ve, pero es requisito de evaluación (P2
§5.5, §6.3) y respalda los requisitos de rendimiento.

**Prueba independiente**: se juega la misma partida con distintos K y se comprueba que las
consultas dan lo mismo; se ejecuta `--bench` dos veces con la misma semilla y se revisan sus
secciones.

**Escenarios de aceptación**:

1. **Dada** la misma partida jugada con K = 1, K = 10, K = 100 y con el K por defecto, **cuando** se
   consultan los mismos instantes y acciones, **entonces** los resúmenes son idénticos. *(FR-420,
   FR-421)*
2. **Dada** una partida con K = 10, **cuando** se hace cualquier consulta, **entonces** la
   reconstrucción aplica o deshace cambios de a lo sumo 10 acciones del jugador. *(FR-423)*
3. **Dada** una partida de 5 000 acciones con K = 10, **cuando** termina, **entonces** hay a lo sumo
   un punto de control cada 10 acciones del jugador, y fuera de ellos solo se guardaron los
   cambios. *(FR-422, FR-424)*
4. **Cuando** se ejecuta con `--checkpoint-cada 0`, `--checkpoint-cada -3` o `--checkpoint-cada x`,
   **entonces** el programa termina con un error de argumentos. *(FR-420)*
5. **Dada** una semilla, **cuando** se ejecuta `--bench` dos veces, **entonces** las partidas
   sintéticas de la línea de tiempo son idénticas. *(FR-427)*
6. **Cuando** se ejecuta `--bench`, **entonces** reporta memoria y tiempo de consulta para al menos
   tres valores de K, para la alternativa sin puntos de control y para la alternativa de
   reconstrucción descartada, y comprueba que todas dan los mismos resúmenes. *(FR-428, FR-429,
   FR-430)*
7. **Dada** una partida sintética de al menos 5 000 acciones del jugador (FR-427: 2 000 salas,
   50 cazadores, acciones mezcladas, sin que la partida termine) con el K por defecto,
   **cuando** `--bench` mide consultas `historia` repartidas por toda la partida, **entonces** el
   p95 es menor que 50 ms. *(FR-432)*
8. **Dado** el escenario de 50 cazadores de la capacidad 001 con la línea de tiempo activa,
   **cuando** `--bench` mide el ciclo de eventos, **entonces** el p95 sigue por debajo de 20 ms.
   *(FR-433)*
9. **Cuando** `--bench` mide la memoria de la línea de tiempo con partidas de 2 500 y 5 000
   acciones con el mismo K, **entonces** la de 5 000 no pasa de 2,5 veces la de 2 500, y con el K
   por defecto la memoria es menor que un tercio de la de guardar una copia completa del estado en
   cada acción. *(FR-424, FR-434)*
10. **Dadas** partidas de 2 500 y 5 000 acciones con el mismo K, **cuando** `--bench` mide cuántos
    puntos de control examina una consulta para ubicar el más cercano, **entonces** esa cantidad no
    crece en proporción a la cantidad de puntos de control. *(FR-425)*
11. **Dada** la misma cripta, semilla y acciones, **cuando** se juega con la línea de tiempo activa,
    **entonces** el `partida.log`, el estado final y el resultado son los mismos que da la partida
    sin línea de tiempo (por ejemplo, el `--replay` de un log de la 001). *(FR-426)*
12. **Cuando** se ejecuta `--bench`, **entonces** no instancia la vista ni hace solicitudes de red.
    *(FR-431)*

---

### Casos borde

- **`historia 0`**: estado en el instante 0, justo antes de la primera decisión del jugador si le
  toca en 0 (FR-401).
- **`historia <t>` con t igual al reloj actual**: el estado actual (FR-401, FR-403).
- **t entre dos eventos**: el estado después del último evento con tiempo ≤ t (FR-401).
- **Consulta que cae justo en un punto de control**: mismo resumen que cualquier otra (FR-421).
- **Pergamino que revierte acciones posteriores al último punto de control, o que cruza un punto
  de control**: los puntos de control de acciones revertidas dejan de existir junto con ellas
  (FR-410, FR-412).
- **Consulta inmediatamente después de un pergamino**: `#k` vuelve a numerarse con las acciones que
  quedaron (FR-411).
- **Partida terminada**: `historia` no está disponible; se usa `--replay … --hasta` (FR-409).
- **`--hasta` sin `--replay`** o con un valor inválido: error de argumentos (FR-416).
- **Cargar con otro `--checkpoint-cada`**: aviso y se usa el K guardado (FR-418).
- **Archivo de la primera parte o del formato anterior de la 001**: rechazo con mensaje de
  incompatibilidad; no se migra (FR-419).
- **K mayor que la cantidad de acciones de la partida**: solo existe el punto de control inicial (si
  lo hay) y las consultas siguen cumpliendo FR-423 (FR-422, FR-423).

## Requisitos *(obligatorio)*

Los identificadores son estables y no se renumeran (constitución, principio IX). Usan la serie 400
para no chocar con las otras capacidades.

### Requisitos funcionales — Qué se consulta

- **FR-401**: El estado en el instante t DEBE ser el de después de ejecutar todos los eventos con
  tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, DEBE ser el estado
  justo antes de esa decisión, sin los eventos del mismo instante que en la agenda vienen después
  de ella.
- **FR-402**: El estado antes de la acción #k DEBE ser el estado justo antes de que el jugador tome
  su acción número k, contando las acciones como P1 y sin las acciones deshechas.
- **FR-403**: El comando `historia <t>` DEBE aceptar un entero t ≥ 0 y mostrar el resumen del estado
  en el instante t. Si t es mayor que el reloj actual, DEBE rechazarse con un mensaje.
- **FR-404**: El comando `historia #k` DEBE aceptar un entero k entre 1 y n + 1, donde n es la
  cantidad de acciones del jugador; #(n + 1) es el estado actual. Fuera de ese rango DEBE rechazarse
  con un mensaje.
- **FR-405**: Un comando `historia` mal formado (sin argumento, con texto que no es un entero ≥ 0 o
  `#` seguido de algo que no es un entero) DEBE tratarse como comando inválido, igual que en P1. Ni
  un rechazo ni un comando inválido DEBEN consumir tiempo ni cambiar ningún estado.
- **FR-406**: El resumen DEBE mostrar como mínimo: el instante consultado (t, o #k) y el reloj de ese
  estado (el reloj que tenía la partida en él: el tiempo del último evento ejecutado o el de la
  decisión del jugador pendiente), nunca el reloj actual de la partida; número de la próxima acción
  del jugador en ese estado (#k); sala del jugador; vida, ataque, defensa y velocidad; inventario;
  efectos activos; enemigos de esa sala con su vida; y el mapa conocido del jugador tal como era en
  ese estado (el mapa conocido lo define la capacidad 002). El mismo resumen DEBE usarse en
  `historia` y en `--replay … --hasta`, y para un mismo estado DEBE dar exactamente el mismo texto
  en la partida, en `--replay … --hasta` y después de guardar y cargar. Si la vista muestra el reloj
  actual, lo hace fuera del resumen.

### Requisitos funcionales — La consulta no cambia la partida

- **FR-407**: Una consulta `historia` NO DEBE consumir tiempo virtual, NO DEBE contar como acción del
  jugador, NO DEBE anotarse en `partida.log`, NO DEBE cambiar lo que el pergamino puede deshacer y NO
  DEBE cambiar el estado del generador aleatorio ni ningún otro estado del juego. Tampoco DEBE hacer
  solicitudes de red ni gastar presupuesto de solicitudes.
- **FR-408**: Una partida con consultas intercaladas y la misma partida sin consultas DEBEN terminar
  idénticas: mismo estado, mismo `partida.log` y mismo resultado.
- **FR-409**: `historia` DEBE estar disponible solo mientras la partida está en curso. Con la partida
  terminada DEBE indicarse que se use `--replay … --hasta`.

### Requisitos funcionales — Pergamino de retroceso

- **FR-410**: Las acciones revertidas con un pergamino, y todo lo que ocurrió por ellas, DEBEN dejar
  de existir en la línea de tiempo: ninguna consulta posterior las muestra, y la línea describe la
  partida tal como quedó.
- **FR-411**: Después de un pergamino, `historia #k` DEBE numerarse con las acciones que quedaron.
- **FR-412**: Recortar la línea de tiempo al usar un pergamino NO DEBE recorrer toda la historia: su
  costo DEBE depender de lo revertido, no de la cantidad total de acciones de la partida.

### Requisitos funcionales — Reproducción con `--hasta`

- **FR-413**: `--replay partida.log --hasta t` DEBE reproducir la partida hasta el instante t e
  imprimir el resumen (FR-406) del estado en t (FR-401).
- **FR-414**: `--replay … --hasta` NO DEBE instanciar la vista.
- **FR-415**: Si t es posterior al final del log, DEBE mostrarse el último estado e indicarse que la
  partida terminó antes de t, o que el log termina antes de t si la partida no había terminado.
  `--replay … --hasta` DEBE terminar con código 0 siempre que muestra un resumen (también en este
  caso) y con 1 si el log no se puede leer o reproducir, igual que `--replay`.
- **FR-416**: `--hasta` sin `--replay`, o con un valor que no es un entero ≥ 0, DEBE ser un error de
  argumentos que termina el programa sin iniciar ninguna partida.

### Requisitos funcionales — Persistencia

- **FR-417**: Guardar y cargar una partida DEBE conservar la línea de tiempo completa y su K: después
  de cargar, toda consulta da el mismo resumen que antes de guardar y la partida continúa igual.
- **FR-418**: Al cargar se DEBE usar el K guardado. Si `--checkpoint-cada` indica otro valor, DEBE
  avisarse y usarse el guardado.
- **FR-419**: El formato del archivo de partida cambia. Un archivo de la primera parte o del formato
  anterior de la capacidad 001 DEBE rechazarse con un mensaje de formato incompatible, sin cambiar la
  partida en curso; NUNCA DEBE cargarse en silencio ni migrarse.

### Requisitos funcionales — Puntos de control y memoria

- **FR-420**: `--checkpoint-cada K` DEBE aceptar un entero K ≥ 1; cualquier otro valor DEBE ser un
  error de argumentos. Sin la bandera se usa el K por defecto, que se elige con mediciones de
  `--bench` y se documenta en el README y en `DECISIONES.md`.
- **FR-421**: El resultado de toda consulta DEBE ser el mismo para cualquier K e igual al de
  reproducir la partida desde el inicio hasta ese punto.
- **FR-422**: Los puntos de control DEBEN ser copias completas del estado (incluido el del generador
  aleatorio si se reconstruye re-simulando) y DEBE haber a lo sumo uno cada K acciones del jugador.
- **FR-423**: Ninguna consulta DEBE aplicar ni deshacer cambios de más de K acciones del jugador.
- **FR-424**: Fuera de los puntos de control solo DEBE guardarse la información necesaria para
  reconstruir los cambios. La memoria de la línea de tiempo DEBE crecer con la cantidad de cambios
  ocurridos más un punto de control cada K acciones, nunca con acciones × tamaño del estado.
- **FR-425**: Ubicar el punto de control más cercano a un instante o acción pedidos NO DEBE recorrer
  todos los puntos de control.
- **FR-426**: Registrar la línea de tiempo NO DEBE cambiar el juego: con la línea activa, la misma
  cripta, semilla y acciones DEBEN producir la misma partida que sin ella, y todas las pruebas de
  P1 y de la 001 DEBEN seguir pasando (salvo el formato del archivo de partida, FR-419).

### Requisitos funcionales — Medición

- **FR-427**: `--bench` DEBE generar partidas sintéticas de al menos 5 000 acciones del jugador, de
  forma determinista por semilla, sobre la cripta sintética de 2 000 salas con 50 cazadores activos
  de la capacidad 001. Las acciones DEBEN mezclar movimientos, ataques, recoger y usar objetos y
  algunos pergaminos, y el jugador DEBE tener vida de sobra para que la partida no termine antes de
  las 5 000 acciones (como en el bench del ciclo de P1).
- **FR-428**: `--bench` DEBE medir memoria y tiempo de consulta para al menos tres valores de K y para
  la alternativa sin puntos de control. Esta última PUEDE medirse con menos consultas que las de
  FR-432, porque cada una puede tener que reconstruir toda la partida.
- **FR-429**: `--bench` DEBE medir la alternativa de reconstrucción descartada (hacia adelante, re-
  simulando, o hacia atrás, invirtiendo cambios) frente a la elegida.
- **FR-430**: `--bench` DEBE comprobar que todas las alternativas medidas dan los mismos resúmenes y
  reportar cualquier diferencia como error.
- **FR-431**: `--bench` DEBE ejecutarse sin instanciar la vista y sin red.

### Requisitos de rendimiento

Medidos en el equipo local, sin red ni vista (P2 §6.1; constitución, principio VI).

- **FR-432**: El p95 de las consultas `historia` (al menos 200, repartidas por toda la partida de
  forma determinista) DEBE ser menor que 50 ms en la partida sintética de FR-427 (al menos 5 000
  acciones del jugador) con el K por defecto.
- **FR-433**: Con la línea de tiempo activa, el p95 del ciclo de eventos entre dos decisiones del
  jugador DEBE seguir siendo menor que 20 ms en el escenario de medición de la capacidad 001 (FR-035).
- **FR-434**: Según `--bench`, al pasar de 2 500 a 5 000 acciones del jugador con el mismo K, la
  memoria de la línea de tiempo NO DEBE pasar de 2,5 veces la anterior; y con el K por defecto DEBE
  ser menor que un tercio de la memoria que ocuparía guardar una copia completa del estado en cada
  acción del jugador.

### Entidades clave

- **Línea de tiempo**: historia de la partida tal como quedó, desde el instante 0 hasta el reloj
  actual, con sus puntos de control y los cambios entre ellos.
- **Punto de control**: copia completa del estado en una acción del jugador; incluye el estado del
  generador aleatorio si se re-simula.
- **Cambio registrado**: información mínima para aplicar o deshacer un cambio del estado del juego,
  asociada a su instante y a la acción del jugador a la que pertenece.
- **Consulta**: instante t o acción #k pedidos; produce un resumen sin modificar la partida.
- **Resumen**: los datos de FR-406 de un estado.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-401**: El 100 % de los escenarios de aceptación de esta especificación, incluidos los seis
  casos de «Línea de tiempo» del Apéndice B, tienen una prueba automatizada que cita su FR y pasa.
- **SC-402**: En partidas sintéticas generadas por semilla (al menos 20, con pergaminos), el 100 %
  de las consultas coincide con el estado obtenido reproduciendo la partida desde el inicio, para
  al menos tres valores de K.
- **SC-403**: Una partida con consultas intercaladas y la misma sin consultas producen el mismo
  `partida.log`, byte por byte.
- **SC-404**: Según `--bench`, el p95 de `historia` es menor que 50 ms en una partida de al menos
  5 000 acciones sobre la cripta de 2 000 salas con 50 cazadores, con el K por defecto.
- **SC-405**: Según `--bench`, el p95 del ciclo de eventos con la línea de tiempo activa sigue por
  debajo de 20 ms en el escenario de la capacidad 001.
- **SC-406**: `--bench` muestra, para al menos tres valores de K y la alternativa sin puntos de
  control, la memoria y el tiempo de consulta, y con ellos el grupo justifica el K por defecto en
  `DECISIONES.md`.
- **SC-407**: El 100 % de los archivos de formatos anteriores probados (primera parte y 001) se
  rechazan con un mensaje de incompatibilidad; ninguno se carga.
- **SC-408**: Todas las pruebas de la primera parte, de la 001 y de la 003 siguen pasando, salvo las
  que comprueban el formato del archivo de partida, que se actualizan al formato nuevo.
- **SC-409**: Según `--bench`, la memoria de la línea de tiempo con 5 000 acciones no pasa de 2,5 veces
  la de 2 500 (mismo K), y con el K por defecto es menor que un tercio de la de copiar el estado
  completo en cada acción.

## Supuestos

- Esta especificación no define el mapa conocido; lo define la capacidad 002 (niebla de guerra). Aquí
  solo se exige que el resumen lo muestre como era en el estado consultado (FR-406). Mientras la 002
  no exista, el resumen no puede mostrarlo completo; las pruebas de esa parte dependen de la 002.
- Qué cuenta como acción del jugador es lo que ya cuenta P1; esta capacidad no cambia ese conteo.
- El K por defecto no se fija aquí: lo elige el plan con mediciones de `--bench` (P2 §3.6).
- Reconstruir hacia adelante (re-simulando) o hacia atrás (invirtiendo cambios) es decisión del
  plan; solo se exige que el resultado sea el mismo (FR-421) y que la alternativa descartada se
  mida (FR-429).
- El umbral de FR-432 usa el p95 de al menos 200 consultas, igual que la 001 usa el p95 para los
  20 ms; es una meta del grupo para hacer verificable el límite de 50 ms de P2 §6.1.
- Si el profesor ajusta el límite de 50 ms por enmienda (P2 §2.7), se actualiza FR-432.
