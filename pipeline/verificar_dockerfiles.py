"""Verifica que cada Dockerfile propio este endurecido:
version de imagen base fija, no correr como root, y tener HEALTHCHECK.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def evaluar(ruta: Path):
    texto = ruta.read_text(encoding="utf-8")
    lineas = [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]

    match_from = re.search(r"^FROM\s+(\S+)", texto, re.MULTILINE)
    imagen = match_from.group(1) if match_from else ""
    tiene_tag_fijo = ":" in imagen and not imagen.endswith(":latest")

    tiene_user_no_root = any(
        re.match(r"^USER\s+(?!root\b)(?!0\b)\S+", l) for l in lineas
    )

    tiene_healthcheck = any(l.startswith("HEALTHCHECK") for l in lineas)

    return {
        "archivo": str(ruta.relative_to(RAIZ)),
        "imagen_base": imagen,
        "imagen_base_version_fija": tiene_tag_fijo,
        "usuario_no_root": tiene_user_no_root,
        "tiene_healthcheck": tiene_healthcheck,
    }


def main():
    dockerfiles = sorted(RAIZ.glob("app/*/Dockerfile"))
    if not dockerfiles:
        print(json.dumps({"etapa": "dockerfiles_endurecidos", "error": "no se encontraron Dockerfiles"}))
        sys.exit(1)

    resultados = [evaluar(d) for d in dockerfiles]
    fallidos = [
        r for r in resultados
        if not (r["imagen_base_version_fija"] and r["usuario_no_root"] and r["tiene_healthcheck"])
    ]

    salida = {"etapa": "dockerfiles_endurecidos", "resultados": resultados, "fallidos": len(fallidos)}
    print(json.dumps(salida, indent=2, ensure_ascii=False))

    for r in resultados:
        estado = "OK" if r not in fallidos else "FALLO"
        print(f"  [{estado}] {r['archivo']}: imagen={r['imagen_base']} "
              f"version_fija={r['imagen_base_version_fija']} "
              f"no_root={r['usuario_no_root']} healthcheck={r['tiene_healthcheck']}", file=sys.stderr)

    sys.exit(1 if fallidos else 0)


if __name__ == "__main__":
    main()
