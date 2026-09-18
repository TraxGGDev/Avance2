import os
import psycopg2

DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        connect_timeout=5,
    )


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            creado_en TIMESTAMPTZ DEFAULT now()
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            nombre_original TEXT NOT NULL,
            s3_key_original TEXT NOT NULL,
            s3_key_miniatura TEXT,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            duracion_segundos REAL,
            mensaje_error TEXT,
            creado_en TIMESTAMPTZ DEFAULT now(),
            procesado_en TIMESTAMPTZ
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()
