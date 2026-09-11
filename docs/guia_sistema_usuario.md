# Manual del Sistema y Guía de Usuario — Metro de Nueva York (MTA NYCT)
## Aplicación de Escritorio Fluent Desktop & Base de Datos Oracle 23ai

> **Entregable Oficial No. 14**: Manual breve de uso, arquitectura de software, instalación en un clic, guía operativa ilustrada de las 7 interfaces de usuario, simulador de torniquetes OMNY, orquestación de procedimientos almacenados y solución de incidencias.

---

## 1. Arquitectura Técnica del Sistema

El sistema fue concebido bajo una **Arquitectura en Tres Capas (3-Tier)** orientada al alto rendimiento transaccional (OLTP) y la experiencia de usuario moderna:

```mermaid
graph TD
    subgraph Capa 1 : Presentación (Desktop UI)
        UI[PyQt5 + QFluentWidgets]
        T1[Dashboard Interface]
        T2[Stations Interface]
        T3[Fleet Interface]
        T4[Staff Interface]
        T5[Cards & Turnstile Interface]
        T6[Incidents Interface]
        T7[Queries Interface]
        UI --> T1 & T2 & T3 & T4 & T5 & T6 & T7
    end

    subgraph Capa 2 : Servicios y Lógica de Aplicación (Python 3.14)
        SVC[services/actions_service.py]
        METRO[services/metro_service.py]
        CAT[services/queries_catalog.py]
        DB[services/db.py]
        TH[workers/query_worker.py - QThread]
        UI --> TH --> DB
        UI --> SVC --> DB
        UI --> METRO --> DB
        UI --> CAT --> DB
    end

    subgraph Capa 3 : Base de Datos y Negocio (Oracle 23ai FREEPDB1)
        ORA[(Oracle Database 23ai)]
        TAB[33 Tablas en 3NF]
        IDX[63 Índices B-Tree]
        PLSQL[Lógica PL/SQL]
        VWS[9 Vistas Analíticas]
        FNS[9 Funciones de Cálculo]
        SPS[6 Stored Procedures]
        TRG[8 Triggers de Integridad]
        DB --> ORA
        ORA --> TAB & IDX & PLSQL
        PLSQL --> VWS & FNS & SPS & TRG
    end
```

### Principios Arquitectónicos
1. **Lógica de Integridad Centralizada en Oracle**: Las reglas críticas de negocio (saldo no negativo, verificación de licencias, asignación de flotas, auditoría) se ejecutan directamente en el motor de base de datos mediante PL/SQL (Stored Procedures, Funciones y Triggers), asegurando integridad incluso frente a múltiples clientes concurrentes.
2. **Interfaz Nativa Fluida (Windows 11 Fluent Design)**: Desarrollada con `PyQt5` y `PyQt-Fluent-Widgets`, respetando las directrices de diseño de Microsoft: controles acrílicos, esquinas redondeadas, navegación lateral tipo barra plegable (`NavigationInterface`), animaciones suaves y soporte nativo para modo Claro y Oscuro.
3. **No-Bloqueo de UI (Asincronía a 60 FPS)**: Las consultas analíticas complejas se despachan a hilos secundarios mediante `QueryWorker(QThread)`, evitando que la interfaz se congele durante la ejecución de reportes pesados.

---

## 2. Instalación y Despliegue en un Clic

El sistema incluye scripts por lotes optimizados para Windows (`.bat`) y Linux/macOS (`.sh`) con autodetección automática del servicio Pluggable Database (`FREEPDB1` o `XEPDB1`).

### 2.1 Requisitos Previos del Entorno
- **Sistema Operativo**: Windows 10/11 (64-bit), Linux o macOS.
- **Python**: Versión 3.10 o superior (verificado y optimizado en Python 3.14).
- **Oracle Database**: Oracle Database 23ai Free o 21c Express Edition ejecutándose en `localhost:1521`.
- **Dependencias Python**:
  ```bash
  pip install PyQt5 PyQt-Fluent-Widgets oracledb
  ```

### 2.2 Despliegue Automatizado de Base de Datos en Dos Pasos

Abra una terminal en la raíz del proyecto (`c:\Projects\MetroNY`):

#### Paso 1: Configurar Esquema, Tablas e Índices
Ejecute:
```cmd
database\dbconfigurar.bat
```
*Qué realiza*:
1. Detecta automáticamente la PDB activa (`FREEPDB1`).
2. Conecta con privilegios DBA (`sys/oracle as sysdba`) y crea el tablespace `METRO_DATA` y el usuario `METRO_NY` con permisos completos.
3. Ejecuta `02_ddl_tablas.ddl`: Crea las 33 tablas normalizadas en 3NF con llaves primarias, foráneas y restricciones CHECK.
4. Ejecuta `03_datos_prueba.ddl`: Inserta 208 registros con datos reales de la red MTA de Nueva York.
5. Ejecuta `04_indices.ddl`: Genera los 63 índices B-Tree de optimización sobre claves foráneas y columnas de alta selectividad.

#### Paso 2: Compilar Lógica PL/SQL y Automatizaciones
Ejecute:
```cmd
database\dbprogramar.bat
```
*Qué realiza*:
1. Compila `05_vistas.sql`: Las 9 vistas analíticas y operativas (`VW_*`).
2. Compila `06_funciones.sql`: Las 9 funciones de cálculo de negocio (`FN_*`).
3. Compila `07_procedimientos.sql`: Los 6 procedimientos almacenados transaccionales (`SP_*`).
4. Compila `08_triggers.sql`: Los 8 triggers de integridad, bitácora y sincronización de flota (`TRG_*`).
5. Realiza una auditoría final verificando que `USER_ERRORS` reporte **0 errores**.

---

## 3. Lanzamiento de la Aplicación de Escritorio

Para iniciar la aplicación gráfica institucional de MetroNY:
```cmd
python prototypes/desktop/main.py
```

### Elementos de la Ventana Principal
- **Barra de Navegación Lateral (NavigationInterface)**: Permite conmutar instantáneamente entre los 7 módulos del sistema mediante iconos modernos Fluent.
- **Selector de Tema en Barra de Título**: Conmutador dinámico de tema Claro / Oscuro ubicado en el extremo superior derecho, permitiendo adaptar la paleta cromática a la iluminación ambiental.
- **Feedback Visual (InfoBar)**: Notificaciones toast no intrusivas en la esquina superior derecha que alertan sobre el éxito de las operaciones o detallan errores transaccionales en español.

---

## 4. Guía Operativa Módulo por Módulo

### 4.1 Módulo 1: Panel General (Dashboard)
- **Propósito**: Supervisión ejecutiva en tiempo real del estado de la red.
- **Componentes**:
  1. **6 Tarjetas de Estadísticas (StatCards)**:
     - *Estaciones Activas*: Total de terminales y paradas habilitadas.
     - *Trenes en Servicio*: Unidades en circulación comercial.
     - *Líneas Operativas*: Líneas troncales prestando servicio.
     - *Pasajeros Hoy*: Conteo acumulado de ingresos por torniquetes en la fecha actual.
     - *Recaudación Total ($ USD)*: Ingresos brutos recaudados en el sistema.
     - *Incidentes Abiertos*: Alertas activas pendientes de resolución por el centro de control.
  2. **Tabla de Estado de Líneas**: Muestra cada línea con su color oficial MTA, cantidad de estaciones, división técnica y estado (`Operativa`, `Con Retrasos`, `Suspendida`).

---

### 4.2 Módulo 2: Directorio de Estaciones (Red)
- **Propósito**: Consulta de infraestructura de detención de pasajeros y accesibilidad universal.
- **Modo de Operación**:
  1. **Búsqueda Instantánea**: Escriba en la caja de texto para filtrar estaciones por nombre (ej. `Times Sq`, `Grand Central`, `Fulton St`) o código.
  2. **Filtro por Borough**: Filtre por distrito (`Manhattan`, `Brooklyn`, `Queens`, `The Bronx`).
  3. **Filtro de Accesibilidad ADA**: Active la casilla `Solo accesibles (ADA)` para visualizar únicamente las estaciones equipadas con rampas y elevadores para sillas de ruedas.
  4. **Detalle de Andenes y Servicios**: Al seleccionar una estación en la tabla, el panel inferior lista sus plataformas (Uptown / Downtown) y los servicios disponibles (Wi-Fi, sanitarios, presencia policial).

---

### 4.3 Módulo 3: Flota y Material Rodante
- **Propósito**: Administración de los trenes de la flota, monitoreo de kilometraje e intervención en talleres.
- **Acciones Clave**:
  1. **Filtro Operativo**: Visualice trenes por su estado (`Disponible`, `En Operación`, `En Mantenimiento`, `Fuera de Servicio`).
  2. **Crear Orden de Mantenimiento (Acción Transaccional)**:
     - Seleccione un tren de la tabla (ej. Tren `A-01` con alto kilometraje).
     - Haga clic en el botón primario **"Crear Orden de Taller"**.
     - En el diálogo modal Fluent:
       - El número del tren seleccionado aparecerá precargado.
       - Elija el tipo de mantenimiento: `Preventivo`, `Correctivo`, `Revisión CBTC`, `Inspección de Frenos`.
       - Seleccione la prioridad: `Baja`, `Media`, `Alta`, `Crítica`.
       - Asigne al técnico líder calificado de la lista desplegable.
     - Al confirmar (**Guardar Orden**), el sistema invoca en Oracle `SP_CREAR_ORDEN_MANTENIMIENTO`:
       - Se inserta la orden en `ORDEN_MANTENIMIENTO` y se asigna el técnico en `ORDEN_TECNICO`.
       - El estado del tren cambia automáticamente a `'En Mantenimiento'`.
       - El trigger `TRG_TREN_CAMBIO_ESTADO` audita la operación en la tabla `BITACORA`.
       - La tabla de la flota se refresca en caliente sin reiniciar la aplicación.

---

### 4.4 Módulo 4: Personal Operativo
- **Propósito**: Gestión de recursos humanos, organigrama, turnos y vigencia de licencias técnicas.
- **Modo de Operación**:
  1. **Directorio de Empleados**: Lista a maquinistas, supervisores de estación y técnicos de taller con su código institucional y fecha de contratación.
  2. **Relación Jerárquica**: Visualice inmediatamente quién es el supervisor directo de cada empleado.
  3. **Control de Certificaciones de Conducción**: Al seleccionar un maquinista, el panel de licencias muestra los modelos de tren para los cuales está habilitado (R142, R160, etc.) y la fecha de caducidad. Si la certificación está vencida, el trigger de base de datos `TRG_CERTIFICACION_ALERTA_VENCIDA` impedirá que sea asignado a un viaje programado.

---

### 4.5 Módulo 5: Pasajeros, Billetaje OMNY y Simulador de Torniquetes
- **Propósito**: Módulo estrella del sistema. Administra los medios de pago OMNY y permite simular el paso físico por torniquetes de estación.
- **Componentes Visuales**:
  1. **Tarjeta OMNY Visual (`VisualOmnyCard`)**:
     - Renderizado de tarjeta física con gradiente azul MTA, logotipo y chip contactless `(((•))) OMNY`.
     - Tipografía monoespaciada institucional para el número de tarjeta (ej. `OMNY-1000-2001`).
     - Nombre del titular y badge cromático dinámico de saldo (verde si $\ge \$2.90$, rojo si es inferior).
  2. **Simulador de Paso por Torniquete ($2.90)**:
     - Seleccione la estación de ingreso (ej. `Times Square - 42nd St`).
     - Seleccione la tarjeta activa del pasajero.
     - Presione el botón **"Validar Paso en Torniquete ($2.90)"**.
     - El sistema invoca en Oracle `SP_REGISTRAR_INGRESO`:
       - Si la tarjeta tiene fondos y está activa: Descuenta exactamente **\$2.90**, emite un sonido o notificación verde (`InfoBar.success`: *"Paso Autorizado: Buen Viaje"*) y actualiza instantáneamente el saldo en pantalla.
       - Si el saldo es insuficiente: Muestra una notificación de advertencia naranja (`InfoBar.warning`: *"Saldo insuficiente ($X.XX). Recargue su tarjeta."*).
       - Si la tarjeta está bloqueada o cancelada: Muestra un error crítico en rojo (`InfoBar.error`).
  3. **Recarga de Saldo Express**:
     - Permite abonar fondos a la tarjeta seleccionada mediante botones rápidos (+$5, +$10, +$20, +$50) o un selector numérico libre.
     - Seleccione el medio de pago: `Tarjeta de Débito`, `Tarjeta de Crédito`, `Efectivo en Estación`, `Apple Pay / Google Pay`.
     - Presione **"Confirmar Recarga"**: Se ejecuta `SP_RECARGAR_TARJETA` en Oracle, registrando la transacción con recibo fiscal y restaurando el saldo.
  4. **Historiales Dinámicos en Pestañas**:
     - Alterne entre el **"Historial de Validaciones en Torniquete"** y el **"Historial de Recargas"** para auditar cada transacción en tiempo real.

---

### 4.6 Módulo 6: Gestión de Incidentes y Contingencias
- **Propósito**: Control de contingencias de tráfico (averías, emergencias médicas, inundaciones) y despacho de medidas correctivas.
- **Acciones Clave**:
  1. **Registrar Nuevo Incidente (Acción Transaccional)**:
     - Presione el botón primario **"Registrar Incidente"**.
     - En el diálogo modal Fluent `RegistrarIncidenteDialog`:
       - Ingrese el tipo de incidente y seleccione la severidad (`Baja`, `Media`, `Alta`, `Crítica`).
       - Elija el tipo de elemento de red afectado: `Estación`, `Tren`, `Ruta` o `Línea`.
       - El selector secundario se adaptará dinámicamente listando únicamente las estaciones o trenes existentes.
       - Indique el tipo de contingencia: `Cierre de Estación`, `Retiro de Tren`, `Suspensión de Tramo`, `Cambio de Ruta`.
     - Al confirmar, se invoca `SP_REGISTRAR_INCIDENTE`, registrando el evento y sus activos asociados.
  2. **Cancelar Viajes Afectados (Acción de Despacho)**:
     - Cuando una estación o tramo es clausurado, seleccione el incidente en la tabla y presione **"Cancelar Viajes Afectados"**.
     - El procedimiento `SP_CANCELAR_VIAJES_AFECTADOS` actualizará automáticamente a `'Cancelado'` todos los viajes programados en curso o pendientes que debían atravesar dicha zona, alertando a los despachadores.

---

### 4.7 Módulo 7: Las 15 Consultas Mínimas Obligatorias
- **Propósito**: Interfaz interactiva para responder a las 15 consultas canónicas exigidas por el pliego del proyecto.
- **Características**:
  1. **Selector de Consulta**: Menú desplegable con las 15 consultas numeradas.
  2. **Filtros Parámetricos Dinámicos**: Al seleccionar una consulta, el panel de controles se reconfigura en tiempo real (selectores de fecha para viajes, barras deslizadoras para umbrales de retraso en minutos, selectores de línea, etc.).
  3. **SQL Preview Reactivo**: Caja de código que muestra la sentencia SQL exacta parametrizada que se ejecutará en Oracle, ideal para explicaciones y defensa ante el catedrático.
  4. **Ejecución y Tabla de Resultados**: Al pulsar **"Ejecutar Consulta"**, un hilo asíncrono `QueryWorker` ejecuta la sentencia en `FREEPDB1` y puebla la tabla con paginación fluida.

---

## 5. Matriz de Procedimientos Almacenados y Funciones PL/SQL

El siguiente cuadro resume el enlace entre la interfaz gráfica y la lógica interna de base de datos:

| Objeto PL/SQL | Tipo | Invocado Desde (Vista / Acción) | Propósito de Negocio |
| :--- | :---: | :--- | :--- |
| `SP_REGISTRAR_INGRESO` | SP | `cards_interface.py` &rarr; Torniquete | Valida tarjeta, deduce tarifa ($2.90) e inserta en `VIAJE_PASAJERO`. |
| `SP_RECARGAR_TARJETA` | SP | `cards_interface.py` &rarr; Recargas | Acredita monto, actualiza `TARJETA` y genera comprobante en `RECARGA`. |
| `SP_CREAR_ORDEN_MANTENIMIENTO` | SP | `fleet_interface.py` &rarr; Modal Taller | Genera orden, asigna técnico y pasa el tren a `'En Mantenimiento'`. |
| `SP_REGISTRAR_INCIDENTE` | SP | `incidents_interface.py` &rarr; Modal Incidente | Registra contingencia y relaciona los activos afectados en red. |
| `SP_CANCELAR_VIAJES_AFECTADOS`| SP | `incidents_interface.py` &rarr; Cancelar Viajes| Pasa a `'Cancelado'` los despachos que cruzan activos clausurados. |
| `SP_PROGRAMAR_VIAJE` | SP | Módulo de Despacho | Valida disponibilidad de tren y maquinista certificado antes de despachar. |
| `FN_SALDO_TARJETA` | FN | `actions_service.py` | Retorna el saldo disponible de una tarjeta OMNY. |
| `FN_TARJETA_VALIDA` | FN | `actions_service.py` | Evalúa si la tarjeta está activa, vigente y con saldo $\ge \$2.90$. |
| `FN_TREN_DISPONIBLE` | FN | `actions_service.py` | Valida si un tren puede ser asignado sin órdenes de taller abiertas. |
| `FN_RUTA_OPERATIVA` | FN | `actions_service.py` | Retorna si una ruta está libre de incidentes bloqueantes. |
| `FN_COSTO_ORDEN_MANTENIMIENTO`| FN | `actions_service.py` | Calcula en vivo el costo acumulado de repuestos y técnicos en una orden. |

---

## 6. Solución de Problemas Frecuentes (Troubleshooting)

### A. Error `ORA-12541: TNS:no listener` o `ORA-12514`
- **Causa**: El servicio del Listener de Oracle no está activo o la PDB `FREEPDB1` no se ha abierto.
- **Solución**:
  Abra PowerShell como Administrador y ejecute:
  ```powershell
  lsnrctl start
  sqlplus sys/oracle as sysdba
  SQL> alter pluggable database all open;
  SQL> exit;
  ```

### B. Error `ORA-01017: invalid username/password`
- **Causa**: La contraseña del usuario de base de datos difiere de la predeterminada.
- **Solución**: Revise el archivo `prototypes/desktop/config.py` y ajuste las credenciales `DB_USER` y `DB_PASSWORD` para que coincidan con su instalación local.

### C. Error de Escala o Borrosidad en Pantallas 4K (High-DPI)
- **Causa**: Windows aplica un factor de reescalado automático al proceso de Python.
- **Solución**: La aplicación incluye en `prototypes/desktop/main.py` la directiva `QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)`, garantizando bordes nítidos y fuentes vectoriales claras en cualquier resolución.
