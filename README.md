# Sistema de Gestión del Metro de Nueva York (MTA NYCT)

**Curso:** Bases de Datos I  
**Motor de Base de Datos:** Oracle Database 21c / 23ai / 26ai Free  
**Esquema:** `METRO_NY`  
**Pluggable Database:** `FREEPDB1`

---

## 🚇 Descripción del Proyecto

Este repositorio contiene la arquitectura, modelo relacional (3FN), scripts DDL, datos de prueba y consultas analíticas para el **Sistema de Gestión del Metro de Nueva York (MTA NYCT)**.

El sistema modela de forma integral la red de transporte subterráneo:
* **Infraestructura y Red**: 5 Líneas icónicas (1, A, C, 7, L), 12 Estaciones, Plataformas, Servicios y Transferencias.
* **Operación y Rutas**: Rutas locales/expresas, paradas secuenciales, horarios y viajes programados.
* **Flota y Material Rodante**: Trenes (R142, R160, R179, R211), composición de vagones y depósitos/patios.
* **Personal y Seguridad**: Empleados, certificaciones de conducción vigentes y asignación de turnos.
* **Recaudación y Pasajes**: Tarifas oficiales (Base, Adulto Mayor, Escolar), tarjetas OMNY nominales/anónimas, recargas y validación en torniquetes.
* **Mantenimiento**: Órdenes preventivas/correctivas, repuestos e inspectores técnicos.
* **Gestión de Incidentes**: Registro de eventos operativos con contrainte de **Arco Exclusivo** para elementos afectados.

---

## 🚀 Guía de Instalación Rápida (Para el Equipo)

Cualquier integrante del grupo puede clonar este repositorio y tener la base de datos completa y lista en su computadora en **menos de 30 segundos**.

### Requisitos Previos
1. Tener instalado **Oracle Database** (21c, 23ai o 26ai Free) con el servicio `FREEPDB1` activo.
2. Contar con acceso a `sqlplus` desde la terminal.

---

### Opción 1: Instalación Automática (Recomendada)

El sistema cuenta con **auto-detección de Pluggable Database** (`FREEPDB1` para Oracle 23ai/26ai Free o `XEPDB1` para Oracle XE).

* **En Windows**:
  Haz doble clic sobre:
  ```text
  dbsetup.bat
  ```
* **En Linux / macOS / WSL**:
  Otorga permisos y ejecuta:
  ```bash
  chmod +x dbsetup.sh
  ./dbsetup.sh
  ```

El script detectará tu PDB activo, creará los tablespaces, el usuario `METRO_NY`, las 33 tablas, insertará los 208 datos de prueba y compilará los 63 índices B-Tree en segundos.

---

### Opción 2: Instalación Manual por Comandos

Si prefieres ejecutar los scripts individualmente (reemplaza `FREEPDB1` por tu PDB si usas XE como `XEPDB1`):

```powershell
# 1. Crear tablespaces limpios y usuario METRO_NY (como SYSDBA):
sqlplus / as sysdba @database\01_configuracion_usuario.ddl

# 2. Crear las 33 tablas normalizadas, llaves foráneas y secuencias:
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @database\02_ddl_tablas.ddl

# 3. Insertar los 208 registros de datos de prueba del Metro de NY:
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @database\03_datos_prueba.ddl

# 4. Construir los 63 índices B-Tree de rendimiento en TS_METRO_IDX:
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @database\04_indices.ddl
```

---

## 💻 Prototipos de Aplicación

El proyecto incluye dos alternativas funcionales para interactuar con la base de datos Oracle:

### 1. Aplicación de Escritorio Nativa (PyQt5) — `prototypes/desktop`
Ventana nativa con **conexión directa a Oracle** (sin servidores intermedios), tema claro por defecto, alternancia a tema oscuro, buscador de estaciones en vivo y ejecutor de las 15 consultas mínimas.

* **En Windows (1 Clic)**:
  Haz doble clic en:
  ```text
  prototypes\desktop\start.bat
  ```
* **En Linux / macOS**:
  ```bash
  chmod +x prototypes/desktop/start.sh
  ./prototypes/desktop/start.sh
  ```

---

### 2. Aplicación Web (HTML5 / CSS3 / Vanilla JS + Flask) — `prototypes/webapp`
Dashboard web servido en `http://localhost:5000` con selector de temas y diseño oficial MTA.

* **En Windows (1 Clic)**:
  Haz doble clic en:
  ```text
  start.bat
  ```
* **En Linux / macOS**:
  ```bash
  chmod +x start.sh
  ./start.sh
  ```

---

## 📊 Credenciales y Conexión

Para conectarte desde **VS Code** (usando la extensión *Oracle SQL Developer*) o cualquier cliente (DBeaver, SQL Developer):

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

El archivo `database/consultas_minimas.ddl` contiene la resolución completa y documentada de las **15 consultas mínimas exigidas en el enunciado del proyecto**.

Puedes ejecutarlas desde la **App de Escritorio PyQt5**, el **Dashboard Web**, o directamente por terminal:
```powershell
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @database\consultas_minimas.ddl
```
O abrir `database/consultas_minimas.ddl` en **VS Code**, colocar el cursor sobre cualquier consulta y presionar `Ctrl + Enter`.

---

## 📁 Estructura del Repositorio

```text
MetroNY/
├── .vscode/
│   └── settings.json           # Asociación de archivos .ddl con sintaxis PL/SQL
├── docs/
│   ├── Enunciado...md          # Especificación oficial de requerimientos
│   └── legacy/                 # Documentos históricos
├── database/                   # Scripts de base de datos Oracle (.ddl)
│   ├── 01_configuracion_usuario.ddl # Tablespaces dedicados y usuario METRO_NY
│   ├── 02_ddl_tablas.ddl           # DDL maestro (33 tablas en 3FN, 50 FKs, secuencias)
│   ├── 03_datos_prueba.ddl         # Carga de datos reales (208 inserts y sincronización)
│   ├── 04_indices.ddl              # 63 Índices B-Tree optimizados en TS_METRO_IDX
│   ├── consultas_minimas.ddl       # Las 15 consultas mínimas resueltas y formateadas
│   └── get_pdb.sql                 # Script auxiliar para auto-detección del PDB
├── prototypes/
│   ├── desktop/                # Aplicación de escritorio nativa (Python + PyQt5)
│   │   ├── app.py              # Ventana gráfica (Dashboard, Estaciones, 15 Consultas)
│   │   ├── db.py               # Conexión directa a Oracle y catálogo
│   │   ├── styles.py           # Estilos QSS (Tema Claro por defecto + Tema Oscuro)
│   │   ├── requirements.txt    # Dependencias (PyQt5, oracledb)
│   │   ├── start.bat           # Lanzador en 1 clic para Windows
│   │   └── start.sh            # Lanzador para Linux / macOS
│   └── webapp/                 # Aplicación web (HTML/CSS/JS + Flask)
│       ├── backend/            # Mini-servidor Flask y conector Oracle
│       ├── frontend/           # HTML5, CSS3 y JS Vanilla
│       ├── start.bat           # Lanzador web para Windows
│       └── start.sh            # Lanzador web para Linux
├── dbsetup.bat                 # Instalador de la base de datos en 1 clic para Windows
├── dbsetup.sh                  # Instalador de la base de datos para Linux / macOS
├── start.bat                   # Lanzador web rápido desde la raíz
├── start.sh                    # Lanzador web rápido desde la raíz
├── .gitignore                  # Exclusión de binarios (.dbf), logs y temporales
└── README.md                   # Documentación principal del repositorio
```

