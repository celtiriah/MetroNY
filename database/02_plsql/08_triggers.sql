-- ======================================================================
-- SISTEMA DE GESTION DEL METRO DE NUEVA YORK [MTA NYCT]
-- Capa de Programacion PL/SQL - 08_triggers.sql
-- 8 Triggers de Integridad, Auditoria y Control Operativo
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

-- 7. Trigger: Alertar y bloquear si el conductor asignado tiene la certificacion vencida
CREATE OR REPLACE TRIGGER TRG_CERTIFICACION_ALERTA_VENCIDA
BEFORE INSERT OR UPDATE OF conductor_id, fecha ON VIAJE_PROGRAMADO
FOR EACH ROW
DECLARE
    v_certificaciones_validas NUMBER := 0;
BEGIN
    SELECT COUNT(*)
    INTO v_certificaciones_validas
    FROM CERTIFICACION
    WHERE empleado_id = :NEW.conductor_id
      AND estado = 'Vigente'
      AND fecha_vencimiento >= :NEW.fecha;

    IF v_certificaciones_validas = 0 THEN
        RAISE_APPLICATION_ERROR(-20015, 'Operacion rechazada: El conductor asignado (ID ' || :NEW.conductor_id || ') no posee una certificacion tecnica vigente para la fecha del viaje.');
    END IF;
END;
/

-- 8. Trigger: Auditoria de creacion y actualizacion de incidentes en BITACORA
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

EXIT;
