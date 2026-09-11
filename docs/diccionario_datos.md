# Diccionario de Datos Institucional — Metro de Nueva York (MTA NYCT)
## Esquema Canónico de Base de Datos Relacional (Oracle 23ai)

> **Entregable Oficial No. 4**: Especificación exhaustiva de tablas, columnas, dominios de datos, llaves primarias, foráneas, restricciones de unicidad y restricciones CHECK de integridad semántica.

---

## 1. Estándares y Convenciones Físicas de Diseño

En estricta observancia de los lineamientos metodológicos de la cátedra de Sistemas de Bases de Datos 1 (Bases de Datos I) y el estándar **Barker CDM / Oracle Data Modeler**:
1. **Nomenclatura de Tablas**:
   - Escritas rigurosamente en **MAYÚSCULAS**, en número **SINGULAR** y sin caracteres especiales ni tildes (ej. `ESTACION`, `TREN`, `ORDEN_MANTENIMIENTO`).
2. **Nomenclatura de Columnas**:
   - Nombres claros y funcionales en **MAYÚSCULAS** dentro de Oracle, evitando redundar el nombre de la entidad en el atributo salvo llaves foráneas descriptivas (ej. `ESTACION.NOMBRE`, no `ESTACION.NOMBRE_ESTACION`).
3. **Tipos de Datos Utilizados**:
   - Cadenas alfanuméricas: `VARCHAR2(n)` de longitud dinámica (se prohíbe `CHAR(n)` para evitar desperdicio de almacenamiento en bloque con espacios en blanco).
   - Numéricos: `NUMBER` para identificadores enteros y `NUMBER(p,s)` para montos monetarios ($ USD) o distancias kilométricas con decimales exactos.
   - Fechas y Tiempos: `DATE` para marcas de tiempo con precisión de segundos (almacena año, mes, día, hora, minuto, segundo en formato interno compacto de 7 bytes).
4. **Nomenclatura Canónica de Restricciones**:
   - Llave Primaria: `PK_<NOMBRE_TABLA>`
   - Llave Foránea: `FK_<NOMBRE_TABLA>_<COLUMNA>`
   - Llave Única: `UK_<NOMBRE_TABLA>_<COLUMNA>`
   - Restricción Check: `CK_<NOMBRE_TABLA>_<COLUMNA>`
5. **Políticas de Restricción**:
   - Ninguna restricción de negocio ha sido delegada a nombres automáticos de sistema (`SYS_C...`).
   - Se prohíbe el almacenamiento de atributos derivados o calculados (saldos totales, recaudaciones acumuladas, etc.), calculándose en tiempo real mediante vistas y funciones.


---

## 2. Inventario General de Tablas del Esquema `METRO_NY`

| No. | Tabla | Propósito Operativo en la Red MTA | Total Columnas | Total Constraints |
| :---: | :--- | :--- | :---: | :---: |
| 1 | [`BITACORA`](#bitacora) | Registro transversal de auditoría del sistema que almacena eventos críticos (cambios de estado operativo de trenes, aperturas/cierres de incidentes, modificaciones tarifarias) disparados por triggers de base de datos. | 7 | 2 |
| 2 | [`CERTIFICACION`](#certificacion) | Gestión de licencias técnicas y certificaciones operativas del personal ferroviario (maquinistas, supervisores de tráfico, técnicos de vía), con control riguroso de fechas de emisión, vigencia y estado. | 7 | 3 |
| 3 | [`CERTIFICACION_MODELO`](#certificacion_modelo) | Entidad asociativa que especifica los modelos de material rodante (R142, R160, R211, etc.) para los cuales un maquinista o técnico cuenta con habilitación oficial de conducción o mantenimiento. | 3 | 4 |
| 4 | [`DEPOSITO`](#deposito) | Yardas, depósitos y talleres principales de maniobras de la MTA (ej. 207th St Yard, Coney Island Complex, Pitkin Yard) donde se resguardan, limpian e intervienen los convoyes de la flota. | 5 | 2 |
| 5 | [`EMPLEADO`](#empleado) | Padrón institucional de recursos humanos de MTA New York City Transit. Almacena nombres atómicos, cargo, turno habitual, fecha de contratación y supervisor jerárquico inmediato. | 13 | 6 |
| 6 | [`EQUIPO`](#equipo) | Inventario de activos e instalaciones electromecánicas situadas en estaciones (elevadores accesibles ADA, escaleras mecánicas mecánicas, torniquetes OMNY, máquinas expendedoras MVM) con estado operativo. | 13 | 5 |
| 7 | [`ESTACION`](#estacion) | Infraestructura física de detención de pasajeros de la red. Contiene datos de localización geográfica (WGS84 lat/long), distrito administrativo (borough), accesibilidad universal ADA y estado de servicio. | 16 | 8 |
| 8 | [`ESTACION_SERVICIO`](#estacion_servicio) | Entidad asociativa que registra la disponibilidad de servicios al usuario en cada estación (baños públicos, puestos de primeros auxilios, Wi-Fi subterráneo, custodia policial NYPD Transit). | 4 | 5 |
| 9 | [`HORARIO`](#horario) | Plan maestro de frecuencias y ventanas de operación para los días de semana (Weekday), sábados (Saturday) y domingos/feriados (Sunday/Holiday). | 9 | 3 |
| 10 | [`HORARIO_ESTACION`](#horario_estacion) | Horarios oficiales de apertura y cierre de accesos de cada estación para cada día de la semana. | 7 | 6 |
| 11 | [`INCIDENTE`](#incidente) | Control y despacho de contingencias operativas en la red (fallas de señal CBTC, emergencias médicas, intrusión en vía, inundaciones) con nivel de severidad, estado y reporte cronológico. | 12 | 7 |
| 12 | [`INCIDENTE_ELEMENTO_AFECTADO`](#incidente_elemento_afectado) | Entidad asociativa que relaciona cada incidente con el activo específico afectado (estación, tramo de vía, tren o ruta completa) y detalla la medida de contingencia aplicada. | 10 | 10 |
| 13 | [`LINEA`](#linea) | Líneas troncales comerciales del sistema de metro (ej. Línea A - 8th Avenue Express, Línea 7 - Flushing Local/Express), color identificador MTA, división técnica (A o B) y terminales. | 11 | 6 |
| 14 | [`LINEA_ESTACION`](#linea_estacion) | Entidad asociativa que define la topología de la red: el orden secuencial en que una línea recorre sus estaciones, con distancias kilométricas y tiempos estimados de enlace. | 6 | 5 |
| 15 | [`MODELO_TREN`](#modelo_tren) | Catálogo técnico de material rodante (ej. R142, R160, R188, R211). Define gálibo estructural (División A estrecho vs División B ancho), fabricante, tipo de propulsión y velocidad máxima de diseño. | 3 | 2 |
| 16 | [`ORDEN_MANTENIMIENTO`](#orden_mantenimiento) | Órdenes de servicio técnico preventivo, correctivo o predictivo aplicadas a trenes, vagones o equipos de estación, con prioridad, horas invertidas y estado de ejecución. | 12 | 6 |
| 17 | [`ORDEN_REPUESTO`](#orden_repuesto) | Entidad asociativa que contabiliza los componentes y repuestos mecánicos o electrónicos consumidos en una orden de mantenimiento, con sus cantidades y costos unitarios. | 5 | 3 |
| 18 | [`ORDEN_TECNICO`](#orden_tecnico) | Entidad asociativa que asigna el personal técnico calificado a una orden de mantenimiento, registrando horas hombre trabajadas y rol de intervención. | 4 | 4 |
| 19 | [`PASAJERO`](#pasajero) | Padrón de usuarios del sistema de metro. Registra datos personales atómicos, categoría de usuario (Regular, Estudiante, Adulto Mayor, Discapacidad) para la aplicación de descuentos. | 9 | 4 |
| 20 | [`PLATAFORMA`](#plataforma) | Andenes físicos de embarque dentro de las estaciones, especificando sentido de circulación (Uptown / Downtown / Manhattan-bound), tipo de andén y estado operativo. | 6 | 3 |
| 21 | [`RECARGA`](#recarga) | Transacciones financieras de acreditación de saldo en tarjetas OMNY mediante medios de pago aprobados (efectivo, tarjeta bancaria, pago móvil), registrando saldos previo y posterior. | 9 | 4 |
| 22 | [`REPUESTO`](#repuesto) | Catálogo de repuestos e insumos ferroviarios (zapatas de freno, pastillas de contacto de tercer riel, bombas de aire, módulos lógicos CBTC), stock y costo unitario. | 4 | 2 |
| 23 | [`RUTA`](#ruta) | Variantes de servicio de una línea (ej. A Express vía Fulton St, A Local nocturno) con sentido, terminales y tipo de servicio (Local, Expreso, Nocturno). | 12 | 7 |
| 24 | [`RUTA_DETALLE`](#ruta_detalle) | Secuencia pormenorizada de paradas para una ruta específica, señalando explícitamente si el tren se detiene para ascenso/descenso de pasajeros o pasa de largo sin parada (servicio exprés). | 9 | 6 |
| 25 | [`TARIFA`](#tarifa) | Estructura tarifaria reglamentaria aprobada por la MTA (Tarifa Base $2.90, Tarifa Reducida $1.45, Boleto Único, Pase Semanal con tope tarifario) con vigencia temporal. | 11 | 3 |
| 26 | [`TARJETA`](#tarjeta) | Cuentas de pago y soportes inteligentes OMNY (tarjetas físicas sin contacto, billeteras móviles, pases institucionales), saldo disponible y estado operativo de validación. | 8 | 6 |
| 27 | [`TRANSFERENCIA`](#transferencia) | Pasajes y pasillos peatonales subterráneos que permiten el trasbordo gratuito entre diferentes líneas y plataformas dentro de una misma estación o complejo intermodal. | 5 | 5 |
| 28 | [`TREN`](#tren) | Unidades de tracción y formaciones activas de la flota. Controla kilometraje acumulado, estado operativo en tiempo real (Disponible, En Operación, En Mantenimiento, Fuera de Servicio) y depósito base. | 10 | 5 |
| 29 | [`TREN_VAGON`](#tren_vagon) | Composición física y acoplamiento de coches individuales dentro de un tren específico, indicando el orden secuencial de cada vagón en la formación. | 6 | 3 |
| 30 | [`TURNO`](#turno) | Asignaciones y horarios de servicio operativo para el personal de conducción, supervisión de andén y despacho de trenes. | 10 | 5 |
| 31 | [`VAGON`](#vagon) | Coches individuales de pasajeros, clasificados por tipo de coche (cabina motriz 'A' o coche remolque intermedio 'B'), con capacidad de pasajeros sentados/de pie y fabricante. | 8 | 4 |
| 32 | [`VIAJE_PASAJERO`](#viaje_pasajero) | Registro de transacciones de validación y acceso de pasajeros en los torniquetes OMNY, debitando la tarifa correspondiente en la estación de abordaje. | 11 | 8 |
| 33 | [`VIAJE_PROGRAMADO`](#viaje_programado) | Despachos y corridas programadas de trenes en la red, asignando tren físico, maquinista certificado, ruta, horario de salida proyectado y control de retrasos en tiempo real. | 13 | 8 |

---

## 3. Especificación Detallada de Entidades y Columnas

### <a id="bitacora"></a> BITACORA
**Descripción Funcional**: Registro transversal de auditoría del sistema que almacena eventos críticos (cambios de estado operativo de trenes, aperturas/cierres de incidentes, modificaciones tarifarias) disparados por triggers de base de datos.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_BITACORA` | `NUMBER(14)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `FECHA_HORA` | `TIMESTAMP(6)` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `TABLA_AFECTADA` | `VARCHAR2(30)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `OPERACION` | `VARCHAR2(10)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `REGISTRO_ID` | `NUMBER(14)` | NULL | — | Llave foránea que referencia a la tabla REGISTRO. |
| `USUARIO` | `VARCHAR2(50)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `DESCRIPCION` | `VARCHAR2(500)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_BITACORA` sobre `(ID_BITACORA)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_BITACORA_OPERACION` sobre columna `OPERACION`: `operacion IN ('DELETE', 'INSERT', 'UPDATE')`

---

### <a id="certificacion"></a> CERTIFICACION
**Descripción Funcional**: Gestión de licencias técnicas y certificaciones operativas del personal ferroviario (maquinistas, supervisores de tráfico, técnicos de vía), con control riguroso de fechas de emisión, vigencia y estado.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_CERTIFICACION` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `EMPLEADO_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `EMPLEADO.ID_EMPLEADO` | Llave foránea que referencia a la tabla EMPLEADO. |
| `TIPO_CERTIFICACION` | `VARCHAR2(60)` | **NOT NULL** | — | Clasificación o tipología funcional del registro. |
| `FECHA_EMISION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_VENCIMIENTO` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `INSTITUCION_EMISORA` | `VARCHAR2(100)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_CERTIFICACION` sobre `(ID_CERTIFICACION)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_CERTIFICACION_EMPLEADO_ID`: Columna `(EMPLEADO_ID)` &rarr; Referencia `EMPLEADO(ID_EMPLEADO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_CERTIFICACION_ESTADO` sobre columna `ESTADO`: `estado IN ('Revocada', 'Vencida', 'Vigente')`

---

### <a id="certificacion_modelo"></a> CERTIFICACION_MODELO
**Descripción Funcional**: Entidad asociativa que especifica los modelos de material rodante (R142, R160, R211, etc.) para los cuales un maquinista o técnico cuenta con habilitación oficial de conducción o mantenimiento.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_CERTIFICACION_MODELO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CERTIFICACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `CERTIFICACION.ID_CERTIFICACION`, **UK** | Llave foránea que referencia a la tabla CERTIFICACION. |
| `MODELO_ID` | `NUMBER(4)` | **NOT NULL** | FK &rarr; `MODELO_TREN.ID_MODELO`, **UK** | Llave foránea que referencia a la tabla MODELO. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_CERTIFICACION_MODELO` sobre `(ID_CERTIFICACION_MODELO)`
- **Unicidad (UK)**: `UK_CERTIFICACION_MODELO_1` sobre `(CERTIFICACION_ID, MODELO_ID)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_CERTIFICACION_MODELO_C_D986`: Columna `(CERTIFICACION_ID)` &rarr; Referencia `CERTIFICACION(ID_CERTIFICACION)`
  - `FK_CERTIFICACION_MODELO_M_46AE`: Columna `(MODELO_ID)` &rarr; Referencia `MODELO_TREN(ID_MODELO)`

---

### <a id="deposito"></a> DEPOSITO
**Descripción Funcional**: Yardas, depósitos y talleres principales de maniobras de la MTA (ej. 207th St Yard, Coney Island Complex, Pitkin Yard) donde se resguardan, limpian e intervienen los convoyes de la flota.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_DEPOSITO` | `NUMBER(4)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO` | `VARCHAR2(10)` | NULL | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NOMBRE` | `VARCHAR2(100)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `UBICACION` | `VARCHAR2(200)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `CAPACIDAD` | `NUMBER(5)` | NULL | — | Capacidad máxima de diseño (pasajeros o unidades). |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_DEPOSITO` sobre `(ID_DEPOSITO)`
- **Unicidad (UK)**: `UK_DEPOSITO_CODIGO` sobre `(CODIGO)`

---

### <a id="empleado"></a> EMPLEADO
**Descripción Funcional**: Padrón institucional de recursos humanos de MTA New York City Transit. Almacena nombres atómicos, cargo, turno habitual, fecha de contratación y supervisor jerárquico inmediato.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_EMPLEADO` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_EMPLEADO` | `VARCHAR2(15)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `NOMBRE_COMPLETO` | `VARCHAR2(150)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FECHA_NACIMIENTO` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `DIRECCION` | `VARCHAR2(200)` | NULL | — | Dirección física o calle de ubicación del activo. |
| `TELEFONO` | `VARCHAR2(20)` | NULL | — | Número de teléfono de contacto institucional. |
| `CORREO_ELECTRONICO` | `VARCHAR2(100)` | NULL | **UK** | Dirección de correo electrónico oficial de contacto. |
| `FECHA_CONTRATACION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `CARGO` | `VARCHAR2(50)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `TURNO_HABITUAL` | `VARCHAR2(20)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `SALARIO` | `NUMBER(10,2)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTADO_LABORAL` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `SUPERVISOR_ID` | `NUMBER(8)` | NULL | FK &rarr; `EMPLEADO.ID_EMPLEADO` | Llave foránea que referencia a la tabla SUPERVISOR. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_EMPLEADO` sobre `(ID_EMPLEADO)`
- **Unicidad (UK)**: `UK_EMPLEADO_CORREO_ELECTRONICO` sobre `(CORREO_ELECTRONICO)`
- **Unicidad (UK)**: `UK_EMPLEADO_NUMERO_EMPLEADO` sobre `(NUMERO_EMPLEADO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_EMPLEADO_SUPERVISOR_ID`: Columna `(SUPERVISOR_ID)` &rarr; Referencia `EMPLEADO(ID_EMPLEADO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_EMPLEADO_CARGO` sobre columna `CARGO`: `cargo IN ('Agente de Seguridad', 'Conductor', 'Operador de Control', 'Personal de Atención al Pasajero', 'Supervisor de Estación', 'Técnico de Mantenimiento')`
  - `CK_EMPLEADO_ESTADO_LABORAL` sobre columna `ESTADO_LABORAL`: `estado_laboral IN ('Activo', 'Permiso', 'Retirado', 'Suspendido', 'Vacaciones')`

---

### <a id="equipo"></a> EQUIPO
**Descripción Funcional**: Inventario de activos e instalaciones electromecánicas situadas en estaciones (elevadores accesibles ADA, escaleras mecánicas mecánicas, torniquetes OMNY, máquinas expendedoras MVM) con estado operativo.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_EQUIPO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO_EQUIPO` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `TIPO_EQUIPO` | `VARCHAR2(30)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `TIPO_REFERENCIA` | `VARCHAR2(15)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `REFERENCIA_ID` | `NUMBER(10)` | NULL | — | Llave foránea que referencia a la tabla REFERENCIA. |
| `UBICACION` | `VARCHAR2(200)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FABRICANTE` | `VARCHAR2(60)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `MODELO` | `VARCHAR2(60)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NUMERO_SERIE` | `VARCHAR2(30)` | NULL | — | Número secuencial, código de serie o folio identificador. |
| `FECHA_INSTALACION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `FECHA_ULTIMA_REVISION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_PROXIMA_REVISION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_EQUIPO` sobre `(ID_EQUIPO)`
- **Unicidad (UK)**: `UK_EQUIPO_CODIGO_EQUIPO` sobre `(CODIGO_EQUIPO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_EQUIPO_ESTADO` sobre columna `ESTADO`: `estado IN ('Disponible', 'En Mantenimiento', 'Fuera de Servicio')`
  - `CK_EQUIPO_TIPO_EQUIPO` sobre columna `TIPO_EQUIPO`: `tipo_equipo IN ('Elevador', 'Escalera Eléctrica', 'Plataforma', 'Señal', 'Tren', 'Vagón', 'Vía')`
  - `CK_EQUIPO_TIPO_REFERENCIA` sobre columna `TIPO_REFERENCIA`: `tipo_referencia IN ('ESTACION', 'NINGUNO', 'PLATAFORMA', 'TREN', 'VAGON')`

---

### <a id="estacion"></a> ESTACION
**Descripción Funcional**: Infraestructura física de detención de pasajeros de la red. Contiene datos de localización geográfica (WGS84 lat/long), distrito administrativo (borough), accesibilidad universal ADA y estado de servicio.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_ESTACION` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO` | `VARCHAR2(10)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NOMBRE` | `VARCHAR2(100)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `DIRECCION` | `VARCHAR2(200)` | NULL | — | Dirección física o calle de ubicación del activo. |
| `DISTRITO` | `VARCHAR2(20)` | NULL | CK | Distrito administrativo de la ciudad de Nueva York. |
| `LATITUD` | `NUMBER(9,6)` | NULL | — | Coordenada geográfica WGS84 para georreferenciación. |
| `LONGITUD` | `NUMBER(9,6)` | NULL | — | Coordenada geográfica WGS84 para georreferenciación. |
| `FECHA_INAUGURACION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `CANTIDAD_ACCESOS` | `NUMBER(3)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `CANTIDAD_PLATAFORMAS` | `NUMBER(2)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTADO_OPERATIVO` | `VARCHAR2(25)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `HORARIO_FUNCIONAMIENTO` | `VARCHAR2(50)` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `ELEVADORES_DISPONIBLES` | `CHAR(1)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESCALERAS_ELECTRICAS_DISPONIBLES` | `CHAR(1)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ACCESIBLE_DISCAPACIDAD` | `CHAR(1)` | NULL | CK | Indicador de accesibilidad universal para personas con movilidad reducida (ADA). |
| `TIPO_ESTACION` | `VARCHAR2(20)` | NULL | CK | Clasificación o tipología funcional del registro. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_ESTACION` sobre `(ID_ESTACION)`
- **Unicidad (UK)**: `UK_ESTACION_CODIGO` sobre `(CODIGO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_ESTACION_ACCESIBLE_DIS_40E0` sobre columna `ACCESIBLE_DISCAPACIDAD`: `accesible_discapacidad IN ('N', 'S')`
  - `CK_ESTACION_DISTRITO` sobre columna `DISTRITO`: `distrito IN ('Brooklyn', 'Manhattan', 'Queens', 'Staten Island', 'The Bronx')`
  - `CK_ESTACION_ELEVADORES_DI_9827` sobre columna `ELEVADORES_DISPONIBLES`: `elevadores_disponibles IN ('N', 'S')`
  - `CK_ESTACION_ESCALERAS_ELE_3BDE` sobre columna `ESCALERAS_ELECTRICAS_DISPONIBLES`: `escaleras_electricas_disponibles IN ('N', 'S')`
  - `CK_ESTACION_ESTADO_OPERATIVO` sobre columna `ESTADO_OPERATIVO`: `estado_operativo IN ('Cerrada', 'Cerrada Temporalmente', 'Operativa')`
  - `CK_ESTACION_TIPO_ESTACION` sobre columna `TIPO_ESTACION`: `tipo_estacion IN ('Cerrada Temporalmente', 'Expresa', 'Local', 'Terminal', 'Transferencia')`

---

### <a id="estacion_servicio"></a> ESTACION_SERVICIO
**Descripción Funcional**: Entidad asociativa que registra la disponibilidad de servicios al usuario en cada estación (baños públicos, puestos de primeros auxilios, Wi-Fi subterráneo, custodia policial NYPD Transit).

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_ESTACION_SERVICIO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `ESTACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION`, **UK** | Llave foránea que referencia a la tabla ESTACION. |
| `TIPO_SERVICIO` | `VARCHAR2(40)` | NULL | **UK**, CK | Clasificación o tipología funcional del registro. |
| `DISPONIBLE` | `CHAR(1)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_ESTACION_SERVICIO` sobre `(ID_ESTACION_SERVICIO)`
- **Unicidad (UK)**: `UK_ESTACION_SERVICIO_1` sobre `(ESTACION_ID, TIPO_SERVICIO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_ESTACION_SERVICIO_ESTA_DEE3`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_ESTACION_SERVICIO_DISP_9CAD` sobre columna `DISPONIBLE`: `disponible IN ('N', 'S')`
  - `CK_ESTACION_SERVICIO_TIPO_D3A9` sobre columna `TIPO_SERVICIO`: `tipo_servicio IN ('Acceso Bicicletas', 'Atención al Pasajero', 'Conexión Autobuses', 'Conexión Trenes Regionales', 'Máquinas Expendedoras', 'Policía/Seguridad', 'Servicios Sanitarios', 'Venta/Recarga Tarjetas')`

---

### <a id="horario"></a> HORARIO
**Descripción Funcional**: Plan maestro de frecuencias y ventanas de operación para los días de semana (Weekday), sábados (Saturday) y domingos/feriados (Sunday/Holiday).

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_HORARIO` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `RUTA_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `RUTA.ID_RUTA` | Llave foránea que referencia a la tabla RUTA. |
| `DIA_SEMANA` | `VARCHAR2(20)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `HORA_INICIO` | `DATE` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `HORA_FIN` | `DATE` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `FRECUENCIA_MINUTOS` | `NUMBER(4)` | NULL | — | Intervalo temporal expresado en minutos. |
| `TIPO_SERVICIO` | `VARCHAR2(20)` | NULL | — | Clasificación o tipología funcional del registro. |
| `FECHA_VIGENCIA_DESDE` | `DATE` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_VIGENCIA_HASTA` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_HORARIO` sobre `(ID_HORARIO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_HORARIO_RUTA_ID`: Columna `(RUTA_ID)` &rarr; Referencia `RUTA(ID_RUTA)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_HORARIO_DIA_SEMANA` sobre columna `DIA_SEMANA`: `dia_semana IN ('Domingo', 'Festivo', 'Fin de Semana', 'Jueves', 'Lunes', 'Lunes a Viernes', 'Martes', 'Miercoles', 'Sabado', 'Viernes')`

---

### <a id="horario_estacion"></a> HORARIO_ESTACION
**Descripción Funcional**: Horarios oficiales de apertura y cierre de accesos de cada estación para cada día de la semana.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_HORARIO_ESTACION` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `ESTACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION`, **UK** | Llave foránea que referencia a la tabla ESTACION. |
| `TIPO_DIA` | `VARCHAR2(20)` | **NOT NULL** | **UK**, CK | Clasificación o tipología funcional del registro. |
| `HORA_APERTURA` | `VARCHAR2(5)` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `HORA_CIERRE` | `VARCHAR2(5)` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `ES_24_HORAS` | `CHAR(1)` | NULL | CK | Hora de ejecución, llegada, salida o programación. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_HORARIO_ESTACION` sobre `(ID_HORARIO_ESTACION)`
- **Unicidad (UK)**: `UK_HORARIO_ESTACION_1` sobre `(ESTACION_ID, TIPO_DIA)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_HORARIO_ESTACION_ESTACION_ID`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_HORARIO_EST_ESTADO` sobre columna `ESTADO`: `estado IN ('Suspendido', 'Vigente')`
  - `CK_HORARIO_EST_TIPO_DIA` sobre columna `TIPO_DIA`: `tipo_dia IN ('Domingo', 'Festivo', 'Lunes a Viernes', 'Sabado', 'Todos los Dias')`
  - `CK_HORARIO_EST_24H` sobre columna `ES_24_HORAS`: `es_24_horas IN ('N', 'S')`

---

### <a id="incidente"></a> INCIDENTE
**Descripción Funcional**: Control y despacho de contingencias operativas en la red (fallas de señal CBTC, emergencias médicas, intrusión en vía, inundaciones) con nivel de severidad, estado y reporte cronológico.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_INCIDENTE` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_INCIDENTE` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `TIPO` | `VARCHAR2(30)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `DESCRIPCION` | `VARCHAR2(500)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FECHA_HORA_INICIO` | `TIMESTAMP(6)` | **NOT NULL** | CK | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_HORA_FIN` | `TIMESTAMP(6)` | NULL | CK | Fecha y/o marca temporal del evento o vigencia. |
| `NIVEL_SEVERIDAD` | `VARCHAR2(10)` | NULL | CK | Nivel de criticidad del evento (Bajo, Medio, Alto, Crítico). |
| `REPORTADO_POR_ID` | `NUMBER(8)` | NULL | FK &rarr; `EMPLEADO.ID_EMPLEADO` | Llave foránea que referencia a la tabla REPORTADO_POR. |
| `ESTADO` | `VARCHAR2(15)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `CAUSA_IDENTIFICADA` | `VARCHAR2(300)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ACCIONES_REALIZADAS` | `VARCHAR2(500)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `PASAJEROS_AFECTADOS_ESTIMADO` | `NUMBER(8)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_INCIDENTE` sobre `(ID_INCIDENTE)`
- **Unicidad (UK)**: `UK_INCIDENTE_NUMERO_INCIDENTE` sobre `(NUMERO_INCIDENTE)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_INCIDENTE_REPORTADO_POR_ID`: Columna `(REPORTADO_POR_ID)` &rarr; Referencia `EMPLEADO(ID_EMPLEADO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_INCIDENTE_ESTADO` sobre columna `ESTADO`: `estado IN ('Abierto', 'Cerrado', 'En Atención')`
  - `CK_INCIDENTE_FECHA_HORA_FIN` sobre columna `FECHA_HORA_FIN, FECHA_HORA_INICIO`: `fecha_hora_fin >= fecha_hora_inicio`
  - `CK_INCIDENTE_NIVEL_SEVERIDAD` sobre columna `NIVEL_SEVERIDAD`: `nivel_severidad IN ('Alto', 'Bajo', 'Crítico', 'Medio')`
  - `CK_INCIDENTE_TIPO` sobre columna `TIPO`: `tipo IN ('Accidente', 'Congestión', 'Emergencia Médica', 'Falla Eléctrica', 'Falla Mecánica', 'Falla de Señalización', 'Incendio', 'Inundación', 'Mantenimiento no Programado', 'Objeto en la Vía', 'Problema de Seguridad')`

---

### <a id="incidente_elemento_afectado"></a> INCIDENTE_ELEMENTO_AFECTADO
**Descripción Funcional**: Entidad asociativa que relaciona cada incidente con el activo específico afectado (estación, tramo de vía, tren o ruta completa) y detalla la medida de contingencia aplicada.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_INCIDENTE_ELEMENTO` | `NUMBER(12)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `INCIDENTE_ID` | `NUMBER(10)` | **NOT NULL** | FK &rarr; `INCIDENTE.ID_INCIDENTE` | Llave foránea que referencia a la tabla INCIDENTE. |
| `TIPO_ELEMENTO` | `VARCHAR2(20)` | **NOT NULL** | CK | Clasificación o tipología funcional del registro. |
| `ESTACION_ID` | `NUMBER(8)` | NULL | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION. |
| `TREN_ID` | `NUMBER(8)` | NULL | FK &rarr; `TREN.ID_TREN` | Llave foránea que referencia a la tabla TREN. |
| `RUTA_ID` | `NUMBER(8)` | NULL | FK &rarr; `RUTA.ID_RUTA` | Llave foránea que referencia a la tabla RUTA. |
| `EQUIPO_ID` | `NUMBER(10)` | NULL | FK &rarr; `EQUIPO.ID_EQUIPO` | Llave foránea que referencia a la tabla EQUIPO. |
| `VIAJE_ID` | `NUMBER(10)` | NULL | FK &rarr; `VIAJE_PROGRAMADO.ID_VIAJE` | Llave foránea que referencia a la tabla VIAJE. |
| `LINEA_ID` | `NUMBER(6)` | NULL | FK &rarr; `LINEA.ID_LINEA` | Llave foránea que referencia a la tabla LINEA. |
| `TIPO_AFECTACION` | `VARCHAR2(30)` | NULL | CK | Clasificación o tipología funcional del registro. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_INCIDENTE_ELEMENTO_AFECTADO` sobre `(ID_INCIDENTE_ELEMENTO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_INC_ELEM_EQUIPO_ID`: Columna `(EQUIPO_ID)` &rarr; Referencia `EQUIPO(ID_EQUIPO)`
  - `FK_INC_ELEM_ESTACION_ID`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_INC_ELEM_LINEA_ID`: Columna `(LINEA_ID)` &rarr; Referencia `LINEA(ID_LINEA)`
  - `FK_INC_ELEM_RUTA_ID`: Columna `(RUTA_ID)` &rarr; Referencia `RUTA(ID_RUTA)`
  - `FK_INC_ELEM_TREN_ID`: Columna `(TREN_ID)` &rarr; Referencia `TREN(ID_TREN)`
  - `FK_INC_ELEM_VIAJE_ID`: Columna `(VIAJE_ID)` &rarr; Referencia `VIAJE_PROGRAMADO(ID_VIAJE)`
  - `FK_INCIDENTE_ELEMENTO_AFE_53BA`: Columna `(INCIDENTE_ID)` &rarr; Referencia `INCIDENTE(ID_INCIDENTE)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_INCIDENTE_ELEMENTO_AFE_8B3B` sobre columna `TIPO_AFECTACION`: `tipo_afectacion IN ('Cambio de Ruta', 'Cancelación', 'Cierre de Estación', 'Cierre de Plataforma', 'Retiro de Tren', 'Retraso', 'Suspensión de Tramo')`
  - `CK_INCIDENTE_ELEMENTO_TIPO` sobre columna `TIPO_ELEMENTO`: `tipo_elemento IN ('EQUIPO', 'ESTACION', 'LINEA', 'RUTA', 'TREN', 'VIAJE_PROGRAMADO')`

---

### <a id="linea"></a> LINEA
**Descripción Funcional**: Líneas troncales comerciales del sistema de metro (ej. Línea A - 8th Avenue Express, Línea 7 - Flushing Local/Express), color identificador MTA, división técnica (A o B) y terminales.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_LINEA` | `NUMBER(6)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO` | `VARCHAR2(10)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NOMBRE` | `VARCHAR2(100)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `COLOR` | `VARCHAR2(20)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTACION_ORIGEN_ID` | `NUMBER(8)` | NULL | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION_ORIGEN. |
| `ESTACION_DESTINO_ID` | `NUMBER(8)` | NULL | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION_DESTINO. |
| `ESTADO_OPERATIVO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `TIPO_SERVICIO_PRINCIPAL` | `VARCHAR2(20)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `FECHA_INAUGURACION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `LONGITUD_KM` | `NUMBER(6,2)` | NULL | — | Coordenada geográfica WGS84 para georreferenciación. |
| `OPERADOR_RESPONSABLE` | `VARCHAR2(100)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_LINEA` sobre `(ID_LINEA)`
- **Unicidad (UK)**: `UK_LINEA_CODIGO` sobre `(CODIGO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_LINEA_ESTACION_DESTINO_ID`: Columna `(ESTACION_DESTINO_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_LINEA_ESTACION_ORIGEN_ID`: Columna `(ESTACION_ORIGEN_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_LINEA_ESTADO_OPERATIVO` sobre columna `ESTADO_OPERATIVO`: `estado_operativo IN ('Activa', 'Fuera de Servicio', 'Suspendida')`
  - `CK_LINEA_TIPO_SERVICIO_PR_99EB` sobre columna `TIPO_SERVICIO_PRINCIPAL`: `tipo_servicio_principal IN ('Especial', 'Expreso', 'Local', 'Nocturno', 'Temporal')`

---

### <a id="linea_estacion"></a> LINEA_ESTACION
**Descripción Funcional**: Entidad asociativa que define la topología de la red: el orden secuencial en que una línea recorre sus estaciones, con distancias kilométricas y tiempos estimados de enlace.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_LINEA_ESTACION` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `LINEA_ID` | `NUMBER(6)` | **NOT NULL** | FK &rarr; `LINEA.ID_LINEA`, **UK** | Llave foránea que referencia a la tabla LINEA. |
| `ESTACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION`, **UK** | Llave foránea que referencia a la tabla ESTACION. |
| `ORDEN` | `NUMBER(3)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `DISTANCIA_KM` | `NUMBER(6,2)` | NULL | — | Distancia o recorrido acumulado medido en kilómetros. |
| `TIEMPO_ESTIMADO_MIN` | `NUMBER(5)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_LINEA_ESTACION` sobre `(ID_LINEA_ESTACION)`
- **Unicidad (UK)**: `UK_LINEA_ESTACION_1` sobre `(LINEA_ID, ESTACION_ID)`
- **Unicidad (UK)**: `UK_LINEA_ESTACION_2` sobre `(LINEA_ID, ORDEN)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_LINEA_ESTACION_ESTACION_ID`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_LINEA_ESTACION_LINEA_ID`: Columna `(LINEA_ID)` &rarr; Referencia `LINEA(ID_LINEA)`

---

### <a id="modelo_tren"></a> MODELO_TREN
**Descripción Funcional**: Catálogo técnico de material rodante (ej. R142, R160, R188, R211). Define gálibo estructural (División A estrecho vs División B ancho), fabricante, tipo de propulsión y velocidad máxima de diseño.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_MODELO` | `NUMBER(4)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NOMBRE_MODELO` | `VARCHAR2(50)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FABRICANTE` | `VARCHAR2(60)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_MODELO_TREN` sobre `(ID_MODELO)`
- **Unicidad (UK)**: `UK_MODELO_TREN_NOMBRE_MODELO` sobre `(NOMBRE_MODELO)`

---

### <a id="orden_mantenimiento"></a> ORDEN_MANTENIMIENTO
**Descripción Funcional**: Órdenes de servicio técnico preventivo, correctivo o predictivo aplicadas a trenes, vagones o equipos de estación, con prioridad, horas invertidas y estado de ejecución.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_ORDEN` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_ORDEN` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `EQUIPO_ID` | `NUMBER(10)` | **NOT NULL** | FK &rarr; `EQUIPO.ID_EQUIPO` | Llave foránea que referencia a la tabla EQUIPO. |
| `TIPO_MANTENIMIENTO` | `VARCHAR2(40)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `DESCRIPCION_TRABAJO` | `VARCHAR2(500)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FECHA_SOLICITUD` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_PROGRAMADA` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_INICIO` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_FINALIZACION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `PRIORIDAD` | `VARCHAR2(10)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `COSTO` | `NUMBER(10,2)` | NULL | — | Monto monetario expresado en dólares estadounidenses ($ USD). |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_ORDEN_MANTENIMIENTO` sobre `(ID_ORDEN)`
- **Unicidad (UK)**: `UK_ORDEN_MANTENIMIENTO_NU_422C` sobre `(NUMERO_ORDEN)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_ORDEN_MANTENIMIENTO_EQ_95B5`: Columna `(EQUIPO_ID)` &rarr; Referencia `EQUIPO(ID_EQUIPO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_ORDEN_MANTENIMIENTO_ESTADO` sobre columna `ESTADO`: `estado IN ('Cancelada', 'Completada', 'En Ejecución', 'Programada', 'Solicitada', 'Suspendida')`
  - `CK_ORDEN_MANTENIMIENTO_PR_F06F` sobre columna `PRIORIDAD`: `prioridad IN ('Alta', 'Baja', 'Media', 'Urgente')`
  - `CK_ORDEN_MANTENIMIENTO_TI_3D5F` sobre columna `TIPO_MANTENIMIENTO`: `tipo_mantenimiento IN ('Correctivo', 'Inspección de Seguridad', 'Predictivo', 'Preventivo')`

---

### <a id="orden_repuesto"></a> ORDEN_REPUESTO
**Descripción Funcional**: Entidad asociativa que contabiliza los componentes y repuestos mecánicos o electrónicos consumidos en una orden de mantenimiento, con sus cantidades y costos unitarios.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_ORDEN_REPUESTO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `ORDEN_ID` | `NUMBER(10)` | **NOT NULL** | FK &rarr; `ORDEN_MANTENIMIENTO.ID_ORDEN` | Llave foránea que referencia a la tabla ORDEN. |
| `REPUESTO_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `REPUESTO.ID_REPUESTO` | Llave foránea que referencia a la tabla REPUESTO. |
| `CANTIDAD` | `NUMBER(6)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `COSTO_TOTAL` | `NUMBER(10,2)` | NULL | — | Monto monetario expresado en dólares estadounidenses ($ USD). |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_ORDEN_REPUESTO` sobre `(ID_ORDEN_REPUESTO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_ORDEN_REPUESTO_ORDEN_ID`: Columna `(ORDEN_ID)` &rarr; Referencia `ORDEN_MANTENIMIENTO(ID_ORDEN)`
  - `FK_ORDEN_REPUESTO_REPUESTO_ID`: Columna `(REPUESTO_ID)` &rarr; Referencia `REPUESTO(ID_REPUESTO)`

---

### <a id="orden_tecnico"></a> ORDEN_TECNICO
**Descripción Funcional**: Entidad asociativa que asigna el personal técnico calificado a una orden de mantenimiento, registrando horas hombre trabajadas y rol de intervención.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_ORDEN_TECNICO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `ORDEN_ID` | `NUMBER(10)` | **NOT NULL** | FK &rarr; `ORDEN_MANTENIMIENTO.ID_ORDEN`, **UK** | Llave foránea que referencia a la tabla ORDEN. |
| `EMPLEADO_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `EMPLEADO.ID_EMPLEADO`, **UK** | Llave foránea que referencia a la tabla EMPLEADO. |
| `ROL_EN_ORDEN` | `VARCHAR2(40)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_ORDEN_TECNICO` sobre `(ID_ORDEN_TECNICO)`
- **Unicidad (UK)**: `UK_ORDEN_TECNICO_1` sobre `(ORDEN_ID, EMPLEADO_ID)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_ORDEN_TECNICO_EMPLEADO_ID`: Columna `(EMPLEADO_ID)` &rarr; Referencia `EMPLEADO(ID_EMPLEADO)`
  - `FK_ORDEN_TECNICO_ORDEN_ID`: Columna `(ORDEN_ID)` &rarr; Referencia `ORDEN_MANTENIMIENTO(ID_ORDEN)`

---

### <a id="pasajero"></a> PASAJERO
**Descripción Funcional**: Padrón de usuarios del sistema de metro. Registra datos personales atómicos, categoría de usuario (Regular, Estudiante, Adulto Mayor, Discapacidad) para la aplicación de descuentos.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_PASAJERO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `IDENTIFICADOR` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NOMBRE` | `VARCHAR2(150)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FECHA_NACIMIENTO` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `CORREO_ELECTRONICO` | `VARCHAR2(100)` | NULL | — | Dirección de correo electrónico oficial de contacto. |
| `TELEFONO` | `VARCHAR2(20)` | NULL | — | Número de teléfono de contacto institucional. |
| `TIPO_PASAJERO` | `VARCHAR2(25)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `FECHA_REGISTRO` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `ESTADO` | `VARCHAR2(15)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_PASAJERO` sobre `(ID_PASAJERO)`
- **Unicidad (UK)**: `UK_PASAJERO_IDENTIFICADOR` sobre `(IDENTIFICADOR)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_PASAJERO_ESTADO` sobre columna `ESTADO`: `estado IN ('Activo', 'Inactivo')`
  - `CK_PASAJERO_TIPO_PASAJERO` sobre columna `TIPO_PASAJERO`: `tipo_pasajero IN ('Adulto Mayor', 'Empleado Autorizado', 'Estudiante', 'Persona con Discapacidad', 'Regular')`

---

### <a id="plataforma"></a> PLATAFORMA
**Descripción Funcional**: Andenes físicos de embarque dentro de las estaciones, especificando sentido de circulación (Uptown / Downtown / Manhattan-bound), tipo de andén y estado operativo.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_PLATAFORMA` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `ESTACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION. |
| `IDENTIFICADOR` | `VARCHAR2(20)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `DIRECCION_VIAJE` | `VARCHAR2(30)` | NULL | — | Dirección física o calle de ubicación del activo. |
| `CAPACIDAD_APROXIMADA` | `NUMBER(6)` | NULL | — | Capacidad máxima de diseño (pasajeros o unidades). |
| `ESTADO_OPERATIVO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_PLATAFORMA` sobre `(ID_PLATAFORMA)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_PLATAFORMA_ESTACION_ID`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_PLATAFORMA_ESTADO_OPERATIVO` sobre columna `ESTADO_OPERATIVO`: `estado_operativo IN ('Fuera de Servicio', 'Mantenimiento', 'Operativa')`

---

### <a id="recarga"></a> RECARGA
**Descripción Funcional**: Transacciones financieras de acreditación de saldo en tarjetas OMNY mediante medios de pago aprobados (efectivo, tarjeta bancaria, pago móvil), registrando saldos previo y posterior.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_RECARGA` | `NUMBER(12)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_TRANSACCION` | `VARCHAR2(25)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `TARJETA_ID` | `NUMBER(10)` | **NOT NULL** | FK &rarr; `TARJETA.ID_TARJETA` | Llave foránea que referencia a la tabla TARJETA. |
| `FECHA_HORA` | `TIMESTAMP(6)` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `MONTO` | `NUMBER(8,2)` | **NOT NULL** | — | Monto monetario expresado en dólares estadounidenses ($ USD). |
| `MEDIO_PAGO` | `VARCHAR2(20)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTACION_CANAL` | `VARCHAR2(50)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `SALDO_ANTERIOR` | `NUMBER(8,2)` | NULL | — | Monto monetario expresado en dólares estadounidenses ($ USD). |
| `SALDO_POSTERIOR` | `NUMBER(8,2)` | NULL | — | Monto monetario expresado en dólares estadounidenses ($ USD). |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_RECARGA` sobre `(ID_RECARGA)`
- **Unicidad (UK)**: `UK_RECARGA_NUMERO_TRANSACCION` sobre `(NUMERO_TRANSACCION)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_RECARGA_TARJETA_ID`: Columna `(TARJETA_ID)` &rarr; Referencia `TARJETA(ID_TARJETA)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_RECARGA_MEDIO_PAGO` sobre columna `MEDIO_PAGO`: `medio_pago IN ('App Móvil', 'Efectivo', 'Tarjeta Crédito', 'Tarjeta Débito', 'Transferencia')`

---

### <a id="repuesto"></a> REPUESTO
**Descripción Funcional**: Catálogo de repuestos e insumos ferroviarios (zapatas de freno, pastillas de contacto de tercer riel, bombas de aire, módulos lógicos CBTC), stock y costo unitario.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_REPUESTO` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NOMBRE` | `VARCHAR2(100)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `COSTO_UNITARIO` | `NUMBER(8,2)` | NULL | — | Monto monetario expresado en dólares estadounidenses ($ USD). |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_REPUESTO` sobre `(ID_REPUESTO)`
- **Unicidad (UK)**: `UK_REPUESTO_CODIGO` sobre `(CODIGO)`

---

### <a id="ruta"></a> RUTA
**Descripción Funcional**: Variantes de servicio de una línea (ej. A Express vía Fulton St, A Local nocturno) con sentido, terminales y tipo de servicio (Local, Expreso, Nocturno).

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_RUTA` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO` | `VARCHAR2(15)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `LINEA_ID` | `NUMBER(6)` | **NOT NULL** | FK &rarr; `LINEA.ID_LINEA` | Llave foránea que referencia a la tabla LINEA. |
| `ESTACION_ORIGEN_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION_ORIGEN. |
| `ESTACION_DESTINO_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION_DESTINO. |
| `SENTIDO` | `VARCHAR2(20)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `TIPO_SERVICIO` | `VARCHAR2(20)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `DISTANCIA_TOTAL_KM` | `NUMBER(6,2)` | NULL | — | Distancia o recorrido acumulado medido en kilómetros. |
| `DURACION_ESTIMADA_MIN` | `NUMBER(5)` | NULL | — | Intervalo temporal expresado en minutos. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `FECHA_VIGENCIA_DESDE` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_VIGENCIA_HASTA` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_RUTA` sobre `(ID_RUTA)`
- **Unicidad (UK)**: `UK_RUTA_CODIGO` sobre `(CODIGO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_RUTA_ESTACION_DESTINO_ID`: Columna `(ESTACION_DESTINO_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_RUTA_ESTACION_ORIGEN_ID`: Columna `(ESTACION_ORIGEN_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_RUTA_LINEA_ID`: Columna `(LINEA_ID)` &rarr; Referencia `LINEA(ID_LINEA)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_RUTA_ESTADO` sobre columna `ESTADO`: `estado IN ('Activa', 'Cancelada', 'Cerrada Temporalmente')`
  - `CK_RUTA_TIPO_SERVICIO` sobre columna `TIPO_SERVICIO`: `tipo_servicio IN ('Especial', 'Expreso', 'Local', 'Nocturno', 'Temporal')`

---

### <a id="ruta_detalle"></a> RUTA_DETALLE
**Descripción Funcional**: Secuencia pormenorizada de paradas para una ruta específica, señalando explícitamente si el tren se detiene para ascenso/descenso de pasajeros o pasa de largo sin parada (servicio exprés).

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_RUTA_DETALLE` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `RUTA_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `RUTA.ID_RUTA`, **UK** | Llave foránea que referencia a la tabla RUTA. |
| `ESTACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION`, **UK** | Llave foránea que referencia a la tabla ESTACION. |
| `ORDEN_LLEGADA` | `NUMBER(3)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `HORA_ESTIMADA_LLEGADA` | `DATE` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `HORA_ESTIMADA_SALIDA` | `DATE` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `DISTANCIA_DESDE_ANTERIOR_KM` | `NUMBER(6,2)` | NULL | — | Distancia o recorrido acumulado medido en kilómetros. |
| `TIEMPO_DESDE_ANTERIOR_MIN` | `NUMBER(5)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `SE_DETIENE` | `CHAR(1)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_RUTA_DETALLE` sobre `(ID_RUTA_DETALLE)`
- **Unicidad (UK)**: `UK_RUTA_DETALLE_1` sobre `(RUTA_ID, ORDEN_LLEGADA)`
- **Unicidad (UK)**: `UK_RUTA_DETALLE_2` sobre `(RUTA_ID, ESTACION_ID)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_RUTA_DETALLE_ESTACION_ID`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_RUTA_DETALLE_RUTA_ID`: Columna `(RUTA_ID)` &rarr; Referencia `RUTA(ID_RUTA)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_RUTA_DETALLE_SE_DETIENE` sobre columna `SE_DETIENE`: `se_detiene IN ('N', 'S')`

---

### <a id="tarifa"></a> TARIFA
**Descripción Funcional**: Estructura tarifaria reglamentaria aprobada por la MTA (Tarifa Base $2.90, Tarifa Reducida $1.45, Boleto Único, Pase Semanal con tope tarifario) con vigencia temporal.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_TARIFA` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO` | `VARCHAR2(15)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `NOMBRE` | `VARCHAR2(60)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `DESCRIPCION` | `VARCHAR2(200)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `MONTO` | `NUMBER(8,2)` | **NOT NULL** | — | Monto monetario expresado en dólares estadounidenses ($ USD). |
| `TIPO_PASAJERO` | `VARCHAR2(25)` | NULL | — | Clasificación o tipología funcional del registro. |
| `FECHA_INICIO_VIGENCIA` | `DATE` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_FIN_VIGENCIA` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `CANTIDAD_MAXIMA_VIAJES` | `NUMBER(4)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `DURACION_BENEFICIO_DIAS` | `NUMBER(5)` | NULL | — | Intervalo temporal expresado en minutos. |
| `ESTADO` | `VARCHAR2(15)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_TARIFA` sobre `(ID_TARIFA)`
- **Unicidad (UK)**: `UK_TARIFA_CODIGO` sobre `(CODIGO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_TARIFA_ESTADO` sobre columna `ESTADO`: `estado IN ('Suspendida', 'Vencida', 'Vigente')`

---

### <a id="tarjeta"></a> TARJETA
**Descripción Funcional**: Cuentas de pago y soportes inteligentes OMNY (tarjetas físicas sin contacto, billeteras móviles, pases institucionales), saldo disponible y estado operativo de validación.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_TARJETA` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_TARJETA` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `PASAJERO_ID` | `NUMBER(10)` | NULL | FK &rarr; `PASAJERO.ID_PASAJERO` | Llave foránea que referencia a la tabla PASAJERO. |
| `FECHA_EMISION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_VENCIMIENTO` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `SALDO_DISPONIBLE` | `NUMBER(8,2)` | NULL | CK | Monto monetario expresado en dólares estadounidenses ($ USD). |
| `TARIFA_ID` | `NUMBER(8)` | NULL | FK &rarr; `TARIFA.ID_TARIFA` | Llave foránea que referencia a la tabla TARIFA. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_TARJETA` sobre `(ID_TARJETA)`
- **Unicidad (UK)**: `UK_TARJETA_NUMERO_TARJETA` sobre `(NUMERO_TARJETA)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_TARJETA_PASAJERO_ID`: Columna `(PASAJERO_ID)` &rarr; Referencia `PASAJERO(ID_PASAJERO)`
  - `FK_TARJETA_TARIFA_ID`: Columna `(TARIFA_ID)` &rarr; Referencia `TARIFA(ID_TARIFA)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_TARJETA_ESTADO` sobre columna `ESTADO`: `estado IN ('Activa', 'Bloqueada', 'Cancelada', 'Reportada Perdida', 'Vencida')`
  - `CK_TARJETA_SALDO_DISPONIBLE` sobre columna `SALDO_DISPONIBLE`: `saldo_disponible >= 0`

---

### <a id="transferencia"></a> TRANSFERENCIA
**Descripción Funcional**: Pasajes y pasillos peatonales subterráneos que permiten el trasbordo gratuito entre diferentes líneas y plataformas dentro de una misma estación o complejo intermodal.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_TRANSFERENCIA` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `ESTACION_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION`, **UK** | Llave foránea que referencia a la tabla ESTACION. |
| `LINEA_ORIGEN_ID` | `NUMBER(6)` | **NOT NULL** | FK &rarr; `LINEA.ID_LINEA`, **UK** | Llave foránea que referencia a la tabla LINEA_ORIGEN. |
| `LINEA_DESTINO_ID` | `NUMBER(6)` | **NOT NULL** | FK &rarr; `LINEA.ID_LINEA`, **UK** | Llave foránea que referencia a la tabla LINEA_DESTINO. |
| `TIEMPO_ESTIMADO_MIN` | `NUMBER(4)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_TRANSFERENCIA` sobre `(ID_TRANSFERENCIA)`
- **Unicidad (UK)**: `UK_TRANSFERENCIA_1` sobre `(ESTACION_ID, LINEA_ORIGEN_ID, LINEA_DESTINO_ID)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_TRANSFERENCIA_ESTACION_ID`: Columna `(ESTACION_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_TRANSFERENCIA_LINEA_DE_3222`: Columna `(LINEA_DESTINO_ID)` &rarr; Referencia `LINEA(ID_LINEA)`
  - `FK_TRANSFERENCIA_LINEA_OR_0F7F`: Columna `(LINEA_ORIGEN_ID)` &rarr; Referencia `LINEA(ID_LINEA)`

---

### <a id="tren"></a> TREN
**Descripción Funcional**: Unidades de tracción y formaciones activas de la flota. Controla kilometraje acumulado, estado operativo en tiempo real (Disponible, En Operación, En Mantenimiento, Fuera de Servicio) y depósito base.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_TREN` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO_INTERNO` | `VARCHAR2(15)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `MODELO_ID` | `NUMBER(4)` | **NOT NULL** | FK &rarr; `MODELO_TREN.ID_MODELO` | Llave foránea que referencia a la tabla MODELO. |
| `ANIO_FABRICACION` | `NUMBER(4)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `CAPACIDAD_TOTAL` | `NUMBER(6)` | NULL | — | Capacidad máxima de diseño (pasajeros o unidades). |
| `ESTADO_OPERATIVO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `KILOMETRAJE_ACUMULADO` | `NUMBER(10,2)` | NULL | — | Distancia o recorrido acumulado medido en kilómetros. |
| `DEPOSITO_ID` | `NUMBER(4)` | NULL | FK &rarr; `DEPOSITO.ID_DEPOSITO` | Llave foránea que referencia a la tabla DEPOSITO. |
| `FECHA_ULTIMA_INSPECCION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_PROXIMA_INSPECCION` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_TREN` sobre `(ID_TREN)`
- **Unicidad (UK)**: `UK_TREN_CODIGO_INTERNO` sobre `(CODIGO_INTERNO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_TREN_DEPOSITO_ID`: Columna `(DEPOSITO_ID)` &rarr; Referencia `DEPOSITO(ID_DEPOSITO)`
  - `FK_TREN_MODELO_ID`: Columna `(MODELO_ID)` &rarr; Referencia `MODELO_TREN(ID_MODELO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_TREN_ESTADO_OPERATIVO` sobre columna `ESTADO_OPERATIVO`: `estado_operativo IN ('Disponible', 'En Mantenimiento', 'En Operación', 'Fuera de Servicio', 'Retirado')`

---

### <a id="tren_vagon"></a> TREN_VAGON
**Descripción Funcional**: Composición física y acoplamiento de coches individuales dentro de un tren específico, indicando el orden secuencial de cada vagón en la formación.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_TREN_VAGON` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `TREN_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `TREN.ID_TREN` | Llave foránea que referencia a la tabla TREN. |
| `VAGON_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `VAGON.ID_VAGON` | Llave foránea que referencia a la tabla VAGON. |
| `POSICION` | `NUMBER(2)` | **NOT NULL** | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `FECHA_INICIO` | `DATE` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `FECHA_FIN` | `DATE` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_TREN_VAGON` sobre `(ID_TREN_VAGON)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_TREN_VAGON_TREN_ID`: Columna `(TREN_ID)` &rarr; Referencia `TREN(ID_TREN)`
  - `FK_TREN_VAGON_VAGON_ID`: Columna `(VAGON_ID)` &rarr; Referencia `VAGON(ID_VAGON)`

---

### <a id="turno"></a> TURNO
**Descripción Funcional**: Asignaciones y horarios de servicio operativo para el personal de conducción, supervisión de andén y despacho de trenes.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_TURNO` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `CODIGO_TURNO` | `VARCHAR2(15)` | **NOT NULL** | **UK** | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `EMPLEADO_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `EMPLEADO.ID_EMPLEADO` | Llave foránea que referencia a la tabla EMPLEADO. |
| `FECHA` | `DATE` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `HORA_INICIO` | `TIMESTAMP(6)` | **NOT NULL** | — | Hora de ejecución, llegada, salida o programación. |
| `HORA_FIN` | `TIMESTAMP(6)` | **NOT NULL** | — | Hora de ejecución, llegada, salida o programación. |
| `TIPO_LUGAR` | `VARCHAR2(20)` | NULL | CK | Clasificación o tipología funcional del registro. |
| `LUGAR_ID` | `NUMBER(10)` | NULL | — | Llave foránea que referencia a la tabla LUGAR. |
| `FUNCION` | `VARCHAR2(50)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTADO_ASISTENCIA` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_TURNO` sobre `(ID_TURNO)`
- **Unicidad (UK)**: `UK_TURNO_CODIGO_TURNO` sobre `(CODIGO_TURNO)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_TURNO_EMPLEADO_ID`: Columna `(EMPLEADO_ID)` &rarr; Referencia `EMPLEADO(ID_EMPLEADO)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_TURNO_ESTADO_ASISTENCIA` sobre columna `ESTADO_ASISTENCIA`: `estado_asistencia IN ('Ausente', 'Permiso', 'Presente', 'Programado', 'Sustituido', 'Vacaciones')`
  - `CK_TURNO_TIPO_LUGAR` sobre columna `TIPO_LUGAR`: `tipo_lugar IN ('Centro de Control', 'Depósito', 'Estación', 'Ruta', 'Tren')`

---

### <a id="vagon"></a> VAGON
**Descripción Funcional**: Coches individuales de pasajeros, clasificados por tipo de coche (cabina motriz 'A' o coche remolque intermedio 'B'), con capacidad de pasajeros sentados/de pie y fabricante.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_VAGON` | `NUMBER(8)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_SERIE` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `TIPO_VAGON` | `VARCHAR2(20)` | NULL | — | Clasificación o tipología funcional del registro. |
| `CAPACIDAD_SENTADOS` | `NUMBER(4)` | NULL | — | Capacidad máxima de diseño (pasajeros o unidades). |
| `CAPACIDAD_DE_PIE` | `NUMBER(4)` | NULL | — | Capacidad máxima de diseño (pasajeros o unidades). |
| `ANIO_FABRICACION` | `NUMBER(4)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `ACCESIBILIDAD` | `CHAR(1)` | NULL | CK | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_VAGON` sobre `(ID_VAGON)`
- **Unicidad (UK)**: `UK_VAGON_NUMERO_SERIE` sobre `(NUMERO_SERIE)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_VAGON_ACCESIBILIDAD` sobre columna `ACCESIBILIDAD`: `accesibilidad IN ('N', 'S')`
  - `CK_VAGON_ESTADO` sobre columna `ESTADO`: `estado IN ('Disponible', 'En Uso', 'Fuera de Servicio', 'Mantenimiento')`

---

### <a id="viaje_pasajero"></a> VIAJE_PASAJERO
**Descripción Funcional**: Registro de transacciones de validación y acceso de pasajeros en los torniquetes OMNY, debitando la tarifa correspondiente en la estación de abordaje.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_VIAJE_PASAJERO` | `NUMBER(14)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_TRANSACCION` | `VARCHAR2(25)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `TARJETA_ID` | `NUMBER(10)` | **NOT NULL** | FK &rarr; `TARJETA.ID_TARJETA` | Llave foránea que referencia a la tabla TARJETA. |
| `ESTACION_INGRESO_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION_INGRESO. |
| `FECHA_HORA_INGRESO` | `TIMESTAMP(6)` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `ESTACION_SALIDA_ID` | `NUMBER(8)` | NULL | FK &rarr; `ESTACION.ID_ESTACION` | Llave foránea que referencia a la tabla ESTACION_SALIDA. |
| `FECHA_HORA_SALIDA` | `TIMESTAMP(6)` | NULL | — | Fecha y/o marca temporal del evento o vigencia. |
| `TARIFA_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `TARIFA.ID_TARIFA` | Llave foránea que referencia a la tabla TARIFA. |
| `MONTO_COBRADO` | `NUMBER(8,2)` | NULL | — | Monto monetario expresado en dólares estadounidenses ($ USD). |
| `VIAJE_PROGRAMADO_ID` | `NUMBER(10)` | NULL | FK &rarr; `VIAJE_PROGRAMADO.ID_VIAJE` | Llave foránea que referencia a la tabla VIAJE_PROGRAMADO. |
| `ESTADO_TRANSACCION` | `VARCHAR2(15)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_VIAJE_PASAJERO` sobre `(ID_VIAJE_PASAJERO)`
- **Unicidad (UK)**: `UK_VIAJE_PASAJERO_NUMERO__D88E` sobre `(NUMERO_TRANSACCION)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_VIAJE_PASAJERO_ESTACIO_3F85`: Columna `(ESTACION_INGRESO_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_VIAJE_PASAJERO_ESTACIO_9F8E`: Columna `(ESTACION_SALIDA_ID)` &rarr; Referencia `ESTACION(ID_ESTACION)`
  - `FK_VIAJE_PASAJERO_TARIFA_ID`: Columna `(TARIFA_ID)` &rarr; Referencia `TARIFA(ID_TARIFA)`
  - `FK_VIAJE_PASAJERO_TARJETA_ID`: Columna `(TARJETA_ID)` &rarr; Referencia `TARJETA(ID_TARJETA)`
  - `FK_VIAJE_PAS_VIAJE_PROG_ID`: Columna `(VIAJE_PROGRAMADO_ID)` &rarr; Referencia `VIAJE_PROGRAMADO(ID_VIAJE)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_VIAJE_PASAJERO_ESTADO__0D11` sobre columna `ESTADO_TRANSACCION`: `estado_transaccion IN ('Abierta', 'Anulada', 'Cerrada')`

---

### <a id="viaje_programado"></a> VIAJE_PROGRAMADO
**Descripción Funcional**: Despachos y corridas programadas de trenes en la red, asignando tren físico, maquinista certificado, ruta, horario de salida proyectado y control de retrasos en tiempo real.

#### Columnas y Atributos
| Columna | Tipo de Dato | Nulidad | Restricción | Descripción y Dominio de Negocio |
| :--- | :--- | :---: | :---: | :--- |
| `ID_VIAJE` | `NUMBER(10)` | **NOT NULL** | **PK** | Identificador único y llave primaria de la entidad. |
| `NUMERO_VIAJE` | `VARCHAR2(20)` | **NOT NULL** | **UK** | Número secuencial, código de serie o folio identificador. |
| `RUTA_ID` | `NUMBER(8)` | **NOT NULL** | FK &rarr; `RUTA.ID_RUTA` | Llave foránea que referencia a la tabla RUTA. |
| `HORARIO_ID` | `NUMBER(8)` | NULL | FK &rarr; `HORARIO.ID_HORARIO` | Llave foránea que referencia a la tabla HORARIO. |
| `FECHA` | `DATE` | **NOT NULL** | — | Fecha y/o marca temporal del evento o vigencia. |
| `HORA_PROG_SALIDA` | `TIMESTAMP(6)` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `HORA_REAL_SALIDA` | `TIMESTAMP(6)` | NULL | CK | Hora de ejecución, llegada, salida o programación. |
| `HORA_PROG_LLEGADA` | `TIMESTAMP(6)` | NULL | — | Hora de ejecución, llegada, salida o programación. |
| `HORA_REAL_LLEGADA` | `TIMESTAMP(6)` | NULL | CK | Hora de ejecución, llegada, salida o programación. |
| `TREN_ID` | `NUMBER(8)` | NULL | FK &rarr; `TREN.ID_TREN` | Llave foránea que referencia a la tabla TREN. |
| `CONDUCTOR_ID` | `NUMBER(8)` | NULL | FK &rarr; `EMPLEADO.ID_EMPLEADO` | Llave foránea que referencia a la tabla CONDUCTOR. |
| `ESTADO` | `VARCHAR2(20)` | NULL | CK | Estado operativo o administrativo regulado por restricción CHECK. |
| `CANTIDAD_ESTIMADA_PASAJEROS` | `NUMBER(6)` | NULL | — | Atributo descriptivo de la entidad dentro de las operaciones de MTA. |

#### Restricciones de Integridad y Reglas Semánticas
- **Llave Primaria**: `PK_VIAJE_PROGRAMADO` sobre `(ID_VIAJE)`
- **Unicidad (UK)**: `UK_VIAJE_PROGRAMADO_NUMER_C5CD` sobre `(NUMERO_VIAJE)`
- **Llaves Foráneas (Integridad Referencial)**:
  - `FK_VIAJE_PROGRAMADO_CONDU_9753`: Columna `(CONDUCTOR_ID)` &rarr; Referencia `EMPLEADO(ID_EMPLEADO)`
  - `FK_VIAJE_PROGRAMADO_HORARIO_ID`: Columna `(HORARIO_ID)` &rarr; Referencia `HORARIO(ID_HORARIO)`
  - `FK_VIAJE_PROGRAMADO_RUTA_ID`: Columna `(RUTA_ID)` &rarr; Referencia `RUTA(ID_RUTA)`
  - `FK_VIAJE_PROGRAMADO_TREN_ID`: Columna `(TREN_ID)` &rarr; Referencia `TREN(ID_TREN)`
- **Restricciones CHECK (Reglas de Negocio)**:
  - `CK_VIAJE_PROGRAMADO_ESTADO` sobre columna `ESTADO`: `estado IN ('Cancelado', 'Completado', 'En Abordaje', 'En Curso', 'Programado', 'Retrasado')`
  - `CK_VIAJE_PROGRAMADO_HORA__C368` sobre columna `HORA_REAL_LLEGADA, HORA_REAL_SALIDA`: `hora_real_llegada >= hora_real_salida`

---

