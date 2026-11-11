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
