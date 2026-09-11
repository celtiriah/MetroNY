# Modelo Entidad-Relación y Transformación Relacional
## Sistema de Gestión de la Red de Metro de Nueva York (MTA NYCT)

> **Entregables Oficiales No. 2, 3 y 5**: Identificación de entidades, atributos, dominios, relaciones, cardinalidades en notación Barker CDM / Oracle Data Modeler, diagramas conceptuales por subsistemas y mapeo formal al esquema relacional de Oracle.

---

## 1. Clasificación Tipológica de Entidades

El modelo de datos del Metro de Nueva York fue concebido para administrar de manera integral tanto la infraestructura física fija (vías, estaciones, plataformas) como la flota móvil, el tráfico comercial en tiempo real, el billetaje contactless OMNY, el personal técnico y los incidentes 24/7.

Las **33 entidades** se clasifican formalmente en cuatro categorías ontológicas:

```mermaid
pie title Distribución Tipológica de Entidades en MetroNY
    "Entidades Fuertes (Maestras)" : 9
    "Entidades Débiles (Existenciales)" : 13
    "Entidades Asociativas (N:M)" : 10
    "Entidades de Auditoría" : 1
```

### 1.1 Entidades Fuertes (Maestras Independientes)
Poseen existencia autónoma en el dominio del negocio; no dependen de la existencia previa de otra entidad para subsistir:
1. `LINEA`: Define las arterias troncales del metro de Nueva York (A, 1, 7, L, etc.).
2. `ESTACION`: Complejos de abordaje y transferencia en los cinco distritos (boroughs).
3. `MODELO_TREN`: Especificaciones de ingeniería rodante (R142, R160, R211, etc.).
4. `DEPOSITO`: Patios y yardas maestras de maniobras y pernocte de material rodante.
5. `EMPLEADO`: Recursos humanos contratados por MTA NYCT.
6. `PASAJERO`: Usuarios registrados en el sistema de transporte metropolitano.
7. `REPUESTO`: Catálogo de inventario de piezas mecánicas y electrónicas de repuesto.
8. `TARIFA`: Parámetros regulatorios y montos oficiales del pasaje ($2.90 base, $1.45 reducida).
9. `TURNO`: Horarios reglamentarios de jornada laboral del personal operativo.

### 1.2 Entidades Débiles (Dependientes por Existencia)
Su existencia está condicionada a la ocurrencia de una entidad padre:
1. `PLATAFORMA`: Depende existencialmente de una `ESTACION` (`ON DELETE CASCADE`).
2. `EQUIPO`: Maquinaria electromecánica (elevadores, escaleras, torniquetes) ligada a una `ESTACION`.
3. `VAGON`: Coche individual dependiente de las especificaciones de su fabricante.
4. `TREN`: Convoy operativo acoplado dependiente de su `MODELO_TREN` y asignado a un `DEPOSITO`.
5. `RUTA`: Recorrido comercial dependiente de una `LINEA` de metro.
6. `HORARIO`: Ventana de servicio asociada a una `RUTA`.
7. `VIAJE_PROGRAMADO`: Despacho de circulación dependiente de una `RUTA` y un `TREN`.
8. `TARJETA`: Medio de pago OMNY emitido a nombre de un `PASAJERO`.
9. `RECARGA`: Transacción de abono dependiente de una `TARJETA`.
10. `VIAJE_PASAJERO`: Registro de acceso por torniquete dependiente de una `TARJETA` y una `TARIFA`.
11. `INCIDENTE`: Evento anómalo en la red reportado por un `EMPLEADO`.
12. `ORDEN_MANTENIMIENTO`: Intervención de taller programada para un `TREN` o `EQUIPO`.
13. `CERTIFICACION`: Habilitación técnica emitida a favor de un `EMPLEADO`.

### 1.3 Entidades Asociativas (Resolución de Relaciones Muchos a Muchos $N:M$)
Permiten romper relaciones complejas $N:M$ convirtiéndolas en dos relaciones $1:N$, agregando atributos de intersección:
1. `LINEA_ESTACION`: Intersección entre `LINEA` y `ESTACION`. Agrega el orden topológico, distancia en km y tiempo estimado de enlace.
2. `TRANSFERENCIA`: Conexión peatonal interna entre dos estaciones o plataformas de diferentes líneas. Agrega el tiempo promedio de caminata y accesibilidad.
3. `ESTACION_SERVICIO`: Intersección entre `ESTACION` y el catálogo de servicios complementarios (baños, Wi-Fi, policía).
4. `HORARIO_ESTACION`: Mapeo de días de la semana y horas de apertura/cierre de accesos por estación.
5. `RUTA_DETALLE`: Secuencia pormenorizada de paradas para una `RUTA`, indicando si el tren se detiene o pasa sin parada (expreso).
6. `TREN_VAGON`: Asignación y acople físico de vagones dentro de un `TREN`, especificando su orden posicional (coche cabina, remolque intermedio).
7. `CERTIFICACION_MODELO`: Certificación de un maquinista u operario respecto a los modelos de tren autorizados para conducir.
8. `ORDEN_REPUESTO`: Repuestos consumidos en una orden de mantenimiento con cantidad y costo histórico unitario.
9. `ORDEN_TECNICO`: Técnicos asignados a una orden de mantenimiento con horas hombre y rol asignado.
10. `INCIDENTE_ELEMENTO_AFECTADO`: Activos de la red afectados por una contingencia (estación, tren, tramo de vía) y tipo de afectación.

### 1.4 Entidad de Auditoría Transversal
1. `BITACORA`: Almacena el historial de eventos críticos de seguridad y cambios de estado operativo mediante triggers de base de datos (`TRG_*`).

---

## 2. Diagramas Entidad-Relación por Subsistemas Funcionales (Mermaid)

Para garantizar una lectura limpia y comprensible del modelo conceptual, se dividió el esquema en seis diagramas modulares de dominio:

### 2.1 Subsistema 1: Infraestructura Ferroviaria y Complejos de Estación

```mermaid
erDiagram
    LINEA ||--o{ LINEA_ESTACION : "recorre"
    ESTACION ||--o{ LINEA_ESTACION : "es recorrida por"
    ESTACION ||--o{ PLATAFORMA : "contiene"
    ESTACION ||--o{ EQUIPO : "alberga"
    ESTACION ||--o{ ESTACION_SERVICIO : "brinda"
    ESTACION ||--o{ HORARIO_ESTACION : "opera en"
    ESTACION ||--o{ TRANSFERENCIA : "origen conexion"
    ESTACION ||--o{ TRANSFERENCIA : "destino conexion"

    LINEA {
        number id_linea PK
        varchar codigo UK
        varchar nombre
        varchar color_hex
        varchar division
        varchar estado_operativo
    }

    ESTACION {
        number id_estacion PK
        varchar codigo UK
        varchar nombre
        varchar borough
        varchar direccion
        number latitud
        number longitud
        varchar accesibilidad_ada
        varchar estado_operativo
    }

    PLATAFORMA {
        number id_plataforma PK
        number estacion_id FK
        varchar numero_plataforma
        varchar sentido
        varchar tipo_plataforma
    }

    LINEA_ESTACION {
        number id_linea_estacion PK
        number linea_id FK
        number estacion_id FK
        number orden_estacion
        number distancia_km_anterior
        number tiempo_minutos_anterior
    }

    TRANSFERENCIA {
        number id_transferencia PK
        number estacion_origen_id FK
        number estacion_destino_id FK
        number tiempo_caminata_minutos
        varchar accesible_silla_ruedas
    }
```

### 2.2 Subsistema 2: Rutas Comerciales, Frecuencias y Programación de Viajes

```mermaid
erDiagram
    LINEA ||--o{ RUTA : "define variantes en"
    RUTA ||--o{ RUTA_DETALLE : "compuesta por"
    ESTACION ||--o{ RUTA_DETALLE : "parada en"
    RUTA ||--o{ HORARIO : "programada con"
    RUTA ||--o{ VIAJE_PROGRAMADO : "ejecuta recorridos de"
    TREN ||--o{ VIAJE_PROGRAMADO : "tracciona"
    EMPLEADO ||--o{ VIAJE_PROGRAMADO : "conducido por"

    RUTA {
        number id_ruta PK
        number linea_id FK
        varchar codigo_ruta UK
        varchar sentido
        varchar tipo_servicio
        number distancia_total_km
        varchar estado
    }

    RUTA_DETALLE {
        number id_ruta_detalle PK
        number ruta_id FK
        number estacion_id FK
        number orden_parada
        number se_detiene
        varchar hora_estimada_llegada
    }

    HORARIO {
        number id_horario PK
        number ruta_id FK
        varchar tipo_dia
        varchar hora_inicio
        varchar hora_fin
        number frecuencia_minutos
    }

    VIAJE_PROGRAMADO {
        number id_viaje PK
        number ruta_id FK
        number tren_id FK
        number conductor_id FK
        varchar codigo_viaje UK
        date fecha_programada
        date hora_salida_programada
        date hora_salida_real
        varchar estado
        number minutos_retraso
    }
```

### 2.3 Subsistema 3: Material Rodante, Talleres y Órdenes de Mantenimiento

```mermaid
erDiagram
    MODELO_TREN ||--o{ TREN : "diseño tecnico de"
    MODELO_TREN ||--o{ VAGON : "diseño coches de"
    DEPOSITO ||--o{ TREN : "alberga en patio"
    TREN ||--o{ TREN_VAGON : "acopla"
    VAGON ||--o{ TREN_VAGON : "forma parte de"
    TREN ||--o{ ORDEN_MANTENIMIENTO : "intervenido en"
    EQUIPO ||--o{ ORDEN_MANTENIMIENTO : "reparado en"
    ORDEN_MANTENIMIENTO ||--o{ ORDEN_REPUESTO : "consume"
    REPUESTO ||--o{ ORDEN_REPUESTO : "utilizado como"
    ORDEN_MANTENIMIENTO ||--o{ ORDEN_TECNICO : "ejecutada por"
    EMPLEADO ||--o{ ORDEN_TECNICO : "trabaja en"

    MODELO_TREN {
        number id_modelo PK
        varchar nombre UK
        varchar fabricante
        varchar galibo
        varchar tipo_propulsion
    }

    TREN {
        number id_tren PK
        varchar numero_tren UK
        number modelo_id FK
        number deposito_id FK
        varchar estado_operativo
        number kilometraje_total
        date fecha_ultima_inspeccion
    }

    VAGON {
        number id_vagon PK
        varchar numero_serie UK
        number modelo_id FK
        varchar tipo_vagon
        number capacidad_pasajeros
    }

    ORDEN_MANTENIMIENTO {
        number id_orden PK
        varchar codigo_orden UK
        number tren_id FK
        number equipo_id FK
        varchar tipo_mantenimiento
        varchar prioridad
        varchar estado
        date fecha_programada
    }
```

### 2.4 Subsistema 4: Personal Operativo, Turnos y Certificaciones

```mermaid
erDiagram
    EMPLEADO ||--o{ EMPLEADO : "supervisa jerarquicamente a"
    TURNO ||--o{ EMPLEADO : "asigna jornada a"
    EMPLEADO ||--o{ CERTIFICACION : "obtiene"
    CERTIFICACION ||--o{ CERTIFICACION_MODELO : "habilita para"
    MODELO_TREN ||--o{ CERTIFICACION_MODELO : "cubierto por"

    EMPLEADO {
        number id_empleado PK
        varchar numero_empleado UK
        varchar primer_nombre
        varchar primer_apellido
        varchar cargo
        number supervisor_id FK
        number turno_habitual_id FK
        date fecha_contratacion
        varchar estado
    }

    CERTIFICACION {
        number id_certificacion PK
        number empleado_id FK
        varchar tipo_certificacion
        date fecha_emision
        date fecha_vencimiento
        varchar estado
    }

    CERTIFICACION_MODELO {
        number id_certificacion_modelo PK
        number certificacion_id FK
        number modelo_id FK
    }

    TURNO {
        number id_turno PK
        varchar nombre UK
        varchar hora_inicio
        varchar hora_fin
        varchar tipo_jornada
    }
```

### 2.5 Subsistema 5: Pasajeros, Billetaje OMNY y Torniquetes

```mermaid
erDiagram
    PASAJERO ||--o{ TARJETA : "titular de"
    TARJETA ||--o{ RECARGA : "acredita fondos en"
    TARJETA ||--o{ VIAJE_PASAJERO : "valida paso con"
    TARIFA ||--o{ VIAJE_PASAJERO : "aplica valor a"
    ESTACION ||--o{ VIAJE_PASAJERO : "torniquete de acceso en"

    PASAJERO {
        number id_pasajero PK
        varchar numero_identificacion UK
        varchar nombre
        varchar correo_electronico
        varchar categoria_usuario
    }

    TARJETA {
        number id_tarjeta PK
        varchar numero_tarjeta UK
        number pasajero_id FK
        number saldo_disponible
        varchar estado
        date fecha_emision
        date fecha_vencimiento
    }

    RECARGA {
        number id_recarga PK
        number tarjeta_id FK
        number monto
        varchar metodo_pago
        varchar numero_transaccion UK
        date fecha_hora
    }

    TARIFA {
        number id_tarifa PK
        varchar codigo UK
        varchar nombre
        number monto
        varchar estado
    }

    VIAJE_PASAJERO {
        number id_viaje_pasajero PK
        number tarjeta_id FK
        number estacion_ingreso_id FK
        number tarifa_id FK
        number monto_cobrado
        date fecha_hora_ingreso
        varchar estado_transaccion
    }
```

### 2.6 Subsistema 6: Contingencias, Incidentes y Auditoría

```mermaid
erDiagram
    EMPLEADO ||--o{ INCIDENTE : "reporta a despacho"
    INCIDENTE ||--o{ INCIDENTE_ELEMENTO_AFECTADO : "detalla impacto en"

    INCIDENTE {
        number id_incidente PK
        varchar codigo_incidente UK
        varchar tipo_incidente
        varchar severidad
        varchar estado
        date fecha_hora_inicio
        date fecha_hora_cierre
        number reportado_por_id FK
        varchar descripcion
    }

    INCIDENTE_ELEMENTO_AFECTADO {
        number id_elemento_afectado PK
        number incidente_id FK
        varchar tipo_elemento
        number id_elemento
        varchar tipo_afectacion
        varchar observaciones
    }

    BITACORA {
        number id_bitacora PK
        timestamp fecha_hora
        varchar operacion
        varchar tabla_afectada
        varchar registro_id
        varchar usuario_oracle
        varchar detalle
    }
```

---

## 3. Reglas de Lectura Barker CDM (Ejemplos Canónicos)

Siguiendo el estándar formal **Barker CDM / Oracle Data Modeler**, las relaciones se leen bidireccionalmente:

1. **`LINEA` &harr; `RUTA`**:
   - *Cada* `LINEA` **puede** originar una o muchas `RUTA`s.
   - *Cada* `RUTA` **debe** pertenecer a una y solo una `LINEA`.
2. **`ESTACION` &harr; `PLATAFORMA`**:
   - *Cada* `ESTACION` **debe** contener una o muchas `PLATAFORMA`s.
   - *Cada* `PLATAFORMA` **debe** estar ubicada en una y solo una `ESTACION`.
3. **`TREN` &harr; `VIAJE_PROGRAMADO`**:
   - *Cada* `TREN` **puede** traccionar uno o muchos `VIAJE_PROGRAMADO`s.
   - *Cada* `VIAJE_PROGRAMADO` **debe** ser traccionado por uno y solo un `TREN`.
4. **`PASAJERO` &harr; `TARJETA`**:
   - *Cada* `PASAJERO` **puede** ser titular de una o muchas `TARJETA`s.
   - *Cada* `TARJETA` **debe** pertenecer a uno y solo un `PASAJERO`.
5. **`EMPLEADO` &harr; `EMPLEADO` (Relación Reflexiva de Jerarquía)**:
   - *Cada* `EMPLEADO` **puede** supervisar a uno o muchos `EMPLEADO`s.
   - *Cada* `EMPLEADO` **puede** estar bajo la supervisión de uno y solo un `EMPLEADO` (opcional en ambos extremos para admitir el nodo raíz de la Dirección General).

---

## 4. Transformación al Modelo Relacional de Oracle

El proceso de ingeniería directa (*Engineer to Relational Model*) convirtió las definiciones conceptuales en estructuras relacionales concretas:

1. **Mapeo de Claves Primarias**:
   - Cada entidad fuerte o débil adoptó una llave primaria sintética entera mediante secuencias de Oracle (`ID_*`), eliminando claves naturales compuestas voluminosas y agilizando las búsquedas por índice B-Tree único.
2. **Mapeo de Relaciones $1:N$**:
   - El identificador del lado '1' se propaga como columna `FOREIGN KEY` en la tabla del lado 'N' (ej. `ESTACION_ID` en `PLATAFORMA`).
3. **Mapeo de Relaciones $N:M$**:
   - Se crearon tablas asociativas intermedias dedicadas con claves foráneas apuntando a ambas entidades maestras y restricciones de integridad en cascada según las políticas de seguridad de la red.
4. **Exportación Formal a Formato Vectorial (PDF)**:
   - Para cumplir estrictamente con el requerimiento de evaluación del profesor (Lecciones 7 y 8):
     $$\text{Oracle SQL Developer Data Modeler} \longrightarrow \text{File} \longrightarrow \text{Print Diagram} \longrightarrow \text{To PDF File}$$
   - Esto preserva la fidelidad vectorial al ampliar el diagrama, evitando penalizaciones por degradación visual de capturas de pantalla ráster.
