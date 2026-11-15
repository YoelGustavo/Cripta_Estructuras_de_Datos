# Contrato: comandos `mapa` e `ir a`, y `partida.log` (FR-210, FR-211, FR-216 a FR-223)

## `mapa`

- Exactamente la palabra `mapa` (sin distinguir mayúsculas, como los otros comandos de consola).
- Muestra el texto de [vista.md](vista.md#mapa).
- No es acción, no consume tiempo, no va a `partida.log`, no pide nada a la red, no cambia nada
  (FR-211). Lo atiende el `Controlador` antes de traducir, como `historia`.
- `mapa 3` (o cualquier argumento): sigue el camino de un comando que no se entiende, igual que en
  P1 → `ComandoInvalido` con su mensaje; nada cambia.

## `ir a <sala>`

Gramática: tres palabras separadas por espacios: `ir`, `a`, y la sala en dígitos ASCII (sin signo).
Cualquier otra forma (`ir`, `ir a`, `ir a x`, `ir a -3`, `ir a 3 4`, `ir b 3`) es `ComandoInvalido`
(FR-216, HU3-3).

Rechazos (FR-216): `AccionInvalida`, sin consumir tiempo, sin anotar nada en el log ni en la línea
de tiempo.

| Caso | Mensaje |
|---|---|
| La sala no existe o no está explorada | `No conoces la sala <id>.` (el mismo texto en los dos casos) |
| Es la sala actual | `Ya estás en la sala <id>.` |
| Explorada, sin ruta conocida | `No conoces una ruta abierta hasta la sala <id>.` |

Ejecución (`Comandos.ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar_sala,
anotar_comentario)`): por cada paso,

1. pide la dirección a `Viaje.siguiente_direccion`; sin ruta → se detiene (`SIN_RUTA`);
2. `garantizar_sala` del destino del paso, **antes** del `mover`; si lanza `RuntimeError` → se
   detiene (`PASO_IMPOSIBLE`) sin mover. Es la única fuente de `PASO_IMPOSIBLE`;
3. si es el primer paso, `anotar_comentario("ir a <id>")`;
4. `ejecutar_paso("mover <d>")`. En el `Controlador` es `_ejecutar_comando_jugador`: exactamente
   lo mismo que un `mover` escrito a mano (`_asegurar_linea`, ejecutar, línea de tiempo,
   `registro.anotar`, `_actualizar_fichas_en_uso`, `precargar_async`). Un error que salga de aquí no
   es una parada: sale de `ejecutar_ir_a` y `procesar_comando` lo muestra como con cualquier comando;
5. `Viaje.despues_del_paso`.

Un viaje de n pasos hace las mismas solicitudes a la red que los n `mover` escritos a mano
(principio V).

Al terminar, la vista muestra el motivo (texto en [vista.md](vista.md#motivos-de-parada)) y después
el estado, como tras cualquier comando.

## `partida.log`

- Formato de registro **1**, sin cambios en el encabezado.
- Cada paso de un viaje es una línea `mover <d>` (FR-222).
- La orden va como comentario **antes del primer `mover`** del viaje: `# ir a <id>`. Un viaje sin
  pasos no deja ninguna línea.
- Después de `---`, toda línea que empieza con `#` es un comentario: `leer_registro` la ignora, así
  que `--replay` y `--replay … --hasta` no la ven (FR-223).
- Los logs de P1 y de la 001 no tienen comentarios y se leen igual (SC-206).

Ejemplo:

```text
# CRIPTA registro de partida
formato 1
cripta …
…
---
esperar
# ir a 7
mover E
mover E
mover N
abrir S
```
