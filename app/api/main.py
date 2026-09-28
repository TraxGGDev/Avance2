import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import psycopg2
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from db import get_conn, init_db
from exportar_clip import router as exportar_router
from recursos import JWT_SECRET, S3_BUCKET, s3, usuario_actual

EXTENSIONES_PERMITIDAS = {".mp4", ".mov", ".webm", ".avi", ".mkv"}
TAMANO_MAXIMO_BYTES = 200 * 1024 * 1024  # 200 MB

app = FastAPI(title="Clips Cortos")
app.include_router(exportar_router)


@app.on_event("startup")
def al_iniciar():
    init_db()


@app.get("/salud")
def salud():
    return {"status": "ok"}


@app.post("/auth/registro")
def registro(datos: dict):
    username = (datos.get("username") or "").strip()
    password = datos.get("password") or ""
    if len(username) < 3 or len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="El usuario necesita al menos 3 caracteres y la contrasena al menos 6",
        )
    hash_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username, hash_pw),
        )
        usuario_id = cur.fetchone()[0]
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="El usuario ya existe")
    finally:
        cur.close()
        conn.close()
    return {"id": usuario_id, "username": username}


@app.post("/auth/login")
def login(datos: dict):
    username = datos.get("username") or ""
    password = datos.get("password") or ""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM usuarios WHERE username = %s", (username,))
    fila = cur.fetchone()
    cur.close()
    conn.close()
    if not fila or not bcrypt.checkpw(password.encode(), fila[1].encode()):
        raise HTTPException(status_code=401, detail="Usuario o contrasena invalidos")
    expiracion = datetime.now(timezone.utc) + timedelta(hours=8)
    token = jwt.encode(
        {"sub": str(fila[0]), "username": username, "exp": expiracion}, JWT_SECRET, algorithm="HS256"
    )
    return {"token": token}


@app.post("/videos")
async def subir_video(archivo: UploadFile = File(...), usuario=Depends(usuario_actual)):
    ext = os.path.splitext(archivo.filename or "")[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {ext or 'desconocido'}")
    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(status_code=400, detail="El archivo excede el limite de 200MB")

    clave = f"originales/{uuid.uuid4()}{ext}"
    s3.put_object(Bucket=S3_BUCKET, Key=clave, Body=contenido, ServerSideEncryption="AES256")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO videos (usuario_id, nombre_original, s3_key_original)
           VALUES (%s, %s, %s) RETURNING id""",
        (int(usuario["sub"]), archivo.filename, clave),
    )
    video_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": video_id, "estado": "pendiente"}


@app.get("/videos")
def listar_videos(usuario=Depends(usuario_actual)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, nombre_original, estado, duracion_segundos, s3_key_miniatura,
                  mensaje_error, creado_en
           FROM videos WHERE usuario_id = %s ORDER BY creado_en DESC""",
        (int(usuario["sub"]),),
    )
    filas = cur.fetchall()
    cur.close()
    conn.close()

    resultado = []
    for f in filas:
        miniatura_url = None
        if f[4]:
            miniatura_url = s3.generate_presigned_url(
                "get_object", Params={"Bucket": S3_BUCKET, "Key": f[4]}, ExpiresIn=3600
            )
        resultado.append(
            {
                "id": f[0],
                "nombre_original": f[1],
                "estado": f[2],
                "duracion_segundos": f[3],
                "miniatura_url": miniatura_url,
                "mensaje_error": f[5],
                "creado_en": f[6].isoformat(),
            }
        )
    return resultado


@app.get("/", response_class=HTMLResponse)
def index():
    ruta = os.path.join(os.path.dirname(__file__), "static", "index.html")
    with open(ruta, encoding="utf-8") as f:
        return f.read()
