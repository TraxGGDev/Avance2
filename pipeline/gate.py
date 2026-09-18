"""Punto unico de decision del pipeline de Clips Cortos.

Corre cada etapa como un subproceso independiente, respeta el exit code de
cada una como su veredicto individual, genera el SBOM, y al final imprime
UN solo veredicto consolidado: BLOQUEADO o PERMITIDO. Ver el detalle de cada
etapa, su umbral y por que se eligio, en docs/tabla_decisiones_pipeline.md.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

ETAPAS_QUE_BLOQUEAN = [
    ("Secretos en el codigo", "etapa_secretos.py"),
    ("Dependencias vulnerables", "etapa_dependencias.py"),
    ("Analisis estatico (SAST)", "etapa_estatico.py"),
    ("Infraestructura como codigo", "verificar_iac.py"),
    ("Dockerfiles endurecidos", "verificar_dockerfiles.py"),
]


def correr_etapa(nombre, script):
    ruta = RAIZ / "pipeline" / script
    print("\n" + "=" * 70)
    print(f" ETAPA: {nombre}")
    print("=" * 70)
    proceso = subprocess.run([sys.executable, str(ruta)], cwd=RAIZ)
    paso = proceso.returncode == 0
    print(f"--> Resultado de '{nombre}': {'PERMITE' if paso else 'BLOQUEA'}")
    return paso


def generar_sbom():
    print("\n" + "=" * 70)
    print(" SBOM (CycloneDX) -- no bloquea, es un artefacto obligatorio")
    print("=" * 70)
    reportes = RAIZ / "reportes"
    reportes.mkdir(exist_ok=True)
    requirements = ""
    for req in [RAIZ / "app" / "api" / "requirements.txt", RAIZ / "app" / "worker" / "requirements.txt"]:
        requirements += req.read_text(encoding="utf-8") + "\n"
    salida = reportes / "sbom_cyclonedx.json"
    proceso = subprocess.run(
        [sys.executable, "-m", "cyclonedx_py", "requirements", "-", "-o", str(salida)],
        input=requirements, text=True, capture_output=True,
    )
    if proceso.returncode == 0:
        print(f"SBOM generado en {salida.relative_to(RAIZ)}")
    else:
        print("No se pudo generar el SBOM:", file=sys.stderr)
        print(proceso.stderr, file=sys.stderr)


def main():
    resultados = []
    for nombre, script in ETAPAS_QUE_BLOQUEAN:
        resultados.append((nombre, correr_etapa(nombre, script)))

    generar_sbom()

    print("\n" + "=" * 70)
    print(" RESUMEN DE ETAPAS")
    print("=" * 70)
    for nombre, paso in resultados:
        print(f"  {'[PERMITE]' if paso else '[BLOQUEA]'} {nombre}")

    bloqueada_por = [nombre for nombre, paso in resultados if not paso]

    print("\n" + "=" * 70)
    if bloqueada_por:
        print(" VEREDICTO FINAL: BLOQUEADO")
        print(" Etapas que bloquearon: " + ", ".join(bloqueada_por))
        print("=" * 70)
        sys.exit(1)
    else:
        print(" VEREDICTO FINAL: PERMITIDO")
        print(" Todas las etapas pasaron sus umbrales.")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
