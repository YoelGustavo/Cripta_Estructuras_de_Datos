# Contrato: archivo de partida, formato 4 (FR-226, FR-227)

Formato 4 en `GuardadoBinario` (`FORMATO_GUARDADO = 4`) y en `GuardadoJSON` (`FORMATO_JSON = 4`).
Todo lo del formato 3 de la 004 sigue igual (encabezado, bloque general, registros de sala, bloque
`linea`, índice, cabecera de 22 bytes). Se agregan dos campos, escritos con los métodos del
escritor abstracto:

```text
general
  …                         (igual que en el formato 3)
  conocimiento: grupo
    salas: lista            (solo las no desconocidas, en orden de índice = orden de id)
      sala: entero
      estado: entero        (1 avistada, 2 explorada)

sala
  …
  puertas: lista
    direccion, destino, cerrada, llave, cierre_automatico, costo   (igual)
    recordada: entero       (0 nunca observada, 1 abierta, 2 cerrada)
  …
```

- Los dos lados de una salida escriben el mismo `recordada` (comparten el `EstadoPuerta`).
- Los puntos de control de la 004 se escriben con `escribir_general` y `escribir_sala`, así que
  llevan su propio conocimiento sin cambios en `escribir_linea`.
- Firmas sin cambios: `guardar_partida(partida, ruta, encabezado, linea=None)`,
  `ArchivoGuardado(ruta).cargar_partida(fichas)` y sus versiones JSON.

## Al cargar

- `leer_sala` lee `recordada` y lo pasa a `Puerta`. `compartir_estado_con` exige que los dos lados
  coincidan; si no, `DatosInvalidos` → `ErrorGuardado`.
- `armar_partida` crea el `MapaConocido` y llama a `restaurar(lista)`, que valida:
  - cada `sala` existe y aparece una sola vez, en orden creciente;
  - cada `estado` es 1 o 2;
  - la sala inicial está explorada (FR-201);
  - una sala es avistada si y solo si no está explorada y es destino de una salida de una sala
    explorada (FR-202);
  - cada salida de una sala explorada tiene `recordada` distinto de 0 (FR-203, FR-204).

  Si algo falla, `ErrorGuardado` con la sala.
- Una partida cargada no trae `RutaConocida`: la crea en el primer `ir a` (research D7).

## Rechazos (FR-227)

- Formatos 1 (P1), 2 (001) y 3 (004, sin mapa conocido): `ErrorGuardado` con el mensaje que ya
  existe, «Formato incompatible: la partida se guardó con la versión <v> del formato[ JSON] y este
  programa lee la versión 4; no se puede cargar». La partida en curso no cambia.
- Nunca se migra.
