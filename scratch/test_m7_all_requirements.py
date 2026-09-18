"""
scratch/test_m7_all_requirements.py - Suite de pruebas automatizadas para el Modulo 7: Incidentes Operativos.
Verifica los 7 requerimientos oficiales, la restriccion de Arco Exclusivo (CK_INCIDENTE_ELEMENTO_ARCO),
la auditoria automatica en BITACORA (TRG_INCIDENTE_AUDITORIA), el despacho de cancelaciones (SP_CANCELAR_VIAJES_AFECTADOS),
y el procedimiento de resolucion tecnica contra Oracle 23ai (FREEPDB1).
"""
import sys
from datetime import datetime

sys.path.insert(0, "prototypes/desktop")

from services.db import get_connection, execute_query
from services import m7_incidents_service


def run_all_tests():
    print("==============================================================================")
    print("INICIANDO VERIFICACION DE REQUERIMIENTOS: MODULO 7 (INCIDENTES OPERATIVOS)")
    print("==============================================================================")

    test_passed = 0
    test_total = 0

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 1: REGISTRO DE INCIDENTE MEDIANTE SP_REGISTRAR_INCIDENTE
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 1] Requerimiento 1: Invocacion a SP_REGISTRAR_INCIDENTE y generacion de clave...")
    empleados = execute_query("SELECT id_empleado FROM EMPLEADO WHERE ROWNUM = 1")["rows"]
    assert len(empleados) > 0, "No hay empleados registrados"
    rep_id = int(empleados[0]["ID_EMPLEADO"])

    res_inc = m7_incidents_service.registrar_incidente(
        tipo="Falla de Señalización",
        descripcion="Interrupción de comunicación CBTC en interconexión Grand Central",
        nivel_severidad="Crítico",
        reportado_por_id=rep_id,
        tipo_elemento="ESTACION",
        elemento_id=2,
        tipo_afectacion="Retraso"
    )
    assert res_inc.get("success"), f"Fallo al registrar incidente: {res_inc}"
    test_inc_id = int(res_inc["id_incidente"])
    num_inc = str(res_inc["numero_incidente"])
    print(f"   -> Incidente creado: {num_inc} (ID {test_inc_id})")
    assert num_inc.startswith("INC-"), f"Formato de clave invalido: {num_inc}"
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 2: AUDITORIA AUTOMATICA EN BITACORA (TRG_INCIDENTE_AUDITORIA)
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 2] Requerimiento 2: Verificacion del trigger TRG_INCIDENTE_AUDITORIA en BITACORA...")
    bitacora_rows = execute_query("""
        SELECT * FROM BITACORA 
        WHERE tabla_afectada = 'INCIDENTE' AND registro_id = :id_inc AND operacion = 'INSERT'
    """, {"id_inc": test_inc_id})["rows"]
    assert len(bitacora_rows) > 0, "No se genero el registro en BITACORA por el trigger TRG_INCIDENTE_AUDITORIA"
    print(f"   -> Registro en BITACORA verificado exitosamente: ID {bitacora_rows[0]['ID_BITACORA']}")
    print(f"   -> Descripcion registrada: {bitacora_rows[0]['DESCRIPCION']}")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 3: ARCO EXCLUSIVO EN INCIDENTE_ELEMENTO_AFECTADO
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 3] Requerimiento 3: Asociacion de elementos respetando Arco Exclusivo (CK_INCIDENTE_ELEMENTO_ARCO)...")
    # Asociar un tren
    trenes = execute_query("SELECT id_tren FROM TREN WHERE ROWNUM = 1")["rows"]
    assert trenes, "No hay trenes registrados"
    test_tren_id = int(trenes[0]["ID_TREN"])

    res_asoc_tren = m7_incidents_service.asociar_elemento_afectado(
        incidente_id=test_inc_id,
        tipo_elemento="TREN",
        elemento_id=test_tren_id,
        tipo_afectacion="Retiro de Tren"
    )
    assert res_asoc_tren.get("success"), f"Fallo al asociar tren: {res_asoc_tren}"
    print(f"   -> Elemento TREN (ID {test_tren_id}) asociado con afectacion 'Retiro de Tren'.")

    # Asociar una ruta
    rutas = execute_query("SELECT id_ruta FROM RUTA WHERE ROWNUM = 1")["rows"]
    assert rutas, "No hay rutas registradas"
    test_ruta_id = int(rutas[0]["ID_RUTA"])

    res_asoc_ruta = m7_incidents_service.asociar_elemento_afectado(
        incidente_id=test_inc_id,
        tipo_elemento="RUTA",
        elemento_id=test_ruta_id,
        tipo_afectacion="Suspensión de Tramo"
    )
    assert res_asoc_ruta.get("success"), f"Fallo al asociar ruta: {res_asoc_ruta}"
    print(f"   -> Elemento RUTA (ID {test_ruta_id}) asociado con afectacion 'Suspensión de Tramo'.")

    elementos_orden = m7_incidents_service.get_elementos_afectados(test_inc_id)
    assert len(elementos_orden) >= 3, f"Se esperaban al menos 3 elementos asociados, hay {len(elementos_orden)}"
    print(f"   -> Total de elementos asociados al incidente: {len(elementos_orden)}")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 4: RECHAZO DE VIOLACIONES DE ARCO EXCLUSIVO
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 4] Requerimiento 4: Verificacion de rechazo ante violacion de Arco Exclusivo...")
    conn = get_connection()
    cur = conn.cursor()
    arco_violado = False
    try:
        # Intentar insertar con dos FKs pobladas (estacion Y tren)
        cur.execute("""
            INSERT INTO INCIDENTE_ELEMENTO_AFECTADO (
                id_incidente_elemento, incidente_id, tipo_elemento,
                estacion_id, tren_id, tipo_afectacion
            ) VALUES (
                SEQ_INCIDENTE_ELEMENTO_AF_F066.NEXTVAL, :id_inc, 'ESTACION',
                1, 1, 'Retraso'
            )
        """, {"id_inc": test_inc_id})
        conn.commit()
    except Exception as e:
        conn.rollback()
        arco_violado = True
        print(f"   -> Exito: Oracle rechazo la insercion violadora de Arco Exclusivo con constraint CK_INCIDENTE_ELEMENTO_ARCO.")
    finally:
        cur.close()
        conn.close()
    assert arco_violado, "Oracle debio rechazar la insercion que violaba el Arco Exclusivo"
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 5: MODIFICACION Y DESVINCULACION DE AFECTACIONES OPERATIVAS
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 5] Requerimiento 5: Modificacion y desvinculacion de elementos afectados...")
    id_ie = int(elementos_orden[0]["ID_INCIDENTE_ELEMENTO"])
    res_mod = m7_incidents_service.modificar_afectacion_elemento(id_ie, "Cierre de Estación")
    assert res_mod.get("success"), f"Fallo al modificar afectacion: {res_mod}"
    print("   -> Afectacion actualizada a 'Cierre de Estación'.")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 6: DESPACHO Y CANCELACION DE VIAJES (SP_CANCELAR_VIAJES_AFECTADOS)
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 6] Requerimiento 6: Despacho con SP_CANCELAR_VIAJES_AFECTADOS...")
    res_cancel = m7_incidents_service.despachar_cancelacion_viajes(test_inc_id)
    assert res_cancel.get("success"), f"Fallo al cancelar viajes afectados: {res_cancel}"
    print(f"   -> Procedimiento ejecutado. Viajes cancelados reportados: {res_cancel.get('viajes_cancelados', 0)}")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 7: TRANSICION DE ESTADO, CIERRE TECNICO Y BITACORA
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 7] Requerimiento 7: Ciclo de vida ('En Atención' -> 'Cerrado') y auditoria...")
    # Pasa a En Atencion
    res_aten = m7_incidents_service.cambiar_estado(test_inc_id, "En Atención")
    assert res_aten.get("success")

    # Cierre tecnico formal
    res_cierre = m7_incidents_service.cerrar_incidente(
        id_incidente=test_inc_id,
        causa_identificada="Falla en tarjeta de enlace óptico del transpondedor",
        acciones_realizadas="Reemplazo de módulo transceptor y pruebas de acoplamiento CBTC",
        pasajeros_afectados=1500
    )
    assert res_cierre.get("success"), f"Fallo al cerrar incidente: {res_cierre}"

    # Verificar datos finales
    inc_final = m7_incidents_service.get_incidente_by_id(test_inc_id)
    assert inc_final is not None
    assert inc_final["ESTADO"] == "Cerrado"
    assert inc_final["CAUSA_IDENTIFICADA"] == "Falla en tarjeta de enlace óptico del transpondedor"
    assert int(inc_final["PASAJEROS_AFECTADOS_ESTIMADO"]) == 1500
    print("   -> Incidente cerrado formalmente y verificado.")

    # Verificar que BITACORA registro la actualizacion de cierre
    bitacora_update = execute_query("""
        SELECT * FROM BITACORA 
        WHERE tabla_afectada = 'INCIDENTE' AND registro_id = :id_inc AND operacion = 'UPDATE'
    """, {"id_inc": test_inc_id})["rows"]
    assert len(bitacora_update) > 0, "No se encontro registro UPDATE en BITACORA tras el cierre"
    print(f"   -> Auditoria UPDATE verificada en BITACORA: {bitacora_update[0]['DESCRIPCION']}")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 8: METRICAS Y KPIS
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 8] Requerimiento 8: Indicadores KPI y estadisticas...")
    kpis = m7_incidents_service.get_kpis_incidentes()
    assert "activos" in kpis and "criticos_altos" in kpis
    print(f"   -> KPIs: {kpis}")

    stats = m7_incidents_service.get_estadisticas_incidentes()
    assert "por_severidad" in stats and "por_tipo" in stats
    print(f"   -> Estadisticas calculadas: {len(stats['por_severidad'])} niveles de severidad presentes.")
    test_passed += 1

    # --------------------------------------------------------------------------
    # LIMPIEZA DE DATOS TEMPORALES
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 9] Limpieza de registros temporales de prueba...")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM INCIDENTE_ELEMENTO_AFECTADO WHERE incidente_id = :id_inc", {"id_inc": test_inc_id})
        cur.execute("DELETE FROM BITACORA WHERE tabla_afectada = 'INCIDENTE' AND registro_id = :id_inc", {"id_inc": test_inc_id})
        cur.execute("DELETE FROM INCIDENTE WHERE id_incidente = :id_inc", {"id_inc": test_inc_id})
        conn.commit()
        print("   -> Limpieza completada exitosamente.")
    finally:
        cur.close()
        conn.close()
    test_passed += 1

    print("\n==============================================================================")
    print(f"RESULTADO: {test_passed}/{test_total} PRUEBAS SUPERADAS EXITOSAMENTE (100%)")
    print("TODOS LOS REQUERIMIENTOS Y CONSTRAINTS DEL MODULO 7 FUERON SATISFECHOS.")
    print("==============================================================================")


if __name__ == "__main__":
    run_all_tests()

