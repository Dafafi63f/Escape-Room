# -*- coding: utf-8 -*-
"""
Auditoría del banco: distractores (A–D) y cobertura global de plantillas.

Uso (recomendado vía mantenimiento.py):
  python Files/Scripts/mantenimiento.py auditar-distractores
  python Files/Scripts/mantenimiento.py auditar-plantillas
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent

from utils_plantillas_pool import es_uso_copia_dataset
from utils_texto import normalizar_basico, normalizar_pregunta

PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"
PATH_REPORT = BASE / "Data" / "auditoria_distractores.md"

LETRAS = ("A", "B", "C", "D")

_PLACEHOLDER = re.compile(
    r"(^|\b)(tbd|xxx|lorem|opcion\s*[abcd]|respuesta\s*[abcd]|"
    r"todas\s+las\s+anteriores|ninguna\s+de\s+las\s+anteriores|"
    r"todas\s+son\s+correctas)(\b|$)",
    re.I,
)
_NUMERIC_OK = re.compile(r"^[\d\s.,+\-*/^()%€$·πeOlogn√]+$", re.I)
_GENERICAS = re.compile(
    r"(error de sintaxis|no\s+existe|siempre\s+es\s+0|nunca\s+se\s+puede|"
    r"no\s+tiene\s+sentido|no\s+aplica|no\s+es\s+posible|imposible\s+siempre)",
    re.I,
)
_CASTELLANO = re.compile(
    r"\b(ningún|ninguna|también|además|número|código|fácil|dónde|qué\s+es\s+un)\b",
    re.I,
)


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"\w+", normalizar_basico(s), flags=re.UNICODE) if len(t) > 2}


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def _norm_opt(s: str) -> str:
    return normalizar_basico(s)


def auditar_item(
    label: str,
    pregunta: str,
    opciones: dict[str, str],
    correcta: str,
) -> list[dict]:
    inc: list[dict] = []
    corr = (correcta or "").strip().upper()
    vals = {L: (opciones.get(L) or "").strip() for L in LETRAS}

    if corr not in LETRAS:
        inc.append({"id": label, "tipo": "correcta_invalida", "detalle": repr(correcta)})

    vacias = [L for L in LETRAS if not vals[L]]
    if vacias:
        inc.append({"id": label, "tipo": "opcion_vacia", "detalle": ",".join(vacias)})

    if corr in LETRAS and not vals.get(corr):
        inc.append({"id": label, "tipo": "correcta_vacia", "detalle": corr})

    norms = {_norm_opt(v) for v in vals.values() if v}
    if len(norms) < 4:
        dup = Counter(_norm_opt(v) for v in vals.values() if v)
        reps = [k[:60] for k, n in dup.items() if n > 1]
        inc.append({"id": label, "tipo": "opciones_duplicadas", "detalle": "; ".join(reps[:3])})

    for L, v in vals.items():
        if not v:
            continue
        if len(v) < 3 and not _NUMERIC_OK.match(v):
            inc.append({"id": label, "tipo": "opcion_muy_corta", "detalle": f"{L}={v!r}"})
        if _PLACEHOLDER.search(v):
            inc.append({"id": label, "tipo": "placeholder", "detalle": f"{L}: {v[:80]}"})
        if _GENERICAS.search(v) and L != corr:
            inc.append({"id": label, "tipo": "distractor_generico", "detalle": f"{L}: {v[:80]}"})

    if corr in LETRAS and vals.get(corr):
        nc = _norm_opt(vals[corr])
        for L, v in vals.items():
            if L == corr or not v:
                continue
            nv = _norm_opt(v)
            if (
                len(nc) >= 12
                and len(nv) >= 12
                and nc != nv
                and (nc in nv or nv in nc)
                and abs(len(nc) - len(nv)) < 20
            ):
                inc.append(
                    {
                        "id": label,
                        "tipo": "filtracion_respuesta",
                        "detalle": f"correcta({corr})≈{L}: {v[:70]}",
                    }
                )

    pares_sim = []
    for i, a in enumerate(LETRAS):
        for b in LETRAS[i + 1 :]:
            if not vals[a] or not vals[b]:
                continue
            j = _jaccard(vals[a], vals[b])
            if j >= 0.92 and len(_tokens(vals[a])) >= 4:
                pares_sim.append(f"{a}-{b}({j:.2f})")
    if pares_sim:
        inc.append({"id": label, "tipo": "opciones_muy_parecidas", "detalle": ", ".join(pares_sim)})

    lens = [len(vals[L]) for L in LETRAS if vals[L]]
    if len(lens) >= 2 and max(lens) > 4 * min(lens) and max(lens) > 80:
        inc.append(
            {
                "id": label,
                "tipo": "desbalance_longitud",
                "detalle": f"lens={lens}",
            }
        )

    if corr in LETRAS:
        correct_len = len(vals[corr])
        otros = [len(vals[L]) for L in LETRAS if L != corr and vals[L]]
        if otros and correct_len == max([correct_len] + otros) and correct_len > 60:
            if correct_len > 1.8 * (sum(otros) / len(otros)):
                inc.append(
                    {
                        "id": label,
                        "tipo": "correcta_mas_larga",
                        "detalle": f"len({corr})={correct_len}, media_otros={sum(otros)/len(otros):.0f}",
                    }
                )

    enun = normalizar_pregunta(pregunta)
    for L, v in vals.items():
        nv = normalizar_pregunta(v)
        if nv and enun and nv == enun:
            inc.append({"id": label, "tipo": "opcion_igual_enunciado", "detalle": L})

    return inc


def cargar_dataset() -> list[dict]:
    return list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))


def cargar_plantillas() -> list[tuple[str, str, dict]]:
    data = json.load(PATH_PLANTILLAS.open(encoding="utf-8"))
    out: list[tuple[str, str, dict]] = []
    for tema, items in data.items():
        for i, t in enumerate(items):
            label = f"{tema}#{i}"
            out.append(
                (
                    label,
                    tema,
                    {
                        "pregunta": t.get("pregunta", ""),
                        "opciones": {L: t.get(L, "") for L in LETRAS},
                        "correcta": t.get("correcta", ""),
                        "uso": t.get("uso", ""),
                    },
                )
            )
    return out


def expandir_variaciones(tema: str, idx: int, t: dict) -> list[tuple[str, dict]]:
    base = {
        "pregunta": t.get("pregunta", ""),
        "opciones": {L: t.get(L, "") for L in LETRAS},
        "correcta": t.get("correcta", ""),
        "uso": t.get("uso", ""),
    }
    vars_ = t.get("variaciones")
    if not vars_:
        return [(f"{tema}#{idx}", base)]
    outs = []
    for vi, var in enumerate(vars_):
        p, opts = base["pregunta"], dict(base["opciones"])
        for key, val in var.items():
            ph = "{" + str(key) + "}"
            p = p.replace(ph, str(val))
            for L in LETRAS:
                opts[L] = opts[L].replace(ph, str(val))
        outs.append((f"{tema}#{idx}v{vi}", {**base, "pregunta": p, "opciones": opts}))
    return outs


def cargar_plantillas_expandidas() -> list[tuple[str, dict]]:
    data = json.load(PATH_PLANTILLAS.open(encoding="utf-8"))
    out: list[tuple[str, dict]] = []
    for tema, items in data.items():
        for i, t in enumerate(items):
            for label, item in expandir_variaciones(tema, i, t):
                out.append((label, item))
    return out


def agrupar(incidencias: list[dict]) -> Counter:
    return Counter(x["tipo"] for x in incidencias)


def escribir_reporte(
    inc_ds: list[dict],
    inc_pl: list[dict],
    path: Path,
) -> None:
    lines = [
        "# Auditoría de distractores",
        "",
        f"- **Dataset** (`Preguntas.csv`): {len(inc_ds)} incidencias",
        f"- **Plantillas** (expandidas): {len(inc_pl)} incidencias",
        "",
        "## Resumen por tipo (dataset)",
        "",
    ]
    for tipo, n in agrupar(inc_ds).most_common():
        lines.append(f"- `{tipo}`: {n}")
    lines.extend(["", "## Resumen por tipo (plantillas)", ""])
    for tipo, n in agrupar(inc_pl).most_common():
        lines.append(f"- `{tipo}`: {n}")

    def bloque(titulo: str, items: list[dict], lim: int = 80) -> None:
        lines.extend(["", f"## {titulo}", ""])
        por_tipo: dict[str, list[dict]] = defaultdict(list)
        for x in items:
            por_tipo[x["tipo"]].append(x)
        for tipo in sorted(por_tipo.keys()):
            lines.append(f"### {tipo}")
            for x in por_tipo[tipo][:lim]:
                lines.append(f"- **{x['id']}**: {x['detalle']}")
            rest = len(por_tipo[tipo]) - lim
            if rest > 0:
                lines.append(f"- … +{rest} más")
            lines.append("")

    bloque("Detalle dataset", inc_ds)
    bloque("Detalle plantillas (muestra)", inc_pl, lim=40)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def auditar_plantillas_global() -> int:
    from collections import defaultdict as dd

    from objetivos_balanceo import SLOTS_CANONICOS_12, plantillas_minimas_por_materia
    from utils_orden_temas import cargar_orden_temas

    _USO_A_SLOT = {
        "general": ("Teoria", "Media"),
        "dificil": ("Teoria", "Dificil"),
        "calculo": ("Calculo", "Media"),
        "repuesto": None,
        "reserva": None,
    }

    def _norm(s: str) -> str:
        return (s or "").strip()

    def _key_row(r: dict) -> tuple:
        return (
            _norm(r.get("Materia") or r.get("Tema", "")),
            _norm(r.get("Pregunta", "")),
            _norm(r.get("A", "")),
            _norm(r.get("B", "")),
            _norm(r.get("C", "")),
            _norm(r.get("D", "")),
            _norm(r.get("Correcta", "")),
        )

    def _key_tpl(tema: str, t: dict) -> tuple:
        return (
            _norm(tema),
            _norm(t.get("pregunta", "")),
            _norm(t.get("A", "")),
            _norm(t.get("B", "")),
            _norm(t.get("C", "")),
            _norm(t.get("D", "")),
            _norm(t.get("correcta", "")),
        )

    temas, _ = cargar_orden_temas()
    minimo = plantillas_minimas_por_materia()

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))

    keys_plant = {_key_tpl(tema, t) for tema, items in plantillas.items() for t in items}
    faltan_ds = sum(1 for r in rows if _key_row(r) not in keys_plant)
    n_dataset_tag = sum(
        1 for items in plantillas.values() for t in items if es_uso_copia_dataset(str(t.get("uso", "")))
    )

    print("=" * 72)
    print("AUDITORÍA GLOBAL DE PLANTILLAS")
    print("=" * 72)
    print(f"Dataset: {len(rows)} filas | Plantillas: {sum(len(v) for v in plantillas.values())}")
    print(f"Copias etiquetadas dataset_*: {n_dataset_tag}")
    print(f"Filas del CSV ausentes en plantillas: {faltan_ds}")

    huecos_balance: list[str] = []
    bajo_minimo: list[str] = []
    slots_objetivo = Counter(SLOTS_CANONICOS_12)

    print("\nBalance pool EXTRA (sin dataset_*; tipo/dificultad o uso general/dificil/calculo):")
    print("-" * 72)

    for tema in temas:
        items = plantillas.get(tema, [])
        extra = [t for t in items if not es_uso_copia_dataset(str(t.get("uso", "")))]
        por_slot: Counter = Counter()
        for t in extra:
            tipo = _norm(t.get("tipo", ""))
            dif = _norm(t.get("dificultad", ""))
            if not tipo or not dif:
                infer = _USO_A_SLOT.get(t.get("uso"))
                if infer:
                    tipo, dif = infer
            if tipo and dif:
                por_slot[(tipo, dif)] += 1
        por_ds = Counter(
            (_norm(t.get("tipo", "Teoria")), _norm(t.get("dificultad", "Media")))
            for t in items
            if es_uso_copia_dataset(str(t.get("uso", "")))
        )
        faltan_slot = [
            f"{tipo}/{dif}"
            for (tipo, dif), _need in slots_objetivo.items()
            if por_slot.get((tipo, dif), 0) < 1 and por_ds.get((tipo, dif), 0) < 1
        ]
        if faltan_slot:
            huecos_balance.append(f"{tema}: falta {', '.join(faltan_slot)}")
        if len(items) < minimo:
            bajo_minimo.append(f"{tema}: {len(items)} < {minimo}")

    if huecos_balance:
        print(
            f"  [HUECOS] {len(huecos_balance)} materias sin cubrir algún slot "
            "(ni extra ni copia dataset_*):"
        )
        for line in huecos_balance[:15]:
            print(f"    - {line}")
        if len(huecos_balance) > 15:
            print(f"    ... +{len(huecos_balance) - 15} más")
    else:
        print("  [OK] Todas las materias tienen ≥1 plantilla extra por cada (Tipo, Dificultad)")

    if bajo_minimo:
        print(f"\n  [BAJO MÍNIMO] {len(bajo_minimo)} materias con <{minimo} entradas totales:")
        for line in bajo_minimo[:10]:
            print(f"    - {line}")
    else:
        print(f"\n  [OK] Todas ≥ {minimo} entradas por materia (2× dataset)")

    por_clave: dict[tuple, list[str]] = dd(list)
    for tema, items in plantillas.items():
        for i, t in enumerate(items):
            k = (
                _norm(t.get("pregunta", "")),
                _norm(t.get("A", "")),
                _norm(t.get("B", "")),
                _norm(t.get("C", "")),
                _norm(t.get("D", "")),
            )
            por_clave[k].append(f"{tema}#{i}")

    exact_global = {k: v for k, v in por_clave.items() if len(v) > 1 and k[0]}
    print(f"\nDuplicados exactos globales (mismo enunciado+opciones): {len(exact_global)}")
    for _k, labels in list(exact_global.items())[:8]:
        print(f"  {' | '.join(labels[:4])}{'…' if len(labels) > 4 else ''}")

    print("\nComandos sugeridos:")
    print("  python Files/Scripts/mantenimiento.py plantillas pipeline")
    print("  python Files/Scripts/duplicados.py plantillas")
    print("=" * 72)

    return 1 if faltan_ds or exact_global else (1 if huecos_balance else 0)


def main_distractores(*, json_path: str = "", solo_dataset: bool = False) -> int:

    inc_ds: list[dict] = []
    for row in cargar_dataset():
        label = f"Id {row.get('Id', '?')}"
        inc_ds.extend(
            auditar_item(
                label,
                row.get("Pregunta", ""),
                {L: row.get(L, "") for L in LETRAS},
                row.get("Correcta", ""),
            )
        )

    inc_pl: list[dict] = []
    if not solo_dataset:
        for label, item in cargar_plantillas_expandidas():
            inc_pl.extend(
                auditar_item(
                    label,
                    item["pregunta"],
                    item["opciones"],
                    item["correcta"],
                )
            )

    print("=== Distractores: Preguntas.csv ===")
    print(f"Filas: {len(cargar_dataset())} | Incidencias: {len(inc_ds)}")
    for tipo, n in agrupar(inc_ds).most_common(12):
        print(f"  {tipo}: {n}")

    if not solo_dataset:
        print("\n=== Distractores: plantillas (expandidas) ===")
        n_pl = len(cargar_plantillas_expandidas())
        print(f"Instancias: {n_pl} | Incidencias: {len(inc_pl)}")
        for tipo, n in agrupar(inc_pl).most_common(12):
            print(f"  {tipo}: {n}")

    escribir_reporte(inc_ds, inc_pl, PATH_REPORT)
    print(f"\nInforme: {PATH_REPORT}")

    if json_path:
        out = {"dataset": inc_ds, "plantillas": inc_pl}
        Path(json_path).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return 1 if inc_ds else 0


def main(argv: list[str] | None = None) -> int:
    forward = list(argv if argv is not None else sys.argv[1:])
    if forward and forward[0] == "plantillas":
        return auditar_plantillas_global()
    if forward and forward[0] == "distractores":
        forward = forward[1:]
    parser = argparse.ArgumentParser(description="Auditoría de distractores")
    parser.add_argument("--json", type=str, default="")
    parser.add_argument("--solo-dataset", action="store_true")
    args = parser.parse_args(forward)
    return main_distractores(json_path=args.json, solo_dataset=args.solo_dataset)


if __name__ == "__main__":
    raise SystemExit(main())
