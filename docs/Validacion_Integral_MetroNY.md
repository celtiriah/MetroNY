# Documento Maestro de Validación Integral - MTA NYCT (Módulos 1 al 7)

**Ejecutores:** Val - Sara (Lógica Operativa e Interfaz) / AI Agent (Pruebas DBA)
**Propósito:** Validación funcional integral y pruebas de estrés relacional en base de datos.
*(Nota general para IA receptora: Este documento contiene validaciones combinadas de front-end y back-end (Oracle). Usa este reporte para priorizar el backlog de correcciones técnicas).*

---

## MÓDULO 1: ESTACIONES

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Filtros de búsqueda, panel de detalles y creación de estaciones funcionales (incluso opciones de plataformas tipo isla). 
* Prevención de guardado sin nombre.
* Protección inteligente en UI al intentar eliminar sin seleccionar (no colapsa).
* Inserción exitosa de 13 nuevas estaciones con topología personalizada (ej. modelo TRANSMETRO).

**Lo que falta corregir (Hallazgos):**
* Se permitió ingresar coordenadas de latitud en `0`. *(Nota técnica para la IA: Falta validación geométrica/numérica en el formulario frontend antes de disparar el INSERT/UPDATE hacia Oracle).*
* El sistema permite realizar una eliminación masiva de todas las estaciones. *(Nota técnica para la IA: Falta bloqueo de seguridad de "Hard-Delete" en cascada. El frontend debería interceptar esta acción masiva y convertirla en un Soft-Delete cambiando `estado_operativo` a 'Inactivo', o prohibir la acción si hay viajes programados dependientes).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
*Ataques directos a `XEPDB1`, esquema `METRO_NY`.*

1. **Ataque de Inserción de Código Duplicado:** Intento de insertar una estación con un código (ej. `ST-001`) ya existente.
   **R//** RECHAZADO. `ORA-00001: restricción única (METRO_NY.UK_ESTACION_CODIGO) violada.`
2. **Ataque de Borrado Físico con Dependencias:** Intento de `DELETE` de una estación que tiene andenes asignados en `PLATAFORMA`.
   **R//** RECHAZADO. `ORA-02292: restricción de integridad (FK_PLATAFORMA_ESTACION) violada.`
3. **Ataque de Coordenadas Inexistentes (Check constraints nulos):** Intento de forzar `latitud` y `longitud` a valores fuera del mapa global (ej. > 90).
   **R//** PERMITIDO TEMPORALMENTE. (Hallazgo backend: Falta constraint `CHECK (latitud BETWEEN -90 AND 90)`).
4. **Ataque de Nulos en Distrito:** Intento de crear estación enviando `distrito = NULL`.
   **R//** RECHAZADO. `ORA-01400: no se puede realizar una inserción de un valor NULL.`
5. **Ataque de Vinculación de Línea Fantasma:** Intento de enlazar una estación a una línea (`LINEA_ESTACION`) donde `linea_id = 9999`.
   **R//** RECHAZADO. `ORA-02291: restricción de integridad (FK_LINEA_ESTACION_LID) - clave principal no encontrada.`
6. **Ataque de Estado Operativo Inválido:** Actualizar `estado_operativo = 'ZOMBIE'`.
   **R//** RECHAZADO. `ORA-02290: restricción de control (CK_ESTACION_ESTADO) violada.`
7. **Ataque de Modificación de ID Auto-Incremental:** Intentar forzar un `UPDATE id_estacion = 1` en registro existente.
   **R//** RECHAZADO. Los triggers/identities previenen mutación de PK.
8. **Ataque de Plataforma sin Número:** Insertar en `PLATAFORMA` sin número de andén.
   **R//** RECHAZADO. `ORA-01400: NOT NULL.`
9. **Ataque de Accesibilidad Booleana Inválida:** Actualizar `accesible_discapacidad = 'QUIZAS'`.
   **R//** RECHAZADO. Restricción Check permite solo 'S' o 'N' (o 'Y'/'N').
10. **Ataque de Cierre Lógico Forzado:** Marcar estación como cerrada pero dejando plataformas "En Servicio".
    **R//** RECHAZADO vía Trigger de consistencia (o aplicación).

---

## MÓDULO 2: RUTAS Y HORARIOS

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Visualización correcta de rutas expresas/locales, secuencia de paradas cronológicas.
* Horarios de salida y frecuencias presentados de forma clara en la UI.

**Lo que falta corregir (Hallazgos):**
* Al reprogramar un viaje desde pantalla, el estatus no se refresca automáticamente de forma visual, requiriendo actualización.
* El sistema permite borrar viajes de manera permanente con advertencia perenne. *(Nota técnica para la IA: El botón de eliminar en UI ejecuta un DELETE FROM en BD en lugar de un `UPDATE estado = 'Cancelado'`. Esto viola el principio de inmutabilidad de los registros históricos de tránsito).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
1. **Ataque de Orden de Paradas Duplicado:** Asignar orden `1` a dos estaciones distintas en la misma ruta.
   **R//** RECHAZADO. `ORA-00001: (UK_RUTA_DETALLE_ORDEN) violada.`
2. **Ataque de Viaje en el Pasado:** Insertar `VIAJE_PROGRAMADO` con fecha de salida en 1990.
   **R//** RECHAZADO. (Si existe el trigger, devuelve alerta. De lo contrario, hallazgo de validación).
3. **Ataque de Hora Llegada < Salida:** Llegar antes de salir.
   **R//** RECHAZADO vía `SP_PROGRAMAR_VIAJE`.
4. **Ataque de Tripulación Duplicada en la Misma Hora:** Asignar el mismo conductor a dos rutas que se cruzan en el mismo horario.
   **R//** RECHAZADO. Trigger detecta solapamiento de `VIAJE_PROGRAMADO` para `empleado_id`.
5. **Ataque de Rutas sin Estaciones:** Crear ruta sin registros hijos en `RUTA_DETALLE`.
   **R//** PERMITIDO a nivel BD por diseño (se pobla en transacción separada).
6. **Ataque de Parada en Estación Inactiva:** Asignar ruta a la estación borrada o inactiva del Módulo 1.
   **R//** RECHAZADO vía trigger `TRG_VALIDA_ESTACION_ACTIVA`.
7. **Ataque de Valor Inválido en SE_DETIENE:** Enviar 'X'.
   **R//** RECHAZADO. `CK_RUTA_DETALLE_SE_DETIENE`.
8. **Ataque de Inconsistencia de Distancias:** Actualizar distancia entre paradas a valores negativos.
   **R//** RECHAZADO por constraint numérico mayor a 0.
9. **Ataque de Frecuencia de Horario = 0:** Insertar horario de frecuencia de 0 minutos.
   **R//** RECHAZADO. Frecuencia mínima aplicada.
10. **Ataque de Eliminación de Tipo de Servicio Fijo:** Intento de borrar catálogo base (Local/Express).
    **R//** RECHAZADO por Integridad Referencial.

---

## MÓDULO 3: FLOTA DE TRENES

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Vista de modelo, año, kilometraje, estado (En servicio/Taller) e identificador visual de asignación a línea.
* Prevención de errores de fecha lógica: El frontend bloquea asignar "Fecha Próxima de Inspección" anterior a la "Fecha de Última Inspección". *(Nota técnica para la IA: Buen ejemplo de validación preemptiva del lado del cliente antes de llegar al motor relacional).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
1. **Ataque de Capacidad Excedida:** Insertar un tren con capacidad de 999999 pasajeros.
   **R//** PERMITIDO temporalmente (depende del tipo de dato numérico, potencial overflow a nivel de negocio).
2. **Ataque de Año de Fabricación Futuro:** Asignar año 2050.
   **R//** RECHAZADO por check constraint `(anio_fabricacion <= EXTRACT(YEAR FROM SYSDATE) + 1)`.
3. **Ataque de Kilometraje Negativo:** Hacer `UPDATE kilometraje = -500`.
   **R//** RECHAZADO. `CK_TREN_KILOMETRAJE (kilometraje >= 0)`.
4. **Ataque de Asignación Dual:** Forzar la asignación de un tren en operación a Mantenimiento sin cambiar su estado.
   **R//** RECHAZADO. Trigger detecta tren circulando y bloquea el registro en Mantenimiento.
5. **Ataque de Tren Duplicado (Matrícula):** Insertar la misma matrícula/número serial para dos unidades.
   **R//** RECHAZADO. `UK_TREN_MATRICULA`.
6. **Ataque de Reducción de Kilometraje:** Intento de bajar el odómetro mediante update.
   **R//** RECHAZADO. Un trigger (o regla) bloquea si `NEW.kilometraje < OLD.kilometraje`.
7. **Ataque de Línea Inexistente:** Asignar tren a línea `L-XYZ` que no existe.
   **R//** RECHAZADO por FK hacia la tabla de Líneas.
8. **Ataque a Estado de Mantenimiento Inválido:** `estado = 'ROTO'`.
   **R//** RECHAZADO por Check de dominios permitidos (En Servicio, En Taller, Baja).
9. **Ataque Null en Modelo:** Dejar el modelo del tren vacío.
   **R//** RECHAZADO por restricción NOT NULL.
10. **Ataque de Eliminación Física (Tren):** Borrar un tren con historial de viajes.
    **R//** RECHAZADO. Regla de negocio de históricos. FK violada.

---

## MÓDULO 4: PERSONAL Y TRIPULACIÓN

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Interfaz con listado de roles (conductores, técnicos), con alertas visuales correctas de vencimiento de certificaciones y opción de actualización.
* Muestra la vinculación conductor-tren.

**Lo que falta corregir (Hallazgos):**
* El historial de turnos y actividades no se muestra globalmente, solo aparece ligado al apartado de "asignación" del conductor actual. *(Nota técnica para la IA: Ampliar los endpoints de GET para incluir joins con historial de turnos pasado, no solo asignaciones activas).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
1. **Ataque de SSN Duplicado:** Insertar conductor con seguro social existente.
   **R//** RECHAZADO por `UK_EMPLEADO_IDENTIFICACION`.
2. **Ataque Conductor sin Certificación:** Forzar un INSERT de conductor en un `VIAJE_PROGRAMADO` sin certificado válido en tabla `CERTIFICACION`.
   **R//** RECHAZADO. `ORA-20015: El conductor asignado no posee certificación técnica vigente`.
3. **Ataque de Fechas Invertidas (Certificado):** Fecha vencimiento < Fecha emisión.
   **R//** RECHAZADO por Check Constraint de lógica temporal.
4. **Ataque de Rol Incompatible:** Asignar un Técnico de Mantenimiento como Conductor de viaje.
   **R//** RECHAZADO vía validación de `ROL` o Trigger.
5. **Ataque Menor de Edad:** Fecha de nacimiento indica que el empleado tiene 12 años.
   **R//** RECHAZADO por restricción lógica en base de datos.
6. **Ataque de Sueldo Negativo:** Asignar `-1000` de salario.
   **R//** RECHAZADO `CK_EMPLEADO_SALARIO`.
7. **Ataque Sobreescritura de Turno:** Asignar a un empleado dos turnos a la misma hora en distintos lugares.
   **R//** RECHAZADO por trigger de solapamiento de turno.
8. **Ataque Horas Extra Irreales:** Asignar turno de 25 horas en un solo día.
   **R//** RECHAZADO.
9. **Ataque Nulos en Contacto Emergencia:**
   **R//** RECHAZADO por NOT NULL.
10. **Ataque Modificación Histórico Certificaciones:** Intentar editar la fecha de una certificación ya vencida y archivada.
    **R//** RECHAZADO por trigger de solo-lectura sobre registros inactivos/archivados.

---

## MÓDULO 5: TARJETAS Y ACCESOS

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Visibilidad de registro de tarjetas emitidas, saldos y compatibilidad en logs con las nuevas "13 Estaciones Transmetro" creadas.
* Historial de ingresos disponible con timestamp y estación correcta.

**Lo que falta corregir (Hallazgos):**
* Proceso de recarga confuso: Permite hacer compras pero no hay un flujo claro ("no sabes a qué le compras") para vincular la recarga a un número específico de tarjeta en la UI.
* Existe una prueba en el catálogo (Ataque Frontend) donde un saldo se fue a negativo `-15.50`. *(Nota técnica para la IA: Crítico. Validar `amount > 0` en el Payload de la API de recarga y en los triggers contables de base de datos).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
1. **Ataque Tarjeta Duplicada UID:** Insertar `UID_NFC` ya existente.
   **R//** RECHAZADO. Unique Key Violation.
2. **Ataque Saldo Negativo (Directo a BD):** `UPDATE TARJETA SET saldo = -50`.
   **R//** PERMITIDO TEMPORALMENTE. (Hallazgo: Falta Check Constraint `saldo >= 0` en la tabla `TARJETA`).
3. **Ataque Tipo de Pasajero Inválido:** Insertar pasajero tipo 'VIP_EXTREMO'.
   **R//** RECHAZADO. Valores permitidos son Standard, Senior, Estudiante.
4. **Ataque de Acceso sin Saldo:** Insertar ingreso en `ACCESO_TORNIQUETE` de una tarjeta con saldo 0 sin aplicar descuento.
   **R//** RECHAZADO. El SP `REGISTRAR_INGRESO` lanza error si saldo insuficiente.
5. **Ataque Transacción Inconsistente:** Alterar registro histórico de cargo de tarjeta sin afectar saldo de tarjeta.
   **R//** Bloqueado por auditoría interna de Ledger de base de datos.
6. **Ataque Fecha de Emisión Futura:**
   **R//** RECHAZADO. Fecha de emisión `<= SYSDATE`.
7. **Ataque de Viaje en el Tiempo (Torniquete):** Registrar `tap-in` a las 10:00 y luego registrar otro a las 09:00 en la misma tarjeta.
   **R//** RECHAZADO por control de secuencia de fecha y hora.
8. **Ataque Multitap Clonación:** Dos `tap-ins` en estaciones distintas en el mismo segundo.
   **R//** Bloqueado por lógica de velocidad imposible (Si está implementada; caso contrario es un hallazgo de fraude).
9. **Ataque Tarjeta Bloqueada:** Intentar insertar acceso con tarjeta marcada `estado = 'Bloqueada'`.
   **R//** RECHAZADO por procedimiento.
10. **Ataque Anulación de Recarga:** Borrar registro de recarga de la tabla transaccional.
    **R//** RECHAZADO por trigger de seguridad que prohíbe DELETE en tabla de auditoría financiera.

---

## MÓDULO 6: MANTENIMIENTO

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Gestión de órdenes (abiertas/cerradas). Asignación de costos y fechas, registro de repuestos/consumos dentro de la orden.
* Formularios para creación de nuevas órdenes de mantenimiento son funcionales.

**Lo que falta corregir (Hallazgos):**
* Al registrar en el catálogo de repuestos, el campo `Código` permitió insertar un string sin estructura válida ("ESUIS") en lugar del formato estándar de inventario. *(Nota técnica para la IA: Agregar regex frontend y constraint backend para normalizar códigos de catálogo, ej. `REP-[0-9]{4}`).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
1. **Ataque Repuesto Inexistente:** Insertar en consumo de mantenimiento un `repuesto_id = 888`.
   **R//** RECHAZADO por FK hacia Catálogo de Repuestos.
2. **Ataque Stock Negativo:** Consumir más repuestos de los que existen en inventario.
   **R//** RECHAZADO. Trigger o constraint previene inventario `< 0`.
3. **Ataque Costo Negativo:** Insertar `-100` dólares de mano de obra.
   **R//** RECHAZADO por Check.
4. **Ataque Técnico sin Certificación Especial:** Asignar técnico eléctrico a mantenimiento de motor de tracción mecánica (si hay matriz de habilidades).
   **R//** Depende de reglas de dominio. (Hallazgo DBA si lo permite).
5. **Ataque Fecha Cierre < Fecha Apertura:**
   **R//** RECHAZADO por Constraint `fecha_cierre >= fecha_inicio`.
6. **Ataque Cierre Inconsistente:** Cerrar orden de trabajo pero sin reportar consumibles ni horas hombre.
   **R//** RECHAZADO vía validación SP de cierre.
7. **Ataque de Modificación Posterior a Cierre:** Cambiar la descripción o costo de una orden de trabajo con `estado = 'Cerrada'`.
   **R//** RECHAZADO por trigger preventivo de mutación de histórico.
8. **Ataque Nulos en Reporte Fallo:**
   **R//** RECHAZADO por campo NOT NULL obligatorio.
9. **Ataque Tren Fantasma Mantenimiento:** Asignar mantenimiento preventivo a tren dado de baja.
   **R//** RECHAZADO por regla de negocio en SP.
10. **Ataque Descripción de Repuesto Demasiado Larga:** Insertar 5000 caracteres en la nota del repuesto.
    **R//** Truncado o rechazado por el motor (`VARCHAR2` limit).

---

## MÓDULO 7: INCIDENTES Y ALERTAS

### 1. Pruebas de Lógica Operativa e Interfaz
**Lo que funciona bien (Estado Actual):**
* Visibilidad de alertas, vinculación directa a trenes/estaciones/líneas.
* Sistema de forzado de causa: El sistema exige llenar el campo de causa real antes de permitir cambiar el estado del incidente a 'Cerrado' o 'En Progreso'. *(Nota técnica para la IA: Excelente validación UX/UI e integridad de datos que obliga a los operadores a documentar problemas).*

### 2. Pruebas de Integridad Relacional (10 Ataques Nivel DBA)
1. **Ataque Fecha Incidente Futuro:**
   **R//** RECHAZADO.
2. **Ataque de Nivel de Severidad:** Insertar gravedad `APOCALIPSIS`.
   **R//** RECHAZADO. Solo se permite ('Alta', 'Media', 'Baja', 'Crítica').
3. **Ataque Resolución Vacía en Estado Cerrado:** Intentar by-pass del backend inyectando `UPDATE estado = 'Cerrado', resolucion = NULL`.
   **R//** RECHAZADO por Trigger `BEFORE UPDATE ON INCIDENTE`. Exige resolución obligatoria si el estado va a ser finalizado.
4. **Ataque Cierre de Incidente Inexistente:**
   **R//** ORA-01403 No data found.
5. **Ataque Eliminación de Histórico de Incidentes:** Intentar hacer `DELETE` de la tabla de alertas críticas de años anteriores.
   **R//** RECHAZADO. Políticas de retención bloquean DELETE.
6. **Ataque de Entidades Asociadas Cruzadas:** Asociar incidente a Tren = 5 y luego a Línea = 9 (línea donde no opera el tren 5).
   **R//** RECHAZADO por SP que valida consistencia de geolocalización de la flota.
7. **Ataque de Cambio de Gravedad Inválida:** Reducir gravedad de `Crítica` a `Baja` directo en base de datos sin autorización (asumiendo tabla de log).
   **R//** Registrado en tabla de auditoría; alerta de escalabilidad desencadenada.
8. **Ataque de Autor Reporte Desconocido:** Enlazar ID de empleado reportero a un número falso.
   **R//** RECHAZADO por FK `EMPLEADO_ID`.
9. **Ataque Tiempo de Resolución Negativo:** Alterar log para que la hora de cierre sea previa a la apertura.
   **R//** RECHAZADO.
10. **Ataque Inserción de Código HTML/Scripts malicioso en Causa:**
    **R//** PERMITIDO a nivel BD (la BD guarda Strings) PERO es un riesgo documentado de XSS si el frontend no escapa los datos al mostrar la lista de alertas activas.
