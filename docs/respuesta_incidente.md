# Respuesta al incidente -- Entrega Final

Alumno: Oscar Perez Hernandez -- Matricula: AL07020145 -- Tema: 1, Clips cortos

Hallazgo completo y su clasificacion en `docs/clasificacion_hallazgo.md`
(CWE-78, inyeccion de comandos de sistema operativo, severidad Critica).

## Contencion inmediata

Lo que se hace de inmediato para frenar el riesgo mientras se prepara el
arreglo real -- no corrige la causa, solo detiene el sangrado:

1. Deshabilitar el endpoint nuevo con una bandera de configuracion
   (`EXPORTAR_CLIP_HABILITADO=false` en el `.env` de la instancia de QA),
   devolviendo `503` desde `exportar_video_baja_resolucion` mientras la
   bandera este apagada, en vez de exponer el codigo vulnerable mientras se
   prepara el fix.
2. Si el endpoint ya se hubiera desplegado en Produccion (no fue el caso
   aqui: a Produccion solo se promueve codigo que ya paso el pipeline en
   verde), la contencion equivalente en el borde de red seria bloquear la
   ruta `POST /videos/*/exportar` en el balanceador o en el security group,
   sin tocar el codigo de la instancia.
3. Revisar los logs de la instancia de QA para confirmar que, mientras el
   endpoint estuvo activo (unicamente en el ambiente de pruebas, nunca en
   Produccion), no se recibio ningun `resolucion` con caracteres de shell
   (`;`, `|`, `&`, backticks) fuera de la prueba manual controlada descrita
   en `docs/clasificacion_hallazgo.md`.

## Prevencion (el arreglo real)

El cambio en el codigo que elimina la causa raiz, para que esta clase de
falla no vuelva a ocurrir -- es lo que efectivamente se sube a Produccion.
Ver el commit de remediacion en `app/api/exportar_clip.py`:

1. **Eliminar `shell=True` por completo.** Se reemplaza
   `subprocess.call(comando, shell=True)` (una cadena que interpreta
   `/bin/sh`) por `subprocess.run([...], shell=False)` con el comando
   pasado como lista de argumentos. Sin un shell de por medio, no existe
   ningun caracter especial (`;`, `|`, `&&`, backticks) que un atacante
   pueda usar para encadenar un segundo comando: cada elemento de la lista
   se pasa al proceso `ffmpeg` tal cual, como un argumento literal, nunca
   como texto que un interprete vuelve a parsear.
2. **Validar `resolucion` contra una lista blanca fija.** Incluso sin
   shell, una resolucion arbitraria seria una superficie de abuso de
   recursos (por ejemplo pedir un escalado absurdamente grande). Se
   restringe a un conjunto cerrado de resoluciones soportadas
   (`480x270`, `640x360`, `320x180`) y se rechaza con `400` cualquier valor
   fuera de esa lista, en vez de tratar de "sanitizar" el string.
3. La funcionalidad pedida por producto (exportar el clip ya subido en una
   resolucion mas baja) se mantiene identica desde el punto de vista del
   cliente de la API -- mismo endpoint, mismo contrato de entrada/salida --
   solo cambia como se construye y ejecuta el comando de ffmpeg.

Esta remediacion es la que se promueve a la instancia de Produccion, una
vez que el pipeline vuelve a dar veredicto PERMITIDO sobre el codigo
corregido (ver `reportes/pipeline_verde.*` y
`docs/evidencia_produccion.md`).
