class DatosInvalidos(Exception):
    """Los datos de la cripta o del catálogo no cumplen el contrato
    (FR-010, FR-011; contracts/datos-servicio.md).

    No hereda de ValueError ni de RuntimeError a propósito: el Controlador
    trata ValueError como un comando inválido y RuntimeError como un error
    de red, y esto no es ninguna de las dos cosas. El mensaje nombra la
    salida o la ficha y el problema, por ejemplo:

        La salida E de la sala 3 tiene un costo inválido: 0
    """
