---

description: "Lista de tareas de la capacidad 002 — Niebla de guerra e «ir a»"
---

# Tareas: Niebla de guerra e «ir a»

**Entrada**: documentos de diseño en `specs/002-niebla-ir-a/`

**Requisitos previos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: obligatorias (constitución, principio IX; SC-201). Cada escenario de aceptación tiene
una tarea de prueba que cita su FR en el nombre del método o en el docstring. Dentro de cada fase,
las pruebas se escriben **antes** del código y deben **fallar** al escribirse.

**Organización**: siete fases, cada una con punto de control: al terminarla, `python -m unittest`
completo en verde. Cada tarea cita los FR o escenarios que atiende y nombra el archivo que toca. Las
tareas de medición citan el límite del principio VI que verifican.

**Entrega**: miércoles 18 de noviembre de 2026; ver «Calendario sugerido» al final.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo con las demás [P] de su bloque: toca otro archivo y no depende
  de una tarea sin terminar.
- **[HUx]**: historia de usuario de spec.md:
  - HU1: solo veo lo que he explorado;
  - HU2: la antorcha deja ver las salas vecinas;
  - HU3: viajar con «ir a»;
  - HU4: el conocimiento es estado del juego;
  - HU5: medición con `--bench`.
- «HUx-n» es el escenario de aceptación n de la historia x. «Dx» es la decisión x de research.md.
- Rutas relativas a la raíz del repositorio. Las pruebas nunca leen `cache/`: arman criptas
  sintéticas con `tests/ayudas_cripta.py` y usan un `AlmacenDisco` en una carpeta temporal.

---

## Fase 1: Estructura (fundacional)

**Propósito**: el estado recordado de las puertas y el `MapaConocido`, probados por separado, antes
de tocar la partida.

**⚠️ T001 se hace antes de cualquier commit de código de la 002 (principio VIII).**

- [X] T001 Confirmar en Git, en commits propios y antes del código: (a) `specs/002-niebla-ir-a/spec.md` con «Estado: Confirmada»; (b) plan.md, research.md, data-model.md, contracts/, quickstart.md y este tasks.md. Lo hace el grupo (principio VIII; FR-201 a FR-236).

### Pruebas de la estructura (escribir primero; deben fallar)

- [X] T002 Crear `tests/test_mapa_conocido.py` con `TestPuertaRecordada` (FR-204 a FR-206; research D2): una `Puerta` nueva tiene `estado.recordada is None`; los dos lados de una salida comparten `recordada` (escribir por un lado se lee por el otro, FR-205); `Puerta(…, recordada=ABIERTA)` lo guarda; `compartir_estado_con` con un lado `None` toma el otro; con `ABIERTA` frente a `CERRADA` lanza `DatosInvalidos`; `copy.deepcopy` de un `EstadoPuerta` copia `recordada` y deja `observador = None`.
- [X] T003 En `tests/test_mapa_conocido.py`, `TestMapaConocido` (FR-201 a FR-203, FR-224, FR-235, FR-236; data-model «MapaConocido»; research D1, D3, D4), sobre un `Mapa` de `tests/ayudas_cripta.py` (`mapa_de`) y una función de anotar que guarda los `Cambio` en un `RegistroAccion`:
  - todo empieza `DESCONOCIDA`; `estado(sala)`, `esta_explorada(sala)` y `recordada(puerta)` leen por `sala.indice` y `puerta.estado`;
  - `explorar(sala)`: la sala pasa a `EXPLORADA`, cada salida queda con `recordada` igual a su estado real, y cada destino desconocido pasa a `AVISTADA`; un destino ya explorado no cambia;
  - una salida sin vuelta que llega a la sala explorada no hace avistada a su origen (FR-202); una salida hacia una sala que no existe no avista nada (D4, D14);
  - `observar(sala)` solo cambia las salidas cuyo estado real difiere del recordado;
  - **un `Cambio` solo si el valor cambia**: explorar dos veces la misma sala sin cambios en sus puertas no anota nada la segunda vez (D3);
  - deshacer el `RegistroAccion` (en orden inverso) devuelve estados, `recordada` y los contadores `exploradas` y `avistadas` exactamente a como estaban;
  - un observador falso recibe `sala_explorada` y `puerta_recordada` al cambiar **y** al deshacer;
  - `salas_conocidas()` recorre en orden de id;
  - `validar(id_sala_inicial)` (data-model «MapaConocido»): pasa sobre un conocimiento armado con `explorar`; lanza `ValueError` con la sala inicial no explorada, una avistada que no es destino de una explorada, un destino de una explorada que quedó desconocido y una salida de sala explorada con `recordada` `None`;
  - `restaurar(lista)`: acepta una lista válida; rechaza con `ValueError` un id inexistente, repetido o desordenado y un estado distinto de 1 y 2, y lo que rechaza `validar()` (contracts/guardado.md);
  - `copy.deepcopy` copia `_estados` y contadores y deja `observador = None`.

### Implementación de la estructura

- [X] T004 En `crypta/Modelo/Puerta.py`: constantes `ABIERTA = 1` y `CERRADA = 2` (`None` = nunca observada); `EstadoPuerta.recordada` (atributo simple, sin aviso al `observador` del cazador); `Puerta(…, recordada=None)`; en `compartir_estado_con`, si un lado es `None` se toma el otro y si los dos difieren, `DatosInvalidos` con las salas, como con los costos (FR-204 a FR-206; data-model «EstadoPuerta»).
- [X] T005 Crear `crypta/Modelo/MapaConocido.py` (FR-201 a FR-203, FR-235, FR-236; research D1, D3, D4; data-model «MapaConocido»): constantes `DESCONOCIDA = 0`, `AVISTADA = 1`, `EXPLORADA = 2`; `MapaConocido(mapa, anotar)` con `_estados` (`Vector` de V ceros), `exploradas`, `avistadas`, `observador = None`; `estado`, `esta_explorada`, `recordada`, `explorar`, `observar`, `avistar`, `restaurar_sala((indice, anterior))`, `restaurar_puerta((estado, anterior))`, `restaurar(lista)` (valida la lista, fija los estados y llama a `validar`), `validar(id_sala_inicial)` como método aparte (FR-201 a FR-204; lo usa también T041), `salas_conocidas()` y `__deepcopy__`. Cada escritura que cambia el valor anota `Cambio.de_operacion("conocimiento", self, "restaurar_sala" | "restaurar_puerta", (objetivo, anterior))` con la función `anotar` recibida, y avisa al observador. **No** guarda un `historial.registrar_cambio`: recibe una función (en la partida será `partida._anotar`, T011). Sin `dict`, `set` ni `collections` (principio I).

**Punto de control**: `python -m unittest` en verde.

---

## Fase 2: Niebla en la partida (HU1 y HU2, prioridades 1 y 2)

**Objetivo**: el jugador conoce solo lo explorado; la antorcha explora las vecinas; la bitácora y la
vista solo muestran lo que corresponde; `mapa` muestra lo conocido.

**Prueba independiente**: con una cripta sintética pequeña, se mueve al jugador por una secuencia
fija, se cambian puertas lejos de él y se compara mapa conocido, vista, `mapa` y bitácora con lo
esperado; se repite con y sin antorcha comparando enemigos, trampas y solicitudes.

### Pruebas de las historias 1 y 2 (escribir primero; deben fallar)

- [X] T006 [HU1] Crear `tests/test_niebla.py` con `TestConocimientoEnPartida` (FR-201 a FR-206): HU1-1 (partida nueva en la sala 1 con salidas a 2 y 3: 1 explorada con sus salidas observadas, 2 y 3 avistadas, ninguna otra conocida); HU1-2 (al entrar a la 2, explorada, y sus destinos no explorados avistados); HU1-3 (puerta 2–4 vista abierta desde 2, cerrada con el jugador en 1: se recuerda abierta; al volver a 2 **o** al entrar a 4, cerrada desde ambos lados); HU1-4 (puerta de la sala actual con cierre automático mientras el jugador espera: en la siguiente decisión ya se recuerda cerrada); HU1-5 (salida sin vuelta de 5 a la sala actual: no se observa, no aparece y 5 no queda avistada por ella).
- [X] T007 [HU1] En `tests/test_niebla.py`, `TestBitacoraNiebla` (FR-208; HU1-6): con el jugador en la sala 1, regeneración de un enemigo en la 7, rearme de una trampa en la 8 y cierre automático en la 9 no dejan ningún aviso; lo mismo en la sala 1 sí deja su aviso (textos de contracts/vista.md). Además (FR-205, FR-208): el cierre automático de una **salida sin vuelta que llega a la sala 1** desde otra sala no deja aviso, y el de una salida de la sala 1 sí.
- [X] T008 [HU1] En `tests/test_niebla.py`, `TestVistaNiebla` (FR-207, FR-209; HU1-7, HU1-10): cerrar a mano una puerta de la sala actual fuera de una acción (`puerta.cerrar()`) sin observarla → la sección SALIDAS de `VistaConsola.mostrar_estado` (salida capturada) sigue diciendo «Abierta», porque lee `recordada`; las vecinas no exploradas aparecen solo por su id; con la precarga habiendo descargado el contenido de salas no exploradas (gestor de contenido de `tests/ayudas_cripta.py`), ni la vista, ni el texto de `mapa`, ni la bitácora nombran esas salas ni su contenido; el reporte de resolubilidad al iniciar no cambia el mapa conocido.
- [X] T009 [HU2] En `tests/test_niebla.py`, `TestAntorcha` (FR-212 a FR-215; HU2-1 a HU2-4): con antorcha encendida, entrar a la 2 (salidas abiertas y cerradas a 3, 4 y 5) deja 3, 4 y 5 exploradas con sus salidas observadas en ese instante y sus destinos no explorados avistados; sus enemigos siguen dormidos, sus trampas armadas y su contenido no se muestra (HU2-2, Apéndice B); sin antorcha solo la 2; tras apagarse, solo la sala a la que se entra, y lo anterior sigue explorado; entrar después a una sala explorada por la antorcha despierta a sus enemigos y activa sus trampas como en P1; una antorcha que revela una sala **ya explorada** la deja explorada y vuelve a observar sus salidas (una puerta suya que cambió queda con su estado real; caso borde). **Solicitudes**: la misma partida con y sin antorcha (con `FuenteContadora` y `controlador_sintetico`) hace las mismas solicitudes **por operación** (cantidad de cada tipo de solicitud de `FuenteContadora`). No se compara el orden: `FuenteContadora` no lo guarda y la precarga corre en otro hilo (FR-214, principio V).
- [X] T010 [P] [HU1] En `tests/test_controlador.py`, `TestComandoMapa` (FR-210, FR-211; HU1-1, HU1-8, HU1-9): el texto de `mapa` coincide carácter por carácter con contracts/vista.md («Mapa») para una cripta pequeña (exploradas y avistadas por id, salidas en N, S, E, O, «abierta|cerrada»); `mapa` no cambia el reloj, ni las acciones, ni `partida.log`, ni las solicitudes, ni el estado serializado; `mapa 3` da el mismo error que un comando desconocido en P1 y nada cambia.

### Implementación de las historias 1 y 2

- [X] T011 [HU1] [HU2] En `crypta/Modelo/Partida.py` (FR-201, FR-204, FR-205, FR-212 a FR-215; research D3, D4): en `__init__`, `self.conocimiento = MapaConocido(self.mapa, self._anotar)` — **el método `_anotar` de la Partida**, que busca `self.estado.historial` en cada llamada (D3: `leer_linea` reemplaza el historial por asignación); en `iniciar`, `conocimiento.explorar(sala inicial)` antes de programar el primer turno; en `_poner_jugador_en`, `explorar(sala)` y, si `antorcha_encendida()`, `explorar` cada `puerta.sala_destino_ref` no `None` de sus salidas, abiertas o cerradas, sin tocar contenido, enemigos ni trampas; en `_correr_hasta_el_jugador`, al sacar `TURNO_JUGADOR` y **antes del `return`**, `conocimiento.observar(self.sala_actual())`. Comprobar que `Partida.__deepcopy__` copia el conocimiento (el método ligado se reubica por el `memo`).
- [X] T012 [HU1] En `crypta/Modelo/Partida.py` (FR-205, FR-208; research D11): `_cerrar_puerta` avisa solo si la puerta es una **salida de la sala del jugador**: alguna puerta de `sala_actual().puertas()` comparte su `EstadoPuerta` (O(4)); una salida sin vuelta que llega a la sala del jugador no avisa; `_regenerar`, solo si `enemigo.sala_actual == jugador.sala_actual`; `_rearmar_trampa`, solo si la trampa está entre las trampas de la sala del jugador (recorrido de esa sala, O(trampas de la sala)). Los demás avisos no cambian.
- [X] T013 [HU1] En `crypta/Modelo/Resumen.py` (FR-210, FR-228; data-model «Resumen»): `SalaResumida(id, nombre, salidas)` con cada salida `(direccion, destino, costo, recordada)` en N, S, E, O; `MapaResumido(exploradas, avistadas)`; `armar_mapa_resumido(partida)` recorriendo `conocimiento.salas_conocidas()` en O(V + salidas exploradas). Todavía no cambia `Resumen.mapa_conocido` (eso es T037).
- [X] T014 [HU1] (depende de T013: formatea `MapaResumido` y `SalaResumida`) Crear `crypta/Vista/FormatoMapa.py` con `formatear_mapa(mapa_resumido)` → `str`, exactamente el formato «Mapa» de contracts/vista.md (FR-210), y `lineas_mapa(mapa_resumido, sangria)` para reutilizarlas en el resumen (T037).
- [X] T015 [HU1] En `crypta/Vista/VistaConsola.py` (FR-207, FR-210; contracts/vista.md): en SALIDAS, «Cerrada»/«Abierta» sale de `puerta.estado.recordada` (el texto no cambia; «necesita <llave>» se mantiene, D14); `mostrar_mapa(mapa_resumido)` imprime `formatear_mapa`; `mostrar_ayuda` agrega `mapa` e `ir a <sala>`.
- [X] T016 [HU1] En `crypta/Controlador/Controlador.py` (FR-211): `mapa` sin argumentos se atiende en `procesar_comando` antes de traducir, como `historia`: arma el `MapaResumido` y llama a `vista.mostrar_mapa`; no ejecuta comando, no anota en `partida.log`, no toca la línea de tiempo ni la red. Con argumentos sigue al camino de un comando desconocido.
- [X] T017 [HU1] Ajustar las pruebas existentes que esperaban avisos de la bitácora sobre otras salas (FR-208) o información de salas no conocidas en la vista (buscar en `tests/` los textos de contracts/vista.md «Bitácora»). Cada prueba ajustada lleva un comentario que cita FR-208 (si aplica) y SC-207. Si no hay ninguna, anotarlo en la tarea al cerrarla (SC-207). **Hecho**: se ajustaron `TestCompatibilidadP1` en `tests/test_terreno.py` (la bitácora se compara sin los tres avisos de FR-208; el resto del estado sigue igual a `p1_esperado.json`) y `test_nueva_partida_usa_los_datos_de_la_cripta` en `tests/test_controlador.py` (un `Mapa()` vacío en lugar de `Mock()`, porque la `Partida` arma su `MapaConocido`). Ninguna prueba de la vista mostraba salas no conocidas.

**Punto de control**: `python -m unittest` en verde. HU1 y HU2 se pueden demostrar con `mapa` y la
antorcha (quickstart §2).

---

## Fase 3: «ir a» (HU3, prioridad 3)

**Objetivo**: `ir a <sala>` viaja por la ruta conocida más barata, paso a paso, como movimientos
ordinarios, se detiene por los motivos de FR-221 y deja `partida.log` reproducible.

**Prueba independiente**: con criptas sintéticas armadas para cada caso, se ejecuta `ir a` y se
comprueba cada paso, el instante de cada acción, el motivo de parada y el `partida.log`.

### Pruebas de la historia 3 (escribir primero; deben fallar)

- [X] T018 [HU3] Crear `tests/test_ir_a.py` con `TestRutaConocida` (FR-217, FR-218; research D5, D6; data-model «RutaConocida»): solo usa salas exploradas y salidas con `recordada == ABIERTA`; desempate por menor id de la vecina y, a la misma vecina, N, S, E, O; después de un paso sin cambios no hay búsqueda nueva (contador `busquedas`); un cambio de `recordada` con un extremo asentado invalida (contador `invalidaciones`) y uno sin extremos asentados no; explorar una sala vecina de una asentada invalida; en modo `TOTAL` todo cambio invalida y en `RECALCULAR` cada paso busca; en todos los casos el paso coincide con `paso_desde_cero` (`RutaPorCazador` hacia adelante).
- [X] T019 [HU3] En `tests/test_ir_a.py`, `TestIrAValidacion` (FR-216; HU3-1 a HU3-3): `ir a 9` con 9 no explorada y `ir a 99999` dan **el mismo** mensaje («No conoces la sala <id>.»), sin tiempo ni log; `ir a` a la sala actual y a una explorada sin ruta conocida se rechazan con sus mensajes de contracts/cli.md; `ir`, `ir a`, `ir a x`, `ir a -3`, `ir a 3 4` e `ir b 3` son `ComandoInvalido` (`leer_ir_a`).
- [X] T020 [HU3] En `tests/test_ir_a.py`, `TestIrARuta` (FR-217 a FR-219; HU3-4 a HU3-8): HU3-4 (1–4 de costo 500 contra 1–2–4 de 100 + 100: va por la 2); HU3-5 (empate: el primer paso va a la 3, no a la 5); HU3-6 (la ruta más barata por una sala avistada no se usa); HU3-7 (puerta recordada abierta y cerrada en realidad: al llegar se observa, el mapa se actualiza y el siguiente paso la evita; sin alternativa, el viaje se detiene con `SIN_RUTA` sin consumir tiempo adicional; Apéndice B); **HU3-8, dos casos con la llave en el inventario**: (1) rechazo al inicio: la única ruta cruza una puerta **recordada cerrada**; (2) parada a medio camino: la puerta se recordaba abierta y se **descubre cerrada al llegar**. En los dos, la puerta sigue cerrada y no hay ningún `abrir` en `partida.log` (FR-219).
- [X] T021 [HU3] En `tests/test_ir_a.py`, `TestIrAPasos` (FR-220, FR-221; HU3-9 a HU3-13, HU3-16): HU3-9 (4 pasos de costo 100, 250, 100 y 300 con velocidad 100: cada paso es una acción con su intervalo y entre pasos corren los eventos del reloj); HU3-10 (sala con enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene, `ENEMIGOS`; Apéndice B); HU3-11 (daño por ataque, por trampa y por pulso de veneno: se detiene después del paso, `DANIO`); HU3-12 (presupuesto agotado y sin conexión **en `garantizar_sala`**: `PASO_IMPOSIBLE`, sin hacer el paso ni consumir su tiempo); un `RuntimeError` lanzado **dentro del `mover`** no es `PASO_IMPOSIBLE`: sale de `ejecutar_ir_a` (research D8); HU3-13 (muerte y victoria: `FIN_PARTIDA`); **caso borde: `ir a` desde una sala con enemigos** se permite y no se detiene antes del primer paso: el primer paso se hace y las paradas se revisan solo después de cada paso (Supuestos; FR-221); HU3-16 (un enemigo entra a la sala del jugador entre dos pasos sin atacar: sigue; si ataca y hace daño: se detiene). Cada caso comprueba el texto del motivo (contracts/vista.md).
- [X] T022 [HU3] En `tests/test_ir_a.py`, `TestIrALog` (FR-222, FR-223; HU3-14, HU3-15; SC-206): un viaje de 3 pasos deja `# ir a <id>` seguido de tres `mover <d>`; un viaje sin pasos (paso imposible en el primero) no deja ninguna línea; `leer_registro` ignora las líneas que empiezan con `#` después de `---`; `--replay` del log da la misma partida (estado serializado, reloj, resultado); un `partida.log` de P1 y uno de la 001 se reproducen igual que antes.
- [X] T023 [P] [HU3] En `tests/test_controlador.py`, `TestIrAEnControlador` (FR-220, FR-222; principio V; research D8): en la misma partida, un viaje de 3 pasos y los 3 `mover` escritos a mano dan (a) la **misma secuencia de llamadas** a `garantizar_sala` y a `precargar_async`, registrada por un gestor de contenido espía que envuelve al real, y (b) las mismas solicitudes **por operación** según `FuenteContadora` (que no guarda el orden; la precarga corre en otro hilo, así que no se compara el orden de las solicitudes); la línea de tiempo y `partida.log` quedan iguales en los dos caminos salvo el comentario; el motivo de parada se muestra; un rechazo no anota nada.

### Implementación de la historia 3

- [X] T024 [P] [HU3] En `crypta/Adaptadores/RegistroPartida.py` (FR-222, FR-223; research D10): `anotar_comentario(texto)` escribe `# <texto>` (con `_revisar_una_linea`); `leer_registro` no encola las líneas que empiezan con `#` después de `---`. `FORMATO_REGISTRO` sigue en 1.
- [X] T025 [P] [HU3] Crear `crypta/Modelo/RutaConocida.py` (FR-217, FR-218; research D5, D6, D12; data-model «RutaConocida»): `RutaConocida(mapa, conocimiento, modo=SELECTIVA)` con una `DistanciasLimitadas(V, entradas_conocidas)` de `crypta/estructuras` (origen = destino); `siguiente_paso(sala, destino)` → `Puerta` o `None` con la regla de desempate de `Perseguidor._decidir_con` leyendo `recordada`; `paso_desde_cero(sala, destino)` con `RutaPorCazador`; `puerta_recordada(estado)`, `sala_explorada(sala)` e `invalidar()` según D6; contadores `busquedas`, `invalidaciones`, `pasos`. Reutiliza las constantes de modo de `crypta/Modelo/Perseguidor.py`.
- [X] T026 [HU3] En `crypta/Modelo/Partida.py` (FR-221, FR-225; research D7, D8): `ruta_conocida()` crea la `RutaConocida` la primera vez y la registra como `conocimiento.observador`; `_ruta_conocida` en `_NO_SE_COPIAN` y `None` en la copia; `mover` fija `self.enemigos_al_entrar` (enemigos vivos de la sala destino al entrar, **antes** de activar a los dormidos; transitorio, no es estado del juego); `usar_pergamino` también llama a `_ruta_conocida.invalidar()` si existe.
- [X] T027 [HU3] Crear `crypta/Modelo/Viaje.py` (FR-216, FR-221; data-model «Viaje»): constantes `LLEGADA`, `ENEMIGOS`, `DANIO`, `SIN_RUTA`, `PASO_IMPOSIBLE`, `FIN_PARTIDA`; `Viaje.validar(partida, id_destino)` (`AccionInvalida` con los mensajes de contracts/cli.md; id inexistente = no explorado); `siguiente_direccion(partida)`; `despues_del_paso(partida, vida_antes)` en el orden `FIN_PARTIDA`, `LLEGADA`, `DANIO`, `ENEMIGOS`; `detener(motivo, detalle=None)`; `pasos`.
- [X] T028 [HU3] En `crypta/Controlador/Comandos.py` (FR-216, FR-220 a FR-222; contracts/cli.md): `leer_ir_a(texto)` → id o `ComandoInvalido`; `ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar_sala=None, anotar_comentario=None)` → `Viaje`: por cada paso, dirección o `SIN_RUTA`; `garantizar_sala` del destino **antes** del `mover` (solo su `RuntimeError` da `PASO_IMPOSIBLE`); `anotar_comentario("ir a <id>")` antes del primer paso; `ejecutar_paso("mover <d>")` (sus errores no se atrapan); `despues_del_paso`.
- [X] T029 [P] [HU3] En `crypta/Vista/FormatoMapa.py`, `texto_motivo(viaje)` con los textos de contracts/vista.md («Motivos de parada») (FR-221).
- [X] T030 [HU3] En `crypta/Controlador/Controlador.py` (FR-216, FR-220 a FR-222; principio V; research D8): separar `_ejecutar_comando_jugador(comando)` con lo que hoy hace `procesar_comando` con un comando escrito a mano, en el mismo orden (`_asegurar_linea`; `ejecutar_comando` con `garantizar_sala`; `linea.registrar`; `registro.anotar`; `_actualizar_fichas_en_uso`; `precargar_async` si la partida sigue), sin atrapar errores; `procesar_comando` lo usa para los comandos escritos a mano dentro del mismo `try`; `ir a` se reconoce antes de traducir, llama a `ejecutar_ir_a` con `_ejecutar_comando_jugador` y `registro.anotar_comentario`, y muestra `texto_motivo`.

**Punto de control**: `python -m unittest` en verde. HU3 se puede demostrar con `ir a` y `--replay`
(quickstart §3).

---

## Fase 4: Estado del juego (HU4, prioridad 4)

**Objetivo**: el conocimiento se revierte con el pergamino, se guarda en el formato 4 y forma parte
de la línea de tiempo; se cierra T057 de la 004.

**Prueba independiente**: se juega, se usa el pergamino, se guarda y se carga, y se consulta la
historia, comparando el mapa conocido en cada caso.

### Pruebas de la historia 4 (escribir primero; deben fallar)

- [X] T031 [P] [HU4] En `tests/test_pergaminos.py`, `TestPergaminoNiebla` (FR-224, FR-225; HU4-1, HU4-2; Apéndice B): con antorcha, entrar a una sala que explora 4 vecinas y usar un pergamino devuelve la sala, las 4 vecinas, sus avistadas y las puertas observadas exactamente al estado anterior; un viaje de 3 pasos que se detuvo y un pergamino: se revierte solo el último paso y el viaje no se reanuda.
- [X] T032 [P] [HU4] En `tests/test_persistencia.py` (FR-226, FR-227; HU4-3, HU4-4; contracts/guardado.md): 30 salas exploradas con puertas recordadas distintas de las reales → idéntico tras guardar y cargar, en binario y en JSON; archivos de formato 1, 2 y **3** rechazados con «Formato incompatible …» y la partida en curso sin cambios; los dos lados de una salida con `recordada` distinto → `ErrorGuardado`; `conocimiento` inválido (avistada que no es destino de una explorada) → `ErrorGuardado`. Pasar a 4 las pruebas existentes que esperaban el formato 3, con un comentario que cite FR-227 y SC-207.
- [X] T033 [P] [HU4] En `tests/test_linea_tiempo.py`, `TestMapaConocidoEnHistoria` (**T057 de la 004**; HU1-11 de la 004; FR-228 y HU4-5 de esta): puerta observada abierta en el instante 300 y cerrada en el 900 → `historia 500` la muestra abierta y coincide con el oráculo (`jugar_con_oraculo`); lo mismo tras guardar y cargar, y con `--replay … --hasta 500`.
- [X] T034 [HU4] En `tests/test_linea_tiempo.py`, `TestConocimientoTrasCargar` (FR-224, FR-228; research D3): guardar con línea de tiempo, cargar, consultar **dos veces** el mismo instante → el mismo resumen, y el conocimiento del punto de control (estados del `MapaConocido` y `recordada` de cada puerta) igual antes y después de las consultas. Debe fallar si `MapaConocido` guardara `historial.registrar_cambio` en lugar de `partida._anotar`.
- [X] T035 [P] [HU4] En `tests/test_resumen.py`: la línea fija «Mapa conocido: no disponible (capacidad 002)» pasa al texto de contracts/vista.md («Resumen»), con un comentario que cite FR-228 y SC-207.

### Implementación de la historia 4

- [X] T036 [HU4] En `crypta/Adaptadores/EstadoPartida.py` (FR-226, FR-227; contracts/guardado.md): `escribir_sala` agrega `recordada` por salida (0 nunca observada, 1 abierta, 2 cerrada); `leer_sala` lo lee y lo pasa a `Puerta`; `escribir_general` agrega el grupo `conocimiento` con la lista de salas no desconocidas (`sala`, `estado`) en orden de índice; `leer_general` lo lee; `_armar` llama a `partida.conocimiento.restaurar(lista)` y convierte su `ValueError` en `ErrorGuardado`. Los puntos de control de la línea (`escribir_linea`, `leer_linea`) lo heredan sin cambios.
- [X] T037 [HU4] En `crypta/Adaptadores/GuardadoBinario.py` y `crypta/Adaptadores/GuardadoJSON.py`: `FORMATO_GUARDADO = 4` y `FORMATO_JSON = 4`; los formatos 1, 2 y 3 se rechazan con el mensaje que ya existe (FR-227). Firmas sin cambios.
- [X] T038 [HU4] Completar la línea «Mapa conocido» (T057 de la 004; FR-228): `crypta/Modelo/Resumen.py` arma `mapa_conocido = armar_mapa_resumido(partida)`; `crypta/Vista/FormatoResumen.py` imprime «Mapa conocido: <E> exploradas, <A> avistadas» seguido de `lineas_mapa` con la sangría de contracts/vista.md; actualizar la línea en `specs/004-linea-de-tiempo/contracts/resumen.md`.
- [X] T039 [HU4] Cuando T033, T034 y T038 estén en verde, marcar T057 como hecha (`[X]`) en `specs/004-linea-de-tiempo/tasks.md` y quitar «Bloqueada por la 002» de su texto y de sus notas.

**Punto de control**: `python -m unittest` en verde (quickstart §4).

---

## Fase 5: Equivalencia (SC-202, SC-203)

**Propósito**: comprobar en muchas partidas generadas que la niebla nunca filtra y que «ir a»
reutilizando decide lo mismo que desde cero.

- [X] T040 Extender `tests/ayudas_cripta.py` (SC-202, SC-203): `partida_niebla(semilla)`: cripta sintética pequeña sin red, con nombres de sala únicos y **ninguno contenido en otro** (no «Sala 1» y «Sala 10»; por ejemplo «Cámara-<id>-fin», con un sufijo fijo después del id), costos variables, puertas con cierre automático, antorchas y pergaminos en el suelo, enemigos errantes; y `comandos_niebla(partida, azar, cantidad)`, que mezcla los de `comando_al_azar` con `usar` de antorchas y `ir a <sala explorada>`.
- [X] T041 Crear `tests/test_equivalencia_niebla.py` (SC-202, SC-203; FR-207, FR-209, FR-217, FR-218): al menos 20 partidas por semilla con antorcha, puertas que cambian, pergaminos y viajes. **SC-202**, después de cada comando y sin buscar números en el texto crudo: (a) cada «sala <id>» de la sección SALIDAS de `mostrar_estado` (salida capturada) es una sala explorada, avistada o que no existe en la cripta; (b) en las líneas de `formatear_mapa`, cada sala listada como explorada lo está, cada avistada lo está, y ninguna desconocida aparece; (c) ningún nombre de sala no explorada aparece en SALIDAS, en el texto del mapa ni en los mensajes **nuevos** de la bitácora de ese comando (los viejos no cuentan: el pergamino no los borra, caso borde de la spec). **FR-204**: las salidas de la sala actual tienen `recordada` igual a su estado real. **FR-201, FR-202**: `partida.conocimiento.validar(partida.id_sala_inicial)` no lanza. **SC-203**: un `ejecutar_paso` envoltorio compara, antes de cada paso, la dirección elegida con `ruta_conocida().paso_desde_cero(...)`. 0 diferencias.
- [X] T042 Corregir en el código de las fases 1 a 4 cualquier diferencia que encuentre T041 (citando el FR que se rompía). Si una diferencia revela un caso que la spec no cubre, primero se corrige spec.md en un commit propio (principio VIII). **Hecho**: T041 no encontró diferencias en 22 partidas (≈760 pasos de «ir a» comparados, 0 diferencias); no hubo nada que corregir. Para comprobar que la prueba detecta fallos, se saboteó en memoria la invalidación de la ruta (`puerta_recordada`, `sala_explorada`), el avistamiento y el texto del mapa: todos dieron diferencias o fallos.

**Punto de control**: `python -m unittest` en verde.

---

## Fase 6: Medición (HU5, prioridad 5)

**Objetivo**: `--bench` con N1 a N4 (contracts/bench.md) y las mediciones de la 001 y la 004
repetidas con la carga nueva.

**Prueba independiente**: `--bench` dos veces con la misma semilla; mismas huellas y secciones.

### Pruebas de la historia 5 (escribir primero; deben fallar)

- [X] T043 [HU5] En `tests/test_bench.py`, `TestBenchNiebla` (FR-229 a FR-233; HU5-1 a HU5-3, HU5-7): la huella de la cripta, el mapa conocido y los viajes es la misma en dos ejecuciones; N1 a N4 corren en modo rápido con una **carpeta de copias temporal vacía** (usan la sintética de 300 salas; nunca `cache/`); N4 con una variante saboteada (que elige otro paso) da ERROR y código distinto de 0; N2 con entradas que revelan distinto en los dos mapas da ERROR; con una fuente y una vista que fallan si se les pide algo, nada falla. Los límites de FR-234 a FR-236 solo se comprueban como «calculados y reportados».

### Implementación de la historia 5

- [X] T044 [P] [HU5] En `crypta/bench/bench_cazador.py`, agregar `(300, 20, 15)` a `TAMANOS` (contracts/bench.md; FR-234 c). Sin cambiar las filas existentes de B1 a B9.
- [X] T045 [HU5] Crear `crypta/bench/bench_niebla.py` con el generador (FR-229; contracts/bench.md «Criptas y mapas conocidos»): `mapa_conocido_completo(mapa, anotar)`, `mapa_conocido_parcial(mapa, n, anotar)` (anchura desde el centro), `desactualizar(conocimiento, fraccion, azar)` (5 % de puertas cerradas recordadas abiertas), `copia_mas_grande(carpeta)` (esqueleto de la copia local más grande o `None`; carpeta como parámetro; sin escribir ids, principio IV), `viajes(mapa, conocimiento, azar, minimo_viajes=20, minimo_pasos=200)` y `huella(...)`. `MapaConocido` recibe la función de anotar que corresponda (D3).
- [X] T046 [HU5] En `crypta/bench/bench_niebla.py`, `ejecutar_n1(rapido=False)` (FR-230, FR-235; SC-205; principio VI): 2 000 salas con 200 y 2 000 exploradas; consultas de `estado` y `recordada` con la elegida y con `ArbolBusqueda` armado con `desde_ordenados` por id y por (sala, dirección); media y cociente 2 000/200; «¿cumple?» para la elegida (≤ 2); nota de research D1.
- [X] T047 [HU5] En `crypta/bench/bench_niebla.py`, `ejecutar_n2(rapido=False)` (FR-230, FR-236; SC-205): `CriptaSintetica(20000)` con regiones de 200 y 2 000; 1 000 entradas con antorcha en las mismas salas a **más de 2 pasos** de la región de 2 000; explorar con un `RegistroAccion` por entrada y deshacerlo; elegida frente a «copia del mapa conocido por acción»; cociente ≤ 2 al explorar y al deshacer; **ERROR** si los cambios registrados de una entrada difieren entre los dos mapas.
- [X] T048 [HU5] En `crypta/bench/bench_niebla.py`, `ejecutar_n3(rapido=False, carpeta=CARPETA_COPIAS)` (FR-231, FR-234; SC-204; principio VI «Paso de ir a: 5 ms»): (a) 2 000 salas con mapa completo, (b) desactualizado, (c) tamaño de la de referencia de `carpeta` o sintética de 300; ≥ 20 viajes y ≥ 200 pasos; variantes selectiva, total y recalcular; media, p95 y máximo de todos los pasos y del primer paso aparte; pasos por viaje; fracción de pasos que buscaron; búsquedas e invalidaciones; «¿cumple?» p95 < 5 ms en (a) y (c); viaje de calentamiento; solo se cronometra `siguiente_paso`.
- [X] T049 [HU5] En `crypta/bench/bench_niebla.py`, `ejecutar_n4(rapido=False)` (FR-232; SC-203): compara, fuera de lo cronometrado, cada paso de N3 con `paso_desde_cero` y entre variantes, cada consulta de N1 y cada entrada de N2 entre la elegida y la alternativa; 0 diferencias o ERROR.
- [X] T050 [HU5] En `crypta/bench/bench.py`, registrar `niebla_n1` a `niebla_n4` en `SECCIONES` con sus títulos de contracts/bench.md; código distinto de 0 si N2 o N4 dan ERROR (FR-232, FR-233).
- [ ] T050a [HU5] **Condicional: solo si el p95 de N3 (a) o (c) no cumple 5 ms** en una corrida previa de `python -m crypta.bench.bench niebla_n3` (FR-234; principio VI «Paso de ir a: 5 ms»; research D12). En `crypta/Modelo/RutaConocida.py`, una variante de `entradas_conocidas` que recorre el `Vector` de entradas sin generador y llena un `Vector` de pares reutilizable; en `crypta/bench/bench_niebla.py`, una fila más de N3 con esa variante y su comparación en N4. Se queda la variante más rápida si N4 da 0 diferencias. Si el p95 cumple, la tarea se marca «no hizo falta» con el número de N3.
- [ ] T051 [HU5] Correr, en el equipo local y en una sola ejecución, `python -m crypta.bench.bench niebla_n1 niebla_n2 niebla_n3 niebla_n4 ciclo_cazadores linea_l1 linea_l4 --guardar docs/resultados_bench_002.txt` (FR-234 a FR-236; principio VI: paso de «ir a» 5 ms, ciclo 20 ms, historia 50 ms; principio XI). **No** tocar `docs/resultados_bench_p2.txt`, `docs/resultados_bench_003.txt` ni `docs/resultados_bench_004.txt`. Anotar qué límites cumplen y cuáles van a Límites (D14). Si se hizo T050a, N3 reporta las dos variantes.

**Punto de control**: `python -m unittest` en verde y `docs/resultados_bench_002.txt` generado.

---

## Fase 7: Cierre (documentación y revisión)

- [ ] T052 Escribir la sección P2 §5.3 «El mapa conocido» de `DECISIONES.md` desde research.md (D1 a D14): problema, alternativas, decisión, complejidad, evidencia de `docs/resultados_bench_002.txt` (N1 a N4 y las repeticiones de B7, L1 y L4), si la ruta de «ir a» comparte implementación con el cazador y por qué (D5), límites conocidos (primer paso, p95 si no cumple, conocimiento cambiante), enlaces a spec.md y plan.md, y si la decisión final coincide con plan.md (constitución X; FR-234).
- [ ] T053 [P] Actualizar `README.md`: comandos `mapa` e `ir a <sala>`, el comentario `# ir a` en `partida.log`, el formato 4 del archivo de partida (los anteriores se rechazan) y cómo correr las pruebas de la 002 y las secciones `niebla_n1` a `niebla_n4` (constitución X).
- [ ] T054 [P] Registrar en `PROMPTS_LLM.md` las invocaciones de `/speckit-plan`, el ajuste del plan, `/speckit-tasks` y las de implementación de la 002. Lo hace el grupo (constitución X).
- [ ] T055 Revisión de trazabilidad (principio IX): cada FR-201 a FR-236 y cada escenario HU1-1 a HU5-7 tiene al menos una prueba que lo cita; los seis casos del Apéndice B (HU2-2, HU3-1, HU3-7, HU3-10, HU4-1, HU4-2) están cubiertos; ningún import prohibido por el principio I en los archivos nuevos o cambiados (`dict`/`set` como estructura, `heapq`, `bisect`, `collections`); spec.md, plan.md y contracts/ coinciden con el programa (si no, se corrigen primero en su propio commit). Recorrer quickstart.md completo.
- [ ] T056 `python -m unittest` completo en verde antes del último commit de código (principio IX; SC-201, SC-207).

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1** (T001–T005): T001 antes de cualquier commit de código. Bloquea todo lo demás.
- **Fase 2** (HU1, HU2): depende de la fase 1.
- **Fase 3** (HU3): depende de la fase 2 (observar antes de decidir es lo que hace válida la ruta).
- **Fase 4** (HU4): depende de las fases 2 y 3 (HU4-2 usa un viaje).
- **Fase 5**: depende de las fases 2 a 4.
- **Fase 6** (HU5): T044–T050 dependen de las fases 1 y 3 (usan `MapaConocido` y `RutaConocida`, no la partida); T050a (condicional) va después de T048 y T049 y antes de T051; T051 depende de la fase 5, para medir el código final.
- **Fase 7**: depende de T051.

### Dentro de cada fase

Pruebas → modelo → vista y controlador. Las pruebas deben fallar antes de implementar.

### Archivos con varias tareas (no se reparten a la vez)

| Archivo | Tareas, en orden |
|---|---|
| `tests/test_mapa_conocido.py` | T002, T003 |
| `tests/test_niebla.py` | T006, T007, T008, T009 |
| `tests/test_controlador.py` | T010, T023 |
| `tests/test_ir_a.py` | T018, T019, T020, T021, T022 |
| `tests/test_linea_tiempo.py` | T033, T034 |
| `crypta/Modelo/Partida.py` | T011, T012, T026 |
| `crypta/Modelo/Resumen.py` | T013, T038 |
| `crypta/Vista/FormatoMapa.py` | T014, T029 |
| `crypta/Controlador/Controlador.py` | T016, T030 |
| `crypta/bench/bench_niebla.py` | T045 → T046 → T047 → T048 → T049 → T050a (si hace falta) |

---

## Ejemplos de trabajo en paralelo

### Fase 2

```text
T010 (tests/test_controlador.py)  ‖  T006–T009 (tests/test_niebla.py, en orden)
T014 (FormatoMapa)  ‖  T011–T012 (Partida)
```

### Fase 3

```text
T023 (test_controlador)  ‖  T018–T022 (test_ir_a)
T024 (RegistroPartida)  ‖  T025 (RutaConocida)  ‖  T029 (texto_motivo)
```

### Fase 4

```text
T031 (test_pergaminos)  ‖  T032 (test_persistencia)  ‖  T033 (test_linea_tiempo)  ‖  T035 (test_resumen)
```

### Fase 6 y 7

```text
T044 (bench_cazador)  ‖  T043 (test_bench)
T053 (README)  ‖  T054 (PROMPTS_LLM)
```

---

## Estrategia de implementación

### MVP primero

Fases 1 y 2: con el mapa conocido, la antorcha, la bitácora filtrada y `mapa`, la niebla ya
funciona y se puede demostrar (HU1, HU2). Parar, validar con quickstart §2 y seguir.

### Entrega incremental

1. Fase 1 → estructura probada.
2. Fase 2 → niebla jugable (MVP).
3. Fase 3 → «ir a» con log reproducible.
4. Fase 4 → pergamino, guardado y línea de tiempo (cierra T057 de la 004).
5. Fase 5 → equivalencia en partidas generadas.
6. Fase 6 → evidencia de `--bench`.
7. Fase 7 → documentación y revisión.

### Calendario sugerido (entrega el miércoles 18 de noviembre)

| Día | Fases |
|---|---|
| Domingo 15 | T001 y fase 1 (y la fase 2 si da tiempo) |
| Lunes 16 | fases 2 a 4 |
| Martes 17, mañana | fases 5 y 6 |
| Martes 17, tarde | fase 7 |
| Miércoles 18 | solo la entrega |

---

## Notas

- Cada tarea se cierra con su commit de código, con `python -m unittest` en verde (constitución,
  puerta de commit). Los commits los hace el grupo.
- `MapaConocido` anota siempre con `partida._anotar` (research D3); T034 lo comprueba.
- Cada paso de `ir a` pasa por `Controlador._ejecutar_comando_jugador` (research D8); T023 lo
  comprueba con solicitudes.
- `PASO_IMPOSIBLE` sale solo de `garantizar_sala`, antes del `mover` (research D8); T021 lo comprueba.
- El bench escribe solo en `docs/resultados_bench_002.txt`.
- Si una tarea encuentra un caso que la spec no cubre, se para y se corrige primero la spec
  (principio VIII).
