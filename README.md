
# CRIPTA — Proyecto I de Estructuras de Datos

Juego de exploración de mazmorras desarrollado en Python. Organiza la lógica del juego mediante Modelo, Vista, Controlador y Adaptadores, e incorpora estructuras de datos propias, persistencia, reproducción de partidas y pruebas de rendimiento.

## Segunda parte: terreno y cazador

La segunda parte se desarrolla con especificaciones de spec-kit (v1.3.1) y el agente Claude Code. La especificación, el plan y las tareas de esta capacidad están en `specs/001-terreno-cazador/`; las decisiones, en `DECISIONES.md` (secciones 5.1 y 5.2).

- **Costo de las salidas.** Cada salida tiene un costo de movimiento (100 si la cripta no lo dice). Moverse por ella tarda ese costo, para el jugador y para los enemigos. Una cripta con un costo inválido (0, decimal, texto o distinto en los dos lados) no se juega: el programa muestra la salida y el problema.
- **Cazadores.** Un enemigo nuevo que persigue al jugador por la ruta más barata si está dentro de su rango (que viene en su ficha del catálogo), y espera si no puede llegar.
- **En la pantalla**, cada salida muestra su costo, abierta o cerrada (`N: sala 3 (Abierta, costo 250)`), y los cazadores llevan la etiqueta `[cazador]`. El comando `ayuda` lo explica.

## Requisitos

- Python 3.11 o superior.
- Git (opcional, para clonar el repositorio).
- Conexión a Internet para obtener datos en modo online.
- Datos locales descargados previamente para utilizar el modo `--offline`.

## Instalación desde un entorno limpio

En una terminal de PowerShell:

```powershell
git clone https://github.com/YoelGustavo/Cripta_Estructuras_de_Datos.git
cd Cripta_Estructuras_de_Datos
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

La dependencia externa es `requests`, utilizada para las solicitudes HTTP a la API de CRIPTA.

El archivo `requirements.txt` debe contener:

```text
requests>=2.31,<3
```

Después de crear o actualizar ese archivo, instalar con:

```powershell
python -m pip install -r requirements.txt
```

Los módulos `json`, `os`, `struct`, `threading`, `time` y `uuid` pertenecen a la biblioteca estándar de Python y no deben añadirse a `requirements.txt`.

Todos los comandos siguientes se ejecutan desde la raíz del repositorio, donde está la carpeta `crypta`.

## Comandos principales

### Iniciar una partida

```powershell
python -m crypta.main
```

De forma predeterminada se utiliza la cripta `cripta-01`, el jugador `Aventurero` y una caché de 25 fichas.

### Consultar las criptas disponibles

```powershell
python -m crypta.main --listar
```

### Elegir una cripta, jugador y semilla

```powershell
python -m crypta.main --cripta cripta-01 --jugador Aventurero --semilla 12345
```

### Ajustar la capacidad de la caché

```powershell
python -m crypta.main --cache-size 25
```

La capacidad debe ser mayor que cero.

## Modo offline

```powershell
python -m crypta.main --offline --cripta cripta-01
```

Utiliza exclusivamente datos almacenados en disco, sin consultar el servicio HTTP.

Para funcionar necesita que los datos de esa cripta y del catálogo ya estén disponibles localmente. Se recomienda iniciar primero una partida online para descargar los datos necesarios.

El almacenamiento local utiliza la carpeta `cache/`, creada automáticamente en el directorio de trabajo.

Para listar criptas disponibles sin conexión:

```powershell
python -m crypta.main --offline --listar
```

## Guardar y cargar una partida

Dentro de la consola interactiva, escribe:

```text
guardar
```

Este comando crea dos archivos:

- `partida.cripta`: contiene el estado de la partida en formato binario.
- `partida.cripta.log`: contiene una copia de los comandos ejecutados hasta ese momento.

Para continuar desde el guardado, escribe:

```text
cargar
```

Ambos archivos deben mantenerse juntos y ser compatibles con la cripta y el catálogo activos.

El archivo usa la versión 2 del formato, que guarda el costo de cada salida. Las partidas guardadas con la primera parte (versión 1) no se cargan: el programa avisa que el formato no coincide.

El guardado se reemplaza al ejecutar `guardar` nuevamente.

## Registro y reproducción de partidas (--replay)

Al iniciar una partida normal se crea `partida.log` en el directorio de trabajo.

El archivo corresponde a la última partida y se reemplaza al iniciar otra. Se recomienda copiarlo si se desea conservarlo.

Para reproducirlo sin interacción por teclado:

```powershell
python -m crypta.main --replay partida.log
```

Para reproducirlo utilizando únicamente datos locales:

```powershell
python -m crypta.main --offline --replay partida.log
```

La reproducción comprueba la compatibilidad de los datos registrados. No se abre la interfaz interactiva.

## Pruebas de rendimiento (--bench)

Para ejecutar todos los benchmarks:

```powershell
python -m crypta.main --bench
```

Ejecuta los benchmarks definidos en `crypta/bench/bench.py` sin iniciar el juego, sin utilizar HTTP ni abrir la interfaz interactiva.

Los modos `--bench` y `--replay` no pueden utilizarse simultáneamente.

También se puede ejecutar directamente el módulo de benchmarks para elegir secciones, usar cargas reducidas o guardar los resultados.

### Ejecutar todas las secciones

```powershell
python -m crypta.bench.bench
```

### Ejecutar solo agenda y guardado

```powershell
python -m crypta.bench.bench agenda guardado
```

### Ejecutar con tamaños pequeños

```powershell
python -m crypta.bench.bench --rapido
```

### Guardar los resultados en un archivo de texto

```powershell
python -m crypta.bench.bench --guardar docs/resultados_bench.txt
```

### Secciones disponibles

- `agenda`: agenda de eventos.
- `ciclo`: ciclo entre dos decisiones.
- `cache`: caché de fichas.
- `inventario`: inventario e historial.
- `rastro`: rastro del jugador.
- `ordenamiento`: algoritmos de ordenamiento.
- `red`: bitácora y solicitudes de red.
- `guardado`: comparación entre almacenamiento binario y JSON.

Secciones de la segunda parte (cazador y costos de las salidas):

- `cazadores`: B1, un cazador frente a 50.
- `rangos`: B2, rango pequeño frente a rango grande.
- `tamano`: B3, la misma región en criptas de 2000 y 20000 salas.
- `compartido`: B4, una búsqueda compartida frente a una por cazador.
- `reutilizar`: B5, reutilizar la búsqueda frente a recalcular siempre.
- `equivalencia`: B6, compara cada decisión con un cálculo desde cero. Si alguna difiere, imprime `ERROR` y el programa termina con código 1.
- `ciclo_cazadores`: B7, ciclo con 50 cazadores (p95 menor que 20 ms).
- `escala`: B8, ciclo con 10, 25, 50 y 100 cazadores.
- `distancias`: B9, vectores con marca frente a `ArbolBusqueda`.

Las criptas de estas secciones son sintéticas y se generan igual con la misma semilla. Los resultados de la segunda parte están en `docs/resultados_bench_p2.txt`; `docs/resultados_bench.txt` es el de la primera parte.

```powershell
python -m crypta.bench.bench cazadores rangos tamano compartido reutilizar equivalencia ciclo_cazadores escala distancias --guardar docs/resultados_bench_p2.txt
```

La sección `guardado` compara los formatos binario y JSON con criptas sintéticas de 100, 1000 y 5000 salas.

Con `--rapido` se utiliza únicamente una cripta de 100 salas.

Se comparan los siguientes aspectos:

- Tamaño de los archivos.
- Tiempo de carga completa.
- Tiempo de lectura de una sala.
- Cantidad de bytes leídos.

Los resultados se muestran en consola de forma predeterminada.

Con `--guardar RUTA`, también se escriben en el archivo indicado. El programa crea la carpeta contenedora si no existe.

Los archivos `partida.bin` y `partida.json` utilizados durante la comparación se crean en una carpeta temporal y se eliminan al finalizar la medición.

## Pruebas unitarias

Las pruebas están en la carpeta `tests` de la raíz. Para correrlas todas:

```powershell
python -m unittest
```

Solo las de la segunda parte (terreno y cazador):

```powershell
python -m unittest -v tests.test_terreno tests.test_cazador tests.test_distancias_limitadas tests.test_equivalencia_cazador
```

`tests.test_terreno` incluye `TestCompatibilidadP1`, que repite una partida grabada con la primera parte (`tests/datos/p1_partida.log`) y comprueba que una cripta sin costos se juega igual.

## Archivos generados y persistencia

| Archivo o dato | Ubicación y descripción |
|---|---|
| Registro de la última partida | `partida.log`. Se crea en el directorio de trabajo y se reemplaza al iniciar otra partida. |
| Tabla de puntajes | `puntajes.txt`. Almacena los puntajes registrados. |
| Fichas del catálogo | `cache/catalogo.json`. Contiene la versión del catálogo y las fichas descargadas. |
| Copias locales de criptas | `cache/<id-de-cripta>.json`, por ejemplo, `cache/cripta-01.json`. Contiene la versión, el esqueleto, los contenidos y los datos generales disponibles. |
| Partida guardada | `partida.cripta`. Archivo binario generado mediante el comando `guardar`. |
| Registro asociado al guardado | `partida.cripta.log`. Copia del registro correspondiente al momento de guardar. |
| Guardado JSON alternativo | Archivo `.json` cuya ruta se indica al invocar el adaptador `GuardadoJSON.py`. |
| Resultados de benchmarks | Se muestran en consola y opcionalmente se guardan en `docs/resultados_bench.txt` o en otra ruta indicada. |

Las rutas relativas corresponden al directorio desde el que se ejecuta el programa.

## Formatos de guardado de partidas

El proyecto implementa dos adaptadores de persistencia, aunque el comando interactivo `guardar` utiliza el formato binario.

### Guardado binario

Archivo:

```text
crypta/Adaptadores/GuardadoBinario.py
```

En el juego se utiliza el archivo `partida.cripta`.

Durante los benchmarks se utiliza la extensión `.bin`.

Este formato contiene:

- Encabezado de la partida.
- Estado general.
- Registros individuales de las salas.
- Índice ordenado de las salas.

El índice permite consultar una sala sin cargar todas las demás.

También permite recuperar la partida completa para continuar jugando.

### Guardado JSON

Archivo:

```text
crypta/Adaptadores/GuardadoJSON.py
```

Utiliza archivos con extensión `.json`.

Almacena:

- Encabezado de la partida.
- Estado general.
- Lista de salas.

Para acceder a una sala, el adaptador carga el documento JSON completo en memoria.

### Escritura segura y recuperación

Ambos métodos escriben primero en un archivo temporal con sufijo `.tmp` y después lo reemplazan por el archivo definitivo.

En el juego, el controlador guarda por defecto en `partida.cripta` y crea también `partida.cripta.log`.

El comando `cargar` recupera el guardado y verifica que su registro asociado exista y corresponda a:

- La misma cripta.
- La misma versión de la cripta.
- La misma versión del catálogo.
- La misma semilla.
- El mismo jugador.

Las rutas personalizadas corresponden a llamadas directas a los adaptadores.

Estos archivos son distintos de `partida.log`, que registra comandos para el modo `--replay`.

## Organización del código

- `crypta/Modelo/`: entidades, estado y reglas del juego.
- `crypta/Vista/`: presentación e interacción por consola.
- `crypta/Controlador/`: coordinación de la partida y sus acciones.
- `crypta/Adaptadores/`: acceso HTTP, almacenamiento local, guardado y registros.
- `crypta/estructuras/`: implementaciones propias de estructuras de datos.
- `crypta/bench/`: pruebas y mediciones de rendimiento.
- `crypta/main.py`: punto de entrada y argumentos de línea de comandos.

Las pruebas unitarias se encuentran en sus carpetas correspondientes según la organización del repositorio.

## Registro de uso de inteligencia artificial

Las consultas realizadas a herramientas de inteligencia artificial se documentan en el archivo `PROMPTS_LLM.md`.

## Ayuda de línea de comandos

Para consultar los argumentos disponibles:

```powershell
python -m crypta.main --help
```
