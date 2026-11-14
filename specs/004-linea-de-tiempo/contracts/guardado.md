# Contrato: archivo de partida, formato 3 (FR-417 a FR-419)

Formato 3 en `GuardadoBinario` (`FORMATO_GUARDADO = 3`) y en `GuardadoJSON` (`FORMATO_JSON = 3`).
Se mantienen, sin cambios, el encabezado, el bloque general, los registros de sala y el índice. Se
agrega un bloque `linea`, escrito con los mismos métodos del escritor abstracto (`entero`, `texto`,
`empezar_grupo`, `empezar_lista`…). En el binario va después de los registros de sala y la cabecera
guarda su posición y su largo.

```text
linea
  k: entero
  entradas: lista
    tipo: entero (0 acción, 1 no acción, 2 ajuste)
    comando: texto
    reloj: entero
    numero_accion: entero
    pergaminos_inventario, posicion_actual, pergaminos_sala: entero_opcional (solo en ajuste)
  puntos: lista
    ancla: entero
    posicion: entero
    general: grupo con escribir_general(e, punto.partida)
    salas: lista con escribir_sala(e, sala) de cada sala del mapa del punto
```

Firmas (no cambian; las llamadas existentes siguen igual):

- `guardar_partida(partida, ruta, encabezado, linea=None)` y `guardar_partida_json(…, linea=None)`.
  Sin línea se escribe un bloque `linea` **vacío**: solo `k`, con las listas `entradas` y `puntos`
  vacías.
- `ArchivoGuardado(ruta).cargar_partida(fichas)` y `ArchivoGuardadoJSON(ruta).cargar_partida(fichas)`
  siguen devolviendo **solo la partida**. La línea leída queda en el atributo `linea` del objeto
  lector (no de la `Partida`, research D12); si el bloque estaba vacío, `linea` es `None`.
- El `Controlador` toma `archivo.linea`. Si es `None`, crea una línea nueva con el punto inicial en
  el estado cargado (ancla a₀ = acciones del estado cargado, data-model.md).

Al cargar:

- Cada punto se arma con `armar_partida`, con las fichas del repositorio, un historial sin límite y
  una bitácora vacía (research D3).
- `decisiones` se reconstruye recorriendo las entradas una vez, en O(n).
- Se valida que las anclas sean a₀, a₀ + K, a₀ + 2K… sin huecos, que las posiciones sean
  crecientes y que los relojes suban estrictamente. Si algo falla, `ErrorGuardado`.

Rechazos (FR-419):

- Formato 1 (P1) o 2 (001): `ErrorGuardado` con el mensaje de formato incompatible que ya existe. La
  partida en curso no cambia.
- Un archivo cortado o inconsistente también da `ErrorGuardado`.
- Nunca se migra.

K: se usa el guardado. Si `--checkpoint-cada` dice otro, se avisa (contracts/cli.md).
