import json
import os
import subprocess
import tempfile
import time
import uuid

import boto3
import psycopg2

DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_PORT = os.environ.get("DB_PORT", "5432")
S3_BUCKET = os.environ["S3_BUCKET"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
INTERVALO_SEGUNDOS = int(os.environ.get("INTERVALO_POLLING", "5"))
ARCHIVO_LATIDO = "/tmp/heartbeat"

s3 = boto3.client("s3", region_name=AWS_REGION)


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        port=DB_PORT, connect_timeout=5,
    )


def tomar_siguiente_pendiente(conn):
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE videos SET estado = 'procesando'
        WHERE id = (
            SELECT id FROM videos WHERE estado = 'pendiente'
            ORDER BY creado_en ASC LIMIT 1 FOR UPDATE SKIP LOCKED
        )
        RETURNING id, s3_key_original;
        """
    )
    fila = cur.fetchone()
    conn.commit()
    cur.close()
    return fila


def marcar_error(conn, video_id, mensaje):
    cur = conn.cursor()
    cur.execute(
        "UPDATE videos SET estado = 'error', mensaje_error = %s, procesado_en = now() WHERE id = %s",
        (mensaje, video_id),
    )
    conn.commit()
    cur.close()


def procesar(conn, video_id, clave_original):
    with tempfile.TemporaryDirectory() as tmp:
        ruta_local = os.path.join(tmp, "entrada")
        s3.download_file(S3_BUCKET, clave_original, ruta_local)

        try:
            resultado = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", ruta_local],
                capture_output=True, text=True, timeout=60, check=True,
            )
            duracion = float(json.loads(resultado.stdout)["format"]["duration"])
        except Exception as e:
            marcar_error(conn, video_id, f"Formato de video invalido o corrupto: {e}")
            return

        ruta_miniatura = os.path.join(tmp, "miniatura.jpg")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", ruta_local, "-ss", "00:00:01.000", "-vframes", "1", ruta_miniatura],
                capture_output=True, timeout=60, check=True,
            )
        except Exception as e:
            marcar_error(conn, video_id, f"No se pudo generar la miniatura: {e}")
            return

        clave_miniatura = f"miniaturas/{uuid.uuid4()}.jpg"
        s3.upload_file(
            ruta_miniatura, S3_BUCKET, clave_miniatura,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )

    cur = conn.cursor()
    cur.execute(
        """UPDATE videos SET estado = 'listo', duracion_segundos = %s,
           s3_key_miniatura = %s, procesado_en = now() WHERE id = %s""",
        (duracion, clave_miniatura, video_id),
    )
    conn.commit()
    cur.close()


def latido():
    with open(ARCHIVO_LATIDO, "w") as f:
        f.write(str(time.time()))


def main():
    print("Worker de procesamiento de clips iniciado", flush=True)
    while True:
        latido()
        try:
            conn = get_conn()
            fila = tomar_siguiente_pendiente(conn)
            if fila:
                video_id, clave = fila
                print(f"Procesando video {video_id} ({clave})", flush=True)
                try:
                    procesar(conn, video_id, clave)
                    print(f"Video {video_id} procesado correctamente", flush=True)
                except Exception as e:
                    marcar_error(conn, video_id, str(e))
                    print(f"Video {video_id} marcado como error: {e}", flush=True)
            conn.close()
        except Exception as e:
            print(f"Error en el ciclo del worker: {e}", flush=True)
        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()
