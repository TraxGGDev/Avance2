# Evidencia de promocion a Produccion

Alumno: Oscar Perez Hernandez -- Matricula: AL07020145 -- Tema: 1, Clips cortos

## Instancia de Produccion

- ID de instancia: `i-0a226c2547e0330cf` (distinta de `i-09c6520cc686811ec`,
  la instancia de QA del Avance 2)
- Nombre (tag): `clipscortos-prod`
- IP publica: `3.89.254.59` -- DNS: `ec2-3-89-254-59.compute-1.amazonaws.com`
- AMI: `ami-0cdb4c9b0d678e416` (Amazon Linux 2023), la misma que usa QA
- Security group: `sg-0e151fffbd6c79e47` (`clipscortos-app-sg`, el mismo
  que QA -- Produccion y QA comparten el bucket S3 y la RDS, solo cambia
  la instancia donde corre el contenedor de la app)
- Fecha y hora de creacion: 2026-09-28, ~03:20 UTC
- Commit desplegado (hash corto): `c0879c5` -- ya incluye el parche del
  Tema 1 remediado (CWE-78), la actualizacion de dependencias vulnerables
  y las correcciones encontradas al probar el flujo end-to-end

## Pasos seguidos para desplegar

1. Se lanzo una instancia EC2 nueva (misma AMI, mismo rol de IAM
   `LabInstanceProfile` y mismo security group que QA, para reusar el
   acceso ya autorizado al bucket S3 y a la RDS).
2. Se instalo Docker y Docker Compose (Amazon Linux 2023 no los trae por
   defecto).
3. Se clono el repositorio en la instancia de Produccion, en el commit
   `c0879c5`, que ya incluye la remediacion completa.
4. Se copio el `.env` real (nunca se sube al repositorio) con las mismas
   credenciales de RDS y S3 que usa QA.
5. Se corrio `docker-compose up --build -d`.
6. Se verifico:
   - `GET /salud` responde `{"status":"ok"}`.
   - Flujo completo probado de extremo a extremo: registro, login,
     subida de un video, y exportar en baja resolucion (`POST
     /videos/{id}/exportar` con `resolucion=640x360`) -- respondio `200`
     y el archivo exportado quedo en el bucket S3 real
     (`exports/27/...mp4`).
   - Un intento de inyeccion en el mismo endpoint (`resolucion="480x270;
     touch /tmp/pwned_desde_api"`) fue rechazado con `400` por la lista
     blanca, confirmando que la remediacion esta activa tambien en
     Produccion.

## Nota sobre el credito del Learner Lab

La instancia de Produccion (`i-0a226c2547e0330cf`) se termino el
2026-09-29 a las 03:31 UTC, inmediatamente despues de tomar las capturas
de evidencia (consola de AWS y la app corriendo en el navegador), para no
seguir consumiendo credito del Learner Lab con dos instancias EC2
corriendo en paralelo. La instancia de QA (`i-09c6520cc686811ec`) sigue
activa, igual que en el Avance 2.
