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
- Los costos de las salidas son enteros ≥ 1 y distintos entre sí: la ruta con menos salas no siempre es la más barata.
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
- Las distancias dependen solo de la sala del jugador y de qué puertas están abiertas (los costos no cambian). Moverse, morir o cambiar de velocidad no las afecta.
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
