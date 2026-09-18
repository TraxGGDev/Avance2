"""Escaner de infraestructura como codigo, hecho a la medida.

Nota de justificacion (docs/tabla_decisiones_pipeline.md): se evaluo usar
checkov, pero su dependencia nativa lxml no compila en Python 3.14 en este
equipo (falta Microsoft C++ Build Tools). En vez de bajar la version de
Python solo para una etapa, se escribio este verificador propio: revisa
exactamente las reglas de seguridad que importan para ESTA app (bucket
privado y cifrado, RDS sin acceso publico y cifrada, sin contrasenas
literales en el .tf) en vez de una lista generica de cientos de reglas.
"""
import json
import re
import sys
from pathlib import Path

DIRECTORIO_INFRA = Path(__file__).resolve().parent.parent / "infra"


def leer_tf():
    contenido = ""
    for archivo in sorted(DIRECTORIO_INFRA.glob("*.tf")):
        contenido += f"\n# --- {archivo.name} ---\n" + archivo.read_text(encoding="utf-8")
    return contenido


def revisar(contenido: str):
    hallazgos = []

    def check(id_, descripcion, severidad, ok):
        hallazgos.append(
            {"id": id_, "descripcion": descripcion, "severidad": severidad, "paso": bool(ok)}
        )

    check(
        "IAC001",
        "El bucket de S3 tiene bloqueado el acceso publico (block_public_acls, "
        "block_public_policy, ignore_public_acls, restrict_public_buckets = true)",
        "CRITICAL",
        all(
            re.search(rf"{campo}\s*=\s*true", contenido)
            for campo in [
                "block_public_acls",
                "block_public_policy",
                "ignore_public_acls",
                "restrict_public_buckets",
            ]
        ),
    )

    check(
        "IAC002",
        "El bucket de S3 tiene configurado cifrado por defecto (server side encryption)",
        "CRITICAL",
        "apply_server_side_encryption_by_default" in contenido,
    )

    check(
        "IAC003",
        "La instancia RDS tiene storage_encrypted = true",
        "CRITICAL",
        bool(re.search(r"storage_encrypted\s*=\s*true", contenido)),
    )

    check(
        "IAC004",
        "La instancia RDS tiene publicly_accessible = false",
        "CRITICAL",
        bool(re.search(r"publicly_accessible\s*=\s*false", contenido)),
    )

    bloques_ingress = re.findall(r"ingress\s*\{([^}]*)\}", contenido)
    ingress_5432_abierto = any(
        "5432" in bloque and "0.0.0.0/0" in bloque for bloque in bloques_ingress
    )
    check(
        "IAC005",
        "Ningun bloque de entrada (ingress) del security group de RDS permite "
        "0.0.0.0/0 en el puerto de la base de datos",
        "CRITICAL",
        not ingress_5432_abierto,
    )

    check(
        "IAC006",
        "La contrasena de la base de datos no esta escrita como texto literal en el .tf "
        "(debe venir de var.db_password)",
        "CRITICAL",
        "password = var.db_password" in contenido or "password  = var.db_password" in contenido,
    )

    return hallazgos


def main():
    contenido = leer_tf()
    hallazgos = revisar(contenido)
    fallidos_criticos = [h for h in hallazgos if not h["paso"] and h["severidad"] == "CRITICAL"]

    resultado = {
        "etapa": "infraestructura_como_codigo",
        "total_checks": len(hallazgos),
        "checks": hallazgos,
        "fallidos_criticos": len(fallidos_criticos),
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    for h in hallazgos:
        marca = "OK" if h["paso"] else "FALLO"
        print(f"  [{marca}] {h['id']} ({h['severidad']}): {h['descripcion']}", file=sys.stderr)

    sys.exit(1 if fallidos_criticos else 0)


if __name__ == "__main__":
    main()
