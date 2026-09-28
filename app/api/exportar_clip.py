"""
Exportar clip en resolucion reducida
Tema: Clips cortos

Producto pide: el usuario puede pedir una version en baja resolucion de su
clip ya subido, para compartirla mas rapido en redes con poco ancho de banda.

Adaptado del Blueprint de Flask entregado (exportar_clip.py) a un router de
FastAPI, integrado con el almacenamiento real de esta app (S3, no disco
local) y protegido con el mismo login (JWT) que ya usa el resto de la API.

Remediacion (ver docs/clasificacion_hallazgo.md y docs/respuesta_incidente.md):
la version original armaba un comando de shell concatenando el parametro
"resolucion" que llega del cliente y lo ejecutaba con
subprocess.call(comando, shell=True) -- inyeccion de comandos de sistema
operativo (CWE-78). Se corrigio en dos partes: (1) ffmpeg se invoca con
subprocess.run() y una lista de argumentos, sin shell de por medio, para
que ningun caracter especial del shell (;, |, &&, backticks) tenga efecto;
(2) "resolucion" se valida contra una lista blanca fija de valores
soportados en vez de aceptar cualquier cadena.
"""
import os
import subprocess
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException

from db import get_conn
from recursos import S3_BUCKET, s3, usuario_actual

router = APIRouter()

RESOLUCIONES_PERMITIDAS = {"480x270", "640x360", "320x180"}


@router.post("/videos/{video_id}/exportar")
def exportar_video_baja_resolucion(video_id: int, datos: dict, usuario=Depends(usuario_actual)):
    """Genera una copia en baja resolucion del clip usando ffmpeg."""
    resolucion = datos.get("resolucion", "480x270")
    if resolucion not in RESOLUCIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Resolucion no soportada. Usa una de: {sorted(RESOLUCIONES_PERMITIDAS)}",
        )

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT s3_key_original FROM videos WHERE id = %s AND usuario_id = %s",
        (video_id, int(usuario["sub"])),
    )
    fila = cur.fetchone()
    cur.close()
    conn.close()

    if not fila:
        raise HTTPException(status_code=404, detail="clip no encontrado")
    clave_original = fila[0]

    with tempfile.TemporaryDirectory() as tmp:
        origen = os.path.join(tmp, "original")
        s3.download_file(S3_BUCKET, clave_original, origen)
        destino = os.path.join(tmp, f"exportado_{resolucion}.mp4")

        subprocess.run(
            ["ffmpeg", "-y", "-i", origen, "-vf", f"scale={resolucion}", destino],
            capture_output=True, timeout=60, check=True, shell=False,
        )

        clave_exportada = f"exports/{video_id}/{uuid.uuid4()}.mp4"
        s3.upload_file(
            destino, S3_BUCKET, clave_exportada,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )

    return {"s3_key_exportado": clave_exportada}
