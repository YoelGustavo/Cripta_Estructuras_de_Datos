# Constitución del Proyecto CRIPTA

Proyecto CRIPTA, EIF-207 Estructuras de Datos, II ciclo 2026, segunda parte. Se continúa sobre el
código de la primera parte, en Python 3.11 o superior.

Esta constitución manda sobre todo el proyecto. Toda spec.md, plan.md y tasks.md, y todo el
código, DEBEN cumplirla. Si un plan o una tarea la contradice, se corrige el plan o la tarea; la
constitución nunca se ignora. Todo lo establecido en la primera parte (P1) sigue vigente salvo que
la segunda parte (P2) lo cambie explícitamente.

## Principios

### I. Estructuras de datos propias (P1 §7, P1 §4.9, P2 §6.2)

- Las estructuras de los problemas evaluados (agenda de eventos, rutas del cazador y de «ir a»,
  mapa conocido, resolubilidad, línea de tiempo, caché, inventario, historial de retroceso y
  ordenamientos) DEBEN implementarse a mano en `crypta/estructuras`.
- Prohibido para esos problemas: `dict` y `set` como índice, caché, tabla de búsqueda o estructura
  propia; `heapq`; `bisect`; `collections` (`deque`, `OrderedDict`, `defaultdict`, `Counter`);
  `networkx` o cualquier biblioteca de grafos o de búsqueda de rutas; `list.sort()` y `sorted()`
  en los ordenamientos evaluados.
- `list` solo se permite como almacenamiento contiguo dentro de nuestro `Vector`. Los `dict` que
  devuelve `json` solo se usan para leer datos y se traducen a nuestras estructuras.
- Permitidos: `struct`, `json`, `requests`, bibliotecas de interfaz y la biblioteca estándar que no
  reemplace una estructura evaluada.
- Se pueden reutilizar las estructuras de la primera parte (`Vector`, `ListaSimple`, `ListaDoble`,
  `Cola`, `Pila`, `MonticuloMin`, `ArbolBusqueda`, `CacheLRU`, `ordenar`) o crear nuevas del
  temario del curso (grafos, tablas hash, búsqueda binaria), siempre implementadas por nosotros.
- Ni el agente ni un plan generado pueden agregar dependencias nuevas (en `requirements.txt` o en
  imports) sin aprobación explícita del grupo.

**Razón**: elegir, implementar y defender las estructuras es el objeto de evaluación; una
biblioteca equivalente anula el trabajo evaluado.

### II. Determinismo (P1 §2, P2 §3)

- Misma versión de cripta, misma semilla y misma secuencia de acciones DEBEN producir exactamente
  la misma partida, incluida la misma secuencia de llamadas al generador aleatorio.
- Todo el azar sale de una instancia propia `random.Random(semilla)`; nunca del generador global
  del módulo `random`.
- Todo empate se rompe con una regla fija y documentada:
  - agenda de eventos: menor tiempo y luego menor número de secuencia; toda reprogramación recibe
    un número de secuencia nuevo;
  - activación simultánea de enemigos: orden ascendente de id de instancia;
  - rutas del cazador y de «ir a»: primer paso hacia la vecina de menor id entre las que inician
    una ruta de costo mínimo;
  - resolubilidad: orden de obtención de llaves y ciclo reportado deterministas.
- Ni el tiempo real ni el orden de llegada de respuestas de red deciden nada; esperar la red nunca
  avanza el reloj virtual.
- Reutilizar un cálculo anterior (rutas, distancias, alcanzabilidad) solo es válido si se puede
  demostrar que da el mismo resultado que calcular desde cero en ese instante.

**Razón**: `--replay` es el mecanismo principal de evaluación y de reporte de errores.

### III. Arquitectura MVC (P1 §6)

- El Modelo contiene las reglas del juego y las estructuras, y NO conoce HTTP, archivos ni la
  interfaz concreta.
- La red y el disco van detrás de adaptadores con un mismo contrato lógico; `--offline` cambia la
  fuente sin poner `if` por todo el modelo.
- `--replay`, `--bench` y `--verificar` DEBEN ejecutarse sin instanciar la vista interactiva.

**Razón**: permite probar y medir el modelo de forma aislada y reproducible.

### IV. Nada quemado en el código (P1 §9)

- Prohibido escribir datos de una cripta concreta: números de sala, ids de entidades o instancias,
  cantidad de páginas, presupuestos, estadísticas, costos de salidas o rangos.
- Todo sale del servicio, del catálogo o de la copia local validada. Las únicas constantes
  permitidas son las reglas del juego fijadas por los enunciados (por ejemplo, costo 100 por
  omisión de una salida, límite de 5 retrocesos).

**Razón**: la revisión usa una cripta no publicada previamente.

### V. Red y presupuesto (P1 §3, P1 §5.1, P2 Apéndice A)

- Se respeta `presupuesto_solicitudes` en cada partida; su valor nunca se calcula ni se quema.
- Toda solicitud HTTP cuenta, incluidas `/llaves`, las verificaciones de versión y los reintentos
  después de un 429.
- Se usan lotes, precarga y persistencia local validada por versión de cripta y de catálogo. Lo
  persistido por la primera parte se invalida mediante esa validación de versión, nunca borrando
  archivos a mano.
- Lo leído de disco o en modo `--offline` no cuenta como solicitud.
- Al final de cada partida se reportan solicitudes realizadas, presupuesto, aciertos y fallos de
  caché.

**Razón**: el presupuesto de red es una restricción evaluada y verificada en la defensa.

### VI. Rendimiento medido (P1 §5.2, P2 §6.1, P2 §6.3)

- Toda afirmación de rendimiento se respalda con `--bench`, usando criptas sintéticas
  deterministas por semilla, y midiendo también la alternativa descartada cuando el enunciado lo
  pide (cálculo compartido frente a individual, reutilización frente a recálculo, recorrido
  incremental frente a repetido, distintos valores de K y la alternativa sin puntos de control).
- Límites en el equipo local, sin red ni renderizado:

  | Operación | Límite | Condiciones |
  |---|---|---|
  | Ciclo de eventos entre dos decisiones del jugador | 20 ms | Decenas de cazadores activos |
  | Verificación de resolubilidad | 200 ms | La cripta publicada más grande |
  | Consulta de historia | 50 ms | Partida de 5000 acciones, K por defecto |
  | Paso de «ir a» | 5 ms | Mapa conocido completo |

- Si el profesor ajusta estos valores por enmienda (P2 §2.7), se actualiza esta tabla.

**Razón**: una decisión de estructura sin mediciones propias no satisface el objetivo del curso.

### VII. Reversibilidad (P1 §2.11, P1 §4.6, P2 §3.5, P2 §3.6)

- Todo cambio del estado del juego, incluido el mapa conocido por el jugador, se registra con la
  información mínima para invertirlo.
- Prohibido guardar copias completas del estado, con una única excepción: los puntos de control de
  la línea de tiempo, como máximo uno cada K acciones del jugador. Si se reconstruye re-simulando,
  el punto de control incluye el estado del `random.Random`.
- La cantidad de pergaminos de retroceso y la caché quedan fuera del estado reversible.
- Consultar la historia nunca consume tiempo virtual, nunca se anota en `partida.log` y nunca
  modifica el historial de retroceso ni ningún otro estado del juego.

**Razón**: la memoria debe crecer con los cambios ocurridos, no con «acciones por tamaño del
estado».

### VIII. Primero la especificación (P2 §2.2, P2 §2.4, P2 §2.6)

- Cada capacidad sigue el flujo specify → clarify → plan → tasks → analyze → implement. Ningún
  código de una capacidad se escribe antes de que su spec.md esté confirmado en Git.
- spec.md contiene reglas del juego, historias de usuario, escenarios de aceptación y requisitos
  funcionales y de rendimiento numerados; NUNCA nombra estructuras de datos, clases ni módulos.
- plan.md contiene las estructuras elegidas, las alternativas, la complejidad, los módulos
  afectados y las mediciones planificadas; NUNCA agrega reglas que no estén en spec.md.
- Si al implementar se descubre que la especificación estaba mal, primero se corrige la
  especificación y después el código, en commits separados.
- Al entregar, ninguna especificación puede estar desactualizada respecto al programa; un
  comportamiento sin especificación es un defecto del mismo tipo.

**Razón**: el historial de Git y la coherencia spec–código se evalúan y se demuestran en la
defensa.

### IX. Trazabilidad y pruebas (P2 §2.5)

- Cada requisito funcional tiene un id estable (FR-001, FR-002, …) que no se renumera.
- Cada caso del Apéndice B de P2 («casos que deben tener un resultado definido») aparece como
  escenario de aceptación en alguna especificación.
- Cada escenario tiene al menos una prueba automatizada (o un `partida.log` de reproducción) que
  cita su FR.
- Cada tarea de tasks.md cita los FR que atiende; no hay tareas sin requisito.
- `python -m unittest` pasa completo, incluidas las pruebas de la primera parte, antes de cada
  commit de código.

**Razón**: en la defensa se recorre un requisito al azar: escenario, tarea, código y prueba.

### X. Documentación (P2 §7.1, P2 §7.2, P1 §8, P1 §10)

- `DECISIONES.md` tiene una sección por cada problema de P2 §5, con problema, alternativas,
  decisión, complejidad, evidencia de `--bench` y límites conocidos; enlaza a su spec y su plan, y
  dice si la decisión final coincide con plan.md y, si no, qué medición motivó el cambio.
- `PROMPTS_LLM.md` registra cada invocación de spec-kit con texto propio y cada prompt a un LLM,
  con fecha, herramienta, texto y uso.
- El README indica la versión de spec-kit (v1.3.1), el agente (Claude Code), los comandos nuevos
  (`--verificar`, `--forzar`, `--checkpoint-cada`, `--replay … --hasta`) y cómo correr las pruebas
  de aceptación.

**Razón**: la documentación es entregable evaluado y debe reflejar lo que el programa hace.

### XI. Compatibilidad con la primera parte (P2 §3.6, P2 §5.6, P1 §4.10)

- Un archivo de guardado de la primera parte se reporta como incompatible o se migra
  explícitamente; nunca se carga en silencio.
- Las decisiones de la primera parte (en especial agenda de eventos e historial de retroceso) se
  vuelven a medir con la carga nueva (cazadores, costos variables, línea de tiempo). Si alguna
  deja de ser adecuada, se cambia y se documenta el antes y el después; si sigue siendo adecuada,
  se muestra con datos.

**Razón**: las reglas nuevas cambian la carga sobre estructuras existentes.

## Fuentes y precedencia

Enunciados oficiales; las referencias de la forma «P1 §x» y «P2 §x» apuntan a sus secciones:

- **P1** — primera parte: `docs/Primer Proyecto - Estructuras de Datos II 2026.pdf`
- **P2** — segunda parte: `docs/Cripta - Parte II.pdf`

El texto de P2 está en `docs/Cripta - Parte II.txt`, convertido del PDF. El agente DEBE leer ese
archivo, porque en este equipo no puede leer los PDF. Si hay diferencias, la fuente oficial sigue
siendo el PDF.

Orden de precedencia ante un conflicto:

1. Enmiendas del profesor (P2 §2.7).
2. P2, en lo que modifique explícitamente a P1.
3. P1.
4. Esta constitución, que traduce los enunciados en principios del grupo y agrega reglas propias.
5. spec.md, plan.md y tasks.md de cada capacidad.

Swagger del servicio es la referencia del contrato HTTP exacto; los enunciados lo son para las
reglas del juego, restricciones, rendimiento y evaluación.

## Flujo de trabajo y puertas de calidad

- **Especificación por capacidad**: como mínimo una especificación por cada capacidad de P2 §3:
  terreno y cazador, niebla de guerra (incluido «ir a»), resolubilidad y línea de tiempo, en
  `specs/<NNN-capacidad>/`.
- **Puerta de plan**: plan.md incluye una revisión de cumplimiento de los principios I–XI. Toda
  estructura o dependencia propuesta se revisa contra el principio I antes de aprobar el plan.
- **Puerta de tareas**: cada tarea cita sus FR; las tareas de medición citan el límite del
  principio VI que verifican.
- **Puerta de analyze**: se ejecuta `/speckit-analyze` antes de implementar; toda violación de la
  constitución se trata como crítica.
- **Puerta de commit de código**: `python -m unittest` completo en verde; ningún import prohibido
  por el principio I; el spec.md correspondiente ya confirmado en un commit anterior.
- **Puerta de entrega**: specs sincronizadas con el programa, `DECISIONES.md` con evidencia de
  `--bench`, `PROMPTS_LLM.md` y README actualizados.

## Governanza

- Esta constitución prevalece sobre cualquier spec, plan, tarea o práctica del proyecto.
- Solo se modifica por decisión explícita del grupo o por una enmienda del profesor (P2 §2.7).
  Cada modificación sube la versión y anota la fecha y el motivo del cambio.
- Versionado semántico:
  - MAJOR: se elimina o redefine un principio de forma incompatible.
  - MINOR: se agrega un principio o sección, o se amplía materialmente una regla.
  - PATCH: aclaraciones, redacción o rutas sin cambio de significado.
- Revisión de cumplimiento: en cada fase (plan, tasks, analyze, implement) el agente DEBE revisar
  el cumplimiento de estos principios y señalar cualquier violación en lugar de seguir adelante.
  Si un plan o una tarea contradice la constitución, el error es del grupo y se corrige el
  artefacto, no la constitución (salvo enmienda formal).

**Version**: 1.0.1 | **Ratified**: 2026-11-05 | **Last Amended**: 2026-11-07
