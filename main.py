import reporte_pd
import reporte_txt
from simulacion_camion import MINUTOS_ENTRE_SALIDAS, SimulacionTransporte

RESPUESTA_SI = 1


def preguntar_si_no(pregunta: str) -> bool:
    """Hace una pregunta de si/no por consola.

    Entradas:
        pregunta: texto de la pregunta.
    Modifica: nada (lee del teclado).
    Retorna: True si el usuario contesta 1.
    """
    return int(input(pregunta + " (1 = si, 0 = no): ")) == RESPUESTA_SI


def preguntar_entero(pregunta: str, valor_por_defecto: int) -> int:
    """Pide un numero entero por consola; si se deja vacio usa el valor por defecto.

    Entradas:
        pregunta: texto de la pregunta.
        valor_por_defecto: valor que se usa si el usuario solo da enter.
    Modifica: nada (lee del teclado).
    Retorna: el entero elegido.
    """
    respuesta = input(pregunta + " (enter = " + str(valor_por_defecto) + "): ")
    return int(respuesta) if respuesta.strip() else valor_por_defecto


def main() -> None:
    """Pide los parametros, corre la simulacion y le pasa el resultado en crudo a los dos reportes.

    Entradas: ninguna.
    Modifica: nada (lee del teclado e imprime en consola).
    Retorna: nada.
    """
    cantidad_camiones = preguntar_entero("Cantidad de camiones", 1)
    minutos_entre_salidas = preguntar_entero("Minutos entre salidas desde la estacion inicial", MINUTOS_ENTRE_SALIDAS)
    mostrar_historial = preguntar_si_no("Mostrar historial de cada parada?")

    simulacion = SimulacionTransporte(cantidad_camiones, minutos_entre_salidas)
    simulacion.ejecutar()

    reporte_txt.generar_reporte(simulacion, mostrar_historial)
    reporte_pd.generar_reporte(simulacion)


if __name__ == "__main__":
    main()
