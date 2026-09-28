-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Capa de Programacion PL/SQL - 08_triggers.sql
-- 34 Triggers de Integridad, Auditoria, Antifraude y Control Operativo
-- ======================================================================

-- 1. Trigger: Impedir que el saldo de una tarjeta sea negativo
CREATE OR REPLACE TRIGGER TRG_TARJETA_SALDO_NO_NEGATIVO
BEFORE INSERT OR UPDATE OF saldo_disponible ON TARJETA
FOR EACH ROW
BEGIN
    IF :NEW.saldo_disponible < 0 THEN
        RAISE_APPLICATION_ERROR(-20010, 'Regla de negocio violada: El saldo de una tarjeta OMNY no puede ser negativo.');
    END IF;
END;
/

-- 2. Trigger: Registrar en BITACORA cada cambio de estado operativo de un tren
CREATE OR REPLACE TRIGGER TRG_TREN_CAMBIO_ESTADO
AFTER UPDATE OF estado_operativo ON TREN
FOR EACH ROW
BEGIN
    IF :OLD.estado_operativo != :NEW.estado_operativo THEN
        INSERT INTO BITACORA (
            id_bitacora, fecha_hora, tabla_afectada,
            operacion, registro_id, usuario, descripcion
        ) VALUES (
            SEQ_BITACORA.NEXTVAL, SYSTIMESTAMP, 'TREN',
            'UPDATE', :NEW.id_tren, USER,
            'Cambio de estado operativo del tren ' || :NEW.codigo_interno || 
            ' de "' || :OLD.estado_operativo || '" a "' || :NEW.estado_operativo || '"'
        );
    END IF;
END;
/

-- 3. Trigger: Preservar la inmutabilidad de tarifas aplicadas en transacciones pasadas
CREATE OR REPLACE TRIGGER TRG_TARIFA_HISTORIAL
BEFORE UPDATE OR DELETE ON TARIFA
FOR EACH ROW
DECLARE
    v_usos NUMBER := 0;
BEGIN
    SELECT COUNT(*)
    INTO v_usos
    FROM VIAJE_PASAJERO
    WHERE tarifa_id = :OLD.id_tarifa;

    IF v_usos > 0 THEN
        IF DELETING THEN
            RAISE_APPLICATION_ERROR(-20011, 'No es posible eliminar una tarifa que ya ha sido aplicada a transacciones historicas.');
        ELSIF UPDATING('monto') AND :NEW.monto != :OLD.monto THEN
            RAISE_APPLICATION_ERROR(-20012, 'No se puede modificar el monto de una tarifa ya aplicada. Debe crearse una nueva tarifa con su fecha de vigencia.');
        END IF;
    END IF;
END;
/

-- 4. Trigger: Actualizar el estado del tren a 'En Operación' al iniciar un viaje
CREATE OR REPLACE TRIGGER TRG_TREN_INICIAR_VIAJE
AFTER UPDATE OF estado ON VIAJE_PROGRAMADO
FOR EACH ROW
BEGIN
    IF :NEW.estado = 'En Curso' AND (:OLD.estado IS NULL OR :OLD.estado != 'En Curso') THEN
        UPDATE TREN
        SET estado_operativo = 'En Operación'
        WHERE id_tren = :NEW.tren_id;
    END IF;
END;
/

-- 5. Trigger: Liberar el tren a 'Disponible' cuando el viaje finalice
CREATE OR REPLACE TRIGGER TRG_TREN_FINALIZAR_VIAJE
AFTER UPDATE OF estado ON VIAJE_PROGRAMADO
FOR EACH ROW
BEGIN
    IF :NEW.estado = 'Completado' AND (:OLD.estado IS NULL OR :OLD.estado != 'Completado') THEN
        UPDATE TREN
        SET estado_operativo = 'Disponible'
        WHERE id_tren = :NEW.tren_id 
          AND estado_operativo = 'En Operación';
    END IF;
END;
/

-- 6. Trigger: Impedir la asignacion de un tren en mantenimiento a un viaje
CREATE OR REPLACE TRIGGER TRG_TREN_MANTENIMIENTO_NO_ASIGNAR
BEFORE INSERT OR UPDATE OF tren_id, estado ON VIAJE_PROGRAMADO
FOR EACH ROW
DECLARE
    v_estado_tren VARCHAR2(30);
BEGIN
    IF :NEW.estado IN ('Programado', 'En Abordaje', 'En Curso') THEN
        SELECT estado_operativo
        INTO v_estado_tren
        FROM TREN
        WHERE id_tren = :NEW.tren_id;

        IF v_estado_tren = 'En Mantenimiento' THEN
            RAISE_APPLICATION_ERROR(-20013, 'Operacion rechazada: No se puede asignar a un viaje el tren ' || :NEW.tren_id || ' porque se encuentra en mantenimiento.');
        ELSIF v_estado_tren = 'Fuera de Servicio' OR v_estado_tren = 'Retirado' THEN
            RAISE_APPLICATION_ERROR(-20014, 'Operacion rechazada: El tren seleccionado esta fuera de servicio o retirado.');
        END IF;
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        NULL;
END;
/

-- 7. Trigger: Validación de Certificación Técnica y Rol Compatible en Viajes
CREATE OR REPLACE TRIGGER TRG_CERTIFICACION_ALERTA_VENCIDA
BEFORE INSERT OR UPDATE OF conductor_id, fecha ON VIAJE_PROGRAMADO
FOR EACH ROW
DECLARE
    v_certificaciones_validas NUMBER := 0;
    v_cargo VARCHAR2(50);
BEGIN
    IF :NEW.conductor_id IS NOT NULL THEN
        -- 1. Validar compatibilidad de rol / cargo
        SELECT cargo INTO v_cargo
        FROM EMPLEADO
        WHERE id_empleado = :NEW.conductor_id;

        IF v_cargo NOT IN ('Conductor', 'Operador de Control') THEN
            RAISE_APPLICATION_ERROR(-20016, 'Rol incompatible: El empleado asignado tiene el cargo "' || v_cargo || '" y no esta facultado como Conductor de viaje.');
        END IF;

        -- 2. Validar certificación técnica vigente
        SELECT COUNT(*)
        INTO v_certificaciones_validas
        FROM CERTIFICACION
        WHERE empleado_id = :NEW.conductor_id
          AND estado = 'Vigente'
          AND fecha_vencimiento >= :NEW.fecha;

        IF v_certificaciones_validas = 0 THEN
            RAISE_APPLICATION_ERROR(-20015, 'Operacion rechazada: El conductor asignado (ID ' || :NEW.conductor_id || ') no posee una certificacion tecnica vigente para la fecha del viaje.');
        END IF;
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20017, 'Empleado inexistente: El conductor asignado no figura en el padron de personal.');
END;
/

-- 8. Trigger: Auditoria de incidentes y detección de desescalamiento no autorizado en BITACORA
CREATE OR REPLACE TRIGGER TRG_INCIDENTE_AUDITORIA
AFTER INSERT OR UPDATE ON INCIDENTE
FOR EACH ROW
BEGIN
    IF INSERTING THEN
        INSERT INTO BITACORA (
            id_bitacora, fecha_hora, tabla_afectada,
            operacion, registro_id, usuario, descripcion
        ) VALUES (
            SEQ_BITACORA.NEXTVAL, SYSTIMESTAMP, 'INCIDENTE',
            'INSERT', :NEW.id_incidente, USER,
            'Apertura de nuevo incidente: ' || :NEW.numero_incidente || ' (' || :NEW.tipo || ') - Severidad: ' || :NEW.nivel_severidad
        );
    ELSIF UPDATING THEN
        -- Alerta de escalabilidad ante reducción drástica de severidad
        IF (:OLD.nivel_severidad IN ('Crítico', 'Critico', 'Alto', 'Alta') 
            AND :NEW.nivel_severidad IN ('Bajo', 'Baja', 'Medio', 'Media')) THEN
            INSERT INTO BITACORA (
                id_bitacora, fecha_hora, tabla_afectada,
                operacion, registro_id, usuario, descripcion
            ) VALUES (
                SEQ_BITACORA.NEXTVAL, SYSTIMESTAMP, 'INCIDENTE',
                'ALERTA_ESCALABILIDAD', :NEW.id_incidente, USER,
                'ALERTA_ESCALABILIDAD: Reducción de severidad (' || :OLD.nivel_severidad || ' -> ' || :NEW.nivel_severidad || ') en incidente ' || :NEW.numero_incidente
            );
        END IF;

        INSERT INTO BITACORA (
            id_bitacora, fecha_hora, tabla_afectada,
            operacion, registro_id, usuario, descripcion
        ) VALUES (
            SEQ_BITACORA.NEXTVAL, SYSTIMESTAMP, 'INCIDENTE',
            'UPDATE', :NEW.id_incidente, USER,
            'Actualizacion incidente ' || :NEW.numero_incidente || ' - Estado: ' || :NEW.estado || ' - Pasajeros estimados: ' || :NEW.pasajeros_afectados_estimado
        );
    END IF;
END;
/

-- 9. Trigger: Validación de estación activa para paradas de ruta
CREATE OR REPLACE TRIGGER TRG_VALIDA_ESTACION_ACTIVA
BEFORE INSERT OR UPDATE OF estacion_id ON RUTA_DETALLE
FOR EACH ROW
DECLARE
    v_estado VARCHAR2(30);
    v_nombre VARCHAR2(100);
BEGIN
    SELECT estado_operativo, nombre INTO v_estado, v_nombre
    FROM ESTACION
    WHERE id_estacion = :NEW.estacion_id;

    IF v_estado IN ('Cerrada', 'Inactiva') THEN
        RAISE_APPLICATION_ERROR(-20010, 'No se puede asignar la parada: la estacion ' || v_nombre || ' esta ' || v_estado || '.');
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20011, 'Estacion inexistente en la red de metro.');
END;
/

-- 10. Trigger: Evitar viajes en fechas pasadas remotas o incoherentes
CREATE OR REPLACE TRIGGER TRG_VIAJE_FECHA_VALIDA
BEFORE INSERT OR UPDATE OF fecha, hora_prog_salida ON VIAJE_PROGRAMADO
FOR EACH ROW
BEGIN
    IF :NEW.fecha < TO_DATE('2020-01-01', 'YYYY-MM-DD') THEN
        RAISE_APPLICATION_ERROR(-20020, 'Fecha de viaje invalida: No se permite programar viajes con fechas en el pasado remoto (' || TO_CHAR(:NEW.fecha, 'YYYY-MM-DD') || ').');
    END IF;
END;
/

-- 11. Trigger: Validación de Año de Fabricación en TREN [1950 .. SYSDATE + 1]
CREATE OR REPLACE TRIGGER TRG_TREN_VALIDA_ANIO
BEFORE INSERT OR UPDATE OF anio_fabricacion ON TREN
FOR EACH ROW
BEGIN
    IF :NEW.anio_fabricacion IS NOT NULL THEN
        IF :NEW.anio_fabricacion < 1950 OR :NEW.anio_fabricacion > EXTRACT(YEAR FROM SYSDATE) + 1 THEN
            RAISE_APPLICATION_ERROR(-20038, 'Anio de fabricacion invalido para el tren: Debe estar comprendido entre 1950 y ' || (EXTRACT(YEAR FROM SYSDATE) + 1) || '.');
        END IF;
    END IF;
END;
/

-- 12. Trigger: Validación de Año de Fabricación en VAGON [1950 .. SYSDATE + 1]
CREATE OR REPLACE TRIGGER TRG_VAGON_VALIDA_ANIO
BEFORE INSERT OR UPDATE OF anio_fabricacion ON VAGON
FOR EACH ROW
BEGIN
    IF :NEW.anio_fabricacion IS NOT NULL THEN
        IF :NEW.anio_fabricacion < 1950 OR :NEW.anio_fabricacion > EXTRACT(YEAR FROM SYSDATE) + 1 THEN
            RAISE_APPLICATION_ERROR(-20039, 'Anio de fabricacion invalido para el vagon: Debe estar comprendido entre 1950 y ' || (EXTRACT(YEAR FROM SYSDATE) + 1) || '.');
        END IF;
    END IF;
END;
/

-- 13. Trigger: Protección contra Reducción de Odómetro en TREN
CREATE OR REPLACE TRIGGER TRG_TREN_ODOMETRO_PROTECCION
BEFORE UPDATE OF kilometraje_acumulado ON TREN
FOR EACH ROW
BEGIN
    IF :NEW.kilometraje_acumulado < :OLD.kilometraje_acumulado THEN
        RAISE_APPLICATION_ERROR(-20031, 'Intento de manipulacion de odometro: El kilometraje acumulado no puede reducirse (Valor actual: ' || :OLD.kilometraje_acumulado || ', Nuevo: ' || :NEW.kilometraje_acumulado || ').');
    END IF;
END;
/

-- 14. Trigger: Prevención de Eliminación Física de Tren con Historial Operativo (Regla 25)
CREATE OR REPLACE TRIGGER TRG_TREN_PREVENIR_DELETE
BEFORE DELETE ON TREN
FOR EACH ROW
DECLARE
    v_viajes NUMBER;
    v_vagones NUMBER;
    v_ordenes NUMBER;
    v_incidentes NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_viajes FROM VIAJE_PROGRAMADO WHERE tren_id = :OLD.id_tren;
    IF v_viajes > 0 THEN
        RAISE_APPLICATION_ERROR(-20032, 'Integridad operativa: No se puede eliminar fisicamente un tren con historial de viajes (' || v_viajes || ' viajes registrados). Utilice la baja logica (Retirado).');
    END IF;

    SELECT COUNT(*) INTO v_vagones FROM TREN_VAGON WHERE tren_id = :OLD.id_tren;
    IF v_vagones > 0 THEN
        RAISE_APPLICATION_ERROR(-20036, 'Integridad de flota: No se puede eliminar el tren porque posee ' || v_vagones || ' registro(s) de acoplamiento historico (Regla 25).');
    END IF;

    SELECT COUNT(*) INTO v_ordenes FROM ORDEN_MANTENIMIENTO om
    JOIN EQUIPO eq ON om.equipo_id = eq.id_equipo
    WHERE eq.tipo_referencia = 'TREN' AND eq.referencia_id = :OLD.id_tren;
    IF v_ordenes > 0 THEN
        RAISE_APPLICATION_ERROR(-20037, 'Integridad de mantenimiento: No se puede eliminar el tren porque posee historial de ordenes de mantenimiento (' || v_ordenes || ' ordenes).');
    END IF;

    SELECT COUNT(*) INTO v_incidentes FROM INCIDENTE_ELEMENTO_AFECTADO WHERE tren_id = :OLD.id_tren;
    IF v_incidentes > 0 THEN
        RAISE_APPLICATION_ERROR(-20040, 'Integridad de seguridad: No se puede eliminar el tren porque figura en ' || v_incidentes || ' reporte(s) de incidentes.');
    END IF;
END;
/

-- 15. Trigger: Bloqueo de cambio a Mantenimiento o Fuera de Servicio si tiene viajes activos
CREATE OR REPLACE TRIGGER TRG_TREN_ESTADO_OPERATIVO_CHK
BEFORE UPDATE OF estado_operativo ON TREN
FOR EACH ROW
DECLARE
    v_viajes_activos NUMBER;
BEGIN
    IF :NEW.estado_operativo IN ('En Mantenimiento', 'Fuera de Servicio', 'Retirado') THEN
        SELECT COUNT(*) INTO v_viajes_activos
        FROM VIAJE_PROGRAMADO
        WHERE tren_id = :NEW.id_tren AND estado IN ('En Curso', 'En Abordaje');

        IF v_viajes_activos > 0 THEN
            RAISE_APPLICATION_ERROR(-20033, 'Conflicto operativo: No se puede cambiar el tren ' || :NEW.codigo_interno || ' a ' || :NEW.estado_operativo || ' mientras tiene ' || v_viajes_activos || ' viaje(s) activo(s) en curso o abordaje.');
        END IF;
    END IF;
END;
/

-- 16. Trigger: Validación de Edad Mínima Laboral (Mínimo 18 años cumplidos)
CREATE OR REPLACE TRIGGER TRG_EMPLEADO_EDAD_MINIMA
BEFORE INSERT OR UPDATE OF fecha_nacimiento ON EMPLEADO
FOR EACH ROW
BEGIN
    IF :NEW.fecha_nacimiento IS NOT NULL THEN
        IF :NEW.fecha_nacimiento > ADD_MONTHS(SYSDATE, -18 * 12) THEN
            RAISE_APPLICATION_ERROR(-20041, 'Validacion laboral: El empleado debe tener al menos 18 anios de edad cumplidos (Fecha nacimiento: ' || TO_CHAR(:NEW.fecha_nacimiento, 'YYYY-MM-DD') || ').');
        END IF;
    END IF;
END;
/

-- 17. Trigger: Prevención de Sobreescritura / Solapamiento de Turnos
CREATE OR REPLACE TRIGGER TRG_TURNO_NO_SOLAPADO
BEFORE INSERT OR UPDATE OF empleado_id, fecha, hora_inicio, hora_fin ON TURNO
FOR EACH ROW
DECLARE
    v_conflicto NUMBER := 0;
BEGIN
    IF :NEW.estado_asistencia NOT IN ('Sustituido', 'Permiso', 'Vacaciones') THEN
        SELECT COUNT(*)
        INTO v_conflicto
        FROM TURNO
        WHERE empleado_id = :NEW.empleado_id
          AND fecha = :NEW.fecha
          AND id_turno != NVL(:NEW.id_turno, -1)
          AND estado_asistencia NOT IN ('Sustituido', 'Permiso', 'Vacaciones')
          AND hora_inicio < :NEW.hora_fin
          AND hora_fin > :NEW.hora_inicio;

        IF v_conflicto > 0 THEN
            RAISE_APPLICATION_ERROR(-20042, 'Conflicto de turno: El empleado (ID ' || :NEW.empleado_id || ') ya tiene un turno programado que se solapa en el horario indicado para la fecha ' || TO_CHAR(:NEW.fecha, 'YYYY-MM-DD') || '.');
        END IF;
    END IF;
END;
/

-- 18. Trigger: Validación de Duración de Turno y Límite de Jornada (Máx 16 horas)
CREATE OR REPLACE TRIGGER TRG_TURNO_DURACION_MAXIMA
BEFORE INSERT OR UPDATE OF hora_inicio, hora_fin ON TURNO
FOR EACH ROW
DECLARE
    v_diff_hours NUMBER;
BEGIN
    IF :NEW.hora_fin <= :NEW.hora_inicio THEN
        RAISE_APPLICATION_ERROR(-20043, 'Horario invalido: La hora de finalizacion del turno debe ser posterior a la hora de inicio.');
    END IF;

    v_diff_hours := (
        EXTRACT(DAY FROM (:NEW.hora_fin - :NEW.hora_inicio)) * 24 +
        EXTRACT(HOUR FROM (:NEW.hora_fin - :NEW.hora_inicio)) +
        EXTRACT(MINUTE FROM (:NEW.hora_fin - :NEW.hora_inicio)) / 60
    );

    IF v_diff_hours > 16 THEN
        RAISE_APPLICATION_ERROR(-20044, 'Jornada laboral excedida: La duracion del turno (' || ROUND(v_diff_hours, 1) || ' horas) no puede superar el limite reglamentario de 16 horas continuas.');
    END IF;
END;
/

-- 19. Trigger: Inmutabilidad de Certificaciones Históricas / Vencidas
CREATE OR REPLACE TRIGGER TRG_CERTIFICACION_INMUTABLE
BEFORE UPDATE ON CERTIFICACION
FOR EACH ROW
BEGIN
    IF :OLD.estado IN ('Vencida', 'Revocada') THEN
        IF :OLD.fecha_vencimiento != :NEW.fecha_vencimiento OR :OLD.fecha_emision != :NEW.fecha_emision THEN
            RAISE_APPLICATION_ERROR(-20045, 'Inmutabilidad de historico: No se permite modificar las fechas de una certificacion en estado "' || :OLD.estado || '". Registre una nueva emision o renovacion de licencia.');
        END IF;
    END IF;
END;
/

-- 20. Trigger: Fecha de emisión de tarjeta no puede ser futura
CREATE OR REPLACE TRIGGER TRG_TARJETA_FECHA_EMISION
BEFORE INSERT OR UPDATE OF fecha_emision ON TARJETA
FOR EACH ROW
BEGIN
    IF :NEW.fecha_emision IS NOT NULL AND :NEW.fecha_emision > SYSDATE THEN
        RAISE_APPLICATION_ERROR(-20052, 'Validacion temporal: La fecha de emision de la tarjeta no puede ser futura.');
    END IF;
END;
/

-- 21. Trigger: Validación de tarjeta en torniquetes (no bloqueada ni vencida)
CREATE OR REPLACE TRIGGER TRG_ACCESO_VALIDAR_TARJETA
BEFORE INSERT ON VIAJE_PASAJERO
FOR EACH ROW
DECLARE
    v_estado VARCHAR2(30);
    v_venc   DATE;
BEGIN
    SELECT estado, fecha_vencimiento
    INTO v_estado, v_venc
    FROM TARJETA
    WHERE id_tarjeta = :NEW.tarjeta_id;

    IF v_estado != 'Activa' THEN
        RAISE_APPLICATION_ERROR(-20055, 'Acceso denegado: La tarjeta se encuentra inhabilitada (Estado: ' || v_estado || ').');
    END IF;

    IF v_venc IS NOT NULL AND v_venc < TRUNC(SYSDATE) THEN
        RAISE_APPLICATION_ERROR(-20057, 'Acceso denegado: La tarjeta se encuentra vencida con fecha ' || TO_CHAR(v_venc, 'YYYY-MM-DD') || '.');
    END IF;
END;
/

-- 22. Trigger: Secuencia cronológica en torniquetes (no tap-in previo a su último acceso)
CREATE OR REPLACE TRIGGER TRG_ACCESO_SECUENCIA_TEMPORAL
BEFORE INSERT ON VIAJE_PASAJERO
FOR EACH ROW
DECLARE
    v_max_fecha TIMESTAMP;
BEGIN
    SELECT MAX(fecha_hora_ingreso)
    INTO v_max_fecha
    FROM VIAJE_PASAJERO
    WHERE tarjeta_id = :NEW.tarjeta_id;

    IF v_max_fecha IS NOT NULL AND :NEW.fecha_hora_ingreso < v_max_fecha THEN
        RAISE_APPLICATION_ERROR(-20053, 'Inconsistencia temporal: No se puede registrar un acceso anterior al ultimo ingreso registrado (' || TO_CHAR(v_max_fecha, 'YYYY-MM-DD HH24:MI:SS') || ').');
    END IF;
END;
/

-- 23. Trigger: Antifraude / Multitap (velocidad imposible entre estaciones distintas < 5 min)
CREATE OR REPLACE TRIGGER TRG_ACCESO_ANTIFRAUDE
BEFORE INSERT ON VIAJE_PASAJERO
FOR EACH ROW
DECLARE
    v_ult_estacion NUMBER;
    v_ult_fecha    TIMESTAMP;
    v_diff_seg     NUMBER;
BEGIN
    BEGIN
        SELECT estacion_ingreso_id, fecha_hora_ingreso
        INTO v_ult_estacion, v_ult_fecha
        FROM (
            SELECT estacion_ingreso_id, fecha_hora_ingreso
            FROM VIAJE_PASAJERO
            WHERE tarjeta_id = :NEW.tarjeta_id
            ORDER BY fecha_hora_ingreso DESC
        )
        WHERE ROWNUM = 1;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            v_ult_estacion := NULL;
    END;

    IF v_ult_estacion IS NOT NULL AND v_ult_estacion != :NEW.estacion_ingreso_id THEN
        v_diff_seg := ABS(
            EXTRACT(DAY FROM (:NEW.fecha_hora_ingreso - v_ult_fecha)) * 86400 +
            EXTRACT(HOUR FROM (:NEW.fecha_hora_ingreso - v_ult_fecha)) * 3600 +
            EXTRACT(MINUTE FROM (:NEW.fecha_hora_ingreso - v_ult_fecha)) * 60 +
            EXTRACT(SECOND FROM (:NEW.fecha_hora_ingreso - v_ult_fecha))
        );
        IF v_diff_seg < 300 THEN
            RAISE_APPLICATION_ERROR(-20054, 'Alerta de antifraude / multitap: Acceso simultaneo o velocidad imposible entre estaciones distintas (' || ROUND(v_diff_seg) || ' segundos transcurridos, minimo 300 segundos requerido).');
        END IF;
    END IF;
END;
/

-- 24. Trigger: Integridad de Ledger y Auditoria en VIAJE_PASAJERO
CREATE OR REPLACE TRIGGER TRG_VIAJE_PASAJERO_AUDITORIA
BEFORE DELETE OR UPDATE OF id_viaje_pasajero, numero_transaccion, tarjeta_id, estacion_ingreso_id, fecha_hora_ingreso, tarifa_id, monto_cobrado ON VIAJE_PASAJERO
FOR EACH ROW
DECLARE
    v_tipo_soporte VARCHAR2(20);
BEGIN
    IF DELETING THEN
        BEGIN
            SELECT NVL(tipo_soporte, 'Tarjeta') INTO v_tipo_soporte
            FROM TARJETA
            WHERE id_tarjeta = :OLD.tarjeta_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                v_tipo_soporte := 'Boleto';
        END;

        IF v_tipo_soporte != 'Boleto' THEN
            RAISE_APPLICATION_ERROR(-20059, 'Integridad de ledger: No esta permitido eliminar registros historicos de viajes/accesos de tarjetas.');
        END IF;
    ELSE
        RAISE_APPLICATION_ERROR(-20060, 'Integridad contable: No esta permitido alterar el cargo financiero, tarifa o tarjeta de un acceso ya registrado.');
    END IF;
END;
/

-- 25. Trigger: Inmutabilidad y Auditoria Financiera en RECARGA
CREATE OR REPLACE TRIGGER TRG_RECARGA_PREVENIR_DELETE
BEFORE DELETE OR UPDATE OF id_recarga, numero_transaccion, tarjeta_id, monto, saldo_anterior, saldo_posterior ON RECARGA
FOR EACH ROW
BEGIN
    IF DELETING THEN
        RAISE_APPLICATION_ERROR(-20056, 'Regla de auditoria financiera: No esta permitido eliminar transacciones de recarga registradas.');
    ELSE
        RAISE_APPLICATION_ERROR(-20061, 'Regla de auditoria financiera: No esta permitido alterar montos o saldos de transacciones de recarga ya emitidas.');
    END IF;
END;
/

-- 26. Trigger: Validar y actualizar stock disponible al consumir repuestos
CREATE OR REPLACE TRIGGER TRG_CONSUMO_REPUESTO_STOCK
BEFORE INSERT OR UPDATE OR DELETE ON ORDEN_REPUESTO
FOR EACH ROW
DECLARE
    v_stock_actual NUMBER := 0;
    v_ord_estado   VARCHAR2(30);
    v_diff         NUMBER;
BEGIN
    -- Validar que la orden asociada no este cerrada/completada
    IF INSERTING OR UPDATING THEN
        SELECT estado INTO v_ord_estado FROM ORDEN_MANTENIMIENTO WHERE id_orden = :NEW.orden_id;
    ELSE
        SELECT estado INTO v_ord_estado FROM ORDEN_MANTENIMIENTO WHERE id_orden = :OLD.orden_id;
    END IF;

    IF v_ord_estado IN ('Completada', 'Cerrada') THEN
        RAISE_APPLICATION_ERROR(-20076, 'No se permite modificar consumos de repuestos de una orden de mantenimiento completada/cerrada.');
    END IF;

    -- Manejo de inventario segun operacion
    IF INSERTING THEN
        BEGIN
            SELECT stock_disponible INTO v_stock_actual
            FROM REPUESTO
            WHERE id_repuesto = :NEW.repuesto_id
            FOR UPDATE;

            IF v_stock_actual < :NEW.cantidad THEN
                RAISE_APPLICATION_ERROR(-20071, 'Stock insuficiente para el repuesto ID ' || :NEW.repuesto_id || '. Disponible: ' || v_stock_actual || ', Solicitado: ' || :NEW.cantidad);
            END IF;

            UPDATE REPUESTO
            SET stock_disponible = stock_disponible - :NEW.cantidad
            WHERE id_repuesto = :NEW.repuesto_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                NULL;
        END;

    ELSIF UPDATING THEN
        IF :NEW.repuesto_id = :OLD.repuesto_id THEN
            v_diff := :NEW.cantidad - :OLD.cantidad;
            IF v_diff > 0 THEN
                SELECT stock_disponible INTO v_stock_actual
                FROM REPUESTO
                WHERE id_repuesto = :NEW.repuesto_id
                FOR UPDATE;

                IF v_stock_actual < v_diff THEN
                    RAISE_APPLICATION_ERROR(-20071, 'Stock insuficiente para ampliar consumo de repuesto ID ' || :NEW.repuesto_id || '. Disponible: ' || v_stock_actual || ', Requerido adicional: ' || v_diff);
                END IF;

                UPDATE REPUESTO
                SET stock_disponible = stock_disponible - v_diff
                WHERE id_repuesto = :NEW.repuesto_id;
            ELSIF v_diff < 0 THEN
                UPDATE REPUESTO
                SET stock_disponible = stock_disponible + ABS(v_diff)
                WHERE id_repuesto = :NEW.repuesto_id;
            END IF;
        ELSE
            -- Cambio de repuesto: restaurar antiguo y descontar del nuevo
            UPDATE REPUESTO
            SET stock_disponible = stock_disponible + :OLD.cantidad
            WHERE id_repuesto = :OLD.repuesto_id;

            SELECT stock_disponible INTO v_stock_actual
            FROM REPUESTO
            WHERE id_repuesto = :NEW.repuesto_id
            FOR UPDATE;

            IF v_stock_actual < :NEW.cantidad THEN
                RAISE_APPLICATION_ERROR(-20071, 'Stock insuficiente para el nuevo repuesto ID ' || :NEW.repuesto_id || '. Disponible: ' || v_stock_actual || ', Solicitado: ' || :NEW.cantidad);
            END IF;

            UPDATE REPUESTO
            SET stock_disponible = stock_disponible - :NEW.cantidad
            WHERE id_repuesto = :NEW.repuesto_id;
        END IF;

    ELSIF DELETING THEN
        UPDATE REPUESTO
        SET stock_disponible = stock_disponible + :OLD.cantidad
        WHERE id_repuesto = :OLD.repuesto_id;
    END IF;
END;
/

-- 27. Trigger: Inmutabilidad histórica de órdenes completadas/cerradas
CREATE OR REPLACE TRIGGER TRG_ORDEN_MANT_HISTORICO
BEFORE UPDATE OR DELETE ON ORDEN_MANTENIMIENTO
FOR EACH ROW
BEGIN
    IF DELETING THEN
        IF :OLD.estado IN ('Completada', 'Cerrada') THEN
            RAISE_APPLICATION_ERROR(-20076, 'No se permite eliminar una orden de mantenimiento completada/cerrada (registro histórico inmutable).');
        END IF;
    ELSIF UPDATING THEN
        IF :OLD.estado IN ('Completada', 'Cerrada') THEN
            IF :OLD.costo != :NEW.costo 
               OR :OLD.descripcion_trabajo != :NEW.descripcion_trabajo
               OR :OLD.equipo_id != :NEW.equipo_id
               OR :OLD.tipo_mantenimiento != :NEW.tipo_mantenimiento
               OR (:OLD.fecha_inicio IS NOT NULL AND :NEW.fecha_inicio IS NOT NULL AND :OLD.fecha_inicio != :NEW.fecha_inicio)
               OR (:OLD.fecha_finalizacion IS NOT NULL AND :NEW.fecha_finalizacion IS NOT NULL AND :OLD.fecha_finalizacion != :NEW.fecha_finalizacion)
            THEN
                RAISE_APPLICATION_ERROR(-20076, 'No se permite modificar datos técnicos, fechas ni costos de una orden de mantenimiento completada/cerrada.');
            END IF;
        END IF;
    END IF;
END;
/

-- 28. Trigger: Validación al cerrar/completar orden de trabajo
CREATE OR REPLACE TRIGGER TRG_ORDEN_MANT_VALIDAR_CIERRE
BEFORE UPDATE OF estado ON ORDEN_MANTENIMIENTO
FOR EACH ROW
DECLARE
    v_count_tec NUMBER := 0;
BEGIN
    IF :NEW.estado IN ('Completada', 'Cerrada') AND :OLD.estado NOT IN ('Completada', 'Cerrada') THEN
        -- Exigir al menos un técnico asignado
        SELECT COUNT(*) INTO v_count_tec
        FROM ORDEN_TECNICO
        WHERE orden_id = :NEW.id_orden;

        IF v_count_tec = 0 THEN
            RAISE_APPLICATION_ERROR(-20074, 'No se puede cerrar una orden de trabajo sin técnicos asignados en cuadrilla.');
        END IF;

        -- Exigir descripción válida
        IF :NEW.descripcion_trabajo IS NULL OR LENGTH(TRIM(:NEW.descripcion_trabajo)) < 3 THEN
            RAISE_APPLICATION_ERROR(-20075, 'No se puede cerrar una orden de trabajo sin descripción válida del trabajo realizado.');
        END IF;
    END IF;
END;
/

-- 29. Trigger: Prevenir asignación de mantenimiento a trenes/equipos dados de baja
CREATE OR REPLACE TRIGGER TRG_ORDEN_MANT_VALIDAR_EQUIPO
BEFORE INSERT ON ORDEN_MANTENIMIENTO
FOR EACH ROW
DECLARE
    v_tipo_ref    VARCHAR2(30);
    v_ref_id      NUMBER;
    v_eq_estado   VARCHAR2(30);
    v_tren_estado VARCHAR2(30);
BEGIN
    SELECT tipo_referencia, referencia_id, estado
    INTO v_tipo_ref, v_ref_id, v_eq_estado
    FROM EQUIPO
    WHERE id_equipo = :NEW.equipo_id;

    IF v_tipo_ref = 'TREN' AND v_ref_id IS NOT NULL THEN
        SELECT estado_operativo INTO v_tren_estado
        FROM TREN
        WHERE id_tren = v_ref_id;

        IF v_tren_estado IN ('Retirado', 'Dado de Baja') THEN
            RAISE_APPLICATION_ERROR(-20077, 'No se puede asignar mantenimiento a un tren que ha sido dado de baja o retirado del servicio activo.');
        END IF;
    END IF;

    IF v_eq_estado IN ('Retirado', 'Dado de Baja') THEN
        RAISE_APPLICATION_ERROR(-20078, 'No se puede programar mantenimiento para un activo retirado o dado de baja.');
    END IF;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE_APPLICATION_ERROR(-20080, 'El activo/equipo ID ' || :NEW.equipo_id || ' especificado no existe.');
END;
/

-- 30. Trigger: Validaciones en asignación técnica (ORDEN_TECNICO)
CREATE OR REPLACE TRIGGER TRG_ORDEN_TECNICO_VALIDAR
BEFORE INSERT OR UPDATE OR DELETE ON ORDEN_TECNICO
FOR EACH ROW
DECLARE
    v_ord_estado  VARCHAR2(30);
    v_emp_estado  VARCHAR2(30);
    v_emp_cargo   VARCHAR2(100);
    v_count_cert  NUMBER := 0;
BEGIN
    IF DELETING THEN
        SELECT estado INTO v_ord_estado FROM ORDEN_MANTENIMIENTO WHERE id_orden = :OLD.orden_id;
        IF v_ord_estado IN ('Completada', 'Cerrada') THEN
            RAISE_APPLICATION_ERROR(-20076, 'No se permite modificar la cuadrilla técnica de una orden completada/cerrada.');
        END IF;
    ELSE
        SELECT estado INTO v_ord_estado FROM ORDEN_MANTENIMIENTO WHERE id_orden = :NEW.orden_id;
        IF v_ord_estado IN ('Completada', 'Cerrada') THEN
            RAISE_APPLICATION_ERROR(-20076, 'No se permite asignar técnicos a una orden completada/cerrada.');
        END IF;

        -- Validar empleado activo y cargo técnico
        SELECT estado_laboral, cargo INTO v_emp_estado, v_emp_cargo
        FROM EMPLEADO
        WHERE id_empleado = :NEW.empleado_id;

        IF v_emp_estado != 'Activo' THEN
            RAISE_APPLICATION_ERROR(-20072, 'El empleado asignado no se encuentra activo laboralmente.');
        END IF;

        IF v_emp_cargo NOT LIKE '%T%cnico%' AND v_emp_cargo NOT LIKE '%Mantenimiento%' THEN
            RAISE_APPLICATION_ERROR(-20073, 'Solo personal con cargo técnico puede ser asignado a órdenes de mantenimiento.');
        END IF;

        -- Validar certificación vigente si se le asigna rol de especialista
        IF :NEW.rol_en_orden LIKE '%Especialista%' THEN
            SELECT COUNT(*) INTO v_count_cert
            FROM CERTIFICACION
            WHERE empleado_id = :NEW.empleado_id
              AND estado = 'Vigente'
              AND (fecha_vencimiento IS NULL OR fecha_vencimiento >= TRUNC(SYSDATE));

            IF v_count_cert = 0 THEN
                RAISE_APPLICATION_ERROR(-20079, 'El técnico no cuenta con certificaciones técnicas vigentes para actuar como especialista.');
            END IF;
        END IF;
    END IF;
END;
/

-- 31. Trigger: Validación Temporal: Rechazo de Fecha Futura en INCIDENTE
CREATE OR REPLACE TRIGGER TRG_INCIDENTE_VALIDAR_FECHA
BEFORE INSERT OR UPDATE OF fecha_hora_inicio ON INCIDENTE
FOR EACH ROW
BEGIN
    IF :NEW.fecha_hora_inicio > SYSTIMESTAMP + INTERVAL '5' MINUTE THEN
        RAISE_APPLICATION_ERROR(-20080, 'La fecha y hora de inicio del incidente no puede ser futura.');
    END IF;
END;
/

-- 32. Trigger: Validación de Cierre Técnico e Integridad de Resolución en INCIDENTE
CREATE OR REPLACE TRIGGER TRG_INCIDENTE_VALIDAR_CIERRE
BEFORE INSERT OR UPDATE ON INCIDENTE
FOR EACH ROW
BEGIN
    IF :NEW.estado = 'Cerrado' THEN
        IF (:NEW.resolucion IS NULL OR LENGTH(TRIM(:NEW.resolucion)) < 3)
           AND ((:NEW.causa_identificada IS NULL OR LENGTH(TRIM(:NEW.causa_identificada)) < 3)
                OR (:NEW.acciones_realizadas IS NULL OR LENGTH(TRIM(:NEW.acciones_realizadas)) < 3)) THEN
            RAISE_APPLICATION_ERROR(-20083, 'No se puede cerrar un incidente sin documentar la causa raíz y las acciones correctivas o resolución técnica.');
        END IF;

        IF :NEW.resolucion IS NOT NULL AND :NEW.acciones_realizadas IS NULL THEN
            :NEW.acciones_realizadas := :NEW.resolucion;
        ELSIF :NEW.acciones_realizadas IS NOT NULL AND :NEW.resolucion IS NULL THEN
            :NEW.resolucion := :NEW.acciones_realizadas;
        END IF;

        IF :NEW.fecha_hora_fin IS NULL THEN
            :NEW.fecha_hora_fin := SYSTIMESTAMP;
        END IF;

        IF :NEW.fecha_hora_fin < :NEW.fecha_hora_inicio THEN
            RAISE_APPLICATION_ERROR(-20082, 'La fecha de resolución no puede ser anterior a la apertura del incidente.');
        END IF;
    END IF;
END;
/

-- 33. Trigger: Políticas de Retención de Históricos (Bloqueo de DELETE en INCIDENTE)
CREATE OR REPLACE TRIGGER TRG_INCIDENTE_RETENCION_HISTORICA
BEFORE DELETE ON INCIDENTE
FOR EACH ROW
BEGIN
    IF :OLD.estado = 'Cerrado' 
       OR :OLD.nivel_severidad IN ('Crítico', 'Critico', 'Alto', 'Alta')
       OR :OLD.fecha_hora_inicio < SYSTIMESTAMP - INTERVAL '1' DAY THEN
        RAISE_APPLICATION_ERROR(-20081, 'Políticas de retención y auditoría prohíben la eliminación física de incidentes históricos o críticos.');
    END IF;
END;
/

-- 34. Compound Trigger: Validación de Consistencia Geográfica y Flota Cruzada
CREATE OR REPLACE TRIGGER TRG_INC_ELEM_VALIDAR_CRUCE
FOR INSERT OR UPDATE ON INCIDENTE_ELEMENTO_AFECTADO
COMPOUND TRIGGER
    TYPE t_elem IS RECORD (
        incidente_id NUMBER,
        tipo_elemento VARCHAR2(20),
        tren_id NUMBER,
        linea_id NUMBER
    );
    TYPE t_elem_list IS TABLE OF t_elem INDEX BY PLS_INTEGER;
    g_elems t_elem_list;
    g_count PLS_INTEGER := 0;

    BEFORE STATEMENT IS
    BEGIN
        g_count := 0;
        g_elems.DELETE;
    END BEFORE STATEMENT;

    AFTER EACH ROW IS
    BEGIN
        g_count := g_count + 1;
        g_elems(g_count).incidente_id := :NEW.incidente_id;
        g_elems(g_count).tipo_elemento := :NEW.tipo_elemento;
        g_elems(g_count).tren_id := :NEW.tren_id;
        g_elems(g_count).linea_id := :NEW.linea_id;
    END AFTER EACH ROW;

    AFTER STATEMENT IS
        v_incompatible NUMBER;
    BEGIN
        FOR i IN 1..g_count LOOP
            IF g_elems(i).tipo_elemento = 'TREN' AND g_elems(i).tren_id IS NOT NULL THEN
                SELECT COUNT(*) INTO v_incompatible
                FROM INCIDENTE_ELEMENTO_AFECTADO a
                WHERE a.incidente_id = g_elems(i).incidente_id
                  AND a.tipo_elemento = 'LINEA'
                  AND a.linea_id IS NOT NULL
                  AND EXISTS (
                      SELECT 1 FROM VIAJE_PROGRAMADO vp
                      WHERE vp.tren_id = g_elems(i).tren_id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM VIAJE_PROGRAMADO vp
                      JOIN RUTA r ON vp.ruta_id = r.id_ruta
                      WHERE vp.tren_id = g_elems(i).tren_id
                        AND r.linea_id = a.linea_id
                  );
                IF v_incompatible > 0 THEN
                    RAISE_APPLICATION_ERROR(-20086, 'Inconsistencia operativa de red: El tren ' || g_elems(i).tren_id || ' no opera en la línea asociada al incidente.');
                END IF;
            ELSIF g_elems(i).tipo_elemento = 'LINEA' AND g_elems(i).linea_id IS NOT NULL THEN
                SELECT COUNT(*) INTO v_incompatible
                FROM INCIDENTE_ELEMENTO_AFECTADO a
                WHERE a.incidente_id = g_elems(i).incidente_id
                  AND a.tipo_elemento = 'TREN'
                  AND a.tren_id IS NOT NULL
                  AND EXISTS (
                      SELECT 1 FROM VIAJE_PROGRAMADO vp
                      WHERE vp.tren_id = a.tren_id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM VIAJE_PROGRAMADO vp
                      JOIN RUTA r ON vp.ruta_id = r.id_ruta
                      WHERE vp.tren_id = a.tren_id
                        AND r.linea_id = g_elems(i).linea_id
                  );
                IF v_incompatible > 0 THEN
                    RAISE_APPLICATION_ERROR(-20086, 'Inconsistencia operativa de red: La línea ' || g_elems(i).linea_id || ' no corresponde a la asignación del tren asociado al incidente.');
                END IF;
            END IF;
        END LOOP;
    END AFTER STATEMENT;
END TRG_INC_ELEM_VALIDAR_CRUCE;
/

EXIT;
