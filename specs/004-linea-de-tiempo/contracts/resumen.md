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
Mapa conocido: <E> exploradas, <A> avistadas
  <id> <nombre>
    <dir>: sala <destino>, costo <costo>, <abierta|cerrada>
  ...
  Avistadas: <id>, <id>, ... | ninguna
[Aviso: <texto de FR-415>]
```

Reglas:

- `<pedido>` es `instante <t>` o `acción #<k>`, tal como lo pidió el jugador.
- Los efectos van en el orden fijo veneno, antorcha, velocidad.
- El inventario va en su orden real (`Inventario.orden_real`).
- Los enemigos van en el orden del `Vector` de la sala; solo se listan los activos y vivos.
- Los números son enteros sin separador de miles.
- El texto termina con un salto de línea.
- El mapa conocido es el **del estado consultado**, no el actual (HU1-11). Sus líneas son las de
  `mapa` de la capacidad 002 (`crypta/Vista/FormatoMapa.lineas_mapa`) sin su encabezado: salas
  exploradas por id, sus salidas en N, S, E, O con el estado recordado, y las avistadas solo por su
  id (specs/002-niebla-ir-a/contracts/vista.md «Resumen»; FR-228 de la 002). Hasta la 002 la línea
  era fija: «Mapa conocido: no disponible (capacidad 002)».
- La línea de aviso solo aparece en el caso de FR-415.
