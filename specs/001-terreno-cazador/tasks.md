---

description: "Lista de tareas de la capacidad 001 — Terreno y cazador"
---

# Tareas: Terreno y cazador

**Entrada**: documentos de diseño en `specs/001-terreno-cazador/`

**Requisitos previos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: obligatorias (constitución, principio IX; SC-001). Cada escenario de aceptación tiene
una tarea de prueba que cita su FR en el nombre del método o en el docstring. Las pruebas de una
historia se escriben **antes** de implementarla y deben **fallar** al escribirse (salvo la de FR-008,
que protege lo que ya funciona y debe pasar desde el primer día).

**Organización**: por fases y, dentro de ellas, por historia de usuario. Cada tarea dura una o dos
horas, cita los FR que atiende y nombra el archivo que toca.

**Entrega**: miércoles 18 de noviembre de 2026. Las historias 1 y 2 van primero porque son las que
más pesan; ver «Calendario sugerido» al final.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo con las demás [P] de su bloque: toca otro archivo y no depende
  de una tarea sin terminar.
- **[HUx]**: historia de usuario de spec.md (HU1 terreno, HU2 cazador, HU3 equivalencia, HU4 bench).
- «HUx-n» es el escenario de aceptación n de la historia x.
- Rutas relativas a la raíz del repositorio. `DECISIONES.md` está en la raíz.

---

## Fase 1: Preparación

**Propósito**: fijar la evidencia de la primera parte antes de tocar el código, y dejar listas las
ayudas que usan todas las pruebas nuevas.

**⚠️ T001 se hace antes de cualquier commit de código de la 001.**

- [ ] T001 Grabar `tests/datos/p1_partida.log` con el código actual (FR-008): antes de cualquier commit de código de la 001, sin cambios locales, jugar `python -m crypta.main --offline --cripta cripta-01 --semilla 2026 --jugador Prueba` con unos 40 comandos que pasen por mover, esperar, atacar, recoger, soltar, equipar, usar, abrir una puerta y usar un pergamino; copiar el `partida.log` resultante a `tests/datos/p1_partida.log`, y copiar los JSON de la primera parte desde Git con `git show 9c93927:cache/cripta-01.json > tests/datos/p1_cripta-01.json` y `git show 9c93927:cache/catalogo.json > tests/datos/p1_catalogo.json` (copias fijas: la prueba nunca lee `cache/`). Comprobar que los JSON copiados no tienen ningún campo `costo`.
- [ ] T002 Registrar el estado final esperado de esa partida en `tests/datos/p1_esperado.json` (FR-008): crear el script versionado `tests/datos/grabar_esperado_p1.py`, con una función de extracción del estado final que reutiliza T004; con el mismo código de T001, el script repite `tests/datos/p1_partida.log` sobre una copia temporal de los datos fijos (`AlmacenDisco` en una carpeta temporal, sin red) y escribe reloj final, sala, vida y resultado del jugador, cantidad de eventos ejecutados, mensajes en orden y `random.Random.getstate()` serializado.
- [ ] T003 [P] Crear `tests/ayudas_cripta.py` (habilita FR-001 a FR-027): funciones para armar esqueletos sintéticos pequeños a mano (salas, salidas con `costo` opcional, puertas cerradas, salidas sin vuelta), fichas de errante, rastreador y cazador (con `rango`), una `Partida` lista con jugador y enemigos en salas dadas, una fuente falsa que cuenta solicitudes (`obtener_catalogo`, `obtener_contenido`) y una fuente que falla si se la llama.
- [ ] T004 Escribir `TestCompatibilidadP1` en `tests/test_terreno.py` (FR-008, HU1-8): copia `tests/datos/p1_cripta-01.json` y `p1_catalogo.json` a una carpeta temporal, arma un `AlmacenDisco` sobre ella, repite `tests/datos/p1_partida.log` sin red, obtiene el estado final con la misma función de extracción de `tests/datos/grabar_esperado_p1.py` y lo compara con `tests/datos/p1_esperado.json` (mismos instantes, eventos, estado del azar y resultado). Esta prueba **debe pasar ya** con el código actual.
- [ ] T005 Punto de control (FR-008): `python -m unittest` en verde (pruebas de P1 + `TestCompatibilidadP1`) y commit «tareas 001: datos fijos de P1 y ayudas de prueba».

**Punto de control**: la primera parte queda grabada; desde aquí cualquier cambio que altere una
partida sin costos rompe `TestCompatibilidadP1`.

---

## Fase 2: Base común (costo en las puertas, DatosInvalidos, índices y entradas del mapa)

**Propósito**: lo que necesitan todas las historias: leer y validar el costo de cada salida, la
excepción propia y los índices densos y entradas que usan las búsquedas.

**⚠️ CRÍTICO**: ninguna historia empieza antes de terminar esta fase.

### Pruebas de la base (escribir primero; deben fallar)

- [ ] T006 [P] Escribir `TestCostoSalidas` en `tests/test_terreno.py` (FR-001, FR-002, FR-010; carga de HU1-12 y HU1-13): sin `costo` → 100; `"costo": null` cuenta como no declarado; solo un lado declara 250 → 250 en ambos sentidos y no se rechaza; ambos iguales → ese valor; lados 200 y 300 → `DatosInvalidos`; costo 0, `2.5`, `250.0`, `true` y `"250"` → `DatosInvalidos`. El mensaje nombra la sala, la dirección y el problema, como en `contracts/datos-servicio.md`.
- [ ] T007 Escribir `TestIndicesYEntradas` en `tests/test_terreno.py` (habilita FR-014, FR-018, FR-019, FR-036): cada sala tiene `indice` en 0..V−1 según el recorrido en orden del mapa, sin repetir; `entradas` de cada sala contiene los pares (Puerta, Sala origen) de las salidas y→x, incluida una salida sin vuelta; `EstadoPuerta.extremos` son las dos salas; el observador recibe aviso solo cuando `cerrada` cambia de valor (abrir, cierre automático y `setattr` del pergamino).
- [ ] T008 [P] Escribir en `tests/test_controlador.py` la prueba de arranque con datos inválidos (FR-010): `main` con una cripta cuya salida tiene costo 0 muestra el mensaje de `DatosInvalidos` y no crea la `Partida` ni la vista.

### Implementación de la base

- [ ] T009 [P] Crear `crypta/Modelo/DatosInvalidos.py` (FR-010, FR-011): excepción propia que **no** hereda de `ValueError` ni de `RuntimeError` (ver T054), con un mensaje que nombra la salida o la ficha y el problema.
- [ ] T010 Leer el costo crudo en `crypta/Modelo/Sala.py` (FR-001, FR-010): después de T009 y acordando con T011 la firma de `Puerta`; cada salida guarda el `costo` del JSON o `None` si falta o es `null`; si un lado declara un valor que no es entero JSON («rechaza `bool`, `float` y texto») o es < 1, lanza `DatosInvalidos` con «La salida <dir> de la sala A tiene un costo inválido: <valor>». Se pasa a `Puerta(..., costo=None)`.
- [ ] T011 Agregar el costo a `EstadoPuerta` en `crypta/Modelo/Puerta.py` (FR-001, FR-002, FR-010, FR-024): después de T009 y con la firma `Puerta(..., costo=None)` acordada con T010; constante única `COSTO_POR_OMISION = 100`; `Puerta.costo` como propiedad de solo lectura sobre el estado compartido; `compartir_estado_con` une los lados: ambos iguales → ese; solo uno → ese en ambos sentidos; ninguno → 100; distintos → `DatosInvalidos` «La salida entre las salas A (dir) y B (dir) declara costos distintos: x y y». Una puerta sin pareja (salida sin vuelta) queda con su costo o 100.
- [ ] T012 Agregar extremos y observador a `EstadoPuerta` en `crypta/Modelo/Puerta.py` (habilita FR-018, FR-019): campos `extremos` (Sala, Sala) y `observador` (referencia o None), ninguno es estado del juego; el setter de `cerrada` llama a `observador.puerta_cambio(estado)` solo si el valor cambia.
- [ ] T013 Asignar índices, entradas y extremos en `crypta/Modelo/Mapa.py` (FR-002, FR-010, habilita FR-014 y FR-036): al cargar, recorrer el `ArbolBusqueda` en orden y dar `indice` 0..V−1 a cada sala; armar `entradas` de cada sala en un `Vector` (O(V + E)); fijar `extremos` en `_compartir_puertas`, que llama a `Puerta.compartir_estado_con` (es esta la que valida los costos, T011; `Mapa` no repite la validación); exponer `cantidad_salas` y `sala_por_indice` (un `Vector` de V salas). Sin `dict` ni `set`.
- [ ] T014 Mostrar `DatosInvalidos` al arrancar en `crypta/main.py` (FR-010, FR-011): atraparla al cargar cripta y catálogo, imprimir el mensaje y terminar sin iniciar la partida ni crear la vista.
- [ ] T015 Punto de control (FR-001, FR-002, FR-008, FR-010): `python -m unittest` en verde (T006–T008 ya pasan y `TestCompatibilidadP1` sigue verde) y commit «001 base: costo de salidas, DatosInvalidos, índices y entradas».

**Punto de control**: las salidas tienen costo validado y el mapa tiene lo que necesitan las
búsquedas. Las fases 3 y 4 pueden empezar (la 4 en paralelo con la 3 si hay gente).

---

## Fase 3: Historia 1 — Terreno con costo (Prioridad 1) 🎯 MVP

**Objetivo**: todo movimiento, de cualquier actor, tarda según el costo de la salida; lo demás
queda como en P1.

**Prueba independiente**: con una cripta sintética con salidas de distintos costos y sin
cazadores, se mueve al jugador, errantes y rastreadores y se comprueba el instante de su siguiente
acción (la vista de HU1-9 se hace en la fase 7).

### Pruebas de la historia 1 (escribir primero; deben fallar)

> Todas en `tests/test_terreno.py`, clase `TestMovimientoConCosto` salvo que se indique otra; como
> comparten archivo, no son [P] entre sí. T025 sí es [P] (otro archivo).

- [ ] T016 [US1] Prueba HU1-1 en `tests/test_terreno.py` (FR-001, FR-003): jugador de velocidad 100 en el instante 0 se mueve por una salida de costo 250 → aparece en la sala destino y su siguiente acción queda en 250.
- [ ] T017 [US1] Prueba HU1-2 en `tests/test_terreno.py` (FR-001, FR-003): salida sin campo `costo`, actor de velocidad 100 → siguiente acción 100 unidades después. Puede pasar desde el inicio: protege comportamiento existente.
- [ ] T018 [US1] Prueba HU1-3 en `tests/test_terreno.py` (FR-002, FR-003): salida de costo 250 entre las salas 3 y 7; un actor va de 3 a 7 y otro de 7 a 3 → ambos cuestan 250.
- [ ] T019 [US1] Prueba HU1-4 en `tests/test_terreno.py` (FR-003, FR-004): velocidad 150 y costo 1 → intervalo `max(1, 1 * 100 // 150)` = 1.
- [ ] T020 [US1] Prueba HU1-5 en `tests/test_terreno.py` (FR-007): velocidad 100, salida de costo 300 en el instante 0 (programado en 300); en el instante 100 la velocidad pasa a 200 → reprogramado en 100 + max(1, (300 − 100) * 100 // 200) = 200 con número de secuencia nuevo.
- [ ] T021 [US1] Prueba HU1-6 en `tests/test_terreno.py` (FR-004, FR-006): errante y rastreador en salas con salidas de distintos costos; comparar con la misma cripta sin costos: mismo destino, mismo `random.Random.getstate()` después de decidir, y solo cambia el instante de la siguiente acción.
- [ ] T022 [US1] Prueba HU1-7 en `tests/test_terreno.py` (FR-005): en una sala con salidas de costo 400, atacar, esperar, usar, equipar, recoger, soltar y abrir una puerta conservan su costo de P1 §2.3.
- [ ] T023 [US1] Prueba HU1-10 en `tests/test_terreno.py` (FR-024): dos criptas sintéticas idénticas salvo costos, misma semilla y mismos comandos → los instantes difieren según los costos de cada una.
- [ ] T024 [US1] Prueba HU1-13 (movimiento) en `tests/test_terreno.py` (FR-001, FR-010): solo el lado de la sala 3 declara 250; un actor va de 7 a 3 → el movimiento cuesta 250.
- [ ] T025 [P] [US1] Prueba HU1-11 en `tests/test_persistencia.py` (FR-025): con una fuente falsa, una copia local del esqueleto de P1 con otra versión de cripta se invalida sin borrar archivos a mano; se descarga el esqueleto nuevo con sus costos y se persiste junto con su versión; ninguna solicitud extra (FR-027). Puede pasar desde el inicio: protege comportamiento existente.

### Implementación de la historia 1

- [ ] T026 [P] [US1] Devolver la salida elegida en `crypta/Modelo/Rastreador.py` (FR-004, FR-006): `sala_con_rastro_mas_fresco` (o la función equivalente) devuelve la puerta por la que se llega a la sala elegida, además de la sala; mismo orden de opciones y mismas llamadas al azar.
- [ ] T027 [US1] Usar el costo de la salida en el movimiento del jugador en `crypta/Modelo/Partida.py` (FR-003, FR-004): `mover` termina la acción con `puerta.costo` en lugar de `COSTO_MOVER`; eliminar la constante `COSTO_MOVER`.
- [ ] T028 [US1] Devolver la puerta en `_destino_errante` y `_aplicar_comportamiento` de `crypta/Modelo/Partida.py` (FR-004, FR-006): el errante y el rastreador devuelven la puerta elegida; `_tirar_dado` se llama igual que en P1 (depende de T026).
- [ ] T029 [US1] Programar el turno enemigo con el costo de la acción en `_turno_enemigo` de `crypta/Modelo/Partida.py` (FR-003, FR-004, FR-005): `COSTO_ATACAR` (100) si atacó y `COSTO_ESPERAR` (100) si esperó; `puerta.costo` si se movió; intervalo `max(1, costo * 100 // velocidad)`.
- [ ] T030 [US1] Revisar la invalidación por versión en `crypta/Controlador/GestorCripta.py` (FR-025, FR-027): si T025 falla, ajustar para que la copia local de otra versión se descarte y el esqueleto nuevo se guarde con su versión, sin solicitudes nuevas; si T025 ya pasa, dejar constancia en el commit de que no hizo falta cambio.
- [ ] T031 [US1] Punto de control (FR-001 a FR-008, FR-010, FR-024, FR-025): `python -m unittest` en verde, en especial `TestCompatibilidadP1` (FR-008), y commit «001 HU1: terreno con costo».

**Punto de control**: el terreno funciona y una cripta sin costos sigue idéntica a P1.

---

## Fase 4: Historia 2 — El cazador persigue por la ruta más barata (Prioridad 2)

**Objetivo**: el cazador ataca si comparte sala, espera si no tiene ruta o d > rango, y si no da un
paso hacia la vecina de menor id que inicia una ruta de costo mínimo.

**Prueba independiente**: criptas sintéticas pequeñas armadas para cada caso, con un cazador
activo y el jugador en salas conocidas; se comprueba la acción, la sala resultante y el instante de
la siguiente acción (la etiqueta de la vista, HU2-12, se hace en la fase 7).

### Pruebas de la historia 2 (escribir primero; deben fallar)

> Salvo que se indique otra, todas en `tests/test_cazador.py` y no son [P] entre sí. T032 y T047 son
> [P] (otros archivos).

- [ ] T032 [P] [US2] Escribir `tests/test_distancias_limitadas.py` (FR-014, FR-017, FR-036): en grafos pequeños, distancias iguales a un cálculo sin límite; corte por límite (solo se asientan nodos con dist ≤ límite); `extender_hasta` en dos pasos da lo mismo que de una vez; `reiniciar` no limpia vectores y los valores viejos no se leen (marca); salidas sin vuelta: se recorren entradas, no salidas; `RutaPorCazador` da el primer paso de menor id.
- [ ] T033 [US2] Prueba HU2-1 en `tests/test_cazador.py` (FR-013): cazador activo en la sala del jugador → ataca con costo 100 y no se mueve.
- [ ] T034 [US2] Prueba HU2-2 en `tests/test_cazador.py` (FR-014, FR-015): sin ruta de salidas abiertas hasta el jugador → espera con costo 100.
- [ ] T035 [US2] Prueba HU2-3 en `tests/test_cazador.py` (FR-015): rango 600, ruta más barata 700 → espera con costo 100.
- [ ] T036 [US2] Prueba HU2-4 en `tests/test_cazador.py` (FR-015, FR-016): rango 600, ruta más barata exactamente 600 → avanza un paso.
- [ ] T037 [US2] Prueba HU2-5 en `tests/test_cazador.py` (FR-014, FR-016): rango 1000, cazador en 1 y jugador en 2; salida 1–2 de costo 500 y ruta 1–3–4–2 de costo 100 cada salida → se mueve a 3 y la acción cuesta 100.
- [ ] T038 [US2] Prueba HU2-6 en `tests/test_cazador.py` (FR-017): rango 1000, vecinas 5 y 3 ambas al inicio de rutas de costo mínimo → se mueve a 3.
- [ ] T039 [US2] Prueba HU2-7 en `tests/test_cazador.py` (FR-017): cuadrícula con muchas rutas de igual costo que se cruzan; el primer paso es la vecina de menor id con costo(u, v) + dist(v, jugador) = d, comparado con `RutaPorCazador` en todas las salas de la cuadrícula.
- [ ] T040 [US2] Prueba HU2-8 en `tests/test_cazador.py` (FR-014, FR-018): salida 1–2 de costo 100 cerrada y ruta 1–3–2 de costo 400 abierta → se mueve a 3; la puerta sigue cerrada después.
- [ ] T041 [US2] Prueba HU2-9 en `tests/test_cazador.py` (FR-018, FR-027): la ruta pasa por salas sin contenido descargado → misma decisión que con todo descargado y la fuente que cuenta solicitudes no registra ninguna nueva.
- [ ] T042 [US2] Prueba HU2-10 en `tests/test_cazador.py` (FR-012): cazador dormido en una sala nunca visitada; el jugador entra → se activa con primera acción en reloj + intervalo con base 100; varios a la vez se activan en orden ascendente de id de instancia. Puede pasar desde el inicio: protege comportamiento existente.
- [ ] T043 [US2] Prueba HU2-11 en `tests/test_cazador.py` (FR-003, FR-016): velocidad 120, rango 1000, se mueve por una salida de costo 250 → siguiente acción `max(1, 250 * 100 // 120)` = 208 unidades después.
- [ ] T044 [US2] Prueba HU2-13 en `tests/test_cazador.py` (FR-011): misma cripta con el jugador a costo 700; con rango 600 en la ficha espera con costo 100, con rango 800 avanza un paso.
- [ ] T045 [US2] Prueba HU2-14 (antes de iniciar) en `tests/test_cazador.py` (FR-011): ficha de cazador sin `rango`, con −1, `600.0`, `true`, `"600"` o `null` → `DatosInvalidos` «La ficha <id> (cazador) tiene un rango inválido o ausente: <valor>» y no se inicia la partida.
- [ ] T046 [US2] Prueba HU2-15 en `tests/test_cazador.py` (FR-011, FR-013, FR-015): rango 0 sin compartir sala → espera con costo 100; compartiendo sala → ataca.
- [ ] T047 [P] [US2] Prueba HU2-14 (partida empezada) en `tests/test_controlador.py` (FR-011): la ficha inválida llega por la precarga a mitad de partida → la sesión termina de forma controlada con el mismo mensaje, no se trata como comando inválido y `partida.log` existe con los comandos ya jugados.

### Implementación de la historia 2

- [ ] T048 [P] [US2] Crear `crypta/estructuras/DistanciasLimitadas.py` (FR-014, FR-036; research D1, D5): Dijkstra perezoso y reanudable sobre índices densos, genérico (recibe V y una función que recorre las entradas abiertas de un nodo como pares (origen, costo)); campos `_dist`, `_marca`, `_asentada` (`Vector` de V enteros), `_frontera` (`MonticuloMin` de tuplas (dist, nodo)), `_calculo`, `_origen`, `_hasta` y contadores de búsquedas y nodos asentados; `reiniciar(origen)` O(1) sumando 1 a `_calculo`; `extender_hasta(limite, objetivo=None)` se detiene al asentar `objetivo` o cuando el mínimo de la frontera supera `limite`; `distancia(nodo)` y `esta_asentada(nodo)` O(1). Sin `heapq`, `dict` ni `set`.
- [ ] T049 [P] [US2] Crear `crypta/estructuras/RutaPorCazador.py` (FR-017, FR-031; research D2): Dijkstra desde la sala del cazador por salidas de ida con etiqueta (distancia, primer paso) en orden lexicográfico; al empatar en distancia conserva el menor id de primer paso; se detiene al asentar al jugador o al pasar el rango; mismos `Vector` con marca.
- [ ] T050 [P] [US2] Validar la ficha del cazador en `crypta/Controlador/RepositorioFichas.py` (FR-011, FR-024): al entrar una ficha (red o disco) con `comportamiento: "cazador"`, exigir «`rango` presente, entero (no `bool`) y ≥ 0»; si no, `DatosInvalidos` con el mensaje de `contracts/datos-servicio.md`.
- [ ] T051 [P] [US2] Tomar el rango de la ficha en `crypta/Modelo/Enemigo.py` (FR-011, FR-012, FR-024): aceptar `"cazador"` como comportamiento; `rango` (entero ≥ 0 o None, no es estado del juego) se lee de la ficha en `activar` y se valida otra vez por defensa; ningún rango escrito en el código.
- [ ] T052 [US2] Crear `Decision` y `Perseguidor.decidir` en `crypta/Modelo/Perseguidor.py` (FR-013 a FR-018, FR-021; research D3): `Decision(accion ∈ {atacar, esperar, mover}, puerta, costo)` con costo 100 para atacar y esperar y `puerta.costo` para mover; `decidir(cazador, sala_jugador)`: si el origen guardado difiere, reinicia; si u = P ataca; extiende mientras el mínimo ≤ rango y u no esté asentada; si u no quedó asentada espera; si no, entre las salidas abiertas de u con costo(u, v) + dist(v) = d elige la v de menor id (empate de dos salidas a la misma v: la primera en orden N, S, E, O). No usa el generador aleatorio. Por ahora invalida todo ante cualquier aviso de puerta (`puerta_cambio`); la invalidación selectiva es de la fase 5.
- [ ] T053 [US2] Agregar la rama del cazador en `crypta/Modelo/Partida.py` (FR-004, FR-013, FR-016, FR-019, FR-023): crear un `Perseguidor` por partida y registrarlo como observador de cada `EstadoPuerta`; en `_aplicar_comportamiento`, el cazador pide la `Decision`, ataca con el daño de P1 (que sí usa el azar), se mueve con `_mover_enemigo` o espera, y `_turno_enemigo` lo programa con `decision.costo`. Los movimientos usan los `Cambio` existentes (FR-020).
- [ ] T054 [US2] Terminar la sesión ante `DatosInvalidos` en `crypta/Controlador/Controlador.py` y `crypta/main.py` (FR-011): a mitad de partida, `DatosInvalidos` sale de `GestorContenido` (`procesar_pendientes` o `garantizar_sala`, en el hilo principal); el `Controlador` la atrapa alrededor de todo el procesamiento del comando, no solo en los `except ValueError`, muestra el mensaje y termina la sesión de forma controlada. `DatosInvalidos` no hereda de `RuntimeError`, para que el `except RuntimeError` de la precarga no la trague. En `crypta/main.py`, `--replay` también la atrapa, muestra el mensaje y termina. `partida.log` ya queda escrito porque `RegistroPartida.anotar` cierra el archivo en cada comando.
- [ ] T055 [US2] Punto de control (FR-003, FR-011 a FR-018, FR-021, FR-027): `python -m unittest` en verde, con `TestCompatibilidadP1` todavía verde, y commit «001 HU2: cazador».

**Punto de control**: historias 1 y 2 completas salvo la vista. Es lo que más pesa en la entrega.

---

## Fase 5: Historia 3 — La decisión del cazador siempre es correcta (Prioridad 3)

**Objetivo**: reutilizar la búsqueda sin cambiar nunca la decisión; pergamino, replay y guardado
con cazadores.

**Prueba independiente**: partida sintética con muchos cambios de puertas, movimientos y cambios de
velocidad; en cada turno de cada cazador la decisión coincide con un cálculo desde cero.

### Pruebas de la historia 3 (escribir primero; deben fallar)

> Todas en `tests/test_equivalencia_cazador.py` salvo T064, que es [P] (otro archivo).

- [ ] T056 [US3] Preparar el verificador en `tests/test_equivalencia_cazador.py` (FR-019, SC-002): envolver el `Perseguidor` de la partida para que, en cada turno de cazador, compare su `Decision` con `decidir_desde_cero` (otra `DistanciasLimitadas`, siempre reiniciada) y con `RutaPorCazador`, y falle con el instante, el cazador y ambas decisiones si difieren.
- [ ] T057 [US3] Prueba HU3-1 en `tests/test_equivalencia_cazador.py` (FR-019): rango 1000, la ruta más barata cruza una puerta que se cierra entre dos turnos (por cierre automático y por otro evento) → toma la siguiente ruta o espera, igual que el verificador.
- [ ] T058 [US3] Prueba HU3-2 en `tests/test_equivalencia_cazador.py` (FR-019): cazador que esperaba sin ruta; se abre una puerta que crea una ruta ≤ 1000 → en su siguiente turno avanza por ella.
- [ ] T059 [US3] Prueba HU3-3 en `tests/test_equivalencia_cazador.py` (FR-014, FR-019): el jugador se mueve entre dos turnos del cazador a una sala a costo ≤ 1000 → decide hacia la nueva sala, igual que el verificador.
- [ ] T060 [US3] Prueba HU3-4 en `tests/test_equivalencia_cazador.py` (FR-019, FR-023): varios cazadores con turno en el mismo instante; actúan en orden de la agenda (tiempo, secuencia) y cada uno decide con el estado vigente en su turno.
- [ ] T061 [US3] Prueba HU3-5 y SC-002 en `tests/test_equivalencia_cazador.py` (FR-019): otros actores mueren, cambian de sala y de velocidad entre turnos; y una partida sintética determinista de ≥ 1 000 turnos de cazador con puertas que cambian seguido → 100 % de coincidencia con el verificador.
- [ ] T062 [US3] Prueba HU3-6 en `tests/test_equivalencia_cazador.py` (FR-019, FR-020): pergamino de retroceso después de que un cazador se movió → vuelve a su sala, vida y próxima acción anteriores, y sus decisiones siguientes coinciden con el verificador.
- [ ] T063 [US3] Prueba HU3-7 en `tests/test_equivalencia_cazador.py` (FR-021): partida con cazadores reproducida con `--replay` (misma semilla y comandos) → mismas decisiones en los mismos instantes; y decidir no cambia `random.Random.getstate()`.
- [ ] T064 [P] [US3] Prueba HU3-8 en `tests/test_persistencia.py` (FR-026): guardar y cargar una partida con cazadores conserva costos de salidas, sala, vida, rango (desde la ficha) y próxima acción, y la partida sigue igual que sin guardar; un archivo de formato 1 se rechaza con «La partida se guardó con la versión 1 del formato y este programa lee la versión 2: no se puede cargar»; un archivo con una ficha de cazador de rango inválido, o con dos lados de una puerta con costos distintos, se rechaza con `ErrorGuardado` (no con `DatosInvalidos`).

### Implementación de la historia 3

- [ ] T065 [US3] Agregar `decidir_desde_cero` y los modos de reutilización a `crypta/Modelo/Perseguidor.py` (FR-019, FR-032, FR-033; research D4): modos «recalcular siempre», «invalidación total» y «selectiva» (por defecto); en modo selectivo `puerta_cambio(estado)` invalida solo si algún extremo está asentado en el cálculo vigente (O(1)); `invalidar()` público; `decidir_desde_cero` usa su propia `DistanciasLimitadas`.
- [ ] T066 [US3] Invalidar al usar el pergamino en `crypta/Modelo/Partida.py` (FR-020): `usar_pergamino` llama a `perseguidor.invalidar()` después de revertir; las búsquedas no entran al historial (research D6).
- [ ] T067 [P] [US3] Escribir y leer el costo de cada puerta en `crypta/Adaptadores/EstadoPartida.py` (FR-026): en `escribir_sala`, después de `cierre_automatico`, `entero("costo", puerta.costo)`; `leer_sala` lo lee y lo pasa a `Puerta`. Al cargar una partida, atrapar `DatosInvalidos` (la de `Enemigo.activar` y también la de `compartir_estado_con` dentro de `leer_sala`) y convertirla en `ErrorGuardado`. El rango no se escribe.
- [ ] T068 [P] [US3] Subir `FORMATO_GUARDADO` de 1 a 2 en `crypta/Adaptadores/GuardadoBinario.py` (FR-026).
- [ ] T069 [P] [US3] Subir `FORMATO_JSON` una versión en `crypta/Adaptadores/GuardadoJSON.py` (FR-026).
- [ ] T070 [US3] Crear un `Perseguidor` nuevo al cargar una partida en `crypta/Modelo/Partida.py` (FR-019, FR-026): la partida cargada crea su perseguidor y lo registra en las puertas leídas. El rango ya se relee en `Enemigo.activar`, que la carga llama.
- [ ] T071 [US3] Punto de control (FR-019 a FR-021, FR-023, FR-026): `python -m unittest` en verde y commit «001 HU3: equivalencia, pergamino y guardado».

**Punto de control**: el cazador es correcto con reutilización, y guardar, cargar y repetir funcionan.

---

## Fase 6: Historia 4 — Medición con `--bench` (Prioridad 4)

**Objetivo**: las secciones B1–B9 de `contracts/bench.md`, deterministas, sin vista ni red.

**Prueba independiente**: ejecutar `--bench` dos veces con la misma semilla; mismas criptas, todas
las secciones presentes y sin vista.

### Pruebas de la historia 4 (escribir primero; deben fallar)

> Todas en `tests/test_bench.py`; corren las secciones en modo rápido.

- [ ] T072 [US4] Prueba HU4-1 en `tests/test_bench.py` (FR-028, SC-006): dos generaciones con la misma semilla → misma huella (salas, salidas, costos, puertas y ubicación de cazadores serializados en orden).
- [ ] T073 [US4] Pruebas HU4-2 y HU4-3 en `tests/test_bench.py` (FR-029, FR-030): B1 reporta 1 y 50 cazadores (ninguno en la sala del jugador, todos dentro de su rango); B2 y B3 reportan rango pequeño y grande, y 2 000 y 20 000 salas.
- [ ] T074 [US4] Pruebas HU4-4 y HU4-5 en `tests/test_bench.py` (FR-031, FR-032): B4 reporta compartido frente a por cazador con 1, 10 y 50; B5 reporta las tres variantes en puertas casi estables e inestables con tiempo, búsquedas y salas asentadas.
- [ ] T075 [US4] Prueba HU4-6 en `tests/test_bench.py` (FR-033): B6 reporta 0 diferencias; con una variante saboteada a propósito imprime ERROR y devuelve código distinto de 0.
- [ ] T076 [US4] Prueba HU4-7 en `tests/test_bench.py` (FR-034): las secciones nuevas corren con una fuente que falla si se la llama y una vista que falla si se instancia.
- [ ] T077 [US4] Pruebas HU4-8, HU4-9 y HU4-10 en `tests/test_bench.py` (FR-035, FR-036, FR-037): B7, B3 y B8 calculan y reportan p95, cociente 20 000 / 2 000 y cociente por cazador 100 / 10, con su «¿cumple?» (la prueba no exige el límite; eso lo comprueba `--bench` completo).

### Implementación de la historia 4

- [ ] T078 [US4] Crear el generador en `crypta/bench/bench_cazador.py` (FR-028, FR-030): cuadrícula `ancho × alto` con salidas a las 4 vecinas (algunas quitadas); costo en [1, 500] y puerta derivados de (semilla, coordenadas) con su propio `random.Random`, para que la región alrededor del jugador sea idéntica en criptas de distinto tamaño; cazadores a distancias repartidas dentro del rango (ninguno en la sala del jugador), tomados del orden en que `DistanciasLimitadas` asienta las salas, sin `sorted()`; rango pequeño = distancia de la sala número 100; función `huella`.
- [ ] T079 [US4] Agregar B1 y B2 a `crypta/bench/bench_cazador.py` (FR-029, FR-030): 2 000 salas; 1 frente a 50 cazadores; rango pequeño frente a grande, con tiempo medio por decisión y salas asentadas.
- [ ] T080 [US4] Agregar B3 a `crypta/bench/bench_cazador.py` (FR-030, FR-036, SC-005): rango ≈ 100 salas en 2 000 y 20 000 salas; tiempo medio por decisión, cociente y «¿cumple?» (cociente < 2).
- [ ] T081 [US4] Agregar B4 a `crypta/bench/bench_cazador.py` (FR-031): compartido (`Perseguidor`) frente a por cazador (`RutaPorCazador`) con 1, 10 y 50 cazadores, puertas estables e inestables; reportar cuál gana en cada condición.
- [ ] T082 [US4] Agregar B5 y B6 a `crypta/bench/bench_cazador.py` (FR-032, FR-033): las tres variantes de reutilización con ≈ 1 cambio de puerta cada 50 acciones y ≥ 1 por acción; cada decisión de B4 y B5 comparada con `decidir_desde_cero`; cualquier diferencia se imprime como ERROR y el proceso sale con código distinto de 0.
- [ ] T083 [US4] Agregar B7 a `crypta/bench/bench_ciclo.py` (FR-035, SC-004): depende del generador de T078; 2 000 salas, 50 cazadores repartidos dentro de su rango, `ACCIONES = 60` con calentamiento; el jugador sigue un recorrido fijo derivado de la semilla, sin ataques ni esperas; media, p95, máximo y «¿cumple?» (p95 < 20 ms). Si existe una copia local de la cripta oficial, B7 también corre sobre ella.
- [ ] T084 [US4] Agregar B8 y B9 a `crypta/bench/bench_cazador.py` (FR-037, SC-008; research D5): ciclo con 10, 25, 50 y 100 cazadores, tiempo por cazador y cociente 100 / 10 con «¿cumple?» (≤ 2); vectores con marca frente a `ArbolBusqueda` en la misma búsqueda.
- [ ] T085 [US4] Registrar las secciones nuevas en `crypta/bench/bench.py` (FR-028 a FR-034): agregarlas a `ejecutar` con modo rápido, propagar el código de salida de B6 y no instanciar la vista ni la red.
- [ ] T086 [US4] Ejecutar `python -m crypta.main --bench` dos veces con la misma semilla y guardar la salida en `docs/resultados_bench_p2.txt` (FR-028, FR-035 a FR-037); `docs/resultados_bench.txt` no se toca, porque lo cita la primera parte de `DECISIONES.md`. Comprobar huellas iguales, B3 < 2, B6 con 0 diferencias, B7 p95 < 20 ms y B8 ≤ 2, y anotar si la cripta oficial ya se publicó. Si algún límite no se cumple, anotarlo y avisar al grupo antes de seguir.
- [ ] T087 [US4] Punto de control (FR-028 a FR-037): `python -m unittest` en verde y commit «001 HU4: secciones de --bench y resultados».

**Punto de control**: hay evidencia medida para defender las decisiones de research.md.

---

## Fase 7: Cierre (vista, documentación y revisión)

**Propósito**: lo que ve el jugador, la documentación exigida (principio X) y las revisiones de la
constitución.

### Pruebas de la vista (escribir primero; deben fallar)

- [ ] T088 Prueba HU1-9 en `tests/test_controlador.py` (FR-009): jugador en una sala con salidas abiertas y cerradas → la vista muestra el costo de cada salida de la sala actual (se comprueba que aparezca la información, no la línea completa).
- [ ] T089 Prueba HU2-12 en `tests/test_controlador.py` (FR-022): sala con un cazador y otros enemigos → `[cazador]` aparece solo en el cazador.

### Implementación y documentación

- [ ] T090 Mostrar costos y la etiqueta del cazador en `crypta/Vista/VistaConsola.py` (FR-009, FR-022, SC-007): `mostrar_estado` agrega «costo N» a cada salida, abierta o cerrada, y `[cazador]` a los cazadores, como en `contracts/vista.md`; `mostrar_ayuda` explica la etiqueta y que el número de cada salida es su costo.
- [ ] T091 [P] Escribir la sección §5.1 «La ruta más barata del cazador» en `DECISIONES.md` (FR-014 a FR-018, FR-029 a FR-031, FR-036, FR-037): con los seis apartados (problema, alternativas, decisión, complejidad, evidencia y límites), a partir de research D1, D2, D3 y D5, con la complejidad de las operaciones más frecuentes del plan, las alternativas descartadas y los números de B1–B4, B8 y B9 de `docs/resultados_bench_p2.txt`; enlazar a `specs/001-terreno-cazador/spec.md` y `plan.md`, decir si la decisión final coincide con plan.md y, si no, qué medición motivó el cambio; quitar «provisional» solo donde la medición lo respalde.
- [ ] T092 Escribir la sección §5.2 «Rutas que dejan de ser válidas» en `DECISIONES.md` (FR-019, FR-020, FR-032, FR-033): con los seis apartados (problema, alternativas, decisión, complejidad, evidencia y límites), a partir de research D4 y D6 (tabla de eventos que invalidan, demostración de «ambos extremos sin asentar», que las búsquedas no son estado del juego) y los números de B5, B6 y B7 de `docs/resultados_bench_p2.txt`; enlazar a `specs/001-terreno-cazador/spec.md` y `plan.md`, y decir si la decisión final coincide con plan.md y, si no, qué medición motivó el cambio; si la selectiva no ahorra frente a la total, decir que se adoptó la total. Depende de T091 (mismo archivo).
- [ ] T098 Escribir la sección §5.6 «Revisión de decisiones de la primera parte» en `DECISIONES.md` (FR-035, FR-037; constitución XI; P2 §5.6): correr las mediciones de agenda e historial de la primera parte (`crypta/bench/bench_agenda.py` y la tabla HISTORIAL de `crypta/bench/bench_inventario.py`) con la carga de B7 (cazadores y costos) y escribir el antes y el después con los números de `docs/resultados_bench.txt` y `docs/resultados_bench_p2.txt`. Queda marcada como **parcial** hasta la capacidad de la línea de tiempo. Depende de T083 y de T092 (mismo archivo).
- [ ] T093 [P] Actualizar `README.md` (FR-009, FR-022, FR-026, FR-034; constitución X): versión de spec-kit (v1.3.1) y agente utilizado (Claude Code); costo de las salidas y cazadores en la vista, formato de guardado 2 (los archivos de formato 1 no se cargan), nuevas secciones de `--bench` y cómo correr las pruebas de la capacidad.
- [ ] T094 [P] Completar `PROMPTS_LLM.md` (principio X; FR-001 a FR-037): registrar los prompts usados en `/speckit-tasks` y en la implementación de esta capacidad.
- [ ] T095 Revisar imports prohibidos y constantes quemadas en `crypta/` (FR-024; principio I): `git grep -n -E "import (heapq|bisect|collections|networkx)|from (heapq|bisect|collections|networkx)" -- crypta` sin resultados; revisar a mano que `DistanciasLimitadas.py`, `RutaPorCazador.py` y `Perseguidor.py` no usen `dict`, `set`, `sorted` ni `list.sort`; `git grep` de números de costo o rango en `crypta/Modelo` y `crypta/Controlador`: solo queda `COSTO_POR_OMISION = 100` en `crypta/Modelo/Puerta.py`. Corregir lo que aparezca en el archivo donde aparezca.
- [ ] T096 Validar de punta a punta según `specs/001-terreno-cazador/quickstart.md` (FR-008, FR-009, FR-022, FR-026; SC-001 a SC-008): pasos 1 a 6, incluida la prueba manual en el juego, y marcar en `specs/001-terreno-cazador/checklists/requirements.md` lo comprobado.
- [ ] T097 Punto de control final (FR-001 a FR-037): `python -m unittest` en verde y commit «001 cierre: vista, DECISIONES §5.1 y §5.2, README»; listo para entregar el 18 de noviembre.

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1 (preparación)**: sin dependencias. **T001 y T002 antes de cualquier cambio de código.**
- **Fase 2 (base común)**: depende de la fase 1. Bloquea todas las historias.
- **Fase 3 (HU1)**: depende de la fase 2.
- **Fase 4 (HU2)**: depende de la fase 2. Usa el costo de la acción de HU1 (T029) para programar al
  cazador: las pruebas y las estructuras (T032–T051) pueden avanzar en paralelo con la fase 3, pero
  T053 espera a T029.
- **Fase 5 (HU3)**: depende de la fase 4.
- **Fase 6 (HU4)**: depende de la fase 5 (B5 y B6 usan los modos de T065). El generador (T078) puede
  empezarse en cuanto termine T048.
- **Fase 7 (cierre)**: la vista (T088–T090) solo depende de las fases 3 y 4 y se puede adelantar;
  T091 y T092 dependen de T086 (resultados del bench); T098 depende de T083 y T092; T097 depende de todo, incluida T098.

### Dentro de cada historia

- Pruebas primero, y deben fallar; después la implementación; al final el punto de control.
- Estructuras (`crypta/estructuras`) antes que el modelo (`Perseguidor`), y el modelo antes que
  `Partida` y el `Controlador`.
- Las tareas que tocan el mismo archivo van en el orden de sus ID.

### Archivos con varias tareas (no se reparten a la vez)

| Archivo | Tareas |
|---|---|
| `tests/test_terreno.py` | T004, T006, T007, T016–T024 |
| `tests/test_cazador.py` | T033–T046 |
| `tests/test_equivalencia_cazador.py` | T056–T063 |
| `tests/test_controlador.py` | T008, T047, T088, T089 |
| `tests/test_persistencia.py` | T025, T064 |
| `tests/test_bench.py` | T072–T077 |
| `crypta/Modelo/Puerta.py` | T011, T012 |
| `crypta/Modelo/Partida.py` | T027, T028, T029, T053, T066, T070 |
| `crypta/Modelo/Perseguidor.py` | T052, T065 |
| `crypta/bench/bench_cazador.py` | T078–T082, T084 |
| `DECISIONES.md` | T091, T092, T098 |

---

## Ejemplos de trabajo en paralelo

### Fase 2

```text
Integrante A: T006 → T010 (Sala.py)          # pruebas de costo y lectura del costo
Integrante B: T009 → T011 → T012 (Puerta.py) # excepción, costo y observador
Integrante C: T008 → T014 (main.py)          # arranque con datos inválidos
Luego: T007 → T013 (Mapa.py), que necesita Sala y Puerta.
```

### Historia 1

```text
Integrante A: T016–T024 (tests/test_terreno.py)
Integrante B: T025 → T030 (persistencia y GestorCripta)
Integrante C: T026 (Rastreador.py)
Luego, en orden: T027 → T028 → T029 (Partida.py)
```

### Historia 2 (puede empezar junto con la historia 1)

```text
Integrante A: T032 → T048 (DistanciasLimitadas) → T049 (RutaPorCazador)
Integrante B: T033–T046 (tests/test_cazador.py)
Integrante C: T047 → T050 → T051 → T054 (Controlador, repositorio, Enemigo)
Luego: T052 (Perseguidor) → T053 (Partida, después de T029)
```

### Historias 3 y 4

```text
Integrante A: T056–T063 → T065 → T066 → T070
Integrante B: T064 → T067, T068, T069 (guardado)
Integrante C: T078 → T072–T077 → T079… (bench, en cuanto exista T048)
```

---

## Estrategia de implementación

### MVP primero

1. Fases 1 y 2.
2. Fase 3 (HU1): el terreno ya cambia el juego y P1 sigue idéntica. **Validar** con
   `python -m unittest` y `TestCompatibilidadP1`.
3. Fase 4 (HU2): con esto está lo que más pesa en la evaluación.

### Entrega incremental

Cada fase termina en un commit con todo en verde. Si el tiempo no alcanza, lo que queda fuera es
de las últimas fases; nunca se deja una fase a medias sin su punto de control.

### Calendario sugerido (la 001 termina el viernes 13 de noviembre)

Faltan las capacidades 002, 003 y 004, así que toda la 001 queda terminada el viernes 13.

| Día | Fases |
|---|---|
| Mié 11 | Fase 1 (T001 primero) y fase 2 |
| Jue 12 | Fase 3 (HU1) y fase 4 (HU2) |
| Vie 13 | Fase 5 (HU3), fase 6 (HU4) y fase 7 (cierre) |

---

## Notas

- [P] = otro archivo y sin dependencias pendientes.
- Cada prueba cita su FR en el nombre del método o en el docstring (principio IX); los escenarios
  se nombran HUx-n en el docstring.
- Comprobar que la prueba falla antes de implementar, salvo `TestCompatibilidadP1`.
- Nunca usar `cache/` en las pruebas: solo `tests/datos/` copiado a una carpeta temporal.
- Si una tarea encuentra un caso que la spec no cubre, se para y se corrige primero la spec
  (principio VIII).
