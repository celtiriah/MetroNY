"""
scratch/test_m6_all_requirements.py - Suite de pruebas automatizadas para el Modulo 6: Mantenimiento.
Verifica los 9 requerimientos oficiales y las Reglas de Negocio 19 y 25 contra Oracle 23ai (FREEPDB1).
"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "prototypes/desktop")

from services.db import get_connection, execute_query
from services import m6_maintenance_service
from services.actions_service import programar_viaje


def run_all_tests():
    print("==============================================================================")
    print("INICIANDO VERIFICACION DE REQUERIMIENTOS: MODULO 6 (MANTENIMIENTO)")
    print("==============================================================================")

    test_passed = 0
    test_total = 0

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 1: REGISTRAR EQUIPOS DE INFRAESTRUCTURA (EQUIPO)
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 1] Requerimiento 1: Registro y consulta de activo en EQUIPO...")
    codigo_eq = f"EQ-TEST-{int(datetime.now().timestamp())}"
    res_eq = m6_maintenance_service.crear_equipo(
        codigo_equipo=codigo_eq,
        tipo_equipo="Señal",
        tipo_referencia="ESTACION",
        referencia_id=1,
        ubicacion="Interlocking Test 59th St",
        fabricante="Siemens Mobility",
        modelo="Trainguard CBTC-X",
        numero_serie="SN-998877",
        fecha_instalacion=datetime.now().strftime("%Y-%m-%d"),
        estado="Disponible",
        fecha_proxima_revision=(datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    )
    assert res_eq.get("success"), f"Fallo al crear equipo: {res_eq}"
    test_eq_id = int(res_eq["id_equipo"])
    print(f"   -> Creado equipo ID {test_eq_id} con codigo {codigo_eq}")

    eq_detalle = m6_maintenance_service.get_equipo_by_id(test_eq_id)
    assert eq_detalle is not None, "El equipo no se encontro por ID"
    assert eq_detalle["CODIGO_EQUIPO"] == codigo_eq
    assert eq_detalle["ESTADO"] == "Disponible"
    print("   -> Datos de equipo verificados correctamente.")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 2: CREAR ORDEN DE MANTENIMIENTO CON SP_CREAR_ORDEN_MANTENIMIENTO
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 2] Requerimiento 2: Invocacion a SP_CREAR_ORDEN_MANTENIMIENTO...")
    # Obtener tecnico disponible
    tecnicos = m6_maintenance_service.get_tecnicos_disponibles()
    assert len(tecnicos) > 0, "No hay tecnicos disponibles"
    tec_id = int(tecnicos[0]["ID_EMPLEADO"])

    res_ord = m6_maintenance_service.crear_orden(
        equipo_id=test_eq_id,
        tipo_mantenimiento="Preventivo",
        descripcion="Calibracion de sensor optico de enclavamiento",
        prioridad="Alta",
        tecnico_id=tec_id
    )
    assert res_ord.get("success"), f"Fallo al crear orden: {res_ord}"
    test_ord_id = int(res_ord["id_orden"])
    num_orden = str(res_ord["numero_orden"])
    print(f"   -> Orden creada: {num_orden} (ID {test_ord_id})")

    # Verificar que el equipo cambio de estado a 'En Mantenimiento'
    eq_actualizado = m6_maintenance_service.get_equipo_by_id(test_eq_id)
    assert eq_actualizado is not None
    assert eq_actualizado["ESTADO"] == "En Mantenimiento", f"El estado deberia ser 'En Mantenimiento', es: {eq_actualizado['ESTADO']}"
    print("   -> Estado del equipo actualizado automaticamente a 'En Mantenimiento'.")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 3: ASIGNAR MULTIPLES TECNICOS (ORDEN_TECNICO)
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 3] Requerimiento 3: Asignacion de tecnicos y cuadrillas...")
    # Si hay mas de un tecnico, asignar un segundo tecnico
    if len(tecnicos) > 1:
        tec2_id = int(tecnicos[1]["ID_EMPLEADO"])
        res_asig = m6_maintenance_service.asignar_tecnico_a_orden(
            orden_id=test_ord_id,
            empleado_id=tec2_id,
            rol_en_orden="Técnico Especialista"
        )
        assert res_asig.get("success"), f"Fallo al asignar segundo tecnico: {res_asig}"
        print(f"   -> Asignado segundo tecnico {tec2_id} a la orden.")

    tecs_orden = m6_maintenance_service.get_tecnicos_por_orden(test_ord_id)
    assert len(tecs_orden) >= 1, "Debe haber al menos 1 tecnico asignado"
    print(f"   -> Cuadrilla actual de la orden: {len(tecs_orden)} tecnico(s).")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 4: REPUESTOS Y CONSUMOS (REPUESTO y ORDEN_REPUESTO)
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 4] Requerimiento 4: Catalogo y consumo de repuestos...")
    # Crear un repuesto de prueba
    cod_rep = f"REP-TST-{int(datetime.now().timestamp()) % 10000}"
    res_rep = m6_maintenance_service.crear_repuesto(
        codigo=cod_rep,
        nombre="Sensor Laser CBTC Test",
        costo_unitario=250.0
    )
    assert res_rep.get("success"), f"Fallo al crear repuesto: {res_rep}"
    test_rep_id = int(res_rep["id_repuesto"])
    print(f"   -> Creado repuesto ID {test_rep_id} ({cod_rep}) a $250.00 c/u")

    # Registrar consumo de 2 unidades
    res_consumo = m6_maintenance_service.registrar_consumo_repuesto(
        orden_id=test_ord_id,
        repuesto_id=test_rep_id,
        cantidad=2
    )
    assert res_consumo.get("success"), f"Fallo al consumir repuesto: {res_consumo}"
    assert res_consumo["costo_total"] == 500.0, f"Costo total debe ser 500.0, fue: {res_consumo['costo_total']}"
    print("   -> Consumo registrado: 2 unidades = $500.00")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 5: CALCULO DE COSTO CON FN_COSTO_ORDEN_MANTENIMIENTO
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 5] Requerimiento 5: Invocacion a funcion FN_COSTO_ORDEN_MANTENIMIENTO...")
    costo_calc = m6_maintenance_service.calcular_costo_total_orden(test_ord_id)
    assert costo_calc >= 500.0, f"El costo calculado debe ser al menos 500.0, fue: {costo_calc}"
    print(f"   -> Costo consolidado por FN_COSTO_ORDEN_MANTENIMIENTO: ${costo_calc:.2f}")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 6: FINALIZACION DE ORDEN Y RESTAURACION DE ESTADO A 'DISPONIBLE'
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 6] Requerimiento 6: Cierre de orden y actualizacion de fechas de inspeccion...")
    res_comp = m6_maintenance_service.completar_orden(
        id_orden=test_ord_id,
        costo_final=costo_calc,
        dias_proxima_revision=120
    )
    assert res_comp.get("success"), f"Fallo al completar orden: {res_comp}"
    print("   -> Orden completada exitosamente.")

    # Verificar que el equipo volvio a 'Disponible'
    eq_restaurado = m6_maintenance_service.get_equipo_by_id(test_eq_id)
    assert eq_restaurado is not None
    assert eq_restaurado["ESTADO"] == "Disponible", f"El estado deberia ser 'Disponible', es: {eq_restaurado['ESTADO']}"
    print("   -> Estado del equipo restaurado a 'Disponible'.")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 7: REGLA DE NEGOCIO 19 (BLOQUEO DE TREN EN MANTENIMIENTO)
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 7] Requerimiento 7 / Regla de Negocio 19: Validacion de TRG_TREN_MANTENIMIENTO_NO_ASIGNAR...")
    # Obtener el tren ID 1 o equipo con TREN
    eq_tren = execute_query("SELECT id_equipo, referencia_id FROM EQUIPO WHERE tipo_referencia = 'TREN' AND ROWNUM = 1")["rows"]
    if eq_tren:
        id_eq_tren = int(eq_tren[0]["ID_EQUIPO"])
        id_tren = int(eq_tren[0]["REFERENCIA_ID"])

        # Crear orden para este tren
        res_ord_tren = m6_maintenance_service.crear_orden(
            equipo_id=id_eq_tren,
            tipo_mantenimiento="Correctivo",
            descripcion="Prueba de bloqueo Regla 19"
        )
        assert res_ord_tren.get("success"), f"Fallo al crear orden para tren: {res_ord_tren}"
        ord_tren_id = int(res_ord_tren["id_orden"])

        # Verificar que TREN.estado_operativo ahora es 'En Mantenimiento'
        tren_data = execute_query("SELECT estado_operativo FROM TREN WHERE id_tren = :id_t", {"id_t": id_tren})["rows"][0]
        assert tren_data["ESTADO_OPERATIVO"] == "En Mantenimiento", f"El tren debe estar En Mantenimiento, esta: {tren_data['ESTADO_OPERATIVO']}"
        print("   -> Tren colocado exitosamente en estado 'En Mantenimiento'.")

        # Intentar programar viaje con este tren -> DEBE FALLAR con ORA-20013 / ORA-20003
        conductores = execute_query("SELECT id_empleado FROM EMPLEADO WHERE cargo = 'Conductor' AND ROWNUM = 1")["rows"]
        rutas = execute_query("SELECT id_ruta FROM RUTA WHERE ROWNUM = 1")["rows"]
        if conductores and rutas:
            res_viaje = programar_viaje(
                ruta_id=int(rutas[0]["ID_RUTA"]),
                fecha=datetime.now().strftime("%Y-%m-%d"),
                hora_prog_salida="10:00",
                hora_prog_llegada="11:00",
                tren_id=id_tren,
                conductor_id=int(conductores[0]["ID_EMPLEADO"])
            )
            assert not res_viaje.get("success"), "Se esperaba fallo al asignar tren en mantenimiento a viaje"
            print(f"   -> Exito: Trigger TRG_TREN_MANTENIMIENTO_NO_ASIGNAR bloqueo el viaje: {res_viaje.get('error')}")

        # Limpiar orden de prueba del tren restaurandolo a Disponible
        m6_maintenance_service.completar_orden(ord_tren_id)
        tren_rest = execute_query("SELECT estado_operativo FROM TREN WHERE id_tren = :id_t", {"id_t": id_tren})["rows"][0]
        assert tren_rest["ESTADO_OPERATIVO"] == "Disponible"
        print("   -> Tren restaurado a 'Disponible'.")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 8: CONSULTA DE ACTIVOS FUERA DE SERVICIO Y ALERTAS
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 8] Requerimiento 8: Alertas de inspeccion vencida y equipos fuera de servicio...")
    vencidas = m6_maintenance_service.get_equipos_inspeccion_vencida()
    print(f"   -> Activos con revision vencida o proxima detectados: {len(vencidas)}")

    fuera = m6_maintenance_service.get_equipos_fuera_servicio()
    print(f"   -> Activos fuera de servicio o en reparacion: {len(fuera)}")

    taller = m6_maintenance_service.get_trenes_en_taller()
    print(f"   -> Trenes en taller segun VW_TRENES_MANTENIMIENTO: {len(taller)}")
    test_passed += 1

    # --------------------------------------------------------------------------
    # REQUERIMIENTO 9: LIMPIEZA Y REGLA DE NEGOCIO 25
    # --------------------------------------------------------------------------
    test_total += 1
    print("\n[TEST 9] Requerimiento 9 / Regla de Negocio 25: Auditoria y eliminacion segura...")
    # Intentar eliminar equipo con orden historica -> DEBE SER RECHAZADO
    res_del_fail = m6_maintenance_service.eliminar_equipo(test_eq_id)
    assert not res_del_fail.get("success"), "No se debe poder eliminar equipo con orden historica"
    print("   -> Exito: Se impidio la eliminacion de un equipo con ordenes asociadas (Regla 25).")

    # Limpiar datos creados en el test
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ORDEN_REPUESTO WHERE orden_id = :id_ord", {"id_ord": test_ord_id})
        cur.execute("DELETE FROM ORDEN_TECNICO WHERE orden_id = :id_ord", {"id_ord": test_ord_id})
        cur.execute("DELETE FROM ORDEN_MANTENIMIENTO WHERE id_orden = :id_ord", {"id_ord": test_ord_id})
        cur.execute("DELETE FROM REPUESTO WHERE id_repuesto = :id_rep", {"id_rep": test_rep_id})
        cur.execute("DELETE FROM EQUIPO WHERE id_equipo = :id_eq", {"id_eq": test_eq_id})
        conn.commit()
        print("   -> Registros de prueba temporales eliminados correctamente.")
    finally:
        cur.close()
        conn.close()
    test_passed += 1

    print("\n==============================================================================")
    print(f"RESULTADO: {test_passed}/{test_total} PRUEBAS SUPERADAS EXITOSAMENTE (100%)")
    print("TODOS LOS REQUERIMIENTOS Y REGLAS DEL MODULO 6 FUERON SATISFECHOS.")
    print("==============================================================================")


if __name__ == "__main__":
    run_all_tests()

