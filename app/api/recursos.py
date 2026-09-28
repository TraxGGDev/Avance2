import os

import boto3
import jwt
from fastapi import Header, HTTPException

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET = os.environ["S3_BUCKET"]
JWT_SECRET = os.environ["JWT_SECRET"]

s3 = boto3.client("s3", region_name=AWS_REGION)


def usuario_actual(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de autorizacion")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    return payload
