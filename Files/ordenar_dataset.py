# -*- coding: utf-8 -*-
"""
Orden canónico del banco `Data/Preguntas.csv`.

Este script delega en `reordenar_balance_por_materia.py`, que aplica:
- materias en el orden de `Data/listado_materias.csv`;
- por cada materia: 5 Teoría + 5 Cálculo, con escalón TF…TM…TD y CF…CM…CD (Facil→Media→Difícil; empate por Id);
- reparto de dificultad por bloque de 10 compatible con el global 134/133/133;
- Id 1…400 y permutación de opciones para `Correcta` = ciclo (Id−1) mod 4.

Para ver la lógica sin modificar el CSV: `python reordenar_balance_por_materia.py --explicar`
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPT = Path(__file__).resolve().parent / "reordenar_balance_por_materia.py"


def main() -> None:
    r = subprocess.run([sys.executable, str(SCRIPT)], cwd=BASE)
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    main()
