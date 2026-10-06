from simulacion_camion import CAPACIDAD_CAMION, HORA_INICIO_JORNADA, IDA, SimulacionTransporte


def convertir_a_12_horas(horas_24: int) -> tuple[int, str]:
    """Convierte una hora de formato 24 h a formato 12 h.

    Entradas:
        horas_24: hora entre 0 y 23.
    Modifica: nada.
    Retorna: tupla (hora de 1 a 12, "AM" o "PM").
    """
    periodo = "AM" if horas_24 < 12 else "PM"
    horas_12 = horas_24 % 12
    if horas_12 == 0:
        horas_12 = 12
    return horas_12, periodo


def formatear_hora(minuto: int) -> str:
    """Convierte un minuto de la jornada a hora de reloj, por ejemplo "05:30 AM".

    Entradas:
        minuto: minutos desde el inicio de la jornada.
    Modifica: nada.
    Retorna: la hora como texto.
    """
    horas_24 = HORA_INICIO_JORNADA + minuto // 60
    minutos = minuto % 60
    horas_12, periodo = convertir_a_12_horas(horas_24)
    return str(horas_12).zfill(2) + ":" + str(minutos).zfill(2) + " " + periodo


def imprimir_historial(simulacion: SimulacionTransporte) -> None:
    """Imprime cada parada de cada camion: hora, estacion y sentido, suben, bajan, ocupacion y gente que se quedo.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada (solo imprime en consola).
    Retorna: nada.
    """
    print("===== HISTORIAL DE PARADAS =====")
    for registro in simulacion.historial_paradas:
        if registro.es_terminal:
            texto_estacion = "Terminal (estacion 1)"
        else:
            texto_estacion = "Estacion " + str(registro.numero_estacion) + (" (ida)" if registro.sentido == IDA else " (vuelta)")
        linea = (formatear_hora(registro.minuto) + " | Camion " + str(registro.numero_camion) + " | " + texto_estacion
                 + " | suben " + str(registro.subieron) + ", bajan " + str(registro.bajaron)
                 + " | a bordo " + str(registro.ocupacion) + "/" + str(CAPACIDAD_CAMION))
        if registro.quedaron_esperando > 0:
            linea += " | LLENO: se quedan esperando " + str(registro.quedaron_esperando)
        print(linea)


def imprimir_resumen_estaciones(simulacion: SimulacionTransporte) -> None:
    """Imprime por estacion cuanta gente subio y bajo y que tan seguido el camion llego lleno.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada (solo imprime en consola).
    Retorna: nada.
    """
    print("===== PATRON DE CARGA Y DESCARGA POR ESTACION =====")
    for estacion in simulacion.estaciones:
        registros_estacion = [registro for registro in simulacion.historial_paradas if registro.numero_estacion == estacion.numero_estacion]
        paradas_atendidas = [registro for registro in registros_estacion if not registro.es_terminal]
        total_subieron = sum(registro.subieron for registro in registros_estacion)
        total_bajaron = sum(registro.bajaron for registro in registros_estacion)
        paradas_con_camion_lleno = sum(1 for registro in paradas_atendidas if registro.quedaron_esperando > 0)
        total_dejados = sum(registro.quedaron_esperando for registro in paradas_atendidas)
        promedio_dejados = total_dejados / len(paradas_atendidas)
        print(
            f"Estacion {estacion.numero_estacion:>2}"
            f" | llegadas/min {estacion.probabilidad_llegada_por_minuto:.2f}"
            f" | subieron {total_subieron:>4}"
            f" | bajaron {total_bajaron:>4}"
            f" | paradas con camion lleno {paradas_con_camion_lleno}/{len(paradas_atendidas)}"
            f" | promedio dejados por parada {promedio_dejados:.1f}"
        )


def imprimir_analisis(simulacion: SimulacionTransporte) -> None:
    """Imprime los indicadores generales del sistema y una conclusion sobre si el servicio alcanza.

    Entradas:
        simulacion: simulacion ya ejecutada.
    Modifica: nada (solo imprime en consola).
    Retorna: nada.
    """
    paradas_atendidas = [registro for registro in simulacion.historial_paradas if not registro.es_terminal]
    paradas_con_camion_lleno = sum(1 for registro in paradas_atendidas if registro.quedaron_esperando > 0)
    total_dejados = sum(registro.quedaron_esperando for registro in paradas_atendidas)
    promedio_dejados = total_dejados / len(paradas_atendidas)
    minutos_espera = [pasajero.minuto_abordaje - pasajero.minuto_llegada for pasajero in simulacion.pasajeros_transportados]
    espera_promedio = sum(minutos_espera) / len(minutos_espera)
    if paradas_con_camion_lleno == 0:
        conclusion = "el servicio completa la ruta sin dejar pasajeros por falta de capacidad."
    else:
        conclusion = "el servicio NO alcanza; conviene agregar camiones o reducir el intervalo entre salidas."

    print(f"""===== ANALISIS DEL SISTEMA =====
Camiones: {len(simulacion.camiones)}, salida cada {simulacion.minutos_entre_salidas} minutos
Salidas programadas sin camion disponible: {simulacion.salidas_sin_camion_disponible}
Pasajeros transportados: {len(simulacion.pasajeros_transportados)}
Espera promedio en estacion antes de abordar: {espera_promedio:.1f} minutos
Paradas donde el camion lleno dejo gente: {paradas_con_camion_lleno}/{len(paradas_atendidas)}
Promedio de pasajeros que quedan esperando por parada: {promedio_dejados:.1f}
CONCLUSION: {conclusion}""")


def generar_reporte(simulacion: SimulacionTransporte, mostrar_historial: bool) -> None:
    """Imprime el reporte de texto completo.

    Entradas:
        simulacion: simulacion ya ejecutada.
        mostrar_historial: si es True, imprime tambien el historial de cada parada.
    Modifica: nada (solo imprime en consola).
    Retorna: nada.
    """
    if mostrar_historial:
        imprimir_historial(simulacion)
    imprimir_resumen_estaciones(simulacion)
    imprimir_analisis(simulacion)
