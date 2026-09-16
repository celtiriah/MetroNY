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
│   │       ├── m3_fleet_interface.py   # MÓDULO 3: Flota y material rodante
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

### [PENDIENTE] Módulo 3: Trenes y Material Rodante (PENDIENTE DE IMPLEMENTACIÓN)
> **Requerimientos del Enunciado**:
- [ ] Registrar trenes (código, modelo R142/R160/R179/R211, fabricante, año, capacidad total, depósito asignado).
- [ ] Registrar vagones individuales (número de serie, tipo, capacidad sentados/de pie, accesibilidad).
- [ ] Armar la composición de un tren asignando vagones en posiciones secuenciales.
- [ ] Conservar el historial completo de asignaciones de vagones a trenes en el tiempo.
- [ ] Modificar el estado operativo de un tren (Disponible, En Operación, En Mantenimiento, Fuera de Servicio, Retirado).
- [ ] Consultar la disponibilidad de trenes en tiempo real mediante `FN_VERIFICAR_TREN_DISPONIBLE`.
- [ ] Asignar trenes a viajes específicos impidiendo asignaciones simultáneas (Regla de negocio 8).
- [ ] Bloquear automáticamente la asignación de trenes en estado de mantenimiento o con inspección técnica vencida (Regla de negocio 11).

---

### [PENDIENTE] Módulo 4: Personal Operativo (PENDIENTE DE IMPLEMENTACIÓN)
> **Requerimientos del Enunciado**:
- [ ] Registrar empleados (número, nombre, fecha nacimiento, contacto, cargo, salario, fecha de contratación).
- [ ] Asignar estructura jerárquica de supervisión (empleado - supervisor).
- [ ] Registrar certificaciones técnicas de conducción asociadas a modelos específicos de tren con fecha de emisión y vencimiento.
- [ ] Programar turnos de trabajo asignados a estaciones, trenes, depósitos o centros de control.
- [ ] Asignar conductores a viajes programados verificando licencia vigente mediante `FN_VERIFICAR_LICENCIA_VIGENTE`.
- [ ] Controlar alertas de vencimiento de certificaciones.
- [ ] Detectar e impedir traslapes de turnos o asignación de conductores a viajes simultáneos (Reglas de negocio 9 y 10).
- [ ] Registrar ausencias, permisos, licencias médicas y sustituciones de personal.

---

### [PROTOTIPADO PARCIAL] Módulo 5: Pasajeros y Tarjetas OMNY (PROTOTIPADO PARCIAL / PENDIENTE DE FORMALIZACIÓN)
> **Estado Actual**: Contamos con la vista interactiva `m5_cards_interface.py` que incluye la tarjeta OMNY visual, el simulador de validación en torniquete ($2.90) con invocación directa a `SP_REGISTRAR_INGRESO`, recargas exprés con `SP_RECARGAR_TARJETA` y visor de historiales.  
> **Requerimientos pendientes para completar el módulo al 100%**:
- [x] Recarga de saldo con actualización de balance y auditoría (`SP_RECARGAR_TARJETA`).
- [x] Registro y cobro de viaje en torniquete con deducción de tarifa (`SP_REGISTRAR_INGRESO`).
- [x] Detección reactiva de tarjetas bloqueadas, vencidas o sin saldo.
- [x] Consulta de saldo y visualización de historiales de validación y recarga.
- [ ] Registro formal de pasajeros frecuentes con datos demográficos y tipo (Regular, Estudiante, Adulto Mayor, Discapacidad).
- [ ] Diálogo de emisión de nuevas tarjetas electrónicas nominales o anónimas.
- [ ] Gestión administrativa del ciclo de vida de la tarjeta (activar, bloquear por extravío, cancelar).
- [ ] Catálogo de tarifas con fechas de vigencia y tipos de producto (pase diario, semanal, mensual).

---

### [PENDIENTE] Módulo 6: Mantenimiento (PENDIENTE DE IMPLEMENTACIÓN)
> **Requerimientos del Enunciado**:
- [ ] Registrar equipos de infraestructura (vías, señales, andenes, elevadores, escaleras eléctricas, subestaciones).
- [ ] Generar órdenes de mantenimiento preventivo, correctivo, predictivo o inspección técnica vinculadas a `SP_CREAR_ORDEN_MANTENIMIENTO`.
- [ ] Asignación de técnicos responsables y cuadrillas a las órdenes de trabajo.
- [ ] Registrar repuestos utilizados en cada intervención con cantidades y costos unitarios.
- [ ] Gestionar el ciclo de estados de la orden (Solicitada, Programada, En Ejecución, Suspendida, Completada, Cancelada).
- [ ] Actualizar automáticamente la fecha de última revisión y calcular la fecha de próxima inspección obligatoria.
- [ ] Consultar equipos fuera de servicio y alertas de mantenimientos preventivos vencidos.

---

### [PENDIENTE] Módulo 7: Incidentes Operativos (PENDIENTE DE IMPLEMENTACIÓN)
> **Requerimientos del Enunciado**:
- [ ] Registrar incidencias operativas con tipología estandarizada (falla mecánica, eléctrica, señalización, médica, seguridad, clima, etc.).
- [ ] Clasificar incidentes por nivel de severidad (Bajo, Medio, Alto, Crítico).
- [ ] Asociar incidentes con los elementos de red afectados respetando la contrainte de **Arco Exclusivo** (estación, tren, ruta, equipo).
- [ ] Enlace con `SP_CANCELAR_VIAJES_AFECTADOS` para suspender automáticamente viajes que crucen por el sector impactado.
- [ ] Registrar bitácora de acciones correctivas y resolución técnica.
- [ ] Procedimiento de cierre de incidentes con cálculo exacto de la duración del evento.
- [ ] Panel de consulta de incidentes activos y métricas estadísticas por línea y estación.

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
