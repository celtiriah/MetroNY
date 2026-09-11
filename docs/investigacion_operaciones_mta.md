# Investigación Operativa: Funcionamiento del Metro de Nueva York (MTA NYCT)

> **Documento Técnico y Metodológico de Referencia para el Proyecto MetroNY**  
> Este documento detalla la estructura física, operativa, tarifaria y de mantenimiento del sistema de metro real de la ciudad de Nueva York (MTA New York City Transit), estableciendo el mapeo directo con el modelo relacional Oracle, la lógica PL/SQL y la interfaz de escritorio de MetroNY.

---

## 1. División Histórica del Sistema: División A vs División B

El metro de Nueva York es el resultado de la integración de tres antiguas empresas competidoras: **IRT** (*Interborough Rapid Transit*), **BMT** (*Brooklyn-Manhattan Transit*) y **IND** (*Independent Subway System*). En la actualidad, el sistema permanece dividido operativamente en dos divisiones **físicamente incompatibles**:

### 1.1 División A (Líneas IRT - Rutas Numeradas)
* **Líneas**: 1, 2, 3, 4, 5, 6, 7 y el servicio de lanzadera *42nd St Shuttle* (S).
* **Gálibo y Dimensiones de Túneles**: Construidos a partir de 1904 con curvas más cerradas y gálibo estrecho.
* **Dimensiones de Vagones**: Ancho de **2.67 metros (8 ft 9 in)** y longitud de **15.5 metros (51 ft)**.
* **Flota de Trenes**: Series R62, R62A, R142, R142A, R188.

### 1.2 División B (Líneas BMT / IND - Rutas con Letras)
* **Líneas**: A, B, C, D, E, F, G, J, L, M, N, Q, R, W, Z y lanzaderas (*Franklin Av Shuttle*, *Rockaway Park Shuttle*).
* **Gálibo y Dimensiones de Túneles**: Diseñados posteriormente con especificaciones más amplias y estaciones de mayor longitud.
* **Dimensiones de Vagones**: Ancho de **3.05 metros (10 ft)** y longitud de **18.3 a 22.8 metros (60 a 75 ft)**.
* **Flota de Trenes**: Series R46, R68, R68A, R160, R179, R211.

### 1.3 Regla Operativa Crítica para el Proyecto
> [!IMPORTANT]
> Un tren de la División B **no puede ingresar físicamente** a un túnel de la División A (colisionaría con las paredes y andenes).  
> **Mapeo en MetroNY**: La entidad `DIVISION` se vincula con `MODELO_TREN` y `LINEA`. El procedimiento `SP_PROGRAMAR_VIAJE` debe validar que la división del tren asignado coincida obligatoriamente con la división de la línea donde operará la ruta.

---

## 2. Operación de Vías: Troncales, Servicios Locales vs Expresos

A diferencia de la mayoría de los metros del mundo (que operan con doble vía fija y paradas uniformes), el metro de Nueva York utiliza un sistema de vías múltiples altamente dinámico:

### 2.1 Vías Cuádruples (Quadruple Track) en Grandes Avenidas
En los corredores troncales de Manhattan (Lexington Avenue, 8th Avenue, 7th Avenue, Broadway, Queens Boulevard), existen **3 o 4 vías paralelas**:
* **Vías Exteriores (Servicio Local)**: Se detienen en todas y cada una de las estaciones del tramo (ej. línea 1 o 6 local).
* **Vías Interiores (Servicio Expreso)**: Omiten estaciones secundarias y sólo se detienen en nudos de correspondencia neurálgicos (ej. líneas 2, 3, 4, 5, A, D).

### 2.2 Vía Central Reversible en Horas Punta (Peak-Direction Express)
En líneas de tres vías (como la Línea 7 en Queens o la Línea 6 en el Bronx):
* Por la mañana, la vía central opera como expreso hacia Manhattan (*Manhattan-bound*).
* Por la tarde/noche, la misma vía se invierte para operar como expreso hacia los distritos exteriores (*Outbound*).
* Se identifican visualmente con un rombo en la señalética: `<6>`, `<7>`.

### 2.3 Complejos de Estaciones (Transfer Stations)
Estaciones originalmente independientes están conectadas bajo tierra mediante pasillos peatonales intermedios dentro de la zona de pago (ej. *Times Square - 42nd St / Port Authority*, *Fulton Center*, *Atlantic Av - Barclays Ctr*).

* **Mapeo en MetroNY**:
  * La tabla `PLATAFORMA` modela los andenes específicos asignados a vías locales o expresas.
  * La tabla `ESTACION_COMPLEJO` y `TRANSFERENCIA` gestiona las conexiones peatonales internas.
  * La tabla `RUTA` define secuencias de paradas diferenciadas (`secuencia_parada`) para itinerarios locales o expresos sobre la misma línea troncal.

---

## 3. Sistema de Peaje y Validación: OMNY, MetroCard y Reglas Tarifarias

### 3.1 Estructura Tarifaria Plana (Flat Fare)
* **Tarifa Estándar**: **$2.90 USD** por viaje simple (subterráneo + autobús local).
* **Tarifa Reducida (*Reduced-Fare*)**: **$1.45 USD** para adultos mayores (65+ años) y personas con discapacidad certificada.

### 3.2 Sistema Contactless OMNY (*One Metro New York*)
OMNY permite validar el ingreso directamente en los torniquetes mediante tarjetas bancarias sin contacto, dispositivos móviles (Apple Pay / Google Wallet) o la tarjeta física prepago OMNY.

* **Tope Tarifario Semanal (7-Day Fare Capping)**:
  * En una ventana de 7 días consecutivos, los primeros **12 viajes son cobrados** ($2.90 × 12 = $34.80 USD).
  * A partir del 13.º viaje con el mismo medio de pago, **todos los viajes subsiguientes son gratuitos** hasta que finalice el ciclo de 7 días.
* **Transbordos Gratuitos (Free Transfer - 2 Horas)**:
  * Todo pasajero tiene derecho a **un transbordo gratuito** dentro de los **120 minutos (2 horas)** posteriores a la primera validación.
  * Aplica entre metro y autobús local, o entre estaciones de metro seleccionadas con transferencia fuera de torniquete (ej. Lexington Av/63rd St a 59th St).

* **Mapeo en MetroNY**:
  * `TARJETA`, `TARIFA`, `PAGO_RECARGA`, `VIAJE_PASAJERO`.
  * **Procedimiento `SP_REGISTRAR_INGRESO`**: Deduce $2.90 (o $1.45), verifica saldo disponible $\ge$ tarifa, bloquea paso si la tarjeta está en estado `Bloqueada` o `Vencida`, y registra el paso en el torniquete.
  * **Procedimiento `SP_RECARGAR_TARJETA`**: Abona saldo a la tarjeta y registra la transacción en `PAGO_RECARGA`.
  * **Módulo 5 Desktop (`cards_interface.py`)**: Interfaz visual de torniquete interactivo con indicador lumínico (Paso Autorizado Verde / Saldo Insuficiente Rojo).

---

## 4. Parque Móvil, Cocheras y Mantenimiento Técnico

El material rodante de la MTA se distribuye y mantiene en **24 depósitos y talleres (Yards & Shops)**:

### 4.1 Talleres de Gran Reparación (Overhaul Shops)
* **Coney Island Complex (Brooklyn)**: El mayor taller ferroviario metropolitano del mundo, encargado de revisiones pesadas, cambio de bogies y motores de tracción para la División B.
* **207th Street Overhaul Shop (Alto Manhattan)**: Taller principal para la División A y material rodante de mantenimiento de vía.

### 4.2 Ciclos de Inspección Programada (SMS - Scheduled Maintenance Service)
* **Inspecciones SMS (cada 30 a 90 días)**: Verificación rigurosa de zapatas de freno, compresores, patines colectores de tercer riel (600/750V DC), sistemas de puertas neumáticas y climatización (HVAC).
* **Composiciones Fijas**: Los coches operan agrupados en parejas fijas (*married pairs* A-B) o formaciones semirreversibles de 4, 5, 8, 10 u 11 vagones acoplados.

* **Mapeo en MetroNY**:
  * Tablas `TALLER`, `DEPOSITO`, `TREN`, `VAGON`, `ORDEN_MANTENIMIENTO`.
  * **Procedimiento `SP_CREAR_ORDEN_MANTENIMIENTO`**: Cambia automáticamente el estado del tren a `'En Mantenimiento'` y asigna al taller y técnico responsable.
  * **Trigger `TRG_TREN_MANTENIMIENTO_NO_ASIGNAR`**: Impide que la base de datos permita programar viajes a un tren con orden de taller abierta.
  * **Consulta 7 del catálogo**: Filtra trenes con más de 90 días desde su última fecha de revisión técnica.

---

## 5. Personal Operativo y Despacho Ferroviario

Un tren comercial en Nueva York opera con una tripulación de **dos personas** (salvo líneas automatizadas o cortas con régimen OPTO - *One-Person Train Operation*):

1. **Maquinista / Conductor (Train Operator / Motorman)**:
   * Ubicado en la cabina delantera. Conduce la unidad, vigila la señalización en vía y controla aceleración/frenado.
2. **Jefe de Tren (Conductor)**:
   * Ubicado en la cabina intermedia (generalmente coche 5 o 6). Responsable de la apertura y cierre de puertas tras verificar el despeje visual del andén (*point to the zebra board*), y emite anuncios a pasajeros.
3. **Puesto de Control Centralizado (RCC - Rail Control Center)**:
   * Supervisa en tiempo real toda la red metropolitana, coordina enclavamientos, desvíos y respuesta a emergencias.
4. **Habilitaciones y Certificaciones**:
   * Las licencias no son genéricas: exigen certificación por **División (A o B)**, por **Tipo de Tren** (tecnología moderna NTT vs trenes electromecánicos SMEE) y por **Línea / Ruta** (conocimiento de pendientes y límites de velocidad).

* **Mapeo en MetroNY**:
  * Tablas `EMPLEADO`, `CARGO`, `TURNO`, `CERTIFICACION`.
  * **Vista `VW_CERTIFICACIONES_POR_VENCER`**: Detecta licencias que expiran en menos de 30 días para evitar suspensiones operativas.
  * **Procedimiento `SP_PROGRAMAR_VIAJE`**: Verifica que el empleado asignado tenga cargo de maquinista, certificación vigente y sin solapamiento de turnos.

---

## 6. Gestión de Incidencias Operativas (Operación Continua 24/7)

El metro de Nueva York opera **24 horas al día, 365 días al año**. Al no cerrar durante la noche, el mantenimiento de vías y la gestión de contingencias se realiza bajo tráfico constante:

### 6.1 Tipología Real de Incidencias MTA
* `Fallo de Señalización`: Falsa ocupación de circuito de vía o semáforo en rojo preventivo.
* `Condición de Vía`: Deformación térmica del riel, presencia de objetos o pérdida de energía en tercer riel.
* `Emergencia Médica`: Pasajero descompensado en vagón o andén que requiere asistencia de paramédicos del FDNY.
* `Investigación Policial / Persona en Vía`: Desconexión de corriente de tracción por seguridad.
* `Activación Freno de Emergencia`: Disparo de la válvula por obstáculo (*trip-cock*) o acción de un pasajero.

### 6.2 Estrategias de Despacho para Mitigar Retrasos
* **Rerouting (Desvío de Ruta)**: Trenes de una línea son derivados por la vía troncal de otra línea (ej. trenes F circulando por la vía E).
* **Running Light (Paso a Expreso)**: Un tren local es despachado por la vía rápida para recuperar intervalo (*headway*).
* **Short-Turning (Corte de Recorrido)**: El tren finaliza antes de su terminal para dar la vuelta en un escape y rellenar un hueco en el sentido opuesto.

* **Mapeo en MetroNY**:
  * Tablas `INCIDENTE`, `INCIDENTE_ELEMENTO`, `AFECTACION`.
  * **Procedimiento `SP_REGISTRAR_INCIDENTE`**: Registra el evento, gravedad (Baja, Media, Alta, Crítica) y elementos afectados (`LINEA`, `ESTACION`, `TRAMO_VIA`).
  * **Procedimiento `SP_CANCELAR_VIAJES_AFECTADOS`**: Cancela o reprograma de forma automática los viajes que se dirigen a un tramo cerrado.
  * **Módulo 7 Desktop (`incidents_interface.py`)**: Monitor de incidencias activas con cálculo de retrasos en cascada.

---

## 7. Matriz de Mapeo: Realidad MTA vs Arquitectura MetroNY

| Concepto Operativo MTA | Objeto en Base de Datos Oracle | Componente en App Desktop Fluent |
| :--- | :--- | :--- |
| Incompatibilidad de Gálibo (Div A vs B) | `DIVISION`, `MODELO_TREN`, `LINEA` | Filtros por división en catálogo y flota |
| 4 Vías (Expreso / Local) | `PLATAFORMA`, `RUTA`, `RUTA_ESTACION` | Directorio de andenes y detalle de rutas |
| Cobro $2.90 y Tarjeta OMNY | `TARJETA`, `TARIFA`, `SP_REGISTRAR_INGRESO` | Simulador interactivo de torniquete (Módulo 5) |
| Recargas de Saldo | `PAGO_RECARGA`, `SP_RECARGAR_TARJETA` | Formulario de recarga con confirmación Fluent |
| Retirada a Taller (SMS) | `TALLER`, `ORDEN_MANTENIMIENTO`, `SP_CREAR_ORDEN` | Botón "Enviar a Mantenimiento" en flota |
| Bloqueo de Tren en Taller | `TRG_TREN_MANTENIMIENTO_NO_ASIGNAR` | Advertencia y bloqueo en asignación de tren |
| Certificación de Maquinistas | `CERTIFICACION`, `VW_CERTIFICACIONES_POR_VENCER` | Indicadores de licencias y turnos en personal |
| Alerta de Contingencias 24/7 | `INCIDENTE`, `SP_REGISTRAR_INCIDENTE` | Panel de incidentes en tiempo real y severidad |
| Supresión por Vía Afectada | `SP_CANCELAR_VIAJES_AFECTADOS` | Reflejo inmediato en el panel de viajes activos |
