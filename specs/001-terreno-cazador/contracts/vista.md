# Contrato: lo que muestra la vista de consola (FR-009, FR-022, SC-007)

Se amplía `VistaConsola.mostrar_estado`. El formato exacto del texto no es estado del juego; las
pruebas comprueban que aparezca la información, no la línea completa.

## Salidas de la sala actual

Cada salida muestra su costo, esté abierta o cerrada:

```text
Salidas:
  N: sala 3 (Abierta, costo 100)
  E: sala 7 (Cerrada, necesita itm_llave_bronce, costo 250)
```

## Enemigos presentes

Los cazadores se marcan con la etiqueta `[cazador]`; los demás enemigos no llevan etiqueta nueva:

```text
Enemigos:
  1. Sabueso óseo [e-1203] [cazador] - Vida: 18/18
  2. Rata [e-0402] - Vida: 5/5
```

La ayuda (`mostrar_ayuda`) agrega una línea que explica la etiqueta `[cazador]` y que el número de
cada salida es su costo de movimiento.

`--replay`, `--bench` y `--verificar` no instancian la vista (principio III).
