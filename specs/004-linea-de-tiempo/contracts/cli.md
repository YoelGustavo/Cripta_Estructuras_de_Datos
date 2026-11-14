# Contrato: comandos y argumentos (FR-403 a FR-405, FR-409, FR-413 a FR-416, FR-418, FR-420)

## Comando `historia` durante la partida

| Entrada | Resultado | ¿Cambia algo? |
|---|---|---|
| `historia <t>`, con t entero ≥ 0 y t ≤ reloj | resumen del estado en t (contracts/resumen.md) | no (FR-407) |
| `historia <t>`, con t > reloj | mensaje: `No se puede consultar el instante <t>: el reloj de la partida va en <reloj>.` | no |
| `historia #k`, con 1 ≤ k ≤ n + 1 | resumen del estado antes de la acción #k | no |
| `historia #k` fuera de rango | mensaje: `No hay acción #<k>: la partida tiene <n> acciones (consulta de #1 a #<n+1>).` | no |
| `historia`, `historia abc`, `historia -5`, `historia 2,5`, `historia #x`, `historia 3 4` | `ComandoInvalido`: el mismo tratamiento que un comando inválido de P1 | no |
| `historia …` con la partida terminada | mensaje: `La partida terminó: usa --replay <log> --hasta <t> para consultarla.` | no |

- Sin signo ni espacios internos: t y k tienen que ser dígitos ASCII.
- `historia` no se anota en `partida.log` ni pasa por `ejecutar_comando`.
- La ayuda de la vista agrega la línea `historia <t> | #k   Ver cómo estaba la partida`.

## Argumentos nuevos

| Argumento | Valores | Error de argumentos (código 2 de `argparse`, sin iniciar partida) |
|---|---|---|
| `--checkpoint-cada K` | entero ≥ 1. Sin la bandera, el K por defecto (research D4), que aparece en `--help` | `0`, `-3`, `x`, `2.5` |
| `--hasta t` | entero ≥ 0. Solo con `--replay` | sin `--replay`, `-1`, `x` |

- `--checkpoint-cada` se usa al jugar y en `--replay`.
- Al cargar una partida guardada con otro K, se avisa
  `La partida guardada usa --checkpoint-cada <K_guardado>; se usa ese valor.` y se sigue con el K
  guardado (FR-418).

## `--replay <log> --hasta t`

| Caso | Salida | Código |
|---|---|---|
| El log se reproduce y t ≤ reloj final | resumen del estado en t | 0 |
| t > reloj final y la partida terminó | resumen del último estado + `La partida terminó en el instante <r>, antes de <t>.` | 0 |
| t > reloj final y la partida no terminó | resumen del último estado + `El log termina en el instante <r>, antes de <t>.` | 0 |
| Log ilegible, incompatible o que no se puede repetir | mismo mensaje que `--replay` hoy | 1 |

- No se instancia la vista (FR-414).
- El resumen se imprime con `FormatoResumen` directamente en la salida estándar.
