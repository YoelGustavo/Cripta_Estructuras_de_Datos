---

description: "Lista de tareas de la capacidad 004 — Línea de tiempo"
---

# Tareas: Línea de tiempo

**Entrada**: documentos de diseño en `specs/004-linea-de-tiempo/`

**Requisitos previos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: obligatorias (constitución, principio IX; SC-401). Cada escenario de aceptación tiene
una tarea de prueba que cita su FR en el nombre del método o en el docstring. Las pruebas de una
historia se escriben **antes** de implementarla y deben **fallar** al escribirse.

**Organización**: por fases y, dentro de ellas, por historia de usuario. Cada tarea cita los FR que
atiende y nombra el archivo que toca. Las tareas de medición citan el límite del principio VI que
verifican.

**Entrega**: miércoles 18 de noviembre de 2026; ver «Calendario sugerido» al final.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo con las demás [P] de su bloque: toca otro archivo y no depende
  de una tarea sin terminar.
- **[HUx]**: historia de usuario de spec.md:
  - HU1: consultar durante la partida;
  - HU2: pergamino;
  - HU3: `--replay … --hasta`;
  - HU4: guardar y cargar;
  - HU5: puntos de control y `--bench`.
- «HUx-n» es el escenario de aceptación n de la historia x. «Dx» es la decisión x de research.md.
- Notación: n acciones netas, K acciones entre puntos de control, «punto» = punto de control.
- «Oráculo»: resúmenes tomados de la partida **viva** mientras se juega, en cada decisión y en
  instantes intermedios (T003).
- Rutas relativas a la raíz del repositorio.

---

## Fase 1: Preparación

**Propósito**: que la spec y el plan coincidan antes del código, y que las pruebas tengan oráculo y
partidas armadas.

**⚠️ T001 se hace antes de cualquier commit de código de la 004.**

- [X] T001 Confirmar en Git, en un commit de spec propio y antes de `tasks.md` y del código, la corrección de FR-427 en `specs/004-linea-de-tiempo/spec.md`: (a) al menos 5 000 acciones; (b) la partida de escala de 2 000 salas con 50 cazadores, al menos 1 000 acciones y solo el K por defecto, porque con 5 000 los puntos ocuparían ≈ 2,2 GB. HU5-7 y SC-404 ya dicen lo mismo; FR-432 remite a FR-427 b. También «Estado: Confirmada». El texto ya está escrito; falta el commit, que hace el grupo (principio VIII; FR-427, FR-432). **Bloquea T050.**
- [X] T002 Confirmar en Git `specs/004-linea-de-tiempo/tasks.md` y los anexos del plan corregidos en un commit propio, después de T001 (principio VIII; FR-401 a FR-434).
- [X] T003 Extender `tests/ayudas_cripta.py` y crear `crypta/bench/oraculo_linea.py` (habilita las pruebas de FR-401 a FR-426 y L3 de FR-430). Todos los imports nuevos van dentro de las funciones, para no romper las pruebas mientras no existen los módulos. El bench no importa nada de `tests/`; las pruebas reutilizan el módulo del bench. En `tests/ayudas_cripta.py`:
  - `partida_con_pergaminos(semilla)`: una partida sintética pequeña, sin red, con salas aún sin contenido, objetos (arma, armadura, poción), pergaminos de retroceso en el suelo, un enemigo errante, una puerta con cierre automático y veneno. Devuelve también la fuente contadora y el gestor de contenido.
  - `comandos_al_azar(partida, azar, cantidad)`: genera comandos válidos que mezclan `mover`, `atacar`, `recoger`, `usar`, `equipar`, `avanzar`, `retroceder`, `recoger_pergamino` y `pergamino`.

  En `crypta/bench/oraculo_linea.py` (data-model.md, «Oráculo»):
  - `jugar_con_oraculo(partida, linea, comandos, garantizar)`: juega con `ejecutar_y_registrar` (T020). Antes de cada comando guarda `formatear_resumen(armar_resumen(partida, "#k"))`. Con el callback `Partida.al_ejecutar_evento` (T009) guarda también el resumen en el instante de cada evento ejecutado, y al terminar lo vuelve a `None`. Devuelve el oráculo como `Vector` de (pedido, texto).
  - `serializar_estado(partida, omitir_salas=None)`: bytes de `escribir_general` + `escribir_sala` con `EscritorBinario`. Si se pasa `omitir_salas` (un `Vector` de ids), omite el registro de contenido de esas salas (D8).

**Punto de control**: `python -m unittest` en verde (las ayudas nuevas aún no se usan).

---

## Fase 2: Base común (estructura, cambios a P1, copia y resumen)

**Propósito**: lo que usan todas las historias: búsqueda binaria, historial sin límite, tope de
tiempo, copia de la partida para los puntos, y el resumen con su texto.

**⚠️ CRÍTICO**: ninguna historia empieza antes de terminar esta fase.

### Pruebas de la base (escribir primero; deben fallar)

- [X] T004 [P] Escribir `tests/test_busqueda_binaria.py` (D5; habilita FR-403). `primera_no_menor(vector, valor, clave)`:
  - con un `Vector` vacío → 0;
  - con un elemento;
  - con empates → la **primera** posición con clave ≥ valor;
  - con un valor mayor que todos → `len(vector)`;
  - con un valor menor que todos → 0;
  - cuenta de comparaciones ≤ ⌈log₂(n + 1)⌉ + 1 con n = 1 000.
- [X] T005 [P] Escribir `TestBaseLinea` en `tests/test_linea_tiempo.py` (D3, D9; FR-407, FR-426):
  - `Historial(limite=None)` registra 1 000 acciones sin descartar ninguna y las deshace todas; `Historial()` sigue con límite 5, y `Historial(0)` sigue lanzando `ValueError`.
  - `Partida.tope_tiempo` es `None` por omisión, y una partida jugada con y sin el atributo tocado da la misma serialización (`serializar_estado`).
  - `Partida.al_ejecutar_evento` es `None` por omisión; con un callback, se llama una vez por cada evento ejecutado que no es el turno del jugador, y la partida jugada con y sin callback da la misma serialización (FR-426).
  - Con `tope_tiempo = t`, la acción se detiene antes del primer evento con tiempo > t. Si el siguiente evento es el turno del jugador en t, se detiene antes de esa decisión. Deshacer esa acción a medias deja la serialización igual a la de antes.
  - `copy.deepcopy(partida)`:
    - comparte `Sala.contenido` (`is`) y `_fichas` (`is`);
    - da `_perseguidor is None`, `al_ejecutar_evento is None`, `observador is None` en el `EstadoPuerta` de cada puerta, una bitácora vacía distinta y un `Historial` vacío sin límite;
    - la copia serializa igual que el original;
    - jugar 20 comandos sobre la copia no cambia la serialización ni la bitácora del original.
- [X] T006 [P] Escribir `tests/test_resumen.py` (FR-406; contracts/resumen.md):
  - texto completo exacto de una partida armada a mano, con veneno, antorcha y velocidad (orden fijo veneno, antorcha, velocidad), inventario en orden real con arma y armadura equipadas y «<- actual», pergaminos, dos enemigos activos y vivos más uno dormido y uno muerto (que no salen), y la línea fija «Mapa conocido: no disponible (capacidad 002)»;
  - el texto no contiene el reloj actual cuando el estado es otro;
  - la línea de aviso solo aparece si se pasa un aviso;
  - termina con salto de línea.

### Implementación de la base

- [X] T007 [P] Crear `crypta/estructuras/BusquedaBinaria.py` (D5; FR-403): función `primera_no_menor(vector, valor, clave)` sobre un `Vector` ordenado por `clave`, en O(log n), sin `bisect`. Hace pasar T004.
- [X] T008 Cambiar `crypta/Modelo/Historial.py` (D2; FR-423): `Historial(limite=5)` acepta `limite=None` = «sin límite» y en `registrar` no descarta cuando `limite is None`; el resto, igual. Parte de T005.
- [X] T009 Cambiar `crypta/Modelo/Partida.py` (D9; FR-401, FR-426):
  - atributo `tope_tiempo = None`. En `_correr_hasta_el_jugador`, si `tope_tiempo` no es `None`, usa `self.agenda.siguiente_si_corresponde(self.tope_tiempo)` en lugar de `siguiente()` y, si devuelve `None`, retorna sin lanzar «La agenda se quedó sin eventos»;
  - callback opcional `al_ejecutar_evento = None` (data-model.md): si no es `None`, se llama con `(partida, evento)` después de `_ejecutar(evento)`.

  Sin tope ni callback, el código actual no cambia. Parte de T005.
- [X] T010 Agregar `__deepcopy__` (D3; FR-422):
  - en `crypta/Modelo/Sala.py`: comparte `contenido`;
  - en `EstadoPuerta` de `crypta/Modelo/Puerta.py`: copia sin `observador`;
  - en `crypta/Modelo/Partida.py`: comparte `_fichas`; `_perseguidor = None`; `al_ejecutar_evento = None`; `bitacora = Bitacora()` nueva; `estado.historial = Historial(limite=None)`; el resto se copia con el `memo` recibido.
  
  Usar solo el `memo` que entrega `copy`: ningún `dict` propio como índice (principio I). Hace pasar T005.

  *Hecho, con dos ajustes encontrados al implementar*:
  - `Mapa.__deepcopy__` copia en dos pasadas: primero registra en el `memo` una sala vacía por cada sala y después las llena (`Sala.copia_vacia`, `Sala.llenar_copia`). Con un `deepcopy` directo, la recursión baja por la cadena de salas vecinas y da `RecursionError` con el límite normal de Python ya con 300 salas (medido).
  - En Python 3.14, `copy` trata las funciones como atómicas y no consulta el `memo`, así que `Partida.__deepcopy__` fija `_fichas`, `_perseguidor = None` y `al_ejecutar_evento = None` después de copiar.
- [X] T011 [P] Crear `crypta/Modelo/Resumen.py` (D10; FR-406): clase `Resumen` con `pedido`, `reloj`, `proxima_accion`, `sala` (id, nombre), `vida`, `vida_max`, `ataque`, `defensa`, `velocidad`, `inventario` (`Vector` en `Inventario.orden_real`, con equipados y actual), `pergaminos`, `efectos`, `enemigos` (`Vector` de (id de instancia, nombre, vida) de los activos y vivos de la sala, en el orden del `Vector`), `mapa_conocido = None` mientras no exista la 002, y `aviso = None`. La función `armar_resumen(partida, pedido, aviso=None)` solo lee la partida.
- [X] T012 [P] Crear `crypta/Vista/FormatoResumen.py` (FR-406): función pura `formatear_resumen(resumen) -> str` con el texto exacto de `contracts/resumen.md`. Hace pasar T006 junto con T011.
- [X] T013 Punto de control (D3, D5, D9, D10; FR-406, FR-422, FR-426): `python -m unittest` en verde (T004–T006 pasan; P1, 001 y 003 siguen verdes) y commit «004 base: búsqueda binaria, historial sin límite, tope, copia y resumen».

**Punto de control**: una partida se puede copiar sin arrastrar red ni búsqueda, re-ejecutar hasta
un instante y resumir.

---

## Fase 3: Historia 1 — Consultar el pasado durante la partida (Prioridad 1) 🎯 MVP

**Objetivo**: `historia <t>` e `historia #k` dan el resumen del estado pedido, reconstruido hacia
adelante sobre el punto anterior y deshecho después (D2), sin tocar la partida viva.

**Prueba independiente**: partida sintética corta con comandos fijos; cada consulta se compara con
el oráculo.

### Pruebas de la historia 1 (escribir primero; deben fallar)

- [X] T014 [P] [HU1] Escribir `TestConsultas` en `tests/test_linea_tiempo.py` (FR-401 a FR-404), contra el oráculo de T003 con K = 3, 10 y 22:
  - HU1-1: reloj ≈ 1 200, `historia 500`: el texto muestra el reloj de ese estado, no el actual;
  - HU1-2: `historia <reloj+1>` se rechaza con el mensaje de contracts/cli.md (Apéndice B);
  - HU1-3: tres eventos en el mismo instante sin decisión → estado después de los tres (Apéndice B);
  - HU1-4: decisión en t y un evento posterior del mismo instante → estado antes de la decisión;
  - HU1-5: 40 acciones: `#1`, `#20` y `#41` (= estado actual);
  - HU1-6: `#0` y `#42` rechazados;
  - casos borde: `historia 0`, t = reloj actual, t entre dos eventos, consulta que cae justo en un punto.
- [X] T015 [P] [HU1] Escribir `TestComandoHistoria` en `tests/test_controlador.py` (FR-405, FR-409), con `controlador_sintetico`:
  - HU1-7: `historia`, `historia abc`, `historia -5`, `historia 2,5`, `historia #x` y `historia 3 4` → mismo tratamiento que un comando inválido de P1, y nada cambia;
  - HU1-10: con victoria y con derrota, el mensaje «La partida terminó: usa --replay <log> --hasta <t> para consultarla.»;
  - `historia` no aparece en `partida.log`.
- [X] T016 [P] [HU1] Escribir `TestConsultaNoCambiaNada` en `tests/test_linea_tiempo.py` (FR-407, FR-408; SC-403):
  - HU1-8: 30 consultas al azar. No cambian la serialización de la partida viva, `azar.getstate()`, `len(historial)` ni lo que deshace el pergamino, el reloj, `acciones_jugador`, el log, las solicitudes ni el presupuesto (Apéndice B).
  - HU1-9: la misma partida con y sin 30 consultas intercaladas: mismo estado, mismo log byte por byte y mismo resultado.
  - HU1-12: partida en línea con salas sin descargar y `FuenteQueFalla` después de iniciar; las consultas de instantes cerca de esas salas no hacen solicitudes.
  - D8: para el punto usado, `serializar_estado(punto, omitir_salas=salas que la consulta cargó)` es igual antes y después de 50 consultas, y repetir cada consulta da el mismo resumen.
  - FR-423: un contador de acciones re-ejecutadas y deshechas es ≤ K en cada consulta.
  - FR-425: un contador de puntos examinados es 1 en cada consulta.

### Implementación de la historia 1

- [X] T017 [HU1] Crear `crypta/Modelo/LineaDeTiempo.py` con `EntradaLinea`, `PuntoDeControl` y `Objetivo` exactamente como en data-model.md (D1, D5; FR-402, FR-422, FR-425):
  - `EntradaLinea`:
    - `tipo`: «`ACCION`, `NO_ACCION` o `AJUSTE`»;
    - `comando`: «texto ya traducido, el mismo que va a `partida.log`; vacío en `AJUSTE`»;
    - `reloj`: «`int ≥ 0`»;
    - `numero_accion`: «`int ≥ 1`»;
    - campos de ajuste: «solo en `AJUSTE`».
  - `PuntoDeControl(ancla, posicion, partida)`, con el invariante «a lo sumo un punto por múltiplo de K» y «el punto j está en la posición j del `Vector` de puntos».
  - `Objetivo(pedido, acciones_completas, tope, es_actual)`.
- [X] T018 [HU1] En `crypta/Modelo/LineaDeTiempo.py`, clase `LineaDeTiempo(k)` (D1, D5; FR-401 a FR-404, FR-417, FR-420, FR-422, FR-425):
  - `k` «`int ≥ 1`» (`ValueError` si no);
  - `entradas`, `decisiones` (reloj, posición) y `puntos` como `Vector`;
  - `iniciar(partida)`: primer punto con `copy.deepcopy`, con ancla a₀ = `partida.acciones_jugador` (0 en una partida nueva; las del estado cargado si el archivo no traía línea, T038); `ubicar_*` rechaza lo anterior a a₀;
  - `registrar(partida, comando, acciones_antes)` para +1 y 0: crea el punto si el total es múltiplo de K y no existe;
  - `ubicar_instante(t, reloj_actual)` con `primera_no_menor` sobre `decisiones` (empate → primera);
  - `ubicar_accion(k)` con rango [1, n + 1];
  - `cantidad_acciones()`;
  - contador `puntos_examinados` para FR-425;
  - el rechazo lleva los mensajes de contracts/cli.md (excepción `ConsultaRechazada`).
  
  Sin `dict` ni `bisect`.

  *Hecho.* `registrar` recibe también `reloj_antes`: el reloj de la decisión, que después del comando ya no se puede leer. Hasta T026, un pergamino (−1) dejaba la línea marcada y toda consulta posterior se rechazaba; T026 quitó ese rechazo.
- [X] T019 [HU1] Crear `crypta/Modelo/Reconstruccion.py` (D2, D7, D8; FR-401, FR-407, FR-421, FR-423). Función `consultar(linea, objetivo, partida_viva, reejecutar)` → `Resumen`:
  - si `es_actual` es verdadero, `armar_resumen(partida_viva, …)`;
  - si no, punto j = ⌊m/K⌋ y `Sello`: `terminada`, `resultado`, `puerta_de_salida_abierta`, `enemigos_derrotados`, pergaminos del inventario, nodo del objeto actual, largo de la bitácora, `agenda.siguiente_secuencia` y un `Vector` de (sala, pergaminos) de cada sala donde entra el jugador;
  - re-ejecuta las entradas desde `punto.posicion` con `reejecutar(copia, comando, garantizar)`, donde `garantizar` busca la sala en `partida_viva.mapa` y hace `asignar_contenido(sala_viva.contenido)` en la del punto, o lanza `RuntimeError` si la viva no está cargada; nunca hay red;
  - la última acción corre con `tope_tiempo = t` si el objetivo lo pide;
  - arma el resumen;
  - deshace con `historial.deshacer_ultima` tantas veces como acciones re-ejecutó;
  - restaura el sello y `tope_tiempo = None`. **Ojo**: `Agenda.restaurar_secuencia` solo acepta una agenda nueva (lanza `ValueError` si no), así que el sello necesita un método nuevo de `Agenda`, por ejemplo `rebobinar_secuencia(n)` con n ≤ la actual. Encontrado en T005, donde la prueba restaura el número de secuencia a mano;
  - **no** descarga ni deshace la carga de contenido de las salas cargadas (decisión del grupo, D7);
  - contador de acciones re-ejecutadas para FR-423.
  
  `reejecutar` se inyecta: Modelo no importa Controlador.

  *Hecho.* Agregados a P1, sin cambiar su comportamiento:
  - `Agenda.rebobinar_secuencia(n)`, que rechaza n mayor que el actual o con un evento pendiente de secuencia ≥ n;
  - `Inventario.nodo_actual` y `Inventario.poner_nodo_actual`;
  - `Sala.estado_de_pergaminos` y `Sala.restaurar_estado_de_pergaminos`.

  El sello guarda, además, los objetos de cada sala donde entra el jugador, porque `apartar_pergaminos` los cambia fuera del historial. Al restaurar deja la bitácora del punto vacía e invalida su búsqueda del cazador.
- [X] T020 [HU1] En `crypta/Controlador/Comandos.py` (D12; FR-408, FR-413):
  - agregar `ejecutar_y_registrar(partida, linea, comando, garantizar_sala)`: llama a `ejecutar_comando` y, si no lanzó, pasa a `linea.registrar(partida, comando, acciones_antes)`;
  - agregar `leer_historia(texto)` → (`"instante"`, t) o (`"accion"`, k). Solo dígitos ASCII; cualquier otra forma lanza `ComandoInvalido` (FR-405).
- [X] T021 [HU1] En `crypta/Controlador/Controlador.py` (FR-403 a FR-409):
  - `Controlador` recibe `k` (por omisión, el K por defecto: constante `K_POR_DEFECTO = 22` en `crypta/Modelo/LineaDeTiempo.py`, research D4) y crea `self.linea` al iniciar la partida (`linea.iniciar` después de `Partida.iniciar`);
  - `procesar_comando` reconoce `historia` **antes** de `_traducir`: con la partida terminada, el mensaje de FR-409; si no, `leer_historia` → `ubicar_*` → `consultar(…, reejecutar=ejecutar_comando)` → `vista.mostrar_resumen`;
  - los comandos de juego pasan por `ejecutar_y_registrar`;
  - `historia` nunca se anota en el log.

  *Hecho, con un ajuste*: el `Controlador` sigue llamando a `ejecutar_comando` por su nombre de módulo y anota la línea él mismo, con la misma regla que `ejecutar_y_registrar`. Así las pruebas de P1 que reemplazan `Controlador.ejecutar_comando` siguen pasando (SC-408). Además, la línea solo se arma sobre una `Partida` del Modelo, no sobre un doble de prueba. Al cargar una partida se crea una línea nueva desde el estado cargado, hasta T038.
- [X] T022 [P] [HU1] En `crypta/Vista/VistaConsola.py`: `mostrar_resumen(resumen)` imprime `formatear_resumen(resumen)`; la ayuda agrega `historia <t> | #k   Ver cómo estaba la partida` (contracts/cli.md; FR-406).
- [X] T023 [HU1] Punto de control (FR-401 a FR-409, FR-423, FR-425): T014–T016 pasan, `python -m unittest` en verde (891 pruebas, 1 omitida que ya existía) y commit «004 HU1: historia durante la partida» (lo hace el grupo).

**Punto de control**: el MVP funciona sin pergaminos, guardado ni replay.

### Bloqueada por la 002

- [ ] T057 [HU1] **Bloqueada por la 002.** Escribir `TestMapaConocidoEnHistoria` en `tests/test_linea_tiempo.py` (FR-406; HU1-11) y completar la línea «Mapa conocido» del resumen en `crypta/Modelo/Resumen.py` y `crypta/Vista/FormatoResumen.py`. En un instante en que el jugador recordaba una puerta abierta que después observó cerrada, `historia` muestra el mapa conocido de ese instante, no el actual, y coincide con el oráculo. Se hace al implementar la 002, y **el plan de la 002 la debe incluir**. El mapa conocido entra en el historial (constitución VII), así que la reconstrucción de T019 lo deshace sin cambios en el sello. Hasta entonces, el resumen imprime la línea fija de contracts/resumen.md.

---

## Fase 4: Historia 2 — La línea de tiempo respeta el pergamino (Prioridad 2)

**Objetivo**: lo revertido deja de existir en la línea; `#k` se renumera; el recorte cuesta lo
revertido (D6).

**Prueba independiente**: se juega, se usa un pergamino y se compara con el oráculo y con una partida
que nunca hizo esas acciones.

### Pruebas de la historia 2 (escribir primero; deben fallar)

- [X] T024 [P] [HU2] Escribir `TestPergamino` en `tests/test_linea_tiempo.py` (FR-410 a FR-412):
  - HU2-1: 30 acciones y 3 pergaminos; ninguna consulta muestra lo revertido; `#28` = estado actual; `#29` se rechaza (Apéndice B);
  - HU2-2: `historia <t>` con t > el reloj que quedó se rechaza;
  - HU2-3: con acciones nuevas después del pergamino, cada resumen es igual al de una partida que hizo directamente las acciones que quedaron, salvo los pergaminos gastados, los pergaminos de las salas y la posición del objeto actual del inventario (se comparan los textos con esas líneas normalizadas), e igual al oráculo sin normalizar;
  - HU2-4: el pergamino quita a lo sumo las entradas y puntos revertidos; con 100 y con 2 000 acciones previas, el contador de entradas examinadas es el mismo;
  - casos borde: pergamino que revierte la acción de un ancla (el punto desaparece y se vuelve a crear al llegar otra vez a ese total); pergamino justo después de crear un punto; consulta inmediatamente después del pergamino; `avanzar` después de la acción revertida.
- [X] T025 [P] [HU2] Escribir `tests/test_equivalencia_linea.py` (FR-421; SC-402): al menos 20 partidas por semilla con `partida_con_pergaminos` y `comandos_al_azar` (≥ 150 comandos, con pergaminos), con K = 1, 10, 22 y un K mayor que n (solo el punto 0, como la alternativa sin puntos). El 100 % de las consultas `#k`, y una de cada evento del oráculo por `t`, son iguales al oráculo.

### Implementación de la historia 2

- [X] T026 [HU2] En `crypta/Modelo/LineaDeTiempo.py`, `revertir(partida)`, llamado por `registrar` cuando `acciones_jugador` bajó en 1 (D6; FR-410 a FR-412):
  - quita del final las entradas hasta la última `ACCION` incluida, y su fila de `decisiones`;
  - quita los puntos cuya `ancla` supera el nuevo total;
  - agrega una entrada `AJUSTE` con `pergaminos_inventario`, `posicion_actual` (índice del objeto actual en `orden_real`, o `None`) y `pergaminos_sala` de la sala actual.
  
  Costo O(lo revertido). Contador de entradas examinadas para HU2-4.

  *Hecho.* El contador es `ultimas_examinadas`. Si el pergamino revierte una acción anterior a la línea (una línea creada a mitad de partida, por ejemplo al cargar), la línea se reinicia desde el estado actual, en vez de fallar. Se agregaron a P1, sin cambiar su comportamiento, `Inventario.poner_actual_por_posicion` y `Sala.fijar_pergaminos`.
- [X] T027 [HU2] En `crypta/Modelo/Reconstruccion.py`, aplicar las entradas `AJUSTE` al re-ejecutar: fija pergaminos del inventario, el objeto actual por posición y los pergaminos de la sala actual. El sello de T019 ya los restaura (D6, D8; FR-410, FR-421).
- [X] T028 [HU2] Punto de control (FR-410 a FR-412, FR-421): T024 y T025 pasan, `python -m unittest` en verde (899 pruebas, 1 omitida que ya existía) y commit «004 HU2: línea de tiempo con pergamino» (lo hace el grupo). La equivalencia de T025 (20 partidas × 4 K) tarda unos 40 s, casi todo en la variante sin puntos de control.

---

## Fase 5: Historia 3 — Consultar un `partida.log` sin jugar (Prioridad 3)

**Objetivo**: `--replay log --hasta t` imprime el mismo resumen que `historia t`, sin vista (D12).

**Prueba independiente**: se reproduce un log conocido con distintos `--hasta` y se compara con lo
que dio `historia` en la partida original.

### Pruebas de la historia 3 (escribir primero; deben fallar)

- [X] T029 [P] [HU3] Escribir `tests/test_replay_hasta.py` (FR-413 a FR-416), llamando a `main` con argumentos y una fuente sin conexión en carpeta temporal:
  - HU3-1: `--hasta 500` imprime exactamente el texto que dio `historia 500` en la partida, con una vista que falla si se instancia;
  - HU3-2: partida terminada antes de t → último estado + «La partida terminó en el instante <r>, antes de <t>.», código 0 (Apéndice B);
  - HU3-3: log que acaba antes de t → «El log termina en el instante <r>, antes de <t>.», código 0; log ilegible → código 1;
  - HU3-4: `--hasta 500` sin `--replay`, `--hasta -1` y `--hasta x` → error de argumentos sin iniciar partida;
  - HU3-5: log con pergamino → resumen sin lo revertido.

### Implementación de la historia 3

- [X] T030 [HU3] En `crypta/Controlador/Reproductor.py` (D12; FR-413): `reproducir_registro(…, k=K_POR_DEFECTO)` crea una `LineaDeTiempo(k)`, la inicia después de `partida.iniciar()` y ejecuta cada comando con `ejecutar_y_registrar`. `Reproduccion` agrega el atributo `linea`. Los errores no cambian.
- [X] T031 [HU3] En `crypta/main.py` (FR-414 a FR-416; contracts/cli.md):
  - argumento `--hasta t` (entero ≥ 0, con un `type` propio que rechaza negativos y no enteros);
  - `parser.error` si viene sin `--replay`;
  - en `reproducir(args)`, si hay `--hasta`: ubica t en `resultado.linea` (o el último estado con el aviso de FR-415 si t > reloj final), `consultar` y `print(formatear_resumen(...))`, código 0;
  - sin `--hasta`, la salida actual no cambia;
  - nunca se instancia la vista.

  *Hecho.* El resumen va en `mostrar_hasta(resultado, t)`. Con t posterior al final, se resume la partida reproducida con el pedido «instante <t>» y el aviso en la línea «Aviso:» (contracts/resumen.md). `reproducir` lee `hasta` con `getattr` porque las pruebas de P1 arman `args` sin ese campo.
- [X] T032 [HU3] Punto de control (FR-413 a FR-416): T029 pasa, `python -m unittest` en verde (906 pruebas, 1 omitida que ya existía) y commit «004 HU3: --replay … --hasta» (lo hace el grupo).

---

## Fase 6: Historia 4 — Guardar y cargar con la línea de tiempo (Prioridad 4)

**Objetivo**: formato 3 con el bloque `linea`, escrito con el recorrido de `EstadoPartida`; rechazo
de los formatos 1 y 2 (D11).

**Prueba independiente**: guardar, cargar y comparar consultas; intentar cargar archivos viejos.

### Pruebas de la historia 4 (escribir primero; deben fallar)

- [X] T033 [P] [HU4] Escribir `TestLineaGuardada` en `tests/test_persistencia.py` (FR-417 a FR-419; contracts/guardado.md):
  - HU4-1: 200 acciones con pergaminos; guardar en binario y en JSON; cargar; 50 consultas `t` y `#k` dan el mismo texto que antes de guardar; la partida sigue y termina igual que sin guardar;
  - HU4-2: guardada con K = 10 y cargada con un controlador con K = 50 → aviso «La partida guardada usa --checkpoint-cada 10; se usa ese valor.» y K = 10;
  - HU4-3: archivo de P1 (formato 1) → «formato incompatible» y la partida en curso no cambia (Apéndice B);
  - HU4-4: archivo de la 001 (formato 2), igual;
  - archivo con anclas con huecos, posiciones no crecientes o relojes que no suben → `ErrorGuardado`;
  - `guardar_partida(partida, ruta, encabezado)` **sin** línea escribe un bloque `linea` vacío (solo K); `cargar_partida` devuelve solo la partida y `archivo.linea is None`; el `Controlador` crea entonces una línea nueva con el punto inicial en el estado cargado, y `historia #k` de una acción anterior a la carga se rechaza;
  - con línea, `cargar_partida` sigue devolviendo solo la partida y la línea queda en `archivo.linea` (binario y JSON).
- [X] T034 [P] [HU4] Actualizar en `tests/test_persistencia.py` las pruebas que comprueban el número de formato del archivo de partida para que esperen el formato 3. Solo esas cambian: las demás llamadas a `guardar_partida` y `cargar_partida` siguen iguales porque las firmas no cambian (FR-419; SC-408).

### Implementación de la historia 4

- [X] T035 [HU4] *(Hecho: `leer_linea(l, encabezado, fichas)` recibe también el encabezado, que necesita `armar_partida`; la validación está en `LineaDeTiempo.desde_guardado`, en el Modelo.)* En `crypta/Adaptadores/EstadoPartida.py` (D11; contracts/guardado.md; FR-417 a FR-419), con el escritor y el lector abstractos existentes:
  - `escribir_linea(e, linea, k)`: con `linea = None`, solo `k` y las listas `entradas` y `puntos` vacías; si no, k, la lista de entradas (`tipo` 0/1/2, `comando`, `reloj`, `numero_accion` y los tres `entero_opcional` del ajuste) y la lista de puntos (`ancla`, `posicion`, grupo `general` con `escribir_general(e, punto.partida)` y lista `salas` con `escribir_sala` de cada sala del punto);
  - `leer_linea(l, fichas)`: devuelve `None` si el bloque está vacío; si no, arma cada punto con `armar_partida`, le pone `Historial(limite=None)`, una `Bitacora()` nueva y `_perseguidor = None`, y reconstruye `decisiones` en O(n);
  - valida anclas a₀, a₀ + K, a₀ + 2K… sin huecos, posiciones crecientes y relojes que suben estrictamente; si algo falla, `ErrorGuardado`.
- [X] T036 [HU4] En `crypta/Adaptadores/GuardadoBinario.py` (FR-417, FR-419; contracts/guardado.md): `FORMATO_GUARDADO = 3`; el bloque `linea` va después de los registros de sala, con su posición y su largo en la cabecera. **Las firmas no cambian**: `guardar_partida(partida, ruta, encabezado, linea=None)` (sin línea, bloque vacío con el K por defecto) y `ArchivoGuardado.cargar_partida(fichas)` sigue devolviendo solo la partida; la línea leída queda en `self.linea` (`None` si el bloque estaba vacío), no en la `Partida` (D12). El rechazo de otros formatos queda igual. Las llamadas existentes de `tests/` y `crypta/bench/bench.py` no se tocan.

  *Hecho, con un ajuste*: el bloque `linea` **no** lleva su posición ni su largo en la cabecera. Va entre la última sala y el índice: empieza donde termina el último registro de sala y llega hasta el índice. Así la cabecera de 22 bytes no cambia y siguen pasando, sin tocarlas, las pruebas de P1 que leen sus campos por posición (SC-408). El mensaje de rechazo ahora empieza con «Formato incompatible:» (`mensaje_de_formato`, que comparte el JSON). contracts/guardado.md ya lo dice.
- [X] T037 [HU4] En `crypta/Adaptadores/GuardadoJSON.py`: `FORMATO_JSON = 3`, el mismo bloque `linea` con `EscritorJSON`/`LectorJSON`, `guardar_partida_json(…, linea=None)` y `ArchivoGuardadoJSON.linea` después de `cargar_partida`, que sigue devolviendo solo la partida (FR-417, FR-419).
- [X] T038 [HU4] En `crypta/Controlador/Controlador.py` (FR-417, FR-418): `guardar` pasa `linea=self.linea`; `cargar_partida` toma `archivo.linea` después de `archivo.cargar_partida(...)`. Si no es `None`, avisa si `self.k != linea.k` con el texto de HU4-2 y adopta la línea cargada. Si es `None`, crea `LineaDeTiempo(self.k)` e `iniciar(nueva_partida)` con el punto inicial en el estado cargado (ancla a₀ = `acciones_jugador` cargadas, data-model.md).

  *Hecho, y además*:
  - `guardar` sigue llamando a `guardar_partida` con 3 argumentos cuando no hay línea, que es lo que espera la prueba de P1 con partida falsa.
  - Hueco de P1 que afectaba a FR-419: `procesar_comando("cargar")` no atrapaba `ErrorGuardado`, así que un archivo incompatible terminaba el programa. Ahora muestra el rechazo y la partida en curso no cambia (prueba en T033).
- [X] T039 [HU4] Punto de control (FR-417 a FR-419): T033 y T034 pasan, `python -m unittest` en verde (913 pruebas, 1 omitida que ya existía) y commit «004 HU4: guardado formato 3 con la línea de tiempo» (lo hace el grupo).

---

## Fase 7: Historia 5 — Puntos de control y medición (Prioridad 5)

**Objetivo**: `--checkpoint-cada K`, y las secciones L1–L8 de `--bench` que eligen y defienden el K
por defecto (contracts/bench.md).

**Prueba independiente**: misma partida con distintos K; `--bench` dos veces con la misma semilla.

### Pruebas de la historia 5 (escribir primero; deben fallar)

- [X] T040 [P] [HU5] Escribir `TestCheckpointCada` en `tests/test_controlador.py` (FR-420, FR-422, FR-424, FR-426):
  - HU5-4: `--checkpoint-cada 0`, `-3`, `x` y `2.5` → error de argumentos;
  - `--help` muestra el K por defecto;
  - HU5-1: la misma partida con K = 1, 10, 100 y el K por defecto da resúmenes idénticos;
  - HU5-3: 5 000 acciones con K = 10 → anclas 0, 10, 20…, y entre ellas solo entradas;
  - HU5-11: el log de una partida de la 001 reproducido con y sin línea da el mismo estado final (`serializar_estado`) y el mismo resultado.
- [X] T041 [P] [HU5] Escribir las pruebas de la línea de tiempo en `tests/test_bench.py` (FR-427 a FR-431):
  - HU5-5: huella repetible de `partida_linea` con la misma semilla;
  - L1–L8 corren en modo rápido (acciones y consultas reducidas);
  - HU5-6: L3 con una variante saboteada (reconstrucción que salta una acción) imprime ERROR y `ejecutar` devuelve un código ≠ 0;
  - HU5-12: fuente y vista que fallan si se usan;
  - L1, L4 y L5 calculan y reportan sus cocientes y su «¿cumple?».

### Implementación de la historia 5

- [X] T042 [HU5] En `crypta/main.py` (FR-420; contracts/cli.md): argumento `--checkpoint-cada K`, con un `type` propio para enteros ≥ 1 y `default=K_POR_DEFECTO`. El ayuda dice el valor. Se pasa al `Controlador` (T021) y a `Reproductor.reproducir_registro` (T030).
- [X] T043 [HU5] Crear `crypta/bench/bench_linea.py`, el generador (FR-427; contracts/bench.md). `partida_linea(cripta, semilla, acciones)`:
  - **(a)**: cripta-06 si la copia local tiene contenidos (se comprueba en `AlmacenDisco`, sin red). Si no, una sintética de 300 salas en cuadrícula con costos variables, puertas abiertas, cerradas y con llave, armas, armaduras, pociones, pergaminos de retroceso y **20 enemigos activos** repartidos.
  - **(b)**: `partida_con_cazadores(50)` de `crypta/bench/bench_ciclo.py` con los mismos objetos y pergaminos.
  - Jugador con `vida_max = 10**9`. Acciones mezcladas y deterministas con un `random.Random(semilla)` propio: ≥ 5 000 netas en (a) y ≥ 1 000 en (b), con **un `pergamino` de retroceso cada 50 acciones** (contracts/bench.md); las rechazadas no cuentan.
  - Huella: las cantidades del generador (salas, enemigos activos, acciones, intervalo de pergaminos), los comandos, el reloj final y `serializar_estado` final (de `crypta/bench/oraculo_linea.py`).
  - Consultas: ≥ 200 repartidas con la semilla, mitad `#k` y mitad `t`, algunas entre dos decisiones.
- [X] T044 [HU5] En `crypta/bench/bench_linea.py`, la variante **hacia atrás** solo para el bench (D2; FR-429): `PuntoFinal` B_j = copia de C_j con las K acciones del tramo re-ejecutadas y su historial sin límite. La consulta deshace desde el final hasta el objetivo, resume y vuelve re-ejecutando. Reporta el costo de crear cada B_j y la memoria de sus cambios.
- [X] T045 [HU5] En `crypta/bench/bench_linea.py`, **L1** (FR-428, FR-432, SC-404, SC-406; principio VI «Consulta de historia 50 ms»):
  - (a) con K = 10, 16, 22, 32 y 64, y sin puntos de control (solo el punto 0, 20 consultas);
  - **la línea de cada K se libera (`del` y `gc.collect()`) antes de armar la siguiente**;
  - (b) solo el K por defecto con 1 000 acciones;
  - reporta media, p95 (`Medicion.percentil` de la 001) y máximo de la consulta y tiempo total de crear los puntos, **medidos con `tracemalloc` apagado**;
  - la memoria de la línea se mide en **una corrida aparte** con la misma semilla y `tracemalloc` encendido, sin medir tiempos;
  - «¿cumple?» p95 < 50 ms solo para (a) con el K por defecto; (b) sin límite, con la nota «si pasa de 50 ms va a Límites»;
  - cada fila dice qué cripta usó.
- [X] T046 [HU5] En `crypta/bench/bench_linea.py`, **L2** (FR-429): adelante frente a atrás en (a) con el K por defecto, con consulta (media, p95), creación por punto y memoria. **L3** (FR-430): todas las variantes de L1 (a) y la de atrás contra el oráculo de `jugar_con_oraculo` (`crypta/bench/oraculo_linea.py`; el bench no importa nada de `tests/`). Cuenta comparadas y diferencias; cualquier diferencia → ERROR y código ≠ 0.
- [X] T047 [HU5] En `crypta/bench/bench_linea.py`, **L4** (FR-433, SC-405; principio VI «Ciclo de eventos 20 ms»): el escenario B7 (`medir_ciclo_cazadores` de `crypta/bench/bench_ciclo.py`) con y sin línea, con el K por defecto y ≥ 500 acciones medidas, de modo que la fracción de copias sea 1/K. Reporta media, p95, máximo y ciclos que copiaron. «¿cumple?» p95 < 20 ms.
- [X] T048 [HU5] En `crypta/bench/bench_linea.py`, **L5**, **L6**, **L7** y **L8**. Ningún tiempo se mide con `tracemalloc` encendido; la memoria siempre va en una corrida aparte:
  - L5 (FR-424, FR-434, SC-409): memoria con 2 500 y 5 000 acciones, mismo K, cociente ≤ 2,5; con el K por defecto frente a la copia por acción estimada (acciones × tamaño medido de una copia, sin materializarla), < 1/3;
  - L6 (FR-425): puntos examinados por consulta con 2 500 y 5 000 acciones;
  - L7 (D3): `deepcopy` sin ganchos, con ganchos (la elegida) y por el recorrido de `EstadoPartida`, en (a) y (b): tiempo sin `tracemalloc` y memoria en una corrida aparte;
  - L8 (FR-417, D11): tamaño y tiempo de guardar y cargar 5 000 acciones en binario.
- [X] T049 [HU5] En `crypta/bench/bench.py` (FR-427 a FR-431): registrar las secciones L1–L8 en `SECCIONES` con los nombres `linea_l1` … `linea_l8` (contracts/bench.md), para poder correrlas solas, con el modo rápido que use `tests/test_bench.py`. El código de salida es ≠ 0 si L3 falla. Hace pasar T041.

  *Hecho, con ajustes en `crypta/bench/bench_linea.py`*:
  - La cripta (a) es la copia local **más grande** solo si tiene todo su contenido; si no, la sintética. Hoy `cache/` tiene copias chicas con contenido, y la regla «la más grande con contenido» las habría elegido.
  - La memoria de la línea se mide con `tracemalloc` sobre una copia de sus entradas y puntos, no volviendo a jugar la partida.
  - L3 usa 1 000 acciones y hasta 300 entradas del oráculo por variante.
  - En modo rápido, L7 mide solo (a): las copias de 2 000 salas con `tracemalloc` tardan minutos.
  - La variante hacia atrás guarda en cada frontera entre entradas lo que el historial de P1 no devuelve (pergaminos, objeto a la vista, pergaminos de las salas del tramo), y no rebobina la secuencia al volver. Con eso da los mismos resúmenes que el oráculo.

  contracts/bench.md quedó actualizado.
- [ ] T050 [HU5] **La hace el grupo.** Correr **solo** las secciones L1 a L8, no el bench completo (requiere T001): `python -m crypta.bench.bench linea_l1 linea_l2 linea_l3 linea_l4 linea_l5 linea_l6 linea_l7 linea_l8 --guardar docs/resultados_bench_004.txt`. Si L1 (a) con K = 22 da p95 ≥ 50 ms o L4 da p95 ≥ 20 ms, **parar**: elegir K según research D4 con los números medidos, cambiar `K_POR_DEFECTO` y volver a correr. Si ningún K cumple las dos, documentarlo antes de cambiar el diseño (principio VI; FR-432, FR-433).
- [X] T051 [HU5] Punto de control (FR-420, FR-427 a FR-434): T040 y T041 pasan, `python -m unittest` en verde (930 pruebas, 1 omitida que ya existía; el bench en modo rápido tarda unos 70 s dentro de la suite) y commit «004 HU5: --checkpoint-cada y --bench de la línea de tiempo» (lo hace el grupo). T050 queda para el grupo.

---

## Fase 8: Cierre (documentación y revisión)

- [X] T052 [P] Escribir `DECISIONES.md` §5.5 «Línea de tiempo» desde research.md (principio X; FR-420, FR-432 a FR-434): problema, alternativas (D1–D3), decisión, complejidad, evidencia de L1–L8 de `docs/resultados_bench_004.txt`, enlaces a spec y plan, y si el K final coincide con el plan (22) y, si no, qué medición lo cambió. En **Límites**:
  - la partida de escala (p95 de L1 (b), pausa de la copia de L4, memoria);
  - el margen de FR-433;
  - que las salas cargadas durante una consulta quedan cargadas en el punto (D7);
  - que, por eso, el archivo guardado de una partida con consultas no es igual byte por byte al de la misma partida sin consultas; el estado, el log y el resultado sí (D11; FR-408).
  
  Volver a medir el historial de retroceso de P1 con la carga nueva (principio XI) con los números de deshacer de L1 y L2.
- [X] T053 [P] Actualizar `README.md` (principio X; FR-403, FR-404, FR-413 a FR-416, FR-419, FR-420): `historia <t>` e `historia #k`, `--checkpoint-cada K` con el K por defecto y por qué, `--replay … --hasta`, el formato 3 del archivo de partida (los anteriores se rechazan) y cómo correr las pruebas de aceptación de la 004.
- [ ] T054 [P] **La hace el grupo.** Registrar en `PROMPTS_LLM.md` las invocaciones de `/speckit-plan` (con sus ajustes), `/speckit-tasks` y `/speckit-analyze` de la 004 y sus arreglos, con fecha, herramienta, texto y uso (principio X; trazabilidad de FR-401 a FR-434).
- [X] T055 (FR-422, FR-424, FR-426) Revisar imports prohibidos en los archivos nuevos y cambiados (`grep` de `dict(`, `set(`, `{}` como estructura, `bisect`, `heapq`, `collections`, `sorted(`, `.sort(`) y que no haya ids ni números de cripta en el código (principios I y IV). Recorrer `quickstart.md` de punta a punta. Confirmar que `spec.md` sigue coincidiendo con el programa (principio VIII).
- [X] T056 Punto de control final (FR-426; SC-408): `python -m unittest` completo en verde (932 pruebas, 1 omitida que ya existía) y commit «004 cierre: DECISIONES §5.5 y README» (el commit lo hace el grupo).

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1**: T001 primero (commit de spec), después T002; T003 no depende de ellas.
- **Fase 2**: depende de T003; bloquea todas las historias.
- **HU1 (fase 3)**: depende de la fase 2. Es el MVP.
- **HU2 (fase 4)**: depende de HU1 (T017–T020).
- **HU3 (fase 5)**: depende de HU1 (T018–T020). Puede ir en paralelo con HU2; T029 HU3-5 necesita HU2.
- **HU4 (fase 6)**: depende de HU1 y HU2 (el ajuste se guarda).
- **HU5 (fase 7)**: T042 depende de T021 y T030; T043–T048 dependen de HU2; T050 depende de T001 y de T049.
- **Cierre (fase 8)**: depende de T050.
- **T057**: bloqueada por la 002; se hace al implementar la 002 y no bloquea la entrega de esta capacidad, que mientras tanto muestra la línea fija del mapa conocido.

### Dentro de cada historia

Pruebas → modelo → controlador y vista → punto de control. Las pruebas deben fallar antes de
implementar.

### Archivos con varias tareas (no se reparten a la vez)

| Archivo | Tareas, en orden |
|---|---|
| `tests/test_linea_tiempo.py` | T005, T014, T016, T024, T057 |
| `tests/test_controlador.py` | T015, T040 |
| `tests/test_persistencia.py` | T033, T034 |
| `crypta/Modelo/Partida.py` | T009, T010 |
| `crypta/Modelo/LineaDeTiempo.py` | T017, T018, T026 |
| `crypta/Modelo/Reconstruccion.py` | T019, T027 |
| `crypta/Controlador/Controlador.py` | T021, T038 |
| `crypta/main.py` | T031, T042 |
| `crypta/bench/bench_linea.py` | T043 → T044 → T045 → T046 → T047 → T048 |

---

## Ejemplos de trabajo en paralelo

### Fase 2

```text
Integrante A: T004 → T007 (BusquedaBinaria)
Integrante B: T005 → T008 → T009 → T010 (Historial, tope, copia)
Integrante C: T006 → T011 → T012 (Resumen y su texto)
```

### Historia 1

```text
Integrante A: T014, T016 → T017 → T018 → T019 (Modelo)
Integrante B: T015 → T020 → T021 (Controlador)
Integrante C: T022 (Vista)
```

### Historias 2 y 3

```text
Integrante A: T024, T025 → T026 → T027 (pergamino)
Integrante B: T029 → T030 → T031 (replay --hasta)
```

### Historias 4 y 5

```text
Integrante A: T033, T034 → T035 → T036, T037 → T038
Integrante B: T040, T041 → T042 → T043 → … → T049
Integrante C: T052–T054 en cuanto exista docs/resultados_bench_004.txt
```

---

## Estrategia de implementación

### MVP primero

1. Fases 1 y 2.
2. Fase 3 (HU1): `historia` correcta y sin efectos. **Validar** con `python -m unittest`.
3. Fase 4 (HU2): sin ella, la línea mostraría estados que ya no existen.

### Entrega incremental

Cada fase termina en un commit con todo en verde. Si el tiempo no alcanza, lo que queda fuera es
de las últimas fases; nunca se deja una fase a medias sin su punto de control. La medición (T050)
no se puede omitir: el K por defecto se defiende con ella.

### Calendario sugerido (entrega el miércoles 18 de noviembre)

| Día | Fases |
|---|---|
| Sáb 14 | Fase 1 (T001 primero) y fase 2 |
| Dom 15 | Fase 3 (HU1) y fase 4 (HU2) |
| Lun 16 | Fase 5 (HU3) y fase 6 (HU4); empezar el generador del bench (T043) |
| Mar 17 | Fase 7 (HU5, con T050) y fase 8 (cierre) |

---

## Notas

- [P] = otro archivo y sin dependencias pendientes.
- Cada prueba cita su FR en el nombre del método o en el docstring (principio IX); los escenarios
  se nombran HUx-n en el docstring. Los 6 casos de «Línea de tiempo» del Apéndice B están en T014
  (HU1-2, HU1-3), T016 (HU1-8), T024 (HU2-1), T029 (HU3-2) y T033 (HU4-3).
- Comprobar que cada prueba falla antes de implementar.
- Nunca usar `cache/` en las pruebas: siempre un `AlmacenDisco` en una carpeta temporal.
- HU1-11 (mapa conocido en el instante consultado) es **T057, bloqueada por la 002**: se hace al
  implementar la 002 y el plan de la 002 la debe incluir. Hasta entonces el resumen muestra la línea
  fija «Mapa conocido: no disponible (capacidad 002)» (supuesto de la spec).
- T050 (bench de la 004) y T054 (`PROMPTS_LLM.md`) las hace el grupo.
- Si una tarea encuentra un caso que la spec no cubre, se para y se corrige primero la spec
  (principio VIII).
