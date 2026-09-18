"""Etapa: secretos en el codigo.

Riesgo que cubre: que una credencial real (password de RDS, llave de AWS,
JWT_SECRET) quede escrita en el codigo fuente en vez de venir de variables
de entorno, y termine publicada en el repositorio de Git.

Umbral: bloquea si detect-secrets encuentra 1 o mas hallazgos en el codigo
propio (app/, infra/, pipeline/, docker-compose.yml). No se acepta ningun
hallazgo: un secreto real filtrado, aunque sea uno solo, es suficiente para
comprometer la cuenta de AWS Academy.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTAS_A_ESCANEAR = ["app", "infra", "pipeline", "docker-compose.yml"]


def main():
    proceso = subprocess.run(
        [sys.executable, "-m", "detect_secrets", "scan", "--all-files", *RUTAS_A_ESCANEAR],
        cwd=RAIZ, capture_output=True, text=True,
    )
    try:
        datos = json.loads(proceso.stdout)
    except json.JSONDecodeError:
        print("No se pudo interpretar la salida de detect-secrets:", file=sys.stderr)
        print(proceso.stdout, file=sys.stderr)
        print(proceso.stderr, file=sys.stderr)
        sys.exit(1)

    resultados = datos.get("results", {})
    total = sum(len(v) for v in resultados.values())

    print("Etapa: secretos en el codigo (detect-secrets)")
    print("Umbral que bloquea: 1 o mas secretos detectados")
    print(f"Secretos encontrados: {total}")
    for archivo, hallazgos in resultados.items():
        for h in hallazgos:
            print(f"  [HALLAZGO] {archivo}:{h['line_number']} tipo={h['type']}")

    sys.exit(1 if total > 0 else 0)


if __name__ == "__main__":
    main()
