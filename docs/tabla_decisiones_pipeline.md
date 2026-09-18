# Tabla de decisiones de mi pipeline

Este documento es el corazon de la entrega: no se califica cuantos controles
pusiste, sino que puedas justificar cada uno.

## Riesgos que introduce MI aplicacion

| # | Riesgo concreto de mi app | Que control lo cubre | Por que ese control |
|---|---|---|---|
| 1 | Una credencial real (password de RDS, JWT_SECRET, llaves de AWS) queda escrita en el codigo fuente y se sube al repositorio | Etapa de secretos (`detect-secrets`, `pipeline/etapa_secretos.py`) | Es el unico control que revisa directamente el contenido del codigo en busca de credenciales, que es exactamente el requisito minimo "cero credenciales en el codigo" |
| 2 | El endpoint `/videos` acepta archivos subidos por cualquier usuario autenticado y los pasa a `boto3`, `psycopg2` y, en el worker, a `ffmpeg`/`ffprobe`; una vulnerabilidad conocida en esas librerias es explotable directamente por ese camino | Analisis de dependencias (`pip-audit`, `pipeline/etapa_dependencias.py`) | Mis dependencias directas son pocas (7 en total entre api y worker), asi que revisarlas una por una contra la base de datos de vulnerabilidades conocidas es barato y de alto impacto |
| 3 | Un error propio en como manejo el archivo subido o las contrasenas (por ejemplo, una inyeccion al construir un comando de `ffmpeg`, o comparar contrasenas sin `bcrypt`) | Analisis estatico (`bandit`, `pipeline/etapa_estatico.py`) | Bandit conoce los patrones inseguros mas comunes en Python (uso de `subprocess` con `shell=True`, comparaciones de contrasenas inseguras, etc.), que son justo los que mi propio codigo podria introducir |
| 4 | El bucket de S3 o la base de datos RDS quedan mal configurados (acceso publico o sin cifrado), exponiendo videos y datos de usuarios que se supone son privados | Verificador de IaC (`pipeline/verificar_iac.py`) sobre `infra/*.tf` | Es la unica etapa que revisa la configuracion de la infraestructura antes de aplicarla, en vez de descubrir el problema hasta que el recurso ya esta creado en AWS |
| 5 | Un contenedor corriendo como root, o con una imagen base sin version fija, aumenta el dano posible si el proceso de la app es comprometido a traves del endpoint de subida de archivos | Verificador de Dockerfiles (`pipeline/verificar_dockerfiles.py`) | El requisito minimo pide explicitamente Dockerfile endurecido (version fija, sin root, con HEALTHCHECK); este control automatiza esa revision en vez de confiar en que no se me olvide |

## Mis etapas y sus umbrales

| Etapa | Herramienta | Que revisa | Umbral que bloquea | Por que ese umbral |
|---|---|---|---|---|
| Secretos en el codigo | detect-secrets | app/, infra/, pipeline/, docker-compose.yml en busca de credenciales, tokens y contrasenas literales | 1 o mas secretos detectados | Un secreto real filtrado, aunque sea uno solo, es suficiente para comprometer la cuenta de AWS Academy; no hay un numero "aceptable" de credenciales expuestas |
| Dependencias vulnerables | pip-audit | Los dos `requirements.txt` (api y worker) contra la base de datos de vulnerabilidades conocidas (OSV/PyPI Advisory) | 1 o mas vulnerabilidades conocidas | Con tan pocas dependencias directas, llegar a cero vulnerabilidades conocidas es alcanzable; no se justifica tolerar ninguna cuando el numero de librerias es tan chico |
| Analisis estatico (SAST) | bandit | Codigo propio en `app/` | 1 o mas hallazgos de severidad HIGH con confianza MEDIUM o superior | Bloquear en LOW o MEDIUM genera demasiado ruido en una app de este tamano (bandit marca hasta el uso normal de `subprocess`); HIGH+confianza media es el punto donde el hallazgo casi siempre es real |
| Infraestructura como codigo | Verificador propio (`verificar_iac.py`) | `infra/*.tf`: bucket S3 privado y cifrado, RDS sin acceso publico y cifrada, sin contrasenas literales | 1 o mas de las 6 reglas CRITICAL fallidas | Las 6 reglas verifican exactamente los requisitos minimos obligatorios del reto para S3 y RDS; ninguna de ellas es negociable |
| Dockerfiles endurecidos | Verificador propio (`verificar_dockerfiles.py`) | Cada `app/*/Dockerfile`: imagen base con version fija, `USER` distinto de root, `HEALTHCHECK` presente | 1 o mas Dockerfiles incumpliendo cualquiera de las 3 condiciones | Son exactamente las 3 condiciones que el requisito minimo pide para "Dockerfile endurecido"; no tiene sentido un umbral parcial |

Nota sobre la eleccion de herramientas: para infraestructura evalue usar
`checkov`, pero su dependencia nativa `lxml` no compila en este equipo con
Python 3.14 (falta Microsoft C++ Build Tools, y no hay wheel precompilado
para esta version de Python todavia). En vez de bajar la version de Python
solo para esa etapa, escribi un verificador propio que revisa exactamente
las 6 reglas de seguridad que le importan a esta app, en vez de las
cientos de reglas genericas que trae una herramienta como checkov.

## Lo que decidi NO cubrir

| Riesgo que dejo fuera | Por que lo dejo fuera | Que haria si tuviera mas tiempo |
|---|---|---|
| Pruebas dinamicas (DAST) contra la API corriendo | Requiere levantar la app completa (con RDS y S3 reales) dentro del propio pipeline, lo cual añade tiempo y complejidad de infraestructura que no alcance a resolver bien en el tiempo de esta entrega | Agregaria una etapa con OWASP ZAP en modo baseline contra el contenedor `api` levantado en el pipeline, antes de tocar RDS/S3 reales |
| Analisis de la imagen de contenedor ya construida (container image scanning, ej. Trivy) | Mi verificador de Dockerfiles ya cubre los 3 puntos del requisito minimo (version fija, no root, healthcheck); un scanner de imagenes agregaria valor real (vulnerabilidades del sistema operativo base) pero no alcance a integrarlo de forma confiable en el tiempo disponible | Agregaria Trivy sobre la imagen ya construida de `api` y `worker`, bloqueando en severidad HIGH o CRITICAL |
| Limite de tasa (rate limiting) o proteccion contra fuerza bruta en `/auth/login` | Es un riesgo real, pero mi pipeline actual revisa codigo e infraestructura, no comportamiento en tiempo real de la API; cubrir esto necesitaria una etapa de pruebas de carga/DAST que no forma parte de este pipeline | Agregaria un middleware de rate limiting en la propia app y, en el pipeline, una prueba que confirme que el limite existe |
