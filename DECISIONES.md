Deciciones
Nota: Las pruebas y resultados de las evidencias pueden variar dependiendo de la potencia de la maquina donde se esté ejecutando el programa.

4.1
Problema. Todo lo que pasa en el juego es un evento con un tiempo: turnos del jugador y de los enemigos, veneno, antorcha, trampas, puertas, regeneración y efectos de velocidad. En cada paso hay que sacar el de menor tiempo y, si empatan, el de menor secuencia.
Lo que más se hace es sacar el siguiente y volver a programar al actor. Cancelar pasa menos (muere un enemigo, antídoto, cambio de velocidad).

Alternativas:
Vector sin orden: programar es O(1), pero sacar el siguiente obliga a revisar todos.
Vector ordenado: sacar es O(1), pero programar es O(n) porque hay que correr elementos, y se programa casi en cada turno. Se descartó por eso.
Montículo mínimo: sacar y programar en O(log n). Es el que usamos.

Decisión: MonticuloMin sobre nuestro Vector, ordenado por (tiempo, secuencia). La secuencia la pone la Agenda al programar y siempre crece, así el orden es determinista. Para cancelar usamos borrado perezoso: se marca el evento y se descarta cuando sale. Cada actor guarda su próximo evento, así no hay que buscarlo. Un cambio de velocidad cancela el evento viejo y programa uno nuevo.

Complejidad:
Sacar el siguiente: O(log n).
Programar: O(log n).
Cancelar: O(1).
Cantidad de pendientes: O(1), con un contador.

Evidencia: Medimos las dos alternativas descartadas, hechas con nuestro Vector en bench_agenda.py.

Se mide con: (python -m crypta.bench.bench agenda)

Costo de UN turno (sacar el próximo evento y volver a programarlo)
  eventos pendientes   montículo (el juego)   vector ordenado   vector sin orden
  10                                 8.0 µs            4.6 µs             6.8 µs
  100                               11.3 µs           18.9 µs            48.3 µs
  1000                              15.8 µs          184.3 µs           451.9 µs
  5000                              17.1 µs          998.0 µs            2.30 ms
  Montículo: O(log n) por turno. Vector ordenado: O(n) al programar. Vector sin orden: O(n) al sacar.

Costo de cancelar UN evento (muere un enemigo, el antídoto cancela el veneno)
  eventos pendientes   montículo (el juego)   vector ordenado   vector sin orden
  10                                 0.7 µs            2.5 µs             2.2 µs
  100                                0.4 µs           12.1 µs             7.7 µs
  1000                               0.4 µs          142.9 µs            83.4 µs
  5000                               0.4 µs          771.3 µs           445.4 µs
  Montículo: O(1), solo se marca (borrado perezoso; sale cuando le toca). Vectores: O(n), hay que buscarlo y quitarlo.

Límites: Con muy pocos eventos el vector ordenado es más rápido (4,6 contra 8,0 µs con 10). En cripta-01 nunca hubo más de 4 pendientes, así que ahí habría bastado. Dejamos el montículo porque la cripta de la revisión puede ser mucho más grande.

4.2
Problema: Antes de entrar a una sala, su contenido tiene que estar en memoria. Cada solicitud tarda unos 400 ms, igual con 1 sala que con 10. Hay que pedir por adelantado, en lotes, las salas a las que el jugador probablemente va a ir. El programa hace dos cosas: después de cada comando busca salas cercanas sin cargar (precarga), y antes de cada movimiento se asegura de que la sala destino esté cargada.

Alternativas:
Pedir cada sala cuando el jugador entra: es lo más simple, pero se espera ~400 ms en cada puerta y se gasta una solicitud por sala. Se descartó porque el enunciado pide justamente evitar esa espera.
Pedir toda la cripta al inicio: en una cripta grande gasta presupuesto en salas que el jugador nunca visita. Se descartó por el presupuesto.
Precargar las salas más cercanas en lotes de 10: es la que usamos.

Decisión:
Usar una clase llamada GestorContenido.
Después de cada comando, precargar_async hace un BFS desde la sala del jugador (con una Cola y un ArbolBusqueda de visitadas). Junta hasta 10 salas que no estén cargadas ni pedidas y las pide en un solo lote, en otro hilo.
Las solicitudes pendientes se guardan en una Cola en el orden en que se hicieron. Las respuestas se incorporan siempre en ese orden, aunque alguna llegue antes. Así la red no cambia la partida.
Antes de mover, garantizar_sala: si la sala ya está, no hace nada; si viene en camino, espera esa respuesta (el reloj virtual no avanza); si no, la pide sola. Nunca se entra a una sala sin contenido.
Una sala cargada o ya pedida no se vuelve a pedir.
La precarga no se hace si quedan 2 solicitudes o menos del presupuesto. Esas se guardan para la sala a la que el jugador sí quiere entrar.
El BFS revisa como máximo 100 salas. Un contador de salas sin cargar permite no buscar nada cuando ya está todo cargado.

Complejidad.

Precarga: como máximo 100 salas revisadas, sin importar el tamaño de la cripta. O(1) si ya está todo cargado.
Garantizar una sala ya cargada: O(log n) para encontrarla en el mapa (ArbolBusqueda).
Red: hasta 10 salas por solicitud.

Evidencia:

Se mide con: python -m crypta.bench.bench red

Solicitudes para recorrer TODA la cripta (contenido + fichas)
  salas   ingenuo (1 por sala y por ficha)   el juego, caché vacía   el juego, caché caliente
  25                                    52                       8                          0
  100                                  130                      16                          0
  400                                  430                     196                          0

PRECARGA: buscar salas para pedir, en cada acción
  salas de la cripta   toda cargada   falta el 1 % (lejos)
  1000                       4.6 µs                1.18 ms
  5000                       2.8 µs                1.68 ms
  10000                      2.8 µs                1.22 ms
  Toda cargada: no busca nada, O(1).

Limites:
Por el tope de 100 salas revisadas, en una cripta grande ya casi cargada los lotes salen chicos: con 400 salas el juego hizo 196 solicitudes. Siguen siendo menos de la mitad que pedir todo por separado.
Con un presupuesto muy bajo la precarga se apaga, y cada sala nueva cuesta una solicitud con espera.

4.3
Problema: El contenido de una sala no trae las estadísticas de enemigos, objetos y trampas, solo su id de tipo (por ejemplo ent_rata_gigante). Antes de usarlos hay que conseguir la ficha de cada tipo. Los ids llegan en cualquier orden, se repiten entre salas y sirven para varias criptas. Cada vez que llega contenido, el programa junta los tipos que trae, quita los repetidos, revisa si ya los tiene y pide los que faltan.

Alternativas:
Pedir cada ficha cuando se necesita (GET /catalogo/id): una solicitud por tipo. En cripta-01 serían 11 solicitudes solo de catálogo, y el presupuesto de toda la partida es 9. Se descartó.
Pedir el catálogo completo al inicio: no se puede, porque el servicio no tiene esa consulta y no se sabe qué ids existen.
Juntar los ids nuevos y pedirlos en lotes de 10: es la que usamos.

Decisión:
RepositorioFichas.resolver_contenidos llama a GestorContenido cada vez que llega contenido:

Recorre los tipos del contenido. Un ArbolBusqueda de "vistos" evita revisar dos veces el mismo id.
Cada id se busca primero en memoria (CacheLRU), después en disco (guardado con la versión del catálogo) y solo si no está se anota para pedirlo.
Los que faltan van a una ListaSimple que funciona como cola y se piden de 10 en 10.
Si llega un enemigo que suelta objetos, esos ids entran a la misma cola y viajan en el próximo lote.
Todo lo que llega se guarda en memoria y en disco, así nunca se pide dos veces.

Complejidad:
Por cada referencia: O(log k) para saber si ya se vio y O(log c) para buscarla en la caché (k ids distintos, c fichas en memoria).

Evidencia. La tabla de red de la sección 4.2 (python -m crypta.bench.bench red) cuenta contenido y fichas juntos. Con 100 salas y 30 tipos distintos, el juego hace 16 solicitudes en total, contra 130 si se pide cada sala y cada tipo por separado. Con la caché caliente, 0. En cripta-01: 2 solicitudes de catálogo en lugar de 11.

Limites:
Si cambia la versión del catálogo, todas las fichas guardadas dejan de servir y hay que volver a pedirlas.
Los ids que suelta un enemigo solo se conocen después de recibir su ficha, así que pueden costar un lote más.

4.4
Problema:
La memoria le caben como máximo 25 fichas (--cache-size) cuando se llena hay que sacar una, pero nunca una que esté en uso: algo del inventario, del suelo o una trampa de la sala actual, o un enemigo vivo y despierto. Lo que más se hace es preguntar si una ficha ya está en memoria.

Alternativas:
Buscar recorriendo una lista de fichas: O(n) en cada búsqueda. Se descartó porque es la operación más frecuente. La medimos (ver evidencia).
Para elegir cuál sale, FIFO (la que entró primero): saca fichas que se siguen usando todo el tiempo solo porque llegaron temprano. Se descartó.

Decisión:
 CacheLRU.
Un ArbolBusqueda de id → entrada, para buscar.
Una ListaDoble con las fichas que se pueden sacar, de la menos usada a la más reciente. Cada vez que se usa una ficha, su nodo pasa al final; cuando hay que sacar una, sale la del frente.
FichasEnUso revisa después de cada comando qué fichas están en uso y las marca. Una ficha marcada sale de la lista, así que no se puede sacar. Cuando deja de usarse, vuelve a la lista como la más reciente.

Se escogió LRU porque lo que se usó hace poco es de la sala actual o de las cercanas, que es lo que más probablemente se vuelve a necesitar. Lo que lleva tiempo sin usarse es de salas que ya quedaron atrás.

Complejidad:
Si está en memoria -> O(log c) en promedio
Usar una ficha, sacar la menos reciente, marcar y liberar: O(1) en la lista (más el O(log c) de encontrarla).

Evidencia:
usar: (python -m crypta.bench.bench cache).

Una búsqueda (la mitad encuentra la ficha y la otra mitad no):
fichas en caché   árbol de búsqueda (el juego)   recorrer la lista
  25                                      0.6 µs              4.0 µs
  250                                     1.0 µs             37.9 µs
  2500                                    1.6 µs            413.6 µs

Limites:
El ArbolBusqueda no se balancea. Si los ids llegaran ordenados, se volvería una lista y buscar sería O(n). Llegan en el orden en que se descubren, y con 25 fichas la diferencia es mínima.
Leer una ficha del disco carga el catalogo.json completo cada vez. Con un catálogo de miles de fichas, cada fallo costaría bastante más que los 646 µs medidos.
Para saber qué enemigos están despiertos, FichasEnUso recorre los eventos pendientes después de cada comando. Eso crece con la cantidad de eventos.

4.5
Problema: El jugador recorre el inventario hacia adelante y hacia atrás desde el objeto que está viendo, y puede soltar ese objeto esté donde esté. Equipar mueve el objeto al frente. Se pueden pedir vistas ordenadas por peso, valor o nombre sin cambiar el orden real. Con el inventario lleno no se puede recoger.

Alternativas:
Vector: soltar el objeto de la posición i corre todos los que están después, O(n). Equipar (mover al frente) corre a todos los de adelante. Se descartó porque el enunciado pide que soltar no dependa de la posición.
ListaSimple: no tiene puntero al anterior, así que retroceder y soltar obligan a recorrer desde el inicio para encontrar el nodo de atrás. Se descartó.

Decisión:
Inventario guarda los objetos en una ListaDoble y un puntero _actual al nodo que se ve.

Avanzar y retroceder solo mueven el puntero.
Soltar quita ese nodo de la lista. El puntero pasa al siguiente o, si no hay, al anterior.
Equipar mueve el nodo al frente (mover_al_frente). El arma y la armadura equipadas son referencias a sus nodos, así que no hay que buscarlas.

Complejidad:
Avanzar, retroceder, soltar, equipar, recoger: O(1).
Vista ordenada: O(n) para copiar más el ordenamiento (O(n log n) con mergesort, O(n) con inserción si ya casi está ordenado).
Recorrer todo: O(n).

Evidencia:
Comparado con la alternativa del vector:
objetos   lista doble: el 1.º   lista doble: el último   vector: el 1.º   vector: el último
  10                     1.9 µs                   1.6 µs           2.7 µs              0.9 µs
  100                    1.6 µs                   1.5 µs          20.3 µs              0.9 µs
  1000                   1.5 µs                   1.5 µs         223.8 µs              1.0 µs
  La lista cuesta lo mismo en cualquier posición. El vector depende de la posición: el último es barato, pero el primero crece con n.

Límites.

Con un inventario de 10 objetos, como en cripta-01, el Vector habría funcionado casi igual (2,7 contra 1,9 µs), y soltar el último es incluso más rápido con el vector. La lista doble solo hace diferencia con inventarios grandes.
No se puede saltar directo a la posición k: hay que avanzar uno por uno.

4.6
Problema: Un pergamino deshace la última acción del jugador y todo lo que pasó después hasta su siguiente decisión: ataques de enemigos, veneno, trampas, reloj, eventos, rastro, inventario, puertas. Se pueden deshacer como máximo 5 acciones. No se permite guardar copias completas del estado. La cantidad de pergaminos y la caché quedan fuera del retroceso. Lo que más se hace no es deshacer, es anotar: cada cambio que pasa en el juego se anota, aunque nunca se use un pergamino.

Alternativas:
Copia completa de la partida antes de cada acción (deepcopy): el enunciado la prohíbe. Además cuesta en cada acción aunque nunca se use un pergamino. La medimos para ver cuánto costaría (ver evidencia).
Guardar los comandos y volver a jugar desde el inicio hasta la acción anterior: no guarda copias, pero deshacer costaría tanto como toda la partida. Se descartó.

Decisión:
Cada Cambio es una de dos cosas: (objeto, atributo, valor anterior), por ejemplo la vida de una rata antes del golpe; o (objeto, operación que lo devuelve, dato), por ejemplo agenda.restaurar_evento(evento) o volver a meter un nodo del inventario.
Al empezar una acción del jugador se abre un RegistroAccion. Todo cambio hasta la próxima decisión, sea del jugador, de los enemigos o de los efectos, se anota en esa acción abierta.
Los cambios de una acción van en una ListaDoble. Para deshacer se recorre del último al primero, porque hay que deshacerlos en orden inverso.
El Historial es una ListaDoble de acciones. Al pasar de 5 se quita la del frente, que es la más vieja. Una Pila no sirve aquí, porque la más vieja queda al fondo.

Complejidad:
Anotar un cambio: O(1).
Abrir una acción y botar la más vieja: O(1).
Deshacer: O(k) con k cambios de esa acción. Si hay que volver a meter eventos a la agenda, cada uno es O(log n).

Evidencia:
(python -m crypta.bench.bench inventario).

Medimos la alternativa descartada. Una partida con N enemigos activos: usar un pergamino contra sacar una copia completa con deepcopy (solo sacarla, sin restaurarla).
enemigos activos   anotar los cambios (el juego)   foto completa (deepcopy, solo sacarla)
  10                                       68.2 µs                                 17.41 ms
  100                                     574.0 µs                                 27.71 ms
  300                                      1.95 ms                                 57.26 ms

Límites:
Con muchos enemigos activosuna sola acción anota cientos de cambios y 5 acciones guardadas pueden ocupar bastante memoria.
Cada cambio nuevo que se agregue al juego hay que anotarlo a mano. Si se olvida uno, el pergamino deja ese dato mal. Lo controlamos con pruebas que juegan partidas al azar, usan el pergamino y comparan todo el estado.
El número de secuencia de la agenda no vuelve atrás. Después de deshacer, los eventos nuevos reciben números más altos. El orden entre eventos no cambia, porque solo importa cuál es menor.

4.7

Problema: Cada sala guarda cuándo estuvo el jugador allí por última vez. En su turno, un rastreador mira solo las salas vecinas por salidas abiertas y va a la de rastro más fresco.
La decisión no puede depender del tamaño de la cripta ni de lo largo del recorrido. Hay que decidir si los rastros viejos se borran o se detectan al consultarlos.

Alternativas:
Que el rastreador busque un camino hasta el jugador (BFS)
Borrar activamente los rastros viejos con un evento a los 400: agrega un evento por cada acción del jugador, más trabajo para la agenda y más cambios que anotar para el pergamino. Se descartó.
Un número por sala y revisar la antigüedad al consultar: es la que usamos.

Decisión:
Cada Sala tiene ultimo_rastro, un solo número. Al terminar cada acción del jugador, la sala donde quedó recibe el reloj actual. El cambio se anota en el historial, así que el pergamino también lo deshace.
sala_con_rastro_mas_fresco recorre las puertas abiertas de la sala en orden N, S, E, O. Cada puerta apunta directo a su sala vecina, sin buscarla en el mapa. Ignora rastros vacíos o de 400 o más, y se queda con el más fresco o, si empatan, con el de menor id.
La caducidad se detecta al consultar con una resta (reloj - rastro >= 400). Nada se borra.

Complejidad:
Decisión de un rastreador: O(salidas de la sala), a lo sumo 4. No depende de la cripta ni del recorrido.
Refrescar el rastro: O(1).

Evidencia (python -m crypta.bench.bench rastro y ciclo). Medimos la alternativa descartada (HuellasEnLista en bench_rastro.py), con un rastreador lejos del jugador:
 salas de la cripta   pasos del jugador   rastro en cada sala (el juego)   lista de huellas
  100                                 10                           1.5 µs             3.9 µs
  100                               1000                           1.5 µs           199.1 µs
  2500                                10                           1.5 µs             3.8 µs
  2500                             10000                           1.5 µs            1.93 ms

Ciclo completo entre dos decisiones (§5.2), con N enemigos activos a la vez:

 enemigos activos   eventos por acción   modelo: media   ciclo completo: media        p95     máximo   por evento   ¿cumple?
  50                                 64         2.16 ms                 3.51 ms    4.48 ms    4.58 ms        54 µs         sí
  100                               127         4.25 ms                 5.64 ms    7.26 ms    7.63 ms        44 µs         sí
  200                               254         9.27 ms                10.82 ms   13.84 ms   14.45 ms        43 µs         sí
  300                               379        14.36 ms                16.99 ms   23.60 ms   24.52 ms        45 µs         NO
  500                               632        28.11 ms                29.94 ms   42.17 ms   44.19 ms        47 µs         NO

Límites.

En nuestra máquina, el ciclo entre dos decisiones cumple los 20 ms del §5.2 hasta unos 200 enemigos activos a la vez. Con 300 ya no. El rastro no es la causa (cuesta lo mismo con cualquier recorrido). Lo que pesa es el trabajo de cada evento: combate, anotar cambios para el pergamino y mensajes.
Solo se guarda la última visita a cada sala. El rastreador no puede seguir un camino viejo

4.8
Problema: La pantalla muestra solo los últimos 20 mensajes del juego. La memoria tiene que quedar constante toda la partida, y agregar un mensaje no puede mover los 19 anteriores.

Alternativas:
Vector con tope de 20: al llenarse hay que quitar el primero, y eso corre los otros 19. Es justo lo que el enunciado no permite. La medimos (ver evidencia).
Lista sin tope, mostrando los últimos 20: no mueve nada, pero la memoria crece toda la partida. Se descartó.

Decisión: Bitacora usa una Cola(capacidad_max=20) hecha sobre nuestra ListaSimple. Al encolar con la cola llena, primero se quita el del frente (el más viejo) y después se agrega el nuevo al final. Las dos cosas son O(1), porque la lista tiene puntero al primero y al último.

Complejidad:
Agregar un mensaje: O(1), sin mover a nadie.
Quitar un mensaje: O(1)

Evidencia: (python -m crypta.bench.bench red). Medimos la alternativa descartada (BitacoraVector en bench_red.py): agregar un mensaje con la bitácora llena. El bench también revisa que la cola nunca pase del tope.
mensajes guardados   cola con tope (el juego)   vector (corre a todos)
  20                                     1.5 µs                   3.4 µs
  1000                                   1.9 µs                 125.0 µs

Límites:

NOTA: Con 20 mensajes la diferencia casi no se nota
No obstante si la bitacora creciera o se tuviera que cambiar por una bitacora de 1000 mensajes la diferencia se empieza a notar...

4.9 

Problema: Se deben ordenar varias vainas (tabla de puntajes, vistas del inventario, índices del archivo de 
guardado y listas auxiliares del catálogo.)
Hay que tener dos algoritmos y que el programa escoja solo según los datos.

Alternativas:
Siempre mergesort: con datos casi ordenados pierde mucho (1000 elementos: 9,37 ms contra 0,71 ms de inserción).
Siempre inserción: con datos desordenados es O(n²) (1000 aleatorios: 174 ms contra 13 ms).
Elegir solo por tamaño: manda a mergesort listas grandes casi ordenadas, que es justo el caso del mapa y del índice.
Quicksort o heapsort: no son estables, y la tabla de puntajes necesita que los empates queden en el orden en que se registraron.

Decisión:
Si hay 24 elementos o menos (16 si comparar es costoso, por ejemplo ordenar por nombre), usa inserción.
Si no, revisa si está casi ordenado: como máximo un 5 % de descensos, y ninguno que obligue a mover un elemento más de 8 lugares hacia atrás. Si es así, usa inserción.
Si no, usa mergesort.
Los dos algoritmos son estables y trabajan sobre nuestro Vector, sin sort() ni sorted().

Complejidad:
Inserción: O(n) si está casi ordenado, O(n²) en el peor caso.
Mergesort: O(n log n) siempre, con O(n) de memoria extra.

Evidencia:
Al ejecutar (python -m crypta.bench.bench ordenamiento). Medimos los dos algoritmos en cada caso y lo que eligió ordenar().

ORDENAMIENTO (§4.9): números (comparar es barato). Umbral: hasta 11 elementos, inserción
  datos              n   inserción   mergesort   ordenar() elige   ¿bien?
  aleatorio          8     19.0 µs     39.6 µs         insercion       sí
  aleatorio         24    120.4 µs    123.3 µs         insercion       sí
  aleatorio         50    403.1 µs    302.2 µs         mergesort       sí
  aleatorio        200     5.91 ms     1.72 ms         mergesort       sí
  aleatorio       1000   173.66 ms    13.37 ms         mergesort       sí
  casi ordenado      8      9.6 µs     28.4 µs         insercion       sí
  casi ordenado     24     26.3 µs    114.6 µs         insercion       sí
  casi ordenado     50     33.5 µs    295.9 µs         insercion       sí
  casi ordenado    200    134.3 µs     1.47 ms         insercion       sí
  casi ordenado   1000    713.5 µs     9.37 ms         insercion       sí
  invertido          8     20.4 µs     28.6 µs         insercion       sí

Límites:
Que la comparación sea costosa lo dice quien llama a ordenar; el programa no lo mide.
La revisión de "casi ordenado" es conservadora: un solo elemento muy atrasado manda todo a mergesort, aunque inserción también habría sido rápida.
Mergesort necesita memoria extra del tamaño de los datos.

4.10

Problema:
La partida se guarda en un archivo binario de formato propio.
Se tiene que poder leer una sala sin leer todo el archivo, y detectar si el archivo es de otra versión del formato.
Además hay que compararlo con guardar lo mismo en JSON.
Guardar y cargar solo pasan cuando el jugador lo pide (comandos guardar y cargar), así que son poco frecuentes, pero con una cripta grande el archivo crece con las salas.

Alternativas:
JSON: es fácil, pero ocupa unas 3 veces más y para leer una sala hay que leer el archivo entero. Lo medimos (ver evidencia).
Binario sin índice (salas una detrás de otra): para encontrar una sala hay que recorrer las anteriores. Se descartó.

Decisión: 
Adaptadores/GuardadoBinario.py, con struct:
Inicio fijo de 6 bytes: CRPT y la versión del formato. Si no coincide, el archivo se rechaza con un error claro.
Una cabecera, el encabezado (cripta, versiones, semilla, jugador), los datos generales, un registro por sala y, al final, un índice con (id de sala, posición, largo), 20 bytes por sala.
Al guardar, el índice se ordena por id con ordenar (ya viene casi ordenado, así que usa inserción). Se escribe a un .tmp y después se reemplaza el archivo, para no dejar uno a medias.
Al abrir (ArchivoGuardado) se leen solo el inicio, la cabecera, el encabezado y el índice, y con el índice se arma un ArbolBusqueda balanceado (desde_ordenados). leer_sala(id) busca en el árbol, salta a esa posición y lee solo ese registro.

Complejidad.

Guardar: O(tamaño de la partida). Ordenar el índice es O(n) porque ya viene casi ordenado.
Abrir: O(n salas) para leer el índice y armar el árbol.
Leer una sala: O(log n) en el árbol, más leer solo su registro.
Evidencia: 
Al ejecutar (python -m crypta.bench.bench guardado).
La misma partida en los dos formatos (binario / JSON):

  salas                tamaño             cargar todo          leer UNA sala   bytes leídos para UNA sala
  100       29.2 KB / 83.4 KB     25.18 ms / 23.66 ms      8.03 ms / 3.09 ms             2.4 KB / 83.4 KB
  1000    247.1 KB / 770.8 KB   188.37 ms / 179.76 ms     3.19 ms / 90.47 ms           20.0 KB / 770.8 KB
  5000      1.21 MB / 3.80 MB      938.04 ms / 1.20 s   15.35 ms / 162.45 ms            98.1 KB / 3.80 MB
  El binario tiene un índice al final: para una sala lee solo el índice y ese registro. El JSON hay que leerlo entero.

Límites:
Cargar todo cuesta casi lo mismo en los dos formatos, y con 100 y 1000 salas el JSON salió un poco más rápido. La mayor parte del tiempo se va en armar los objetos de la partida, que es igual para los dos.
Con 100 salas, leer una sala salió más lenta en binario (8 ms contra 3 ms), aunque leyó 35 veces menos bytes, y con 1000 salas tardó solo 3 ms. Lo tomamos como ruido: esa sección promedia 5 repeticiones en vez de tomar la mejor, y es la primera que se mide.
Abrir el archivo obliga a leer el índice completo (20 bytes por sala). En una cripta enorme, el índice crece.
En el juego, cargar lee todo, porque hace falta todo para seguir jugando. Leer una sola sala lo usan el bench y las pruebas.
Después de cargar, el historial de deshacer está vacío: los pergaminos sirven desde la siguiente acción.

4.11
Problema: Cada acción del jugador se anota en un archivo de texto al que solo se le agrega al final. El encabezado lleva la cripta, sus versiones y la semilla. Con --replay partida.log la partida se repite sola, sin el usuario. Si la versión del log ya no está disponible, el programa tiene que avisar que no puede garantizar una reproducción fiel en vez de seguir con otros datos.

Alternativas:
Guardar el estado después de cada acción: ocupa muchísimo y no sirve para repetir la partida paso a paso. Se descartó.
Reescribir el archivo entero en cada acción (por ejemplo, una lista en JSON): cada acción costaría más mientras más larga la partida, y si el programa se cae a medio escribir se puede perder todo. Se descartó.

Decisión:
RegistroPartida: crear escribe el encabezado (marca, formato 1, cripta, versión de cripta, versión de catálogo, semilla, jugador y ---). Después, anotar abre en modo "a" y agrega una línea.
Solo se anota un comando si se ejecutó sin error. Se anota en forma fija: atacar e-201 (id de instancia, no el número en pantalla) y recoger 0 (posición desde 0).
leer_registro revisa el encabezado y devuelve los comandos en una Cola, porque se ejecutan en el mismo orden en que se anotaron.
Reproductor:
antes de jugar nada, revisa que estén la versión de la cripta y del catálogo; si no, lanza ReproduccionIncompatible con el mensaje de que no se puede garantizar una reproducción fiel;
después ejecuta cada comando con el mismo ejecutar_comando del juego normal;
si un comando falla, o sobran comandos después del final, lanza ReproduccionFallida con el número de comando.
PreparadorReplay decide de dónde salen los datos. Usa la fuente normal solo si sirve exactamente las versiones del log. Si no, usa la copia local en disco, sin red. Si ninguna sirve, ReproduccionIncompatible. Nunca reproduce contra datos de otra versión.
Para que la partida salga igual: el azar es random.Random(semilla) propio, las respuestas de red se incorporan en orden de solicitud (§4.2) y los enemigos de una sala quedan en el mismo orden sin importar cuándo llegó el contenido.
Al guardar, el log se copia junto al archivo de guardado, y al cargar se restaura. Si no, un log con comandos de antes y después de cargar daría otra partida.

Complejidad:
Anotar un comando: O(1), una línea al final del archivo.
Leer el log: O(líneas), y cada comando sale de la Cola en O(1).

Límites:
Si el servidor ya publicó otra versión y se borró la copia local (cache/), el replay avisa y no se puede repetir la partida.
Reproducir una partida muy larga cuesta tanto como jugarla otra vez. No se puede saltar a la mitad.
partida.log es el de la última partida: una partida nueva lo reemplaza. Para conservar uno, hay que copiarlo o usar guardar.

5.1 La ruta más barata del cazador

**Problema:**
- En su turno, el cazador ataca si comparte sala con el jugador; si no, da un paso por una ruta de costo mínimo hasta él, o espera si no hay ruta o si cuesta más que su rango.
- Los costos de las salidas son enteros ≥ 1 y pueden ser distintos entre sí: la ruta con menos salas no siempre es la más barata.
- Si hay empate, va a la vecina de menor id. La decisión no puede usar el azar.
- Puede haber 50 cazadores o más persiguiendo al mismo jugador en criptas de 2000 a 20000 salas.

**Alternativas:**
- Recorrido por anchura (Cola): solo sirve con costos iguales; da la ruta con menos salas. Se descartó.
- Una búsqueda por cazador desde su sala (RutaPorCazador, Dijkstra con etiqueta (distancia, primer paso)): correcta, pero una búsqueda por cazador en cada turno. La medimos (B4).
- Todas las parejas (Floyd-Warshall): O(V³) de tiempo, O(V²) de memoria y queda inválida con cada puerta. Se descartó.
- A*: no hay heurística, porque las salas no tienen coordenadas. Se descartó.
- Guardar las distancias en un ArbolBusqueda en vez de vectores: la medimos (B9).
- heapq, networkx, dict y set: prohibidos (§6.2).

**Decisión:**
- Una sola búsqueda por partida, compartida por todos los cazadores (Perseguidor), desde la sala del jugador.
- Recorre las entradas de cada sala (las salidas y→x), no las salidas: así da dist(x, jugador) aunque haya salidas sin vuelta. Las entradas se arman una vez al cargar el mapa.
- Dijkstra perezoso y reanudable (estructuras/DistanciasLimitadas.py) sobre nuestro MonticuloMin, con inserción perezosa. Solo se extiende hasta lo que necesita el cazador que decide: min(rango, distancia de su sala).
- Cada sala tiene un índice 0..V−1 en orden de id. Las distancias van en 3 Vector de V enteros con una marca de cálculo: empezar de nuevo es sumar 1 a la marca, sin limpiar nada.
- El cazador mira solo las salidas abiertas de su sala: entre las vecinas v con costo(u, v) + dist(v) = d, la de menor id.
- Coincide con lo planeado (specs/001-terreno-cazador/plan.md, research D1, D2, D3 y D5); las mediciones lo confirmaron y no hubo cambios. Requisitos: specs/001-terreno-cazador/spec.md, FR-014 a FR-018.

**Complejidad:**
- Empezar una búsqueda: O(1).
- Extenderla: O((ΔV + ΔE) log E) por lo que se asienta de nuevo; E ≤ 4V.
- Decisión de un cazador con la búsqueda ya extendida: O(1) (a lo sumo 4 salidas).
- Ciclo con H cazadores: O(H) más lo que haya que extender, una sola vez para todos.
- Memoria: 3 Vector de V enteros y el montículo. Índices y entradas: O(V + E), una vez al cargar.

**Evidencia:**
Se mide con: python -m crypta.bench.bench cazadores rangos tamano compartido escala distancias
Criptas sintéticas deterministas por semilla (docs/resultados_bench_p2.txt).

Búsqueda compartida frente a una por cazador (B4), tiempo por ciclo, 2000 salas
  cazadores   puertas      compartida   por cazador
  1           estables       188.9 µs      172.5 µs
  10          estables       11.36 ms      56.49 ms
  50          estables       14.64 ms     292.84 ms
  50          inestables    116.34 ms     323.83 ms

Límites del enunciado
  medición                                        resultado                    límite   ¿cumple?
  B3: misma región, 2000 frente a 20000 salas     1.62 ms y 1.62 ms (1.00)     < 2      sí
  B8: tiempo por cazador, 100 frente a 10         63.5 µs y 71.4 µs (0.89)     ≤ 2      sí

- B3: con rango pequeño (~100 salas) se asientan 101 salas en las dos criptas. El costo depende de la región, no del tamaño de la cripta.
- B2: rango pequeño 119.7 µs y 7 salas por decisión; rango grande 2.15 ms y 124 salas.
- B9: vectores con marca frente a ArbolBusqueda: 1.72 contra 2.51 ms con rango pequeño, 17.22 contra 39.78 ms con media cripta.

**Límites:**
- Con un solo cazador gana la búsqueda por cazador, por poco (172.5 contra 188.9 µs): no hay con quién compartir.
- Con rango grande cada decisión cuesta lo que haya que explorar (B2: 2.15 ms contra 120 µs).
- Los 3 vectores ocupan memoria proporcional a toda la cripta aunque el rango sea pequeño. Se reservan con el primer turno de un cazador.
- La cripta oficial no se publicó; todo se midió con criptas sintéticas.

5.2 Rutas que dejan de ser válidas

**Problema:**
- Entre dos turnos de un cazador se abren y cierran puertas, el jugador se mueve, se usa un pergamino o se carga una partida.
- La decisión tiene que ser siempre la misma que la de un cálculo desde cero en ese instante (FR-019), pero recalcular en cada turno es caro.
- Hay que saber cuándo la búsqueda guardada sigue sirviendo.

**Alternativas:**
- Recalcular siempre en cada turno de cazador: simple y seguro, pero no reutiliza nada.
- Invalidación total: reutilizar la búsqueda y descartarla ante cualquier cambio de puerta.
- Invalidación selectiva: descartarla solo si la puerta toca una sala ya asentada.
- Actualizar las distancias en cada cambio (algoritmos dinámicos): mucho código y difícil de demostrar equivalente. Se descartó.
Las tres primeras están en Perseguidor (modos RECALCULAR, TOTAL y SELECTIVA) para medirlas.

**Decisión:**
- Invalidación selectiva.
- Las distancias dependen solo de la sala del jugador y de qué puertas están abiertas (los costos no cambian). Que los enemigos se muevan, mueran o cambien de velocidad no las afecta.
- La sala del jugador se compara en cada decisión: cubre moverse, el pergamino y la carga.
- Cada puerta conoce sus dos salas y avisa a la búsqueda solo cuando cambia de abierta a cerrada o al revés. La búsqueda se descarta si alguna de las dos salas ya está asentada.
- Si ninguna lo está, la búsqueda sigue valiendo: esa puerta nunca se usó al relajar, y una ruta nueva por ella cuesta más que todo lo asentado (demostración en research D4).
- El pergamino descarta la búsqueda igual, por seguridad. Una partida cargada crea su propia búsqueda.
- Las búsquedas no son estado del juego: no se guardan ni entran al historial del pergamino.
- Coincide con lo planeado (specs/001-terreno-cazador/plan.md, research D4 y D6): la selectiva ahorró frente a la total (B5), así que se queda. Requisitos: specs/001-terreno-cazador/spec.md, FR-019, FR-020, FR-032 y FR-033.

**Complejidad:**
- Aviso de una puerta: O(1) (mirar si alguna de sus dos salas está asentada).
- Comparar la sala del jugador: O(1).
- Descartar la búsqueda: O(1) (se suma 1 a la marca).

**Evidencia:**
Se mide con: python -m crypta.bench.bench reutilizar equivalencia ciclo_cazadores

Reutilizar frente a recalcular (B5), 2000 salas y 50 cazadores
  puertas         variante             por ciclo   búsquedas   salas asentadas
  casi estables   recalcular siempre   189.50 ms         750            177740
  casi estables   invalidación total    19.98 ms          30             17329
  casi estables   selectiva             16.96 ms          24             14565
  inestables      recalcular siempre   249.44 ms         750            230250
  inestables      invalidación total   257.75 ms         750            230250
  inestables      selectiva            114.81 ms         180            103714

- B6: 8160 decisiones de B4 y B5 comparadas con un cálculo desde cero, 0 diferencias. Si hubiera alguna, el --bench imprime ERROR y termina con código 1.
- Las pruebas comparan cada turno de cazador con un cálculo desde cero en una partida de más de 1000 turnos, con puertas que cambian, muertes y cambios de velocidad: 100 % iguales (tests/test_equivalencia_cazador.py).
- B7 (ciclo con 50 cazadores, 2000 salas, 60 acciones): media 3.04 ms, p95 7.60 ms, máximo 12.03 ms. Límite: p95 < 20 ms. Cumple.

**Límites:**
- B4 y B5 con puertas inestables pasan de 20 ms por ciclo (114.81 ms en B5 con la selectiva), pero ahí cambia una puerta antes de cada decisión: 50 cambios por acción del jugador. El juego no produce eso, porque las puertas solo cambian al abrirlas o por cierre automático.
- B7 mide el modelo (la acción del jugador y los eventos hasta su siguiente decisión), no el Controlador (vista, registro y precarga).
- Con puertas inestables la invalidación total no ahorra nada frente a recalcular siempre (750 búsquedas en las dos).
- La selectiva descarta la búsqueda aunque el cambio no altere la decisión de ningún cazador: basta con que la puerta toque una sala asentada.

5.3 El mapa conocido

**Problema:**
- El jugador solo conoce lo que exploró. Cada sala está explorada, avistada (es destino de una salida de una sala explorada) o desconocida, y cada puerta se recuerda abierta o cerrada como se vio la última vez (FR-201 a FR-206).
- Consultar el estado de una sala y el recordado de una puerta pasa en cada vista, en cada paso de «ir a» y en cada actualización por antorcha (P2 §5.3). Tiene que ser O(1) y no crecer con lo conocido (FR-235).
- Explorar tiene que costar lo que se revela, no el tamaño de lo conocido. El pergamino lo revierte y la línea de tiempo lo reconstruye, así que registrar y deshacer cada cambio tiene que ser barato (FR-236; principio VII: nada de copias por acción).
- «ir a <sala>» viaja por la ruta conocida más barata, paso a paso; si el conocimiento cambia en el camino, el paso siguiente tiene que ser el de un cálculo desde cero (FR-217, FR-218). Límite: p95 del paso < 5 ms (FR-234).
- Hay que justificar si la ruta de «ir a» comparte implementación con la del cazador (P2 §5.3).

**Alternativas:**
- Estado de las salas y de las puertas en un ArbolBusqueda por id y por (sala, dirección), armado con desde_ordenados (insertar en orden lo degeneraría): O(log n) por consulta, y cada observación hay que escribirla por los dos lados de la puerta. La medimos (N1).
- Guardar el estado en la propia Sala: también O(1), pero mezcla el conocimiento con el esqueleto. Se descartó.
- Copiar el mapa conocido antes de cada acción para revertir: lo prohíbe el principio VII. La medimos solo para mostrar que crece (N2).
- Ruta de «ir a» recalculada desde cero en cada paso, o con RutaPorCazador hacia adelante (la sala actual cambia en cada paso, así que no se puede reutilizar nada). La medimos (N3, «recalcular siempre»).
- Invalidación total: reutilizar la búsqueda y descartarla ante cualquier cambio del conocimiento. La medimos (N3 b).
- dict, set, heapq y collections: prohibidos (§6.2).

**Decisión:**
- MapaConocido (Modelo/MapaConocido.py) guarda un Vector de V enteros por el índice denso de la 001 (0 desconocida, 1 avistada, 2 explorada) y dos contadores (research D1). Toda consulta llega con un objeto Sala, así que el índice está a mano.
- El recordado de cada puerta va en su EstadoPuerta, que comparten los dos lados de la salida: observar desde un lado actualiza los dos sin trabajo extra (D2).
- Todo cambio pasa por MapaConocido y anota un Cambio solo si el valor cambia, con el valor anterior. Se anota con partida._anotar, que busca el historial vigente en cada llamada. El pergamino lo deshace con el mismo historial de P1 y la línea de tiempo de la 004 lo reconstruye sin cambios (D3).
- RutaConocida (Modelo/RutaConocida.py) busca **desde el destino** con DistanciasLimitadas, por las entradas conocidas: salas exploradas y puertas recordadas abiertas. Como el destino no cambia entre pasos, lo asentado sigue valiendo y el paso siguiente cuesta O(grado) sin buscar. Desempate: menor id de la vecina y, a la misma vecina, N, S, E, O, igual que el cazador (D5).
- Invalidación selectiva: MapaConocido avisa a la ruta cuando cambia un recordado o una sala pasa a explorada (o deja de estarlo al deshacer). La búsqueda se descarta solo si el cambio toca una sala asentada; la demostración es la de la 001 (research D4 de la 001) sobre el grafo conocido (D6). El pergamino la descarta siempre.
- ¿Comparte implementación con el cazador? (P2 §5.3): sí la estructura, no las reglas ni la instancia.
  - La misma DistanciasLimitadas de la 001 (Dijkstra perezoso y reanudable, con vectores con marca): es genérica sobre índices y una función de entradas. Reutilizarla trae su código ya medido (B9) y probado (B6), y deja una sola implementación de Dijkstra en el proyecto.
  - Reglas separadas: el cazador lee el estado real de las puertas y busca desde la sala del jugador; «ir a» lee el mapa conocido y busca desde el destino. Mezclarlas obligaría a pasarle al cazador lo que el jugador no sabe.
  - Instancias separadas: la del cazador se reinicia cada vez que el jugador se mueve (su origen es la sala del jugador). Compartida, destruiría la búsqueda de «ir a» en cada paso del viaje, que es justo lo que se quiere reutilizar.
- La ruta, su búsqueda y el viaje no son estado del juego: no se guardan, no se revierten y no van a los puntos de control (D7).
- Coincide con lo planeado (specs/002-niebla-ir-a/plan.md, research D1 a D14); las mediciones lo confirmaron y no hubo cambios. La optimización condicional de D12 (T050a) no hizo falta, porque el p95 de N3 cumplió en (a) y en (c). Requisitos: specs/002-niebla-ir-a/spec.md, FR-201 a FR-236.

**Complejidad:**
- Consultar el estado de una sala o el recordado de una puerta: O(1).
- Explorar una sala (con antorcha, a lo sumo 5 salas con 4 salidas): O(1) cambios, sin importar cuánto se conoce. Deshacer: O(cambios anotados).
- Paso de «ir a» con la búsqueda vigente: O(grado de la sala), a lo sumo 4. Con búsqueda nueva: O((ΔV + ΔE) log E) por lo que se asienta.
- Aviso de un cambio a la ruta: O(1) para una puerta; O(grado) para una sala.
- Memoria: un Vector de V enteros y un campo por puerta; la ruta, 3 Vector de V enteros (los de DistanciasLimitadas).

**Evidencia:**
Se mide con: python -m crypta.bench.bench niebla_n1 niebla_n2 niebla_n3 niebla_n4
Criptas sintéticas deterministas por semilla de la 001 (2000 y 20000 salas) y el esqueleto de la copia local más grande, cripta-06 (300 salas) (docs/resultados_bench_002.txt).

Consultas al mapa conocido (N1), 2000 salas, 100000 consultas de cada tipo
  estructura              exploradas   estado: media   recordada: media
  Vector + EstadoPuerta          200          0.5 µs             0.3 µs
  ArbolBusqueda                  200          1.0 µs             1.7 µs
  Vector + EstadoPuerta         2000          0.5 µs             0.3 µs
  ArbolBusqueda                 2000          1.3 µs             2.3 µs

- N1: cociente 2000 / 200 de la elegida 1.12 (límite ≤ 2); el árbol, 1.33. El árbol también cumple el cociente, porque crece como log n, pero cada consulta cuesta de 2 a casi 8 veces más y obliga a escribir los dos lados de cada puerta.

Exploración con antorcha y su reversión (N2), 20000 salas, 1000 entradas a más de 2 pasos de lo conocido
  conocidas   explorar   deshacer   copia por acción: explorar   copia por acción: deshacer   cambios por entrada
  200         155.7 µs    38.6 µs                      1.72 ms                     571.3 µs                  28.6
  2000        186.1 µs    35.5 µs                     15.46 ms                      4.50 ms                  28.6

- N2: cociente 2000 / 200 de la elegida 1.19 al explorar y 0.92 al deshacer (límite ≤ 2): no crecen con lo conocido. La copia por acción crece 8.99 veces al explorar y 7.87 al deshacer, y está prohibida por el principio VII.

Paso de «ir a» (N3): todos los pasos y el primero de cada viaje
  caso                                    variante              pasos      media        p95     máximo   primer paso: p95   buscaron   invalidaciones
  (a) 2000 salas, completo                selectiva               601   515.0 µs    14.6 µs   39.58 ms           35.08 ms      3.2 %                0
  (a) 2000 salas, completo                recalcular siempre      601    8.44 ms   29.91 ms   48.52 ms           35.17 ms    100.0 %                0
  (b) 2000 salas, desactualizado          selectiva               603   552.4 µs    16.6 µs   42.74 ms           35.86 ms      3.6 %                3
  (b) 2000 salas, desactualizado          invalidación total      603   529.3 µs    17.5 µs   42.78 ms           34.86 ms      3.6 %                3
  (b) 2000 salas, desactualizado          recalcular siempre      603    8.30 ms   27.37 ms   63.23 ms           34.24 ms    100.0 %                3
  (c) cripta-06 (300 salas), completo     selectiva               207    53.8 µs   475.2 µs   902.1 µs          863.4 µs      9.2 %                0
  (c) cripta-06 (300 salas), completo     recalcular siempre      207   287.7 µs   715.1 µs   900.6 µs          890.6 µs    100.0 %                0

- (a): con la selectiva solo el 3.2 % de los pasos busca (19 búsquedas en 601 pasos, 30.1 pasos por viaje en promedio) y el p95 queda en 14.6 µs. Recalcular siempre da p95 de 29.91 ms: no cumple los 5 ms.
- (c), la cripta de referencia: p95 de 475.2 µs con la selectiva. Cumple los 5 ms.
- (b), conocimiento desactualizado (el 5 % de las puertas cerradas se recuerdan abiertas): la selectiva y la invalidación total dan lo mismo, 22 búsquedas y 3 invalidaciones cada una. Las puertas desactualizadas que el viaje descubre están en su ruta, así que tocan salas asentadas y las dos variantes descartan la búsqueda en los mismos pasos. En este escenario la selectiva no ahorra nada frente a la total; solo ahorraría cuando el conocimiento cambia lejos de la ruta.
- N4: 405425 comparaciones (400000 consultas de N1, 2000 entradas de N2 y 3425 pasos de N3 contra paso_desde_cero y entre variantes), 0 diferencias. Si hubiera alguna, el --bench imprime ERROR y termina con código 1.
- Las pruebas comparan además, en 22 partidas generadas con antorcha, pergaminos y viajes, cada paso de «ir a» con un cálculo desde cero y lo que muestran la vista, el mapa y la bitácora con lo que el jugador conoce: 0 diferencias (tests/test_equivalencia_niebla.py).
- Mediciones anteriores repetidas con la carga de la 002 (mismo archivo), todas dentro de su límite:
  - B7 (ciclo con 50 cazadores, 2000 salas): p95 7.90 ms; antes 7.60 ms (docs/resultados_bench_p2.txt). Límite 20 ms.
  - L1 con K = 22 (300 salas, 5000 acciones): p95 de la consulta 32.66 ms; antes 26.76 ms (docs/resultados_bench_004.txt). Límite 50 ms.
  - L4 con la línea activa (2000 salas, 50 cazadores): p95 15.99 ms; antes 13.55 ms (docs/resultados_bench_004.txt). Límite 20 ms.

**Límites:**
- Primer paso de un viaje: tiene que buscar desde el destino. Con 2000 salas llega a 39.58 ms (p95 del primer paso 35.08 ms). El p95 de todos los pasos no lo ve porque buscan pocos pasos. FR-234 admite que el primer paso pase de 5 ms si se documenta aquí.
- En la cripta de referencia busca el 9.2 % de los pasos, más que el 5 % que el p95 puede esconder (research D6), porque los viajes son cortos (10.3 pasos en promedio). Igual cumple, porque en 300 salas cada búsqueda es barata (primer paso: máximo 902.1 µs).
- Conocimiento que cambia mucho: cada cambio que toca una sala asentada obliga a buscar de nuevo. Si cambiara en casi todos los pasos, el viaje costaría como recalcular siempre (p95 de 27 a 30 ms con 2000 salas).
- El comando mapa y la línea «Mapa conocido» del resumen de la historia recorren lo conocido: crecen con lo explorado (O(V + salidas exploradas)). Se piden a mano, no en cada ciclo.
- El Vector de estados ocupa memoria proporcional a toda la cripta, aunque se conozca poco.

5.4 Resolubilidad

**Problema:**
- Antes de jugar hay que decir si la cripta se puede ganar usando solo el esqueleto y la ubicación de las llaves (P2 §3.5). Si se puede, un orden de llaves por rondas; si no, las llaves que faltan, la frontera bloqueada, dónde están esas llaves, de qué llave depende cada una y los ciclos.
- Obtener una llave puede abrir una región entera. Repetir el recorrido por cada llave no cumple: el costo tiene que crecer más o menos lineal con salas, salidas y llaves (§5.4).
- La frontera, las dependencias y los ciclos tienen que salir del mismo recorrido, y todo el resultado tiene que ser determinista.
- Límite: 200 ms con la cripta publicada más grande.

**Alternativas:**
- Repetir el recorrido completo desde la sala inicial cada vez que aparecen llaves nuevas (VerificadorIngenuo): O(R · (V + E)). Con llaves encadenadas R ≈ K. La medimos (R1, R3).
- Un recorrido por llave para sacar las dependencias: lo prohíbe FR-313. Está en la ingenua solo para comparar (R4).
- Para pasar del id de una llave a un número:
  - Tabla hash propia: O(1) por búsqueda, pero el número no sirve para ordenar y era una estructura nueva solo para esto. Se analizó y no se implementó.
  - ArbolBusqueda con insertar: con ids que llegan ordenados se degenera en una lista (P1 §4.4). La medimos (R5).
  - Ordenar los ids y armar el árbol con desde_ordenados.
- Dependencias con Dijkstra (MonticuloMin) sobre (capa, llave de origen): correcto, pero más caro que el recorrido 0-1 por capas. Se descartó.
- dict, set, heapq y collections: prohibidos (§6.2).

**Decisión:**
- Un solo recorrido por oleadas (Modelo/Verificador.py) con una Cola y Vector de marcas por índice denso de sala (el de la 001, en orden de id).
- Una puerta cerrada cuya llave todavía no se tiene se estaciona bajo esa llave (un Vector de K listas). Al cerrar la ronda, sus llaves nuevas se ordenan, empiezan a abrir y se liberan sus puertas estacionadas: sus destinos son las semillas de la ronda siguiente. Una llave no abre nada en la misma ronda en que se obtiene, y así salen las rondas de FR-308.
- Pregunta del enunciado («Una llave abre una región con otras tres llaves. ¿Qué hace su verificación con las puertas que encontró cerradas antes de tener esa llave?»): esas puertas quedaron estacionadas bajo esa llave. Al obtenerla se recorren solo ellas y se sigue desde sus destinos; la región ya recorrida no se vuelve a mirar. Las tres llaves de la región nueva forman la ronda siguiente.
- Si no es resoluble, el mismo recorrido sigue por capas más allá de la frontera:
  - La capa 1 empieza en las puertas que quedaron estacionadas, que son la frontera.
  - Cada capa cruza una puerta bloqueada más. Dentro de una capa se avanza por grupos, de la llave de origen menor a la mayor, y el origen se hereda.
  - La primera marca de cada sala da la dependencia: el camino con menos puertas bloqueadas y, si hay empate, la llave de menor id.
- Ciclos: cada llave depende de a lo sumo una; se recorren con marcas de 3 estados y cada ciclo se gira para que empiece en su llave de menor id.
- Numeración (estructuras/NumeracionLlaves.py): ordenar los ids y armar el árbol con desde_ordenados. El número es la posición en el orden por id, así que ordenar llaves es ordenar enteros, y recorrer 0..K-1 ya da el orden por id que piden todas las partes del reporte.
- Coincide con lo planeado (specs/003-resolubilidad/plan.md, research D1 y D3 a D6). La tabla hash quedó sin medir por decisión del grupo. Requisitos: specs/003-resolubilidad/spec.md, FR-301 a FR-336.

**Complejidad:**
- Recorrido por oleadas: O(V + E + L), más O(K log K) para ordenar las rondas.
- Numeración: O((E + L) log K) búsquedas, con altura ⌈log₂(K + 1)⌉ garantizada.
- Frontera: O(V + E), sin ordenar.
- Capas: O(V + E + L + E log E), por ordenar las semillas de cada capa.
- Ciclos: O(K log K).
- Total: más o menos lineal. La ingenua: O(R · (V + E)).

**Evidencia:**
Se mide con: python -m crypta.bench.bench resol_ingenua resol_limite resol_crecimiento resol_igualdad resol_numeracion
Criptas sintéticas deterministas por semilla, con llaves encadenadas: una ronda por llave (docs/resultados_bench_003.txt).

Crecimiento al duplicar el tamaño (R3), criptas resolubles
  salas   llaves   incremental   cociente     ingenua   cociente
  505        125      13.54 ms          —   240.01 ms          —
  1005       250      30.39 ms       2.24   968.88 ms       4.04
  2005       500      62.04 ms       2.04      3.81 s       3.93
  4005      1000     130.04 ms       2.10           —          —
  8005      2000     274.20 ms       2.11           —          —

Límite de 200 ms (R2), desde el esqueleto cargado hasta el texto
  cripta                   salas   llaves      media         p95      máximo   ¿cumple?
  sintética resoluble       2005      500   76.24 ms    84.49 ms    86.60 ms         sí
  sintética no resoluble    2006      500   86.40 ms   101.05 ms   123.00 ms         sí
  cripta-06 (publicada)      300        4    3.60 ms     4.34 ms     4.40 ms         sí

- R1: con 2000 salas y 500 llaves, la ingenua es 66.9 veces más lenta (4.49 s contra 67.05 ms).
- R3: la incremental crece 2.04 a 2.24 veces al duplicar (límite 3); la ingenua, 3.93 a 4.04.
- R4: el texto completo es igual al de la ingenua en las 6 criptas de R1 y en 50 pequeñas, con la ubicación ordenada y barajada: 0 diferencias. Las pruebas comparan además 480 criptas por semilla (tests/test_equivalencia_resolubilidad.py).
- R5: con 2000 ids que llegan ordenados, insertar da altura 2000 y tarda 1.09 s; ordenar + desde_ordenados, altura 11 y 14.70 ms. Con 8000 ids: 63.22 ms y altura 13.
- Criptas reales, con --verificar en línea: cripta-02, 03, 04 y 06 son resolubles (código 0).
  - cripta-05 (24 salas) no es resoluble (código 2): itm_llave_hierro y itm_llave_negra dependen una de la otra. El reporte muestra el ciclo itm_llave_hierro -> itm_llave_negra -> itm_llave_hierro.
  - cripta-06 es la de referencia (300 salas, 4 llaves en 4 rondas): máximo 4.40 ms en R2.

**Límites:**
- Salidas sin vuelta: la verificación supone que el jugador puede volver a cualquier sala de la región. Puede decir «resoluble» en una cripta donde el jugador queda atrapado. Modelar dónde está el jugador obliga a probar órdenes de llaves, que crece de forma exponencial.
- Cargar el esqueleto (armar el Mapa) no entra en los 200 ms: con 2000 salas tarda unos 100 a 110 ms (100.56 y 110.82 ms en R2). Es de P1 y de la 001, y se reporta aparte.
- La ingenua solo se mide hasta 2000 salas: con 4000 y 8000 tardaría minutos. Por eso R4 tampoco compara esas criptas.
- R1 y R3 reportan el mejor de 3 mediciones; la ingenua de 2000 salas, una sola.
- Se confía en la ubicación de las llaves del servicio: no se comprueba que el enemigo que suelta una llave exista ni que inicie en esa sala, porque eso exigiría pedir contenido (FR-321).
Se hace una vez por partida, antes de crear partida.log, y con --verificar.

5.5 Línea de tiempo

**Problema:**
- Con historia <t> o historia #k el jugador ve cómo estaba la partida en un instante o justo antes de una acción. Pasa solo cuando el jugador la pide: una consulta por pedido, que no puede cambiar la partida (FR-407).
- El resumen tiene que ser igual al que se veía en ese momento (FR-421), también después de usar pergaminos, guardar y cargar, y en --replay … --hasta.
- Para responder a tiempo hay que guardar copias de la partida mientras se juega: con K = 22, una copia cada 22 acciones del jugador.
- Límites: p95 de la consulta < 50 ms en la cripta del tamaño de la de referencia (FR-432); con la línea activa, el ciclo entre dos decisiones sigue con p95 < 20 ms (FR-433); la memoria crece lineal y queda por debajo de un tercio de copiar el estado en cada acción (FR-434).

**Alternativas:**
- Una copia por acción: la consulta sería inmediata, pero 5000 acciones ocupan unos 4.7 GB (L5). La prohíbe el principio VII; es la referencia de FR-434.
- Sin puntos de control (solo el estado inicial, re-simular todo): 4.82 s de media por consulta con 5000 acciones (L1). Se descartó.
- Hacia atrás: una copia al final de cada tramo con sus cambios registrados; la consulta deshace hasta el objetivo y vuelve al final re-ejecutando, porque Cambio no sabe rehacer. La medimos (L2).
- Copiar el punto de control en cada consulta y re-simular sobre la copia: la copia sola ya cuesta 46 ms (L7). Se descartó.
- Rehacer con los cambios registrados: exige que cada Cambio de P1 sepa rehacer y traducir sus referencias a la copia. Se analizó y no se implementó.
- Cómo copiar un punto: deepcopy sin ganchos, deepcopy con ganchos y el recorrido de EstadoPartida (escribir y armar). Las medimos (L7).
- dict, set, bisect y collections: prohibidos (§6.2).

**Decisión:**
- La línea (Modelo/LineaDeTiempo.py) guarda en Vector la secuencia neta de comandos (sin los que revirtió un pergamino), con el reloj de cada decisión y su número de acción, y un punto de control (una copia completa de la partida) cada K acciones (research D1).
- Consulta hacia adelante (Modelo/Reconstruccion.py): sobre el punto anterior al objetivo se re-ejecutan a lo sumo K acciones con ejecutar_comando, se arma el resumen y se deshacen con Historial.deshacer_ultima, el mecanismo del pergamino. Lo que el historial no restaura lo guarda y lo devuelve un sello (D2, D8). La partida viva solo se lee.
- historia #k se ubica en O(1); historia <t>, con la búsqueda binaria propia (estructuras/BusquedaBinaria.py). El punto se calcula (j = ⌊(m − a₀) / K⌋): se examina uno solo (D5).
- El pergamino quita del final lo revertido y agrega una entrada de ajuste con lo que queda fuera del historial: pergaminos y objeto a la vista (D6).
- La copia es deepcopy con ganchos __deepcopy__: comparte lo de solo lectura (contenido de las salas, fichas), deja fuera lo que no es estado (búsqueda del cazador, bitácora) y le da un historial sin límite (D3).
- Guardado en formato 3: la línea y cada punto se escriben con el mismo recorrido de EstadoPartida; los formatos 1 y 2 se rechazan (D11).
- K = 22, el que proponía el plan (research D4); las mediciones lo confirmaron. Se cambia con --checkpoint-cada K.
- Requisitos: specs/004-linea-de-tiempo/spec.md, FR-401 a FR-434. Plan: specs/004-linea-de-tiempo/plan.md y research.md.

**Complejidad:**
- Registrar un comando: O(1); una vez cada K acciones, además la copia: O(tamaño de la partida).
- Pergamino: O(lo revertido), a lo sumo 5 acciones.
- Ubicar: #k en O(1); un instante en O(log n).
- Consulta: a lo sumo K acciones re-ejecutadas y deshechas, O(K (a + u)), sin importar n.
- Memoria: n/K copias más n entradas.

**Evidencia:**
Se mide con: python -m crypta.bench.bench linea_l1 linea_l2 linea_l3 linea_l4 linea_l5 linea_l6 linea_l7 linea_l8
Criptas sintéticas deterministas por semilla: 300 salas con 20 enemigos activos (la copia local de la de referencia no tiene contenidos) y 2000 salas con 50 cazadores (docs/resultados_bench_004.txt).

Consulta por K (L1), 300 salas, 5000 acciones, 200 consultas
  K    puntos   p95 consulta     máximo   crear puntos    memoria
  10      501       12.02 ms   14.84 ms        35.68 s   471.0 MB
  16      313       18.44 ms   23.23 ms        20.03 s   298.6 MB
  22      228       26.76 ms   33.09 ms        15.25 s   222.8 MB
  32      157       45.28 ms   66.04 ms        12.23 s   159.6 MB
  64       79       85.71 ms  104.37 ms         4.78 s    95.3 MB

- Por qué K = 22:
  - No 32: el p95 (45.28 ms) queda a menos de 5 ms del límite y el máximo (66.04 ms) ya lo pasa. Con 64 no cumple.
  - No 16: la consulta es más rápida, pero copia en el 6.3 % de las acciones, más que el 5 % que el p95 del ciclo puede esconder (FR-433, research D4), y ocupa 298.6 MB contra 222.8.
  - 22 es el menor K con menos del 5 % de acciones que copian (4.5 %) y deja 23 ms de margen en la consulta.
- Sin puntos de control: media 4.82 s y p95 9.51 s (20 consultas).

Hacia adelante frente a hacia atrás (L2), 300 salas, 5000 acciones, K = 22, 200 consultas
  variante                     media        p95   crear un punto    memoria
  hacia adelante (elegida)  13.43 ms   27.38 ms         63.88 ms   210.1 MB
  hacia atrás               19.02 ms   39.32 ms        108.10 ms   467.1 MB

- L2: hacia atrás no gana en la consulta (tiene que volver al final re-ejecutando), crear cada punto cuesta 1.7 veces más y ocupa más del doble.
- L3: 1873 resúmenes comparados con el oráculo (la partida viva mientras se jugaba), con los cinco K, sin puntos de control y hacia atrás: 0 diferencias.
- L4 (escenario B7 de la 001: 2000 salas, 50 cazadores, 500 acciones): sin línea p95 5.04 ms; con línea p95 13.55 ms, media 16.87 ms y máximo 315.38 ms. Copiaron 23 acciones (4.6 %). Cumple los 20 ms.
- L5: 106.4 MB con 2500 acciones y 212.8 MB con 5000 (cociente 2.00, límite 2.5); 0.046 de la copia por acción (4673.4 MB; límite 1/3).
- L6: un solo punto examinado por consulta, con 114 y con 228 puntos.
- L7: el recorrido de EstadoPartida salió un poco más rápido que deepcopy con ganchos: 40.13 contra 45.84 ms con 300 salas, y 246.38 contra 297.47 ms con 2000. Es al revés de lo que suponía el plan (research D3: armar costaría lo mismo que una copia). Igual se mantuvo deepcopy:
  - la diferencia es de 6 ms por copia, una vez cada 22 acciones (unos 0.3 ms por acción), y no cambia el K ni ningún límite;
  - con 2000 salas el recorrido ocupa más (6.0 contra 5.7 MB por copia), y la memoria es lo que más crece con los puntos;
  - las pruebas de equivalencia y del sello se hicieron con puntos copiados con deepcopy; cambiar la copia en el cierre obligaba a repetir esa validación.
  - deepcopy sin ganchos tarda más (58.61 ms, 1.2 MB) y es incorrecta: copia las fichas con su fuente, la búsqueda del cazador y la bitácora.
- L8: 228 puntos de control en 14.2 MB; guardar 2.43 s, cargar 6.48 s.
- Historial de retroceso de P1 con la carga nueva (principio XI): la consulta deshace hasta 22 acciones con el mismo Historial (ListaDoble) del pergamino, sin límite en los puntos de control, y el p95 queda en 26.76 ms (L1) y 27.38 ms (L2). La partida viva sigue con el límite de 5. Sigue siendo adecuado y no se cambió.

**Límites:**
- Escala (L1 b: 2000 salas, 50 cazadores, 1000 acciones): p95 de la consulta 90.00 ms (media 49.83 ms, máximo 181.10 ms). Pasa de 50 ms; ese escenario no tiene límite en la spec. El plan estimaba 100 a 210 ms.
- Pausa al crear un punto: con 2000 salas, copiar la partida detiene el ciclo hasta ~315 ms (máximo de L4), una vez cada 22 acciones. El p95 no la ve (13.55 ms), la media sí (16.87 contra 2.98 ms sin línea).
- Margen de FR-433: copian el 4.6 % de las acciones, contra el 5 % que el p95 puede esconder. Con K menor que 21 las copias entrarían al p95.
- Memoria: ~210 MB con 5000 acciones en 300 salas (L2 y L5), lineal en las acciones. Con 2000 salas, 286.2 MB con solo 1000 acciones (L1 b); con 5000 serían unos 1.4 GB.
- Guardado: con 5000 acciones el archivo ocupa 14 MB, guardar tarda 2.4 s y cargar 6.5 s (L8).
- Las salas que una consulta carga en un punto de control quedan cargadas (decisión del grupo, research D7). Por eso el archivo guardado de una partida con consultas no es igual byte por byte al de la misma partida sin consultas; el estado, el log y el resultado sí (D11, FR-408).
- El resumen muestra el mapa conocido del instante consultado (lo agregó la 002, T057 de la 004).
- La copia local de la cripta de referencia no tiene contenidos: todo se midió con criptas sintéticas.

5.6 Revisión de decisiones de la primera parte

**Problema:**
- Los cazadores, los costos variables y la línea de tiempo cambian la carga sobre lo que ya existía, en especial la agenda de eventos (§4.1) y el historial de retroceso (§4.6). P2 §5.6 pide repetir las mediciones de la primera parte con la carga nueva y, si una decisión deja de ser adecuada, cambiarla y documentar el antes y el después.

**Alternativas:**
- Mantener cada decisión de la primera parte si los datos lo justifican.
- Cambiarla si deja de serlo: para la agenda, los vectores ordenado o sin orden de §4.1; para el historial, la copia completa por acción de §4.6, que sigue prohibida (principio VII).

**Decisión:**
- La agenda (MonticuloMin con borrado perezoso) y el historial (Cambio por acción, no fotos) siguen siendo adecuados y no se cambiaron.
- Se extendieron sin cambiar la decisión. Antes y después (P2 §7.1):

  estructura            antes (P1)                                              después (P2)
  Agenda                programar, siguiente, cancelar y reprogramar por        además siguiente_si_corresponde(reloj), que con el tope_tiempo de la
                        velocidad sobre el montículo                            Partida detiene el ciclo en un instante (004, research D9), y
                                                                                rebobinar_secuencia, para la consulta de historia (004, research D8)
  Historial             límite fijo de 5 acciones                               Historial(limite=5) en la partida viva; limite=None en los puntos de
                                                                                control, que deshacen hasta K acciones re-ejecutadas (004, research D2)
  Cambio                inventario, agenda, enemigos, puertas, rastro...        además restaurar_sala y restaurar_puerta del mapa conocido, solo cuando
                                                                                el valor cambia (002, research D3)

**Complejidad:**
- Sin cambios respecto de §4.1 y §4.6: turno O(log n), cancelar O(1), anotar O(1), deshacer O(cambios de la acción).
- rebobinar_secuencia: O(pendientes), solo en la consulta de historia. siguiente_si_corresponde: O(log n), como siguiente.

**Evidencia:**
Se mide con: python -m crypta.bench.bench agenda ciclo inventario
Primera parte en docs/resultados_bench.txt y código final en docs/resultados_bench_revision_p1.txt. Carga de cazadores y de la línea de tiempo: B7 y L4 de docs/resultados_bench_002.txt.

Agenda (§4.1), costo de UN turno y de cancelar UN evento con el montículo
  eventos pendientes   turno P1   turno final   cancelar P1   cancelar final
  10                     8.0 µs        7.9 µs        0.7 µs           0.8 µs
  100                   11.3 µs       11.0 µs        0.4 µs           0.4 µs
  1000                  15.8 µs       14.4 µs        0.4 µs           0.4 µs
  5000                  17.1 µs       17.8 µs        0.4 µs           0.4 µs

- La agenda cuesta lo mismo que en P1. Con 5000 pendientes, el turno sigue unas 60 veces más barato que el vector ordenado (17.8 µs contra 1.09 ms) y cancelar, unas 2000 veces (0.4 µs contra 828.1 µs).
- Con la carga nueva: B7 (50 cazadores, 2000 salas) da p95 7.90 ms y L4 sin línea, p95 6.31 ms. Los dos cumplen los 20 ms. La agenda no es el cuello de botella.

Historial (§4.6), usar un pergamino frente a sacar una foto completa (deepcopy)
  enemigos activos   anotar P1   anotar final   foto P1    foto final
  10                   68.2 µs        70.6 µs   17.41 ms     15.64 ms
  100                 574.0 µs       571.7 µs   27.71 ms     24.81 ms
  300                  1.95 ms        1.94 ms   57.26 ms     47.45 ms

- Anotar los cambios cuesta lo mismo que en P1 y sigue muy por debajo de la foto: 221 veces menos con 10 enemigos, 43 con 100 y 24 con 300.
- Con la línea de tiempo, el mismo historial deshace hasta 22 acciones por consulta (sin límite en los puntos de control): L1 con K = 22 da p95 de 32.66 ms (límite 50 ms). L4 con la línea activa da p95 de 15.99 ms (límite 20 ms).
- Con el mapa conocido, una entrada con antorcha anota 28.6 cambios en promedio y deshacerlos tarda 35.5 a 38.6 µs (N2 de la 002).

Ciclo entre dos decisiones (§5.2), 2500 salas toda cargada, 60 acciones
  enemigos activos   modelo P1   modelo final   ciclo P1: p95   ciclo final: p95   ciclo P1: máximo   ciclo final: máximo
  50                   2.16 ms        2.29 ms         4.48 ms            6.09 ms            4.58 ms             470.54 ms
  100                  4.25 ms        4.67 ms         7.26 ms            8.34 ms            7.63 ms             465.09 ms
  200                  9.27 ms        9.64 ms        13.84 ms           25.58 ms           14.45 ms             507.69 ms
  300                 14.36 ms       15.48 ms        23.60 ms           29.30 ms           24.52 ms             533.76 ms
  500                 28.11 ms       26.32 ms        42.17 ms           44.59 ms           44.19 ms             460.42 ms

- El modelo (la acción y los eventos hasta la siguiente decisión, que es donde trabajan la agenda y el historial) cuesta casi lo mismo que en P1: de 2.16 a 2.29 ms con 50 enemigos y de 9.27 a 9.64 ms con 200.
- El ciclo completo pasa por el Controlador, que desde la 004 anota cada comando en la línea de tiempo y copia la partida cada 22 acciones. Esas copias explican los máximos de 460 a 534 ms y la media más alta (25.89 ms con 50 enemigos, contra 3.51 ms en P1). Es la pausa que §5.5 ya documenta.

**Límites:**
- En la primera parte el ciclo completo cumplía los 20 ms hasta unos 200 enemigos activos a la vez (§4.7). Con el código final cumple con 50 y 100 (p95 6.09 y 8.34 ms); con 200 el p95 pasa a 25.58 ms. El modelo casi no cambió, así que no viene de la agenda ni del historial. Estos datos no alcanzan para separar cuánto pone cada parte del Controlador.
- El límite de P2 es con decenas de cazadores activos (§6.1): B7 y L4 lo cumplen.
- La foto completa salió más barata que en P1 (47.45 contra 57.26 ms con 300 enemigos), pero sigue prohibida y sigue costando en cada acción.