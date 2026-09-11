-- Généré par Oracle SQL Developer Data Modeler 24.3.1.351.0831
--   à :        2026-09-03 14:57:01 CST
--   site :      Oracle Database 21c
--   type :      Oracle Database 21c



DROP TABLE BITACORA CASCADE CONSTRAINTS 
;

DROP TABLE CERTIFICACION CASCADE CONSTRAINTS 
;

DROP TABLE CERTIFICACION_MODELO CASCADE CONSTRAINTS 
;

DROP TABLE DEPOSITO CASCADE CONSTRAINTS 
;

DROP TABLE EMPLEADO CASCADE CONSTRAINTS 
;

DROP TABLE EQUIPO CASCADE CONSTRAINTS 
;

DROP TABLE ESTACION CASCADE CONSTRAINTS 
;

DROP TABLE ESTACION_SERVICIO CASCADE CONSTRAINTS 
;

DROP TABLE HORARIO CASCADE CONSTRAINTS 
;

DROP TABLE HORARIO_ESTACION CASCADE CONSTRAINTS 
;

DROP TABLE INCIDENTE CASCADE CONSTRAINTS 
;

DROP TABLE INCIDENTE_ELEMENTO_AFECTADO CASCADE CONSTRAINTS 
;

DROP TABLE LINEA CASCADE CONSTRAINTS 
;

DROP TABLE LINEA_ESTACION CASCADE CONSTRAINTS 
;

DROP TABLE MODELO_TREN CASCADE CONSTRAINTS 
;

DROP TABLE ORDEN_MANTENIMIENTO CASCADE CONSTRAINTS 
;

DROP TABLE ORDEN_REPUESTO CASCADE CONSTRAINTS 
;

DROP TABLE ORDEN_TECNICO CASCADE CONSTRAINTS 
;

DROP TABLE PASAJERO CASCADE CONSTRAINTS 
;

DROP TABLE PLATAFORMA CASCADE CONSTRAINTS 
;

DROP TABLE RECARGA CASCADE CONSTRAINTS 
;

DROP TABLE REPUESTO CASCADE CONSTRAINTS 
;

DROP TABLE RUTA CASCADE CONSTRAINTS 
;

DROP TABLE RUTA_DETALLE CASCADE CONSTRAINTS 
;

DROP TABLE TARIFA CASCADE CONSTRAINTS 
;

DROP TABLE TARJETA CASCADE CONSTRAINTS 
;

DROP TABLE TRANSFERENCIA CASCADE CONSTRAINTS 
;

DROP TABLE TREN CASCADE CONSTRAINTS 
;

DROP TABLE TREN_VAGON CASCADE CONSTRAINTS 
;

DROP TABLE TURNO CASCADE CONSTRAINTS 
;

DROP TABLE VAGON CASCADE CONSTRAINTS 
;

DROP TABLE VIAJE_PASAJERO CASCADE CONSTRAINTS 
;

DROP TABLE VIAJE_PROGRAMADO CASCADE CONSTRAINTS 
;

-- predefined type, no DDL - MDSYS.SDO_GEOMETRY

-- predefined type, no DDL - XMLTYPE

CREATE SEQUENCE SEQ_BITACORA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_CERTIFICACION 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_CERTIFICACION_MODELO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_DEPOSITO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_EMPLEADO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_EQUIPO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_ESTACION 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_ESTACION_SERVICIO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_HORARIO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_HORARIO_ESTACION 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_INCIDENTE 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_INCIDENTE_ELEMENTO_AF_F066 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_LINEA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_LINEA_ESTACION 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_MODELO_TREN 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_ORDEN_MANTENIMIENTO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_ORDEN_REPUESTO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_ORDEN_TECNICO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_PASAJERO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_PLATAFORMA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_RECARGA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_REPUESTO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_RUTA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_RUTA_DETALLE 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_TARIFA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_TARJETA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_TRANSFERENCIA 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_TREN 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_TREN_VAGON 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_TURNO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_VAGON 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_VIAJE_PASAJERO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE SEQUENCE SEQ_VIAJE_PROGRAMADO 
    START WITH 1 
    INCREMENT BY 1 
    NOCACHE 
;

CREATE TABLE BITACORA 
    ( 
     id_bitacora    NUMBER (14)  NOT NULL , 
     fecha_hora     TIMESTAMP  NOT NULL , 
     tabla_afectada VARCHAR2 (30)  NOT NULL , 
     operacion      VARCHAR2 (10) , 
     registro_id    NUMBER (14) , 
     usuario        VARCHAR2 (50) , 
     descripcion    VARCHAR2 (500) 
    ) 
    LOGGING 
;

ALTER TABLE BITACORA 
    ADD CONSTRAINT CK_BITACORA_OPERACION 
    CHECK (operacion IN ('DELETE', 'INSERT', 'UPDATE')) 
;

COMMENT ON TABLE BITACORA IS 'Registro de auditoría de cambios importantes (alimentada por triggers).'
;

COMMENT ON COLUMN BITACORA.id_bitacora IS 'Identificador único' 
;

COMMENT ON COLUMN BITACORA.fecha_hora IS 'NOT NULL' 
;

COMMENT ON COLUMN BITACORA.tabla_afectada IS 'NOT NULL' 
;

COMMENT ON COLUMN BITACORA.operacion IS 'CHECK: INSERT, UPDATE, DELETE' 
;

ALTER TABLE BITACORA 
    ADD CONSTRAINT PK_BITACORA PRIMARY KEY ( id_bitacora ) ;

CREATE TABLE CERTIFICACION 
    ( 
     id_certificacion    NUMBER (8)  NOT NULL , 
     empleado_id         NUMBER (8)  NOT NULL , 
     tipo_certificacion  VARCHAR2 (60)  NOT NULL , 
     fecha_emision       DATE , 
     fecha_vencimiento   DATE , 
     institucion_emisora VARCHAR2 (100) , 
     estado              VARCHAR2 (20) 
    ) 
    LOGGING 
;

ALTER TABLE CERTIFICACION 
    ADD CONSTRAINT CK_CERTIFICACION_ESTADO 
    CHECK (estado IN ('Revocada', 'Vencida', 'Vigente')) 
;

COMMENT ON TABLE CERTIFICACION IS 'Certificación de un empleado (p.ej. para operar cierto modelo de tren).'
;

COMMENT ON COLUMN CERTIFICACION.id_certificacion IS 'Identificador único' 
;

COMMENT ON COLUMN CERTIFICACION.empleado_id IS '-> EMPLEADO. NOT NULL' 
;

COMMENT ON COLUMN CERTIFICACION.tipo_certificacion IS 'NOT NULL' 
;

COMMENT ON COLUMN CERTIFICACION.estado IS 'CHECK: Vigente, Vencida, Revocada' 
;

ALTER TABLE CERTIFICACION 
    ADD CONSTRAINT PK_CERTIFICACION PRIMARY KEY ( id_certificacion ) ;

CREATE TABLE CERTIFICACION_MODELO 
    ( 
     id_certificacion_modelo NUMBER (10)  NOT NULL , 
     certificacion_id        NUMBER (8)  NOT NULL , 
     modelo_id               NUMBER (4)  NOT NULL 
    ) 
    LOGGING 
;

COMMENT ON TABLE CERTIFICACION_MODELO IS 'Modelos de tren que una certificación autoriza operar (atributo multivaluado de CERTIFICACION).'
;

COMMENT ON COLUMN CERTIFICACION_MODELO.id_certificacion_modelo IS 'Identificador único' 
;

COMMENT ON COLUMN CERTIFICACION_MODELO.certificacion_id IS '-> CERTIFICACION. NOT NULL' 
;

COMMENT ON COLUMN CERTIFICACION_MODELO.modelo_id IS '-> MODELO_TREN. NOT NULL' 
;

ALTER TABLE CERTIFICACION_MODELO 
    ADD CONSTRAINT PK_CERTIFICACION_MODELO PRIMARY KEY ( id_certificacion_modelo ) ;

ALTER TABLE CERTIFICACION_MODELO 
    ADD CONSTRAINT UK_CERTIFICACION_MODELO_1 UNIQUE ( certificacion_id , modelo_id ) ;

CREATE TABLE DEPOSITO 
    ( 
     id_deposito NUMBER (4)  NOT NULL , 
     codigo      VARCHAR2 (10) , 
     nombre      VARCHAR2 (100)  NOT NULL , 
     ubicacion   VARCHAR2 (200) , 
     capacidad   NUMBER (5) 
    ) 
    LOGGING 
;

COMMENT ON TABLE DEPOSITO IS 'Depósito / patio donde se resguardan y asignan los trenes.'
;

COMMENT ON COLUMN DEPOSITO.id_deposito IS 'Identificador único' 
;

COMMENT ON COLUMN DEPOSITO.codigo IS 'UNIQUE' 
;

COMMENT ON COLUMN DEPOSITO.nombre IS 'NOT NULL' 
;

COMMENT ON COLUMN DEPOSITO.capacidad IS 'Capacidad de trenes' 
;

ALTER TABLE DEPOSITO 
    ADD CONSTRAINT PK_DEPOSITO PRIMARY KEY ( id_deposito ) ;

ALTER TABLE DEPOSITO 
    ADD CONSTRAINT UK_DEPOSITO_CODIGO UNIQUE ( codigo ) ;

CREATE TABLE EMPLEADO 
    ( 
     id_empleado        NUMBER (8)  NOT NULL , 
     numero_empleado    VARCHAR2 (15)  NOT NULL , 
     nombre_completo    VARCHAR2 (150)  NOT NULL , 
     fecha_nacimiento   DATE , 
     direccion          VARCHAR2 (200) , 
     telefono           VARCHAR2 (20) , 
     correo_electronico VARCHAR2 (100) , 
     fecha_contratacion DATE , 
     cargo              VARCHAR2 (50) , 
     turno_habitual     VARCHAR2 (20) , 
     salario            NUMBER (10,2) , 
     estado_laboral     VARCHAR2 (20) , 
     supervisor_id      NUMBER (8) 
    ) 
    LOGGING 
;

ALTER TABLE EMPLEADO 
    ADD CONSTRAINT CK_EMPLEADO_CARGO 
    CHECK (cargo IN ('Agente de Seguridad', 'Conductor', 'Operador de Control', 'Personal de Atención al Pasajero', 'Supervisor de Estación', 'Técnico de Mantenimiento')) 
;

ALTER TABLE EMPLEADO 
    ADD CONSTRAINT CK_EMPLEADO_ESTADO_LABORAL 
    CHECK (estado_laboral IN ('Activo', 'Permiso', 'Retirado', 'Suspendido', 'Vacaciones')) 
;

COMMENT ON TABLE EMPLEADO IS 'Personal operativo del metro.'
;

COMMENT ON COLUMN EMPLEADO.id_empleado IS 'Identificador único' 
;

COMMENT ON COLUMN EMPLEADO.numero_empleado IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN EMPLEADO.nombre_completo IS 'NOT NULL' 
;

COMMENT ON COLUMN EMPLEADO.correo_electronico IS 'UNIQUE' 
;

COMMENT ON COLUMN EMPLEADO.cargo IS 'CHECK: Conductor, Operador de Control, Supervisor de Estación, Técnico de Mantenimiento, Agente de Seguridad, Personal de Atención al Pasajero' 
;

COMMENT ON COLUMN EMPLEADO.turno_habitual IS 'p.ej. Matutino, Vespertino, Nocturno' 
;

COMMENT ON COLUMN EMPLEADO.estado_laboral IS 'CHECK: Activo, Vacaciones, Permiso, Suspendido, Retirado' 
;

COMMENT ON COLUMN EMPLEADO.supervisor_id IS '-> EMPLEADO (autorreferencia)' 
;

ALTER TABLE EMPLEADO 
    ADD CONSTRAINT PK_EMPLEADO PRIMARY KEY ( id_empleado ) ;

ALTER TABLE EMPLEADO 
    ADD CONSTRAINT UK_EMPLEADO_CORREO_ELECTRONICO UNIQUE ( correo_electronico ) ;

ALTER TABLE EMPLEADO 
    ADD CONSTRAINT UK_EMPLEADO_NUMERO_EMPLEADO UNIQUE ( numero_empleado ) ;

CREATE TABLE EQUIPO 
    ( 
     id_equipo              NUMBER (10)  NOT NULL , 
     codigo_equipo          VARCHAR2 (20)  NOT NULL , 
     tipo_equipo            VARCHAR2 (30) , 
     tipo_referencia        VARCHAR2 (15) , 
     referencia_id          NUMBER (10) , 
     ubicacion              VARCHAR2 (200) , 
     fabricante             VARCHAR2 (60) , 
     modelo                 VARCHAR2 (60) , 
     numero_serie           VARCHAR2 (30) , 
     fecha_instalacion      DATE , 
     estado                 VARCHAR2 (20) , 
     fecha_ultima_revision  DATE , 
     fecha_proxima_revision DATE 
    ) 
    LOGGING 
;

ALTER TABLE EQUIPO 
    ADD CONSTRAINT CK_EQUIPO_TIPO_EQUIPO 
    CHECK (tipo_equipo IN ('Elevador', 'Escalera Eléctrica', 'Plataforma', 'Señal', 'Tren', 'Vagón', 'Vía')) 
;

ALTER TABLE EQUIPO 
    ADD CONSTRAINT CK_EQUIPO_TIPO_REFERENCIA 
    CHECK (tipo_referencia IN ('ESTACION', 'NINGUNO', 'PLATAFORMA', 'TREN', 'VAGON')) 
;

ALTER TABLE EQUIPO 
    ADD CONSTRAINT CK_EQUIPO_ESTADO 
    CHECK (estado IN ('Disponible', 'En Mantenimiento', 'Fuera de Servicio')) 
;

COMMENT ON TABLE EQUIPO IS 'Activo mantenible: vía, señal, plataforma, elevador, escalera, tren o vagón.'
;

COMMENT ON COLUMN EQUIPO.id_equipo IS 'Identificador único' 
;

COMMENT ON COLUMN EQUIPO.codigo_equipo IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN EQUIPO.tipo_equipo IS 'CHECK: Vía, Señal, Plataforma, Elevador, Escalera Eléctrica, Tren, Vagón' 
;

COMMENT ON COLUMN EQUIPO.tipo_referencia IS 'CHECK: ESTACION, PLATAFORMA, TREN, VAGON, NINGUNO' 
;

COMMENT ON COLUMN EQUIPO.referencia_id IS 'Referencia polimórfica según tipo_referencia (sin FK forzada)' 
;

COMMENT ON COLUMN EQUIPO.estado IS 'CHECK: Disponible, En Mantenimiento, Fuera de Servicio' 
;

ALTER TABLE EQUIPO 
    ADD CONSTRAINT PK_EQUIPO PRIMARY KEY ( id_equipo ) ;

ALTER TABLE EQUIPO 
    ADD CONSTRAINT UK_EQUIPO_CODIGO_EQUIPO UNIQUE ( codigo_equipo ) ;

CREATE TABLE ESTACION 
    ( 
     id_estacion                      NUMBER (8)  NOT NULL , 
     codigo                           VARCHAR2 (10)  NOT NULL , 
     nombre                           VARCHAR2 (100)  NOT NULL , 
     direccion                        VARCHAR2 (200) , 
     distrito                         VARCHAR2 (20) , 
     latitud                          NUMBER (9,6) , 
     longitud                         NUMBER (9,6) , 
     fecha_inauguracion               DATE , 
     cantidad_accesos                 NUMBER (3) , 
     cantidad_plataformas             NUMBER (2) , 
     estado_operativo                 VARCHAR2 (25) , 
     horario_funcionamiento           VARCHAR2 (50) , 
     elevadores_disponibles           CHAR (1) , 
     escaleras_electricas_disponibles CHAR (1) , 
     accesible_discapacidad           CHAR (1) , 
     tipo_estacion                    VARCHAR2 (20) 
    ) 
    LOGGING 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT CK_ESTACION_DISTRITO 
    CHECK (distrito IN ('Brooklyn', 'Manhattan', 'Queens', 'Staten Island', 'The Bronx')) 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT CK_ESTACION_ESTADO_OPERATIVO 
    CHECK (estado_operativo IN ('Cerrada', 'Cerrada Temporalmente', 'Operativa')) 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT CK_ESTACION_ELEVADORES_DI_9827 
    CHECK (elevadores_disponibles IN ('N', 'S')) 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT CK_ESTACION_ESCALERAS_ELE_3BDE 
    CHECK (escaleras_electricas_disponibles IN ('N', 'S')) 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT CK_ESTACION_ACCESIBLE_DIS_40E0 
    CHECK (accesible_discapacidad IN ('N', 'S')) 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT CK_ESTACION_TIPO_ESTACION 
    CHECK (tipo_estacion IN ('Cerrada Temporalmente', 'Expresa', 'Local', 'Terminal', 'Transferencia')) 
;

COMMENT ON TABLE ESTACION IS 'Estación del sistema, puede ser usada por varias líneas.'
;

COMMENT ON COLUMN ESTACION.id_estacion IS 'Identificador interno' 
;

COMMENT ON COLUMN ESTACION.codigo IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN ESTACION.nombre IS 'NOT NULL' 
;

COMMENT ON COLUMN ESTACION.distrito IS 'CHECK: Manhattan, Brooklyn, Queens, The Bronx, Staten Island' 
;

COMMENT ON COLUMN ESTACION.cantidad_plataformas IS 'Campo resumen; el detalle vive en PLATAFORMA' 
;

COMMENT ON COLUMN ESTACION.estado_operativo IS 'CHECK: Operativa, Cerrada Temporalmente, Cerrada' 
;

COMMENT ON COLUMN ESTACION.horario_funcionamiento IS 'p.ej. 24 horas / 05:00-01:00' 
;

COMMENT ON COLUMN ESTACION.elevadores_disponibles IS 'CHECK: S, N' 
;

COMMENT ON COLUMN ESTACION.escaleras_electricas_disponibles IS 'CHECK: S, N' 
;

COMMENT ON COLUMN ESTACION.accesible_discapacidad IS 'CHECK: S, N' 
;

COMMENT ON COLUMN ESTACION.tipo_estacion IS 'CHECK: Local, Expresa, Terminal, Transferencia, Cerrada Temporalmente' 
;

ALTER TABLE ESTACION 
    ADD CONSTRAINT PK_ESTACION PRIMARY KEY ( id_estacion ) ;

ALTER TABLE ESTACION 
    ADD CONSTRAINT UK_ESTACION_CODIGO UNIQUE ( codigo ) ;

CREATE TABLE ESTACION_SERVICIO 
    ( 
     id_estacion_servicio NUMBER (10)  NOT NULL , 
     estacion_id          NUMBER (8)  NOT NULL , 
     tipo_servicio        VARCHAR2 (40) , 
     disponible           CHAR (1) 
    ) 
    LOGGING 
;

ALTER TABLE ESTACION_SERVICIO 
    ADD CONSTRAINT CK_ESTACION_SERVICIO_TIPO_D3A9 
    CHECK (tipo_servicio IN ('Acceso Bicicletas', 'Atención al Pasajero', 'Conexión Autobuses', 'Conexión Trenes Regionales', 'Máquinas Expendedoras', 'Policía/Seguridad', 'Servicios Sanitarios', 'Venta/Recarga Tarjetas')) 
;

ALTER TABLE ESTACION_SERVICIO 
    ADD CONSTRAINT CK_ESTACION_SERVICIO_DISP_9CAD 
    CHECK (disponible IN ('N', 'S')) 
;

COMMENT ON TABLE ESTACION_SERVICIO IS 'Servicios disponibles en cada estación (venta de tarjetas, sanitarios, seguridad, etc.).'
;

COMMENT ON COLUMN ESTACION_SERVICIO.id_estacion_servicio IS 'Identificador único' 
;

COMMENT ON COLUMN ESTACION_SERVICIO.estacion_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN ESTACION_SERVICIO.tipo_servicio IS 'CHECK: Venta/Recarga Tarjetas, Máquinas Expendedoras, Servicios Sanitarios, Policía/Seguridad, Atención al Pasajero, Acceso Bicicletas, Conexión Autobuses, Conexión Trenes Regionales' 
;

COMMENT ON COLUMN ESTACION_SERVICIO.disponible IS 'CHECK: S, N' 
;

ALTER TABLE ESTACION_SERVICIO 
    ADD CONSTRAINT PK_ESTACION_SERVICIO PRIMARY KEY ( id_estacion_servicio ) ;

ALTER TABLE ESTACION_SERVICIO 
    ADD CONSTRAINT UK_ESTACION_SERVICIO_1 UNIQUE ( estacion_id , tipo_servicio ) ;

CREATE TABLE HORARIO 
    ( 
     id_horario           NUMBER (8)  NOT NULL , 
     ruta_id              NUMBER (8)  NOT NULL , 
     dia_semana           VARCHAR2 (20) , 
     hora_inicio          DATE , 
     hora_fin             DATE , 
     frecuencia_minutos   NUMBER (4) , 
     tipo_servicio        VARCHAR2 (20) , 
     fecha_vigencia_desde DATE  NOT NULL , 
     fecha_vigencia_hasta DATE 
    ) 
    LOGGING 
;

ALTER TABLE HORARIO 
    ADD CONSTRAINT CK_HORARIO_DIA_SEMANA 
    CHECK (dia_semana IN ('Domingo', 'Festivo', 'Fin de Semana', 'Jueves', 'Lunes', 'Lunes a Viernes', 'Martes', 'Miercoles', 'Sabado', 'Viernes')) 
;

COMMENT ON TABLE HORARIO IS 'Horario de operación programado para una ruta.'
;

COMMENT ON COLUMN HORARIO.id_horario IS 'Identificador único' 
;

COMMENT ON COLUMN HORARIO.ruta_id IS '-> RUTA. NOT NULL' 
;

COMMENT ON COLUMN HORARIO.dia_semana IS 'CHECK: Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo, Lunes a Viernes, Fin de Semana, Festivo' 
;

COMMENT ON COLUMN HORARIO.hora_inicio IS 'Componente de hora' 
;

COMMENT ON COLUMN HORARIO.hora_fin IS 'Componente de hora' 
;

COMMENT ON COLUMN HORARIO.frecuencia_minutos IS 'Minutos entre salidas consecutivas' 
;

COMMENT ON COLUMN HORARIO.fecha_vigencia_desde IS 'NOT NULL' 
;

ALTER TABLE HORARIO 
    ADD CONSTRAINT PK_HORARIO PRIMARY KEY ( id_horario ) ;

CREATE TABLE HORARIO_ESTACION 
    ( 
     id_horario_estacion NUMBER (10)  NOT NULL , 
     estacion_id         NUMBER (8)  NOT NULL , 
     tipo_dia            VARCHAR2 (20)  NOT NULL , 
     hora_apertura       VARCHAR2 (5) DEFAULT '05:00' , 
     hora_cierre         VARCHAR2 (5) DEFAULT '01:00' , 
     es_24_horas         CHAR (1) DEFAULT 'S' , 
     estado              VARCHAR2 (20) DEFAULT 'Vigente' 
    ) 
    LOGGING 
;

ALTER TABLE HORARIO_ESTACION 
    ADD CONSTRAINT CK_HORARIO_EST_TIPO_DIA 
    CHECK (tipo_dia IN ('Domingo', 'Festivo', 'Lunes a Viernes', 'Sabado', 'Todos los Dias')) 
;

ALTER TABLE HORARIO_ESTACION 
    ADD CONSTRAINT CK_HORARIO_EST_24H 
    CHECK (es_24_horas IN ('N', 'S')) 
;

ALTER TABLE HORARIO_ESTACION 
    ADD CONSTRAINT CK_HORARIO_EST_ESTADO 
    CHECK (estado IN ('Suspendido', 'Vigente')) 
;

COMMENT ON TABLE HORARIO_ESTACION IS 'Horarios de apertura y cierre de las estaciones según día de la semana (normalización 3FN).'
;

COMMENT ON COLUMN HORARIO_ESTACION.id_horario_estacion IS 'Identificador único' 
;

COMMENT ON COLUMN HORARIO_ESTACION.estacion_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN HORARIO_ESTACION.tipo_dia IS 'CHECK: Lunes a Viernes, Sabado, Domingo, Festivo, Todos los Dias' 
;

COMMENT ON COLUMN HORARIO_ESTACION.hora_apertura IS 'Formato HH:MM' 
;

COMMENT ON COLUMN HORARIO_ESTACION.hora_cierre IS 'Formato HH:MM' 
;

COMMENT ON COLUMN HORARIO_ESTACION.es_24_horas IS 'CHECK: S, N' 
;

COMMENT ON COLUMN HORARIO_ESTACION.estado IS 'CHECK: Vigente, Suspendido' 
;

ALTER TABLE HORARIO_ESTACION 
    ADD CONSTRAINT PK_HORARIO_ESTACION PRIMARY KEY ( id_horario_estacion ) ;

ALTER TABLE HORARIO_ESTACION 
    ADD CONSTRAINT UK_HORARIO_ESTACION_1 UNIQUE ( estacion_id , tipo_dia ) ;

CREATE TABLE INCIDENTE 
    ( 
     id_incidente                 NUMBER (10)  NOT NULL , 
     numero_incidente             VARCHAR2 (20)  NOT NULL , 
     tipo                         VARCHAR2 (30) , 
     descripcion                  VARCHAR2 (500) , 
     fecha_hora_inicio            TIMESTAMP  NOT NULL , 
     fecha_hora_fin               TIMESTAMP , 
     nivel_severidad              VARCHAR2 (10) , 
     reportado_por_id             NUMBER (8) , 
     estado                       VARCHAR2 (15) , 
     causa_identificada           VARCHAR2 (300) , 
     acciones_realizadas          VARCHAR2 (500) , 
     pasajeros_afectados_estimado NUMBER (8) 
    ) 
    LOGGING 
;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT CK_INCIDENTE_TIPO 
    CHECK (tipo IN ('Accidente', 'Congestión', 'Emergencia Médica', 'Falla Eléctrica', 'Falla Mecánica', 'Falla de Señalización', 'Incendio', 'Inundación', 'Mantenimiento no Programado', 'Objeto en la Vía', 'Problema de Seguridad')) 
;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT CK_INCIDENTE_FECHA_HORA_FIN 
    CHECK (fecha_hora_fin >= fecha_hora_inicio) 
;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT CK_INCIDENTE_NIVEL_SEVERIDAD 
    CHECK (nivel_severidad IN ('Alto', 'Bajo', 'Crítico', 'Medio')) 
;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT CK_INCIDENTE_ESTADO 
    CHECK (estado IN ('Abierto', 'Cerrado', 'En Atención')) 
;

COMMENT ON TABLE INCIDENTE IS 'Incidente operativo ocurrido en la red.'
;

COMMENT ON COLUMN INCIDENTE.id_incidente IS 'Identificador único' 
;

COMMENT ON COLUMN INCIDENTE.numero_incidente IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN INCIDENTE.tipo IS 'CHECK: Falla Mecánica, Falla Eléctrica, Falla de Señalización, Emergencia Médica, Accidente, Problema de Seguridad, Objeto en la Vía, Inundación, Incendio, Congestión, Mantenimiento no Programado' 
;

COMMENT ON COLUMN INCIDENTE.fecha_hora_inicio IS 'NOT NULL' 
;

COMMENT ON COLUMN INCIDENTE.fecha_hora_fin IS 'CHECK: >= fecha_hora_inicio' 
;

COMMENT ON COLUMN INCIDENTE.nivel_severidad IS 'CHECK: Bajo, Medio, Alto, Crítico' 
;

COMMENT ON COLUMN INCIDENTE.reportado_por_id IS '-> EMPLEADO' 
;

COMMENT ON COLUMN INCIDENTE.estado IS 'CHECK: Abierto, En Atención, Cerrado' 
;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT PK_INCIDENTE PRIMARY KEY ( id_incidente ) ;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT UK_INCIDENTE_NUMERO_INCIDENTE UNIQUE ( numero_incidente ) ;

CREATE TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ( 
     id_incidente_elemento NUMBER (12)  NOT NULL , 
     incidente_id          NUMBER (10)  NOT NULL , 
     tipo_elemento         VARCHAR2 (20)  NOT NULL , 
     estacion_id           NUMBER (8) , 
     tren_id               NUMBER (8) , 
     ruta_id               NUMBER (8) , 
     equipo_id             NUMBER (10) , 
     viaje_id              NUMBER (10) , 
     linea_id              NUMBER (6) , 
     tipo_afectacion       VARCHAR2 (30) 
    ) 
    LOGGING 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT CK_INCIDENTE_ELEMENTO_TIPO 
    CHECK (tipo_elemento IN ('EQUIPO', 'ESTACION', 'LINEA', 'RUTA', 'TREN', 'VIAJE_PROGRAMADO')) 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT CK_INCIDENTE_ELEMENTO_AFE_8B3B 
    CHECK (tipo_afectacion IN ('Cambio de Ruta', 'Cancelación', 'Cierre de Estación', 'Cierre de Plataforma', 'Retiro de Tren', 'Retraso', 'Suspensión de Tramo')) 
;

COMMENT ON TABLE INCIDENTE_ELEMENTO_AFECTADO IS 'Asociativa con Arco Exclusivo: elementos de la red afectados con integridad referencial (FK).'
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.id_incidente_elemento IS 'Identificador único' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.incidente_id IS '-> INCIDENTE. NOT NULL' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.tipo_elemento IS 'CHECK: ESTACION, TREN, RUTA, EQUIPO, VIAJE_PROGRAMADO, LINEA' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.estacion_id IS '-> ESTACION (Arco)' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.tren_id IS '-> TREN (Arco)' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.ruta_id IS '-> RUTA (Arco)' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.equipo_id IS '-> EQUIPO (Arco)' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.viaje_id IS '-> VIAJE_PROGRAMADO (Arco)' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.linea_id IS '-> LINEA (Arco)' 
;

COMMENT ON COLUMN INCIDENTE_ELEMENTO_AFECTADO.tipo_afectacion IS 'CHECK: Retraso, Cancelación, Cierre de Estación, Cierre de Plataforma, Suspensión de Tramo, Cambio de Ruta, Retiro de Tren' 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT CK_INCIDENTE_ELEMENTO_ARCO 
    CHECK ((tipo_elemento = 'ESTACION' AND estacion_id IS NOT NULL AND tren_id IS NULL AND ruta_id IS NULL AND equipo_id IS NULL AND viaje_id IS NULL AND linea_id IS NULL) OR (tipo_elemento = 'TREN' AND tren_id IS NOT NULL AND estacion_id IS NULL AND ruta_id IS NULL AND equipo_id IS NULL AND viaje_id IS NULL AND linea_id IS NULL) OR (tipo_elemento = 'RUTA' AND ruta_id IS NOT NULL AND estacion_id IS NULL AND tren_id IS NULL AND equipo_id IS NULL AND viaje_id IS NULL AND linea_id IS NULL) OR (tipo_elemento = 'EQUIPO' AND equipo_id IS NOT NULL AND estacion_id IS NULL AND tren_id IS NULL AND ruta_id IS NULL AND viaje_id IS NULL AND linea_id IS NULL) OR (tipo_elemento = 'VIAJE_PROGRAMADO' AND viaje_id IS NOT NULL AND estacion_id IS NULL AND tren_id IS NULL AND ruta_id IS NULL AND equipo_id IS NULL AND linea_id IS NULL) OR (tipo_elemento = 'LINEA' AND linea_id IS NOT NULL AND estacion_id IS NULL AND tren_id IS NULL AND ruta_id IS NULL AND equipo_id IS NULL AND viaje_id IS NULL))
;
ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT PK_INCIDENTE_ELEMENTO_AFECTADO PRIMARY KEY ( id_incidente_elemento ) ;

CREATE TABLE LINEA 
    ( 
     id_linea                NUMBER (6)  NOT NULL , 
     codigo                  VARCHAR2 (10)  NOT NULL , 
     nombre                  VARCHAR2 (100)  NOT NULL , 
     color                   VARCHAR2 (20) , 
     estacion_origen_id      NUMBER (8) , 
     estacion_destino_id     NUMBER (8) , 
     estado_operativo        VARCHAR2 (20) , 
     tipo_servicio_principal VARCHAR2 (20) , 
     fecha_inauguracion      DATE , 
     longitud_km             NUMBER (6,2) , 
     operador_responsable    VARCHAR2 (100) 
    ) 
    LOGGING 
;

ALTER TABLE LINEA 
    ADD CONSTRAINT CK_LINEA_ESTADO_OPERATIVO 
    CHECK (estado_operativo IN ('Activa', 'Fuera de Servicio', 'Suspendida')) 
;

ALTER TABLE LINEA 
    ADD CONSTRAINT CK_LINEA_TIPO_SERVICIO_PR_99EB 
    CHECK (tipo_servicio_principal IN ('Especial', 'Expreso', 'Local', 'Nocturno', 'Temporal')) 
;

COMMENT ON TABLE LINEA IS 'Línea de metro (p. ej. A, B, 1, 2).'
;

COMMENT ON COLUMN LINEA.id_linea IS 'Identificador interno' 
;

COMMENT ON COLUMN LINEA.codigo IS 'UNIQUE, NOT NULL. Código visible (A, B, 1, 2)' 
;

COMMENT ON COLUMN LINEA.nombre IS 'NOT NULL' 
;

COMMENT ON COLUMN LINEA.color IS 'Color en los mapas' 
;

COMMENT ON COLUMN LINEA.estacion_origen_id IS '-> ESTACION. Terminal de origen' 
;

COMMENT ON COLUMN LINEA.estacion_destino_id IS '-> ESTACION. Terminal de destino' 
;

COMMENT ON COLUMN LINEA.estado_operativo IS 'CHECK: Activa, Suspendida, Fuera de Servicio' 
;

COMMENT ON COLUMN LINEA.tipo_servicio_principal IS 'CHECK: Local, Expreso, Nocturno, Especial, Temporal' 
;

COMMENT ON COLUMN LINEA.longitud_km IS 'Longitud aproximada' 
;

ALTER TABLE LINEA 
    ADD CONSTRAINT PK_LINEA PRIMARY KEY ( id_linea ) ;

ALTER TABLE LINEA 
    ADD CONSTRAINT UK_LINEA_CODIGO UNIQUE ( codigo ) ;

CREATE TABLE LINEA_ESTACION 
    ( 
     id_linea_estacion   NUMBER (10)  NOT NULL , 
     linea_id            NUMBER (6)  NOT NULL , 
     estacion_id         NUMBER (8)  NOT NULL , 
     orden               NUMBER (3)  NOT NULL , 
     distancia_km        NUMBER (6,2) , 
     tiempo_estimado_min NUMBER (5) 
    ) 
    LOGGING 
;

COMMENT ON TABLE LINEA_ESTACION IS 'Asociativa: secuencia de estaciones que recorre cada línea, con distancia y tiempo entre paradas consecutivas.'
;

COMMENT ON COLUMN LINEA_ESTACION.id_linea_estacion IS 'Identificador único' 
;

COMMENT ON COLUMN LINEA_ESTACION.linea_id IS '-> LINEA. NOT NULL' 
;

COMMENT ON COLUMN LINEA_ESTACION.estacion_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN LINEA_ESTACION.orden IS 'NOT NULL. Posición de la estación dentro de la línea' 
;

COMMENT ON COLUMN LINEA_ESTACION.distancia_km IS 'Distancia desde la estación anterior de la línea' 
;

COMMENT ON COLUMN LINEA_ESTACION.tiempo_estimado_min IS 'Tiempo estimado desde la estación anterior' 
;

ALTER TABLE LINEA_ESTACION 
    ADD CONSTRAINT PK_LINEA_ESTACION PRIMARY KEY ( id_linea_estacion ) ;

ALTER TABLE LINEA_ESTACION 
    ADD CONSTRAINT UK_LINEA_ESTACION_1 UNIQUE ( linea_id , estacion_id ) ;

ALTER TABLE LINEA_ESTACION 
    ADD CONSTRAINT UK_LINEA_ESTACION_2 UNIQUE ( linea_id , orden ) ;

CREATE TABLE MODELO_TREN 
    ( 
     id_modelo     NUMBER (4)  NOT NULL , 
     nombre_modelo VARCHAR2 (50)  NOT NULL , 
     fabricante    VARCHAR2 (60)  NOT NULL 
    ) 
    LOGGING 
;

COMMENT ON TABLE MODELO_TREN IS 'Catálogo de modelos de tren. Extraída para 3FN: el fabricante depende del modelo, no de cada tren individual.'
;

COMMENT ON COLUMN MODELO_TREN.id_modelo IS 'Identificador único' 
;

COMMENT ON COLUMN MODELO_TREN.nombre_modelo IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN MODELO_TREN.fabricante IS 'NOT NULL' 
;

ALTER TABLE MODELO_TREN 
    ADD CONSTRAINT PK_MODELO_TREN PRIMARY KEY ( id_modelo ) ;

ALTER TABLE MODELO_TREN 
    ADD CONSTRAINT UK_MODELO_TREN_NOMBRE_MODELO UNIQUE ( nombre_modelo ) ;

CREATE TABLE ORDEN_MANTENIMIENTO 
    ( 
     id_orden            NUMBER (10)  NOT NULL , 
     numero_orden        VARCHAR2 (20)  NOT NULL , 
     equipo_id           NUMBER (10)  NOT NULL , 
     tipo_mantenimiento  VARCHAR2 (40) , 
     descripcion_trabajo VARCHAR2 (500) , 
     fecha_solicitud     DATE , 
     fecha_programada    DATE , 
     fecha_inicio        DATE , 
     fecha_finalizacion  DATE , 
     prioridad           VARCHAR2 (10) , 
     costo               NUMBER (10,2) , 
     estado              VARCHAR2 (20) 
    ) 
    LOGGING 
;

ALTER TABLE ORDEN_MANTENIMIENTO 
    ADD CONSTRAINT CK_ORDEN_MANTENIMIENTO_TI_3D5F 
    CHECK (tipo_mantenimiento IN ('Correctivo', 'Inspección de Seguridad', 'Predictivo', 'Preventivo')) 
;

ALTER TABLE ORDEN_MANTENIMIENTO 
    ADD CONSTRAINT CK_ORDEN_MANTENIMIENTO_PR_F06F 
    CHECK (prioridad IN ('Alta', 'Baja', 'Media', 'Urgente')) 
;

ALTER TABLE ORDEN_MANTENIMIENTO 
    ADD CONSTRAINT CK_ORDEN_MANTENIMIENTO_ESTADO 
    CHECK (estado IN ('Cancelada', 'Completada', 'En Ejecución', 'Programada', 'Solicitada', 'Suspendida')) 
;

COMMENT ON TABLE ORDEN_MANTENIMIENTO IS 'Orden de trabajo de mantenimiento sobre un equipo.'
;

COMMENT ON COLUMN ORDEN_MANTENIMIENTO.id_orden IS 'Identificador único' 
;

COMMENT ON COLUMN ORDEN_MANTENIMIENTO.numero_orden IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN ORDEN_MANTENIMIENTO.equipo_id IS '-> EQUIPO. NOT NULL' 
;

COMMENT ON COLUMN ORDEN_MANTENIMIENTO.tipo_mantenimiento IS 'CHECK: Preventivo, Correctivo, Predictivo, Inspección de Seguridad' 
;

COMMENT ON COLUMN ORDEN_MANTENIMIENTO.prioridad IS 'CHECK: Baja, Media, Alta, Urgente' 
;

COMMENT ON COLUMN ORDEN_MANTENIMIENTO.estado IS 'CHECK: Solicitada, Programada, En Ejecución, Suspendida, Completada, Cancelada' 
;

ALTER TABLE ORDEN_MANTENIMIENTO 
    ADD CONSTRAINT PK_ORDEN_MANTENIMIENTO PRIMARY KEY ( id_orden ) ;

ALTER TABLE ORDEN_MANTENIMIENTO 
    ADD CONSTRAINT UK_ORDEN_MANTENIMIENTO_NU_422C UNIQUE ( numero_orden ) ;

CREATE TABLE ORDEN_REPUESTO 
    ( 
     id_orden_repuesto NUMBER (10)  NOT NULL , 
     orden_id          NUMBER (10)  NOT NULL , 
     repuesto_id       NUMBER (8)  NOT NULL , 
     cantidad          NUMBER (6)  NOT NULL , 
     costo_total       NUMBER (10,2) 
    ) 
    LOGGING 
;

COMMENT ON TABLE ORDEN_REPUESTO IS 'Asociativa: repuestos y cantidades utilizados en una orden de mantenimiento.'
;

COMMENT ON COLUMN ORDEN_REPUESTO.id_orden_repuesto IS 'Identificador único' 
;

COMMENT ON COLUMN ORDEN_REPUESTO.orden_id IS '-> ORDEN_MANTENIMIENTO. NOT NULL' 
;

COMMENT ON COLUMN ORDEN_REPUESTO.repuesto_id IS '-> REPUESTO. NOT NULL' 
;

COMMENT ON COLUMN ORDEN_REPUESTO.cantidad IS 'NOT NULL' 
;

ALTER TABLE ORDEN_REPUESTO 
    ADD CONSTRAINT PK_ORDEN_REPUESTO PRIMARY KEY ( id_orden_repuesto ) ;

CREATE TABLE ORDEN_TECNICO 
    ( 
     id_orden_tecnico NUMBER (10)  NOT NULL , 
     orden_id         NUMBER (10)  NOT NULL , 
     empleado_id      NUMBER (8)  NOT NULL , 
     rol_en_orden     VARCHAR2 (40) 
    ) 
    LOGGING 
;

COMMENT ON TABLE ORDEN_TECNICO IS 'Asociativa: técnicos (empleados) asignados a una orden de mantenimiento.'
;

COMMENT ON COLUMN ORDEN_TECNICO.id_orden_tecnico IS 'Identificador único' 
;

COMMENT ON COLUMN ORDEN_TECNICO.orden_id IS '-> ORDEN_MANTENIMIENTO. NOT NULL' 
;

COMMENT ON COLUMN ORDEN_TECNICO.empleado_id IS '-> EMPLEADO. NOT NULL' 
;

ALTER TABLE ORDEN_TECNICO 
    ADD CONSTRAINT PK_ORDEN_TECNICO PRIMARY KEY ( id_orden_tecnico ) ;

ALTER TABLE ORDEN_TECNICO 
    ADD CONSTRAINT UK_ORDEN_TECNICO_1 UNIQUE ( orden_id , empleado_id ) ;

CREATE TABLE PASAJERO 
    ( 
     id_pasajero        NUMBER (10)  NOT NULL , 
     identificador      VARCHAR2 (20)  NOT NULL , 
     nombre             VARCHAR2 (150)  NOT NULL , 
     fecha_nacimiento   DATE , 
     correo_electronico VARCHAR2 (100) , 
     telefono           VARCHAR2 (20) , 
     tipo_pasajero      VARCHAR2 (25) , 
     fecha_registro     DATE , 
     estado             VARCHAR2 (15) 
    ) 
    LOGGING 
;

ALTER TABLE PASAJERO 
    ADD CONSTRAINT CK_PASAJERO_TIPO_PASAJERO 
    CHECK (tipo_pasajero IN ('Adulto Mayor', 'Empleado Autorizado', 'Estudiante', 'Persona con Discapacidad', 'Regular')) 
;

ALTER TABLE PASAJERO 
    ADD CONSTRAINT CK_PASAJERO_ESTADO 
    CHECK (estado IN ('Activo', 'Inactivo')) 
;

COMMENT ON TABLE PASAJERO IS 'Pasajero registrado (opcional; también existen viajes anónimos).'
;

COMMENT ON COLUMN PASAJERO.id_pasajero IS 'Identificador único' 
;

COMMENT ON COLUMN PASAJERO.identificador IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN PASAJERO.nombre IS 'NOT NULL' 
;

COMMENT ON COLUMN PASAJERO.tipo_pasajero IS 'CHECK: Regular, Estudiante, Adulto Mayor, Persona con Discapacidad, Empleado Autorizado' 
;

COMMENT ON COLUMN PASAJERO.estado IS 'CHECK: Activo, Inactivo' 
;

ALTER TABLE PASAJERO 
    ADD CONSTRAINT PK_PASAJERO PRIMARY KEY ( id_pasajero ) ;

ALTER TABLE PASAJERO 
    ADD CONSTRAINT UK_PASAJERO_IDENTIFICADOR UNIQUE ( identificador ) ;

CREATE TABLE PLATAFORMA 
    ( 
     id_plataforma        NUMBER (8)  NOT NULL , 
     estacion_id          NUMBER (8)  NOT NULL , 
     identificador        VARCHAR2 (20)  NOT NULL , 
     direccion_viaje      VARCHAR2 (30) , 
     capacidad_aproximada NUMBER (6) , 
     estado_operativo     VARCHAR2 (20) 
    ) 
    LOGGING 
;

ALTER TABLE PLATAFORMA 
    ADD CONSTRAINT CK_PLATAFORMA_ESTADO_OPERATIVO 
    CHECK (estado_operativo IN ('Fuera de Servicio', 'Mantenimiento', 'Operativa')) 
;

COMMENT ON TABLE PLATAFORMA IS 'Plataforma física dentro de una estación.'
;

COMMENT ON COLUMN PLATAFORMA.id_plataforma IS 'Identificador único' 
;

COMMENT ON COLUMN PLATAFORMA.estacion_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN PLATAFORMA.identificador IS 'NOT NULL. p.ej. ''Plataforma 1''' 
;

COMMENT ON COLUMN PLATAFORMA.direccion_viaje IS 'p.ej. Norte, Sur' 
;

COMMENT ON COLUMN PLATAFORMA.estado_operativo IS 'CHECK: Operativa, Mantenimiento, Fuera de Servicio' 
;

ALTER TABLE PLATAFORMA 
    ADD CONSTRAINT PK_PLATAFORMA PRIMARY KEY ( id_plataforma ) ;

CREATE TABLE RECARGA 
    ( 
     id_recarga         NUMBER (12)  NOT NULL , 
     numero_transaccion VARCHAR2 (25)  NOT NULL , 
     tarjeta_id         NUMBER (10)  NOT NULL , 
     fecha_hora         TIMESTAMP  NOT NULL , 
     monto              NUMBER (8,2)  NOT NULL , 
     medio_pago         VARCHAR2 (20) , 
     estacion_canal     VARCHAR2 (50) , 
     saldo_anterior     NUMBER (8,2) , 
     saldo_posterior    NUMBER (8,2) 
    ) 
    LOGGING 
;

ALTER TABLE RECARGA 
    ADD CONSTRAINT CK_RECARGA_MEDIO_PAGO 
    CHECK (medio_pago IN ('App Móvil', 'Efectivo', 'Tarjeta Crédito', 'Tarjeta Débito', 'Transferencia')) 
;

COMMENT ON TABLE RECARGA IS 'Recarga de saldo realizada sobre una tarjeta.'
;

COMMENT ON COLUMN RECARGA.id_recarga IS 'Identificador único' 
;

COMMENT ON COLUMN RECARGA.numero_transaccion IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN RECARGA.tarjeta_id IS '-> TARJETA. NOT NULL' 
;

COMMENT ON COLUMN RECARGA.fecha_hora IS 'NOT NULL' 
;

COMMENT ON COLUMN RECARGA.monto IS 'NOT NULL, > 0' 
;

COMMENT ON COLUMN RECARGA.medio_pago IS 'CHECK: Efectivo, Tarjeta Débito, Tarjeta Crédito, Transferencia, App Móvil' 
;

COMMENT ON COLUMN RECARGA.estacion_canal IS 'Estación o canal donde se realizó' 
;

ALTER TABLE RECARGA 
    ADD CONSTRAINT PK_RECARGA PRIMARY KEY ( id_recarga ) ;

ALTER TABLE RECARGA 
    ADD CONSTRAINT UK_RECARGA_NUMERO_TRANSACCION UNIQUE ( numero_transaccion ) ;

CREATE TABLE REPUESTO 
    ( 
     id_repuesto    NUMBER (8)  NOT NULL , 
     codigo         VARCHAR2 (20)  NOT NULL , 
     nombre         VARCHAR2 (100)  NOT NULL , 
     costo_unitario NUMBER (8,2) 
    ) 
    LOGGING 
;

COMMENT ON TABLE REPUESTO IS 'Catálogo de repuestos utilizables en órdenes de mantenimiento.'
;

COMMENT ON COLUMN REPUESTO.id_repuesto IS 'Identificador único' 
;

COMMENT ON COLUMN REPUESTO.codigo IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN REPUESTO.nombre IS 'NOT NULL' 
;

ALTER TABLE REPUESTO 
    ADD CONSTRAINT PK_REPUESTO PRIMARY KEY ( id_repuesto ) ;

ALTER TABLE REPUESTO 
    ADD CONSTRAINT UK_REPUESTO_CODIGO UNIQUE ( codigo ) ;

CREATE TABLE RUTA 
    ( 
     id_ruta               NUMBER (8)  NOT NULL , 
     codigo                VARCHAR2 (15)  NOT NULL , 
     linea_id              NUMBER (6)  NOT NULL , 
     estacion_origen_id    NUMBER (8)  NOT NULL , 
     estacion_destino_id   NUMBER (8)  NOT NULL , 
     sentido               VARCHAR2 (20) , 
     tipo_servicio         VARCHAR2 (20) , 
     distancia_total_km    NUMBER (6,2) , 
     duracion_estimada_min NUMBER (5) , 
     estado                VARCHAR2 (20) , 
     fecha_vigencia_desde  DATE , 
     fecha_vigencia_hasta  DATE 
    ) 
    LOGGING 
;

ALTER TABLE RUTA 
    ADD CONSTRAINT CK_RUTA_TIPO_SERVICIO 
    CHECK (tipo_servicio IN ('Especial', 'Expreso', 'Local', 'Nocturno', 'Temporal')) 
;

ALTER TABLE RUTA 
    ADD CONSTRAINT CK_RUTA_ESTADO 
    CHECK (estado IN ('Activa', 'Cancelada', 'Cerrada Temporalmente')) 
;

COMMENT ON TABLE RUTA IS 'Recorrido concrééeto de una línea entre una estación origen y destino.'
;

COMMENT ON COLUMN RUTA.id_ruta IS 'Identificador único' 
;

COMMENT ON COLUMN RUTA.codigo IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN RUTA.linea_id IS '-> LINEA. NOT NULL' 
;

COMMENT ON COLUMN RUTA.estacion_origen_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN RUTA.estacion_destino_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN RUTA.sentido IS 'p.ej. Norte-Sur' 
;

COMMENT ON COLUMN RUTA.tipo_servicio IS 'CHECK: Local, Expreso, Nocturno, Especial, Temporal' 
;

COMMENT ON COLUMN RUTA.estado IS 'CHECK: Activa, Cerrada Temporalmente, Cancelada' 
;

ALTER TABLE RUTA 
    ADD CONSTRAINT PK_RUTA PRIMARY KEY ( id_ruta ) ;

ALTER TABLE RUTA 
    ADD CONSTRAINT UK_RUTA_CODIGO UNIQUE ( codigo ) ;

CREATE TABLE RUTA_DETALLE 
    ( 
     id_ruta_detalle             NUMBER (10)  NOT NULL , 
     ruta_id                     NUMBER (8)  NOT NULL , 
     estacion_id                 NUMBER (8)  NOT NULL , 
     orden_llegada               NUMBER (3)  NOT NULL , 
     hora_estimada_llegada       DATE , 
     hora_estimada_salida        DATE , 
     distancia_desde_anterior_km NUMBER (6,2) , 
     tiempo_desde_anterior_min   NUMBER (5) , 
     se_detiene                  CHAR (1) 
    ) 
    LOGGING 
;

ALTER TABLE RUTA_DETALLE 
    ADD CONSTRAINT CK_RUTA_DETALLE_SE_DETIENE 
    CHECK (se_detiene IN ('N', 'S')) 
;

COMMENT ON TABLE RUTA_DETALLE IS 'Secuencia ordenada de estaciones que conforman una ruta específica (soporta servicio expreso).'
;

COMMENT ON COLUMN RUTA_DETALLE.id_ruta_detalle IS 'Identificador único' 
;

COMMENT ON COLUMN RUTA_DETALLE.ruta_id IS '-> RUTA. NOT NULL' 
;

COMMENT ON COLUMN RUTA_DETALLE.estacion_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN RUTA_DETALLE.orden_llegada IS 'NOT NULL' 
;

COMMENT ON COLUMN RUTA_DETALLE.hora_estimada_llegada IS 'Componente de hora' 
;

COMMENT ON COLUMN RUTA_DETALLE.hora_estimada_salida IS 'Componente de hora' 
;

COMMENT ON COLUMN RUTA_DETALLE.se_detiene IS 'CHECK: S, N. ''N'' = tren pasa sin detenerse (expreso)' 
;

ALTER TABLE RUTA_DETALLE 
    ADD CONSTRAINT PK_RUTA_DETALLE PRIMARY KEY ( id_ruta_detalle ) ;

ALTER TABLE RUTA_DETALLE 
    ADD CONSTRAINT UK_RUTA_DETALLE_1 UNIQUE ( ruta_id , orden_llegada ) ;

ALTER TABLE RUTA_DETALLE 
    ADD CONSTRAINT UK_RUTA_DETALLE_2 UNIQUE ( ruta_id , estacion_id ) ;

CREATE TABLE TARIFA 
    ( 
     id_tarifa               NUMBER (8)  NOT NULL , 
     codigo                  VARCHAR2 (15)  NOT NULL , 
     nombre                  VARCHAR2 (60) , 
     descripcion             VARCHAR2 (200) , 
     monto                   NUMBER (8,2)  NOT NULL , 
     tipo_pasajero           VARCHAR2 (25) , 
     fecha_inicio_vigencia   DATE  NOT NULL , 
     fecha_fin_vigencia      DATE , 
     cantidad_maxima_viajes  NUMBER (4) , 
     duracion_beneficio_dias NUMBER (5) , 
     estado                  VARCHAR2 (15) 
    ) 
    LOGGING 
;

ALTER TABLE TARIFA 
    ADD CONSTRAINT CK_TARIFA_ESTADO 
    CHECK (estado IN ('Suspendida', 'Vencida', 'Vigente')) 
;

COMMENT ON TABLE TARIFA IS 'Tarifa vigente por tipo de pasajero/producto; se conserva historial.'
;

COMMENT ON COLUMN TARIFA.id_tarifa IS 'Identificador único' 
;

COMMENT ON COLUMN TARIFA.codigo IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN TARIFA.nombre IS 'p.ej. Pase Semanal, Tarifa Reducida' 
;

COMMENT ON COLUMN TARIFA.monto IS 'NOT NULL' 
;

COMMENT ON COLUMN TARIFA.fecha_inicio_vigencia IS 'NOT NULL' 
;

COMMENT ON COLUMN TARIFA.estado IS 'CHECK: Vigente, Vencida, Suspendida' 
;

ALTER TABLE TARIFA 
    ADD CONSTRAINT PK_TARIFA PRIMARY KEY ( id_tarifa ) ;

ALTER TABLE TARIFA 
    ADD CONSTRAINT UK_TARIFA_CODIGO UNIQUE ( codigo ) ;

CREATE TABLE TARJETA 
    ( 
     id_tarjeta        NUMBER (10)  NOT NULL , 
     numero_tarjeta    VARCHAR2 (20)  NOT NULL , 
     pasajero_id       NUMBER (10) , 
     fecha_emision     DATE , 
     fecha_vencimiento DATE , 
     saldo_disponible  NUMBER (8,2) , 
     tarifa_id         NUMBER (8) , 
     estado            VARCHAR2 (20) 
    ) 
    LOGGING 
;

ALTER TABLE TARJETA 
    ADD CONSTRAINT CK_TARJETA_SALDO_DISPONIBLE 
    CHECK (saldo_disponible >= 0) 
;

ALTER TABLE TARJETA 
    ADD CONSTRAINT CK_TARJETA_ESTADO 
    CHECK (estado IN ('Activa', 'Bloqueada', 'Cancelada', 'Reportada Perdida', 'Vencida')) 
;

COMMENT ON TABLE TARJETA IS 'Tarjeta electrónica; puede ser nominal (pasajero_id) o anónima (NULL).'
;

COMMENT ON COLUMN TARJETA.id_tarjeta IS 'Identificador único' 
;

COMMENT ON COLUMN TARJETA.numero_tarjeta IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN TARJETA.pasajero_id IS '-> PASAJERO. NULL = tarjeta anónima' 
;

COMMENT ON COLUMN TARJETA.saldo_disponible IS 'CHECK >= 0' 
;

COMMENT ON COLUMN TARJETA.tarifa_id IS '-> TARIFA. Plan asociado (p.ej. Pase Mensual); NULL si es de pago por viaje' 
;

COMMENT ON COLUMN TARJETA.estado IS 'CHECK: Activa, Bloqueada, Vencida, Reportada Perdida, Cancelada' 
;

ALTER TABLE TARJETA 
    ADD CONSTRAINT PK_TARJETA PRIMARY KEY ( id_tarjeta ) ;

ALTER TABLE TARJETA 
    ADD CONSTRAINT UK_TARJETA_NUMERO_TARJETA UNIQUE ( numero_tarjeta ) ;

CREATE TABLE TRANSFERENCIA 
    ( 
     id_transferencia    NUMBER (10)  NOT NULL , 
     estacion_id         NUMBER (8)  NOT NULL , 
     linea_origen_id     NUMBER (6)  NOT NULL , 
     linea_destino_id    NUMBER (6)  NOT NULL , 
     tiempo_estimado_min NUMBER (4) 
    ) 
    LOGGING 
;

COMMENT ON TABLE TRANSFERENCIA IS 'Transferencia posible entre dos líneas dentro de una estación de transferencia.'
;

COMMENT ON COLUMN TRANSFERENCIA.id_transferencia IS 'Identificador único' 
;

COMMENT ON COLUMN TRANSFERENCIA.estacion_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN TRANSFERENCIA.linea_origen_id IS '-> LINEA. NOT NULL' 
;

COMMENT ON COLUMN TRANSFERENCIA.linea_destino_id IS '-> LINEA. NOT NULL' 
;

COMMENT ON COLUMN TRANSFERENCIA.tiempo_estimado_min IS 'Tiempo estimado para efectuar el cambio' 
;

ALTER TABLE TRANSFERENCIA 
    ADD CONSTRAINT PK_TRANSFERENCIA PRIMARY KEY ( id_transferencia ) ;

ALTER TABLE TRANSFERENCIA 
    ADD CONSTRAINT UK_TRANSFERENCIA_1 UNIQUE ( estacion_id , linea_origen_id , linea_destino_id ) ;

CREATE TABLE TREN 
    ( 
     id_tren                  NUMBER (8)  NOT NULL , 
     codigo_interno           VARCHAR2 (15)  NOT NULL , 
     modelo_id                NUMBER (4)  NOT NULL , 
     anio_fabricacion         NUMBER (4) , 
     capacidad_total          NUMBER (6) , 
     estado_operativo         VARCHAR2 (20) , 
     kilometraje_acumulado    NUMBER (10,2) , 
     deposito_id              NUMBER (4) , 
     fecha_ultima_inspeccion  DATE , 
     fecha_proxima_inspeccion DATE 
    ) 
    LOGGING 
;

ALTER TABLE TREN 
    ADD CONSTRAINT CK_TREN_ESTADO_OPERATIVO 
    CHECK (estado_operativo IN ('Disponible', 'En Mantenimiento', 'En Operación', 'Fuera de Servicio', 'Retirado')) 
;

COMMENT ON TABLE TREN IS 'Unidad de tren que compone la flota.'
;

COMMENT ON COLUMN TREN.id_tren IS 'Identificador único' 
;

COMMENT ON COLUMN TREN.codigo_interno IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN TREN.modelo_id IS '-> MODELO_TREN. NOT NULL' 
;

COMMENT ON COLUMN TREN.estado_operativo IS 'CHECK: Disponible, En Operación, En Mantenimiento, Fuera de Servicio, Retirado' 
;

COMMENT ON COLUMN TREN.deposito_id IS '-> DEPOSITO' 
;

ALTER TABLE TREN 
    ADD CONSTRAINT PK_TREN PRIMARY KEY ( id_tren ) ;

ALTER TABLE TREN 
    ADD CONSTRAINT UK_TREN_CODIGO_INTERNO UNIQUE ( codigo_interno ) ;

CREATE TABLE TREN_VAGON 
    ( 
     id_tren_vagon NUMBER (10)  NOT NULL , 
     tren_id       NUMBER (8)  NOT NULL , 
     vagon_id      NUMBER (8)  NOT NULL , 
     posicion      NUMBER (2)  NOT NULL , 
     fecha_inicio  DATE  NOT NULL , 
     fecha_fin     DATE 
    ) 
    LOGGING 
;

COMMENT ON TABLE TREN_VAGON IS 'Historial de asignación de vagones a trenes (composición del tren en el tiempo).'
;

COMMENT ON COLUMN TREN_VAGON.id_tren_vagon IS 'Identificador único' 
;

COMMENT ON COLUMN TREN_VAGON.tren_id IS '-> TREN. NOT NULL' 
;

COMMENT ON COLUMN TREN_VAGON.vagon_id IS '-> VAGON. NOT NULL' 
;

COMMENT ON COLUMN TREN_VAGON.posicion IS 'NOT NULL. Posición dentro del tren' 
;

COMMENT ON COLUMN TREN_VAGON.fecha_inicio IS 'NOT NULL' 
;

COMMENT ON COLUMN TREN_VAGON.fecha_fin IS 'NULL = asignación vigente' 
;

ALTER TABLE TREN_VAGON 
    ADD CONSTRAINT PK_TREN_VAGON PRIMARY KEY ( id_tren_vagon ) ;

CREATE TABLE TURNO 
    ( 
     id_turno          NUMBER (10)  NOT NULL , 
     codigo_turno      VARCHAR2 (15)  NOT NULL , 
     empleado_id       NUMBER (8)  NOT NULL , 
     fecha             DATE  NOT NULL , 
     hora_inicio       TIMESTAMP  NOT NULL , 
     hora_fin          TIMESTAMP  NOT NULL , 
     tipo_lugar        VARCHAR2 (20) , 
     lugar_id          NUMBER (10) , 
     funcion           VARCHAR2 (50) , 
     estado_asistencia VARCHAR2 (20) 
    ) 
    LOGGING 
;

ALTER TABLE TURNO 
    ADD CONSTRAINT CK_TURNO_TIPO_LUGAR 
    CHECK (tipo_lugar IN ('Centro de Control', 'Depósito', 'Estación', 'Ruta', 'Tren')) 
;

ALTER TABLE TURNO 
    ADD CONSTRAINT CK_TURNO_ESTADO_ASISTENCIA 
    CHECK (estado_asistencia IN ('Ausente', 'Permiso', 'Presente', 'Programado', 'Sustituido', 'Vacaciones')) 
;

COMMENT ON TABLE TURNO IS 'Turno de trabajo programado para un empleado.'
;

COMMENT ON COLUMN TURNO.id_turno IS 'Identificador único' 
;

COMMENT ON COLUMN TURNO.codigo_turno IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN TURNO.empleado_id IS '-> EMPLEADO. NOT NULL' 
;

COMMENT ON COLUMN TURNO.fecha IS 'NOT NULL' 
;

COMMENT ON COLUMN TURNO.hora_inicio IS 'NOT NULL' 
;

COMMENT ON COLUMN TURNO.hora_fin IS 'NOT NULL' 
;

COMMENT ON COLUMN TURNO.tipo_lugar IS 'CHECK: Estación, Tren, Depósito, Ruta, Centro de Control' 
;

COMMENT ON COLUMN TURNO.lugar_id IS 'Referencia polimórfica según tipo_lugar (sin FK forzada)' 
;

COMMENT ON COLUMN TURNO.funcion IS 'Función que realizará' 
;

COMMENT ON COLUMN TURNO.estado_asistencia IS 'CHECK: Programado, Presente, Ausente, Permiso, Vacaciones, Sustituido' 
;

ALTER TABLE TURNO 
    ADD CONSTRAINT PK_TURNO PRIMARY KEY ( id_turno ) ;

ALTER TABLE TURNO 
    ADD CONSTRAINT UK_TURNO_CODIGO_TURNO UNIQUE ( codigo_turno ) ;

CREATE TABLE VAGON 
    ( 
     id_vagon           NUMBER (8)  NOT NULL , 
     numero_serie       VARCHAR2 (20)  NOT NULL , 
     tipo_vagon         VARCHAR2 (20) , 
     capacidad_sentados NUMBER (4) , 
     capacidad_de_pie   NUMBER (4) , 
     anio_fabricacion   NUMBER (4) , 
     estado             VARCHAR2 (20) , 
     accesibilidad      CHAR (1) 
    ) 
    LOGGING 
;

ALTER TABLE VAGON 
    ADD CONSTRAINT CK_VAGON_ESTADO 
    CHECK (estado IN ('Disponible', 'En Uso', 'Fuera de Servicio', 'Mantenimiento')) 
;

ALTER TABLE VAGON 
    ADD CONSTRAINT CK_VAGON_ACCESIBILIDAD 
    CHECK (accesibilidad IN ('N', 'S')) 
;

COMMENT ON TABLE VAGON IS 'Vagón individual; su pertenencia a un tren se conserva como historial en TREN_VAGON.'
;

COMMENT ON COLUMN VAGON.id_vagon IS 'Identificador único' 
;

COMMENT ON COLUMN VAGON.numero_serie IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN VAGON.estado IS 'CHECK: Disponible, En Uso, Mantenimiento, Fuera de Servicio' 
;

COMMENT ON COLUMN VAGON.accesibilidad IS 'CHECK: S, N' 
;

ALTER TABLE VAGON 
    ADD CONSTRAINT PK_VAGON PRIMARY KEY ( id_vagon ) ;

ALTER TABLE VAGON 
    ADD CONSTRAINT UK_VAGON_NUMERO_SERIE UNIQUE ( numero_serie ) ;

CREATE TABLE VIAJE_PASAJERO 
    ( 
     id_viaje_pasajero   NUMBER (14)  NOT NULL , 
     numero_transaccion  VARCHAR2 (25)  NOT NULL , 
     tarjeta_id          NUMBER (10)  NOT NULL , 
     estacion_ingreso_id NUMBER (8)  NOT NULL , 
     fecha_hora_ingreso  TIMESTAMP  NOT NULL , 
     estacion_salida_id  NUMBER (8) , 
     fecha_hora_salida   TIMESTAMP , 
     tarifa_id           NUMBER (8)  NOT NULL , 
     monto_cobrado       NUMBER (8,2) , 
     viaje_programado_id NUMBER (10) , 
     estado_transaccion  VARCHAR2 (15) 
    ) 
    LOGGING 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT CK_VIAJE_PASAJERO_ESTADO__0D11 
    CHECK (estado_transaccion IN ('Abierta', 'Anulada', 'Cerrada')) 
;

COMMENT ON TABLE VIAJE_PASAJERO IS 'Transacción de acceso/salida de un pasajero (nominal o anónimo) al sistema.'
;

COMMENT ON COLUMN VIAJE_PASAJERO.id_viaje_pasajero IS 'Identificador único' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.numero_transaccion IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.tarjeta_id IS '-> TARJETA. NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.estacion_ingreso_id IS '-> ESTACION. NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.fecha_hora_ingreso IS 'NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.estacion_salida_id IS '-> ESTACION' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.tarifa_id IS '-> TARIFA. NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.viaje_programado_id IS '-> VIAJE_PROGRAMADO. Opcional/NULL si abordaje no registrado por tren especifico' 
;

COMMENT ON COLUMN VIAJE_PASAJERO.estado_transaccion IS 'CHECK: Abierta, Cerrada, Anulada' 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT PK_VIAJE_PASAJERO PRIMARY KEY ( id_viaje_pasajero ) ;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT UK_VIAJE_PASAJERO_NUMERO__D88E UNIQUE ( numero_transaccion ) ;

CREATE TABLE VIAJE_PROGRAMADO 
    ( 
     id_viaje                    NUMBER (10)  NOT NULL , 
     numero_viaje                VARCHAR2 (20)  NOT NULL , 
     ruta_id                     NUMBER (8)  NOT NULL , 
     horario_id                  NUMBER (8) , 
     fecha                       DATE  NOT NULL , 
     hora_prog_salida            TIMESTAMP , 
     hora_real_salida            TIMESTAMP , 
     hora_prog_llegada           TIMESTAMP , 
     hora_real_llegada           TIMESTAMP , 
     tren_id                     NUMBER (8) , 
     conductor_id                NUMBER (8) , 
     estado                      VARCHAR2 (20) , 
     cantidad_estimada_pasajeros NUMBER (6) 
    ) 
    LOGGING 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT CK_VIAJE_PROGRAMADO_HORA__C368 
    CHECK (hora_real_llegada >= hora_real_salida) 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT CK_VIAJE_PROGRAMADO_ESTADO 
    CHECK (estado IN ('Cancelado', 'Completado', 'En Abordaje', 'En Curso', 'Programado', 'Retrasado')) 
;

COMMENT ON TABLE VIAJE_PROGRAMADO IS 'Ejecución concrééeta de una ruta en una fecha y hora determinadas.'
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.id_viaje IS 'Identificador único' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.numero_viaje IS 'UNIQUE, NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.ruta_id IS '-> RUTA. NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.horario_id IS '-> HORARIO. Horario que originó el viaje (opcional)' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.fecha IS 'NOT NULL' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.hora_real_llegada IS 'CHECK: >= hora_real_salida' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.tren_id IS '-> TREN' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.conductor_id IS '-> EMPLEADO' 
;

COMMENT ON COLUMN VIAJE_PROGRAMADO.estado IS 'CHECK: Programado, En Abordaje, En Curso, Completado, Retrasado, Cancelado' 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT PK_VIAJE_PROGRAMADO PRIMARY KEY ( id_viaje ) ;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT UK_VIAJE_PROGRAMADO_NUMER_C5CD UNIQUE ( numero_viaje ) ;

ALTER TABLE CERTIFICACION 
    ADD CONSTRAINT FK_CERTIFICACION_EMPLEADO_ID FOREIGN KEY 
    ( 
     empleado_id
    ) 
    REFERENCES EMPLEADO 
    ( 
     id_empleado
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE CERTIFICACION_MODELO 
    ADD CONSTRAINT FK_CERTIFICACION_MODELO_C_D986 FOREIGN KEY 
    ( 
     certificacion_id
    ) 
    REFERENCES CERTIFICACION 
    ( 
     id_certificacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE CERTIFICACION_MODELO 
    ADD CONSTRAINT FK_CERTIFICACION_MODELO_M_46AE FOREIGN KEY 
    ( 
     modelo_id
    ) 
    REFERENCES MODELO_TREN 
    ( 
     id_modelo
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE EMPLEADO 
    ADD CONSTRAINT FK_EMPLEADO_SUPERVISOR_ID FOREIGN KEY 
    ( 
     supervisor_id
    ) 
    REFERENCES EMPLEADO 
    ( 
     id_empleado
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE ESTACION_SERVICIO 
    ADD CONSTRAINT FK_ESTACION_SERVICIO_ESTA_DEE3 FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE HORARIO_ESTACION 
    ADD CONSTRAINT FK_HORARIO_ESTACION_ESTACION_ID FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE HORARIO 
    ADD CONSTRAINT FK_HORARIO_RUTA_ID FOREIGN KEY 
    ( 
     ruta_id
    ) 
    REFERENCES RUTA 
    ( 
     id_ruta
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INC_ELEM_EQUIPO_ID FOREIGN KEY 
    ( 
     equipo_id
    ) 
    REFERENCES EQUIPO 
    ( 
     id_equipo
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INC_ELEM_ESTACION_ID FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INC_ELEM_LINEA_ID FOREIGN KEY 
    ( 
     linea_id
    ) 
    REFERENCES LINEA 
    ( 
     id_linea
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INC_ELEM_RUTA_ID FOREIGN KEY 
    ( 
     ruta_id
    ) 
    REFERENCES RUTA 
    ( 
     id_ruta
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INC_ELEM_TREN_ID FOREIGN KEY 
    ( 
     tren_id
    ) 
    REFERENCES TREN 
    ( 
     id_tren
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INC_ELEM_VIAJE_ID FOREIGN KEY 
    ( 
     viaje_id
    ) 
    REFERENCES VIAJE_PROGRAMADO 
    ( 
     id_viaje
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE_ELEMENTO_AFECTADO 
    ADD CONSTRAINT FK_INCIDENTE_ELEMENTO_AFE_53BA FOREIGN KEY 
    ( 
     incidente_id
    ) 
    REFERENCES INCIDENTE 
    ( 
     id_incidente
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE INCIDENTE 
    ADD CONSTRAINT FK_INCIDENTE_REPORTADO_POR_ID FOREIGN KEY 
    ( 
     reportado_por_id
    ) 
    REFERENCES EMPLEADO 
    ( 
     id_empleado
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE LINEA 
    ADD CONSTRAINT FK_LINEA_ESTACION_DESTINO_ID FOREIGN KEY 
    ( 
     estacion_destino_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE LINEA_ESTACION 
    ADD CONSTRAINT FK_LINEA_ESTACION_ESTACION_ID FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE LINEA_ESTACION 
    ADD CONSTRAINT FK_LINEA_ESTACION_LINEA_ID FOREIGN KEY 
    ( 
     linea_id
    ) 
    REFERENCES LINEA 
    ( 
     id_linea
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE LINEA 
    ADD CONSTRAINT FK_LINEA_ESTACION_ORIGEN_ID FOREIGN KEY 
    ( 
     estacion_origen_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE ORDEN_MANTENIMIENTO 
    ADD CONSTRAINT FK_ORDEN_MANTENIMIENTO_EQ_95B5 FOREIGN KEY 
    ( 
     equipo_id
    ) 
    REFERENCES EQUIPO 
    ( 
     id_equipo
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE ORDEN_REPUESTO 
    ADD CONSTRAINT FK_ORDEN_REPUESTO_ORDEN_ID FOREIGN KEY 
    ( 
     orden_id
    ) 
    REFERENCES ORDEN_MANTENIMIENTO 
    ( 
     id_orden
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE ORDEN_REPUESTO 
    ADD CONSTRAINT FK_ORDEN_REPUESTO_REPUESTO_ID FOREIGN KEY 
    ( 
     repuesto_id
    ) 
    REFERENCES REPUESTO 
    ( 
     id_repuesto
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE ORDEN_TECNICO 
    ADD CONSTRAINT FK_ORDEN_TECNICO_EMPLEADO_ID FOREIGN KEY 
    ( 
     empleado_id
    ) 
    REFERENCES EMPLEADO 
    ( 
     id_empleado
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE ORDEN_TECNICO 
    ADD CONSTRAINT FK_ORDEN_TECNICO_ORDEN_ID FOREIGN KEY 
    ( 
     orden_id
    ) 
    REFERENCES ORDEN_MANTENIMIENTO 
    ( 
     id_orden
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE PLATAFORMA 
    ADD CONSTRAINT FK_PLATAFORMA_ESTACION_ID FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE RECARGA 
    ADD CONSTRAINT FK_RECARGA_TARJETA_ID FOREIGN KEY 
    ( 
     tarjeta_id
    ) 
    REFERENCES TARJETA 
    ( 
     id_tarjeta
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE RUTA_DETALLE 
    ADD CONSTRAINT FK_RUTA_DETALLE_ESTACION_ID FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE RUTA_DETALLE 
    ADD CONSTRAINT FK_RUTA_DETALLE_RUTA_ID FOREIGN KEY 
    ( 
     ruta_id
    ) 
    REFERENCES RUTA 
    ( 
     id_ruta
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE RUTA 
    ADD CONSTRAINT FK_RUTA_ESTACION_DESTINO_ID FOREIGN KEY 
    ( 
     estacion_destino_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE RUTA 
    ADD CONSTRAINT FK_RUTA_ESTACION_ORIGEN_ID FOREIGN KEY 
    ( 
     estacion_origen_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE RUTA 
    ADD CONSTRAINT FK_RUTA_LINEA_ID FOREIGN KEY 
    ( 
     linea_id
    ) 
    REFERENCES LINEA 
    ( 
     id_linea
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TARJETA 
    ADD CONSTRAINT FK_TARJETA_PASAJERO_ID FOREIGN KEY 
    ( 
     pasajero_id
    ) 
    REFERENCES PASAJERO 
    ( 
     id_pasajero
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TARJETA 
    ADD CONSTRAINT FK_TARJETA_TARIFA_ID FOREIGN KEY 
    ( 
     tarifa_id
    ) 
    REFERENCES TARIFA 
    ( 
     id_tarifa
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TRANSFERENCIA 
    ADD CONSTRAINT FK_TRANSFERENCIA_ESTACION_ID FOREIGN KEY 
    ( 
     estacion_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TRANSFERENCIA 
    ADD CONSTRAINT FK_TRANSFERENCIA_LINEA_DE_3222 FOREIGN KEY 
    ( 
     linea_destino_id
    ) 
    REFERENCES LINEA 
    ( 
     id_linea
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TRANSFERENCIA 
    ADD CONSTRAINT FK_TRANSFERENCIA_LINEA_OR_0F7F FOREIGN KEY 
    ( 
     linea_origen_id
    ) 
    REFERENCES LINEA 
    ( 
     id_linea
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TREN 
    ADD CONSTRAINT FK_TREN_DEPOSITO_ID FOREIGN KEY 
    ( 
     deposito_id
    ) 
    REFERENCES DEPOSITO 
    ( 
     id_deposito
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TREN 
    ADD CONSTRAINT FK_TREN_MODELO_ID FOREIGN KEY 
    ( 
     modelo_id
    ) 
    REFERENCES MODELO_TREN 
    ( 
     id_modelo
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TREN_VAGON 
    ADD CONSTRAINT FK_TREN_VAGON_TREN_ID FOREIGN KEY 
    ( 
     tren_id
    ) 
    REFERENCES TREN 
    ( 
     id_tren
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TREN_VAGON 
    ADD CONSTRAINT FK_TREN_VAGON_VAGON_ID FOREIGN KEY 
    ( 
     vagon_id
    ) 
    REFERENCES VAGON 
    ( 
     id_vagon
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE TURNO 
    ADD CONSTRAINT FK_TURNO_EMPLEADO_ID FOREIGN KEY 
    ( 
     empleado_id
    ) 
    REFERENCES EMPLEADO 
    ( 
     id_empleado
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT FK_VIAJE_PAS_VIAJE_PROG_ID FOREIGN KEY 
    ( 
     viaje_programado_id
    ) 
    REFERENCES VIAJE_PROGRAMADO 
    ( 
     id_viaje
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT FK_VIAJE_PASAJERO_ESTACIO_3F85 FOREIGN KEY 
    ( 
     estacion_ingreso_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT FK_VIAJE_PASAJERO_ESTACIO_9F8E FOREIGN KEY 
    ( 
     estacion_salida_id
    ) 
    REFERENCES ESTACION 
    ( 
     id_estacion
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT FK_VIAJE_PASAJERO_TARIFA_ID FOREIGN KEY 
    ( 
     tarifa_id
    ) 
    REFERENCES TARIFA 
    ( 
     id_tarifa
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PASAJERO 
    ADD CONSTRAINT FK_VIAJE_PASAJERO_TARJETA_ID FOREIGN KEY 
    ( 
     tarjeta_id
    ) 
    REFERENCES TARJETA 
    ( 
     id_tarjeta
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT FK_VIAJE_PROGRAMADO_CONDU_9753 FOREIGN KEY 
    ( 
     conductor_id
    ) 
    REFERENCES EMPLEADO 
    ( 
     id_empleado
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT FK_VIAJE_PROGRAMADO_HORARIO_ID FOREIGN KEY 
    ( 
     horario_id
    ) 
    REFERENCES HORARIO 
    ( 
     id_horario
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT FK_VIAJE_PROGRAMADO_RUTA_ID FOREIGN KEY 
    ( 
     ruta_id
    ) 
    REFERENCES RUTA 
    ( 
     id_ruta
    ) 
    NOT DEFERRABLE 
;

ALTER TABLE VIAJE_PROGRAMADO 
    ADD CONSTRAINT FK_VIAJE_PROGRAMADO_TREN_ID FOREIGN KEY 
    ( 
     tren_id
    ) 
    REFERENCES TREN 
    ( 
     id_tren
    ) 
    NOT DEFERRABLE 
;



-- Rapport récapitulatif d'Oracle SQL Developer Data Modeler : 
-- 
-- CREATE TABLE                            33
-- CREATE INDEX                             0
-- ALTER TABLE                            161
-- CREATE VIEW                              0
-- ALTER VIEW                               0
-- CREATE PACKAGE                           0
-- CREATE PACKAGE BODY                      0
-- CREATE PROCEDURE                         0
-- CREATE FUNCTION                          0
-- CREATE TRIGGER                           0
-- ALTER TRIGGER                            0
-- CREATE COLLECTION TYPE                   0
-- CREATE STRUCTURED TYPE                   0
-- CREATE STRUCTURED TYPE BODY              0
-- CREATE CLUSTER                           0
-- CREATE CONTEXT                           0
-- CREATE DATABASE                          0
-- CREATE DIMENSION                         0
-- CREATE DIRECTORY                         0
-- CREATE DISK GROUP                        0
-- CREATE ROLE                              0
-- CREATE ROLLBACK SEGMENT                  0
-- CREATE SEQUENCE                         33
-- CREATE MATERIALIZED VIEW                 0
-- CREATE MATERIALIZED VIEW LOG             0
-- CREATE SYNONYM                           0
-- CREATE TABLESPACE                        0
-- CREATE USER                              0
-- 
-- DROP TABLESPACE                          0
-- DROP DATABASE                            0
-- 
-- REDACTION POLICY                         0
-- 
-- ORDS DROP SCHEMA                         0
-- ORDS ENABLE SCHEMA                       0
-- ORDS ENABLE OBJECT                       0
-- 
-- ERRORS                                   0
-- WARNINGS                                 0

EXIT;
