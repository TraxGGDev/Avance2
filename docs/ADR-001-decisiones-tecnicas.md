# ADR-001: Decisiones tecnicas de Clips Cortos

Fecha: 2026-09-17
Estado: aceptada

## Contexto

Construi una plataforma minima de subida y visualizacion de clips cortos para
el Avance 2 del Reto, individual, con un tiempo de entrega muy ajustado y
usando una cuenta de AWS Academy Learner Lab (sesion de credenciales
temporal, sin permisos de IAM, memoria limitada en la instancia). Prioricé
un MVP que cumpliera los requisitos minimos y la pieza distintiva del tema
(worker asincrono) por encima de funcionalidades extra.

## Decisiones

### 1. Framework del backend

**Elegi:** FastAPI.
**Por que:** genera documentacion interactiva automatica (util para probar
la API sin construir un frontend elaborado), tiene validacion de tipos
integrada y su modelo async encaja bien con un servicio que hace I/O contra
S3 y RDS.
**Que descarte y por que:** Flask. Es igual de valido para el requisito,
pero hubiera tenido que agregar extensiones aparte para documentacion y
validacion, y con el tiempo disponible prefer lo que traia mas de fabrica.

### 2. Separacion en servicios

**Elegi:** dos contenedores propios: `api` (atiende HTTP) y `worker`
(procesa video en segundo plano), coordinados por `docker-compose.yml`. No
uso una cola de mensajes dedicada (Redis/SQS); el propio estado `pendiente`
en la tabla `videos` de RDS funciona como cola, y el worker la consulta con
`SELECT ... FOR UPDATE SKIP LOCKED` para tomar un job sin duplicarlo.
**Por que:** el tema pide explicitamente que el procesamiento del clip
viva en un contenedor separado del API, no como una funcion dentro del
mismo proceso. Usar la base de datos como cola evita sumar una pieza de
infraestructura mas (Redis o SQS) cuando ya tengo RDS obligatorio por los
requisitos minimos, y el volumen esperado para esta entrega es bajo.
**Que descarte y por que:** una cola de mensajes real (SQS o RabbitMQ). Es
la pieza distintiva de otro de los cinco temas (Gestor de tareas
colaborativo), y para el volumen de esta entrega hubiera sido complejidad
sin beneficio medible; lo dejo anotado como mejora futura si el volumen de
videos creciera.

### 3. Almacenamiento

**Elegi:** el archivo binario del video y la miniatura viven unicamente en
S3 (prefijos `originales/` y `miniaturas/`); RDS solo guarda metadatos
(usuario, nombre original, estado, duracion, referencia a la clave de S3).
**Por que:** separar contenido binario de metadatos es el patron estandar
para este tipo de aplicacion: RDS no esta pensado para guardar archivos
grandes, y S3 sí. Ademas asi el worker puede escalar horizontalmente sin
pelearse por locks de archivos.
**Que descarte y por que:** guardar el video como BLOB en la base de datos.
Descartado porque infla el tamano de la instancia RDS innecesariamente y
complica el respaldo, sin ninguna ventaja para este caso de uso.

## Consecuencias

Lo que se facilito: al no meter una cola de mensajes aparte, el
`docker-compose.yml` quedo con solo dos servicios y menos variables de
entorno que coordinar, lo cual ayudo mucho dado el tiempo disponible. Lo que
se complico: usar la base de datos como cola obliga a tener cuidado con
transacciones (el `FOR UPDATE SKIP LOCKED`) para no procesar el mismo video
dos veces si en el futuro corriera mas de una replica del worker; es una
solucion correcta para el volumen actual pero no escalaria igual de bien que
una cola dedicada si el numero de usuarios creciera mucho.
