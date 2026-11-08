# Contrato: datos que llegan del servicio (o de la copia local)

Referencia exacta del HTTP: Swagger del servicio. Esto fija **cómo los interpreta el programa**
(P2 §4.1, Apéndice A). No hay solicitudes nuevas (FR-027).

## Salida en el esqueleto — `GET /criptas/<id>/salas?pagina=n`

```json
"salidas": {
  "N": { "sala": 3 },
  "E": { "sala": 7, "costo": 250, "cerrada": true,
         "llave": "itm_llave_bronce", "cierre_automatico": 500 }
}
```

| Caso | Resultado |
|---|---|
| Ningún lado de la salida trae `costo` | costo 100 |
| Solo un lado trae `costo` = c (entero ≥ 1) | costo c en ambos sentidos |
| Ambos lados traen el mismo c | costo c |
| Ambos lados traen costos distintos | `DatosInvalidos`: «La salida entre las salas A (dir) y B (dir) declara costos distintos: x y y» |
| `costo` < 1, `float` (incluso `250.0`), `bool`, texto o `null` explícito | `DatosInvalidos`: «La salida <dir> de la sala A tiene un costo inválido: <valor>» |

Validez: mientras coincida la versión de la cripta; se persiste con el esqueleto.

## Ficha de cazador — `GET /catalogo?ids=...`

```json
{ "id": "ent_sabueso_oseo", "clase": "enemigo", "comportamiento": "cazador",
  "vida_max": 18, "ataque": 6, "defensa": 2, "velocidad": 120, "rango": 600, "suelta": [] }
```

| Caso | Resultado |
|---|---|
| `rango` entero ≥ 0 | válido (0 incluido) |
| Falta `rango`, o es negativo, `float`, `bool`, texto o `null` | `DatosInvalidos`: «La ficha <id> (cazador) tiene un rango inválido o ausente: <valor>» |
| La ficha inválida llega antes de iniciar | No se inicia la partida |
| La ficha inválida llega con la partida iniciada | La sesión termina de forma controlada con el mismo mensaje; `partida.log` queda escrito |

Validez: mientras coincida la versión global del catálogo; se persiste con la ficha.

`comportamiento` distinto de `errante`, `rastreador` y `cazador` mantiene la regla de P1 (no se
cambia en esta capacidad).
