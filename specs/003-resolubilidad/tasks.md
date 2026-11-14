---

description: "Lista de tareas de la capacidad 003 — Verificación de resolubilidad"
---

# Tareas: Verificación de resolubilidad

**Entrada**: documentos de diseño en `specs/003-resolubilidad/`

**Requisitos previos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: obligatorias (constitución, principio IX; SC-301). Cada escenario de aceptación tiene
una tarea de prueba que cita su FR en el nombre del método o en el docstring. Las pruebas de una
historia se escriben **antes** de implementarla y deben **fallar** al escribirse.

**Organización**: por fases y, dentro de ellas, por historia de usuario. Cada tarea cita los FR que
atiende y nombra el archivo que toca.

**Entrega**: miércoles 18 de noviembre de 2026; ver «Calendario sugerido» al final.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo con las demás [P] de su bloque: toca otro archivo y no depende
  de una tarea sin terminar.
- **[HUx]**: historia de usuario de spec.md (HU1 resoluble y orden, HU2 reporte, HU3 inicio de
  partida, HU4 `--verificar`, HU5 `--bench`).
- «HUx-n» es el escenario de aceptación n de la historia x.
- Rutas relativas a la raíz del repositorio. «Dx» es la decisión x de research.md.
- Notación: V salas, E salidas, L entradas de ubicación, K llaves distintas.

---

## Fase 1: Preparación

**Propósito**: que la spec ajustada esté en Git antes del código y que las pruebas tengan con qué
armar criptas con llaves.

**⚠️ T001 se hace antes de cualquier commit de código de la 003.**

- [X] T001 Confirmar en Git el ajuste de FR-311 de `specs/003-resolubilidad/spec.md` («dentro de la misma sala, primero la ubicación sin enemigo y después las que tienen enemigo, por id de enemigo») en un commit propio, y después los artefactos del plan (`plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`) en otro (principio VIII; FR-311).
- [X] T002 Extender `tests/ayudas_cripta.py` (habilita FR-301 a FR-329): `ubicacion(id_llave, sala, enemigo=None)` que devuelve el dict de una entrada; `respuesta_llaves(*ubicaciones)` → `{"llaves": [...]}`; `datos_generales(...)` acepta `llave_salida=None` (hoy fija `None`); `FuenteQueFalla.obtener_llaves` falla como las demás. Lo que necesita `LlavesNoDisponibles` y el verificador va en T009. No cambia nada de lo que ya hacen las ayudas.

**Punto de control**: `python -m unittest` en verde (las ayudas nuevas aún no se usan).

---

## Fase 2: Base común (numeración, entrada validada, resultado)

**Propósito**: lo que usan todas las historias: pasar ids de llave a números, leer y validar la
ubicación de las llaves y las clases del resultado.

**⚠️ CRÍTICO**: ninguna historia empieza antes de terminar esta fase.

### Pruebas de la base (escribir primero; deben fallar)

- [X] T003 [P] Escribir `tests/test_numeracion_llaves.py` (D1; habilita FR-308, FR-320): con ids repetidos y desordenados, `NumeracionLlaves` da `len` = ids distintos; `numero(a) < numero(b)` ⇔ `a < b` como texto (incluye mayúsculas, dígitos y prefijos: `itm_llave_10` < `itm_llave_9`); `id_de(numero(x)) == x`; `numero` de un id ausente → None; con 1 000 ids que llegan ordenados la altura del árbol interno es ≤ ⌈log₂(1 001)⌉; `NumeracionPorInsercion` con ids ordenados da altura 1 000 (el límite de P1 §4.4) y la misma función `id_de(numero(x)) == x`.
- [X] T004 [P] Escribir `TestUbicacionLlaves` en `tests/test_resolubilidad.py` (FR-319; carga de HU3-7): respuesta válida → `Vector` de `UbicacionLlave` con `id_llave`, `id_sala`, `indice_sala` y `enemigo`; entradas repetidas y lista vacía son válidas; campos extra se ignoran; `DatosInvalidos` con «entrada <n>», el id si lo tiene y el problema para: raíz sin `llaves` o que no es lista, entrada que no es objeto, sin `id`, `id` vacío o no texto, sin `sala`, `sala` `true`, `2.5`, `"4"`, sala que no existe en el esqueleto, `enemigo` que no es texto ni null. Los mensajes siguen `contracts/reporte.md` («La cripta no se puede jugar: la ubicación de llaves tiene un dato inválido: entrada <n> (<id>): <problema>» al mostrarse).

### Implementación de la base

- [X] T005 [P] Crear `crypta/estructuras/NumeracionLlaves.py` (D1; FR-308, FR-320): `NumeracionLlaves(vector_ids)` copia los ids a un `Vector`, los ordena con `ordenar`, quita repetidos contiguos, arma `_ids` (número → id) y `_arbol = ArbolBusqueda.desde_ordenados` de pares `(id, número)`; métodos `numero(id)` O(log K) (None si no está), `id_de(n)` O(1), `__len__`. En el mismo archivo, `NumeracionPorInsercion(vector_ids)` (solo para el bench R5): `ArbolBusqueda.insertar` en orden de llegada, número = orden de llegada, misma interfaz más `altura()`. Sin `dict`, `set`, `sorted` ni `list.sort`.
- [X] T006 [P] Crear `crypta/Modelo/ResultadoVerificacion.py` (data-model.md; FR-306, FR-309 a FR-318, FR-324): clases `ResultadoVerificacion(resoluble, rondas, reporte)`, `Reporte` (`falta_sala_salida`, `falta_llave_salida`, `no_obtenibles`, `frontera`, `ubicaciones_frontera`, `dependencias`, `ciclos`, `salida_sin_puerta`), `PuertaFrontera(id_origen, direccion, id_destino, llave)`, `Dependencia(llave, depende_de, motivo)` con los motivos exactos «no está en la cripta» y «su sala no se alcanza ni abriendo todas las puertas», y `NoVerificable(motivo)`. Todos los conjuntos son `Vector`. Sin lógica.
- [X] T007 Crear `crypta/Modelo/UbicacionLlaves.py` (D2, D7; FR-319): clase `UbicacionLlave(id_llave, id_sala, indice_sala, enemigo)` con `numero_llave = None`; función `leer_ubicaciones(respuesta_json, mapa)` que valida toda la respuesta según `contracts/datos-servicio.md` («`sala` entero JSON (no `bool`, no `float`, no texto) de una sala del esqueleto»; «`enemigo` ausente, null o texto») con `mapa.obtener_sala` (O(log V)), y devuelve un `Vector`. Lanza `DatosInvalidos` (de `crypta/Modelo/DatosInvalidos.py`) en la primera entrada inválida. Hace pasar T004.
- [X] T008 [P] Agregar `LlavesNoDisponibles(RuntimeError)` y el método no abstracto `obtener_llaves(self, cripta_id)` que la lanza por omisión en `crypta/Adaptadores/FuenteDatos.py` (D9; FR-324). Las fuentes falsas existentes siguen funcionando sin cambios.
- [X] T009 Completar `tests/ayudas_cripta.py` (habilita T011–T014 y la fase 5; FR-301, FR-324): `verificar_cripta(esqueleto, generales, llaves)` que, con imports dentro de la función (como `controlador_sintetico`, para no romper las pruebas mientras no existe el verificador), arma el `Mapa` con `mapa_de`, lee la ubicación con `leer_ubicaciones` y llama a `verificar` de `crypta/Modelo/Verificador.py`; y `FuenteContadora` acepta `llaves=None` y define `obtener_llaves(cripta_id)` que cuenta la operación `"obtener_llaves"` y devuelve la respuesta, o lanza `LlavesNoDisponibles` (T008) si es None. Las pruebas T011–T014 se escriben contra esta firma y fallan hasta T015.
- [X] T010 Punto de control (D1, D7; FR-319): `python -m unittest` en verde (T003, T004 pasan; todo lo de P1 y la 001 sigue verde) y commit «003 base: numeración de llaves, ubicación validada, resultado».

**Punto de control**: hay números de llave ordenados por id y ubicaciones validadas. Las fases 3 y 5
pueden empezar (la 5 solo en sus adaptadores, T029 y T033–T036, hasta que exista el verificador).

---

## Fase 3: Historia 1 — Saber si se puede ganar y en qué orden (Prioridad 1) 🎯 MVP

**Objetivo**: el recorrido por oleadas con puertas estacionadas da resoluble o no y el orden por
rondas (D3).

**Prueba independiente**: criptas sintéticas pequeñas armadas con `tests/ayudas_cripta.py`, sin
red; se compara el resultado y el texto del orden.

### Pruebas de la historia 1 (escribir primero; deben fallar)

- [X] T011 [HU1] Escribir `TestResolubleYOrden` en `tests/test_resolubilidad.py`, escenarios HU1-1 a HU1-5 (FR-301, FR-303, FR-304, FR-305, FR-306, FR-308): HU1-1 resoluble con rondas `[a, c]`, `[b, salida]` y el texto exacto de `contracts/reporte.md` («Ronda 1: itm_llave_a, itm_llave_c»); HU1-2 dos ejecuciones y la ubicación barajada dan el mismo texto; HU1-3 llave con `enemigo` en la sala 5 obtenible en esa sala (solo la ubicación por enemigo; FR-321 se prueba en T031); HU1-4 cerrada sin llave se cruza; HU1-5 la misma cripta con `cierre_automatico`, trampas en el contenido y costos distintos da el mismo resultado.
- [X] T012 [HU1] Escribir `TestResolubleCasosBorde` en `tests/test_resolubilidad.py`, escenarios HU1-6 a HU1-9 y casos borde (FR-303, FR-304, FR-305, FR-306, FR-308): HU1-6 salida sin vuelta 2→1 deja `salida` no obtenible; HU1-7 llave con dos ubicaciones, una alcanzable; HU1-8 llave que ninguna puerta pide aparece en el orden; HU1-9 `sala_salida` alcanzable solo por salida abierta → no resoluble; `sala_inicial = sala_salida` necesita una puerta que pida `llave_salida`; puerta hacia `sala_salida` que pide otra llave obtenible no cuenta; una llave obtenida en la ronda r no abre puertas dentro de la misma ronda (cripta donde liberarla antes cambiaría las rondas).
- [X] T013 [P] [HU1] Escribir `TestOrdenSeguible` en `tests/test_equivalencia_resolubilidad.py` (FR-307, SC-302): para ≥ 200 criptas generadas por semilla con un generador pequeño propio de la prueba (zonas y llaves encadenadas, salidas sin vuelta, llaves en varias ubicaciones), el orden del verificador se sigue paso a paso: con las llaves de las rondas anteriores, cada llave de la ronda tiene una ubicación alcanzable (comprobado con un recorrido simple escrito en la prueba), y las rondas coinciden con las de `VerificadorIngenuo`.
- [X] T014 [HU1] Escribir `TestVisitasUnaVez` en `tests/test_resolubilidad.py` (FR-313, FR-335): un contador inyectado en el verificador (parámetro opcional de prueba) muestra que, en una cripta **resoluble** de llaves encadenadas, cada sala se desencola a lo sumo una vez y cada salida se examina a lo sumo dos veces (al procesar su origen y al liberarse); y en una cripta **no resoluble** con varias capas, cada sala se marca a lo sumo una vez (región o capa) y cada salida se examina a lo sumo tres veces (origen, liberación y capa). La parte no resoluble falla hasta T024.

### Implementación de la historia 1

- [X] T015 [HU1] Crear `crypta/Modelo/Verificador.py` con el recorrido por oleadas (D3; FR-301, FR-303 a FR-308): `verificar(mapa, datos_cripta, ubicaciones)`: (1) junta en un `Vector` los ids de las ubicaciones, de las puertas cerradas con `llave` y `llave_salida`, y arma `NumeracionLlaves`; (2) llena `numero_llave` de cada ubicación y `llaves_en_sala` (`Vector` de V con None o `Vector` de números); (3) recorre por rondas con `ronda_sala` (V, −1), `ronda_llave` (K, −1), `abre` (K, False), `estacionadas` (K, None o `Vector` de `(índice origen, índice dirección, índice destino)`), una `Cola` y `nuevas`; las salidas de cada sala en N, S, E, O con `obtener_puerta`; una salida cerrada con llave sin `abre` se estaciona; al vaciarse la cola se ordena `nuevas` con `ordenar`, se agrega la ronda, se activa `abre` y se liberan sus estacionadas como semillas de la ronda siguiente; (4) decide resoluble con `Sala.entradas` de `sala_salida` (FR-305). Devuelve `ResultadoVerificacion` con `rondas` como `Vector` de `Vector` de ids. Salidas con `sala_destino_ref` None se ignoran. No modifica el `Mapa` ni las puertas. Si no es resoluble, por ahora `reporte` con solo `no_obtenibles` (lo completa la fase 4).
- [X] T016 [P] [HU1] Crear `crypta/Vista/FormatoVerificacion.py` con `texto_resultado(resultado)` para el caso resoluble (D10; FR-306): exactamente «Verificación de resolubilidad: la cripta es resoluble.», «Orden de llaves:» y una línea «  Ronda <n>: <id>, <id>» por ronda, según `contracts/reporte.md`. Función pura, sin E/S; ASCII más acentos, flecha `->`.
- [X] T017 [P] [HU1] Crear `crypta/Modelo/VerificadorIngenuo.py` con el orden ingenuo (D8; FR-331): `verificar_ingenuo(mapa, datos_cripta, ubicaciones)` repite un recorrido completo desde `sala_inicial` con las llaves de las rondas anteriores (marcas nuevas en cada repetición), las llaves nuevas forman la ronda siguiente, y para cuando no aparece ninguna; mismo criterio de resoluble. Usa la misma `NumeracionLlaves` y `leer_ubicaciones`; nada de `estacionadas`. Devuelve `ResultadoVerificacion`.
- [X] T018 [HU1] Punto de control (FR-301 a FR-308, FR-313): `python -m unittest` en verde (T011–T014 pasan) y commit «003 HU1: recorrido por oleadas y orden de llaves».

**Punto de control**: la verificación responde resoluble o no y da el orden. MVP de la capacidad.

---

## Fase 4: Historia 2 — Entender por qué no se puede ganar (Prioridad 2)

**Objetivo**: el mismo recorrido sigue por capas y da frontera, ubicaciones, dependencias y ciclos
(D4, D5, D6).

**Prueba independiente**: criptas sintéticas no resolubles armadas para cada caso; se compara cada
parte del reporte y el texto completo.

### Pruebas de la historia 2 (escribir primero; deben fallar)

- [X] T019 [HU2] Escribir `TestReporteBasico` en `tests/test_resolubilidad.py`, escenarios HU2-1, HU2-3, HU2-8, HU2-9, HU2-10 (FR-302, FR-309, FR-310, FR-311, FR-312, FR-316, FR-317, FR-318): HU2-1 el texto completo exacto de `contracts/reporte.md` (no obtenible `salida`; frontera «sala 1, E -> sala 2, pide itm_llave_salida»; ubicación; dependencia; ciclo); HU2-3 `x` sin ubicación: «no está en la cripta» en ubicaciones y en dependencias; HU2-8 línea de FR-317; HU2-9 sin `sala_salida` y sin `llave_salida`: líneas «Falta … en la cripta.» y el resto del reporte calculado igual; HU2-10 puerta bloqueada entre dos salas de la región no aparece en la frontera; frontera ordenada por id de origen y luego N, S, E, O.
- [X] T020 [HU2] Escribir `TestDependencias` en `tests/test_resolubilidad.py`, escenarios HU2-2, HU2-4, HU2-5, HU2-6, HU2-7 (FR-312, FR-314, FR-315): HU2-2 `a` depende de `b`, `b` de `a`, un ciclo `a -> b -> a`; HU2-4 llave en sala a la que solo se llega por salidas sin vuelta que salen de ella → «su sala no se alcanza ni abriendo todas las puertas» y en ningún ciclo; HU2-5 un camino con una puerta (`b`) frente a otro con dos (la primera `a`) → depende de `b`; HU2-6 empate `e`/`d` → `d`; HU2-7 `c` depende de `a` en el ciclo `a -> b -> a`, que es el único ciclo reportado; además: dependencia heredada de la primera puerta bloqueada (tres capas), y dos ciclos ordenados por su primera llave.
- [X] T021 [HU2] Escribir `TestReporteDeterminista` en `tests/test_resolubilidad.py`, escenario HU2-11 y FR-311 (FR-311, FR-316, FR-320, SC-305): la misma cripta no resoluble con la ubicación barajada, con las salas del esqueleto en otro orden y con las salidas de cada sala declaradas en otro orden da el mismo texto byte por byte; una llave con ubicaciones en salas 7 y 3, tres en la 3 (una sin enemigo, otra con `e-2` y otra con `e-1`) se muestra «sala 3, sala 3 (la suelta e-1), sala 3 (la suelta e-2), sala 7».
- [X] T022 [P] [HU2] Escribir `TestEquivalenciaReporte` en `tests/test_equivalencia_resolubilidad.py` (FR-313, FR-314, FR-332, SC-302): ≥ 200 criptas por semilla, mitad no resolubles (ciclos de 1 a 3 llaves, llaves sin ubicación, salidas sin vuelta, empates de dependencia), el texto de `texto_resultado` del verificador es igual al de `VerificadorIngenuo`.

### Implementación de la historia 2

- [X] T023 [HU2] Agregar al final de `verificar` en `crypta/Modelo/Verificador.py` la frontera y las ubicaciones (D6; FR-309, FR-310, FR-311): no obtenibles recorriendo 0..K-1; frontera recorriendo salas de la región por índice 0..V-1 y salidas N, S, E, O (cerrada, llave no obtenible, destino fuera de la región) y marcando en un `Vector` de K booleanos qué llaves pide; ubicaciones ordenadas una vez con `ordenar` por (número de llave, id de sala, enemigo o `""`) y un `Vector` `inicio_ubic` de K+1 posiciones. Depende de T015.
- [X] T024 [HU2] Agregar las capas a `crypta/Modelo/Verificador.py` (D4; FR-312, FR-313, FR-314): `capa_sala` y `origen_sala` (`Vector` de V, −1), `dependencia` (`Vector` de K, −1); semillas de la capa 1 = estacionadas de llaves sin `abre` recorridas por llave 0..K-1, con destino fuera de la región; dentro de cada capa, grupos por origen ascendente expandidos con una `Cola` por salidas cruzables (abiertas, cerradas sin llave o con llave obtenible); puertas bloqueadas desde salas de la capa hacia salas sin marcar van a las semillas de la capa siguiente con el origen heredado; semillas de cada capa siguiente ordenadas por origen con `ordenar` (estable). Al marcar una sala, las llaves no obtenibles ubicadas en ella sin dependencia reciben `origen_sala`. Motivos de «sin dependencia» según `Dependencia`. Nunca un recorrido por llave. Depende de T023.
- [X] T025 [HU2] Agregar los ciclos a `crypta/Modelo/Verificador.py` (D5; FR-315): `estado_ciclo` (`Vector` de K: 0, 1, 2) y una pila en `Vector`; desde cada llave no obtenible en orden 0..K-1 seguir `dependencia`; al encontrar una llave en estado 1, sacar el ciclo de la pila, rotarlo a su menor número y guardarlo; al final ordenar los ciclos por su primera llave con `ordenar`. Llenar `Reporte` completo, incluidos `falta_sala_salida`, `falta_llave_salida` (FR-318) y `salida_sin_puerta` (FR-317). Depende de T024.
- [X] T026 [P] [HU2] Completar `texto_resultado` en `crypta/Vista/FormatoVerificacion.py` para el caso no resoluble (FR-309 a FR-312, FR-315 a FR-318): secciones en el orden de FR-316 con las formas exactas de `contracts/reporte.md`, «  (ninguna)» en secciones vacías, ciclo como «k1 -> k2 -> … -> k1» y las líneas finales de FR-318 y FR-317 en ese orden.
- [X] T027 [P] [HU2] Completar `crypta/Modelo/VerificadorIngenuo.py` con el reporte (D8; FR-314, FR-331, FR-332): frontera, ubicaciones y ciclos recalculados con búsquedas lineales en vectores; dependencia de cada llave no obtenible con un recorrido 0-1 por cada llave distinta de la frontera (dos `Cola`, capa actual y siguiente) desde los destinos de las puertas de la frontera que la piden hasta las ubicaciones de la llave buscada, eligiendo el menor (capas, id). No reutiliza `capa_sala`, `origen_sala` ni `estacionadas`.
- [X] T028 [HU2] Punto de control (FR-302, FR-309 a FR-318, FR-320): `python -m unittest` en verde (T019–T022 pasan) y commit «003 HU2: frontera, dependencias por capas y ciclos».

**Punto de control**: el reporte completo sale del mismo recorrido y coincide con la ingenua.

---

## Fase 5: Historia 3 — La verificación al iniciar una partida (Prioridad 3)

**Objetivo**: pedir y guardar la ubicación de las llaves, verificar antes de crear `partida.log` y
respetar `--forzar` (D9; `contracts/cli.md`).

**Prueba independiente**: `main` con almacén temporal y fuentes falsas, en línea y sin conexión, con
y sin `--forzar`; se comprueba qué se imprime, si inicia, qué solicitudes se hacen y qué queda en
disco.

### Pruebas de la historia 3 (escribir primero; deben fallar)

- [X] T029 [HU3] Escribir `TestLlavesFuentes` en `tests/test_verificacion_inicio.py` (FR-322, FR-323, FR-324; HU3-4, HU3-5, HU3-6): `FuenteHTTP.obtener_llaves` pide `/criptas/<id>/llaves` por `_get` (parchear `requests.get`) y cuenta una solicitud; con el presupuesto agotado lanza `PresupuestoAgotado` sin enviar; `FuenteOffline.obtener_llaves` lee el campo `llaves` de la copia local y sin él lanza `LlavesNoDisponibles`; `AlmacenDisco.guardar_cripta(..., llaves=...)` lo escribe junto a `version`; `GestorCripta.cargar_llaves` usa la copia con la misma versión sin solicitud, la pide con otra versión (la copia se invalida por versión) y la pide si la copia de la misma versión no tiene `llaves`.
- [X] T030 [HU3] Escribir `TestInicioPartida` en `tests/test_verificacion_inicio.py`, escenarios HU3-1, HU3-2, HU3-3, HU3-11 (FR-325, FR-327): `main` (con `sys.argv` y `AlmacenDisco`/`VistaConsola` parcheados, carpeta temporal como directorio actual) con cripta no resoluble sin `--forzar`: imprime el reporte y «La partida no inicia. Use --forzar para jugarla de todos modos.», no instancia la vista, no existe `partida.log`, código 2; con `--forzar`: reporte, «Se inicia la partida por --forzar.» y la partida se crea; resoluble: imprime el orden y la partida se crea; HU3-11: el reporte nombra salas no exploradas y la verificación no cambia ninguna sala ni puerta del `Mapa` (comparar estado de puertas antes y después). *Nota*: la parte de HU3-11 sobre el mapa conocido (las salas siguen desconocidas) se prueba en la capacidad 002, que es la que crea el mapa conocido.
- [X] T031 [HU3] Escribir `TestInicioSinVerificar` en `tests/test_verificacion_inicio.py`, escenarios HU3-4, HU3-5, HU3-6, HU3-7, HU3-8 (FR-319, FR-321, FR-322, FR-323, FR-324, FR-325): en línea sin copia de llaves → una solicitud `obtener_llaves`, contada, y la copia local queda con `llaves` y su versión; segundo inicio → ninguna solicitud de llaves (SC-306); `--offline` con llaves en la copia → ninguna solicitud; `--offline` sin llaves, falla de red y presupuesto agotado → aviso «no se pudo verificar», código 1 sin `--forzar` e inicio con `--forzar`; ubicación con sala inexistente → mensaje de `DatosInvalidos`, código 1, no inicia aun con `--forzar`; en todos, `obtener_contenido` no se llama durante la verificación.
- [X] T032 [HU3] Escribir `TestSinVerificacion` en `tests/test_verificacion_inicio.py`, escenarios HU3-9 y HU3-10 (FR-326, FR-327): `--replay` de un `partida.log` de una partida forzada sobre una cripta no resoluble no llama a `obtener_llaves`, no imprime nada de la verificación y da la misma partida; cargar una partida guardada no verifica; el archivo de partida y `partida.log` no contienen nada de la verificación; usar el pergamino no la toca.

### Implementación de la historia 3

- [X] T033 [P] [HU3] Agregar `obtener_llaves(cripta_id)` a `crypta/Adaptadores/FuenteHTTP.py` (FR-322): `return self._get(f"/criptas/{cripta_id}/llaves")`; cuenta y respeta el presupuesto como toda solicitud, incluidos los reintentos de un 429.
- [X] T034 [P] [HU3] Agregar `obtener_llaves(cripta_id)` a `crypta/Adaptadores/FuenteOffline.py` (FR-324): lee la copia local con `_cripta_local`; devuelve `datos["llaves"]` o lanza `LlavesNoDisponibles` («sin conexión y sin la ubicación de las llaves en la copia local») si no está.
- [X] T035 [P] [HU3] Agregar el parámetro `llaves=None` a `guardar_cripta` en `crypta/Adaptadores/AlmacenDisco.py` (FR-323): si no es None se escribe el campo `llaves` en el JSON, junto a `version`, `esqueleto`, `contenidos` y `datos_generales`.
- [X] T036 [HU3] Cambiar `crypta/Controlador/GestorCripta.py` (D9; FR-322, FR-323, FR-324): `cargar` conserva `guardada.get("llaves")` cuando la versión coincide; nuevo `cargar_llaves(cripta_id)` que devuelve esas llaves o llama a `fuente.obtener_llaves` y las conserva, y traduce `LlavesNoDisponibles`, `PresupuestoAgotado` y `RuntimeError` en `NoVerificable(motivo)` con los motivos de `contracts/reporte.md`; `persistir` pasa `llaves=` a `guardar_cripta`. Depende de T035.
- [X] T037 [HU3] Crear `crypta/Controlador/Verificacion.py` (D9; FR-301, FR-319, FR-321, FR-324): `preparar_verificacion(gestor_cripta, cripta_id, datos_cripta, mapa)` → `cargar_llaves`; si es `NoVerificable`, lo devuelve; si no, `leer_ubicaciones` (deja pasar `DatosInvalidos`) y `verificar`; devuelve `ResultadoVerificacion` o `NoVerificable`. Y `texto_de(resultado)` que usa `texto_resultado` o la línea de «no se pudo verificar». No recibe `GestorContenido`. Depende de T015, T025 y T036.
- [X] T038 [HU3] Cambiar `crypta/main.py` para verificar al iniciar (D9; FR-325, FR-326, FR-327; `contracts/cli.md`): bandera `--forzar` (`store_true`); nueva `preparar_cripta(args)` (almacén, fuente, `GestorCripta.cargar`, `fijar_presupuesto`), que **no** verifica y devuelve la cripta preparada (almacén, fuente, gestor, datos generales, `Mapa`); `crear_partida(args, preparada=None)` **conserva su firma y su retorno de 4 valores** `(controlador, gestor_cripta, datos_cripta, fuente)`: si recibe `preparada` la usa, y si no, llama ella misma a `preparar_cripta` **sin verificar**; después crea repositorio, partida, `partida.log`, vista y controlador como hoy. La verificación vive **solo** en `main` y en `--verificar` (T042): `main` llama a `preparar_cripta`, después a `preparar_verificacion`, imprime el texto, y si no es resoluble o no verificable sin `--forzar`: imprimir la línea de decisión, persistir la copia local si no es `--offline`, y devolver 2 (no resoluble) o 1 (no verificable) sin crear vista ni `partida.log`; con `--forzar`, imprimir «Se inicia la partida por --forzar.»; si inicia, llama a `crear_partida(args, preparada)`; `DatosInvalidos` → 1 aunque haya `--forzar`. `reproducir` no cambia (no verifica; `--forzar` no tiene efecto, FR-336). Los nombres que parchean las pruebas (`crypta.main.AlmacenDisco`, `nueva_partida`, `VistaConsola`) se conservan. Depende de T037.
- [X] T039 [HU3] Ajustar solo los datos de las pruebas existentes que inician una partida **por `main`** (SC-307; FR-324): en `tests/test_controlador.py` (y cualquier otra prueba que llame a `programa.main()` sin `--bench`/`--replay`), las llamadas a `guardar_cripta` de las criptas que usan esas pruebas pasan `llaves={"llaves": [{"id": "itm_llave", "sala": 2}]}` (la cripta de prueba ya es resoluble: `itm_llave` en la sala 2, puerta 2→3 y `sala_salida` 3). Las pruebas que llaman directamente a `programa.crear_partida(args)` no cambian: esa función no verifica (T038). El `ServidorFalso` de las pruebas en línea responde `/criptas/c-prueba/llaves`. No se cambia ninguna aserción, salvo la excepción de SC-307: en `TestPresupuestoEnElJuego` la cuenta exacta de solicitudes sube de 5 a 6 y el presupuesto justo del escenario «sin presupuesto» de 5 a 6, anotados como «+1: ubicación de llaves, FR-322». Depende de T035 y T038.
- [X] T040 [HU3] Punto de control (FR-319, FR-321 a FR-327, FR-336): `python -m unittest` completo en verde (T029–T032 pasan; las pruebas de P1 y la 001 siguen verdes solo con T039) y commit «003 HU3: llaves en la copia local y verificación al iniciar».

**Punto de control**: el juego verifica antes de empezar y respeta `--forzar`.

---

## Fase 6: Historia 4 — `--verificar` (Prioridad 4)

**Objetivo**: verificar desde la línea de comandos sin jugar, con códigos 0, 2 y 1.

**Prueba independiente**: `main` con `--verificar` sobre criptas resolubles, no resolubles e
inválidas; salida, código y que no se crea nada de la partida.

### Pruebas de la historia 4 (escribir primero; deben fallar)

- [X] T041 [P] [HU4] Escribir `TestModoVerificar` en `tests/test_verificacion_inicio.py`, escenarios HU4-1 a HU4-6 (FR-322, FR-323, FR-328, FR-329, FR-336): `--verificar c-prueba` resoluble → texto del orden y código 0; no resoluble → reporte y código 2; falla de red, ubicación inválida y `--offline` sin llaves en la copia → motivo y código 1; en todos, `VistaConsola` parcheada para fallar si se instancia, no existe `partida.log` ni se crea `Partida` (parchear `nueva_partida` para fallar); en línea, las solicitudes (esqueleto si no estaba, llaves) se cuentan y la copia local queda guardada con `llaves`; HU4-6: `--verificar` con `--replay` o con `--bench` → error de uso, código 1, sin llamar a `obtener_llaves`; `--verificar --forzar` da el mismo texto y código que sin `--forzar`.

### Implementación de la historia 4

- [X] T042 [HU4] Agregar `--verificar CRIPTA` a `crypta/main.py` (FR-328, FR-329, FR-336; `contracts/cli.md`): rechazar la combinación con `--replay` o `--bench` antes de verificar (código 1, mismo estilo que hoy); función `verificar(args)` que usa `preparar_cripta` con `args.verificar` como id, imprime el texto, persiste la copia local si no es `--offline` y devuelve 0, 2 o 1; `DatosInvalidos`, `RuntimeError`, `ValueError` y `OSError` → motivo y 1. No crea vista, partida ni `partida.log`; ignora `--forzar`. Depende de T038.
- [X] T043 [HU4] Punto de control (FR-328, FR-329, FR-336): `python -m unittest` en verde (T041 pasa) y commit «003 HU4: --verificar».

---

## Fase 7: Historia 5 — Medición con `--bench` (Prioridad 5)

**Objetivo**: secciones R1–R5 de `contracts/bench.md` con criptas sintéticas por semilla.

**Prueba independiente**: `--bench` dos veces con la misma semilla genera las mismas criptas,
incluye ambas alternativas, coincide en el resultado y no usa vista ni red.

### Pruebas de la historia 5 (escribir primero; deben fallar)

- [X] T044 [HU5] Escribir en `tests/test_bench.py` las pruebas del generador (FR-330; HU5-1): dos llamadas a `generar_cripta_llaves(semilla, salas, llaves, resoluble)` dan la misma huella (salas, salidas con dirección, destino, cerrada, llave y sin vuelta, y ubicaciones serializadas en orden); con `resoluble=True` el verificador dice resoluble y hay una ronda por llave encadenada; con `resoluble=False` dice no resoluble y hay al menos un ciclo; los ids de llave tienen ceros a la izquierda y la respuesta se entrega ordenada y barajada.
- [X] T045 [HU5] Escribir en `tests/test_bench.py` las pruebas de las secciones (FR-331 a FR-335; HU5-2, HU5-3, HU5-6): R1–R5 corren en modo rápido (`rapido=True`, tamaños pequeños) y su texto tiene las columnas de `contracts/bench.md`; R4 con una variante saboteada a propósito (la ingenua devuelve un texto distinto) imprime ERROR y `bench.ejecutar` devuelve código distinto de 0; R2 y R3 imprimen «¿cumple?»; las secciones corren con una fuente que falla si se la llama y con `VistaConsola` parcheada para fallar.

### Implementación de la historia 5

- [X] T046 [HU5] Crear el generador en `crypta/bench/bench_resolubilidad.py` (FR-330; `contracts/bench.md`): `generar_cripta_llaves(semilla, salas, llaves, resoluble=True)` con su propio `random.Random(semilla)`: `llaves + 1` zonas en cadena (cuadrículas pequeñas con salidas abiertas, cerradas sin llave y algunas sin vuelta), la puerta de la zona i a la i+1 pide `itm_llave_<i>` con ceros a la izquierda ubicada en la zona i (a veces con `enemigo`), la última pide `llave_salida` hacia `sala_salida`; puertas distractoras y llaves que ninguna puerta pide; con `resoluble=False`, una zona rota con llave detrás de sí misma o ciclo de 2–3 llaves y algunas llaves sin ubicación; devuelve datos generales, esqueleto, respuesta ordenada y respuesta barajada; y `huella(...)`.
- [X] T047 [HU5] Agregar R1–R3 a `crypta/bench/bench_resolubilidad.py` (FR-331, FR-334, FR-335; principio VI: «Verificación de resolubilidad | 200 ms»): R1 incremental frente a ingenua con (500, 125), (1 000, 250), (2 000, 500), resolubles y no, cociente ingenua / incremental, la ingenua de 2 000 salas con **una sola repetición**; R2 2 000 salas y 500 llaves, media, p95 y máximo desde el esqueleto ya cargado (`Mapa`) y la ubicación en memoria hasta el texto (FR-334), el tiempo de cargar el `Mapa` aparte y sin límite, «¿cumple? < 200 ms», y la cripta publicada más grande si está en `cache/`; R3 incremental con 500, 1 000, 2 000, 4 000 y 8 000 salas (llaves proporcionales), cocientes al duplicar con «¿cumple? ≤ 3», y la ingenua en la misma tabla con 500, 1 000 y 2 000 salas, para comparar sus cocientes con los de la incremental en los mismos tamaños. Usa `medicion.medir` y `medicion.tabla`. Depende de T046.
- [X] T048 [HU5] Agregar R4 y R5 a `crypta/bench/bench_resolubilidad.py` (FR-332, D1): R4 compara el texto del verificador y de la ingenua en las criptas de los tamaños de R1 y en 50 criptas pequeñas por semilla (no las de 4 000 y 8 000 salas), cuenta criptas y diferencias e imprime ERROR por cada diferencia, y la función devuelve un indicador de error; R5 con K = 500, 2 000 y 8 000 ids y E + L búsquedas: `NumeracionPorInsercion` con ids barajados y con ids ordenados frente a `NumeracionLlaves`, con tiempo de construir + buscar y altura de cada árbol. La tabla hash no se mide (research D1). Depende de T047.
- [X] T049 [HU5] Registrar las secciones en `crypta/bench/bench.py` (FR-331 a FR-333): entradas en `SECCIONES` («resol_ingenua» R1, «resol_limite» R2, «resol_crecimiento» R3, «resol_igualdad» R4, «resol_numeracion» R5) con títulos que citen el FR; si R4 encuentra diferencias, `ejecutar` devuelve código distinto de 0, igual que B6. Depende de T048.
- [ ] T050 [HU5] Medir la resolubilidad (FR-334, FR-335; SC-303, SC-304; principio VI): primero `python -m crypta.main --listar` y `python -m crypta.main --verificar <la cripta publicada más grande>` para que quede en `cache/` (si no hay ninguna publicada, anotarlo para `DECISIONES.md`); después correr **solo** las secciones de resolubilidad (`resol_ingenua`, `resol_limite`, `resol_crecimiento`, `resol_igualdad`, `resol_numeracion`) y revisar que R2 y R3 cumplan; si no, parar y revisar la implementación (o documentar el límite) antes de seguir. **No** escribe en `docs/resultados_bench_p2.txt` (ahí están los números de la 001): el bench completo se corre al final del proyecto. Depende de T049.
- [ ] T051 [HU5] Punto de control (FR-330 a FR-335): `python -m unittest` en verde (T044, T045 pasan) y commit «003 HU5: --bench de resolubilidad».

---

## Fase 8: Cierre (documentación y revisión)

**Propósito**: documentación exigida (principio X) y revisiones de la constitución.

- [ ] T052 Escribir la sección §5.4 «Resolubilidad» en `DECISIONES.md` (FR-313, FR-314, FR-331 a FR-335; principio X): problema, alternativas, decisión, complejidad, evidencia y límites, a partir de research D1, D3, D4, D5 y D8 (incluida la tabla hash como alternativa analizada sin medir y la respuesta a «¿qué hace su verificación con las puertas que encontró cerradas antes de tener esa llave?»), con los números de R1–R5 de la corrida de T050 (y, si no hay cripta publicada, que el límite se midió solo con la sintética) y el límite de las salidas sin vuelta de los Supuestos de la spec; enlazar a `specs/003-resolubilidad/spec.md` y `plan.md` y decir si la decisión final coincide con plan.md y, si no, qué medición motivó el cambio. Depende de T050.
- [ ] T053 [P] Actualizar `README.md` (FR-325, FR-328, FR-329; principio X): `--verificar <cripta>` y `--forzar` con sus códigos de salida, que la ubicación de las llaves se guarda en la copia local, las secciones nuevas de `--bench` y cómo correr las pruebas de la capacidad (comando de `quickstart.md` §1).
- [ ] T054 [P] Completar `PROMPTS_LLM.md` (principio X): registrar `/speckit-plan`, los ajustes del grupo al plan, `/speckit-tasks` y los prompts de la implementación de la 003.
- [ ] T055 Revisar imports prohibidos y constantes quemadas (principios I y IV): `git grep -n -E "import (heapq|bisect|collections|networkx)|from (heapq|bisect|collections|networkx)" -- crypta` sin resultados; revisar a mano que `NumeracionLlaves.py`, `UbicacionLlaves.py`, `Verificador.py`, `VerificadorIngenuo.py` y `FormatoVerificacion.py` no usen `dict`, `set`, `sorted` ni `list.sort` (los `dict` de `json` solo se leen en `UbicacionLlaves.py`); `git grep -n "itm_llave" -- crypta` solo en `crypta/bench`. Corregir lo que aparezca donde aparezca.
- [ ] T056 Validar de punta a punta según `specs/003-resolubilidad/quickstart.md` (SC-301 a SC-308): pasos 1 a 5, incluido `--verificar cripta-01` en línea y sin conexión y el inicio con una cripta no resoluble armada con las ayudas de prueba, y marcar lo comprobado en `specs/003-resolubilidad/checklists/requirements.md`.
- [ ] T057 Punto de control final (FR-301 a FR-336): `python -m unittest` en verde y commit «003 cierre: DECISIONES §5.4, README, PROMPTS_LLM».

---

## Dependencias y orden de ejecución

### Entre fases

- **Fase 1**: sin dependencias. **T001 antes de cualquier commit de código.**
- **Fase 2**: depende de la fase 1. Bloquea todas las historias.
- **Fase 3 (HU1)**: depende de la fase 2.
- **Fase 4 (HU2)**: depende de la fase 3 (extiende `Verificador.py`, T015).
- **Fase 5 (HU3)**: los adaptadores (T029, T033–T036) solo dependen de la fase 2 y pueden ir en
  paralelo con las fases 3 y 4; T037 y T038 esperan a T025.
- **Fase 6 (HU4)**: depende de T038.
- **Fase 7 (HU5)**: depende de la fase 4 (necesita el reporte de ambas alternativas para R4). El
  generador (T044, T046) puede empezarse en cuanto termine T015.
- **Fase 8**: T052 depende de T050; T057 depende de todo.

### Dentro de cada historia

- Pruebas primero, y deben fallar; después la implementación; al final el punto de control.
- Estructuras (`crypta/estructuras`) antes que el modelo; el modelo antes que el Controlador y
  `main.py`.
- Las tareas que tocan el mismo archivo van en el orden de sus ID.

### Archivos con varias tareas (no se reparten a la vez)

| Archivo | Tareas |
|---|---|
| `tests/ayudas_cripta.py` | T002, T009 |
| `tests/test_resolubilidad.py` | T004, T011, T012, T014, T019, T020, T021 |
| `tests/test_equivalencia_resolubilidad.py` | T013, T022 |
| `tests/test_verificacion_inicio.py` | T029, T030, T031, T032, T041 |
| `tests/test_bench.py` | T044, T045 |
| `crypta/Modelo/Verificador.py` | T015, T023, T024, T025 |
| `crypta/Modelo/VerificadorIngenuo.py` | T017, T027 |
| `crypta/Vista/FormatoVerificacion.py` | T016, T026 |
| `crypta/main.py` | T038, T042 |
| `crypta/bench/bench_resolubilidad.py` | T046, T047, T048 |

Las pruebas que comparten archivo no llevan [P]: las escribe una sola persona en el orden de sus
ID, o se reparten por clase y se juntan con cuidado.

---

## Ejemplos de trabajo en paralelo

### Fase 2

```text
Integrante A: T003 → T005 (NumeracionLlaves)
Integrante B: T004 → T007 (UbicacionLlaves), después de T006
Integrante C: T006 (ResultadoVerificacion) → T008 (FuenteDatos) → T009 (ayudas)
```

### Historias 1 y 2

```text
Integrante A: T015 → T023 → T024 → T025 (Verificador.py)
Integrante B: T011, T012, T014 → T019, T020, T021 (tests/test_resolubilidad.py)
Integrante C: T016 → T026 (FormatoVerificacion) y T017 → T027 (VerificadorIngenuo), T013, T022
```

### Historia 3 (adaptadores en paralelo con las historias 1 y 2)

```text
Integrante C: T029 → T033, T034, T035 → T036
Luego: T030, T031, T032 → T037 → T038 → T039
```

### Historias 4 y 5

```text
Integrante A: T041 → T042
Integrante B: T044 → T046 (en cuanto exista T015) → T045 → T047 → T048 → T049 → T050
```

---

## Estrategia de implementación

### MVP primero

1. Fases 1 y 2.
2. Fase 3 (HU1): ya se sabe si la cripta es resoluble y el orden. **Validar** con
   `python -m unittest`.
3. Fase 4 (HU2): el reporte con dependencias y ciclos, que es lo que más pesa del problema §5.4.

### Entrega incremental

Cada fase termina en un commit con todo en verde. Si el tiempo no alcanza, lo que queda fuera es
de las últimas fases; nunca se deja una fase a medias sin su punto de control.

### Calendario sugerido (entrega el miércoles 18 de noviembre)

Las capacidades 002 y 004 avanzan en paralelo, así que la 003 se reparte así:

| Día | Fases |
|---|---|
| Sáb 14 | Fases 1 y 2 (T001 primero), fase 3 (HU1); adaptadores de la fase 5 en paralelo |
| Dom 15 | Fase 4 (HU2) |
| Lun 16 | Fase 5 (HU3) y fase 6 (HU4) |
| Mar 17 | Fase 7 (HU5) y fase 8 (cierre) |

---

## Notas

- [P] = otro archivo y sin dependencias pendientes.
- Cada prueba cita su FR en el nombre del método o en el docstring (principio IX); los escenarios
  se nombran HUx-n en el docstring. Los 4 casos de «Resolubilidad» del Apéndice B están en T019
  (HU2-1), T011 (HU1-3 y HU1-2) y T030 (HU3-1).
- Comprobar que cada prueba falla antes de implementar.
- Nunca usar `cache/` en las pruebas: siempre un `AlmacenDisco` en una carpeta temporal.
- Si una tarea encuentra un caso que la spec no cubre, se para y se corrige primero la spec
  (principio VIII).
