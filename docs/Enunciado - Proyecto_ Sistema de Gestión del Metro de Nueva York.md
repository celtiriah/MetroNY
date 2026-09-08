# Proyecto: Sistema de Gestión del Metro de Nueva York

## 1\. Descripción general

La Autoridad Metropolitana de Transporte de Nueva York requiere desarrollar un sistema de información para administrar la operación de su red de metro.

El sistema deberá registrar la infraestructura ferroviaria, las líneas, estaciones, rutas, trenes, recorridos, horarios, personal operativo, mantenimiento, incidencias y utilización del servicio por parte de los pasajeros.

El proyecto se desarrollará utilizando una base de datos Oracle. Como primera etapa, los estudiantes deberán analizar el enunciado, identificar las entidades, atributos, relaciones, cardinalidades y restricciones necesarias, y construir el correspondiente modelo entidad-relación.

Posteriormente, el modelo deberá transformarse en un esquema relacional e implementarse en Oracle.

Para efectos académicos, el sistema será una representación simplificada inspirada en el funcionamiento del metro de Nueva York; no es necesario reproducir exactamente todos los procesos de la red real.  
---

## 2\. Funcionamiento general de la red

La red está conformada por líneas de metro identificadas mediante una letra, número o código. Por ejemplo, podrían existir las líneas A, B, C, 1, 2 y 3\.

Cada línea deberá registrar:

* Código de identificación.  
* Nombre descriptivo.  
* Color utilizado en los mapas.  
* Terminal de origen.  
* Terminal de destino.  
* Estado operativo.  
* Tipo de servicio.  
* Fecha de inauguración.  
* Longitud aproximada.  
* Operador responsable.

Una línea puede prestar diferentes tipos de servicio:

* Servicio local: se detiene en todas las estaciones de su recorrido.  
* Servicio expreso: se detiene únicamente en determinadas estaciones.  
* Servicio nocturno.  
* Servicio especial por eventos.  
* Servicio temporal por mantenimiento o contingencia.

Una misma estación puede ser utilizada por varias líneas. De igual manera, una línea recorre varias estaciones en un orden determinado.

Por esta razón, el sistema deberá almacenar la secuencia en la cual una línea visita sus estaciones, la distancia entre estaciones consecutivas y el tiempo estimado de viaje entre ellas.

---

## 3\. Gestión de estaciones

Cada estación deberá registrarse con la siguiente información:

* Código único.  
* Nombre.  
* Dirección.  
* Distrito o borough.  
* Latitud y longitud.  
* Fecha de inauguración.  
* Cantidad de accesos.  
* Cantidad de plataformas.  
* Estado operativo.  
* Horario de funcionamiento.  
* Disponibilidad de elevadores.  
* Disponibilidad de escaleras eléctricas.  
* Accesibilidad para personas con discapacidad.  
* Servicios disponibles.

Los distritos considerados podrán ser:

* Manhattan.  
* Brooklyn.  
* Queens.  
* The Bronx.  
* Staten Island, si el profesor decide incluir una red complementaria.

Una estación puede contener varias plataformas. Cada plataforma deberá tener un identificador, dirección de viaje, capacidad aproximada y estado operativo.

Las estaciones podrán clasificarse como:

* Estación local.  
* Estación expresa.  
* Terminal.  
* Estación de transferencia.  
* Estación temporalmente cerrada.

En una estación de transferencia, los pasajeros podrán cambiar de una línea a otra. El sistema deberá indicar entre qué líneas es posible realizar la transferencia y el tiempo estimado para efectuarla.

Una estación puede disponer de diferentes servicios, como:

* Venta y recarga de tarjetas.  
* Máquinas expendedoras.  
* Servicios sanitarios.  
* Policía o seguridad.  
* Atención al pasajero.  
* Elevadores.  
* Escaleras eléctricas.  
* Acceso para bicicletas.  
* Conexión con autobuses.  
* Conexión con trenes regionales.

Los elevadores y escaleras eléctricas deberán manejarse como equipos de la estación, ya que pueden encontrarse disponibles, en mantenimiento o fuera de servicio.

---

## 4\. Rutas y recorridos

Una ruta representa el recorrido realizado por una línea entre una estación de origen y una estación de destino.

Cada ruta deberá contener:

* Código de ruta.  
* Línea a la que pertenece.  
* Estación de origen.  
* Estación de destino.  
* Sentido del recorrido.  
* Tipo de servicio.  
* Distancia total.  
* Duración estimada.  
* Estado.  
* Fecha de vigencia.

Una línea puede tener diferentes rutas según:

* El sentido del viaje.  
* El horario.  
* El día de la semana.  
* El tipo de servicio.  
* La existencia de cierres temporales.  
* El mantenimiento de una sección de la vía.

Cada ruta estará formada por una secuencia ordenada de estaciones. Para cada estación incluida en la ruta se deberá registrar:

* Orden de llegada.  
* Hora estimada de llegada.  
* Hora estimada de salida.  
* Distancia desde la estación anterior.  
* Tiempo estimado desde la estación anterior.  
* Indicación de si el tren se detiene o solamente pasa por la estación.

Esta última condición permitirá representar los servicios expresos.

---

## 5\. Horarios y programación del servicio

El sistema deberá permitir definir horarios de operación para cada ruta.

Un horario deberá especificar:

* Ruta asociada.  
* Día de la semana.  
* Hora de inicio.  
* Hora de finalización.  
* Frecuencia programada.  
* Tipo de servicio.  
* Fecha desde la que entra en vigor.  
* Fecha hasta la que permanece vigente.

La frecuencia representa el tiempo aproximado entre la salida de dos trenes consecutivos.

Por ejemplo:

* Cada 4 minutos en hora pico.  
* Cada 8 minutos durante el día.  
* Cada 15 minutos durante la noche.

Un horario puede aplicarse a días laborales, fines de semana, días festivos o fechas especiales.

A partir de un horario se generarán viajes programados. Cada viaje representa la ejecución concreta de una ruta en una fecha y hora determinadas.

Cada viaje deberá registrar:

* Número de viaje.  
* Ruta programada.  
* Fecha.  
* Hora programada de salida.  
* Hora real de salida.  
* Hora programada de llegada.  
* Hora real de llegada.  
* Tren asignado.  
* Conductor asignado.  
* Estado del viaje.  
* Cantidad estimada de pasajeros.

Los estados posibles de un viaje pueden ser:

* Programado.  
* En abordaje.  
* En curso.  
* Completado.  
* Retrasado.  
* Cancelado.

---

## 6\. Trenes y vagones

La organización cuenta con una flota de trenes. Cada tren tendrá:

* Código interno.  
* Modelo.  
* Fabricante.  
* Año de fabricación.  
* Capacidad total.  
* Estado operativo.  
* Kilometraje acumulado.  
* Depósito asignado.  
* Fecha de la última inspección.  
* Fecha de la próxima inspección.

Los trenes podrán encontrarse en los siguientes estados:

* Disponible.  
* En operación.  
* En mantenimiento.  
* Fuera de servicio.  
* Retirado.

Cada tren está compuesto por uno o más vagones. De cada vagón deberá almacenarse:

* Número de serie.  
* Tipo de vagón.  
* Capacidad de pasajeros sentados.  
* Capacidad de pasajeros de pie.  
* Año de fabricación.  
* Posición dentro del tren.  
* Estado.  
* Disponibilidad de accesibilidad.

Un vagón solamente podrá pertenecer a un tren en una fecha determinada. Sin embargo, los vagones pueden cambiarse de un tren a otro, por lo que se deberá conservar el historial de sus asignaciones.

Antes de asignar un tren a un viaje, el sistema deberá comprobar que se encuentre disponible y que no tenga un mantenimiento pendiente que impida su utilización.

---

## 7\. Personal operativo

El sistema deberá administrar a los empleados relacionados con la operación del metro.

De cada empleado se registrará:

* Número de empleado.  
* Nombre completo.  
* Fecha de nacimiento.  
* Dirección.  
* Teléfono.  
* Correo electrónico.  
* Fecha de contratación.  
* Cargo.  
* Turno.  
* Salario.  
* Estado laboral.  
* Supervisor.

Los empleados podrán desempeñar cargos como:

* Conductor.  
* Operador de control.  
* Supervisor de estación.  
* Técnico de mantenimiento.  
* Agente de seguridad.  
* Personal de atención al pasajero.

Un empleado puede tener diferentes certificaciones. Por ejemplo, un conductor deberá contar con una certificación vigente para operar determinados modelos de tren.

Cada certificación deberá incluir:

* Tipo de certificación.  
* Fecha de emisión.  
* Fecha de vencimiento.  
* Institución emisora.  
* Estado.  
* Modelos de tren autorizados.

Un empleado no podrá ser asignado a dos viajes cuyos horarios se traslapen. Asimismo, no podrá asignarse como conductor si su certificación está vencida.

---

## 8\. Turnos y asignaciones

Los empleados trabajan en turnos previamente programados.

Cada turno deberá registrar:

* Código del turno.  
* Empleado asignado.  
* Fecha.  
* Hora de inicio.  
* Hora de finalización.  
* Lugar de trabajo.  
* Función que realizará.  
* Estado de asistencia.

Un turno puede asignarse a una estación, un tren, un depósito, una ruta o un centro de control, dependiendo del cargo del empleado.

El sistema deberá impedir que un empleado tenga turnos superpuestos.

También deberá registrar ausencias, permisos, vacaciones y sustituciones.

---

## 9\. Pasajeros, tarjetas y pagos

El sistema podrá registrar pasajeros frecuentes que utilicen una tarjeta electrónica para ingresar al metro.

No es obligatorio registrar individualmente a todos los pasajeros. También se deberán permitir viajes anónimos realizados con boletos o tarjetas no personalizadas.

De un pasajero registrado se almacenará:

* Identificador.  
* Nombre.  
* Fecha de nacimiento.  
* Correo electrónico.  
* Teléfono.  
* Tipo de pasajero.  
* Fecha de registro.  
* Estado.

Los tipos de pasajero pueden incluir:

* Regular.  
* Estudiante.  
* Adulto mayor.  
* Persona con discapacidad.  
* Empleado autorizado.

Cada tarjeta electrónica deberá registrar:

* Número de tarjeta.  
* Pasajero propietario, cuando corresponda.  
* Fecha de emisión.  
* Fecha de vencimiento.  
* Saldo disponible.  
* Tipo de tarifa.  
* Estado.

Los estados de una tarjeta podrán ser:

* Activa.  
* Bloqueada.  
* Vencida.  
* Reportada como perdida.  
* Cancelada.

Una tarjeta puede recibir múltiples recargas. Cada recarga deberá almacenar:

* Número de transacción.  
* Fecha y hora.  
* Monto.  
* Medio de pago.  
* Estación o canal donde se realizó.  
* Saldo anterior.  
* Saldo posterior.

---

## 10\. Registro de viajes de pasajeros

Cuando un pasajero utiliza una tarjeta para ingresar al metro, el sistema registrará una transacción de acceso.

Cada viaje de pasajero deberá contener:

* Número de transacción.  
* Tarjeta utilizada.  
* Estación de ingreso.  
* Fecha y hora de ingreso.  
* Estación de salida, cuando se registre.  
* Fecha y hora de salida.  
* Tarifa aplicada.  
* Monto cobrado.  
* Estado de la transacción.

El sistema deberá validar que:

* La tarjeta esté activa.  
* La tarjeta no esté vencida.  
* Exista saldo suficiente.  
* La estación de ingreso esté operativa.  
* No exista otro viaje abierto con la misma tarjeta.

Los viajes anónimos deberán registrarse sin necesidad de asociarlos con una persona.

---

## 11\. Tarifas

El precio del servicio dependerá del tipo de pasajero, del producto adquirido o de las reglas definidas por la organización.

Cada tarifa deberá tener:

* Código.  
* Nombre.  
* Descripción.  
* Monto.  
* Tipo de pasajero.  
* Fecha de inicio de vigencia.  
* Fecha de finalización.  
* Cantidad máxima de viajes, si corresponde.  
* Duración del beneficio.  
* Estado.

El sistema deberá conservar el historial de tarifas. Si el precio cambia, no deberá modificarse el valor de las transacciones realizadas anteriormente.

Podrán existir productos como:

* Viaje individual.  
* Pase diario.  
* Pase semanal.  
* Pase mensual.  
* Tarifa reducida.  
* Pase estudiantil.

---

## 12\. Mantenimiento

Los trenes, vagones, vías, señales, plataformas, elevadores y escaleras eléctricas requieren mantenimiento periódico.

Cada equipo deberá contar con:

* Código del equipo.  
* Tipo.  
* Ubicación.  
* Fabricante.  
* Modelo.  
* Número de serie.  
* Fecha de instalación.  
* Estado.  
* Fecha de la última revisión.  
* Fecha de la próxima revisión.

Una orden de mantenimiento deberá registrar:

* Número de orden.  
* Equipo afectado.  
* Tipo de mantenimiento.  
* Descripción del trabajo.  
* Fecha de solicitud.  
* Fecha programada.  
* Fecha de inicio.  
* Fecha de finalización.  
* Técnico responsable.  
* Prioridad.  
* Costo.  
* Estado.

Los tipos de mantenimiento pueden ser:

* Preventivo.  
* Correctivo.  
* Predictivo.  
* Inspección de seguridad.

Los estados de una orden pueden ser:

* Solicitada.  
* Programada.  
* En ejecución.  
* Suspendida.  
* Completada.  
* Cancelada.

Una orden puede requerir varios técnicos y diferentes repuestos. El sistema deberá registrar la cantidad y costo de los repuestos utilizados.

---

## 13\. Incidentes operativos

Durante la operación pueden presentarse incidentes que afecten una estación, un tren, una ruta o un tramo de la red.

Cada incidente deberá registrar:

* Número de incidente.  
* Tipo.  
* Descripción.  
* Fecha y hora de inicio.  
* Fecha y hora de finalización.  
* Lugar afectado.  
* Nivel de severidad.  
* Persona que lo reportó.  
* Estado.  
* Causa identificada.  
* Acciones realizadas.  
* Cantidad estimada de pasajeros afectados.

Los tipos de incidente pueden ser:

* Falla mecánica.  
* Falla eléctrica.  
* Falla de señalización.  
* Emergencia médica.  
* Accidente.  
* Problema de seguridad.  
* Objeto en la vía.  
* Inundación.  
* Incendio.  
* Congestión.  
* Mantenimiento no programado.

Los niveles de severidad podrán ser:

* Bajo.  
* Medio.  
* Alto.  
* Crítico.

Un incidente puede provocar:

* Retraso de uno o varios viajes.  
* Cancelación de viajes.  
* Cierre temporal de una estación.  
* Cierre de una plataforma.  
* Suspensión de un tramo.  
* Cambio temporal de una ruta.  
* Retiro de un tren.

El sistema deberá conservar la relación entre el incidente y todos los elementos afectados.

---

## 14\. Objetivo del sistema

El sistema deberá permitir a la administración:

* Consultar la estructura completa de la red.  
* Conocer qué líneas pasan por una estación.  
* Consultar el orden de estaciones de una ruta.  
* Programar viajes.  
* Asignar trenes y conductores.  
* Controlar horarios y frecuencias.  
* Registrar entradas y salidas de pasajeros.  
* Administrar tarjetas y recargas.  
* Controlar tarifas.  
* Programar mantenimientos.  
* Registrar incidentes.  
* Consultar retrasos y cancelaciones.  
* Obtener estadísticas operativas.

---

# Funcionalidades requeridas

## Módulo 1: Administración de la red

Los estudiantes deberán implementar operaciones para:

* Crear, modificar, consultar y desactivar líneas.  
* Crear y modificar estaciones.  
* Asociar estaciones con líneas.  
* Definir el orden de las estaciones.  
* Registrar distancias y tiempos entre estaciones.  
* Administrar plataformas.  
* Definir estaciones de transferencia.  
* Consultar todas las líneas que pasan por una estación.  
* Consultar todas las estaciones de una línea en el orden correcto.

## Módulo 2: Rutas y horarios

El sistema deberá permitir:

* Crear rutas locales y expresas.  
* Establecer el sentido del recorrido.  
* Definir las paradas de cada ruta.  
* Configurar horarios por día.  
* Configurar frecuencias.  
* Generar viajes programados.  
* Cancelar o reprogramar viajes.  
* Consultar los próximos viajes de una estación.  
* Identificar rutas afectadas por cierres.

## Módulo 3: Trenes

El sistema deberá permitir:

* Registrar trenes y vagones.  
* Armar la composición de un tren.  
* Conservar el historial de vagones asignados.  
* Cambiar el estado de un tren.  
* Consultar disponibilidad.  
* Asignar un tren a un viaje.  
* Impedir asignaciones simultáneas.  
* Impedir el uso de trenes en mantenimiento.

## Módulo 4: Personal

Se deberá poder:

* Registrar empleados.  
* Asignar cargos y supervisores.  
* Registrar certificaciones.  
* Programar turnos.  
* Asignar conductores a viajes.  
* Controlar vencimiento de certificaciones.  
* Detectar traslapes de turnos.  
* Registrar ausencias y sustituciones.

## Módulo 5: Pasajeros y tarjetas

El sistema deberá permitir:

* Registrar pasajeros.  
* Emitir tarjetas.  
* Recargar saldo.  
* Bloquear tarjetas.  
* Registrar el ingreso y salida.  
* Cobrar la tarifa aplicable.  
* Consultar saldo.  
* Consultar el historial de viajes.  
* Registrar viajes anónimos.  
* Detectar tarjetas vencidas o sin saldo.

## Módulo 6: Mantenimiento

Se deberá poder:

* Registrar equipos.  
* Crear órdenes de mantenimiento.  
* Asignar técnicos.  
* Registrar repuestos.  
* Cambiar el estado de una orden.  
* Actualizar la fecha de última revisión.  
* Programar la próxima inspección.  
* Consultar mantenimientos vencidos.  
* Consultar equipos fuera de servicio.

## Módulo 7: Incidentes

El sistema deberá permitir:

* Registrar incidentes.  
* Clasificarlos por tipo y severidad.  
* Asociarlos con estaciones, trenes, rutas o equipos.  
* Registrar los viajes afectados.  
* Registrar acciones correctivas.  
* Cerrar incidentes.  
* Calcular su duración.  
* Consultar incidentes abiertos.  
* Consultar incidentes críticos.  
* Obtener estadísticas por tipo, línea o estación.

---

# Reglas de negocio obligatorias

El modelo deberá representar, como mínimo, las siguientes reglas:

1. Una línea recorre una o varias estaciones.  
2. Una estación puede pertenecer a varias líneas.  
3. El orden de las estaciones debe almacenarse para cada ruta.  
4. Una ruta pertenece a una sola línea.  
5. Una línea puede tener varias rutas.  
6. Una ruta puede tener diferentes horarios.  
7. Un viaje programado corresponde a una ruta y una fecha específica.  
8. Un tren no puede estar asignado a dos viajes simultáneos.  
9. Un conductor no puede atender dos viajes simultáneos.  
10. Un conductor debe poseer una certificación vigente.  
11. Un tren en mantenimiento no puede asignarse a un viaje.  
12. Un vagón no puede pertenecer simultáneamente a dos trenes.  
13. Una tarjeta puede pertenecer a un pasajero o ser anónima.  
14. Una tarjeta puede registrar muchas recargas y muchos viajes.  
15. El saldo de una tarjeta no puede ser negativo.  
16. Una tarjeta bloqueada o vencida no puede utilizarse.  
17. Las tarifas deben conservar un período de vigencia.  
18. Una transacción debe conservar la tarifa cobrada, aunque posteriormente cambie el precio.  
19. Una orden de mantenimiento corresponde a un equipo, pero puede involucrar a varios técnicos.  
20. Un incidente puede afectar varios elementos de la red.  
21. Una estación cerrada no puede permitir nuevos ingresos.  
22. Una estación de transferencia debe estar asociada con al menos dos líneas.  
23. La hora real de llegada no puede ser anterior a la hora real de salida del viaje.  
24. La fecha de finalización de un incidente no puede ser anterior a la fecha de inicio.  
25. Los registros históricos de viajes, pagos, asignaciones y mantenimientos no deberán eliminarse físicamente.

---

# Operaciones que deberán desarrollarse en Oracle

## Procedimientos almacenados

Como mínimo, se recomienda implementar:

1. SP\_PROGRAMAR\_VIAJE  
   Programa un viaje y valida la disponibilidad del tren y del conductor.  
2. SP\_REGISTRAR\_INGRESO  
   Valida la tarjeta, calcula la tarifa, descuenta el saldo y registra el ingreso.  
3. SP\_RECARGAR\_TARJETA  
   Registra una recarga y actualiza el saldo.  
4. SP\_CREAR\_ORDEN\_MANTENIMIENTO  
   Crea una orden y cambia el estado del equipo cuando corresponda.  
5. SP\_REGISTRAR\_INCIDENTE  
   Registra un incidente y los elementos afectados.  
6. SP\_CANCELAR\_VIAJES\_AFECTADOS  
   Cancela viajes debido al cierre de una estación o ruta.

## Funciones

Se suguiere las siguientes funciones que pueden ser de utilidad para el desarrollo de los modulos. 

* Calcular la duración real de un viaje.  
* Calcular los minutos de retraso.  
* Obtener el saldo de una tarjeta.  
* Determinar si una tarjeta es válida.  
* Calcular los ingresos de una estación.  
* Obtener la cantidad de pasajeros transportados por una línea.  
* Verificar si un tren está disponible.  
* Determinar si una ruta se encuentra operativa.  
* Calcular el costo total de una orden de mantenimiento.

## Triggers

Se recomienda implementar triggers para:

* Impedir que el saldo de una tarjeta sea negativo.  
* Registrar cambios de estado de trenes.  
* Registrar cambios de tarifas.  
* Actualizar el estado de un tren al iniciar un viaje.  
* Liberar el tren cuando el viaje finalice.  
* Impedir la asignación de un tren en mantenimiento.  
* Generar una alerta cuando una certificación esté vencida.  
* Mantener una bitácora de cambios importantes.

## Vistas

Recomienda las siguientes vistas para:

* Estado actual de las líneas.  
* Próximas salidas por estación.  
* Viajes retrasados.  
* Trenes disponibles.  
* Trenes en mantenimiento.  
* Incidentes abiertos.  
* Ingresos diarios por línea.  
* Estaciones con mayor cantidad de pasajeros.  
* Certificaciones próximas a vencer.

---

# Consultas mínimas

Se deberán construir consultas SQL que permitan responder:

1. ¿Qué líneas pasan por una estación determinada?  
2. ¿Cuáles son las estaciones de una ruta y en qué orden se visitan?  
3. ¿Qué estaciones permiten transferencia entre líneas?  
4. ¿Qué viajes están programados para una fecha?  
5. ¿Qué viajes presentan retrasos mayores a 15 minutos?  
6. ¿Qué trenes están disponibles?  
7. ¿Qué trenes tienen mantenimiento vencido?  
8. ¿Qué conductor fue asignado a cada viaje?  
9. ¿Cuántos pasajeros utilizaron cada línea durante un período?  
10. ¿Cuánto dinero se recaudó por día, estación y tipo de tarifa?  
11. ¿Cuáles son las estaciones con mayor flujo de pasajeros?  
12. ¿Qué incidentes permanecen abiertos?  
13. ¿Qué línea acumuló más retrasos?  
14. ¿Qué tarjetas fueron bloqueadas o vencieron?  
15. ¿Qué técnicos participaron en una orden de mantenimiento?

---

## Alcance recomendado del modelo entidad-relación

El modelo deberá tener aproximadamente entre 20 y 30 entidades. Algunas entidades candidatas son:

* Línea.  
* Estación.  
* Plataforma.  
* Servicio de estación.  
* Línea-estación.  
* Transferencia.  
* Ruta.  
* Detalle de ruta.  
* Horario.  
* Viaje programado.  
* Tren.  
* Vagón.  
* Composición del tren.  
* Depósito.  
* Empleado.  
* Cargo.  
* Certificación.  
* Turno.  
* Pasajero.  
* Tarjeta.  
* Recarga.  
* Tarifa.  
* Viaje de pasajero.  
* Equipo.  
* Orden de mantenimiento.  
* Técnico asignado.  
* Repuesto.  
* Incidente.  
* Elemento afectado.  
* Bitácora.

Los estudiantes no deberán limitarse a esta lista. Deberán determinar qué entidades son necesarias, cuáles pueden representarse como catálogos y cuáles requieren entidades asociativas.

---

# Entregables del proyecto

1. Documento de análisis del problema.  
2. Identificación de entidades y atributos.  
3. Modelo entidad-relación con:  
   * Entidades fuertes y débiles.  
   * Llaves primarias.  
   * Llaves candidatas.  
   * Relaciones.  
   * Cardinalidades.  
   * Participación total o parcial.  
   * Entidades asociativas.  
   * Atributos multivaluados o compuestos, si fueran necesarios.  
4. Diccionario de datos.  
5. Transformación al modelo relacional.  
6. Normalización hasta tercera forma normal.  
7. Script de creación de la base de datos en Oracle.  
8. Restricciones PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK y NOT NULL.  
9. Scripts de inserción de datos de prueba.  
10. Consultas SQL.  
11. Procedimientos, funciones y triggers en PL/SQL.  
12. Vistas para consultas operativas.  
13. Evidencias de pruebas.  
14. Manual breve de uso.  
15. Carátula con la información de los integrantes del grupo  
16. Presentación final y demostración del sistema.

Cada estudiante creará una carpeta de Google Drive para subir la documentación del proyecto y asegurarse de dar accesos al catedrático. El proyecto se desarrollara en grupo de 7 estudiantes. 