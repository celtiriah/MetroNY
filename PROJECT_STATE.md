# Estado del Proyecto y Memoria Compartida: Metro NY (MTA NYCT)

> **Documento de Sincronización Inter-Entornos y Multi-Agente**  
> Esta bitácora sirve como memoria centralizada y fuente única de verdad para agentes de IA (Antigravity IDE, Antigravity 2.0, VS Code, Claude, Codex) y desarrolladores del equipo.

---

## 1. Contexto del Proyecto, Especificaciones y Reglas Obligatorias

- **Idioma Obligatorio** : **Todos los archivos, documentación, scripts y código del proyecto deben redactarse y mantenerse en ESPAÑOL**, dado que el curso y la evaluación académica se imparten en este idioma.
- **Enunciado y Requerimientos** : [docs/Enunciado - Proyecto_ Sistema de Gestión del Metro de Nueva York.md](docs/Enunciado%20-%20Proyecto_%20Sistema%20de%20Gesti%C3%B3n%20del%20Metro%20de%20Nueva%20York.md).
- **Investigación Operativa MTA** : [docs/investigacion_operaciones_mta.md](docs/investigacion_operaciones_mta.md) (detalles de gálibo División A vs B, vías cuádruples expresas/locales, peaje OMNY con tope de 7 días, mantenimiento SMS en Coney Island/207th St, y contingencias 24/7).
- **Base de Datos** : Oracle Database 23ai local (`FREEPDB1`, fallback automático `XEPDB1`), puerto `1521`, esquema `METRO_NY` / `MetroPass123`.
- **Propósito del Directorio `database/`** : Contiene los scripts canónicos organizados en 3 subcarpetas (`01_setup/`, `02_plsql/`, `03_pruebas/`) ejecutables de manera reproducible mediante `dbconfigurar.bat` (esquema, tablas, datos, índices) y `dbprogramar.bat` (vistas, funciones, SPs y triggers).
- **Prioridad de Desarrollo** : La prioridad absoluta del desarrollo se concentra en la **aplicación de escritorio nativa** en `prototypes/desktop/` (PyQt5 + PyQt-Fluent-Widgets).
- **Regla Estricta de Git** : **JAMÁS ejecutar `git commit` ni `git push` automáticamente**. Todos los cambios deben permanecer sin preparar (unstaged) para que el usuario los revise y realice los commits manualmente.
- **Estándar de Calidad y Tipado (Pylance/Pyright)** : Cumplimiento riguroso del Skill `pyqt-pylance-guardian` (`.agents/skills/pyqt-pylance-guardian/`), con 0 advertencias de tipo, comprobación explícita de `None` (`if var is not None:`) y uso exclusivo de énumérations scopées (`Qt.AlignmentFlag.*`, `QHeaderView.ResizeMode.*`).

---

## 2. Arquitectura Técnica del Código

```text
MetroNY/
├── PROJECT_STATE.md             # Esta bitácora de memoria compartida (en español)
├── README.md                    # Documentación principal del repositorio
│
├── .agents/skills/
│   └── pyqt-pylance-guardian/   # Skill de verificación estática y reglas Pylance/PyQt
│       ├── SKILL.md
│       └── scripts/check_pyqt_pylance.py
│
├── database/                    # SCRIPTS CANÓNICOS Y MODULARES DE BASE DE DATOS
│   ├── dbconfigurar.bat / .sh   # [Paso 1] Instalación de esquema, 33 tablas, 208 datos y 63 índices
│   ├── dbprogramar.bat / .sh    # [Paso 2] Compilación de lógica PL/SQL (9 Vistas, 9 Funciones, 6 SPs, 8 Triggers)
│   ├── get_pdb.sql              # Script SQL de autodetección del servicio PDB activo (FREEPDB1 / XEPDB1)
│   │
│   ├── 01_setup/                # Infraestructura Base y Datos
│   │   ├── 01_configuracion_usuario.ddl # Tablespaces y usuario METRO_NY
│   │   ├── 02_ddl_tablas.ddl    # 33 tablas normalizadas en 3NF con constraints
│   │   ├── 03_datos_prueba.ddl  # 208 registros con datos reales del metro de NY
│   │   └── 04_indices.ddl       # 63 índices B-Tree de optimización
│   │
│   ├── 02_plsql/                # Capa de Negocio y Automatización PL/SQL
│   │   ├── 05_vistas.sql        # 9 vistas analíticas y operativas (VW_*)
│   │   ├── 06_funciones.sql     # 9 funciones de cálculo de negocio (FN_*)
│   │   ├── 07_procedimientos.sql# 6 procedimientos almacenados transaccionales (SP_*)
│   │   └── 08_triggers.sql      # 8 triggers de integridad, auditoría y bitácora (TRG_*)
│   │
│   └── 03_pruebas/              # Validación y Pruebas del Sistema
│       ├── prueba_15_consultas.sql     # Las 15 consultas mínimas obligatorias
│       └── test_plsql_verificacion.sql # Verificación funcional de objetos PL/SQL con rollback
│
├── docs/                        # Documentación académica y técnica (siempre en español)
│   ├── Enunciado - Proyecto...  # Especificación oficial de requerimientos de la cátedra
│   ├── caratula_y_planificacion.md # Carátula institucional, padrón de 7 estudiantes y matriz RACI
│   ├── diccionario_datos.md     # Diccionario institucional de 33 tablas y 270+ restricciones
│   ├── normalizacion_3nf.md     # Dictamen formal de 1NF, 2NF y 3NF con demostraciones matemáticas
│   ├── modelo_entidad_relacion.md # Modelo Barker CDM y diagramas Mermaid modulares
│   ├── guia_sistema_usuario.md  # Manual ilustrado de usuario y arquitectura de 3 capas
│   └── investigacion_operaciones_mta.md # Estudio técnico del metro de NY (Div A/B, OMNY, SMS)
│
├── prototypes/
│   ├── desktop/                 # FOCO PRINCIPAL: App de escritorio nativa (Python 3.14 + PyQt5 + QFluentWidgets)
│   │   ├── main.py              # Punto de entrada principal (High-DPI y loop de eventos Qt)
│   │   ├── config.py            # Credenciales Oracle, PDBs, dimensiones y colores oficiales MTA
│   │   ├── requirements.txt     # Dependencias oficiales (PyQt5, PyQt-Fluent-Widgets, oracledb)
│   │   ├── start.bat / .sh      # Lanzadores en un solo clic
│   │   │
│   │   ├── services/            # Capa de lógica y acceso a datos (Python puro)
│   │   │   ├── db.py            # Conexión oracledb con pool y fallback multi-PDB
│   │   │   ├── metro_service.py # Servicios de dominio (KPIs, líneas, estaciones, flota, personal)
│   │   │   ├── m1_network_service.py # Lógica de negocio y transacciones para MÓDULO 1 (Red y Estaciones)
│   │   │   ├── m2_routes_service.py  # Lógica de negocio y transacciones para MÓDULO 2 (Rutas y Horarios)
│   │   │   ├── m3_fleet_service.py   # Lógica de negocio y transacciones para MÓDULO 3 (Flota y Trenes)
│   │   │   ├── actions_service.py # Enlace con Procedimientos Almacenados y Funciones PL/SQL
│   │   │   └── queries_catalog.py # Catálogo de las 15 consultas analíticas con filtros dinámicos
│   │   │
│   │   ├── workers/             # Hilos de ejecución en segundo plano (Threading asíncrono)
│   │   │   └── query_worker.py  # QThread asíncrono para mantener 60 FPS fluidos
│   │   │
│   │   ├── components/          # Widgets Fluent reutilizables (StatCard, StatusCard)
│   │   │
│   │   └── views/               # Interfaces / Pantallas Fluent
│   │       ├── main_window.py          # Ventana principal FluentWindow (navegación y título)
│   │       ├── dashboard_interface.py  # Panel General (resumen en vivo, 6 KPIs, líneas)
│   │       ├── m1_stations_interface.py # MÓDULO 1: Administración de la Red (100% Implementado)
│   │       ├── m2_routes_interface.py   # MÓDULO 2: Rutas y Horarios (100% Implementado)
│   │       ├── m3_fleet_interface.py    # MÓDULO 3: Flota y Material Rodante (100% Implementado)
│   │       ├── m4_staff_interface.py   # MÓDULO 4: Personal y turnos
│   │       ├── m5_cards_interface.py   # MÓDULO 5: Pasajeros, Tarjetas OMNY y Simulador Torniquete
│   │       ├── m7_incidents_interface.py # MÓDULO 7: Incidentes y afectaciones
│   │       └── queries_interface.py    # 15 Consultas Obligatorias con parámetros dinámicos
│   │
│   └── webapp/                  # Prototipo Web complementario (Flask API + HTML/CSS/JS)
```

---

## 3. Estado de Implementación de los 7 Módulos del Sistema (Enunciado Oficial)

Conforme a la especificación académica oficial ([docs/Enunciado - Proyecto_ Sistema de Gestión del Metro de Nueva York.md](docs/Enunciado%20-%20Proyecto_%20Sistema%20de%20Gesti%C3%B3n%20del%20Metro%20de%20Nueva%20York.md)), el sistema comprende **7 módulos funcionales**. A continuación se detalla el estado actual de implementación de cada uno:

### [COMPLETADO] Módulo 1: Administración de la Red (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m1_stations_interface.py` y `prototypes/desktop/services/m1_network_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con las 9 operaciones requeridas por la cátedra:

- [x] **Op 1: Crear, modificar, consultar y desactivar líneas**: Diálogo modal `LineaDialog` (código, nombre, color oficial en formato HEX, terminal de origen, terminal de destino, longitud en km y operador) con acción reactiva en caliente para conmutar estado (`'Activa'` / `'Inactiva'`).
- [x] **Op 2: Crear y modificar estaciones**: Diálogo modal `EstacionDialog` (código, nombre, dirección, distrito/borough, coordenadas geográficas WGS84, accesibilidad ADA, elevadores, escaleras eléctricas y horarios de servicio) con control de estado operativo (`'Operativa'`, `'Cerrada'`, `'Cerrada Temporalmente'`).
- [x] **Op 3: Asociar estaciones con líneas**: Diálogo modal `AsociarEstacionDialog` con selector de estaciones no asociadas previamente a la línea activa y asignación de orden secuencial.
- [x] **Op 4: Definir el orden de las estaciones**: Control del campo `ORDEN` con validación de unicidad secuencial por línea y ordenación automática ascendente (`ORDER BY se.ORDEN ASC`).
- [x] **Op 5: Registrar distancias y tiempos entre estaciones**: Campos interactivos `DISTANCIA_KM` y `TIEMPO_ESTIMADO_MIN` en `AsociarEstacionDialog`, actualizables de manera independiente para cada tramo inter-estación.
- [x] **Op 6: Administrar plataformas**: Panel inspector de andenes con tabla reactiva, diálogo `PlataformaDialog` (código de andén, dirección de viaje Uptown/Downtown, capacidad estimada de pasajeros y estado) y eliminación con actualización en vivo.
- [x] **Op 7: Definir estaciones de transferencia**: Diálogo `TransferenciaDialog` para vincular enlaces peatonales subterráneos entre dos líneas distintas en la estación seleccionada, registrando el tiempo estimado de caminata en minutos (`TRANSFERENCIA`).
- [x] **Op 8: Consultar todas las líneas que pasan por una estación**: Panel lateral con tabla sincronizada en tiempo real que lista cada línea concurrente, su número de parada en la secuencia, tipo de servicio y badge con el color oficial MTA.
- [x] **Op 9: Consultar todas las estaciones de una línea en el orden correcto**: Pestaña dedicada con selector de línea, visualización en tabla del recorrido completo ordenado de origen a fin, distancias parciales y tiempos acumulados.

---

### [COMPLETADO] Módulo 2: Rutas y Horarios (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m2_routes_interface.py` y `prototypes/desktop/services/m2_routes_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con los 9 requerimientos oficiales del enunciado:

- [x] **Op 1: Crear, modificar y eliminar rutas locales y expresas asociadas a una línea**: Diálogo modal `RutaDialog` (`m2_routes_service.crear_ruta`, `m2_routes_service.modificar_ruta`) para parametrizar código, línea troncal, estaciones terminales origen/destino, distancia total en km, duración estimada en minutos y estado operativo con conmutación en caliente (`'Activa'`, `'Cerrada Temporalmente'`). Incluye botón **"Eliminar Ruta"** con eliminación atómica en cascada (`m2_routes_service.eliminar_ruta`) de paradas, horarios, viajes e incidentes asociados previa confirmación detallando recuentos de dependencias (`m2_routes_service.get_dependencias_ruta`), y filtro dinámico por línea conectado a recarga reactiva (`refresh_rutas`).
- [x] **Op 2: Establecer el sentido del recorrido**: Selectores validados para sentido de marcha (`Norte-Sur`, `Sur-Norte`, `Uptown`, `Downtown`, `Este-Oeste`, `Oeste-Este`) y tipo de servicio comercial (`Local`, `Expreso`).
- [x] **Op 3: Definir la secuencia de paradas de cada ruta**: Tabla interactiva subordinada (`RUTA_DETALLE`) con diálogo modal `ParadaRutaDialog` (`m2_routes_service.asociar_parada_ruta`, `modificar_parada_ruta`, `eliminar_parada_ruta`), permitiendo configurar orden secuencial, hora de paso, distancia, tiempo acumulado e indicando condición de parada: paradas comerciales efectivas (`SE_DETIENE = 'S'`) vs estaciones que el tren sobrepasa sin detenerse en servicios expresos (`SE_DETIENE = 'N'`).
- [x] **Op 4: Configurar y modificar horarios de operación por día de la semana**: Diálogo modal `HorarioDialog` (`m2_routes_service.crear_horario`, `modificar_horario`, `eliminar_horario`) con asignación de días (`Lunes a Viernes`, `Fin de Semana`, `Sabado`, `Domingo`, `Festivo`), franjas horarias y botón **"Modificar Horario"** con precarga completa de datos.
- [x] **Op 5: Configurar frecuencias programadas por franja horaria**: Parámetro `FRECUENCIA_MINUTOS` configurable por franja (hora inicio, hora fin) para intervalos pico matutino, valle, pico vespertino y nocturno.
- [x] **Op 6: Generar viajes programados vinculados al procedimiento almacenado canónico `SP_PROGRAMAR_VIAJE`**: Diálogo modal `ProgramarViajeDialog` (`m2_routes_service.programar_nuevo_viaje`), validando en Oracle la disponibilidad física del tren (`FN_VERIFICAR_TREN_DISPONIBLE`) y la certificación técnica vigente del maquinista asignado (`FN_VERIFICAR_LICENCIA_VIGENTE`), con priorización visual de conductores con certificación vigente en el selector.
- [x] **Op 7: Cancelar, reprogramar, modificar integralmente y eliminar viajes existentes**: Acciones directas sobre la tabla de viajes:
  - Botón **"Cancelar Viaje"** (`m2_routes_service.cancelar_viaje`).
  - Botón **"Reprogramar / Modificar"** con diálogo modal `EditarViajeDialog` (`m2_routes_service.modificar_viaje`) para editar integralmente fecha, horas programadas de salida y llegada, tren asignado (disponible o en operación), maquinista certificado, estado operativo y pasajeros estimados.
  - Botón **"Eliminar Viaje"** (`m2_routes_service.eliminar_viaje`) con confirmación modal y borrado en cascada de validaciones de torniquete (`VIAJE_PASAJERO`) y registros de afectación.
- [x] **Op 8: Consultar los próximos viajes programados que arribarán a una estación determinada**: Pestaña dedicada con selector de estación y tabla reactiva en tiempo real (`m2_routes_service.get_proximos_viajes_estacion`), mostrando código de ruta, sentido, tipo de servicio, hora programada y estado.
- [x] **Op 9: Identificar rutas y viajes afectados ante contingencias y cierres**: Panel de afectaciones activas (`m2_routes_service.get_afectaciones_activas`) y botón de despacho para invocar en cascada el procedimiento `SP_CANCELAR_VIAJES_AFECTADOS` (`m2_routes_service.cancelar_viajes_por_incidente`), protegiendo la integridad de la red.

---

### [COMPLETADO] Módulo 3: Flota, Trenes y Material Rodante (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m3_fleet_interface.py` y `prototypes/desktop/services/m3_fleet_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con los 8 requerimientos del enunciado oficial y las reglas de negocio 8, 11, 12 y 25:

- [x] **Op 1: Registrar trenes y vagones**: Diálogos modales `TrenDialog` y `VagonDialog` para gestión integral CRUD con validación de dominios, unicidad de código/serie, año de fabricación y sincronización automática de activos en la tabla `EQUIPO`.
- [x] **Op 2: Armar la composición de un tren**: Panel interactivo de formación activa (`TREN_VAGON`) con diálogo `AcoplarVagonDialog`, permitiendo incorporar vagones disponibles en posiciones secuenciales (`POSICION = 1, 2, 3...`), reordenar posiciones con botones reactivos Subir/Bajar y recálculo automático dinámico de `CAPACIDAD_TOTAL` en `TREN` sumando las capacidades de los vagones acoplados.
- [x] **Op 3: Conservar el historial completo de vagones asignados (Regla de negocio 25)**: Pestaña dedicada *Historial de Composición* que audita cada asociación activa e histórica. El desacoplamiento nunca borra físicamente el registro: establece `FECHA_FIN = SYSDATE`, renombra las posiciones de los vagones restantes y libera el vagón al inventario en estado `'Disponible'`.
- [x] **Op 4: Cambiar el estado de un tren**: Diálogo modal `CambiarEstadoTrenDialog` para transicionar entre `'Disponible'`, `'En Operación'`, `'En Mantenimiento'`, `'Fuera de Servicio'` y `'Retirado'`, disparando en Oracle el trigger de auditoría `TRG_TREN_CAMBIO_ESTADO` que registra el cambio en la tabla `BITACORA`.
- [x] **Op 5: Consultar disponibilidad operativa en tiempo real**: Pestaña dedicada con tarjetas ejecutivas KPI y visor de diagnóstico por unidad que evalúa la función PL/SQL canónica `FN_TREN_DISPONIBLE`, órdenes de trabajo activas en `ORDEN_MANTENIMIENTO` y detección automática de inspecciones técnicas de seguridad vencidas (`FECHA_PROXIMA_INSPECCION < SYSDATE`).
- [x] **Op 6: Asignar un tren a un viaje programado**: Diálogo modal `AsignarTrenViajeDialog` y botón de desasignación en la tabla de viajes de la flota, sincronizado con `VIAJE_PROGRAMADO`.
- [x] **Op 7: Impedir asignaciones simultáneas solapadas (Regla de negocio 8)**: Validación rigurosa a nivel de servicio y base de datos que detecta y rechaza cualquier intento de asignar un mismo tren a dos viajes cuyos intervalos de salida y llegada se superpongan en la misma fecha.
- [x] **Op 8: Impedir el uso de trenes en mantenimiento o fuera de servicio (Regla de negocio 11)**: Control estricto previo y cumplimiento del trigger de base de datos `TRG_TREN_MANTENIMIENTO_NO_ASIGNAR`, impidiendo que trenes en taller o retirados sean asignados a servicios de pasajeros.
- [x] **Regla de negocio 12: Unicidad de vagón en trenes**: El acoplamiento bloquea automáticamente cualquier intento de asignar un vagón que ya se encuentre acoplado a otra unidad activa.

---

### [COMPLETADO] Módulo 4: Personal Operativo y Turnos (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m4_staff_interface.py` y `prototypes/desktop/services/m4_staff_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con los 8 requerimientos del enunciado oficial y las reglas de negocio 9 y 10:

- [x] **Op 1: Registrar empleados (altas, modificaciones, datos contractuales, salarios)**: Diálogo modal `EmpleadoDialog` (`m4_staff_service.crear_empleado`, `modificar_empleado`, `cambiar_estado_laboral`, `eliminar_empleado`) para gestionar número de nómina, nombre completo, fecha de nacimiento, contacto, cargo, salario, turno habitual y estado laboral (`'Activo'`, `'Permiso'`, `'Vacaciones'`, `'Suspendido'`, `'Retirado'`).
- [x] **Op 2: Asignar cargos y estructura jerárquica de supervisión**: Asignación interactiva de supervisores directos (`SUPERVISOR_ID`), validación de integridad para evitar auto-supervisión (`id_empleado != supervisor_id`), visualización de jerarquía en tabla maestra y consulta de subordinados directos (`get_subordinados`).
- [x] **Op 3: Registrar certificaciones técnicas asociadas a modelos de tren (`CERTIFICACION_MODELO`)**: Diálogo modal `CertificacionDialog` (`m4_staff_service.crear_certificacion`, `modificar_certificacion`, `eliminar_certificacion`) con selección multi-modelo de tren (R142, R160, etc.) persistidos en `CERTIFICACION_MODELO`, agregación de modelos con `LISTAGG` y conteo de días restantes para vencimiento.
- [x] **Op 4: Programar turnos laborales**: Diálogo modal `TurnoDialog` (`m4_staff_service.crear_turno`, `modificar_turno`, `eliminar_turno`) para calendarizar fecha, intervalo horario (inicio y fin), tipo de lugar (`'Estación'`, `'Tren'`, `'Depósito'`, `'Centro de Control'`, `'Ruta'`), función operativa y código de turno autogenerado (`TUR-XXXXXX`).
- [x] **Op 5: Asignar conductores a viajes programados (Reglas de negocio 9 y 10)**: Diálogo modal `AsignarConductorViajeDialog` y botón de desasignación (`m4_staff_service.asignar_conductor_viaje`, `desasignar_conductor_viaje`). Filtra conductores disponibles garantizando certificación técnica vigente para la fecha del viaje (Regla 10 y trigger `TRG_CERTIFICACION_ALERTA_VENCIDA`) e impidiendo solapamiento horario con otro viaje simultáneo (Regla 9).
- [x] **Op 6: Controlar y auditar el vencimiento de certificaciones técnicas**: Botón de auditoría y función en lote `controlar_vencimientos_certificaciones` que detecta licencias caducadas (`fecha_vencimiento < SYSDATE`) y actualiza automáticamente su estado a `'Vencida'`.
- [x] **Op 7: Detectar e impedir traslapes de turnos laborales**: Algoritmo predictivo en `validar_traslape_turno` (`t.hora_inicio < :nueva_fin AND t.hora_fin > :nueva_inicio`) que bloquea la creación o modificación de turnos solapados para un mismo empleado en la misma fecha, complementado con auditoría analítica global del sistema (`detectar_traslapes_turnos`).
- [x] **Op 8: Registrar ausencias y gestionar sustituciones de personal operativo**: Diálogos modales `AsistenciaDialog` y `SustitucionDialog` (`m4_staff_service.registrar_asistencia`, `registrar_sustitucion`) para actualizar estados (`'Presente'`, `'Ausente'`, `'Permiso'`, `'Vacaciones'`) y reemplazar personal operativo marcando el turno como `'Sustituido'` y creando un nuevo turno oficial para el sustituto validando que esté `'Activo'` y libre de traslapes.

---

### [COMPLETADO] Módulo 5: Pasajeros, Tarjetas OMNY y Torniquetes (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m5_cards_interface.py` y `prototypes/desktop/services/m5_cards_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con los 10 requerimientos del enunciado oficial y las reglas de negocio 13, 14, 15, 16, 17, 18, 21 y 25:

- [x] **Op 1: Registrar y modificar pasajeros frecuentes**: Diálogo modal `PasajeroDialog` (`m5_cards_service.crear_pasajero`, `modificar_pasajero`, `cambiar_estado_pasajero`, `eliminar_pasajero`) para gestionar datos demográficos, identificadores y perfiles oficiales (`'Adulto Mayor'`, `'Empleado Autorizado'`, `'Estudiante'`, `'Persona con Discapacidad'`, `'Regular'`).
- [x] **Op 2: Emitir tarjetas nominales y anónimas (Regla de negocio 13)**: Diálogo modal `EmitirTarjetaDialog` (`m5_cards_service.emitir_tarjeta`, `modificar_tarjeta`) para crear tarjetas físicas/virtuales asignadas a pasajeros registrados o tarjetas anónimas/al portador (`PASAJERO_ID = NULL`) con saldo inicial no negativo (Regla 15).
- [x] **Op 3: Recargar saldo de tarjetas (Regla de negocio 14)**: Panel interactivo con montos rápidos (+$5, +$10, +$20, +$50), selector de medios de pago y ejecución del procedimiento almacenado canónico `SP_RECARGAR_TARJETA` (`m5_cards_service.recargar_tarjeta`), actualizando atómicamente el saldo y registrando la transacción en `RECARGA`.
- [x] **Op 4: Bloquear y gestionar el ciclo de vida de las tarjetas (Regla de negocio 16)**: Diálogo modal `BloquearTarjetaDialog` (`m5_cards_service.cambiar_estado_tarjeta`) para alternar estados (`'Activa'`, `'Bloqueada'`, `'Reportada Perdida'`, `'Cancelada'`, `'Vencida'`), impidiendo el acceso en torniquetes ante cualquier estado no activo o caducidad temporal.
- [x] **Op 5: Simulación de paso por torniquete y validación de acceso (Regla de negocio 21)**: Selector de estación y tarjeta con invocación al procedimiento almacenado canónico `SP_REGISTRAR_INGRESO` (`m5_cards_service.validar_ingreso_torniquete`), comprobando en caliente que la estación esté operativa y rechazando accesos en estaciones con estado `'Cerrada Temporalmente'`.
- [x] **Op 6: Cobro de tarifa y registro histórico en `VIAJE_PASAJERO` (Reglas de negocio 17 y 18)**: Descuento exacto de la tarifa según el perfil del usuario ($2.90 base, $1.45 reducida, $0.00 escolar) y persistencia inmutable del monto efectivamente cobrado en `VIAJE_PASAJERO.MONTO_COBRADO`.
- [x] **Op 7: Consulta de saldo en tiempo real (Regla de negocio 15)**: Tarjeta gráfica fotorrealista `VisualOmnyCard` con diseño MTA Blue, tipografía contactless OMNY y balance interactivo con código de color (verde activo, rojo bloqueado, amarillo vencido).
- [x] **Op 8: Historiales de viajes y recargas (Regla de negocio 25)**: Pestaña subordinada con tablas dedicadas para auditoría de validaciones en torniquete y recargas monetarias. Bloqueo estricto de eliminación física (`m5_cards_service.eliminar_tarjeta`) de tarjetas con transacciones históricas.
- [x] **Op 9: Registro de viajes anónimos**: Botón de acceso directo en torniquete que valida ingresos contactless EMV o con tarjetas anónimas sin requerir registro previo de pasajero.
- [x] **Op 10: Detección automática de tarjetas sin saldo o vencidas**: Validación predictiva y rechazo inmediato en torniquete con mensajes claros de saldo insuficiente o fecha de vencimiento expirada.
- [x] **Op 11: Catálogo de tarifas y regla de Fare Capping de la MTA**: Pestaña dedicada con visor y editor de tarifas (`TARIFA`), y panel explicativo del tope tarifario semanal OMNY (máximo $34.00 / 12 viajes en ciclo lunes a domingo).

---

### [COMPLETADO] Módulo 6: Mantenimiento (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m6_maintenance_interface.py` y `prototypes/desktop/services/m6_maintenance_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con los 9 requerimientos del enunciado oficial y las reglas de negocio 19 y 25:

- [x] **Op 1: Registro de equipos e infraestructura (`EQUIPO`)**: Catálogo integral de activos clasificados por tipo (`'Vía'`, `'Señal'`, `'Plataforma'`, `'Elevador'`, `'Escalera Eléctrica'`, `'Tren'`, `'Vagón'`), referencias polimórficas (`'ESTACION'`, `'PLATAFORMA'`, `'TREN'`, `'VAGON'`, `'NINGUNO'`), números de serie, fabricantes y control de fechas de instalación. Diálogos modales `EquipoDialog` con alta, edición y eliminación validada.
- [x] **Op 2: Generación de órdenes de mantenimiento vinculadas a `SP_CREAR_ORDEN_MANTENIMIENTO`**: Diálogo modal `NuevaOrdenDialog` que ejecuta el procedimiento almacenado canónico de Oracle generando la numeración `ORD-YYYY-XXXX`, asociando técnico líder, colocando la orden `'En Ejecución'` y actualizando automáticamente el estado del equipo y del tren asociado a `'En Mantenimiento'`.
- [x] **Op 3: Asignación de cuadrillas y técnicos (`ORDEN_TECNICO`)**: Asignación de múltiples técnicos especializados (`EMPLEADO.cargo = 'Técnico de Mantenimiento'`) a las órdenes de trabajo con asignación de roles (`'Líder de Reparación'`, `'Técnico Mecánico Principal'`, `'Técnico Especialista'`, `'Inspector de Vía y Señales'`), cumplimiento estricto de la restricción `UK_ORDEN_TECNICO_1`, y panel de carga activa de cuadrillas (Consulta 15).
- [x] **Op 4: Catálogo y consumo de repuestos con cálculo de costos (`REPUESTO` y `ORDEN_REPUESTO`)**: Catálogo administrativo de piezas con costo unitario y registro de consumo de repuestos en órdenes de trabajo. Cálculo de costos parciales e integración con la función canónica de Oracle `FN_COSTO_ORDEN_MANTENIMIENTO(p_id_orden)` para calcular el costo total consolidado (base + repuestos).
- [x] **Op 5: Gestión del ciclo de vida de las órdenes**: Transición controlada entre estados (`'Solicitada'`, `'Programada'`, `'En Ejecución'`, `'Suspendida'`, `'Completada'`, `'Cancelada'`). Diálogo modal `CambiarEstadoOrdenDialog` y diálogo de finalización formal `CompletarOrdenDialog`.
- [x] **Op 6: Actualización automática de última revisión y reprogramación de inspección**: Al completar formalmente una orden de trabajo, se registra `fecha_finalizacion`, se actualiza `fecha_ultima_revision = SYSDATE` y se programa automáticamente `fecha_proxima_revision = SYSDATE + N` días en `EQUIPO` (y en `TREN` si aplica).
- [x] **Op 7: Restauración automática de disponibilidad de activos y trenes**: Al finalizar o cancelar una orden de trabajo, si no restan órdenes activas para ese equipo, su estado en `EQUIPO` se restaura atómicamente a `'Disponible'` y, si se trata de un tren, su estado en `TREN.estado_operativo` regresa a `'Disponible'`.
- [x] **Op 8: Bloqueo estricto de trenes en mantenimiento en programación de viajes (Regla de negocio 19)**: Verificado mediante el trigger `TRG_TREN_MANTENIMIENTO_NO_ASIGNAR` en Oracle y validaciones en la capa de servicios, impidiendo despachos o asignaciones a viajes de trenes que se encuentren en taller.
- [x] **Op 9: Monitoreo de material en taller, equipos fuera de servicio y auditoría histórica (Regla de negocio 25)**: Pestaña subordinada de alertas con vista en tiempo real de trenes en taller (`VW_TRENES_MANTENIMIENTO`), inventario de equipos fuera de servicio, detección predictiva de inspecciones de seguridad vencidas y bloqueo de borrado de equipos con órdenes históricas.

---

### [COMPLETADO] Módulo 7: Incidentes Operativos (COMPLETADO AL 100%)
> **Ubicación en código**: `prototypes/desktop/views/m7_incidents_interface.py` y `prototypes/desktop/services/m7_incidents_service.py`.  
> **Estado**: **100% IMPLEMENTADO Y VERIFICADO**. Cumple estrictamente con los 7 requerimientos del enunciado oficial y las reglas de integridad de la base de datos:

- [x] **Op 1: Registro de incidencias con tipología estandarizada y severidad**: Diálogo modal `RegistrarIncidenteDialog` conectado a `SP_REGISTRAR_INCIDENTE`, generando la numeración oficial `INC-YYYYMMDD-XXXX` y clasificando por tipo oficial (`CK_INCIDENTE_TIPO`) y severidad (`'Bajo'`, `'Medio'`, `'Alto'`, `'Crítico'`).
- [x] **Op 2: Asociación de elementos de red con integridad de Arco Exclusivo (`CK_INCIDENTE_ELEMENTO_ARCO`)**: Soporte completo para vincular estaciones, trenes, rutas, líneas, equipos de infraestructura y viajes programados (`INCIDENTE_ELEMENTO_AFECTADO`), garantizando que exactamente una sola clave foránea sea poblada por registro y rechazando cualquier violación a nivel de base de datos.
- [x] **Op 3: Gestión del ciclo de vida y resolución técnica de incidentes**: Transición entre estados (`'Abierto'`, `'En Atención'`, `'Cerrado'`), diálogo modal `CerrarIncidenteDialog` para consignar causa raíz identificada (`causa_identificada`), bitácora de intervenciones (`acciones_realizadas`), pasajeros estimados impactados y cálculo exacto de la duración en minutos/horas.
- [x] **Op 4: Despacho automático de cancelaciones con `SP_CANCELAR_VIAJES_AFECTADOS`**: Enlace interactivo y por procedimiento canónico para suspender masivamente todos los viajes programados que intersecten con las estaciones, rutas o líneas declaradas como afectadas por la contingencia.
- [x] **Op 5: Auditoría operativa en tiempo real con `BITACORA`**: Pestaña dedicada para consultar la bitácora institucional alimentada automáticamente por el trigger de Oracle `TRG_INCIDENTE_AUDITORIA` ante cada alta (`INSERT`) y modificación/cierre (`UPDATE`) de contingencias.
- [x] **Op 6: Simulación y previsualización de impacto en viajes**: Visualizador en tiempo real de viajes en riesgo o potencialmente impactados antes y después de ejecutar la orden de cancelación.
- [x] **Op 7: Panel de métricas y analítica de red**: Agregación estadística de contingencias por nivel de severidad, tipología técnica más recurrente y estado operativo de resolución.

---

## 4. Las 15 Consultas Mínimas Obligatorias (Dinámicas)

Cada consulta cuenta con **parámetros configurables en tiempo real** en la interfaz y previsualización SQL:

1. **Líneas por estación** : Selector de estación (`ESTACION`) o `(Todas)`.
2. **Paradas secuenciales de una ruta** : Selector de código de ruta (`RUTA`) o `(Todas)`.
3. **Estaciones de transferencia** : Filtro por distrito (Manhattan, Brooklyn, Queens, Bronx o Todos).
4. **Viajes por fecha** : Selector de fecha (`YYYY-MM-DD`).
5. **Retrasos mayores a umbral** : Umbral configurable de demora en minutos (por defecto 15).
6. **Disponibilidad de trenes** : Filtro por estado operativo (`Disponible`, `En Mantenimiento`, etc.).
7. **Trenes con inspección vencida o en taller** : Filtro por condición técnica requerida.
8. **Asignación de conductor y licencia** : Búsqueda por nombre o número de empleado.
9. **Pasajeros por línea** : Cálculo de afluencia acumulada en toda la red.
10. **Recaudación por torniquete y estación** : Filtro por estación específica (`ESTACION`) o todas.
11. **Estaciones con mayor afluencia** : Límite configurable (Top N estaciones).
12. **Incidentes abiertos** : Filtro por severidad (Bajo, Medio, Alto, Crítico o Todas).
13. **Líneas con más retrasos acumulados** : Sumatoria de minutos perdidos por demoras operativas.
14. **Tarjetas OMNY bloqueadas o vencidas** : Filtro por estado de tarjeta.
15. **Técnicos en órdenes de mantenimiento** : Selector por número de orden (`ORDEN_MANTENIMIENTO`).

---

## 5. Historial de Hitos y Correcciones Clave

- [x] **Modularización de la app de escritorio** : Separación del script monolítico en módulos desacoplados bajo `prototypes/desktop/`.
- [x] **Aislamiento del selector de pestañas en FluentWindow** : Botones de acción reubicados en `titleBar.hBoxLayout`.
- [x] **Corrección ORA-00904** : Corrección del campo `TURNO_HABITUAL` en la tabla `EMPLEADO`.
- [x] **Threading asíncrono** : Implementación de `QueryWorker(QThread)` para mantener 60 FPS estables.
- [x] **Parámetros dinámicos en las 15 consultas** : Eliminación de consultas fijas; ahora soportan entradas interactivas del usuario con SQL preview reactivo.
- [x] **Investigación Operativa MTA** : Documentación completa en español guardada en `docs/investigacion_operaciones_mta.md` con el análisis de divisiones A/B, OMNY, mantenimiento SMS y gestión de incidentes.
- [x] **Fase 1: Capa de Programación PL/SQL y Reorganización Canónica de Base de Datos** :
  - Reorganización modular del directorio `database/` en tres subdirectorios (`01_setup/`, `02_plsql/`, `03_pruebas/`).
  - Creación de dos scripts de ejecución autónomos con autodetección de PDB: `dbconfigurar.bat` (instalación base) y `dbprogramar.bat` (lógica PL/SQL), con sus equivalentes para Linux/macOS (`.sh`).
  - Implementación y compilación en Oracle 23ai (`FREEPDB1`): 9 Vistas (`VW_*`), 9 Funciones (`FN_*`), 6 Procedimientos (`SP_*`) y 8 Triggers (`TRG_*`).
  - Verificación estricta: **0 errores de compilación** (`user_errors` vacío) y todos los 32 objetos en estado `VALID`.
  - Script de pruebas funcionales automatizadas `database/03_pruebas/test_plsql_verificacion.sql` con rollback seguro.
- [x] **Fase 2: Capa de Servicios y Acciones en Desktop (`prototypes/desktop/services/actions_service.py`)** :
  - Creación de la capa de enlace Python para invocar nativamente mediante `oracledb` los 6 Procedimientos Almacenados (`SP_PROGRAMAR_VIAJE`, `SP_REGISTRAR_INGRESO`, `SP_RECARGAR_TARJETA`, `SP_CREAR_ORDEN_MANTENIMIENTO`, `SP_REGISTRAR_INCIDENTE`, `SP_CANCELAR_VIAJES_AFECTADOS`).
  - Implementación de wrappers para las Funciones PL/SQL y parser robusto de errores de Oracle (`parse_oracle_error`) para capturar y humanizar excepciones `ORA-20xxx`.
- [x] **Fase 3: Documentación Académica y Técnica en `docs/`** :
  - `docs/caratula_y_planificacion.md`: Carátula formal institucional con el padrón de los 7 estudiantes del equipo y matriz de asignación de responsabilidades RACI.
  - `docs/diccionario_datos.md`: Diccionario de datos institucional exhaustivo de las 33 tablas y más de 270 restricciones.
  - `docs/normalizacion_3nf.md`: Dictamen formal de normalización hasta 3NF con demostraciones matemáticas.
  - `docs/modelo_entidad_relacion.md`: Modelo conceptual Barker CDM y diagramas Mermaid modulares.
  - `docs/guia_sistema_usuario.md`: Manual de usuario y guía operativa ilustrada de las vistas de escritorio.
- [x] **Fase 4: Módulo 1 Desktop - Administración Integral de la Red (`m1_stations_interface.py` & `m1_network_service.py`)** :
  - Implementación integral de las 9 operaciones exigidas por el enunciado con diálogos modales Fluent y persistencia directa en Oracle.
- [x] **Fase 5: Calidad de Código y Skill `pyqt-pylance-guardian`** :
  - Investigación y resolución de todas las advertencias Pylance/Pyright en PyQt5 y QFluentWidgets.
  - Creación de la skill con scanner déterminista `.agents/skills/pyqt-pylance-guardian/scripts/check_pyqt_pylance.py`.
  - 100% de los archivos de escritorio validados con 0 errores.
- [x] **Fase 6: Estandarización de Nomenclatura Modular (`mX_`) en Vistas y Servicios** :
  - Renombrado de vistas con prefijo de módulo: `m1_stations_interface.py`, `m3_fleet_interface.py`, `m4_staff_interface.py`, `m5_cards_interface.py`, `m7_incidents_interface.py`.
  - Renombrado del servicio de red a `m1_network_service.py` con stub de compatibilidad.
  - Actualización de imports en `main_window.py` y sincronización completa en toda la documentación (`README.md`, `guia_sistema_usuario.md`, `caratula_y_planificacion.md`, `investigacion_operaciones_mta.md`).
