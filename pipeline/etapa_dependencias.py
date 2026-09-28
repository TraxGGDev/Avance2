"""Etapa: dependencias vulnerables (SCA).

Riesgo que cubre: la app recibe archivos subidos por usuarios no confiables
(el endpoint /videos) y los pasa a librerias de terceros (boto3, psycopg2,
fastapi) y a ffmpeg/ffprobe en el worker. Una vulnerabilidad conocida en esas
librerias es explotable directamente por ese camino de entrada.

Umbral: bloquea si pip-audit encuentra 1 o mas vulnerabilidades conocidas
(CVE/GHSA) en cualquiera de los dos requirements.txt de la aplicacion. No se
usa un umbral de severidad porque pip-audit no siempre reporta severidad
para cada advisory; con tan pocas dependencias directas, cero
vulnerabilidades conocidas es un umbral razonable de alcanzar.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVOS_REQUIREMENTS = [
    RAIZ / "app" / "api" / "requirements.txt",
    RAIZ / "app" / "worker" / "requirements.txt",
]


def main():
    total_vulnerabilidades = 0
    fallo_la_herramienta = False
    print("Etapa: dependencias vulnerables (pip-audit)")
    print("Umbral que bloquea: 1 o mas vulnerabilidades conocidas")
    print("Si pip-audit no logra correr sobre algun archivo, esta etapa bloquea: "
          "una herramienta que no corrio no es evidencia de 'cero vulnerabilidades'.")

    for archivo in ARCHIVOS_REQUIREMENTS:
        proceso = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", str(archivo), "-f", "json"],
            capture_output=True, text=True,
        )
        try:
            datos = json.loads(proceso.stdout)
        except json.JSONDecodeError:
            fallo_la_herramienta = True
            print(f"  [FALLO DE HERRAMIENTA] No se pudo auditar {archivo.relative_to(RAIZ)} "
                  f"(codigo de salida {proceso.returncode}):", file=sys.stderr)
            print(proceso.stderr, file=sys.stderr)
            continue

        dependencias = datos.get("dependencies", datos) if isinstance(datos, dict) else datos
        if isinstance(dependencias, dict):
            dependencias = dependencias.get("dependencies", [])

        for dep in dependencias:
            vulns = dep.get("vulns", [])
            if vulns:
                total_vulnerabilidades += len(vulns)
                for v in vulns:
                    print(
                        f"  [HALLAZGO] {archivo.relative_to(RAIZ)}: "
                        f"{dep['name']} {dep['version']} -> {v['id']}"
                    )

    print(f"Vulnerabilidades encontradas: {total_vulnerabilidades}")
    if fallo_la_herramienta:
        print("Veredicto de la etapa: BLOQUEA (pip-audit fallo al ejecutarse "
              "sobre al menos un archivo, ver detalle arriba)", file=sys.stderr)
        sys.exit(1)
    sys.exit(1 if total_vulnerabilidades > 0 else 0)


if __name__ == "__main__":
    main()
