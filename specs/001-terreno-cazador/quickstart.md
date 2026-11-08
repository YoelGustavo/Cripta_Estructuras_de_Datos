# Guía de validación: Terreno y cazador

Cómo comprobar de punta a punta que la capacidad funciona. Detalle de datos en
[data-model.md](data-model.md) y de formatos en [contracts/](contracts/).

## Requisitos

- Python 3.11 o superior, desde la raíz del repositorio.
- Sin dependencias nuevas (`requirements.txt` no cambia).

## 1. Todas las pruebas (incluidas las de la primera parte)

```powershell
python -m unittest
```

Esperado: todo en verde (SC-001, SC-003). Las pruebas nuevas citan su FR en el nombre o en el
docstring.

## 2. Solo las pruebas de esta capacidad

```powershell
python -m unittest tests.test_terreno tests.test_cazador tests.test_equivalencia_cazador tests.test_distancias_limitadas
```

## 3. Revisión de imports prohibidos (principio I)

```powershell
git grep -n -E "import (heapq|bisect|collections|networkx)|from (heapq|bisect|collections|networkx)" -- crypta
```

Esperado: ninguna línea. Además, revisar a mano que las estructuras nuevas no usen `dict` ni `set`.

## 4. La primera parte sigue igual (FR-008, SC-003)

Repetir un `partida.log` de la primera parte sobre una cripta sin campo `costo`. El archivo
`tests/datos/p1_partida.log` todavía no existe: una tarea lo graba con el código actual (antes de
cualquier cambio de esta capacidad) junto con el estado final esperado.

```powershell
python -m crypta.main --offline --replay tests/datos/p1_partida.log
```

Esperado: el mismo resultado y el mismo estado final que en la primera parte (la prueba
`test_terreno.TestCompatibilidadP1` lo compara automáticamente).

## 5. Mediciones

```powershell
python -m crypta.main --bench
```

Esperado (ver [contracts/bench.md](contracts/bench.md)):

- B3: cociente de tiempo 20 000 / 2 000 salas < 2 → «sí».
- B6: 0 diferencias entre reutilizar y recalcular.
- B7: p95 del ciclo con 50 cazadores < 20 ms → «sí».
- B8: cociente por cazador (100 / 10) ≤ 2 → «sí».
- Ninguna ventana de la vista se abre y no hay tráfico de red.

Ejecutarlo dos veces con la misma semilla debe generar las mismas criptas (la huella impresa coincide).

## 6. Prueba manual en el juego

1. Iniciar una partida contra una cripta de la segunda parte.
2. En la vista, cada salida de la sala muestra su costo; los cazadores aparecen con `[cazador]`.
3. Moverse por una salida cara y comprobar que los enemigos actúan más veces antes del siguiente
   turno.
4. Guardar, cargar y verificar que los costos y los cazadores siguen igual.
