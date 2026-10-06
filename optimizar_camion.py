import random
from dataclasses import dataclass

import plotly.graph_objects as go

from simulacion_camion import ULTIMA_SALIDA_POSIBLE, SimulacionTransporte

INTERVALOS_A_PROBAR = [5, 10, 15, 20, 30]
REPETICIONES_POR_CONFIGURACION = 10
CAMIONES_INICIALES = 5
META_MINUTOS_DE_ESPERA = 15
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
# cada intervalo con su propio simbolo y trazo: con pocos camiones las lineas se enciman y asi se distinguen
SIMBOLOS = ["circle", "square", "diamond", "triangle-up", "x"]
TRAZOS = ["solid", "dash", "dot", "dashdot", "longdash"]


@dataclass
class Configuracion:
    cantidad_camiones: int
    minutos_entre_salidas: int
    minutos_de_espera: float


def medir_minutos_de_espera(cantidad_camiones: int, minutos_entre_salidas: int) -> float:
    """Simula una configuracion varias veces (con semillas fijas) y promedia la espera de los pasajeros.

    Entradas:
        cantidad_camiones: cuantos camiones tiene la flota.
        minutos_entre_salidas: cada cuantos minutos sale un camion.
    Modifica: la semilla del generador random.
    Retorna: minutos de espera promedio en estacion.
    """
    esperas_por_dia = []
    for repeticion in range(REPETICIONES_POR_CONFIGURACION):
        # misma semilla en la repeticion n de todas las configuraciones: todas enfrentan la misma demanda
        random.seed(repeticion)
        simulacion = SimulacionTransporte(cantidad_camiones, minutos_entre_salidas)
        simulacion.ejecutar()
        esperas = [pasajero.minuto_abordaje - pasajero.minuto_llegada for pasajero in simulacion.pasajeros_transportados]
        esperas_por_dia.append(sum(esperas) / len(esperas))
    return sum(esperas_por_dia) / len(esperas_por_dia)


def probar_intervalo(minutos_entre_salidas: int) -> list[Configuracion]:
    """Mide la espera para un intervalo dado empezando con CAMIONES_INICIALES y sumando un camion a la vez
    hasta tener un camion por cada salida que cabe en la jornada.

    Entradas:
        minutos_entre_salidas: intervalo a probar.
    Modifica: la semilla del generador random.
    Retorna: lista de Configuracion, una por cantidad de camiones probada.
    """
    salidas_en_la_jornada = ULTIMA_SALIDA_POSIBLE // minutos_entre_salidas + 1
    return [
        Configuracion(cantidad_camiones, minutos_entre_salidas, medir_minutos_de_espera(cantidad_camiones, minutos_entre_salidas))
        for cantidad_camiones in range(CAMIONES_INICIALES, salidas_en_la_jornada + 1)
    ]


def main() -> None:
    """Prueba todas las configuraciones, imprime la optima (menos camiones que cumplen la meta de espera; si ninguna
    la cumple, la de menor espera) y muestra la grafica.

    Entradas: ninguna.
    Modifica: nada (imprime en consola y abre la grafica).
    Retorna: nada.
    """
    print("Simulando configuraciones...")
    configuraciones = [configuracion for intervalo in INTERVALOS_A_PROBAR for configuracion in probar_intervalo(intervalo)]
    cumplen_meta = [configuracion for configuracion in configuraciones if configuracion.minutos_de_espera <= META_MINUTOS_DE_ESPERA]
    if cumplen_meta:
        optima = min(cumplen_meta, key=lambda configuracion: configuracion.cantidad_camiones)
        print("Optima:", end=" ")
    else:
        # nadie llega a la meta: se toma la de menor espera y, en empate, la de menos camiones
        optima = min(configuraciones, key=lambda configuracion: (round(configuracion.minutos_de_espera, 1), configuracion.cantidad_camiones))
        print(f"Ninguna configuracion llega a la meta de {META_MINUTOS_DE_ESPERA} minutos. La mejor:", end=" ")
    print(f"{optima.cantidad_camiones} camiones saliendo cada {optima.minutos_entre_salidas} minutos "
          f"(la gente espera {optima.minutos_de_espera:.1f} minutos en promedio)")

    figura = go.Figure()
    for indice, intervalo in enumerate(INTERVALOS_A_PROBAR):
        del_intervalo = [configuracion for configuracion in configuraciones if configuracion.minutos_entre_salidas == intervalo]
        llega_a_meta = any(configuracion.minutos_de_espera <= META_MINUTOS_DE_ESPERA for configuracion in del_intervalo)
        figura.add_trace(go.Scatter(
            x=[configuracion.cantidad_camiones for configuracion in del_intervalo],
            y=[configuracion.minutos_de_espera for configuracion in del_intervalo],
            name=f"sale uno cada {intervalo} min" + ("" if llega_a_meta else " (no llega a la meta)"),
            mode="lines+markers",
            line={"color": COLORES[indice], "dash": TRAZOS[indice], "width": 3},
            marker={"symbol": SIMBOLOS[indice], "size": 9},
            hovertemplate="%{x} camiones<br>%{y:.1f} minutos de espera",
        ))
    figura.add_hline(y=META_MINUTOS_DE_ESPERA, line_dash="dash", line_color="#555555",
                     annotation_text=f"meta: {META_MINUTOS_DE_ESPERA} min")
    figura.add_annotation(
        x=optima.cantidad_camiones, y=optima.minutos_de_espera, bgcolor="white", ax=90, ay=-70,
        text=f"{'optima' if cumplen_meta else 'mejor'}: {optima.cantidad_camiones} camiones cada {optima.minutos_entre_salidas} min",
    )
    figura.update_layout(
        title="Cuantos camiones hacen falta para que la gente no espere tanto",
        xaxis_title="Cantidad de camiones",
        yaxis_title="Minutos que espera una persona en la estacion (promedio)",
        template="plotly_white",
    )
    figura.show()


if __name__ == "__main__":
    main()
