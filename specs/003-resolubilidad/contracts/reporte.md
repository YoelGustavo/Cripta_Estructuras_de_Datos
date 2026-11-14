# Contrato: texto de la verificación (FR-306, FR-309 a FR-318, FR-320)

Lo produce `crypta/Vista/FormatoVerificacion.py` (función pura del `ResultadoVerificacion`). Es el
mismo texto en `--verificar`, al iniciar una partida y en la comparación del bench. Debe ser
idéntico byte por byte entre ejecuciones (SC-305).

Reglas comunes:

- Solo caracteres ASCII más letras acentuadas del español; la flecha es `->` (la consola de Windows
  redirigida a archivo no siempre acepta `→`).
- Sangría de dos espacios para cada elemento; una línea por elemento.
- Una sección vacía muestra `  (ninguna)`.
- Las salas se muestran por id; las llaves por id completo.

## Cripta resoluble (FR-306)

Ejemplo de HU1-1:

```text
Verificación de resolubilidad: la cripta es resoluble.
Orden de llaves:
  Ronda 1: itm_llave_a, itm_llave_c
  Ronda 2: itm_llave_b, itm_llave_salida
```

Solo ids, agrupados por ronda, en el orden de las rondas y por id dentro de cada una (FR-308).

## Cripta no resoluble (FR-316: este orden de secciones)

Ejemplo de HU2-1:

```text
Verificación de resolubilidad: la cripta NO es resoluble.
Llaves que no se pueden obtener:
  itm_llave_salida
Frontera bloqueada:
  sala 1, E -> sala 2, pide itm_llave_salida
Dónde están las llaves de la frontera:
  itm_llave_salida: sala 2
Dependencias:
  itm_llave_salida depende de itm_llave_salida
Ciclos de dependencia:
  itm_llave_salida -> itm_llave_salida
```

Formas de cada línea:

| Sección | Línea | FR |
|---|---|---|
| Llaves que no se pueden obtener | `  <id>` | FR-309 |
| Frontera bloqueada | `  sala <origen>, <N\|S\|E\|O> -> sala <destino>, pide <llave>` | FR-310 |
| Dónde están las llaves de la frontera | `  <llave>: sala <s1>, sala <s2> (la suelta <enemigo>), …` o `  <llave>: no está en la cripta` | FR-311 |
| Dependencias | `  <llave> depende de <llave>` | FR-312, FR-314 |
| | `  <llave> no depende de ninguna: no está en la cripta` | |
| | `  <llave> no depende de ninguna: su sala no se alcanza ni abriendo todas las puertas` | |
| Ciclos de dependencia | `  <k1> -> <k2> -> … -> <k1>` (empieza y termina en la de menor id) | FR-315 |

Líneas finales, solo si aplican, en este orden (FR-316):

```text
Falta sala_salida en la cripta.
Falta llave_salida en la cripta.
Se puede obtener <llave_salida>, pero ninguna puerta que la pide lleva a la sala <sala_salida> desde la región alcanzable.
```

(Primera y segunda: FR-318; tercera: FR-317.)

## No se pudo verificar (FR-324)

```text
Verificación de resolubilidad: no se pudo verificar (<motivo>). Se trata como no resoluble.
```

`<motivo>`: `sin conexión y sin la ubicación de las llaves en la copia local`, `falla de red: …` o
`presupuesto de solicitudes agotado`.

## Datos inválidos (FR-319)

```text
La cripta no se puede jugar: la ubicación de llaves tiene un dato inválido: entrada <n> (<id>): <problema>
```

Usa el mismo prefijo que la 001 para `DatosInvalidos`.

## Línea de decisión al iniciar partida (FR-325)

Después del texto anterior, solo en el inicio de partida (no en `--verificar`):

- Resoluble: nada más; la partida inicia.
- No resoluble o no verificable, sin `--forzar`: `La partida no inicia. Use --forzar para jugarla de todos modos.`
- Con `--forzar`: `Se inicia la partida por --forzar.`
