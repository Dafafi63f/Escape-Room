#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lote manual de recategorizaciones (id + materia destino).

Edita la sección CONFIG y ejecuta:
  python Files/recategorizar_lote_manual.py

Por defecto aplica cambios (INPLACE=True).
Si quieres simular sin guardar, pon DRY_RUN=True.
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recategorizar_y_equilibrar import recategorizar_y_equilibrar_por_id


# =========================
# CONFIG (edítame)
# =========================

# True: guarda, reordena y valida en cada operación.
INPLACE = True

# True: simula (no escribe cambios), útil para revisar antes.
DRY_RUN = False

# Lista de operaciones en orden.
# Formato: (id_pregunta, "Materia destino exacta")
OPERACIONES: list[tuple[int, str]] = [
    #(25, "Càlcul Numèric"),
]


PATH_CSV = BASE / "Data" / "Preguntas.csv"


def _clave_fila(r: dict) -> tuple[str, str, str, str, str]:
    return (
        str(r.get("Pregunta", "")).strip(),
        str(r.get("A", "")).strip(),
        str(r.get("B", "")).strip(),
        str(r.get("C", "")).strip(),
        str(r.get("D", "")).strip(),
    )


def _normalizar_texto(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _firma_flexible_fila(r: dict) -> tuple[str, str]:
    # Firma más estable cuando hay cambios menores de acentos/espacios.
    return (
        _normalizar_texto(str(r.get("Pregunta", ""))),
        _normalizar_texto(" ".join(str(r.get(k, "")) for k in ("A", "B", "C", "D"))),
    )


def _resolver_id_actual_desde_id_base(id_base: int) -> tuple[int | None, str]:
    """
    Convierte un Id "estable" (del CSV en HEAD) al Id actual del CSV en disco.
    Esto evita que la renumeración canónica cambie el objetivo entre ejecuciones.
    """
    try:
        raw = subprocess.check_output(["git", "show", "HEAD:Data/Preguntas.csv"], cwd=BASE)
    except Exception:
        return id_base, "id_directo_sin_head"

    base_rows = list(csv.DictReader(raw.decode("utf-8").splitlines(), delimiter=";"))
    base_row = next((r for r in base_rows if str(r.get("Id", "")).strip() == str(id_base)), None)
    if not base_row:
        return None, "id_base_no_existe_en_head"
    clave_obj = _clave_fila(base_row)
    firma_obj = _firma_flexible_fila(base_row)

    with PATH_CSV.open("r", encoding="utf-8", newline="") as f:
        actuales = list(csv.DictReader(f, delimiter=";"))

    # 1) Match exacto por contenido completo.
    row_actual = next((r for r in actuales if _clave_fila(r) == clave_obj), None)
    # 2) Match flexible por firma normalizada.
    if not row_actual:
        row_actual = next((r for r in actuales if _firma_flexible_fila(r) == firma_obj), None)
        if row_actual:
            try:
                return int(str(row_actual.get("Id", "")).strip()), "firma_flexible"
            except Exception:
                return None, "firma_flexible_id_invalido"

    # 3) Fallback: usar el id directo si existe en el CSV actual.
    if not row_actual:
        row_directa = next((r for r in actuales if str(r.get("Id", "")).strip() == str(id_base)), None)
        if row_directa:
            try:
                return int(str(row_directa.get("Id", "")).strip()), "id_directo_fallback"
            except Exception:
                return None, "id_directo_invalido"
        return None, "no_localizada"
    try:
        return int(str(row_actual.get("Id", "")).strip()), "exacta"
    except Exception:
        return None, "exacta_id_invalido"


def main() -> int:
    if not OPERACIONES:
        print("No hay operaciones definidas en OPERACIONES.")
        return 0

    print(f"Operaciones a ejecutar: {len(OPERACIONES)}")
    print(f"INPLACE={INPLACE} | DRY_RUN={DRY_RUN}")

    errores = 0
    for i, (id_obj, materia_destino) in enumerate(OPERACIONES, start=1):
        id_resuelto, modo = _resolver_id_actual_desde_id_base(id_obj)
        print("\n" + "=" * 60)
        if id_resuelto is None:
            errores += 1
            print(f"[{i}/{len(OPERACIONES)}] Id base={id_obj} -> {materia_destino!r}")
            print(
                "[ERROR] No se pudo localizar la pregunta objetivo en el CSV actual "
                f"(motivo={modo})."
            )
            continue
        print(
            f"[{i}/{len(OPERACIONES)}] Id base={id_obj} (Id actual={id_resuelto}) "
            f"-> {materia_destino!r}"
        )
        if modo != "exacta":
            print(f"[AVISO] Resolución no exacta del objetivo (modo={modo}).")
        rc = recategorizar_y_equilibrar_por_id(
            id_objetivo=id_resuelto,
            materia_destino=materia_destino,
            inplace=INPLACE,
            dry_run=DRY_RUN,
        )
        if rc != 0:
            errores += 1
            print(f"[ERROR] Operación {i} devolvió rc={rc}")
        else:
            print(f"[OK] Operación {i} completada")

    print("\n" + "=" * 60)
    if errores:
        print(f"Terminado con {errores} operación(es) con error.")
        return 1
    print("Terminado sin errores.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
