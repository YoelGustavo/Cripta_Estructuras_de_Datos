# Contrato: archivo de partida (FR-026)

## Cambios

- Binario (`GuardadoBinario.py`): `FORMATO_GUARDADO` pasa de 1 a 2.
- JSON del `--bench` (`GuardadoJSON.py`): `FORMATO_JSON` sube una versión, con el mismo cambio.
- En cada puerta escrita por `EstadoPartida.escribir_sala`, después de `cierre_automatico`:
  `entero("costo", puerta.costo)`.
- `leer_sala` lee `costo` y lo pasa a `Puerta`; al compartir estado entre los dos lados, los valores
  deben coincidir (si no, el archivo está dañado: `ErrorGuardado`).

## Lo que NO se escribe

- El rango de los cazadores: sale de la ficha; la carga ya exige la misma `version_catalogo`.
- Las búsquedas de ruta (distancias, frontera, id de cálculo): no son estado del juego (research D6).

## Compatibilidad

- Un archivo con formato 1 se rechaza con el mensaje actual («La partida se guardó con la versión 1
  del formato y este programa lee la versión 2: no se puede cargar»). Nunca se carga en silencio
  (principio XI).
- La especificación de la línea de tiempo puede volver a subir el formato; la migración explícita,
  si se decide hacerla, se especifica allí (P2 §3.6).
