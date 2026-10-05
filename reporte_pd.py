from dataclasses import asdict

import pandas as pd

from simulacion_camion import SimulacionTransporte


def tabla_paradas(simulacion: SimulacionTransporte) -> pd.DataFrame:
    """Convierte el historial de paradas en un DataFrame.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada.
    Retorna: DataFrame con una fila por parada (columnas de RegistroParada).
    """
    return pd.DataFrame([asdict(registro) for registro in simulacion.historial_paradas])


def tabla_pasajeros(simulacion: SimulacionTransporte) -> pd.DataFrame:
    """Convierte los pasajeros transportados en un DataFrame y calcula cuanto espero cada uno.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada.
    Retorna: DataFrame con una fila por pasajero, mas la columna minutos_espera.
    """
    pasajeros = pd.DataFrame([asdict(pasajero) for pasajero in simulacion.pasajeros_transportados])
    pasajeros["minutos_espera"] = pasajeros["minuto_abordaje"] - pasajeros["minuto_llegada"]
    return pasajeros


def tabla_estaciones(simulacion: SimulacionTransporte) -> pd.DataFrame:
    """Convierte las estaciones en un DataFrame.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada.
    Retorna: DataFrame con numero_estacion y llegadas_por_minuto.
    """
    return pd.DataFrame([
        {"numero_estacion": estacion.numero_estacion, "llegadas_por_minuto": estacion.probabilidad_llegada_por_minuto}
        for estacion in simulacion.estaciones
    ])


def resumen_estaciones(paradas: pd.DataFrame, estaciones: pd.DataFrame) -> pd.DataFrame:
    """Agrupa las paradas por estacion: cuantos subieron y bajaron, y que tan seguido el camion llego lleno.

    Entradas:
        paradas: DataFrame de tabla_paradas.
        estaciones: DataFrame de tabla_estaciones.
    Modifica: nada.
    Retorna: DataFrame indexado por numero_estacion con el resumen.
    """
    movimiento = paradas.groupby("numero_estacion")[["subieron", "bajaron"]].sum()
    atendidas = paradas[~paradas["es_terminal"]].assign(camion_lleno=lambda tabla: tabla["quedaron_esperando"] > 0)
    saturacion = atendidas.groupby("numero_estacion").agg(
        paradas_atendidas=("camion_lleno", "size"),
        paradas_con_camion_lleno=("camion_lleno", "sum"),
        promedio_dejados=("quedaron_esperando", "mean"),
    )
    return estaciones.set_index("numero_estacion").join(movimiento).join(saturacion)


def generar_reporte(simulacion: SimulacionTransporte) -> None:
    """Arma los DataFrames a partir de la simulacion e imprime el resumen por estacion y la estadistica de espera.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada (solo imprime en consola).
    Retorna: nada.
    """
    paradas = tabla_paradas(simulacion)
    pasajeros = tabla_pasajeros(simulacion)
    estaciones = tabla_estaciones(simulacion)

    print("===== RESUMEN POR ESTACION (pandas) =====")
    print(resumen_estaciones(paradas, estaciones).round(2).to_string())
    print("===== ESPERA EN ESTACION (minutos, pandas) =====")
    print(pasajeros["minutos_espera"].describe().round(1).to_string())
