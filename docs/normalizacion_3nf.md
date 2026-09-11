# Dictamen Académico de Normalización en Tercera Forma Normal (3NF)
## Sistema de Gestión de la Red de Metro de Nueva York (MTA NYCT)

> **Entregable Oficial No. 6**: Demostración formal, teórica y matemática de la normalización del esquema relacional en Tercera Forma Normal (3NF), análisis de dependencias funcionales, teoremas de descomposición sin pérdida (Lossless Join) y justificación de la eliminación de atributos derivados.

---

## 1. Fundamentos Teóricos del Modelo Relacional

La teoría de normalización relacional, concebida originalmente por Edgar F. Codd (1970, 1972) y desarrollada por autores fundamentales como C.J. Date, R. Elmasri y S. Navathe, constituye la disciplina matemática que garantiza la integridad estructural de las bases de datos relacionales, eliminando anomalías de inserción, modificación y borrado, y mitigando la redundancia perjudicial de datos.

### 1.1 Definiciones Formales

1. **Dependencia Funcional ($X \to Y$)**:
   Sea una relación $R$ con un esquema de atributos $U$. Se dice que un conjunto de atributos $Y \subseteq U$ depende funcionalmente de $X \subseteq U$ (denotado como $X \to Y$) si y solo si para cualesquiera dos tuplas $t_1, t_2 \in R$, se cumple que:
   $$t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

2. **Superclave y Clave Candidata**:
   - Un subconjunto de atributos $K \subseteq U$ es una **Superclave** de $R$ si $K \to U$.
   - $K$ es una **Clave Candidata** si es una superclave minimal; es decir, ningún subconjunto propio $K' \subset K$ satisface $K' \to U$.
   - La **Clave Primaria (PK)** es la clave candidata seleccionada formalmente por el arquitecto de datos para identificar unívocamente las tuplas en el espacio físico.

3. **Atributos Primos y No Primos**:
   - Un atributo $A \in U$ es **primo** si pertenece a al menos una clave candidata de $R$.
   - Un atributo $A \in U$ es **no primo** si no forma parte de ninguna clave candidata.

---

## 2. Primera Forma Normal (1NF): Atomicidad y Ausencia de Grupos Repetitivos

### 2.1 Definición Formal
Una relación $R$ se encuentra en **Primera Forma Normal (1NF)** si y solo si:
1. El dominio de cada atributo contiene únicamente **valores atómicos** (indivisibles dentro del contexto del modelo).
2. No existen **grupos repetitivos** (arreglos, tuplas anidadas o listas de valores dentro de una sola celda).
3. Cada tupla presenta una estructura homogénea y unívocamente identificable mediante una clave primaria.

### 2.2 Descomposiciones Aplicadas en MetroNY para Satisfacer 1NF

#### A. Descomposición de Atributos Compuestos
En el análisis conceptual inicial, surgieron atributos no atómicos como los nombres de personas y las direcciones físicas. Siguiendo las directrices del catedrático, se descompusieron en atributos indivisibles:
- En `EMPLEADO` y `PASAJERO`: En lugar de una cadena desestructurada `nombre_completo`, se definieron atributos atómicos independientes: `NOMBRE`, `APELLIDO`, o componentes individuales de identificación.
- En `ESTACION`: En lugar de un campo de texto compuesto `ubicacion_geografica`, se fragmentó en:
  - `DIRECCION` (`VARCHAR2(150)`)
  - `BOROUGH` (`VARCHAR2(30)`)
  - `LATITUD` (`NUMBER(9,6)`)
  - `LONGITUD` (`NUMBER(9,6)`)
  Garantizando que cada celda almacene un escalar primitivo susceptible de filtrado, indexación B-Tree o funciones espaciales.

#### B. Eliminación de Colecciones y Atributos Multivaluados
En la red de MTA, numerosas entidades presentan colecciones de valores asociados. De haber persistido como campos multivaluados, se habría violado 1NF:
1. **Servicios de Estación**: Una estación dispone de múltiples servicios (Wi-Fi, baños, policía, venta OMNY). En lugar de almacenar cadenas separadas por comas `"WiFi, Baños, Policía"`, se creó la entidad asociativa independiente:
   $$\text{ESTACION\_SERVICIO}(\underline{\text{ID\_ESTACION\_SERVICIO}}, \text{ESTACION\_ID}, \text{TIPO\_SERVICIO}, \text{ESTADO})$$
2. **Horarios de Estación**: Los horarios de apertura y cierre varían según el día de la semana. Se extrajo la relación:
   $$\text{HORARIO\_ESTACION}(\underline{\text{ID\_HORARIO\_ESTACION}}, \text{ESTACION\_ID}, \text{DIA\_SEMANA}, \text{HORA\_APERTURA}, \text{HORA\_CIERRE})$$
3. **Repuestos por Orden de Trabajo**: Una intervención técnica consume múltiples piezas. Se extrajo:
   $$\text{ORDEN\_REPUESTO}(\underline{\text{ID\_ORDEN\_REPUESTO}}, \text{ORDEN\_ID}, \text{REPUESTO\_ID}, \text{CANTIDAD}, \text{COSTO\_UNITARIO})$$
4. **Técnicos por Orden de Mantenimiento**: Varios operarios participan en una misma orden con roles específicos. Se extrajo:
   $$\text{ORDEN\_TECNICO}(\underline{\text{ID\_ORDEN\_TECNICO}}, \text{ORDEN\_ID}, \text{EMPLEADO\_ID}, \text{HORAS\_TRABAJADAS}, \text{ROL\_EN\_ORDEN})$$
5. **Activos Afectados por Incidente**: Un descarrilamiento o inundación afecta simultáneamente estaciones, tramos de vía y trenes. Se extrajo:
   $$\text{INCIDENTE\_ELEMENTO\_AFECTADO}(\underline{\text{ID\_ELEMENTO\_AFECTADO}}, \text{INCIDENTE\_ID}, \text{TIPO\_ELEMENTO}, \text{ID\_ELEMENTO}, \dots)$$

**Conclusión 1NF**: Todas las 33 tablas del esquema operan con columnas escalares, sin repetición interna ni estructuras anidadas.

---

## 3. Segunda Forma Normal (2NF): Dependencia Funcional Completa

### 3.1 Definición Formal
Una relación $R$ se encuentra en **Segunda Forma Normal (2NF)** si y solo si:
1. Se encuentra en **Primera Forma Normal (1NF)**.
2. Todo atributo **no primo** $A \in U$ depende de manera funcional **completa** de cada clave candidata de $R$; es decir, ningún atributo no primo depende funcionalmente de un subconjunto propio de una clave candidata compuesta:
   $$\forall K \text{ (clave candidata)}, \; \forall A \notin K, \; \nexists K' \subset K \text{ tal que } K' \to A$$

> [!NOTE]
> **Teorema de Clave Simple**: Si la clave primaria de una tabla está compuesta por un único atributo ($|PK| = 1$), dicha tabla se encuentra **automáticamente en 2NF**, ya que no existen subconjuntos propios no vacíos de la clave de los cuales un atributo no primo pueda depender.

### 3.2 Análisis de Tablas con Claves Primarias Compuestas o Relaciones $N:M$

En el esquema `METRO_NY`, 27 tablas poseen claves primarias sintéticas simples (`ID_*`). Sin embargo, se analizaron exhaustivamente las tablas intermedias, asociativas y de composición que representan relaciones muchos a muchos:

#### A. Tabla `LINEA_ESTACION`
Representa la topología de parada de una línea en una estación.
- **Clave Candidata Natural**: $\{ \text{LINEA\_ID}, \text{ESTACION\_ID} \}$
- **Dependencias Funcionales**:
  $$\{ \text{LINEA\_ID}, \text{ESTACION\_ID} \} \to \text{ORDEN\_ESTACION}$$
  $$\{ \text{LINEA\_ID}, \text{ESTACION\_ID} \} \to \text{DISTANCIA\_KM\_ANTERIOR}$$
  $$\{ \text{LINEA\_ID}, \text{ESTACION\_ID} \} \to \text{TIEMPO\_MINUTOS\_ANTERIOR}$$
- **Evaluación**:
  - $\text{LINEA\_ID} \not\to \text{ORDEN\_ESTACION}$ (el orden solo tiene sentido en el contexto de una estación concreta recorrida por esa línea).
  - $\text{ESTACION\_ID} \not\to \text{ORDEN\_ESTACION}$ (una estación puede ser la 1ª para la Línea A y la 15ª para la Línea C).
  - Por lo tanto, la dependencia es **completa**. No existe dependencia parcial. $\implies$ **Satisface 2NF**.

#### B. Tabla `RUTA_DETALLE`
Detalla la secuencia programada de estaciones a lo largo de una variante de ruta.
- **Clave Candidata Natural**: $\{ \text{RUTA\_ID}, \text{ORDEN\_PARADA} \}$
- **Dependencias Funcionales**:
  $$\{ \text{RUTA\_ID}, \text{ORDEN\_PARADA} \} \to \text{ESTACION\_ID}$$
  $$\{ \text{RUTA\_ID}, \text{ORDEN\_PARADA} \} \to \text{SE\_DETIENE}$$
  $$\{ \text{RUTA\_ID}, \text{ORDEN\_PARADA} \} \to \text{HORA\_ESTIMADA\_LLEGADA}$$
- **Evaluación**:
  - Saber únicamente la $\text{RUTA\_ID}$ no determina la estación ni si se detiene, pues la ruta posee múltiples estaciones.
  - Saber únicamente el $\text{ORDEN\_PARADA}$ (ej. parada 4) tampoco determina la estación si no se conoce la ruta.
  - La dependencia es **completa respecto a la clave**. $\implies$ **Satisface 2NF**.

#### C. Tabla `TREN_VAGON`
Composición y acople físico de coches en un convoy ferroviario.
- **Clave Candidata Natural**: $\{ \text{TREN\_ID}, \text{VAGON\_ID} \}$ o $\{ \text{TREN\_ID}, \text{POSICION} \}$
- **Dependencias Funcionales**:
  $$\{ \text{TREN\_ID}, \text{VAGON\_ID} \} \to \text{POSICION}$$
  $$\{ \text{TREN\_ID}, \text{VAGON\_ID} \} \to \text{FECHA\_ACOPLE}$$
- **Evaluación**:
  - La posición que ocupa un vagón (ej. coche cabina 1 o remolque 6) y la fecha de acople dependen estrictamente de la formación de ese tren particular. $\implies$ **Satisface 2NF**.

---

## 4. Tercera Forma Normal (3NF): Eliminación de Dependencias Transitivas

### 4.1 Definición Formal
Una relación $R$ se encuentra en **Tercera Forma Normal (3NF)** si y solo si:
1. Se encuentra en **Segunda Forma Normal (2NF)**.
2. Para toda dependencia funcional no trivial $X \to A$ en $R$, se cumple al menos una de las siguientes condiciones:
   - $X$ es una **superclave** de $R$.
   - $A$ es un **atributo primo** de $R$ (forma general de Codd).

Dicho en términos operacionales clásicos: ningún atributo no primo debe depender **transitivamente** de la clave primaria. Es decir, no debe existir una cadena de dependencias:
$$PK \to Y \quad \land \quad Y \to Z$$
donde $Y$ no sea clave candidata y $Z$ sea un atributo no primo.

### 4.2 Descomposiciones Específicas Aplicadas en MetroNY para Alcanzar 3NF

A continuación se demuestran los casos de diseño donde una dependencia transitiva latente fue resuelta mediante descomposición relacional:

#### Caso 1: Flota de Trenes y Modelos de Fabricación
- **Esquema No Normalizado Potencial**:
  $$\text{TREN}(\underline{\text{ID\_TREN}}, \text{NUMERO\_TREN}, \text{MODELO\_NOMBRE}, \text{FABRICANTE}, \text{GALIBO}, \text{TIPO\_PROPULSION}, \text{ESTADO})$$
- **Dependencias Funcionales Presentes**:
  $$DF_1: \text{ID\_TREN} \to \text{NUMERO\_TREN}, \text{MODELO\_NOMBRE}, \text{ESTADO}$$
  $$DF_2: \text{MODELO\_NOMBRE} \to \text{FABRICANTE}, \text{GALIBO}, \text{TIPO\_PROPULSION}$$
- **Violación de 3NF**:
  $$\text{ID\_TREN} \to \text{MODELO\_NOMBRE} \to \text{FABRICANTE}$$
  Dado que $\text{MODELO\_NOMBRE}$ no es una superclave de $\text{TREN}$, el fabricante y el gálibo dependen transitivamente de $\text{ID\_TREN}$.
  - *Anomalía de Inserción*: No se podría registrar un nuevo modelo R211 adquirido por la MTA si aún no tiene un tren físico asignado.
  - *Anomalía de Modificación*: Si Bombardier cambia de razón social, habría que actualizar cientos de registros de trenes.
- **Descomposición 3NF Aplicada**:
  1. $\text{MODELO\_TREN}(\underline{\text{ID\_MODELO}}, \text{NOMBRE}, \text{FABRICANTE}, \text{GALIBO}, \text{TIPO\_PROPULSION}, \text{VELOCIDAD\_MAXIMA})$
  2. $\text{TREN}(\underline{\text{ID\_TREN}}, \text{NUMERO\_TREN}, \text{MODELO\_ID}^{FK}, \text{ESTADO\_OPERATIVO}, \text{KILOMETRAJE\_TOTAL}, \dots)$
  *Resultado*: En $\text{TREN}$, la única DF es $\text{ID\_TREN} \to \dots$, donde $\text{ID\_TREN}$ es superclave. En $\text{MODELO\_TREN}$, $\text{ID\_MODELO}$ es superclave. $\implies$ **3NF rigurosa**.

#### Caso 2: Intervenciones Técnicas y Catálogo de Repuestos
- **Esquema No Normalizado Potencial**:
  $$\text{ORDEN\_REPUESTO}(\underline{\text{ID}}, \text{ORDEN\_ID}, \text{CODIGO\_REPUESTO}, \text{NOMBRE\_REPUESTO}, \text{STOCK\_ALMACEN}, \text{CANTIDAD})$$
- **Dependencias Funcionales**:
  $$DF_1: \text{ID} \to \text{ORDEN\_ID}, \text{CODIGO\_REPUESTO}, \text{CANTIDAD}$$
  $$DF_2: \text{CODIGO\_REPUESTO} \to \text{NOMBRE\_REPUESTO}, \text{STOCK\_ALMACEN}$$
- **Violación de 3NF**: $\text{NOMBRE\_REPUESTO}$ depende de $\text{CODIGO\_REPUESTO}$, que no es superclave de la tabla de consumo.
- **Descomposición 3NF Aplicada**:
  1. $\text{REPUESTO}(\underline{\text{ID\_REPUESTO}}, \text{CODIGO}, \text{NOMBRE}, \text{DESCRIPCION}, \text{STOCK\_ACTUAL}, \text{COSTO\_UNITARIO})$
  2. $\text{ORDEN\_REPUESTO}(\underline{\text{ID\_ORDEN\_REPUESTO}}, \text{ORDEN\_ID}^{FK}, \text{REPUESTO\_ID}^{FK}, \text{CANTIDAD}, \text{COSTO\_UNITARIO})$
  *Resultado*: Se aísla el catálogo físico del inventario. El `COSTO_UNITARIO` en `ORDEN_REPUESTO` congela el valor histórico de la transacción sin depender transitivamente del catálogo actual. $\implies$ **3NF rigurosa**.

#### Caso 3: Viajes de Pasajeros y Esquema Tarifario
- **Esquema No Normalizado Potencial**:
  $$\text{VIAJE\_PASAJERO}(\underline{\text{ID}}, \text{TARJETA\_ID}, \text{TIPO\_TARIFA}, \text{DESCRIPCION\_TARIFA}, \text{VALOR\_OFICIAL\_MTA}, \text{FECHA\_HORA})$$
- **Violación de 3NF**: La descripción y el valor oficial dependen del tipo de tarifa ($Y \to Z$), generando redundancia sobre millones de transacciones de torniquete.
- **Descomposición 3NF Aplicada**:
  1. $\text{TARIFA}(\underline{\text{ID\_TARIFA}}, \text{CODIGO}, \text{NOMBRE}, \text{DESCRIPCION}, \text{MONTO}, \text{FECHA\_VIGENCIA\_INICIO}, \dots)$
  2. $\text{VIAJE\_PASAJERO}(\underline{\text{ID\_VIAJE\_PASAJERO}}, \text{TARJETA\_ID}^{FK}, \text{TARIFA\_ID}^{FK}, \text{MONTO\_COBRADO}, \text{FECHA\_HORA}, \dots)$
  *Resultado*: $\implies$ **3NF rigurosa**.

---

## 5. Teoremas de Descomposición Formal

Para garantizar la corrección matemática de la normalización del esquema de MetroNY, se comprobaron formalmente dos propiedades esenciales:

### 5.1 Propiedad de Reunión sin Pérdida de Información (Lossless Join)
Una descomposición de un esquema $R$ en dos esquemas $R_1$ y $R_2$ (con conjuntos de atributos $U_1$ y $U_2$, donde $U = U_1 \cup U_2$) tiene **Reunión sin Pérdida** con respecto a un conjunto de dependencias funcionales $F$ si y solo si la proyección de la reunión natural recupera exactamente $R$:
$$R = \pi_{U_1}(R) \bowtie \pi_{U_2}(R)$$

**Teorema de Heath**:
La descomposición es de reunión sin pérdida si y solo si al menos una de las siguientes dependencias funcionales pertenece a la clausura $F^+$:
$$(U_1 \cap U_2) \to U_1 \quad \lor \quad (U_1 \cap U_2) \to U_2$$

**Verificación en MetroNY**:
En todas las descomposiciones aplicadas:
$$(U_{\text{TREN}} \cap U_{\text{MODELO\_TREN}}) = \{ \text{MODELO\_ID} \}$$
Dado que $\text{MODELO\_ID}$ es la Clave Primaria de $\text{MODELO\_TREN}$, se cumple que:
$$\{ \text{MODELO\_ID} \} \to U_{\text{MODELO\_TREN}}$$
Por el Teorema de Heath, la descomposición es **estrictamente de reunión sin pérdida de información**. No pueden generarse tuplas espurias al realizar operaciones `JOIN`.

### 5.2 Propiedad de Preservación de Dependencias Funcionales
Una descomposición preserva las dependencias funcionales si la unión de las proyecciones de dependencias en cada relación descompuesta genera la misma clausura que el conjunto original:
$$(\bigcup_{i=1}^n \pi_{R_i}(F))^+ = F^+$$

**Verificación en MetroNY**:
Todas las dependencias de dominio ferroviario (secuencias de ruta, asignación de turnos, consumos de repuestos, vigencias de certificación) pueden verificarse localmente dentro de su tabla respectiva o mediante las restricciones referenciales `FOREIGN KEY` asociadas, sin requerir la ejecución de joins globales entre tablas no relacionadas.

---

## 6. Justificación de la Eliminación Estricta de Atributos Derivados

Una de las directivas más enfáticas de la cátedra de Bases de Datos I establece la **prohibición categórica de almacenar atributos calculados o derivados en las tablas**.

A continuación se detalla la justificación técnica de esta política en MetroNY:

| Atributo Calculado Prohibido | Riesgo de Integridad si se Almacenara en Tabla | Mecanismo Formal Implementado en MetroNY |
| :--- | :--- | :--- |
| **Costo Total de Orden** (`costo_total`) | Si el precio de un repuesto o las horas de un técnico se corrigen, el total almacenado quedaría desincronizado (inconsistencia grave). | **Función PL/SQL** `FN_COSTO_ORDEN_MANTENIMIENTO(p_id_orden)` y vista `VW_COSTO_MANTENIMIENTO` calculan en vivo: $\sum (cant \times costo) + \sum (horas \times tarifa)$. |
| **Retraso en Minutos** (`minutos_retraso`) | La hora real de llegada o salida puede registrar demoras progresivas en cada estación. | **Función PL/SQL** `FN_MINUTOS_RETRASO(p_id_viaje)` calcula dinámicamente `ROUND((hora_real - hora_programada) * 1440)`. |
| **Ingresos Diarios por Estación** | Almacenar un acumulador estático exigiría locks pesados en cada paso por torniquete ($2.90). | **Función PL/SQL** `FN_INGRESOS_ESTACION(p_id_estacion, p_fecha)` y vista `VW_INGRESOS_DIARIOS_LINEA` computan mediante `SUM(monto_cobrado)`. |
| **Total Pasajeros por Línea** | La afluencia es continua (millones de pasajeros diarios). Un campo estático se volvería obsoleto al instante. | **Función PL/SQL** `FN_PASAJEROS_LINEA(p_id_linea, f1, f2)` calcula en tiempo real `COUNT(v.id_viaje_pasajero)`. |
| **Disponibilidad de Tren / Ruta** | El estado operativo depende de la existencia de órdenes abiertas o incidentes activos no resueltos. | **Funciones PL/SQL** `FN_TREN_DISPONIBLE(p_id_tren)` y `FN_RUTA_OPERATIVA(p_id_ruta)` evalúan las tablas asociadas al momento de la consulta. |

---

## 7. Dictamen Final de Normalización

Habiendo analizado de manera exhaustiva el esquema relacional implementado en Oracle 23ai para el **Sistema de Gestión del Metro de Nueva York (MTA NYCT)**:

1. Se comprobó la **atomicidad absoluta** de los dominios y la eliminación de grupos repetitivos (1NF).
2. Se verificó la **dependencia funcional completa** de todos los atributos no primos respecto a las claves candidatas (2NF).
3. Se certificó la **inexistencia de dependencias transitivas** mediante la modularización en 33 entidades especializadas (3NF).
4. Se validó la **preservación de dependencias** y la **reunión sin pérdida** (Lossless Join).
5. Se erradicó el almacenamiento de **atributos derivados**, delegando los cálculos analíticos a la capa de abstracción PL/SQL (vistas y funciones).

Por tanto, se dictamina formalmente que el esquema `METRO_NY` se encuentra en **TERCERA FORMA NORMAL (3NF)** estricta, cumpliendo con la totalidad de los estándares académicos y profesionales exigidos para la entrega del proyecto.
