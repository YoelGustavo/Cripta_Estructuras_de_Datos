# Contrato: texto del resumen (FR-406)

Lo arma `crypta/Vista/FormatoResumen.formatear_resumen(resumen)` y devuelve un `str`. Es el mismo
para `historia`, para `--replay … --hasta` y después de cargar. No incluye el reloj actual de la
partida.

```text
HISTORIA <pedido>
Reloj: <reloj del estado>   Próxima acción: #<k>
Sala: <id> <nombre>
Vida: <vida>/<vida_max>   Ataque: <ataque>   Defensa: <defensa>   Velocidad: <velocidad>
Efectos: <ninguno | veneno hasta <t>, antorcha hasta <t>, velocidad <cambio con signo, p. ej. +30> hasta <t>>
Inventario (<ocupados>/<capacidad>):
  <i>. <nombre> (<id>)[ [arma equipada]| [armadura equipada]][ <- actual]
  ...
  Pergaminos: <cantidad>
Enemigos en la sala: <ninguno>
  <id_instancia> <nombre>: vida <vida>
  ...
Mapa conocido: <lo que defina la 002 | no disponible (capacidad 002)>
[Aviso: <texto de FR-415>]
```

Reglas:

- `<pedido>` es `instante <t>` o `acción #<k>`, tal como lo pidió el jugador.
- Los efectos van en el orden fijo veneno, antorcha, velocidad.
- El inventario va en su orden real (`Inventario.orden_real`).
- Los enemigos van en el orden del `Vector` de la sala; solo se listan los activos y vivos.
- Los números son enteros sin separador de miles.
- El texto termina con un salto de línea.
- La línea del mapa conocido se completa cuando exista la 002 (research D10). Hasta entonces es
  fija.
- La línea de aviso solo aparece en el caso de FR-415.
