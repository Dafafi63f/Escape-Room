#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI unificada de mantenimiento (banco cerrado: 480 CSV + pool juego 1000).

  python Files/mantenimiento.py validar [--detalle] [--estricto]
  python Files/mantenimiento.py revision [--estadisticas]
  python Files/mantenimiento.py dataset [--variedad]
  python Files/mantenimiento.py auditar-distractores [--json PATH] [--solo-dataset]
  python Files/mantenimiento.py auditar-plantillas
  python Files/mantenimiento.py plantillas {comprobar|reclasificar} ...
  python Files/mantenimiento.py duplicados ...
  python Docs/utilidades_distribucion.py [--solo-limpieza] [--dry-run]

Bancos cerrados (solo revisión manual; sin altas/bajas):
  Preguntas.csv, plantillas.json (960 filas, sin variaciones),
  40 exclusivas resistencia en Juego/Comun/preguntas_resistencia_exclusivas_datos.py.
Overrides: TFG_PERMITIR_CSV=1 | TFG_PERMITIR_PLANTILLAS=1.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent
if str(_FILES) not in sys.path:
    sys.path.insert(0, str(_FILES))

ROOT = _FILES.parent

if sys.platform == "win32":
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")

from utils_dataset_csv import borrar_pycache_en_proyecto  # noqa: E402


def cmd_validar(args: argparse.Namespace) -> int:
    from balance_lib import ejecutar_validar

    return ejecutar_validar(detalle=args.detalle, estricto=args.estricto)


def cmd_revision(args: argparse.Namespace) -> int:
    from validacion_dataset import main as val_main

    forward = ["--estadisticas"] if args.estadisticas else []
    return val_main(forward)


def cmd_dataset(args: argparse.Namespace) -> int:
    from validacion_dataset import main as val_main

    forward = ["--extendida"]
    if args.variedad:
        forward.append("--variedad")
    return val_main(forward)


def cmd_auditar_distractores(args: argparse.Namespace) -> int:
    from auditoria import main_distractores

    return main_distractores(json_path=args.json or "", solo_dataset=args.solo_dataset)


def cmd_auditar_plantillas(_args: argparse.Namespace) -> int:
    from auditoria import auditar_plantillas_global

    return auditar_plantillas_global()


def cmd_plantillas(args: argparse.Namespace) -> int:
    from utils_banco_cerrado import rechazar_mutacion_plantillas

    sub = args.plantillas_cmd
    if sub == "reclasificar" and args.aplicar:
        rechazar_mutacion_plantillas("mantenimiento.py plantillas reclasificar --aplicar")

    if sub == "comprobar":
        from auditoria import comprobar_cobertura_plantillas

        return comprobar_cobertura_plantillas()
    if sub == "reclasificar":
        import reclasificar_plantillas as rp

        argv = []
        if args.aplicar:
            argv.append("--aplicar")
        if args.solo_internet:
            argv.append("--solo-internet")
        argv.extend(["--min-score", str(args.min_score), "--margen", str(args.margen)])
        old_argv = sys.argv
        try:
            sys.argv = ["reclasificar_plantillas.py", *argv]
            return rp.main()
        finally:
            sys.argv = old_argv
    return 2


def cmd_duplicados(args: argparse.Namespace) -> int:
    from duplicados import main as dup_main

    return dup_main(args.duplicados_argv)


def cmd_temporales(args: argparse.Namespace) -> int:
    import subprocess

    cmd = [sys.executable, str(ROOT / "Docs" / "utilidades_distribucion.py"), "--solo-limpieza"]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.solo_pycache:
        cmd.append("--solo-pycache")
    if args.solo_juego:
        cmd.append("--solo-juego")
    if args.solo_txt:
        cmd.append("--solo-txt")
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mantenimiento del TFG (dataset cerrado).",
        epilog="Ver Files/README.md y Docs/Entrega/Memoria_TFG.md §5.4",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_val = sub.add_parser("validar", help="Balance y orden canónico (solo lectura)")
    p_val.add_argument("--detalle", action="store_true")
    p_val.add_argument("--estricto", action="store_true")
    p_val.set_defaults(func=cmd_validar)

    p_rev = sub.add_parser("revision", help="Revisión amplia del CSV")
    p_rev.add_argument("--estadisticas", action="store_true")
    p_rev.set_defaults(func=cmd_revision)

    p_ds = sub.add_parser("dataset", help="Validación extendida (hash, complejidad, …)")
    p_ds.add_argument("--variedad", action="store_true")
    p_ds.set_defaults(func=cmd_dataset)

    p_ad = sub.add_parser("auditar-distractores", help="Auditoría de distractores (salida por terminal)")
    p_ad.add_argument("--json", type=str, default="")
    p_ad.add_argument("--solo-dataset", action="store_true")
    p_ad.set_defaults(func=cmd_auditar_distractores)

    p_ap = sub.add_parser("auditar-plantillas", help="Cobertura de plantillas.json")
    p_ap.set_defaults(func=cmd_auditar_plantillas)

    p_pl = sub.add_parser("plantillas", help="Comprobación y auditoría de plantillas.json")
    pl_sub = p_pl.add_subparsers(dest="plantillas_cmd", required=True)
    pl_sub.add_parser("comprobar", help="Cobertura mínima por materia (solo lectura)")
    p_recl = pl_sub.add_parser(
        "reclasificar",
        help="Audita materia de plantillas según contenido (criterios_clasificacion_materia.csv)",
    )
    p_recl.add_argument("--aplicar", action="store_true")
    p_recl.add_argument("--solo-internet", action="store_true")
    p_recl.add_argument("--min-score", type=float, default=2.0)
    p_recl.add_argument("--margen", type=float, default=2.0)
    p_pl.set_defaults(func=cmd_plantillas)

    p_dup = sub.add_parser(
        "duplicados",
        help="Delega en duplicados.py (revisar, plantillas, …)",
    )
    p_dup.add_argument("duplicados_argv", nargs=argparse.REMAINDER)
    p_dup.set_defaults(func=cmd_duplicados)

    p_tmp = sub.add_parser(
        "temporales",
        help="Borra __pycache__, cachés y datos locales del juego en Data/Juego/",
    )
    p_tmp.add_argument("--dry-run", action="store_true")
    grupo_tmp = p_tmp.add_mutually_exclusive_group()
    grupo_tmp.add_argument("--solo-pycache", action="store_true")
    grupo_tmp.add_argument("--solo-juego", action="store_true")
    grupo_tmp.add_argument("--solo-txt", action="store_true")
    p_tmp.set_defaults(func=cmd_temporales)

    p_py = sub.add_parser("pycache", help="Alias de temporales --solo-pycache")
    p_py.add_argument("--dry-run", action="store_true")
    p_py.set_defaults(func=cmd_temporales, solo_pycache=True, solo_txt=False)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    finally:
        borrar_pycache_en_proyecto()


if __name__ == "__main__":
    raise SystemExit(main())
