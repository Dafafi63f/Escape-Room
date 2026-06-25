#!/usr/bin/env python3
# pyright: reportMissingImports=false
# -*- coding: utf-8 -*-
"""
CLI de desarrollo: previsualiza un plan de examen balanceado (modo historia) en terminal.

No es el motor del juego; la lógica está en Juego/Comun/generador_examen_historia.py.

Ejemplo:
  python Files/cli_examen_historia.py --perfil refuerzo --materias 6
  python Files/cli_examen_historia.py --perfil por_curso --curso 2
  python Files/cli_examen_historia.py --perfil simulacro --resumen-historico

Para guardar la salida: redirige a un .txt (p. ej. ... > plan_examen.txt).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent
_JUEGO = _FILES.parent / "Juego"
if str(_FILES) not in sys.path:
    sys.path.insert(0, str(_FILES))
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_orden_materias, cargar_preguntas  # noqa: E402
from Comun.generador_examen_historia import PerfilPedagogico, describir_perfil  # noqa: E402
from Comun.config_historia import validar_config  # noqa: E402
from Comun.presets_historia import argumentos_generador, cargar_presets_historia, config_defecto  # noqa: E402
from Comun.generador_examen_historia import (  # noqa: E402
    cargar_estadisticas_historicas,
    generar_examen,
    resumen_estadisticas,
)
from Comun.modelos import BancoPreguntas  # noqa: E402
from Comun.rutas import resolver_dataset, resolver_listado_materias, resolver_presets  # noqa: E402


def _texto_stdout_seguro(texto: str) -> str:
    """Evita fallos de codificación en terminales Windows (cp1252)."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    return texto.encode(enc, errors="replace").decode(enc)


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(
        description="Previsualizar examen balanceado (usa Juego/Comun/generador_examen_historia.py)",
    )
    p.add_argument(
        "--perfil",
        choices=[x.value for x in PerfilPedagogico],
        default=None,
        help="Perfil pedagógico (omitir si usas --preset)",
    )
    p.add_argument(
        "--preset",
        type=str,
        default=None,
        help="Id de preset en Data/Juego/presets.json (sustituye --perfil y filtros manuales)",
    )
    p.add_argument(
        "--materias",
        type=int,
        default=5,
        help="Materias en el examen (1-20; ignorado en perfil simulacro)",
    )
    p.add_argument("--curso", type=str, default=None, help="Filtro curso (1-4) para por_curso")
    p.add_argument("--semestre", type=str, default=None, help="Filtro semestre opcional (con --curso)")
    p.add_argument("--semilla", type=int, default=None, help="Semilla aleatoria reproducible")
    p.add_argument(
        "--resumen-historico",
        action="store_true",
        help="Muestra materias más exigentes según el histórico",
    )
    args = p.parse_args(argv)

    path_materias = resolver_listado_materias()
    path_csv = resolver_dataset()
    materias_meta = cargar_materias(path_materias)
    preguntas = cargar_preguntas(path_csv, materias_meta)
    orden_materias = cargar_orden_materias(path_materias)
    stats = cargar_estadisticas_historicas(materias_validas=set(materias_meta))

    if args.preset:
        presets = cargar_presets_historia(resolver_presets())
        preset = next((x for x in presets if x.id == args.preset), None)
        if preset is None:
            print(f"Preset desconocido: {args.preset!r}", file=sys.stderr)
            return 2
        cfg = validar_config(
            preset.opciones,
            config_defecto(preset, materias_meta=materias_meta, materias_orden=orden_materias),
            materias_meta=materias_meta,
        )
        gen_kwargs = argumentos_generador(preset, cfg, materias_meta=materias_meta)
        perfil = gen_kwargs["perfil"]
        n_materias = gen_kwargs["n_materias"]
        curso_filtro = gen_kwargs["curso_filtro"]
        semestre_filtro = gen_kwargs["semestre_filtro"]
        grupo_filtro = gen_kwargs["grupo_filtro"]
        preguntas_por_materia = gen_kwargs.get("preguntas_por_materia")
        tipos_permitidos = gen_kwargs.get("tipos_permitidos")
        usar_todas = gen_kwargs["usar_todas_materias_ambito"]
        seleccion_det = gen_kwargs["seleccion_determinista"]
        materia_fija = gen_kwargs.get("materia_fija")
        titulo_perfil = f"{preset.nombre} ({preset.id})"
    else:
        perfil_val = args.perfil or PerfilPedagogico.BALANCEADO.value
        perfil = PerfilPedagogico(perfil_val)
        n_materias = args.materias
        curso_filtro = args.curso
        semestre_filtro = args.semestre
        grupo_filtro = None
        preguntas_por_materia = None
        tipos_permitidos = None
        usar_todas = False
        titulo_perfil = f"{perfil.value} — {describir_perfil(perfil)}"

    if perfil == PerfilPedagogico.POR_CURSO and not curso_filtro:
        print("El perfil por_curso requiere --curso (1-4) o un preset con curso.", file=sys.stderr)
        return 2
    if not usar_todas and perfil != PerfilPedagogico.SIMULACRO and not (1 <= n_materias <= 20):
        print("--materias debe estar entre 1 y 20.", file=sys.stderr)
        return 2

    if args.resumen_historico:
        print(_texto_stdout_seguro(resumen_estadisticas(stats, orden_materias)))
        print()

    try:
        plan = generar_examen(
            preguntas,
            perfil=perfil,
            materias_orden=orden_materias,
            materias_meta=materias_meta,
            stats=stats,
            n_materias=n_materias,
            curso_filtro=curso_filtro,
            semestre_filtro=semestre_filtro,
            grupo_filtro=grupo_filtro,
            preguntas_por_materia=preguntas_por_materia,
            tipos_permitidos=tipos_permitidos,
            usar_todas_materias_ambito=usar_todas,
            seleccion_determinista=seleccion_det,
            materia_fija=materia_fija,
            semilla=args.semilla,
        )
    except ValueError as e:
        print(f"No se pudo generar el examen: {e}", file=sys.stderr)
        return 1

    print(_texto_stdout_seguro(f"Perfil: {titulo_perfil}"))
    print(f"Banco: {BancoPreguntas.DATASET.value} ({len(preguntas)} preguntas)")
    print(_texto_stdout_seguro(f"Materias ({len(plan.materias)}): {', '.join(plan.materias)}"))
    tipos_txt = "/".join(sorted(plan.tipos_permitidos))
    print(f"Preguntas por materia: {plan.preguntas_por_materia} (tipos: {tipos_txt})")
    print(f"Total preguntas: {len(plan.preguntas)}")
    print("\nOrden del examen:")
    for i, pr in enumerate(plan.preguntas, 1):
        snippet = pr.texto[:70] + ("…" if len(pr.texto) > 70 else "")
        print(
            _texto_stdout_seguro(
                f"  {i:>2}. [{pr.materia}] {pr.tipo}/{pr.dificultad} — {snippet}"
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
