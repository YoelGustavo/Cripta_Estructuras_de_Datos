"""La verificación de resolubilidad antes de jugar (capacidad 003; research
D9; contracts/cli.md).

La usan `main` al iniciar una partida y `--verificar`. Solo recibe el
gestor de la cripta (esqueleto y llaves) y el Mapa: nunca el
GestorContenido, así que no puede pedir contenido de salas (FR-321).
"""

from crypta.Modelo.ResultadoVerificacion import NoVerificable
from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
from crypta.Modelo.Verificador import verificar
from crypta.Vista.FormatoVerificacion import ENCABEZADO, texto_resultado


# Códigos de salida (FR-325, FR-329).
RESOLUBLE = 0
NO_VERIFICABLE = 1
NO_RESOLUBLE = 2


def preparar_verificacion(gestor_cripta, cripta_id, datos_cripta, mapa):
    """`ResultadoVerificacion`, o `NoVerificable` si no se pudo obtener la
    ubicación de las llaves (FR-324). Una ubicación inválida lanza
    `DatosInvalidos` (FR-319). `gestor_cripta.cargar` ya se llamó."""
    llaves = gestor_cripta.cargar_llaves(cripta_id)

    if isinstance(llaves, NoVerificable):
        return llaves

    return verificar(mapa, datos_cripta, leer_ubicaciones(llaves, mapa))


def texto_de(resultado):
    """El texto que se muestra (contracts/reporte.md)."""
    if isinstance(resultado, NoVerificable):
        return (f"{ENCABEZADO}no se pudo verificar ({resultado.motivo}). "
                f"Se trata como no resoluble.")

    return texto_resultado(resultado)


def codigo_de(resultado):
    """0 si es resoluble, 2 si no lo es, 1 si no se pudo verificar."""
    if isinstance(resultado, NoVerificable):
        return NO_VERIFICABLE

    return RESOLUBLE if resultado.resoluble else NO_RESOLUBLE
