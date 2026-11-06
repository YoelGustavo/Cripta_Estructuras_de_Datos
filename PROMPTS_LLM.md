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