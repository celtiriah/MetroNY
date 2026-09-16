# Sistema de Gestión del Metro de Nueva York (MTA NYCT)

**Curso:** Bases de Datos I  
**Motor de Base de Datos:** Oracle Database 21c / 23ai / 26ai Free  
**Esquema:** `METRO_NY`  
**Pluggable Database:** `FREEPDB1` (con fallback automático a `XEPDB1`)

---

## 🚇 Descripción del Proyecto

Este repositorio contiene la arquitectura, modelo relacional formal (3FN), scripts DDL/DML, capa de programación PL/SQL (vistas, funciones, procedimientos almacenados y triggers), datos de prueba reales, consultas analíticas y la aplicación de escritorio nativa para el **Sistema de Gestión del Metro de Nueva York (MTA NYCT)**.

El sistema modela de forma integral la red de transporte subterráneo:
* **Infraestructura y Red**: 5 Líneas oficiales (1, A, C, 7, L), 12 Estaciones, Plataformas/Andenes, Transferencias peatonales, Distancias y Tiempos de trayecto.
* **Operación y Rutas**: Rutas locales y expresas, paradas secuenciales ordenadas, horarios, frecuencias y viajes programados.
* **Flota y Material Rodante**: Trenes (R142, R160, R179, R211), composición de vagones, asignaciones históricas y depósitos/patios.
* **Personal y Seguridad**: Empleados, supervisión jerárquica, certificaciones de conducción vigentes y programación de turnos sin solapamiento.
* **Recaudación y Pasajes**: Tarifas oficiales (Base, Reducida, Estudiantil), tarjetas OMNY nominales y anónimas, recargas y validación en torniquetes.
* **Mantenimiento**: Registro de equipos, órdenes de trabajo preventivas/correctivas, repuestos y técnicos asignados.
* **Gestión de Incidentes**: Registro de eventos operativos con contrainte de **Arco Exclusivo** para elementos afectados, severidad y cancelación de viajes afectados.

---

## 🚀 Despliegue de Base de Datos (Scripts Canónicos en 2 Pasos)

La base de datos está organizada de forma modular en `database/` para garantizar una instalación rápida, limpia y 100% reproducible en el equipo:

### Requisitos Previos
1. **Oracle Database** (21c, 23ai o 26ai Free) con el servicio `FREEPDB1` (o `XEPDB1`) activo.
2. Contar con `sqlplus` accesible desde la terminal.

---

### Paso 1: Configuración de Infraestructura y Datos (`dbconfigurar`)
Crea los tablespaces dedicados (`TS_METRO_DAT`, `TS_METRO_IDX`), el usuario `METRO_NY`, las **33 tablas normalizadas en 3FN**, los **208 registros de datos de prueba reales** y los **63 índices B-Tree de optimización**.

* **En Windows (1 Clic)**:
  ```cmd
  database\dbconfigurar.bat
  ```
* **En Linux / macOS / WSL**:
  ```bash
  chmod +x database/dbconfigurar.sh
  ./database/dbconfigurar.sh
  ```

---

### Paso 2: Compilación de Lógica PL/SQL (`dbprogramar`)
Compila la capa de reglas de negocio en Oracle: **9 Vistas** (`VW_*`), **9 Funciones** (`FN_*`), **6 Procedimientos Almacenados** (`SP_*`) y **8 Triggers** (`TRG_*`).

* **En Windows (1 Clic)**:
  ```cmd
  database\dbprogramar.bat
  ```
* **En Linux / macOS / WSL**:
  ```bash
  chmod +x database/dbprogramar.sh
  ./database/dbprogramar.sh
  ```

> [!NOTE]
> Ambos scripts cuentan con **autodetección inteligente de Pluggable Database** mediante `database/get_pdb.sql`, detectando dinámicamente si el entorno utiliza `FREEPDB1` o `XEPDB1`.

---

## 💻 Aplicación de Escritorio Nativa (PyQt5 + QFluentWidgets)

Ubicada en `prototypes/desktop/`, es el **foco principal de desarrollo** del sistema. Proporciona una interfaz gráfica moderna conforme al estándar **Windows 11 Fluent Design System**:

* **Conexión Directa a Oracle**: Utiliza el driver oficial `oracledb` en modo Thin (sin necesidad de cliente Oracle Instant Client pesado).
* **Navegación Fluida**: `FluentWindow` con barra de navegación lateral colapsable, alternancia de temas Claro / Oscuro en caliente y alta densidad visual (High-DPI).
* **Calidad y Cero Errores Pylance**: Verificada con la skill y herramienta estática `pyqt-pylance-guardian`, garantizando tipado estricto, énumérations scopées (`Qt.AlignmentFlag.*`) y control riguroso de valores nulos (`T | None`).

### Ejecución de la Aplicación de Escritorio
* **En Windows (1 Clic)**:
  ```cmd
  prototypes\desktop\start.bat
  ```
* **Por comando manual**:
  ```powershell
  python prototypes\desktop\main.py
  ```

### Módulos y Pantallas Disponibles en la App de Escritorio:
1. **Dashboard General (`dashboard_interface.py`)**: 6 tarjetas métricas de estado operativo en tiempo real, resumen de líneas activas y accesos directos.
2. **Módulo 1: Red y Estaciones (`m1_stations_interface.py`)**: Implementación completa de las 9 operaciones exigidas por la cátedra (CRUD de líneas y estaciones, asociación de estaciones, distancias y tiempos, plataformas, transferencias, consulta de líneas por estación y recorrido ordenado).
3. **Módulo 2: Rutas y Horarios (`m2_routes_interface.py`)**: Implementación completa de las 9 operaciones exigidas (rutas locales y expresas, sentidos de marcha, paradas efectivas vs saltos expresos, horarios semanales y frecuencias, programación de viajes con validación en `SP_PROGRAMAR_VIAJE`, cancelación y reprogramación, próximos arribos por estación y cancelación en cascada por incidentes).
4. **Módulo 3: Flota y Material Rodante (`m3_fleet_interface.py`)**: Directorio de unidades, estado operativo y diálogo modal para generar órdenes de mantenimiento (`SP_CREAR_ORDEN_MANTENIMIENTO`).
5. **Módulo 4: Personal y Turnos (`m4_staff_interface.py`)**: Directorio de personal, cargos y estado de turnos y licencias.
6. **Módulo 5: Pasajeros y Tarifas (`m5_cards_interface.py`)**: Visualizador fotorrealista de tarjeta OMNY, simulador interactivo de validación en torniquete ($2.90 con descuento real en Oracle), recarga de saldo exprés e historiales en vivo.
7. **Módulo 7: Incidentes Operativos (`m7_incidents_interface.py`)**: Registro de incidencias en vivo (`SP_REGISTRAR_INCIDENTE`) y cancelación de viajes afectados (`SP_CANCELAR_VIAJES_AFECTADOS`).
8. **15 Consultas Mínimas Obligatorias (`queries_interface.py`)**: Ejecución dinámica e interactiva de las 15 consultas del enunciado con filtros en tiempo real y visor SQL reactivo.

---

## 📊 Credenciales y Conexión Manual

Para conectarse desde **VS Code** (extensión *Oracle SQL Developer*), **DBeaver**, **DataGrip** o **SQL Developer**:

| Parámetro | Valor |
| :--- | :--- |
| **Host / Servidor** | `localhost` (o `127.0.0.1`) |
| **Puerto** | `1521` |
| **Tipo de Conexión** | `Service Name` |
| **Service Name** | Tu PDB activo (`FREEPDB1` o `XEPDB1`) |
| **Usuario** | `METRO_NY` |
| **Contraseña** | `MetroPass123` |

---

## 🔍 Consultas Mínimas Obligatorias

El proyecto incluye la resolución completa de las **15 consultas analíticas exigidas**:
* Se pueden ejecutar interactivamente desde la **App de Escritorio PyQt5** en la pestaña *15 Consultas*.
* O ejecutarse en bloque desde terminal / SQL*Plus:
  ```powershell
  sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @database\03_pruebas\prueba_15_consultas.sql
  ```

---

## 📚 Documentación Académica y Técnica (`docs/`)

El proyecto cuenta con un paquete exhaustivo de documentación académica en español listo para evaluación universitaria:

* [docs/caratula_y_planificacion.md](docs/caratula_y_planificacion.md): Carátula formal universitaria, padrón de los 7 estudiantes integrantes del equipo, cronograma de hitos y matriz de responsabilidades RACI.
* [docs/diccionario_datos.md](docs/diccionario_datos.md): Diccionario de datos institucional de las 33 tablas y más de 270 restricciones del esquema `METRO_NY` (tipos Oracle, nulidad, PKs, FKs, Unique y Checks semánticos).
* [docs/normalizacion_3nf.md](docs/normalizacion_3nf.md): Dictamen formal de normalización hasta 3NF, justificación matemática de dependencias funcionales y teoremas de reunión sin pérdida (Lossless Join).
* [docs/modelo_entidad_relacion.md](docs/modelo_entidad_relacion.md): Modelo conceptual y relacional Barker CDM, clasificación tipológica de las 33 entidades y diagramas modulares Mermaid.
* [docs/guia_sistema_usuario.md](docs/guia_sistema_usuario.md): Manual de usuario con arquitectura de tres capas, guía de despliegue y manual ilustrado de las vistas de escritorio.
* [docs/investigacion_operaciones_mta.md](docs/investigacion_operaciones_mta.md): Estudio operativo real de la MTA (Divisiones A y B, OMNY fare capping de 7 días, mantenimiento SMS y gestión de incidentes 24/7).

---

## 📁 Estructura del Repositorio

```text
MetroNY/
├── .agents/
│   └── skills/
│       └── pyqt-pylance-guardian/    # Skill de calidad, verificación de tipos y stubs PyQt
├── .vscode/
│   └── settings.json                 # Asociación de archivos .ddl y .sql
├── docs/                             # Documentación académica y técnica (en español)
│   ├── Enunciado - Proyecto...md     # Requerimientos oficiales de la cátedra
│   ├── caratula_y_planificacion.md   # Carátula universitaria y matriz RACI
│   ├── diccionario_datos.md          # Diccionario de datos exhaustivo (33 tablas)
│   ├── normalizacion_3nf.md          # Justificación teórica de Tercera Forma Normal (3NF)
│   ├── modelo_entidad_relacion.md    # Modelo Barker y diagramas Mermaid
│   ├── guia_sistema_usuario.md       # Manual de uso y arquitectura del sistema
│   └── investigacion_operaciones_mta.md # Estudio técnico de la operación del Metro de NY
│
├── database/                         # Scripts canónicos de base de datos Oracle
│   ├── dbconfigurar.bat / .sh        # Instalador de tablas, datos e índices
│   ├── dbprogramar.bat / .sh         # Compilador de Vistas, Funciones, SPs y Triggers
│   ├── get_pdb.sql                   # Autodetección de PDB activo (FREEPDB1 / XEPDB1)
│   ├── 01_setup/                     # Esquema, tablas, datos de prueba e índices
│   │   ├── 01_configuracion_usuario.ddl
│   │   ├── 02_ddl_tablas.ddl
│   │   ├── 03_datos_prueba.ddl
│   │   └── 04_indices.ddl
│   ├── 02_plsql/                     # Lógica de negocio y automatización PL/SQL
│   │   ├── 05_vistas.sql             # 9 Vistas analíticas (VW_*)
│   │   ├── 06_funciones.sql          # 9 Funciones de negocio (FN_*)
│   │   ├── 07_procedimientos.sql     # 6 Procedimientos transaccionales (SP_*)
│   │   └── 08_triggers.sql           # 8 Triggers de auditoría e integridad (TRG_*)
│   └── 03_pruebas/                   # Scripts de validación y consultas
│       ├── prueba_15_consultas.sql   # Las 15 consultas mínimas obligatorias
│       └── test_plsql_verificacion.sql # Pruebas funcionales de objetos PL/SQL
│
├── prototypes/
│   ├── desktop/                      # APLICACIÓN DE ESCRITORIO (PyQt5 + QFluentWidgets)
│   │   ├── main.py                   # Punto de entrada con loop Qt y FluentWindow
│   │   ├── config.py                 # Configuración de conexión y temas MTA
│   │   ├── requirements.txt          # Dependencias (PyQt5, PyQt-Fluent-Widgets, oracledb)
│   │   ├── start.bat / start.sh      # Lanzadores en 1 clic
│   │   ├── services/                 # Capa de acceso a datos y llamadas PL/SQL
│   │   │   ├── db.py                 # Pool de conexiones oracledb
│   │   │   ├── metro_service.py      # Consultas y lectura de catálogo
│   │   │   ├── m1_network_service.py # Servicio especializado para Módulo 1 (Red y Estaciones)
│   │   │   ├── m2_routes_service.py  # Servicio especializado para Módulo 2 (Rutas y Horarios)
│   │   │   ├── actions_service.py    # Invocación de SPs y funciones Oracle
│   │   │   └── queries_catalog.py    # Definición de las 15 consultas dinámicas
│   │   ├── workers/                  # Hilos de fondo asíncronos (QThread)
│   │   ├── components/               # Componentes UI reutilizables
│   │   └── views/                    # Pantallas de la interfaz gráfica
│   │       ├── main_window.py        # Ventana principal y barra de navegación
│   │       ├── dashboard_interface.py # Panel de métricas y KPIs
│   │       ├── m1_stations_interface.py # MÓDULO 1: Administración de la Red
│   │       ├── m2_routes_interface.py   # MÓDULO 2: Rutas y Horarios
│   │       ├── m3_fleet_interface.py  # MÓDULO 3: Flota y material rodante
│   │       ├── m4_staff_interface.py  # MÓDULO 4: Personal y turnos
│   │       ├── m5_cards_interface.py  # MÓDULO 5: Pasajeros, Tarjetas OMNY y Torniquete
│   │       ├── m7_incidents_interface.py # MÓDULO 7: Incidentes y afectaciones
│   │       └── queries_interface.py   # Ejecutor dinámico de las 15 Consultas
│   └── webapp/                       # Prototipo web complementario (Flask API + JS)
│
├── PROJECT_STATE.md                  # Bitácora centralizada y memoria del proyecto
├── implementation_plan.md            # Plan maestro de trabajo
├── .gitignore                        # Exclusiones de Git
└── README.md                         # Este documento
```
