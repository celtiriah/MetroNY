# Estado del Proyecto y Memoria Compartida: Metro NY (MTA NYCT)

> **Documento de Sincronización Inter-Entornos y Multi-Agente**  
> Esta bitácora sirve como memoria centralizada y fuente única de verdad para agentes de IA (Antigravity IDE, Antigravity 2.0, VS Code, Claude, Codex) y desarrolladores del equipo.

---

## 1. Contexto del Proyecto, Especificaciones y Reglas Obligatorias

- **Idioma Obligatorio** : **Todos los archivos, documentación, scripts y código del proyecto deben redactarse y mantenerse en ESPAÑOL**, dado que el curso y la evaluación académica se imparten en este idioma.
- **Enunciado y Requerimientos** : [docs/Enunciado - Proyecto_ Sistema de Gestión del Metro de Nueva York.md](docs/Enunciado%20-%20Proyecto_%20Sistema%20de%20Gesti%C3%B3n%20del%20Metro%20de%20Nueva%20York.md).
- **Investigación Operativa MTA** : [docs/investigacion_operaciones_mta.md](docs/investigacion_operaciones_mta.md) (detalles de gálibo División A vs B, vías cuádruples expresas/locales, peaje OMNY con tope de 7 días, mantenimiento SMS en Coney Island/207th St, y contingencias 24/7).
- **Plan de Implementación Activo** : [implementation_plan.md](implementation_plan.md).
- **Base de Datos** : Oracle Database 23ai local (`FREEPDB1`, fallback `XEPDB1`), puerto `1521`, esquema `METRO_NY` / `MetroPass123`.
- **Propósito del Directorio `database/`** : Contiene los scripts DDL y DML canónicos (`01` a `08`) para la **configuración inicial y homogénea de la base de datos** en los ordenadores de todos los integrantes del equipo mediante `dbsetup.bat` y `dbsetup.sh`. Todos los objetos de base de datos (tablas, datos, índices, vistas, funciones, procedimientos y triggers) deben versionarse aquí para garantizar que cualquier miembro del equipo levante exactamente la misma base de datos con un solo clic.
- **Prioridad de Desarrollo** : La prioridad absoluta del desarrollo se concentra en la aplicación de escritorio nativa en `prototypes/desktop/`.
- **Regla Estricta de Git** : **JAMÁS ejecutar `git commit` ni `git push` automáticamente**. Todos los cambios deben permanecer sin preparar (unstaged) para que el usuario los revise y realice los commits manualmente.
- **Estándar de Diseño UI** : Windows 11 Fluent Design System guiado por la skill `fluent-design` (`~/.gemini/config/skills/fluent-design/SKILL.md`).

---

## 2. Arquitectura Técnica del Código

```text
MetroNY/
├── PROJECT_STATE.md             # Esta bitácora de memoria compartida (en español)
├── implementation_plan.md       # Plan maestro de implementación detallado
│
├── database/                    # SCRIPTS CANÓNICOS Y MODULARES DE BASE DE DATOS
│   ├── dbconfigurar.bat / .sh   # [Paso 1] Instalación de esquema, 33 tablas, 208 datos y 63 índices
│   ├── dbprogramar.bat / .sh    # [Paso 2] Compilación de la lógica PL/SQL (Vistas, Funciones, SPs, Triggers)
│   ├── get_pdb.sql              # Script SQL de autodetección del servicio PDB activo (FREEPDB1)
│   │
│   ├── 01_setup/                # [Módulo 1: Setup e Infraestructura Base]
│   │   ├── 01_configuracion_usuario.ddl # Tablespaces y usuario METRO_NY
│   │   ├── 02_ddl_tablas.ddl    # 33 tablas normalizadas en 3NF con constraints
│   │   ├── 03_datos_prueba.ddl  # 208 registros con datos reales del metro de NY
│   │   └── 04_indices.ddl       # 63 índices B-Tree de optimización
│   │
│   ├── 02_plsql/                # [Módulo 2: Capa de Negocio y Automatización PL/SQL]
│   │   ├── 05_vistas.sql        # 9 vistas analíticas y operativas (VW_*)
│   │   ├── 06_funciones.sql     # 9 funciones de cálculo de negocio (FN_*)
│   │   ├── 07_procedimientos.sql# 6 procedimientos almacenados transaccionales (SP_*)
│   │   └── 08_triggers.sql      # 8 triggers de integridad, auditoría y bitácora (TRG_*)
│   │
│   └── 03_pruebas/              # [Módulo 3: Validación y Pruebas del Sistema]
│       ├── prueba_15_consultas.sql     # Las 15 consultas mínimas obligatorias
│       └── test_plsql_verificacion.sql # Verificación funcional de vistas, funciones, SPs y triggers
│
├── docs/                        # Documentación académica y técnica (siempre en español)
│   ├── Enunciado - Proyecto...  # Especificación oficial de la cátedra
│   ├── investigacion_operaciones_mta.md # Estudio técnico del metro de NY (Div A/B, OMNY, SMS)
│   └── [próximos: diccionario de datos, normalización 3NF, guía del sistema, carátula]
│
├── prototypes/
│   ├── desktop/                 # FOCO PRINCIPAL: App de escritorio nativa (Python 3.14 + PyQt5 + QFluentWidgets)
│   │   ├── main.py              # Punto de entrada principal (High-DPI y loop de eventos Qt)
│   │   ├── config.py            # Credenciales Oracle, PDBs, dimensiones y colores oficiales MTA
│   │   ├── app.py               # Lanzador puente para retrocompatibilidad
│   │   ├── db.py                # Puente hacia services/db.py
│   │   ├── styles.py            # Hojas de estilo QSS para temas Claro y Oscuro
│   │   │
│   │   ├── services/            # Capa de lógica y acceso a datos (Python puro)
│   │   │   ├── db.py            # Conexión oracledb con fallback multi-PDB
│   │   │   ├── metro_service.py # Servicios de dominio (KPIs, líneas, estaciones, flota, personal)
│   │   │   ├── actions_service.py # Servicio de SPs, funciones y acciones transaccionales en Oracle
│   │   │   └── queries_catalog.py # Catálogo de 15 consultas dinámicas obligatorias
│   │   │
│   │   ├── workers/             # Hilos de ejecución en segundo plano (Threading)
│   │   │   └── query_worker.py  # QThread asíncrono para mantener 60 FPS fluidos
│   │   │
│   │   ├── components/          # Widgets Fluent reutilizables (StatCard, StatusCard)
│   │   │
│   │   └── views/               # Interfaces / Pantallas Fluent
│   │       ├── main_window.py          # Ventana principal FluentWindow (navegación y título)
│   │       ├── dashboard_interface.py  # Panel General (resumen en vivo, 6 KPIs, líneas)
│   │       ├── stations_interface.py   # Módulos 1 y 2 (directorio de estaciones, plataformas, ADA)
│   │       ├── fleet_interface.py      # Módulos 3 y 6 (flota, talleres, kilometraje, revisiones)
│   │       ├── staff_interface.py      # Módulo 4 (personal, jerarquía, turnos, certificaciones)
│   │       ├── cards_interface.py      # Módulo 5 (Pasajeros, OMNY, Recargas y Simulador Torniquete)
│   │       ├── incidents_interface.py  # Módulo 7 (incidentes activos, severidad, afectaciones)
│   │       └── queries_interface.py    # 15 Consultas Obligatorias con parámetros dinámicos
│   │
│   └── webapp/                  # Prototipo Web secundario (Flask API + HTML/CSS/JS)
```

---

## 3. Las 15 Consultas Mínimas Obligatorias (Dinámicas)

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

## 4. Historial de Cambios y Correcciones Clave

- [x] **Modularización de la app de escritorio** : Separación del script monolítico en módulos desacoplados bajo `prototypes/desktop/`.
- [x] **Aislamiento del selector de pestañas en FluentWindow** : Botones de acción reubicados en `titleBar.hBoxLayout`.
- [x] **Corrección ORA-00904** : Corrección del campo `TURNO_HABITUAL` en la tabla `EMPLEADO`.
- [x] **Threading asíncrono** : Implementación de `QueryWorker(QThread)` para mantener 60 FPS estables.
- [x] **Parámetros dinámicos en las 15 consultas** : Eliminación de consultas fijas; ahora soportan entradas interactivas del usuario con SQL preview reactivo.
- [x] **Investigación Operativa MTA** : Documentación completa en español guardada en `docs/investigacion_operaciones_mta.md` con el análisis de divisiones A/B, OMNY, mantenimiento SMS y gestión de incidentes.
- [x] **Traducción y Unificación del Plan** : [implementation_plan.md](implementation_plan.md) traducido y sincronizado en español.
- [x] **Fase 1: Capa de Programación PL/SQL y Reorganización Canónica de Base de Datos** :
  - Reorganización modular del directorio `database/` en tres subdirectorios (`01_setup/`, `02_plsql/`, `03_pruebas/`).
  - Creación de dos scripts de ejecución autónomos con autodetección de PDB: `dbconfigurar.bat` (instalación base) y `dbprogramar.bat` (lógica PL/SQL), con sus equivalentes para Linux/macOS (`.sh`).
  - Implementación y compilación en Oracle 23ai (`FREEPDB1`): 9 Vistas (`VW_*`), 9 Funciones (`FN_*`), 6 Procedimientos (`SP_*`) y 8 Triggers (`TRG_*`).
  - Verificación estricta: **0 errores de compilación** (`user_errors` vacío) y todos los 32 objetos en estado `VALID`.
  - Script de pruebas funcionales automatizadas `database/03_pruebas/test_plsql_verificacion.sql` con rollback seguro.
- [x] **Fase 2: Capa de Servicios y Acciones en Desktop (`prototypes/desktop/services/actions_service.py`)** :
  - Creación de la capa de enlace Python para invocar nativamente mediante `oracledb` los 6 Procedimientos Almacenados (`SP_PROGRAMAR_VIAJE`, `SP_REGISTRAR_INGRESO`, `SP_RECARGAR_TARJETA`, `SP_CREAR_ORDEN_MANTENIMIENTO`, `SP_REGISTRAR_INCIDENTE`, `SP_CANCELAR_VIAJES_AFECTADOS`).
  - Implementación de wrappers para las Funciones PL/SQL (`consultar_saldo_tarjeta`, `verificar_tarjeta_valida`, `verificar_tren_disponible`, `verificar_ruta_operativa`, `calcular_costo_mantenimiento`).
  - Parser robusto de errores de Oracle (`parse_oracle_error`) para capturar y humanizar excepciones `ORA-20xxx`, checks, FKs y longitudes.
  - Funciones de apoyo y lookups para ComboBoxes y consultas de tarjetas (`get_tarjetas_resumen`, `get_tarjeta_detalle`, `get_historial_viajes_tarjeta`, `get_historial_recargas_tarjeta`, `get_tarjetas_combo`, `get_estaciones_combo`, etc.).
  - Verificación automatizada con pruebas Python en vivo contra Oracle `FREEPDB1` con 100% de éxito.
- [x] **Fase 3: Módulo 5 Desktop - Pasajeros, Tarifas y Simulador de Torniquete (`prototypes/desktop/views/cards_interface.py`)** :
  - Creación de `CardsInterface` integrado a la barra lateral de navegación con icono `FIF.QRCODE`.
  - Componente visual `VisualOmnyCard`: representación de alta fidelidad de la tarjeta OMNY física con gradiente MTA Blue, chip contactless, número de tarjeta en fuente monoespaciada, nombre del titular y saldo dinámico en verde/rojo.
  - **Simulador Interactivo de Torniquete**:
    - Selector de estación operativa y tarjeta activa.
    - Botón "Validar Paso en Torniquete ($2.90)" conectado a `actions_service.registrar_ingreso` (`SP_REGISTRAR_INGRESO`).
    - Feedback animado mediante `InfoBar`: éxito (verde) con deducción de tarifa, advertencia de saldo insuficiente y error de tarjeta inhabilitada.
    - Actualización reactiva instantánea del saldo en la tarjeta visual, la tabla general y el historial de viajes.
  - **Recarga de Saldo Express**:
    - Selector de monto con botones rápidos (+$5, +$10, +$20, +$50) y `DoubleSpinBox`.
    - Selector de medio de pago conforme a restricciones de BD.
    - Ejecución de `actions_service.recargar_tarjeta` (`SP_RECARGAR_TARJETA`) con recibo de transacción.
  - **Directorio de Tarjetas e Historiales**:
    - Filtro reactivo por estado de tarjeta (`(Todos)`, `Activa`, `Bloqueada`, `Vencida`, `Cancelada`).
    - Tabla sincronizada bidireccionalmente con el simulador al hacer clic en cualquier fila.
    - Pestañas con `SegmentedWidget` para alternar entre el Historial de Validaciones en Torniquete y el Historial de Recargas en tiempo real.
- [x] **Fase 4: Acciones Interactivas en Vistas Existentes (`fleet_interface.py` e `incidents_interface.py`)** :
  - **Módulo de Incidentes (`incidents_interface.py`)**:
    - Implementación del diálogo modal Fluent `RegistrarIncidenteDialog(MessageBoxBase)` con selectores dinámicos dependientes según el tipo de elemento de red (Estación, Tren, Ruta, Línea), severidad, causa y reportante. Conectado a `SP_REGISTRAR_INCIDENTE`.
    - Acción de despacho para cancelar viajes afectados (`SP_CANCELAR_VIAJES_AFECTADOS`) al seleccionar cualquier incidente de la tabla.
  - **Módulo de Flota (`fleet_interface.py`)**:
    - Implementación del diálogo modal Fluent `CrearOrdenMantenimientoDialog(MessageBoxBase)` con preselección inteligente de la unidad elegida en la tabla, selector de tipo de trabajo (Preventivo, Correctivo, CBTC, Frenos), prioridad y técnico líder asignado. Conectado a `SP_CREAR_ORDEN_MANTENIMIENTO`.
    - Actualización automática del estado operativo a `'En Mantenimiento'` y registro de auditoría en `BITACORA` mediante trigger.
    - Recarga reactiva en caliente de tablas y estado de flota sin reiniciar la aplicación.

- [x] **Fase 5: Documentación Académica y Técnica en `docs/`** :
  - `docs/caratula_y_planificacion.md`: Carátula institucional formal según el estándar universitario, padrón de los 7 estudiantes integrantes del equipo con roles asignados, cronograma de hitos y matriz RACI de responsabilidades con estimación de horas por integrante.
  - `docs/diccionario_datos.md`: Diccionario de datos institucional exhaustivo de las 33 tablas y más de 270 restricciones del esquema `METRO_NY`, detallando nombres, tipos Oracle (`NUMBER`, `VARCHAR2`, `DATE`, `TIMESTAMP`), nulidad, llaves primarias, foráneas, restricciones de unicidad y restricciones CHECK de integridad semántica.
  - `docs/normalizacion_3nf.md`: Dictamen formal de normalización hasta Tercera Forma Normal (3NF), sustentación teórica matemática (Codd, Heath), descomposición de atributos compuestos y multivaluados (1NF), eliminación de dependencias parciales (2NF), erradicación de dependencias transitivas (3NF), teoremas de reunión sin pérdida (Lossless Join) y justificación de la prohibición absoluta de atributos derivados.
  - `docs/modelo_entidad_relacion.md`: Modelo conceptual y relacional Barker CDM, clasificación tipológica de las 33 entidades (fuertes, débiles, asociativas y auditoría), reglas de lectura bidireccional, 6 diagramas Mermaid modulares por subsistema y pautas de exportación a PDF vectorial desde Oracle Data Modeler.
  - `docs/guia_sistema_usuario.md`: Manual breve de uso y arquitectura del sistema en tres capas, despliegue en un clic mediante `dbconfigurar.bat` y `dbprogramar.bat`, guía operativa ilustrada de las 7 interfaces Fluent Desktop, simulador de torniquetes OMNY ($2.90) y matriz de orquestación PL/SQL.

---

## 5. Hoja de Ruta Activa y Estado Global del Proyecto

1. [x] **Fase 1: Implementación PL/SQL en `database/`** (Completada y verificada en Oracle 23ai).
2. [x] **Fase 2: Capa de Servicios y Acciones en Desktop (`prototypes/desktop/services/actions_service.py`)** (Completada y verificada en Python).
3. [x] **Fase 3: Módulo 5 Desktop - Pasajeros y Tarifas (`prototypes/desktop/views/cards_interface.py`)** (Completada con simulador interactivo de torniquetes OMNY).
4. [x] **Fase 4: Acciones Interactivas en Vistas Existentes** (Completada con diálogos modales en Flota e Incidentes).
5. [x] **Fase 5: Documentación Académica en `docs/`** (Completada al 100%: Carátula, RACI, Diccionario de Datos, Dictamen 3NF, Modelo E-R y Manual de Usuario).
6. **Estado General**: **100% de los requerimientos y entregables obligatorios del curso completados con éxito**. Listo para la demostración ante el catedrático y empaquetado final en Google Drive.

