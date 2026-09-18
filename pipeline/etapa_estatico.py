"""Etapa: analisis estatico del codigo propio (SAST).

Riesgo que cubre: errores de seguridad en mi propio codigo, en particular el
uso de subprocess para invocar ffmpeg/ffprobe en el worker con datos que
vienen de un archivo subido por el usuario, y el manejo de contrasenas/JWT
en la API.

Umbral: bloquea si bandit encuentra 1 o mas hallazgos de severidad HIGH con
confianza MEDIUM o superior. No se bloquea por LOW/MEDIUM: en una app de
este tamano, exigir cero hallazgos de cualquier severidad genera demasiado
ruido (falsos positivos de bandit en cosas como el uso de subprocess en si
mismo) y esconde las alertas que si importan.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main():
    proceso = subprocess.run(
        [sys.executable, "-m", "bandit", "-r", "app", "-f", "json", "-lll", "-ii"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    try:
        datos = json.loads(proceso.stdout)
    except json.JSONDecodeError:
        print("No se pudo interpretar la salida de bandit:", file=sys.stderr)
        print(proceso.stdout, file=sys.stderr)
        print(proceso.stderr, file=sys.stderr)
        sys.exit(1)

    hallazgos = datos.get("results", [])

    print("Etapa: analisis estatico del codigo (bandit)")
    print("Umbral que bloquea: 1 o mas hallazgos HIGH con confianza MEDIUM o superior")
    print(f"Hallazgos: {len(hallazgos)}")
    for h in hallazgos:
        print(f"  [HALLAZGO] {h['filename']}:{h['line_number']} {h['test_id']} {h['issue_text']}")

    sys.exit(1 if hallazgos else 0)


if __name__ == "__main__":
    main()
