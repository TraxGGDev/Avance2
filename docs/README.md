# Clips Cortos

> Avance 2 del Reto - LSCA2314 - Periodo AD26
> Alumno: Oscar Perez Hernandez   |   Matricula: AL07020145   |   Tema elegido: 1 - Clips cortos

## Que hace esta aplicacion

Clips Cortos es una plataforma minima donde un usuario se registra, inicia sesion
y sube videos cortos. Cada video subido se procesa de forma asincrona en un
segundo contenedor (el worker), que valida el formato, calcula su duracion y
genera una miniatura, sin bloquear la subida ni la API mientras eso ocurre.

## Como se levanta

```bash
cp .env.ejemplo .env     # y llena tus valores (RDS, S3, JWT_SECRET reales)
docker compose up --build
```

La aplicacion queda en http://localhost:8000 y su endpoint de salud
responde en /salud.

## Arquitectura

Hay dos contenedores propios: `api` (FastAPI) atiende registro, login y
subida/consulta de videos, guardando el archivo original directamente en S3 y
un registro en RDS con estado `pendiente`. El contenedor `worker` sondea la
base de datos por videos pendientes (usando `SELECT ... FOR UPDATE SKIP
LOCKED` para no procesar el mismo video dos veces si hubiera mas de una
replica), descarga el video de S3, corre `ffprobe`/`ffmpeg` para obtener la
duracion y una miniatura, sube la miniatura a S3 y actualiza el estado a
`listo` o `error`. La API y el worker nunca se comunican entre si de forma
directa: la base de datos RDS es la cola de trabajo compartida, y S3 es el
unico lugar donde vive el contenido binario.

Ver el diagrama en `docs/diagrama_arquitectura.svg`.

## Servicios de AWS que usa

| Servicio | Para que lo uso | Como lo asegure |
|---|---|---|
| S3 | Guardar los videos originales (`originales/`) y las miniaturas generadas (`miniaturas/`) | Bucket privado, con Block Public Access activado en sus 4 opciones, y cifrado por defecto SSE-S3 (AES256). El acceso desde el navegador a las miniaturas se hace con URLs prefirmadas de un solo uso temporal, nunca haciendo el bucket publico |
| RDS | Guardar usuarios y metadatos de cada video (estado, duracion, referencias a S3) | Instancia Postgres cifrada en reposo (`storage_encrypted = true`), `publicly_accessible = false`, y un security group que solo permite el puerto 5432 desde el security group de la instancia donde corre la app, no desde internet |

## Requisitos minimos del tema

| Requisito de mi tema | Donde se cumple |
|---|---|
| Worker asincrono en su propio contenedor | `app/worker/worker.py`, servicio `worker` en `docker-compose.yml` |
| Registra duracion del clip | `worker.py` usa `ffprobe` y guarda `duracion_segundos` en la tabla `videos` |
| Genera una miniatura | `worker.py` usa `ffmpeg` para extraer un frame y lo sube a S3 |
| Valida el formato | El worker marca el video como `error` si `ffprobe` no puede leerlo; la API tambien rechaza extensiones no soportadas antes de subir a S3 |

## Como se corre el pipeline

```bash
bash pipeline/ejecutar_pipeline.sh
```

Corre las etapas de seguridad (secretos, dependencias, analisis estatico,
infraestructura como codigo y endurecimiento de Dockerfiles), genera el SBOM
y termina con un unico veredicto: BLOQUEADO o PERMITIDO. Ver el detalle de
cada etapa y su umbral en `docs/tabla_decisiones_pipeline.md`.
