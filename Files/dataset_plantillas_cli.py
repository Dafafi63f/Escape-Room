#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI unificada para operaciones de dataset/plantillas.

Fase 1 de consolidación: este archivo enruta a scripts existentes.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FILES = Path(__file__).resolve().parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"


def _run(script_name: str, args: list[str]) -> int:
    cmd = [sys.executable, str(FILES / script_name), *args]
    # Evita fallos cp1252 cuando la ruta del proyecto contiene emoji.
    preview = " ".join([script_name, *args])
    print(f">>> {preview}")
    return subprocess.run(cmd, cwd=BASE).returncode


def _cmd_dataset_balance(args: argparse.Namespace) -> int:
    forward = [args.modo, *args.extra]
    return _run("balance.py", forward)


def _cmd_dataset_recategorizar(args: argparse.Namespace) -> int:
    forward = [f"--id={args.id_objetivo}"]
    if args.materia_destino:
        forward.append(f"--materia-destino={args.materia_destino}")
    if args.inplace:
        forward.append("--inplace")
    if args.dry_run:
        forward.append("--dry-run")
    return _run("recategorizar_y_equilibrar.py", forward)


def _normalizar_texto(s: str) -> str:
    t = unicodedata.normalize("NFKD", s or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _clave_fila(r: dict) -> tuple[str, str, str, str, str]:
    return (
        str(r.get("Pregunta", "")).strip(),
        str(r.get("A", "")).strip(),
        str(r.get("B", "")).strip(),
        str(r.get("C", "")).strip(),
        str(r.get("D", "")).strip(),
    )


def _firma_flexible_fila(r: dict) -> tuple[str, str]:
    return (
        _normalizar_texto(str(r.get("Pregunta", ""))),
        _normalizar_texto(" ".join(str(r.get(k, "")) for k in ("A", "B", "C", "D"))),
    )


def _resolver_id_actual_desde_id_base(id_base: int) -> tuple[int | None, str]:
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

    row_actual = next((r for r in actuales if _clave_fila(r) == clave_obj), None)
    if not row_actual:
        row_actual = next((r for r in actuales if _firma_flexible_fila(r) == firma_obj), None)
        if row_actual:
            try:
                return int(str(row_actual.get("Id", "")).strip()), "firma_flexible"
            except Exception:
                return None, "firma_flexible_id_invalido"
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


def _parse_op(raw_op: str) -> tuple[int, str]:
    if "=" not in raw_op:
        raise ValueError("Formato inválido. Usa --op \"ID=Materia destino exacta\"")
    left, right = raw_op.split("=", 1)
    id_base = int(left.strip())
    materia_destino = right.strip()
    if not materia_destino:
        raise ValueError("Materia destino vacía en --op")
    return id_base, materia_destino


def _cmd_dataset_recategorizar_lote(args: argparse.Namespace) -> int:
    errores = 0
    print(f"Operaciones a ejecutar: {len(args.op)}")
    print(f"INPLACE={args.inplace} | DRY_RUN={args.dry_run}")
    for i, raw in enumerate(args.op, start=1):
        try:
            id_base, materia_destino = _parse_op(raw)
        except ValueError as e:
            errores += 1
            print("\n" + "=" * 60)
            print(f"[{i}/{len(args.op)}] {raw!r}")
            print(f"[ERROR] {e}")
            continue

        id_actual, modo = _resolver_id_actual_desde_id_base(id_base)
        print("\n" + "=" * 60)
        if id_actual is None:
            errores += 1
            print(f"[{i}/{len(args.op)}] Id base={id_base} -> {materia_destino!r}")
            print(f"[ERROR] No se pudo localizar la pregunta objetivo (motivo={modo}).")
            continue
        print(
            f"[{i}/{len(args.op)}] Id base={id_base} (Id actual={id_actual}) "
            f"-> {materia_destino!r}"
        )
        if modo != "exacta":
            print(f"[AVISO] Resolución no exacta del objetivo (modo={modo}).")
        forward = [f"--id={id_actual}", f"--materia-destino={materia_destino}"]
        if args.inplace:
            forward.append("--inplace")
        if args.dry_run:
            forward.append("--dry-run")
        rc = _run("recategorizar_y_equilibrar.py", forward)
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


def _cmd_plantillas_inyectar_dataset(_args: argparse.Namespace) -> int:
    return _run("inyectar_dataset_en_plantillas.py", [])


def _cmd_plantillas_ampliar_web(args: argparse.Namespace) -> int:
    forward: list[str] = []
    if args.inplace:
        forward.append("--inplace")
    if args.dry_run:
        forward.append("--dry-run")
    return _run("ampliar_plantillas_desde_web.py", forward)


def _cmd_plantillas_asegurar(args: argparse.Namespace) -> int:
    forward: list[str] = []
    if args.solo_comprobar:
        forward.append("--solo-comprobar")
    return _run("asegurar_plantillas_sobre_dataset.py", forward)


def _cmd_plantillas_revisar(_args: argparse.Namespace) -> int:
    return _run("revisar_plantillas.py", [])


def _cmd_dataset_validar(_args: argparse.Namespace) -> int:
    return _run("validar_csv.py", [])


def _cmd_dataset_revision(_args: argparse.Namespace) -> int:
    forward: list[str] = []
    if args.estadisticas:
        forward.append("--estadisticas")
    return _run("revision_final.py", forward)


def _cmd_dataset_variedad(args: argparse.Namespace) -> int:
    forward = [args.accion_variedad]
    if args.accion_variedad == "diversificar":
        if args.dry_run:
            forward.append("--dry-run")
        if args.umbral is not None:
            forward.extend(["--umbral", str(args.umbral)])
    return _run("variedad_materias.py", forward)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CLI unificada de dataset/plantillas")
    sub = p.add_subparsers(dest="grupo", required=True)

    p_ds = sub.add_parser("dataset", help="Operaciones sobre dataset")
    sub_ds = p_ds.add_subparsers(dest="accion", required=True)

    p_balance = sub_ds.add_parser("balance", help="Enrutador hacia balance.py")
    p_balance.add_argument(
        "modo",
        choices=["validar", "ajustar", "reordenar", "corregir", "conservador", "agresivo"],
    )
    p_balance.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Argumentos adicionales para balance.py (p.ej. --detalle)",
    )
    p_balance.set_defaults(func=_cmd_dataset_balance)

    p_rec = sub_ds.add_parser("recategorizar", help="Recategoriza un id y equilibra")
    p_rec.add_argument("--id", dest="id_objetivo", required=True)
    p_rec.add_argument("--materia-destino", default=None)
    p_rec.add_argument("--inplace", action="store_true")
    p_rec.add_argument("--dry-run", action="store_true")
    p_rec.set_defaults(func=_cmd_dataset_recategorizar)

    p_lote = sub_ds.add_parser("recategorizar-lote", help="Recategoriza varias operaciones en lote")
    p_lote.add_argument(
        "--op",
        action="append",
        required=True,
        help='Operación con formato "ID=Materia destino exacta". Repetible.',
    )
    p_lote.add_argument("--inplace", action="store_true")
    p_lote.add_argument("--dry-run", action="store_true")
    p_lote.set_defaults(func=_cmd_dataset_recategorizar_lote)

    p_val = sub_ds.add_parser("validar", help="Validación integral del CSV")
    p_val.set_defaults(func=_cmd_dataset_validar)

    p_rev = sub_ds.add_parser("revision", help="Revisión amplia o solo estadísticas")
    p_rev.add_argument(
        "--estadisticas",
        action="store_true",
        help="Solo tablas de distribución (sin chequeos de calidad)",
    )
    p_rev.set_defaults(func=_cmd_dataset_revision)

    p_var = sub_ds.add_parser("variedad", help="Análisis y diversificación temática")
    p_var.add_argument(
        "accion_variedad",
        choices=["analizar", "diversificar", "curado"],
        help="Subcomando de variedad_materias.py",
    )
    p_var.add_argument("--dry-run", action="store_true")
    p_var.add_argument("--umbral", type=float, default=None)
    p_var.set_defaults(func=_cmd_dataset_variedad)

    p_pl = sub.add_parser("plantillas", help="Operaciones sobre plantillas")
    sub_pl = p_pl.add_subparsers(dest="accion", required=True)

    p_inj = sub_pl.add_parser("inyectar-dataset", help="Inyecta dataset en plantillas")
    p_inj.set_defaults(func=_cmd_plantillas_inyectar_dataset)

    p_amp = sub_pl.add_parser("ampliar-web", help="Amplía semillas desde fuentes web")
    p_amp.add_argument("--inplace", action="store_true")
    p_amp.add_argument("--dry-run", action="store_true")
    p_amp.set_defaults(func=_cmd_plantillas_ampliar_web)

    p_ase = sub_pl.add_parser("asegurar", help="Verifica mínimos e inyección dataset")
    p_ase.add_argument("--solo-comprobar", action="store_true")
    p_ase.set_defaults(func=_cmd_plantillas_asegurar)

    p_rev = sub_pl.add_parser("revisar", help="Informe de calidad de plantillas")
    p_rev.set_defaults(func=_cmd_plantillas_revisar)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

