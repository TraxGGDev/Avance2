# Clasificacion del hallazgo -- Entrega Final

Alumno: Oscar Perez Hernandez -- Matricula: AL07020145 -- Tema: 1, Clips cortos

## Hallazgo

El endpoint `POST /videos/{video_id}/exportar` (agregado por el parche del
reto, `app/api/exportar_clip.py`) arma un comando de shell concatenando
directamente el parametro `resolucion` que llega en el cuerpo de la
peticion, y lo ejecuta con `subprocess.call(comando, shell=True)`:

```python
resolucion = datos.get("resolucion", "480x270")
...
comando = f"ffmpeg -y -i {origen} -vf scale={resolucion} {destino}"
subprocess.call(comando, shell=True)
```

Nada valida que `resolucion` tenga la forma `NUMEROxNUMERO`. Cualquier
cadena que el cliente mande ahi se pega tal cual dentro del comando que
interpreta `/bin/sh`.

## Tipo

Inyeccion de comandos de sistema operativo -- **CWE-78** (Improper
Neutralization of Special Elements used in an OS Command).

Se clasifica asi y no, por ejemplo, como inyeccion SQL porque el dato del
usuario nunca llega a una consulta a la base de datos: llega a
`subprocess.call(..., shell=True)`, que es exactamente el patron que define
CWE-78 (un interprete de comandos del sistema operativo recibe una cadena
armada con datos no confiables sin neutralizar los caracteres especiales
del shell como `;`, `|`, `&&` o backticks).

## Severidad: Critica

Justificacion (impacto x facilidad de explotacion):

- **Impacto**: ejecucion arbitraria de comandos con los privilegios del
  proceso de la API dentro del contenedor `api` -- el mismo proceso que
  tiene las credenciales de RDS y el rol de IAM para S3 en variables de
  entorno. Un atacante podria leer `os.environ`, borrar archivos, hacer
  pivote de red dentro de la VPC, o exfiltrar el `JWT_SECRET` y los
  secretos de conexion a la base de datos.
- **Facilidad de explotacion**: el unico requisito es tener una cuenta
  valida en la aplicacion (el endpoint exige JWT, igual que el resto de la
  API) y un `video_id` propio ya subido -- ambos triviales de conseguir via
  `/auth/registro` y `/videos`. No hace falta ninguna condicion especial de
  red ni de configuracion; basta un solo POST con un valor malicioso en
  `resolucion`.
- No se exige "sin autenticacion adicional" como en el ejemplo generico del
  reto porque en esta implementacion el endpoint si esta detras de login;
  aun asi la severidad se mantiene en Critica porque *cualquier* usuario
  autenticado -- incluyendo uno recien registrado, sin ningun privilegio
  especial -- puede ejecutar comandos arbitrarios en el servidor, lo cual
  equivale en la practica a una perdida total de confidencialidad,
  integridad y disponibilidad del sistema.

## Es falso positivo?

No. Se confirmo manualmente enviando un valor de prueba en `resolucion`,
por ejemplo:

```json
{"resolucion": "480x270; touch /tmp/prueba_inyeccion"}
```

El comando resultante (`ffmpeg -y -i <origen> -vf scale=480x270; touch
/tmp/prueba_inyeccion <destino>`) se ejecuta tal cual bajo `/bin/sh -c`, y
el segundo comando (`touch /tmp/prueba_inyeccion`) corre de forma
independiente al de `ffmpeg`. Bandit tambien lo marca automaticamente en la
etapa de analisis estatico del pipeline:

```
[HALLAZGO] app/api/exportar_clip.py:52 B602 subprocess call with shell=True identified, security issue.
```

No hubo ningun hallazgo de esta corrida que se haya descartado como falso
positivo.
