# Sistema de Gestión de la Red de Metro de Nueva York (MTA NYCT)
## Proyecto de Curso — Sistemas de Bases de Datos I

---

### Carátula Institucional

| Campo | Información Académica |
| :--- | :--- |
| **Institución** | Universidad de San Carlos de Guatemala |
| **Facultad** | Facultad de Ingeniería |
| **Escuela** | Escuela de Ciencias y Sistemas |
| **Carrera** | Ingeniería en Ciencias y Sistemas |
| **Curso** | Sistemas de Bases de Datos 1 |
| **Catedrático** | Ing. Catedrático Titular |
| **Tutor / Auxiliar** | Auxiliar de Cátedra |
| **Semestre** | Segundo Semestre 2026 |
| **Nombre del Proyecto** | Sistema de Información y Gestión Operativa del Metro de Nueva York (MTA NYCT) |
| **Versión del Sistema** | 1.0.0 (Entrega Oficial de Cátedra) |
| **Fecha Límite de Entrega** | 8 de octubre de 2026 |
| **Repositorio y Fuente** | Esquema Oracle 23ai (`FREEPDB1`) / Aplicación de Escritorio Fluent Desktop |

---

### Integrantes del Grupo de Trabajo (Grupo No. 07)

El proyecto fue desarrollado y sustentado por un equipo multidisciplinario de siete (7) estudiantes, con roles y áreas de especialización claramente delimitadas:

| No. | Nombre Completo del Estudiante | Carné Universitario | Rol Principal en el Proyecto | Correo Electrónico Institucional |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **Coordinador General & Arquitecto de Base de Datos** | 202200101 | Dirección de proyecto, diseño conceptual E-R y arquitectura física de datos | `estudiante1@ingenieria.usac.edu.gt` |
| **2** | **Especialista en Normalización & Modelado Relacional** | 202200102 | Dictamen de 3NF, dependencias funcionales y diccionario de datos | `estudiante2@ingenieria.usac.edu.gt` |
| **3** | **Ingeniero de Automatización PL/SQL** | 202200103 | Programación de procedimientos almacenados (`SP_*`) y funciones (`FN_*`) | `estudiante3@ingenieria.usac.edu.gt` |
| **4** | **Ingeniero de Integridad & Auditoría de Datos** | 202200104 | Programación de triggers de integridad (`TRG_*`), vistas analíticas (`VW_*`) y bitácora | `estudiante4@ingenieria.usac.edu.gt` |
| **5** | **Desarrollador Principal de Software (Frontend Desktop)** | 202200105 | Implementación UI Fluent (PyQt5, QFluentWidgets), vistas interactivas y modales | `estudiante5@ingenieria.usac.edu.gt` |
| **6** | **Desarrollador de Enlace Transaccional & Backend** | 202200106 | Capa de servicios Python (`oracledb`), manejo de excepciones ORA y subprocesos asíncronos | `estudiante6@ingenieria.usac.edu.gt` |
| **7** | **Ingeniero de Calidad (QA), Pruebas & Documentación** | 202200107 | Verificación de consultas obligatorias, pruebas unitarias de SPs/triggers y manual de usuario | `estudiante7@ingenieria.usac.edu.gt` |

---

## 1. Planificación Detallada del Proyecto y Cronograma de Hitos

Para garantizar la entrega puntual y el cumplimiento del 100% del pliego de requerimientos antes del **8 de octubre de 2026**, se estableció un cronograma de seis (6) fases de trabajo ejecutadas en ciclos iterativos de desarrollo.

### 1.1 Cronograma General de Fases (Milestones)

```mermaid
timeline
    title Cronograma de Hitos del Proyecto MetroNY (MTA NYCT)
    section Fase 1 : Análisis e Infraestructura
        Semana 1 : Investigación MTA & Requerimientos
                 : Modelo Conceptual E-R Barker CDM
        Semana 2 : Normalización 3NF & DDL de 33 Tablas
                 : Inserción de Datos Iniciales & 63 Índices B-Tree
    section Fase 2 : Lógica de Negocio PL/SQL
        Semana 3 : Vistas Analíticas (9) & Funciones (9)
        Semana 4 : Procedimientos Almacenados (6) & Triggers (8)
                 : Pruebas Transaccionales y Rollback Seguro
    section Fase 3 : Capa de Enlace & Servicios
        Semana 5 : Conector oracledb multi-PDB & Threading
                 : actions_service.py y Catálogo de 15 Consultas
    section Fase 4 : Aplicación Fluent Desktop
        Semana 6 : Módulos 1-4 (Dashboard, Estaciones, Flota, Personal)
        Semana 7 : Módulo 5 (OMNY, Torniquete $2.90 y Recargas)
                 : Módulos 6-7 (Incidentes, Acciones y Consultas)
    section Fase 5 : QA & Documentación
        Semana 8 : Diccionario de Datos, Dictamen 3NF y Manual
                 : Ensayos de Demostración en Vivo
```

### 1.2 Fechas Clave y Criterios de Aceptación por Hito

| Hito / Fase | Fechas de Ejecución | Entregables Clave | Criterio de Éxito / Aceptación |
| :--- | :---: | :--- | :--- |
| **Hito 1: Modelo y DDL Base** | 18 Ago — 27 Ago | Esquema relacional, `01_configuracion_usuario.ddl`, `02_ddl_tablas.ddl`, `03_datos_prueba.ddl`, `04_indices.ddl`. | 33 tablas creadas en Oracle 23ai con PK, FK y Checks. Carga de 208 registros reales. |
| **Hito 2: Capa PL/SQL en Oracle** | 28 Ago — 05 Sep | `05_vistas.sql`, `06_funciones.sql`, `07_procedimientos.sql`, `08_triggers.sql`, `dbconfigurar.bat`, `dbprogramar.bat`. | 0 errores en `USER_ERRORS`. 32 objetos en estado `VALID`. Triggers impiden saldos negativos y auditores activos. |
| **Hito 3: Capa de Servicios Python** | 06 Sep — 12 Sep | `services/db.py`, `services/actions_service.py`, `services/metro_service.py`, `services/queries_catalog.py`. | Conexión a `FREEPDB1` nativa vía `oracledb`. Invocación de los 6 SPs y 9 funciones probada con tests unitarios. |
| **Hito 4: Frontend Desktop Fluent** | 13 Sep — 22 Sep | 7 vistas PyQt5 + QFluentWidgets, `cards_interface.py` (Simulador de Torniquetes OMNY), diálogos modales en flota e incidentes. | Interfaz fluida a 60 FPS con threading asíncrono. Soporte para temas Claro/Oscuro y simulación en vivo de cobro y recarga. |
| **Hito 5: Consultas y Pruebas QA** | 23 Sep — 30 Sep | Catálogo de 15 consultas mínimas obligatorias interactivas, `prueba_15_consultas.sql`, `test_plsql_verificacion.sql`. | Las 15 consultas responden con parámetros configurables y SQL preview dinámico en menos de 100 ms. |
| **Hito 6: Documentación Final** | 01 Oct — 08 Oct | Diccionario de datos institucional, dictamen formal 3NF, guía de usuario, carátula y carpeta Google Drive. | Aprobación de la documentación académica completa y validación del 100% de los requisitos del enunciado. |

---

## 2. Matriz RACI de Responsabilidades

La matriz RACI delimita las responsabilidades de cada miembro en cada paquete de trabajo:
- **R (Responsible)**: Persona encargada de ejecutar la tarea.
- **A (Accountable)**: Responsable de la aprobación final y calidad del entregable.
- **C (Consulted)**: Persona consultada para aportar criterios técnicos o de diseño.
- **I (Informed)**: Persona mantenida al tanto del estado de la actividad.

| Paquete de Trabajo / Entregable | Estudiante 1 (Arquitecto) | Estudiante 2 (3NF/Datos) | Estudiante 3 (PL/SQL SP) | Estudiante 4 (Triggers/Vistas) | Estudiante 5 (Frontend UI) | Estudiante 6 (Backend/Svc) | Estudiante 7 (QA/Docs) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Análisis de Requerimientos y Reglas de Negocio** | **A** | R | C | C | I | I | R |
| **2. Modelado Conceptual Barker CDM y Relacional** | **A** | R | C | C | I | I | C |
| **3. Normalización hasta Tercera Forma Normal (3NF)** | C | **A / R** | C | C | I | I | C |
| **4. Diccionario de Datos Institucional (33 Tablas)** | C | **A / R** | C | C | I | I | R |
| **5. DDL de Creación de Tablas, Constraints e Índices** | **A / R** | R | C | C | I | I | C |
| **6. Carga de Datos Iniciales Reales (MTA NY)** | C | R | I | I | I | I | **A / R** |
| **7. Vistas Operativas y Analíticas (`05_vistas.sql`)** | C | I | C | **A / R** | C | C | R |
| **8. Funciones de Cálculo de Negocio (`06_funciones.sql`)** | C | I | **A / R** | C | I | C | R |
| **9. Procedimientos Almacenados (`07_procedimientos.sql`)**| C | I | **A / R** | C | I | C | R |
| **10. Triggers de Integridad y Bitácora (`08_triggers.sql`)**| C | I | C | **A / R** | I | I | R |
| **11. Scripts Autónomos (`dbconfigurar`, `dbprogramar`)** | **A** | I | R | R | I | I | C |
| **12. Capa de Servicios y Acciones (`actions_service.py`)** | C | I | C | C | C | **A / R** | R |
| **13. Interfaz Desktop Fluent (Vistas 1 a 4 y 6-7)** | I | I | I | I | **A / R** | C | C |
| **14. Módulo 5: Tarjetas OMNY y Simulador Torniquete** | C | I | C | C | **A / R** | R | R |
| **15. Catálogo Interactivo de 15 Consultas Obligatorias** | C | I | I | I | R | **A / R** | R |
| **16. Batería de Pruebas Unitarias y de Integración** | C | C | C | C | C | C | **A / R** |
| **17. Manual de Usuario y Evidencias Gráficas** | C | I | I | I | C | C | **A / R** |
| **18. Consolidación de Carpeta Google Drive y Rendu** | **A** | R | R | R | R | R | R |

---

## 3. Estimación y Distribución del Esfuerzo de Trabajo

En estricta observancia de los lineamientos del catedrático sobre la visibilidad del esfuerzo individual dentro del equipo, se detalla a continuación el número de horas invertidas por cada miembro en las distintas fases del desarrollo:

| Miembro del Equipo | Horas Análisis & Diseño | Horas Base de Datos (SQL/PLSQL) | Horas Desarrollo Software (Python/Qt) | Horas Pruebas & QA | Horas Documentación | Total Horas Invertidas | % Aporte al Proyecto |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Estudiante 1 (Arquitecto)** | 22 h | 24 h | 10 h | 8 h | 12 h | **76 h** | 14.8 % |
| **Estudiante 2 (3NF/Datos)** | 18 h | 26 h | 6 h | 10 h | 16 h | **76 h** | 14.8 % |
| **Estudiante 3 (PL/SQL SP)** | 10 h | 34 h | 12 h | 12 h | 8 h | **76 h** | 14.8 % |
| **Estudiante 4 (Triggers/Vistas)**| 10 h | 32 h | 10 h | 14 h | 8 h | **74 h** | 14.4 % |
| **Estudiante 5 (Frontend UI)** | 8 h | 8 h | 38 h | 12 h | 8 h | **74 h** | 14.4 % |
| **Estudiante 6 (Backend/Svc)** | 8 h | 12 h | 32 h | 14 h | 8 h | **74 h** | 14.4 % |
| **Estudiante 7 (QA/Docs)** | 12 h | 10 h | 10 h | 22 h | 20 h | **74 h** | 14.4 % |
| **Totales Acumulados** | **88 h** | **146 h** | **118 h** | **92 h** | **80 h** | **524 h** | **100.0 %** |

---

## 4. Modalidad de Entrega y Acceso a la Documentación

1. **Plataforma de Evaluación**:
   - Cada integrante del equipo subirá de manera individual el enlace a la carpeta compartida de Google Drive con permisos de visualización y descarga completos para el profesor y el auxiliar del curso.
2. **Estructura de Carpetas en Google Drive**:
   ```text
   Google_Drive_MetroNY_Grupo07/
   ├── 01_Caratula_y_Planificacion/
   │   └── caratula_y_planificacion.pdf
   ├── 02_Documentacion_Tecnica/
   │   ├── investigacion_operaciones_mta.pdf
   │   ├── modelo_entidad_relacion.pdf
   │   ├── diagrama_er_barker_vectorial.pdf (Exportado desde Data Modeler)
   │   ├── normalizacion_3nf.pdf
   │   └── diccionario_datos.pdf
   ├── 03_Scripts_Base_Datos_Oracle/
   │   ├── 01_setup/ (01_config, 02_ddl, 03_datos, 04_indices)
   │   ├── 02_plsql/ (05_vistas, 06_funciones, 07_procedimientos, 08_triggers)
   │   ├── 03_pruebas/ (prueba_15_consultas, test_plsql_verificacion)
   │   ├── dbconfigurar.bat y dbconfigurar.sh
   │   └── dbprogramar.bat y dbprogramar.sh
   ├── 04_Codigo_Fuente_Aplicacion/
   │   └── prototypes/desktop/ (Código fuente ejecutable PyQt5/QFluentWidgets)
   ├── 05_Manuales_y_Evidencias/
   │   ├── guia_sistema_usuario.pdf
   │   └── informe_evidencias_pruebas.pdf (Capturas de pantalla paso a paso)
   └── 06_Presentacion_Sustentacion/
       └── presentacion_metro_ny_defensa.pdf
   ```

