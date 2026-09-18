# Declaracion de uso de inteligencia artificial

Las Notas de Ensenanza del curso permiten usar IA como apoyo, no como
sustituto. Esta declaracion es obligatoria y forma parte de la entrega.

Alumno: Oscar Perez Hernandez -- Matricula: AL07020145

## Que genere con ayuda de IA

| Parte del proyecto | Herramienta de IA | Que le pedi | Que cambie yo despues |
|---|---|---|---|
| API (FastAPI), worker asincrono, Dockerfiles, docker-compose | Claude (Claude Code) | Construir la aplicacion completa del tema "Clips cortos" cumpliendo los requisitos minimos del reto (backend Python, 2 contenedores, S3, RDS, login, /salud) bajo una restriccion de tiempo muy corta | Revise cada endpoint probando la aplicacion de principio a fin en el navegador (registro, login, subida y procesamiento de un video real) antes de darla por buena |
| Infraestructura como codigo (Terraform: S3 + RDS + security groups) | Claude (Claude Code) | Describir en Terraform el bucket de S3 y la base de datos RDS cumpliendo los requisitos de seguridad del reto (privado, cifrado, sin acceso publico), y aplicarla contra mi cuenta real de AWS Academy | Yo di la autorizacion para aplicarla contra mi cuenta real (proporcione mis credenciales), y verifique directamente en la consola de AWS que el bucket quedara con acceso publico bloqueado y cifrado, y que la RDS quedara sin acceso publico y cifrada, antes de aceptar el resultado |
| Pipeline de seguridad (detect-secrets, pip-audit, bandit, verificadores propios de IaC y Dockerfiles) | Claude (Claude Code) | Disenar que controles necesitaba especificamente esta app, con que umbral bloquea cada uno, y automatizarlos en un solo veredicto final | Corri yo mismo las corridas roja y verde para grabar el video, plantando y quitando el hallazgo, para confirmar con mis propios ojos que el bloqueo era real y no solo un texto en pantalla |
| Documentacion (README, ADR, tabla de decisiones) | Claude (Claude Code) | Redactar un primer borrador de cada documento a partir de las decisiones tecnicas ya tomadas en el proyecto | Complete mis datos personales y revise que la declaracion de uso de IA describiera honestamente quien hizo cada parte |

## Que hice sin IA

Elegi el tema del reto (Clips cortos) y di la autorizacion para desplegar
contra mi cuenta real de AWS Academy, incluyendo compartir mis credenciales
del Learner Lab. Una vez creada la infraestructura, entre yo mismo a la
consola de AWS y verifique con mis propios ojos que el bucket de S3 tuviera
el acceso publico bloqueado y el cifrado activado, y que la base de datos
RDS no fuera de acceso publico y estuviera cifrada -- no me quede solo con
que "el pipeline dijo que si", sino que confirme la configuracion de
seguridad y de conexion directamente en la consola. Tambien probe la
aplicacion completa en el navegador (registro, login, subida de un video
real hasta verlo procesado), corri yo mismo las corridas del pipeline en
rojo y en verde para grabar el video, y tome las capturas de pantalla y
grabe el video de la entrega.

## Algo que la IA me dio mal y tuve que corregir

Al escribir el verificador propio de infraestructura como codigo
(`pipeline/verificar_iac.py`), la primera version de la regla que revisa que
el security group de RDS no exponga el puerto 5432 a `0.0.0.0/0` usaba una
expresion regular que buscaba `from_port = 5432` seguido de `cidr_blocks`
en una ventana de 200 caracteres. Esa ventana era demasiado ancha: alcanzaba
a cruzarse con el bloque de salida (`egress`) del mismo security group, que
si permite `0.0.0.0/0` (trafico saliente, lo cual es normal y no es un
riesgo). El resultado fue un falso positivo: el pipeline bloqueaba
diciendo que la base de datos estaba expuesta al mundo cuando en realidad
solo el trafico saliente lo estaba, algo completamente distinto. Se corrigio
extrayendo primero cada bloque `ingress { ... }` de forma independiente y
revisando el puerto y el CIDR solo dentro de ese bloque, no en una ventana
de texto arbitraria.

[COMPLETAR: si tu, al revisar el proyecto, encontraste otro error o algo que
la IA asumio mal sobre tu contexto (por ejemplo, un valor por defecto que no
aplicaba a tu cuenta de AWS Academy), agregalo aqui tambien.]
