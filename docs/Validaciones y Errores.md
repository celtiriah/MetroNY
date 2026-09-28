## Módulo 1

* No se pueden agregar transferencias peatonales, mensaje de error “La línea de origen y destino deben ser distintas” aunque ambas sean distintas.  
* Nueva linea: color oficial en código. El campo Operador\_Responsable debería ser una persona ¿Por qué está como MTA New York City Transit?  
* Asociar estación a línea no funciona, no realiza nada al rellenar los campos y clicar en «Guardar Tramo»  
* La base de datos permitió la inserción exitosa de una tarifa con un monto negativo (-15.50). La tabla TARIFA carece de restricciones matemáticas, lo que representa una vulnerabilidad grave para la lógica financiera del sistema. Se requiere aplicar un parche estructural inmediato al esquema ejecutando ALTER TABLE METRO\_NY.TARIFA ADD CONSTRAINT CHK\_TARIFA\_MONTO CHECK (monto \>= 0\) para proteger la integridad de la recaudación. 

## Mejoras en General

* Aumentar el tiempo de las notificaciones emergentes.(Agregar bandeja de notificaciones)  
* Mejorar frontend: agregar paleta de colores en general, estados, botones, etc.