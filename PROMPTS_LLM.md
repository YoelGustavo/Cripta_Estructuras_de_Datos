Prompts utilizados para la elaboración del proyecto:
1. Hola, Claude, estoy haciendo un proyecto de estructuras de datos donde se utilizan distintos TDAs, algoritmos de ordenamiento y manejo de memoria. ¿Puedes analizar el enunciado y explicármelo como si tuviera 10 años? Además, ¿cuántas clases y archivos crees que necesitamos para completar el proyecto? Somos dos personas, así que me gustaría saber cómo podríamos dividir el trabajo equitativamente. Tómate tu tiempo para analizarlo.
Finalidad: Comprender el enunciado, los fundamentos del proyecto y cómo distribuir las responsabilidades entre los integrantes.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
2. Ok, mira el archivo Vector.py que te pasé. ¿Me puedes explicar si está bien implementado, qué cosas debería mejorar y por qué? También me gustaría entender cómo puedo comprobar su funcionamiento utilizando pruebas unitarias con unittest.
Finalidad: Revisar la implementación del vector y aprender a comprobar que sus operaciones funcionan correctamente.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
3. Ok, ahora hice una lista simplemente enlazada. ¿Me puedes revisar el código y explicar qué partes están bien, cuáles podría mejorar y qué errores debería evitar? Me gustaría entender las recomendaciones antes de hacer cambios.
Finalidad: Revisar el funcionamiento de la lista simple e identificar posibles mejoras en su implementación.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
4. Una pregunta, ¿qué significan yield y __iter__ en Python y por qué me recomendaste utilizarlos en mi lista? ¿Me puedes explicar cómo funcionan con un ejemplo sencillo?
Finalidad: Comprender cómo funcionan los iteradores en Python y cómo permiten recorrer una estructura de datos utilizando un ciclo for.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
5. Ok, ahora que terminé la lista simple, ¿me puedes explicar cómo debería probar sus métodos utilizando unittest, de forma similar a como hicimos con el vector? ¿Qué casos normales y casos límite debería revisar?
Finalidad: Aprender a diseñar pruebas unitarias para verificar las operaciones de la lista simplemente enlazada.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
6. ¿Crees que sería válido utilizar la lista simplemente enlazada que ya implementé para construir una cola? ¿Qué ventajas y desventajas tendría reutilizar esa estructura?
Finalidad: Analizar si es conveniente reutilizar la clase ListaSimple para implementar una cola y comprender sus implicaciones.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
7. Ok, ya hice la clase Cola utilizando la lista simple. ¿Me puedes explicar cómo comprobar si ambas clases trabajan correctamente juntas? También quisiera saber qué operaciones y casos límite debería probar con unittest.
Finalidad: Verificar la integración entre la cola y la lista simple, y aprender a probar su comportamiento FIFO.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
8. Una duda, ¿también puedo utilizar la lista simple para implementar una pila o sería mejor utilizar el vector que ya hice? ¿Me puedes explicar cuál opción conviene más y por qué?
Finalidad: Comparar distintas estructuras para implementar una pila y comprender las ventajas de utilizar un vector.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
9. Ok, hice la pila utilizando el vector, pero estoy agregando y eliminando elementos desde la posición 0. ¿Eso está bien o sería más eficiente hacerlo desde el final? ¿Me puedes explicar cómo afecta eso al rendimiento y qué debería probar para verificarlo?
Finalidad: Comprender por qué conviene realizar las operaciones push y pop en el extremo adecuado del vector y evitar operaciones innecesariamente costosas.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
10. Ahora necesito implementar una lista doblemente enlazada, pero no tengo muy claro cómo utilizarla para resolver los puntos 4.4 y 4.5 del proyecto. ¿Me puedes explicar cómo funciona esta estructura y por qué podría ser útil para la caché y el inventario?
Finalidad: Comprender el funcionamiento de una lista doblemente enlazada y su aplicación en los requisitos de caché e inventario.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
11. Me mencionaste que podría utilizar un nodo centinela en la lista doblemente enlazada. ¿Qué es exactamente un nodo centinela, para qué sirve y qué ventajas tiene frente a una lista que no utiliza uno?
Finalidad: Comprender el concepto de nodo centinela y cómo simplifica las operaciones de inserción y eliminación en una lista doble.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
12. Ok, todavía no entiendo muy bien cómo funcionan los métodos enlazar_despues_de y desenlazar. ¿Me puedes explicar paso a paso qué ocurre con las referencias de los nodos cuando agregamos o eliminamos un elemento de una lista doblemente enlazada?
Finalidad: Comprender cómo se modifican los enlaces entre nodos durante las operaciones de inserción y eliminación.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
13. Ya terminé la clase ListaDoble.py. ¿Me puedes ayudar a revisar si su funcionamiento es correcto y explicarme qué casos debería comprobar con unittest? Me interesa especialmente saber si los enlaces se mantienen bien cuando agrego o elimino nodos.
Finalidad: Revisar la implementación de la lista doblemente enlazada y verificar que sus operaciones no dañen la estructura.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
14. Voy a implementar un min-heap utilizando mi clase Vector, pero no recuerdo cómo se calculan las posiciones del padre y de los hijos izquierdo y derecho. ¿Me puedes explicar las fórmulas y mostrarme un ejemplo con índices que comienzan en 0?
Finalidad: Recordar cómo se representan las relaciones entre padres e hijos de un montículo binario almacenado en un vector.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
15. Ok, ahora necesito entender cómo se implementa un min-heap utilizando un vector. ¿Me puedes explicar paso a paso cómo funcionan la inserción, la extracción del mínimo y los procedimientos para mantener el orden del montículo?
Finalidad: Comprender las operaciones fundamentales de un montículo mínimo antes de implementarlas en Python.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
16. Ya tengo una primera versión de MonticuloMin.py. ¿Me puedes revisar la lógica y explicar cómo funcionan sus métodos? También quisiera saber qué pruebas debería hacer para comprobar que siempre se extraiga el elemento con menor prioridad.
Finalidad: Revisar la implementación del montículo mínimo y comprender cómo verificar que conserva sus propiedades.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
17. Según tu opinión, ¿qué algoritmos de ordenamiento serían más adecuados para cumplir con el punto 4.9 del proyecto? Estaba pensando en QuickSort y ordenamiento por inserción. ¿Me puedes explicar sus ventajas, desventajas y en qué situaciones conviene utilizar cada uno?
Finalidad: Comparar algoritmos de ordenamiento con características diferentes para seleccionar los más adecuados según el tamaño y el orden inicial de los datos.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
18. Ok, me recomendaste pasar los elementos de una estructura a un vector antes de ordenarlos. ¿Me puedes explicar por qué sería más conveniente hacer eso en lugar de ordenar directamente los nodos de una lista enlazada? ¿Qué diferencias hay en el acceso a los elementos?
Finalidad: Comprender la importancia del acceso por índice en los algoritmos de ordenamiento y las diferencias entre vectores y listas enlazadas.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
19. Ahora necesito resolver el punto 4.4 del proyecto, que habla de la caché de fichas del catálogo. ¿Me puedes explicar qué operaciones necesita realizar esa caché y qué estructuras de datos podrían ser apropiadas? Quisiera entender las alternativas antes de escoger una.
Finalidad: Analizar los requisitos de la caché y comparar estructuras de datos que permitan buscar, almacenar y recuperar fichas eficientemente.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
20. Me recomendaste utilizar un árbol binario de búsqueda para manejar las fichas del catálogo. ¿Por qué consideras que es una buena opción? ¿Qué ventajas tendría frente a una lista y qué problemas podrían aparecer si el árbol se desbalancea?
Finalidad: Comprender las ventajas y limitaciones de un árbol binario de búsqueda y justificar su posible utilización en la caché.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
21. Ok, creo que voy a utilizar un árbol binario de búsqueda. ¿Me puedes explicar cómo debería funcionar su implementación, especialmente las operaciones de insertar, buscar y eliminar? También quisiera saber qué cuidados debo tener para no perder nodos o referencias.
Finalidad: Comprender las operaciones principales de un árbol binario de búsqueda y los errores que deben evitarse durante su implementación.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
22. Ya terminé una primera versión del árbol binario de búsqueda siguiendo tus recomendaciones. ¿Me puedes revisar el código y explicar qué partes podrían estar incorrectas? Además, ¿qué pruebas debería realizar con unittest para comprobar las inserciones, búsquedas y eliminaciones, especialmente cuando un nodo tiene dos hijos?
Finalidad: Revisar el funcionamiento del árbol binario de búsqueda y aprender a comprobar los diferentes casos de inserción y eliminación.
Fecha aproximada: domingo 13 de septiembre de 2026　Herramienta/modelo: Claude
23. Estoy tratando de entender cómo se relacionan las carpetas Modelo, Vista, Controlador y Adaptadores. ¿Me puedes explicar qué responsabilidad tiene cada una y darme un ejemplo usando CRIPTA?
Finalidad: Comprender la separación MVC.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
24. ¿Cómo puedo decidir qué clases pertenecen al modelo y cuáles al controlador sin mezclar la lógica del juego con la interfaz?
Finalidad: Distinguir responsabilidades.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
25. Mi compañero ya implementó varias estructuras de datos. ¿Qué debo revisar antes de integrarlas con el resto del juego para no romper su funcionamiento?
Finalidad: Planificar integración.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
26. ¿Qué significa que el modelo no debe conocer HTTP ni archivos? Explícamelo con un ejemplo sencillo de una sala de la cripta.
Finalidad: Entender desacoplamiento.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
27. ¿Cómo puedo organizar la integración del proyecto por etapas para comprobar que cada parte funciona antes de unirla con las demás?
Finalidad: Organizar el desarrollo.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
28. ¿Qué diferencia hay entre una prueba unitaria y una prueba de integración? ¿Cuáles son más útiles al conectar las partes de CRIPTA?
Finalidad: Comprender estrategias de pruebas.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
29. ¿Por qué el API pide un X-Cripta-Client-Id y qué podría pasar si genero uno diferente en cada solicitud?
Finalidad: Comprender identificación de cliente.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
30. ¿Qué significa un error HTTP 429 y qué estrategia de reintentos sería apropiada si existe un presupuesto limitado de solicitudes?
Finalidad: Analizar errores de red.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
31. ¿Por qué conviene pedir el contenido de varias salas en una misma solicitud en lugar de consultarlas individualmente?
Finalidad: Comprender consultas por lotes.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
32. ¿Cómo puedo saber qué salas conviene precargar si ya tengo el mapa de conexiones, pero todavía no sé hacia dónde se moverá el jugador?
Finalidad: Explorar precarga de contenido.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
33. ¿Qué debería ocurrir si el jugador intenta entrar en una sala cuyo contenido todavía se está descargando?
Finalidad: Entender sincronización de datos.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
34. ¿Cuál es la diferencia entre el esqueleto de la cripta, el contenido de una sala y una ficha del catálogo? ¿Por qué se descargan por separado?
Finalidad: Comprender contrato de datos.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
35. ¿Cómo puedo diseñar una misma interfaz de acceso a datos para que el juego funcione tanto con HTTP como con archivos locales?
Finalidad: Comprender adaptadores.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
36. ¿Por qué es importante comparar la versión de una cripta y del catálogo antes de reutilizar archivos descargados anteriormente?
Finalidad: Entender validez de datos.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
37. ¿Qué diferencia existe entre guardar fichas en memoria y conservarlas en disco? ¿Cómo se complementan estas dos formas de almacenamiento?
Finalidad: Comprender caché persistente.
Fecha aproximada: domingo 20 de septiembre de 2026　Herramienta/modelo: ChatGPT
38. ¿Qué significa que la caché tenga un tamaño máximo de 25 fichas y qué debería pasar cuando llega a ese límite?
Finalidad: Entender capacidad de caché.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
39. ¿Qué es una política LRU y por qué podría servir para decidir qué ficha liberar de memoria?
Finalidad: Explorar políticas de reemplazo.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
40. ¿Cómo se puede combinar una lista doblemente enlazada con un árbol de búsqueda para consultar y actualizar fichas de una caché?
Finalidad: Relacionar estructuras propias.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
41. ¿Qué problemas aparecerían si una ficha utilizada por un enemigo activo se elimina de la caché? ¿Cómo podría evitarse?
Finalidad: Comprender referencias protegidas.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
42. ¿Qué operaciones de la caché deberían medirse para saber si la estructura elegida realmente es eficiente?
Finalidad: Planificar mediciones.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
43. ¿Por qué un diccionario de Python no puede sustituir las estructuras propias del proyecto y qué alternativas podríamos comparar?
Finalidad: Comprender restricciones.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
44. ¿Qué significa que CRIPTA sea un juego dirigido por eventos en lugar de un juego por rondas? Explícamelo con un ejemplo de jugador y enemigo.
Finalidad: Comprender simulación.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
45. ¿Por qué se utiliza un montículo mínimo para obtener el próximo evento y cómo se resuelven los empates entre eventos con el mismo tiempo?
Finalidad: Comprender agenda de eventos.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
46. ¿Qué ocurre con los eventos pendientes cuando muere un enemigo? ¿Qué alternativas existen para evitar que vuelva a actuar?
Finalidad: Analizar cancelación de eventos.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
47. ¿Cómo afecta la velocidad de un actor al tiempo de su siguiente acción y por qué debe recalcularse cuando cambia su velocidad?
Finalidad: Comprender tiempo virtual.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
48. ¿Por qué conviene utilizar una semilla aleatoria fija para repetir una partida y comprobar errores?
Finalidad: Entender determinismo.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
49. ¿En qué se diferencian los comportamientos guardián, errante y rastreador? ¿Qué información necesita cada uno para decidir?
Finalidad: Comprender enemigos.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
50. ¿Cómo debería funcionar el inventario para poder avanzar, retroceder, equipar y soltar objetos sin recorrerlo completamente?
Finalidad: Comprender inventario.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
51. ¿Qué diferencia hay entre el orden real del inventario y una vista ordenada por nombre, peso o valor?
Finalidad: Entender ordenamientos.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
52. ¿Por qué deshacer una acción mediante registros de cambios consume menos memoria que guardar una copia completa de la partida?
Finalidad: Comprender historial reversible.
Fecha aproximada: domingo 27 de septiembre de 2026　Herramienta/modelo: Claude
53. ¿Qué información mínima habría que recordar para revertir un ataque, una recolección o el movimiento de un enemigo?
Finalidad: Explorar operaciones inversas.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
54. Estoy diseñando los comandos de consola. ¿Qué datos debería mostrar al entrar a una sala para que el jugador pueda decidir qué hacer?
Finalidad: Planificar presentación.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
55. ¿Cómo puede el controlador traducir un comando como «recoger 1» a la posición interna del objeto sin que la vista conozca la estructura del inventario?
Finalidad: Entender traducción de comandos.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
56. ¿Qué diferencia hay entre un comando inválido y una acción válida que el juego no permite en ese momento?
Finalidad: Analizar manejo de errores.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
57. ¿Por qué una consulta como «inventario» no debería consumir tiempo virtual mientras «recoger» sí lo hace?
Finalidad: Distinguir acciones.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
58. ¿Cómo puedo mostrar solamente los últimos 20 mensajes del juego sin aumentar el uso de memoria a medida que avanza la partida?
Finalidad: Comprender bitácora circular.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
59. ¿Qué ventajas y desventajas tiene guardar una partida en un formato binario propio frente a utilizar JSON?
Finalidad: Comparar formatos.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
60. ¿Qué es un índice dentro de un archivo binario y cómo permite recuperar una sala sin leer toda la partida?
Finalidad: Comprender acceso aleatorio.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
61. ¿Qué datos deben guardarse para que una partida cargada conserve el inventario, la sala actual, el reloj y los eventos pendientes?
Finalidad: Entender persistencia.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
62. ¿Por qué el archivo de guardado debe incluir una versión de formato y qué riesgo existe si se carga una versión incompatible?
Finalidad: Comprender compatibilidad.
Fecha aproximada: domingo 4 de octubre de 2026　Herramienta/modelo: ChatGPT
63. ¿Cuál es la diferencia entre guardar el estado completo de una partida y guardar una bitácora de las acciones del jugador?
Finalidad: Distinguir guardado y replay.
Fecha aproximada: sábado 10 de octubre de 2026　Herramienta/modelo: Claude
64. ¿Cómo puede una partida reproducirse sin pedir comandos por teclado si se dispone de un archivo de acciones y una semilla aleatoria?
Finalidad: Comprender reproducción.
Fecha aproximada: sábado 10 de octubre de 2026　Herramienta/modelo: Claude
65. ¿Por qué un replay debe comprobar las versiones de la cripta y del catálogo antes de ejecutar los comandos?
Finalidad: Analizar reproducción fiel.
Fecha aproximada: sábado 10 de octubre de 2026　Herramienta/modelo: Claude
66. ¿Cómo puedo usar unittest para verificar que el controlador reconoce comandos válidos y muestra errores sin ejecutar acciones incorrectas?
Finalidad: Comprender pruebas de controlador.
Fecha aproximada: sábado 10 de octubre de 2026　Herramienta/modelo: Claude
67. ¿Qué significa utilizar mocks en una prueba y por qué ayudan a comprobar el controlador sin conectarse al API?
Finalidad: Aprender simulación de dependencias.
Fecha aproximada: sábado 10 de octubre de 2026　Herramienta/modelo: Claude
68. ¿Qué casos de prueba serían importantes para comprobar que guardar, soltar un objeto y cargar recupera exactamente el estado anterior?
Finalidad: Diseñar prueba de restauración.
Fecha aproximada: sábado 10 de octubre de 2026　Herramienta/modelo: Claude
69. ¿Cómo puedo interpretar que unittest reporte 546 pruebas, una omitida y cero fallidas? ¿Qué demuestra y qué no demuestra ese resultado?
Finalidad: Interpretar resultados de pruebas.
Fecha aproximada: miércoles 14 de octubre de 2026　Herramienta/modelo: ChatGPT
70. ¿Qué mediciones deberían compararse entre guardado binario y JSON para justificar cuál resulta más conveniente?
Finalidad: Analizar benchmarks.
Fecha aproximada: miércoles 14 de octubre de 2026　Herramienta/modelo: ChatGPT
71. ¿Por qué las pruebas con criptas de 100, 1000 y 5000 salas pueden revelar problemas que no se notan con una cripta pequeña?
Finalidad: Comprender escalabilidad.
Fecha aproximada: miércoles 14 de octubre de 2026　Herramienta/modelo: ChatGPT
72. ¿Cómo puedo comprobar que los modos --replay y --bench no dependen de la interfaz interactiva?
Finalidad: Revisar arquitectura de ejecución.
Fecha aproximada: miércoles 14 de octubre de 2026　Herramienta/modelo: ChatGPT
### 5 nov 2026 — Claude Code
- **Prompt:** "/speckit-constitution Proyecto CRIPTA (EIF-207, II ciclo 2026), segunda parte. … "
- **Uso:** crear la constitución del proyecto con spec-kit.

### 7 nov 2026 — Claude Code

**prompt** /speckit-specify Capacidad 001: Terreno y cazador. Nombre corto para la carpeta: terreno-cazador. Fuente: docs/Cripta - Parte II.pdf, secciones §3.1, §3.2, §4.1, §5.1, §5.2, §6.1, §6.3, §7.3 y los Apéndices A y B (parte «Terreno y cazador»). Las reglas de la primera parte están en docs/Primer Proyecto - Estructuras de Datos II 2026.pdf. Escribe la especificación en español, sin nombrar estructuras de datos, algoritmos concretos, clases ni módulos (constitución, principio VIII). Numera los requisitos FR-001, FR-002... y haz que cada escenario de aceptación cite el FR que verifica.

Por qué (desde el juego): en la primera parte moverse siempre costaba lo mismo y ningún enemigo buscaba rutas; el rastreador solo miraba sus salas vecinas. Ahora el terreno hace que unos caminos tarden más que otros, y aparece un enemigo, el cazador, que persigue al jugador por el camino más barato. El jugador tiene que pensar por dónde se mueve.

Historias de usuario, en orden de prioridad:
1. Terreno: como jugador, al moverme por una salida tardo según el costo de esa salida, y veo el costo de cada salida de mi sala actual.
2. Cazador: como jugador, me enfrento a un enemigo que viene hacia mí por la ruta más barata si estoy dentro de su rango, y que espera si no puede llegar.
3. Decisión siempre correcta: aunque se abran o cierren puertas, yo me mueva, otros actores mueran o cambien de sala, o cambien velocidades, el cazador decide en cada turno lo mismo que decidiría calculando desde cero.
4. Medición: el grupo puede medir con --bench el costo de las rutas del cazador y de reutilizar cálculos.

Reglas de terreno:
- Cada salida puede traer un campo costo, entero mayor o igual a 1. Si no lo trae, vale 100. Es el mismo en los dos sentidos.
- Moverse por una salida cuesta el costo de esa salida, en lugar de 100 fijo. El intervalo sigue siendo max(1, costo_salida * 100 // velocidad).
- Aplica a todos los actores: jugador, errantes, rastreadores y cazadores. Atacar, esperar y las demás acciones mantienen su costo. Errantes y rastreadores conservan su comportamiento; solo cambia cuánto tarda su movimiento.
- Si cambia la velocidad de un actor mientras atraviesa una salida costosa, el tiempo restante se reescala como en P1 §2.3.
- Una cripta sin ningún campo costo se juega exactamente igual que en la primera parte.
- La vista muestra el costo de cada salida de la sala actual.

Reglas del cazador:
- Es un cuarto comportamiento de enemigo («cazador») y su ficha del catálogo trae rango, un entero en unidades de costo. Se activa como cualquier enemigo (P1 §2.4).
- En su turno, en este orden: (1) si comparte sala con el jugador, ataca; (2) si no, calcula el costo mínimo d desde su sala hasta la sala actual del jugador, sumando costos y usando solo salidas abiertas en ese instante; (3) si no hay ruta, o si d > rango, espera con costo 100; (4) si hay, avanza un paso por una ruta de costo d y esa acción cuesta el costo de la salida que atraviesa.
- Desempate: siendo u la sala del cazador, entre las vecinas v con costo(u, v) + dist(v, jugador) = d, va a la de menor id. Esto vale aunque haya muchas rutas del mismo costo.
- Conoce el esqueleto completo y el estado actual de todas las puertas. No le afecta la niebla de guerra del jugador, no abre puertas cerradas, y su decisión nunca depende de si el contenido de una sala ya se descargó.
- Su decisión en cada turno es idéntica a la de un cálculo desde cero en ese instante. Se pueden reutilizar cálculos anteriores, pero nunca si eso cambia la decisión.
- Sus movimientos se deshacen con el pergamino como cualquier otra acción enemiga, y la misma semilla con los mismos comandos reproduce sus decisiones (--replay).
- La vista distingue a los cazadores de los demás enemigos.

Datos: el costo llega en el esqueleto y el rango en el catálogo. Se persisten con su versión, y lo guardado por la primera parte se invalida por la validación de versión, no borrando archivos. Guardar y cargar una partida conserva los costos.

Escenarios de aceptación obligatorios (Apéndice B):
- Un cazador no tiene ruta abierta hacia el jugador: espera con costo 100.
- La ruta más barata del cazador cuesta más que su rango: espera con costo 100.
- Existe una ruta de menos salas pero mayor costo y otra de más salas y menor costo: el cazador sigue la de menor costo.
- Dos vecinas inician rutas de costo mínimo: el cazador va a la de menor id.
- Una puerta de la ruta del cazador se cierra entre dos de sus turnos: en el turno siguiente decide como si calculara desde cero.
- Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1.
- Cambia la velocidad de un actor que atraviesa una salida costosa: el tiempo restante se escala según P1 §2.3.
Agrega además: el cazador en la misma sala que el jugador ataca; el cazador no usa una puerta cerrada aunque sea el camino más barato; una cripta sin costos se comporta igual que en la primera parte.

Requisitos de rendimiento:
- El ciclo de eventos entre dos decisiones del jugador toma menos de 20 ms con decenas de cazadores activos en la cripta de referencia.
- La decisión de un cazador con rango pequeño cuesta según la región que queda dentro de su rango, no según el tamaño de la cripta.
- --bench mide, con criptas sintéticas deterministas por semilla: un cazador frente a muchos, rango pequeño frente a grande, cálculo compartido frente a uno por cazador, y reutilizar cálculos frente a recalcular siempre, con puertas que casi nunca cambian y con puertas que cambian seguido.

Fuera de alcance de esta especificación: niebla de guerra, «ir a», resolubilidad y línea de tiempo (tienen su propia especificación).

Deja marcado como pendiente de aclarar: qué hace el programa si un costo es inválido (menor que 1 o no entero) o distinto en cada sentido, y si un cazador no trae rango.

**USO;** Ayudar a crear el specify del cazador y el terreno.

**Prompt** Ajusta specs/001-terreno-cazador/spec.md con estos cambios de revisión del grupo, sin tocar nada más:
1. Las historias dicen "Prioridad: P1..P4" y se confunden con P1/P2 (las partes del proyecto). Cámbialas a "Prioridad 1", "Prioridad 2", "Prioridad 3" y "Prioridad 4".
2. Los escenarios del cazador deben indicar su rango para que la prueba sea exacta. En la historia 2, escenarios 5, 6, 7, 8, 9 y 11, y en la historia 3, escenarios 1 a 5, agrega "de rango 1000" (o un rango que no limite el caso).
3. Cada FR debe tener al menos un escenario de aceptación que lo cite, porque en la defensa se escoge un requisito al azar. Agrega escenarios para: FR-011 (el cazador usa el rango de su ficha del catálogo); FR-024 (dos criptas sintéticas iguales salvo los costos dan instantes distintos con el mismo código: nada está quemado); FR-025 (una copia local de la primera parte con otra versión de cripta se invalida y se descarga el esqueleto nuevo con costos); FR-035, FR-036 y FR-037 (medidos con --bench: ciclo menor a 20 ms con decenas de cazadores; tiempo por decisión con rango pequeño al multiplicar la cripta por 10; trabajo por ciclo que crece linealmente con los cazadores activos).
4. En FR-021 aclara que la decisión del cazador (atacar, esperar o a qué vecina moverse) no usa el generador aleatorio, pero el daño de su ataque sí lo usa, como cualquier ataque (P1 §2.6).
No cambies la numeración de los FR existentes. Deja las marcas NEEDS CLARIFICATION de FR-010 y FR-011 para /speckit-clarify.

**USO:¨** corregir el specify y ajustarlo.

**Prompt** A, con una excepción: si solo un lado de la salida declara costo, ese costo vale en los dos sentidos y no cuenta como asimétrico. Solo se rechaza si los dos lados declaran costos distintos, o si un costo es menor que 1 o no es entero. A partir de ahora responde en español y registra las preguntas y respuestas del clarify en español.
D. Además: un rango 0 es válido. Si la ficha inválida llega con la partida ya empezada (por ejemplo, por la precarga), la partida se detiene de forma controlada con ese mismo mensaje y el partida.log queda guardado.
B. Además: los cazadores deben estar repartidos a distintas distancias del jugador y dentro de su rango, para que de verdad calculen rutas (no que ya estén en su sala atacando). Lo que debe quedar por debajo de 20 ms es el p95 de al menos 60 acciones del jugador, como en la medición de la primera parte.
B
10, 25, 50 y 100 cazadores; el tiempo por cazador (ciclo ÷ cantidad) con 100 no debe pasar de 2 veces el de 10.
 **USO:** preguntas de aclaraciones de (/speckit-clarify)

**Prompt** /speckit-plan Plan para specs/001-terreno-cazador. Responde en español. Contexto técnico: Python 3.11+, sin dependencias nuevas (biblioteca estándar, requests y struct). El código está en crypta/ (Modelo, Vista, Controlador, Adaptadores, estructuras, bench) y las pruebas en tests/ (unittest). El enunciado está en docs/Cripta - Parte II.txt; lee sobre todo §3.1, §3.2, §5.1, §5.2, §6.1 y §6.3. Cumple la constitución: nada de heapq, dict, set, bisect, collections ni bibliotecas de grafos.

Lo que hay que revisar del código actual antes de planear:
- crypta/Modelo/Partida.py tiene COSTO_MOVER = 100 fijo para el jugador, y _aplicar_comportamiento reprograma a los enemigos con 100 tanto al moverse como al esperar. Los movimientos deben pasar a costar lo que cueste la salida.
- Las salidas se leen en crypta/Modelo/Sala.py y crean una Puerta (cerrada, llave, cierre_automatico). Las dos puertas de una salida comparten el estado (EstadoPuerta, en Puerta.py).
- El guardado (crypta/Adaptadores/EstadoPartida.py y GuardadoBinario.py) escribe las puertas de cada sala y tiene una versión de formato.
- Ya tenemos MonticuloMin (con comparador), Cola, ArbolBusqueda, Vector, el historial de cambios (Cambio, Historial) y el framework de medición (crypta/bench, medicion.py).

Propuesta del grupo, para evaluarla en el plan con alternativas y mediciones (no es una decisión cerrada):
1. Ruta más barata: búsqueda de costo mínimo con nuestro MonticuloMin, que se detiene al pasar el rango, para que cueste según la región dentro del rango (FR-036).
2. Cálculo compartido: como el costo es igual en ambos sentidos y las puertas se comparten, dist(v, jugador) = dist(jugador, v). Una sola búsqueda desde la sala del jugador, limitada al mayor rango entre los cazadores activos, da la distancia de todas las salas de esa región. Cada cazador decide mirando solo sus vecinas, con el desempate por menor id de FR-017. Alternativa: una búsqueda por cazador. Medir las dos (FR-031) y decir cuándo conviene cada una.
3. Reutilización (FR-019, FR-032): la distancia depende solo de la sala del jugador y del estado de las puertas; que otros actores se muevan, mueran o cambien de velocidad no la cambia. Reutilizar el cálculo mientras esas dos cosas no cambien, y analizar si un cambio de puerta fuera de la región calculada se puede ignorar con seguridad. Un pergamino y la carga de una partida guardada invalidan lo calculado. La equivalencia con un cálculo desde cero se comprueba con pruebas (FR-033, SC-002).
4. Dónde guardar las distancias sin dict: comparar un campo en cada sala con una marca del cálculo vigente, frente a un ArbolBusqueda por id de sala.
5. Lo calculado para las rutas no es estado del juego: no va en el historial del pergamino ni en el archivo de guardado.

El plan debe incluir:
- los módulos afectados;
- las estructuras y la complejidad de las operaciones más frecuentes;
- las alternativas descartadas y por qué;
- las mediciones planificadas para FR-028 a FR-037 con los valores fijados en Aclaraciones (50 cazadores repartidos dentro de su rango en 2 000 salas, p95 de al menos 60 acciones; región de unas 100 salas en criptas de 2 000 y 20 000; 10, 25, 50 y 100 cazadores con tiempo por cazador de a lo sumo 2 veces);
- el impacto en el guardado (si cambia el formato, se sube su versión);
- la lista de pruebas por FR.

Este plan será el borrador de la sección de DECISIONES.md (P2 §7.1).

**Uso:** crear el plan.md y corregirlo.

**Prompt:** Ajustes de revisión del grupo al plan 001:
1. Cambio de spec (principio VIII, va primero): un campo costo con valor null cuenta como «no declarado» (vale el costo del otro lado o 100), no como inválido. Un float (aunque sea 250.0), un bool o un texto siguen siendo inválidos. Actualiza FR-001, FR-010 y el caso borde en spec.md. Para el rango del cazador, null sigue siendo inválido.
2. Refleja ese cambio en plan.md (quita la nota «Interpretaciones que el grupo debe confirmar») y en contracts/datos-servicio.md.
3. La prueba de FR-008 no puede depender de cache/: si alguien juega cripta-01 en línea, la copia local se actualiza a la versión nueva y el log de la primera parte deja de servir. Guarda en tests/datos/ una copia fija de la cripta y del catálogo de la primera parte junto con p1_partida.log, y haz que la prueba use esa copia. Actualiza plan.md y quickstart.md.
4. En B7 (contracts/bench.md), el jugador debe moverse en un recorrido fijo y determinista durante las 60 acciones, para que los cazadores sigan calculando rutas y no terminen todos atacando en su sala.
No cambies nada más.

**USO** ajuste y correcciones + del plan.md

**Prompt** /speckit-tasks Genera tasks.md para specs/001-terreno-cazador, en español, a partir de plan.md, research.md, data-model.md y contracts/. Requisitos del grupo:
- Cada tarea cita los FR que atiende (principio IX). Las tareas de preparación citan el FR que habilitan.
- Incluye las pruebas: por cada escenario de aceptación, una tarea de prueba que cite su FR, escrita antes de implementar esa historia (primero debe fallar).
- La primera tarea es grabar tests/datos/p1_partida.log, con la copia fija de la cripta y del catálogo de la primera parte, usando el código actual y antes de cualquier cambio (FR-008).
- Organiza por fases: preparación; base común (costo en las puertas, DatosInvalidos, índices y entradas del mapa); historia 1 (terreno); historia 2 (cazador); historia 3 (equivalencia); historia 4 (bench); y cierre (vista, secciones §5.1 y §5.2 de DECISIONES.md a partir de research.md, README y revisión de imports prohibidos).
- Tareas pequeñas, de una o dos horas, cada una con la ruta del archivo que toca, para repartirlas entre los integrantes. Marca con [P] las que se pueden hacer en paralelo sin tocar el mismo archivo.
- Al final de cada fase, un punto de control: python -m unittest en verde y commit.
- Entregamos el miércoles 18 de noviembre: ordena para que las historias 1 y 2 queden primero, porque son las que más pesan.

**USO:** crear el tasks

**Prompt** /speckit-analyze

**USO:** Analiza todo lo q se ha hecho y se clasifica el nivel de prioridad de cada tarea y demás.

**Prompt** /speckit-implement Solo la fase 1 (T001 a T005) de specs/001-terreno-cazador/tasks.md. Detente al terminar su punto de control, marca las tareas hechas en tasks.md y no hagas commit: lo hago yo después de revisar.

**USO:** Datos fijos de la primera parte (una partida grabada y su resultado) y ayudas de prueba, para comprobar que P1 sigue igual (FR-008).

**Prompt** /speckit-implement Solo la fase 2 (T006 a T015) de specs/001-terreno-cazador/tasks.md. Detente al terminar su punto de control, marca las tareas hechas en tasks.md y no hagas commit: lo hago yo después de revisar.

**USo** Base común: costo de las salidas, error DatosInvalidos, índice de cada sala y entradas del mapa.

**Prompt** /speckit-implement Solo la fase 3 (T016 a T031) de specs/001-terreno-cazador/tasks.md. Detente al terminar su punto de control, marca las tareas hechas en tasks.md y no hagas commit: lo hago yo después de revisar.

**USo:** Fase 3 de la 001: mover cuesta lo que dice la salida, para el jugador y los enemigos; las demás acciones cuestan igual que en P1

**Prompt:** /speckit-implement De la fase 4 de specs/001-terreno-cazador/tasks.md haz solo T032, T045, T047, T048, T049, T050, T051 y T054 (las estructuras DistanciasLimitadas y RutaPorCazador, y la validación del rango). Todavía no hagas Perseguidor ni la rama del cazador en Partida. Marca las tareas hechas en tasks.md y no hagas commit.

**USo:** Fase 4 de la 001, parte A: el Dijkstra con límite desde el jugador, la versión por cazador para comparar y la validación del rango de la ficha.

**Prompt** /speckit-implement Termina la fase 4 de specs/001-terreno-cazador/tasks.md: T033 a T044, T046, T052, T053 y el punto de control T055. Marca las tareas hechas en tasks.md y no hagas commit.

**USO:** Fase 4 de la 001, parte B: el cazador decide atacar, esperar o dar un paso por la ruta más barata.

**Prompt:**/speckit-implement De la fase 5 de specs/001-terreno-cazador/tasks.md haz solo T056 a T063, T065 y T066 (verificador, invalidación selectiva y pergamino). Todavía no toques el guardado. Marca las tareas hechas en tasks.md y no hagas commit.

**USO:** Fase 5 invalidacion y equivalencia

**Promt** /speckit-implement Termina la fase 5 de specs/001-terreno-cazador/tasks.md: T064, T067 a T070 y el punto de control T071. Marca las tareas hechas en tasks.md y no hagas commit.

**USO;** Fase 5 de guardado.

**Promt:** /speckit-implement Haz la fase 6 de specs/001-terreno-cazador/tasks.md: T072 a T085 y el punto de control T087. No hagas T086, el bench completo lo corro yo. Marca las tareas hechas en tasks.md y no hagas commit.

**USo:** pruebas de bench.

**Promt** /speckit-implement De la fase 7 de specs/001-terreno-cazador/tasks.md haz solo T088, T089, T090 y T095. Dentro de T095, en crypta/bench/bench_cazador.py cambia TAMANOS (es un dict, prohibido por §6.2) por una tupla de (salas, ancho, alto) y búscalo con un for. Marca las tareas hechas en tasks.md y no hagas commit.

**USO:** 001 vista: costo de salidas y etiqueta del cazador

**Prompt:** /speckit-implement De la fase 7 de specs/001-terreno-cazador/tasks.md haz T091, T092, T093, T096 y el punto de control T097. No hagas T094 (PROMPTS lo llevo yo). T086 ya la hice: los resultados están en docs/resultados_bench_p2.txt (docs/resultados_bench.txt es el de P1 y no se toca); márcala hecha. Las secciones §5.1 y §5.2 van en DECISIONES.md de la raíz, con el mismo formato que las secciones de P1 de ese archivo: sin introducción, los 6 puntos en negrita (Problema, Alternativas, Decisión, Complejidad, Evidencia, Límites), viñetas cortas y una o dos tablas pequeñas con números de docs/resultados_bench_p2.txt. En Límites de §5.2 incluye: B4/B5 inestables pasan de 20 ms pero son 50 cambios de puerta por acción, algo que el juego no produce; B7 mide el modelo y no el Controlador. En T096 deja la prueba manual del juego para mí. No hagas commit.

**USO:** Documentacion y demás.

**Prompt:** /speckit-specify SPECIFY_FEATURE_DIRECTORY=specs/003-resolubilidad. Capacidad 3 del enunciado (docs/Cripta - Parte II.txt): verificación de resolubilidad (§3.5, §4.2, §4.3, §5.4, §6.1, §6.3, §7.3, Apéndices A y B). Numera los requisitos FR-301, FR-302… y los criterios de éxito SC-301… para que no choquen con la 001. Sin nombres de estructuras, clases ni módulos (eso va en el plan). No hagas commit.

Reglas (las del enunciado más estas decisiones del grupo):
- Antes de iniciar una partida se verifica con el esqueleto y la ubicación de las llaves (GET /criptas/<id>/llaves), sin pedir el contenido de ninguna sala. La consulta cuenta en el presupuesto de solicitudes y se guarda con la copia local de la cripta; vale mientras coincida la versión.
- Supuestos de §3.5: se cruza toda salida abierta, toda salida cerrada sin llave y toda salida cerrada cuya llave ya se obtuvo; las llaves no se consumen; todo enemigo se puede derrotar; una llave que suelta un enemigo está en la sala donde ese enemigo inicia; trampas y cierres automáticos no bloquean. Una salida sin vuelta solo se cruza en su sentido.
- Resoluble: desde sala_inicial se obtiene llave_salida y se llega a sala_salida cruzando una salida cerrada que pide llave_salida. Si la cripta no define sala_salida o llave_salida, no es resoluble (en la primera parte tampoco se puede ganar).
- Orden de llaves si es resoluble (determinista): primero, por id, las llaves que se obtienen sin ninguna llave; luego, por id, las que se vuelven obtenibles con esas; y así sucesivamente. Incluye todas las llaves obtenibles.
- Reporte si no es resoluble, todo sacado del mismo recorrido: (1) las llaves que no se pueden obtener; (2) la frontera bloqueada: cada salida cerrada que sale de una sala alcanzable hacia una no alcanzable y pide una llave no obtenible (sala, dirección, sala destino, llave); (3) dónde está cada llave de la frontera (sala, y enemigo si la suelta uno) o que no está en la cripta; (4) los ciclos de dependencia; (5) si llave_salida se obtiene pero ninguna salida que la pide lleva a sala_salida desde la región alcanzable, decirlo.
- Dependencia para los ciclos: una llave no obtenible depende de la llave de la PRIMERA puerta bloqueada del camino que cruza menos puertas bloqueadas desde la región alcanzable hasta su sala (empate: la de menor id). Si su sala no se alcanza ni abriendo todas las puertas, no depende de ninguna y el reporte lo dice. Un ciclo es una cadena A → B → … → A; cada ciclo se reporta una vez, empezando por su llave de menor id. Ejemplo: llave_salida detrás de la única puerta que ella abre → ciclo llave_salida → llave_salida.
- Una misma llave puede estar en varias ubicaciones: se obtiene en cualquiera. Una llave ubicada en una sala que no existe → la cripta se rechaza como dato inválido, igual que en la 001.
- Si no es resoluble, la partida no inicia y se muestra el reporte; con --forzar se muestra el reporte y la partida inicia. Si es resoluble, al iniciar se muestra el orden de llaves.
- Sin conexión y sin la ubicación de las llaves en la copia local no se puede verificar: se avisa y se trata como no resoluble (solo inicia con --forzar).
- --verificar <cripta>: solo verifica e imprime el reporte; no crea la vista, ni la partida, ni partida.log. Código de salida 0 si es resoluble, 2 si no lo es, 1 si hubo un error (red, datos inválidos, sin llaves).
- --replay no verifica: la partida del log ya empezó (pudo ser con --forzar). La verificación no es estado del juego: no se guarda ni la toca el pergamino.

Rendimiento: el costo total crece aproximadamente lineal con salas + salidas + llaves; no se repite el recorrido de la cripta por cada llave obtenida. Máximo 200 ms (equipo local, sin red) con la cripta publicada más grande; mientras no se publique, con una sintética de 20 000 salas y 1 000 llaves encadenadas. --bench: recorrido incremental frente a repetirlo por cada llave, con criptas sintéticas deterministas por semilla con muchas llaves encadenadas.

Los 4 casos de Resolubilidad del Apéndice B van como escenarios de aceptación.

**USO:** Specify del objetivo 003

**Prompt**/speckit-clarify Antes de preguntar, aplica estos cambios del grupo a specs/003-resolubilidad/spec.md:
1. FR-334, SC-303 y el escenario 4 de la historia 5: la cripta sintética de referencia para los 200 ms es de 2 000 salas (el mismo tamaño de referencia de la 001) con 500 llaves encadenadas, no de 20 000 salas.
2. FR-335 y SC-304: al duplicar el tamaño, el tiempo no pasa de 3 veces el anterior (lineal da 2; repetir el recorrido por cada llave da cerca de 4).
3. SC-307: las pruebas de P1 y de la 001 que inician una partida sin conexión necesitan la ubicación de las llaves en sus datos de prueba (FR-324); solo se ajustan esos datos, no lo que comprueban.
4. Marcador de FR-303: la región alcanzable es todo lo que se alcanza desde sala_inicial y se supone que el jugador puede volver a cualquier sala de la región, como pide el enunciado. Agrega en Supuestos el límite: con salidas sin vuelta, la verificación puede decir "resoluble" en una cripta donde el jugador queda atrapado; modelar dónde está el jugador obligaría a probar órdenes de llaves (en el peor caso crece de forma exponencial) y rompería el costo lineal de §5.4.
Después sigue con las preguntas normales.

**USO:** aplicación del clarify en el punto 003

**Prompt:** /speckit-specify SPECIFY_FEATURE_DIRECTORY=specs/004-linea-de-tiempo. Capacidad 4 del enunciado (docs/Cripta - Parte II.txt): línea de tiempo (§3.6, §5.5, §6.1, §6.3, §7.3, Apéndice B «Línea de tiempo»). Numera los requisitos FR-401, FR-402… y los criterios SC-401…. Sin nombres de estructuras, clases ni módulos. No hagas commit.

Reglas (las del enunciado más estas decisiones del grupo):
- Estado en el instante t: el de después de ejecutar todos los eventos con tiempo ≤ t. Si a t le corresponde una decisión del jugador, es el estado justo antes de esa decisión; los eventos del mismo instante que en la agenda vienen después de la decisión no se incluyen.
- historia <t>: t entero ≥ 0; si t es mayor que el reloj actual, se rechaza. historia #k: estado justo antes de la acción número k del jugador, contando como en P1 (las acciones deshechas no cuentan); k va de 1 a acciones del jugador + 1 (este último es el estado actual); fuera de ese rango se rechaza. Texto mal formado → comando inválido, como en P1. Un rechazo no consume tiempo ni cambia nada.
- El resumen muestra como mínimo: instante consultado y reloj, número de acción, sala del jugador, vida y estadísticas (ataque, defensa, velocidad), inventario, efectos activos, enemigos de esa sala con su vida, y el mapa conocido en ese momento (el mapa conocido lo define la capacidad 002, que se especifica aparte; aquí solo se exige mostrarlo como era en t). El mismo resumen sirve para historia y para --replay --hasta.
- La consulta no consume tiempo virtual, no es acción, no se anota en partida.log y no cambia el historial del pergamino ni el estado del azar: una partida con consultas y la misma partida sin consultas terminan idénticas.
- Pergamino: las acciones revertidas dejan de existir en la línea de tiempo y la línea se recorta sin recorrer toda la historia. Después, historia no las muestra y #k se numera con las acciones que quedaron.
- Puntos de control: copias completas del estado (incluido el estado del azar si se reconstruye re-simulando), a lo sumo uno cada K acciones del jugador. --checkpoint-cada K, entero ≥ 1; el valor por defecto lo decide el plan con mediciones. Fuera de los puntos de control solo se guarda lo necesario para reconstruir los cambios. Ninguna consulta aplica o deshace cambios de más de K acciones del jugador. La memoria crece con los cambios ocurridos más un punto de control cada K acciones, nunca con acciones × tamaño del estado. Ubicar el punto de control más cercano no recorre todos los puntos de control.
- Guardar y cargar conserva la línea de tiempo completa y su K. Al cargar se usa el K guardado; si --checkpoint-cada indica otro, se avisa y se usa el guardado. El formato del archivo de partida cambia: un archivo de la primera parte o del formato anterior de la 001 se rechaza con un mensaje de incompatibilidad; nunca se carga en silencio (no se migra).
- --replay partida.log --hasta t: reproduce hasta t e imprime el resumen sin instanciar la vista. Si t es posterior al final del log, muestra el último estado y dice que la partida terminó antes (o que el log termina antes, si la partida no terminó). --hasta sin --replay es un error de argumentos.
- historia solo está disponible mientras la partida está en curso; para una partida terminada está --replay --hasta.

Rendimiento: historia en menos de 50 ms con una partida de al menos 5 000 acciones del jugador y K por defecto (equipo local, sin red ni vista). Registrar la línea de tiempo no debe romper el límite de 20 ms por ciclo de la 001. --bench: partidas sintéticas deterministas por semilla de al menos 5 000 acciones; memoria y tiempo de consulta con al menos tres valores de K y con la alternativa sin puntos de control; y la alternativa de reconstrucción descartada (hacia adelante o hacia atrás), para respaldar la decisión.

Los 6 casos de «Línea de tiempo» del Apéndice B van como escenarios de aceptación.

**USO:** Specify del objetivo 004

**Prompt**/speckit-clarify Antes de preguntar, aplica estos dos cambios del grupo a specs/004-linea-de-tiempo/spec.md:
1. FR-406: el resumen muestra el instante consultado y el reloj de ESE estado, no el reloj actual de la partida, para que historia, --replay --hasta y una carga posterior den exactamente el mismo texto (HU1-1, HU3-1, HU4-1). Si la vista quiere mostrar el reloj actual, va fuera del resumen.
2. FR-407: una consulta tampoco DEBE hacer solicitudes de red ni gastar presupuesto de solicitudes; agrega un escenario que lo pruebe.
Después sigue con las preguntas normales.

**USO:** Clarify de preguntas de 004

**Prompt:** /speckit-specify SPECIFY_FEATURE_DIRECTORY=specs/002-niebla-ir-a. Capacidad 2 del enunciado (docs/Cripta - Parte II.txt): niebla de guerra y viaje automático «ir a» (§3.3, §3.4, §5.3, §6.1, §6.3, §7.3, Apéndice B «Niebla de guerra e ir a»). Numera los requisitos FR-201, FR-202… y los criterios SC-201…. Sin nombres de estructuras, clases ni módulos. No hagas commit.

Reglas (las del enunciado más estas decisiones del grupo):
- Estados de cada sala para el jugador: explorada (entró al menos una vez; la inicial desde el instante 0), avistada (no explorada pero destino de una salida de una explorada) y desconocida. De una explorada conoce nombre, salidas, costo de cada salida y el estado de sus puertas según la última observación; de una avistada solo que existe (se muestra su id, no su nombre).
- Observación de puertas: al entrar a una sala y antes de cada decisión del jugador, el jugador observa las salidas de la sala donde está. Como los dos lados de una puerta son la misma puerta, observarla desde un lado actualiza lo que recuerda de ella. Una salida sin vuelta que llega a la sala actual desde otra no se observa desde aquí. El mapa recuerda el estado de la última observación aunque después cambie.
- Antorcha encendida: al entrar a una sala, también quedan exploradas todas las vecinas a las que llevan sus salidas (abiertas o cerradas), y sus salidas cuentan como observadas en ese instante. No se revela su contenido ni se activan sus enemigos o trampas.
- Todo lo que muestra la vista y lo que usa «ir a» sale solo del conocimiento del jugador. Eso incluye la bitácora: solo muestra lo que pasa en la sala del jugador o le pasa al jugador (no avisa de enemigos que se regeneran o trampas que se rearman en otras salas). El reporte de resolubilidad de la 003 es la excepción ya declarada allí. El esqueleto completo y la precarga siguen siendo infraestructura.
- El conocimiento es estado del juego: se guarda en el archivo de partida (un archivo de un formato anterior se rechaza como incompatible, igual que en la 004), se revierte con el pergamino y forma parte de la línea de tiempo (el resumen de historia de la 004 muestra el mapa conocido de ese momento).
- Comando mapa: muestra las salas exploradas (id, nombre y cada salida con dirección, sala destino, costo y estado recordado) y las salas avistadas, ordenadas por id. No consume tiempo ni es acción.
- ir a <sala>: solo hacia una sala explorada; hacia una no explorada, hacia la sala actual o sin ruta conocida desde el inicio, se rechaza sin consumir tiempo. Texto mal formado → comando inválido, como en P1.
- La ruta usa solo salas exploradas y salidas que el mapa recuerda abiertas; minimiza la suma de costos y desempata como el cazador de la 001 (primer paso hacia la vecina de menor id). Se recalcula antes de cada paso, después de observar las salidas de la sala actual. No abre puertas aunque el jugador tenga la llave.
- Cada paso es un movimiento ordinario completo (cuesta según la 001 y entre paso y paso corren los eventos del reloj). El viaje se detiene cuando: llega; entra a una sala con enemigos (activos o dormidos); el jugador recibe daño (ataque, trampa o veneno); deja de existir una ruta conocida (sin consumir tiempo adicional); un paso no se puede hacer (por ejemplo, sin presupuesto o sin conexión para cargar la sala); o la partida termina. La vista dice por qué se detuvo.
- partida.log: cada paso se anota como un mover individual y la orden ir a como una línea de comentario; la reproducción ignora los comentarios (los logs de P1 se siguen reproduciendo igual). El pergamino revierte solo el último paso y el viaje no se reanuda.

Rendimiento: consultar el estado de una sala o de una puerta recordada es frecuente y no debe depender del tamaño del mapa conocido; explorar cuesta en proporción a las salas reveladas; registrar y deshacer cambios del conocimiento es barato. Un paso de ir a (el cálculo de la ruta) en menos de 5 ms con el mapa conocido completo de la cripta de referencia de la 001 (2 000 salas). --bench: consultas al mapa conocido y cálculo de un paso de ir a, cada uno frente a una alternativa descartada, con criptas sintéticas deterministas por semilla.

Los 6 casos de «Niebla de guerra e ir a» del Apéndice B van como escenarios de aceptación.

**USO:** Specify de caso 002 (niebla + ir a)

**Prompt:** /speckit-clarify Antes de preguntar, aplica estos cambios del grupo a specs/002-niebla-ir-a/spec.md:
1. FR-234, HU5-4 y SC-204: el p95 de menos de 5 ms se mide sobre todos los pasos de al menos 20 viajes completos (200 pasos o más) entre salas repartidas de forma determinista, con el mapa conocido completo de 2 000 salas. --bench reporta aparte el costo del primer paso de cada viaje (el que calcula la ruta entera); si pasa de 5 ms se documenta como límite en DECISIONES.md. Agrega en Supuestos: una búsqueda completa hasta un destino al azar en 2 000 salas tarda varios ms (medido: media 6,4 ms y p95 11 ms en otra máquina), así que recalcular desde cero en cada paso no cumple; el plan debe reutilizar el cálculo entre pasos mientras el mapa conocido no cambie.
2. FR-214 y HU2-2: la antorcha no provoca solicitudes; con y sin antorcha se hacen las mismas solicitudes (la precarga sigue siendo infraestructura, FR-209).
3. FR-216: un id de sala que no existe se rechaza con el mismo mensaje que una sala no explorada, para no revelar qué salas existen.
4. FR-222: la línea de comentario de ir a va antes de los mover de ese viaje.
Después sigue con las preguntas normales.

**USO:** Clarifiy de las preguntas de la seccion 002

**Prompt:** B: solo lo detienen las condiciones de §3.4 (y las técnicas que ya están); si el enemigo ataca, el daño lo detiene.

**USO:** Respuesta a una pregunta que me hizo


**Prompt** /speckit-plan SPECIFY_FEATURE_DIRECTORY=specs/003-resolubilidad (actualiza .specify/feature.json para que apunte ahí). Plan de la capacidad 003 según su spec y la constitución. Indicaciones del grupo:
- Solo TDA del curso (sin dict, set, heapq, bisect ni collections). Reutiliza lo de P1 y la 001: índices densos de las salas, Cola para el recorrido, Vector para marcas y ordenar para los ids.
- Para pasar del id de una llave a un número, compara como alternativas una tabla hash hecha a mano, ArbolBusqueda con inserciones, y ordenar los ids + ArbolBusqueda.desde_ordenados (balanceado). Ojo: un ArbolBusqueda llenado con ids en orden se degenera en una lista (límite documentado en P1 §4.4).
- Un solo recorrido por oleadas: las puertas cerradas cuya llave todavía no se tiene se "estacionan" por llave y se liberan cuando la llave se obtiene. Si la cripta no es resoluble, el MISMO recorrido continúa por capas más allá de la frontera para sacar las dependencias (FR-314) y de ahí los ciclos; nunca un recorrido por llave.
- La alternativa ingenua del bench: repetir el recorrido completo cada vez que se obtiene una llave.
- No implementes nada todavía. No hagas commit.

**USO:** specificacion del plan de los puntos 003

**Prompt:** Ajustes del grupo a specs/003-resolubilidad (no implementes nada, no hagas commit):
1. D1: no se implementa TablaHash ni NumeracionHash. La tabla hash queda como alternativa analizada en research.md, sin medir, y R5 mide solo ArbolBusqueda con insertar (ids barajados y ids ordenados, con su altura) frente a ordenar + desde_ordenados. Quita TablaHash.py y test_tabla_hash.py de plan.md, data-model.md, contracts/bench.md y quickstart.md.
2. contracts/bench.md, R4: compara con la ingenua solo las criptas de los tamaños de R1 y las 50 pequeñas (con 4 000 y 8 000 salas la ingenua tardaría minutos). En R1, la ingenua del tamaño mayor se mide con una sola repetición.
3. D6: en FR-311 de spec.md agrega: "dentro de la misma sala, primero la ubicación sin enemigo y después las que tienen enemigo, por id de enemigo", y en research.md y plan.md quita lo de "se propone llevarlo a la spec".

**USO:** Ajuste del resultado anterior entregado.

**Prompt:** Arreglos del grupo al análisis de la 003 (no implementes nada; no hagas commit):

Spec (specs/003-resolubilidad/spec.md):
- C1: agrega FR-336 en «Modo --verificar»: "--verificar junto con --replay o con --bench es un error de uso: el programa termina con código 1 sin verificar. --forzar no tiene efecto con --verificar ni con --replay." Agrega el escenario HU4-6 que lo prueba.
- A1: en FR-334 aclara que la medición empieza con el esqueleto ya cargado y la ubicación de las llaves en memoria (cargar el esqueleto es de P1 y la 001); el bench reporta la carga aparte, sin límite.

Tareas (tasks.md y, donde aplique, plan.md y contracts/):
- C1: T041 y T042 citan FR-336.
- U1: T038 fija que crear_partida(args) conserva su firma y su retorno de 4 valores y recibe un segundo parámetro opcional con la cripta ya preparada; si no se le da, la prepara ella misma SIN verificar. La verificación vive solo en main y en --verificar. T039 solo agrega llaves a los datos de las pruebas que pasan por main.
- G1: T030 comprueba que el Mapa no cambia; agrega una nota de que la parte de HU3-11 sobre el mapa conocido se prueba en la capacidad 002.
- G2: T011 solo comprueba la ubicación por enemigo; FR-321 queda en T031.
- F1: quita [P] de las tareas que comparten archivo con otra de su bloque.
- F2: en T021, "dos" → "tres".
- U2: T014 usa una cripta resoluble (cada salida a lo sumo dos veces) y agrega una no resoluble (a lo sumo tres).
- F3: R3 mide también la incremental con 500, 1 000 y 2 000 salas, para que sus cocientes se comparen con los de la ingenua en la misma tabla.
- G3: T050 primero lista las criptas con --listar y verifica la más grande con --verificar para que quede en cache/; si no hay ninguna publicada, se anota en DECISIONES.
- T050: no escribe en docs/resultados_bench_p2.txt (ahí están los números de la 001). Solo corre las secciones de resolubilidad y revisa que R2 y R3 cumplan; el bench completo se corre al final del proyecto.

**USO:** Arreglo y specificamiento del analize

**Promp:** /speckit-implement Solo las fases 1 y 2 (T001 a T010) de specs/003-resolubilidad/tasks.md. T001 ya está hecho (yo hice los commits de spec y plan): márcalo. Detente en el punto de control de la fase 2, marca las tareas hechas y no hagas commit.

**USO:** Implementacion de la fase 1 y 2 del punto 003

**Prompt:** /speckit-implement Solo la fase 3 (T011 a T018) de specs/003-resolubilidad/tasks.md. Detente en su punto de control, marca las tareas hechas y no hagas commit.

**USO:** Implementacion de la fase 3 del punto 003

**Prompt:** /speckit-implement Solo la fase 4 (T019 a T028) de specs/003-resolubilidad/tasks.md. Detente en su punto de control, marca las tareas hechas y no hagas commit.

**USO:** IMpplementacion del a fase 4 del punto 003

**Prompt:** /speckit-implement Solo la fase 5 (T029 a T040) de specs/003-resolubilidad/tasks.md. Detente en su punto de control, marca las tareas hechas y no hagas commit.

**USO:** Implementación de la fase 5 del punto 003

**Prompt:** /speckit-implement Solo la fase 6 (T041 a T043) de specs/003-resolubilidad/tasks.md. Detente en su punto de control, marca las tareas hechas y no hagas commit.

**USO:** Implementacion de la fase 6 del punto 003

