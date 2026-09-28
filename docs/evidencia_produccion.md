# Evidencia de promocion a Produccion

Alumno: Oscar Perez Hernandez -- Matricula: AL07020145 -- Tema: 1, Clips cortos

[COMPLETAR: llena esta plantilla despues de desplegar en la instancia de
Produccion. Es la prueba de que el ciclo completo (QA bloquea -> se
clasifica -> se remedia -> QA en verde -> se promueve) funciono de
principio a fin, no solo en la maquina de QA.]

## Instancia de Produccion

- IP publica / DNS: [COMPLETAR]
- Fecha y hora de creacion: [COMPLETAR]
- Commit desplegado (hash corto): `58f5c17` (Remedia inyeccion de comandos
  en /videos/{id}/exportar -- CWE-78) o el que resulte tras el push final
- Confirmacion de que es una instancia NUEVA, distinta de la de QA del
  Avance 2: [COMPLETAR -- por ejemplo, ID de instancia EC2 diferente]

## Pasos seguidos para desplegar

1. Se creo la instancia EC2 de Produccion (security group `app` y subred
   por defecto de `terraform output`, mismo bucket S3 y misma RDS que QA
   -- Produccion y QA comparten datos/infraestructura, solo cambia donde
   corre el contenedor de la app).
2. Se clono el repositorio en la instancia de Produccion, en el commit
   `58f5c17` (o posterior), que ya incluye la remediacion.
3. Se copio el `.env` con las credenciales reales (nunca se sube al
   repositorio).
4. Se corrio `docker compose up --build -d`.
5. Se verifico en el navegador, desde `http://<ip-produccion>:8000`, que
   la aplicacion respondiera en `/salud` y que el flujo completo
   (registro, login, subida de un video, exportar en baja resolucion)
   funcionara con el codigo ya remediado.

## Nota sobre el credito del Learner Lab

La instancia de Produccion se termino inmediatamente despues de tomar la
captura de evidencia, para no consumir el doble de presupuesto de AWS
Academy con dos instancias EC2 corriendo en paralelo.

[COMPLETAR: agrega aqui la hora exacta en que terminaste la instancia.]
