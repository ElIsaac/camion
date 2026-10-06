import random
from dataclasses import dataclass, field
from typing import Literal

TOTAL_ESTACIONES = 32
CAPACIDAD_CAMION = 36
MINUTOS_ENTRE_ESTACIONES = 5
MINUTOS_ENTRE_SALIDAS = 15
HORA_INICIO_JORNADA = 5
HORAS_JORNADA = 17

PROBABILIDAD_LLEGADA_MINIMA_POR_MINUTO = 0.05
PROBABILIDAD_LLEGADA_MAXIMA_POR_MINUTO = 0.30

MINUTOS_JORNADA = HORAS_JORNADA * 60
ESTACION_TERMINAL = 1
ULTIMA_ESTACION = TOTAL_ESTACIONES
IDA = 1
VUELTA = -1
# ruta lineal: va de la 1 a la 32 y regresa en reversa de la 32 a la 1 (31 tramos de ida + 31 de vuelta)
MINUTOS_POR_VUELTA = 2 * (TOTAL_ESTACIONES - 1) * MINUTOS_ENTRE_ESTACIONES
ULTIMA_SALIDA_POSIBLE = MINUTOS_JORNADA - MINUTOS_POR_VUELTA

TipoEvento = Literal["salida", "parada", "terminal"]


@dataclass
class Pasajero:
    minuto_llegada: int
    estacion_destino: int
    minuto_abordaje: int = 0


@dataclass
class Estacion:
    numero_estacion: int
    probabilidad_llegada_por_minuto: float
    ultimo_minuto_generado: int = 0
    esperando_ida: list[Pasajero] = field(default_factory=list)
    esperando_vuelta: list[Pasajero] = field(default_factory=list)


@dataclass
class Camion:
    numero_camion: int
    en_ruta: bool = False
    sentido: int = IDA
    pasajeros_a_bordo: list[Pasajero] = field(default_factory=list)


@dataclass
class Evento:
    minuto: int
    tipo_evento: TipoEvento
    camion: Camion | None = None
    posicion: int = 0


@dataclass
class RegistroParada:
    minuto: int
    numero_camion: int
    numero_estacion: int
    sentido: int
    subieron: int
    bajaron: int
    ocupacion: int
    quedaron_esperando: int
    es_terminal: bool


class SimulacionTransporte:
    def __init__(self, cantidad_camiones: int, minutos_entre_salidas: int) -> None:
        """Crea la simulacion con sus camiones y estaciones (cada estacion con una tasa de llegada al azar).

        Entradas:
            cantidad_camiones: cuantos camiones tiene la flota.
            minutos_entre_salidas: cada cuantos minutos sale un camion de la estacion 1.
        Modifica: inicializa los atributos de la simulacion; consume numeros del generador random.
        Retorna: nada.
        """
        self.minutos_entre_salidas = minutos_entre_salidas
        self.camiones = [Camion(numero_camion=numero) for numero in range(1, cantidad_camiones + 1)]
        self.estaciones = [
            Estacion(
                numero_estacion=numero,
                probabilidad_llegada_por_minuto=random.uniform(
                    PROBABILIDAD_LLEGADA_MINIMA_POR_MINUTO, PROBABILIDAD_LLEGADA_MAXIMA_POR_MINUTO
                ),
            )
            for numero in range(1, TOTAL_ESTACIONES + 1)
        ]
        self.historial_paradas: list[RegistroParada] = []
        self.pasajeros_transportados: list[Pasajero] = []
        self.salidas_sin_camion_disponible = 0
        self.eventos: list[Evento] = []

    # ----- motor de la simulacion: cola de eventos -----

    def ejecutar(self) -> None:
        """Corre la jornada completa procesando la cola de eventos en orden de tiempo.

        Entradas: ninguna.
        Modifica: historial_paradas, pasajeros_transportados, salidas_sin_camion_disponible, la cola de eventos y el estado de camiones y estaciones.
        Retorna: nada.
        """
        self.programar_salidas()
        while self.eventos:
            evento = self.sacar_evento_mas_proximo()
            if evento.tipo_evento == "salida":
                self.procesar_salida(evento.minuto)
            elif evento.tipo_evento == "parada":
                self.atender_parada(evento.camion, evento.posicion, evento.minuto)
            else:
                self.llegar_a_terminal(evento.camion, evento.minuto)

    def programar_salidas(self) -> None:
        """Agenda una salida desde la estacion 1 cada minutos_entre_salidas hasta la ultima salida posible.

        Entradas: ninguna.
        Modifica: agrega eventos "salida" a self.eventos.
        Retorna: nada.
        """
        for minuto in range(0, ULTIMA_SALIDA_POSIBLE + 1, self.minutos_entre_salidas):
            self.programar_evento(minuto, "salida")

    def programar_evento(self, minuto: int, tipo_evento: TipoEvento, camion: Camion | None = None, posicion: int = 0) -> None:
        """Agrega un evento a la cola.

        Entradas:
            minuto: minuto de la jornada en que ocurre.
            tipo_evento: "salida", "parada" o "terminal".
            camion: camion involucrado (None para una salida).
            posicion: estacion donde ocurre la parada (0 si no aplica).
        Modifica: agrega un Evento a self.eventos.
        Retorna: nada.
        """
        self.eventos.append(Evento(minuto=minuto, tipo_evento=tipo_evento, camion=camion, posicion=posicion))

    def sacar_evento_mas_proximo(self) -> Evento:
        """Saca de la cola el evento que ocurre primero.

        Entradas: ninguna.
        Modifica: quita ese evento de self.eventos.
        Retorna: el Evento mas proximo.
        """
        indice_mas_proximo = 0
        for indice in range(len(self.eventos)):
            if self.ocurre_antes(self.eventos[indice], self.eventos[indice_mas_proximo]):
                indice_mas_proximo = indice
        return self.eventos.pop(indice_mas_proximo)

    def ocurre_antes(self, evento: Evento, otro_evento: Evento) -> bool:
        """Compara dos eventos para saber cual va primero; en empate de minuto, la llegada a terminal va antes que la salida.

        Entradas:
            evento: evento a comparar.
            otro_evento: evento contra el que se compara.
        Modifica: nada.
        Retorna: True si evento ocurre antes que otro_evento.
        """
        if evento.minuto != otro_evento.minuto:
            return evento.minuto < otro_evento.minuto
        # en el mismo minuto, el camion que llega a la terminal queda libre antes de asignar la salida
        return evento.tipo_evento == "terminal" and otro_evento.tipo_evento == "salida"

    # ----- lo que pasa en cada tipo de evento -----

    def procesar_salida(self, minuto: int) -> None:
        """Asigna el primer camion libre a la salida programada y lo pone a atender la estacion 1.

        Entradas:
            minuto: minuto de la salida.
        Modifica: marca el camion como en ruta, o suma 1 a salidas_sin_camion_disponible si no hay camion libre.
        Retorna: nada.
        """
        camiones_disponibles = [camion for camion in self.camiones if not camion.en_ruta]
        if not camiones_disponibles:
            self.salidas_sin_camion_disponible += 1
            return
        camion = camiones_disponibles[0]
        camion.en_ruta = True
        camion.sentido = IDA
        self.atender_parada(camion, ESTACION_TERMINAL, minuto)

    def atender_parada(self, camion: Camion, numero_estacion: int, minuto: int) -> None:
        """El camion para en una estacion: llegan pasajeros, bajan los que van ahi, suben los que van en su sentido
        y se agenda la siguiente parada. En la ultima estacion el camion se da la vuelta y regresa en reversa.

        Entradas:
            camion: camion que hace la parada.
            numero_estacion: numero de estacion (1 a TOTAL_ESTACIONES).
            minuto: minuto de la parada.
        Modifica: pasajeros del camion y de la estacion, camion.sentido (en la ultima estacion), historial_paradas,
            pasajeros_transportados y la cola de eventos.
        Retorna: nada.
        """
        estacion = self.estaciones[numero_estacion - 1]
        self.generar_llegadas(estacion, minuto)
        bajaron = self.bajar_pasajeros(camion, numero_estacion)
        if numero_estacion == ULTIMA_ESTACION:
            camion.sentido = VUELTA
        subieron = self.subir_pasajeros(camion, estacion, minuto)
        self.historial_paradas.append(RegistroParada(
            minuto=minuto,
            numero_camion=camion.numero_camion,
            numero_estacion=numero_estacion,
            sentido=camion.sentido,
            subieron=subieron,
            bajaron=bajaron,
            ocupacion=len(camion.pasajeros_a_bordo),
            quedaron_esperando=len(self.fila_del_sentido(estacion, camion.sentido)),
            es_terminal=False,
        ))

        siguiente_estacion = numero_estacion + camion.sentido
        siguiente_minuto = minuto + MINUTOS_ENTRE_ESTACIONES
        if siguiente_estacion == ESTACION_TERMINAL:
            self.programar_evento(siguiente_minuto, "terminal", camion)
        else:
            self.programar_evento(siguiente_minuto, "parada", camion, siguiente_estacion)

    def llegar_a_terminal(self, camion: Camion, minuto: int) -> None:
        """El camion regresa a la terminal (estacion 1): bajan todos los pasajeros y el camion queda libre.

        Entradas:
            camion: camion que llega.
            minuto: minuto de llegada.
        Modifica: vacia el camion, lo marca como libre, agrega el registro a historial_paradas y los pasajeros a pasajeros_transportados.
        Retorna: nada.
        """
        bajaron = self.bajar_pasajeros(camion, ESTACION_TERMINAL)
        self.historial_paradas.append(RegistroParada(
            minuto=minuto,
            numero_camion=camion.numero_camion,
            numero_estacion=ESTACION_TERMINAL,
            sentido=VUELTA,
            subieron=0,
            bajaron=bajaron,
            ocupacion=len(camion.pasajeros_a_bordo),
            quedaron_esperando=0,
            es_terminal=True,
        ))
        camion.en_ruta = False

    # ----- movimiento de pasajeros -----

    def generar_llegadas(self, estacion: Estacion, hasta_minuto: int) -> None:
        """Genera al azar los pasajeros que llegaron a la estacion desde la ultima vez que se reviso; cada uno trae
        un destino al azar y se forma en la fila de ida o de vuelta segun hacia donde va.

        Entradas:
            estacion: estacion donde llegan.
            hasta_minuto: minuto hasta el que se generan llegadas (sin incluirlo).
        Modifica: agrega pasajeros a estacion.esperando_ida o estacion.esperando_vuelta y actualiza estacion.ultimo_minuto_generado.
        Retorna: nada.
        """
        otras_estaciones = [numero for numero in range(1, TOTAL_ESTACIONES + 1) if numero != estacion.numero_estacion]
        for minuto in range(estacion.ultimo_minuto_generado, hasta_minuto):
            if random.random() < estacion.probabilidad_llegada_por_minuto:
                pasajero = Pasajero(minuto_llegada=minuto, estacion_destino=random.choice(otras_estaciones))
                sentido = IDA if pasajero.estacion_destino > estacion.numero_estacion else VUELTA
                self.fila_del_sentido(estacion, sentido).append(pasajero)
        estacion.ultimo_minuto_generado = hasta_minuto

    def fila_del_sentido(self, estacion: Estacion, sentido: int) -> list[Pasajero]:
        """Da la fila de la estacion que corresponde a un sentido.

        Entradas:
            estacion: estacion a consultar.
            sentido: IDA o VUELTA.
        Modifica: nada.
        Retorna: la lista de pasajeros esperando en ese sentido (la misma lista, no una copia).
        """
        return estacion.esperando_ida if sentido == IDA else estacion.esperando_vuelta

    def bajar_pasajeros(self, camion: Camion, numero_estacion: int) -> int:
        """Baja del camion a los pasajeros cuyo destino es la estacion actual.

        Entradas:
            camion: camion del que bajan.
            numero_estacion: estacion donde esta el camion.
        Modifica: camion.pasajeros_a_bordo y pasajeros_transportados.
        Retorna: cuantos pasajeros bajaron.
        """
        pasajeros_que_bajan = [pasajero for pasajero in camion.pasajeros_a_bordo if pasajero.estacion_destino == numero_estacion]
        camion.pasajeros_a_bordo = [pasajero for pasajero in camion.pasajeros_a_bordo if pasajero.estacion_destino != numero_estacion]
        self.pasajeros_transportados.extend(pasajeros_que_bajan)
        return len(pasajeros_que_bajan)

    def subir_pasajeros(self, camion: Camion, estacion: Estacion, minuto: int) -> int:
        """Sube a los pasajeros que esperan en el sentido del camion, en orden de llegada, hasta llenarlo.

        Entradas:
            camion: camion al que suben.
            estacion: estacion donde esperan.
            minuto: minuto de abordaje.
        Modifica: camion.pasajeros_a_bordo, la fila del sentido del camion en la estacion y minuto_abordaje de cada pasajero que sube.
        Retorna: cuantos pasajeros subieron.
        """
        fila = self.fila_del_sentido(estacion, camion.sentido)
        lugares_disponibles = CAPACIDAD_CAMION - len(camion.pasajeros_a_bordo)
        pasajeros_que_suben = fila[:lugares_disponibles]
        del fila[:lugares_disponibles]
        for pasajero in pasajeros_que_suben:
            pasajero.minuto_abordaje = minuto
            camion.pasajeros_a_bordo.append(pasajero)
        return len(pasajeros_que_suben)
