#!/bin/bash
# Corre el pipeline completo de Clips Cortos y termina con un solo veredicto.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR" || exit 1
python pipeline/gate.py
