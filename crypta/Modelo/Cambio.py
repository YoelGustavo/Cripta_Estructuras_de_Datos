class Cambio:

    def __init__(
        self,
        tipo,
        objetivo,
        atributo=None,
        valor_anterior=None,
        operacion=None,
        dato=None
    ):
        self.tipo = tipo
        self.objetivo = objetivo
        self.atributo = atributo
        self.valor_anterior = valor_anterior
        self.operacion = operacion
        self.dato = dato

    @classmethod
    def de_atributo(
        cls,
        tipo,
        objetivo,
        atributo,
        valor_anterior
    ):
        return cls(
            tipo=tipo,
            objetivo=objetivo,
            atributo=atributo,
            valor_anterior=valor_anterior
        )

    @classmethod
    def de_operacion(
        cls,
        tipo,
        objetivo,
        operacion,
        dato=None
    ):
        return cls(
            tipo=tipo,
            objetivo=objetivo,
            operacion=operacion,
            dato=dato
        )

    def deshacer(self):
        if self.atributo is not None:
            setattr(
                self.objetivo,
                self.atributo,
                self.valor_anterior
            )
            return

        if self.operacion is not None:
            metodo = getattr(
                self.objetivo,
                self.operacion
            )

            if self.dato is None:
                metodo()
            else:
                metodo(self.dato)