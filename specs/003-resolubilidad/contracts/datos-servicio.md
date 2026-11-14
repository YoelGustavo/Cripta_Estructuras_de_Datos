# Contrato: ubicación de las llaves (P2 §4.2, FR-319, FR-322 a FR-324)

## Solicitud

`GET /criptas/<id>/llaves` (Swagger del servicio es la referencia exacta). Cuenta en
`presupuesto_solicitudes`, incluidos los reintentos de un 429 (principio V). Se hace a lo sumo una
vez por versión de cripta mientras la copia local sea válida (SC-306).

## Respuesta aceptada

```json
{
  "llaves": [
    { "id": "itm_llave_bronce", "sala": 4 },
    { "id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203" }
  ]
}
```

| Campo | Regla | Si falla |
|---|---|---|
| raíz | objeto con `llaves` lista | `DatosInvalidos` |
| `id` | texto no vacío | `DatosInvalidos` (entrada n) |
| `sala` | entero JSON (no `bool`, no `float`, no texto) de una sala del esqueleto | `DatosInvalidos` (entrada n, id, sala) |
| `enemigo` | ausente, null o texto | `DatosInvalidos` |
| campos extra | se ignoran | — |

Lista vacía es válida (ninguna llave ubicada). Entradas repetidas son válidas.

No se comprueba que el enemigo exista ni que inicie en esa sala: exigiría pedir contenido (FR-321).

## Interfaz de las fuentes

| Método | `FuenteHTTP` | `FuenteOffline` | `FuenteDatos` (por omisión) |
|---|---|---|---|
| `obtener_llaves(cripta_id)` | `_get("/criptas/<id>/llaves")`; puede lanzar `PresupuestoAgotado` o `RuntimeError` | lee el campo `llaves` de la copia local; si no está, `LlavesNoDisponibles` | `LlavesNoDisponibles` |

`LlavesNoDisponibles` (nueva, en `crypta/Adaptadores/FuenteDatos.py`) hereda de `RuntimeError`.
`GestorCripta.cargar_llaves` traduce las tres excepciones en `NoVerificable(motivo)`.

## Copia local

`AlmacenDisco.guardar_cripta(…, llaves=None)` escribe el campo `llaves` en `cache/<cripta>.json`
junto a `version`. `GestorCripta.cargar` conserva las `llaves` de la copia si la versión coincide;
una copia de otra versión ya se descarta entera (P2 §4.3, nunca se borran archivos a mano).
