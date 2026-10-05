import math
import random
from dataclasses import dataclass

import plotly.graph_objects as go

from simulacion_camion import MINUTOS_POR_VUELTA, SimulacionTransporte

INTERVALOS_A_PROBAR = [5, 10, 15, 20, 30]
REPETICIONES_POR_CONFIGURACION = 10
META_MINUTOS_DE_ESPERA = 15
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]


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
    """Mide la espera para un intervalo dado con 1 camion, 2 camiones, ... hasta los necesarios para cubrir todas las salidas.

    Entradas:
        minutos_entre_salidas: intervalo a probar.
    Modifica: la semilla del generador random.
    Retorna: lista de Configuracion, una por cantidad de camiones.
    """
    camiones_para_cubrir_todas_las_salidas = math.ceil(MINUTOS_POR_VUELTA / minutos_entre_salidas)
    return [
        Configuracion(cantidad_camiones, minutos_entre_salidas, medir_minutos_de_espera(cantidad_camiones, minutos_entre_salidas))
        for cantidad_camiones in range(1, camiones_para_cubrir_todas_las_salidas + 1)
    ]


def main() -> None:
    """Prueba todas las configuraciones, imprime la optima (menos camiones que cumplen la meta de espera) y muestra la grafica.

    Entradas: ninguna.
    Modifica: nada (imprime en consola y abre la grafica).
    Retorna: nada.
    """
    print("Simulando configuraciones...")
    configuraciones = [configuracion for intervalo in INTERVALOS_A_PROBAR for configuracion in probar_intervalo(intervalo)]
    cumplen_meta = [configuracion for configuracion in configuraciones if configuracion.minutos_de_espera <= META_MINUTOS_DE_ESPERA]
    optima = min(cumplen_meta, key=lambda configuracion: configuracion.cantidad_camiones)
    print(f"Optima: {optima.cantidad_camiones} camiones saliendo cada {optima.minutos_entre_salidas} minutos "
          f"(la gente espera {optima.minutos_de_espera:.1f} minutos en promedio)")

    figura = go.Figure()
    for intervalo in INTERVALOS_A_PROBAR:
        del_intervalo = [configuracion for configuracion in configuraciones if configuracion.minutos_entre_salidas == intervalo]
        figura.add_trace(go.Scatter(
            x=[configuracion.cantidad_camiones for configuracion in del_intervalo],
            y=[configuracion.minutos_de_espera for configuracion in del_intervalo],
            name=f"sale uno cada {intervalo} min",
            mode="lines+markers",
            hovertemplate="%{x} camiones<br>%{y:.1f} minutos de espera",
        ))
    figura.add_hline(y=META_MINUTOS_DE_ESPERA, line_dash="dash", annotation_text="meta")
    figura.add_annotation(
        x=optima.cantidad_camiones, y=optima.minutos_de_espera, bgcolor="white", ax=90, ay=-70,
        text=f"optima: {optima.cantidad_camiones} camiones cada {optima.minutos_entre_salidas} min",
    )
    figura.update_layout(
        title="Cuantos camiones hacen falta para que la gente no espere tanto",
        xaxis_title="Cantidad de camiones",
        yaxis_title="Minutos que espera una persona en la estacion (promedio)",
        template="plotly_white",
        colorway=COLORES,
    )
    figura.show()


if __name__ == "__main__":
    main()
