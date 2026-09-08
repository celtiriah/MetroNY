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

### Opción 1: Instalación Automática en 1 Clic (Recomendada en Windows)

Simplemente haz doble clic sobre el archivo:
```text
setup.bat
```
El script creará automáticamente los tablespaces, el usuario, las 33 tablas, insertará los 208 datos de prueba y compilará los 63 índices B-Tree sin necesidad de escribir ningún comando.

---

### Opción 2: Instalación Manual por Comandos

Si prefieres ejecutar los scripts individualmente en tu terminal (PowerShell o CMD):

```powershell
# 1. Crear tablespaces limpios y usuario METRO_NY (como SYSDBA):
sqlplus / as sysdba @01_configuracion_usuario.ddl

# 2. Crear las 33 tablas normalizadas, llaves foráneas y secuencias:
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @02_ddl_tablas.ddl

# 3. Insertar los 208 registros de datos de prueba del Metro de NY:
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @03_datos_prueba.ddl

# 4. Construir los 63 índices B-Tree de rendimiento en TS_METRO_IDX:
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @04_indices.ddl
```

---

## 📊 Credenciales y Conexión

Para conectarte desde **VS Code** (usando la extensión *Oracle SQL Developer*) o cualquier herramienta gráfica:

| Parámetro | Valor |
| :--- | :--- |
| **Host / Servidor** | `localhost` (o `127.0.0.1`) |
| **Puerto** | `1521` |
| **Tipo de Conexión** | `Service Name` |
| **Service Name** | `FREEPDB1` |
| **Usuario** | `METRO_NY` |
| **Contraseña** | `MetroPass123` |

---

## 🔍 Consultas Mínimas Obligatorias

El archivo `consultas_minimas.ddl` contiene la resolución completa y documentada de las **15 consultas mínimas exigidas en el enunciado del proyecto**.

Puedes ejecutarlas en bloque o una por una:
```powershell
sqlplus METRO_NY/MetroPass123@localhost:1521/FREEPDB1 @consultas_minimas.ddl
```
O abrir `consultas_minimas.ddl` en **VS Code**, colocar el cursor sobre cualquier consulta y presionar `Ctrl + Enter`.

---

## 📁 Estructura del Repositorio

```text
MetroNY/
├── .vscode/
│   └── settings.json           # Asociación automática de archivos .ddl con PL/SQL
├── docs/
│   ├── Enunciado...md          # Especificación oficial de requerimientos del proyecto
│   └── legacy/                 # Archivos históricos y versiones intermedias
├── 01_configuracion_usuario.ddl # Tablespaces dedicados y creación de usuario
├── 02_ddl_tablas.ddl           # DDL maestro (33 tablas en 3FN, 50 FKs, secuencias)
├── 03_datos_prueba.ddl         # Carga de datos reales (208 inserts y sincronización)
├── 04_indices.ddl              # 63 Índices B-Tree optimizados en TS_METRO_IDX
├── consultas_minimas.ddl       # Las 15 consultas del proyecto con encabezados limpios
├── setup.bat                   # Instalador en 1 clic para Windows
├── .gitignore                  # Exclusión de archivos binarios (.dbf), logs y temporales
└── README.md                   # Documentación principal del repositorio
```
