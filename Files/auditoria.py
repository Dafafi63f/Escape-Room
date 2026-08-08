# -*- coding: utf-8 -*-
"""
Auditoría del banco: distractores (A–D) y cobertura global de plantillas.

Uso (recomendado vía mantenimiento.py):
  python Files/mantenimiento.py auditar-distractores
  python Files/mantenimiento.py auditar-plantillas
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

from utils_plantillas_pool import es_uso_copia_dataset
from utils_texto import normalizar_basico, normalizar_pregunta

from rutas_data import PATH_PREGUNTAS as PATH_CSV, PATH_PLANTILLAS, ruta_escritura_proyecto
LETRAS = ("A", "B", "C", "D")

_PLACEHOLDER = re.compile(
    r"(^|\b)(tbd|xxx|lorem|opcion\s*[abcd]|respuesta\s*[abcd]|"
    r"todas\s+las\s+anteriores|ninguna\s+de\s+las\s+anteriores|"
    r"todas\s+son\s+correctas)(\b|$)",
    re.I,
)
_NUMERIC_OK = re.compile(r"^[\d\s.,+\-*/^()%€$·πelogn√]+$", re.I)
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


def _incidencia(label: str, tipo: str, detalle: str) -> dict:
    return {"id": label, "tipo": tipo, "detalle": detalle}


def _auditar_correcta_y_vacias(
    label: str,
    corr: str,
    correcta: str,
    vals: dict[str, str],
) -> list[dict]:
    inc: list[dict] = []
    if corr not in LETRAS:
        inc.append(_incidencia(label, "correcta_invalida", repr(correcta)))
    vacias = [L for L in LETRAS if not vals[L]]
    if vacias:
        inc.append(_incidencia(label, "opcion_vacia", ",".join(vacias)))
    if corr in LETRAS and not vals.get(corr):
        inc.append(_incidencia(label, "correcta_vacia", corr))
    return inc


def _auditar_opciones_duplicadas(label: str, vals: dict[str, str]) -> list[dict]:
    norms = {_norm_opt(v) for v in vals.values() if v}
    if len(norms) >= 4:
        return []
    dup = Counter(_norm_opt(v) for v in vals.values() if v)
    reps = [k[:60] for k, n in dup.items() if n > 1]
    return [_incidencia(label, "opciones_duplicadas", "; ".join(reps[:3]))]


def _auditar_calidad_opciones(
    label: str, vals: dict[str, str], corr: str
) -> list[dict]:
    inc: list[dict] = []
    for L, v in vals.items():
        if not v:
            continue
        if len(v) < 3 and not _NUMERIC_OK.match(v):
            inc.append(_incidencia(label, "opcion_muy_corta", f"{L}={v!r}"))
        if _PLACEHOLDER.search(v):
            inc.append(_incidencia(label, "placeholder", f"{L}: {v[:80]}"))
        if _GENERICAS.search(v) and L != corr:
            inc.append(_incidencia(label, "distractor_generico", f"{L}: {v[:80]}"))
    return inc


def _auditar_filtracion_respuesta(
    label: str, vals: dict[str, str], corr: str
) -> list[dict]:
    if corr not in LETRAS or not vals.get(corr):
        return []
    inc: list[dict] = []
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
                _incidencia(
                    label,
                    "filtracion_respuesta",
                    f"correcta({corr})≈{L}: {v[:70]}",
                )
            )
    return inc


def _auditar_similitud_y_longitud(
    label: str, vals: dict[str, str], corr: str
) -> list[dict]:
    inc: list[dict] = []
    pares_sim = []
    for i, a in enumerate(LETRAS):
        for b in LETRAS[i + 1 :]:
            if not vals[a] or not vals[b]:
                continue
            j = _jaccard(vals[a], vals[b])
            if j >= 0.92 and len(_tokens(vals[a])) >= 4:
                pares_sim.append(f"{a}-{b}({j:.2f})")
    if pares_sim:
        inc.append(_incidencia(label, "opciones_muy_parecidas", ", ".join(pares_sim)))

    lens = [len(vals[L]) for L in LETRAS if vals[L]]
    if len(lens) >= 2 and max(lens) > 4 * min(lens) and max(lens) > 80:
        inc.append(_incidencia(label, "desbalance_longitud", f"lens={lens}"))

    if corr in LETRAS:
        correct_len = len(vals[corr])
        otros = [len(vals[L]) for L in LETRAS if L != corr and vals[L]]
        if otros and correct_len == max([correct_len] + otros) and correct_len > 60:
            if correct_len > 1.8 * (sum(otros) / len(otros)):
                inc.append(
                    _incidencia(
                        label,
                        "correcta_mas_larga",
                        f"len({corr})={correct_len}, media_otros={sum(otros)/len(otros):.0f}",
                    )
                )
    return inc


def _auditar_opcion_igual_enunciado(
    label: str, pregunta: str, vals: dict[str, str]
) -> list[dict]:
    enun = normalizar_pregunta(pregunta)
    inc: list[dict] = []
    for L, v in vals.items():
        nv = normalizar_pregunta(v)
        if nv and enun and nv == enun:
            inc.append(_incidencia(label, "opcion_igual_enunciado", L))
    return inc


def auditar_item(
    label: str,
    pregunta: str,
    opciones: dict[str, str],
    correcta: str,
) -> list[dict]:
    corr = (correcta or "").strip().upper()
    vals = {L: (opciones.get(L) or "").strip() for L in LETRAS}
    inc: list[dict] = []
    inc.extend(_auditar_correcta_y_vacias(label, corr, correcta, vals))
    inc.extend(_auditar_opciones_duplicadas(label, vals))
    inc.extend(_auditar_calidad_opciones(label, vals, corr))
    inc.extend(_auditar_filtracion_respuesta(label, vals, corr))
    inc.extend(_auditar_similitud_y_longitud(label, vals, corr))
    inc.extend(_auditar_opcion_igual_enunciado(label, pregunta, vals))
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


def expandir_fila_plantilla(tema: str, idx: int, t: dict) -> list[tuple[str, dict]]:
    """Una etiqueta por fila JSON (sin expansión de variaciones)."""
    from utils_plantillas_core import expandir_plantilla_instancias

    outs: list[tuple[str, dict]] = []
    for vi, inst in enumerate(expandir_plantilla_instancias(tema, t)):
        sufijo = f"v{vi}" if vi else ""
        outs.append(
            (
                f"{tema}#{idx}{sufijo}",
                {
                    "pregunta": inst["pregunta"],
                    "opciones": inst["opciones"],
                    "correcta": inst["correcta"],
                    "uso": inst.get("uso", ""),
                },
            )
        )
    return outs


def cargar_plantillas_expandidas() -> list[tuple[str, dict]]:
    data = json.load(PATH_PLANTILLAS.open(encoding="utf-8"))
    out: list[tuple[str, dict]] = []
    for tema, items in data.items():
        for i, t in enumerate(items):
            for label, item in expandir_fila_plantilla(tema, i, t):
                out.append((label, item))
    return out


def agrupar(incidencias: list[dict]) -> Counter:
    return Counter(x["tipo"] for x in incidencias)


def comprobar_cobertura_plantillas() -> int:
    """Comprueba 12 dataset + 12 extra por materia (960 filas). Sin ``variaciones``. Solo lectura."""
    from objetivos_balanceo import (
        MIN_PLANTILLAS_POR_MATERIA_FACTOR,
        TARGET_TOTAL_PREGUNTAS,
        plantillas_minimas_por_materia,
        preguntas_por_materia,
    )
    from utils_orden_temas import cargar_orden_temas

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plant = json.load(f)
    variaciones: list[str] = []
    for tema, items in plant.items():
        for i, t in enumerate(items):
            if isinstance(t, dict) and t.get("variaciones"):
                variaciones.append(f"{tema}[{i}]")
    if variaciones:
        msgs_var = [
            f"Campo 'variaciones' prohibido ({len(variaciones)} filas); "
            "materializar en filas sueltas o eliminar."
        ]
        for v in variaciones[:5]:
            msgs_var.append(f"  - {v}")
        if len(variaciones) > 5:
            msgs_var.append(f"  ... y {len(variaciones) - 5} más")
        print("\n".join(msgs_var))
        return 1
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))
    por_plant = {m: len(plant.get(m, [])) for m in plant}
    por_ds = Counter(r["Materia"] for r in rows)
    minimo = plantillas_minimas_por_materia()
    temas, _ = cargar_orden_temas()

    msgs: list[str] = []
    total_plant = sum(por_plant.values())
    if total_plant != TARGET_TOTAL_PREGUNTAS * 2:
        msgs.append(
            f"Total plantillas ({total_plant}) distinto del objetivo "
            f"({TARGET_TOTAL_PREGUNTAS * 2}: 480 dataset + 480 extra)"
        )
    elif total_plant <= TARGET_TOTAL_PREGUNTAS:
        msgs.append(f"Total plantillas ({total_plant}) no supera el dataset ({TARGET_TOTAL_PREGUNTAS})")
    for tema in temas:
        n_plant = por_plant.get(tema, 0)
        n_ds = por_ds.get(tema, preguntas_por_materia())
        if n_plant <= n_ds:
            msgs.append(f"{tema!r}: {n_plant} plantillas <= {n_ds} en dataset")
        elif n_plant < minimo:
            msgs.append(
                f"{tema!r}: {n_plant} < mínimo {minimo} ({MIN_PLANTILLAS_POR_MATERIA_FACTOR}× dataset)"
            )

    print(f"Dataset: {TARGET_TOTAL_PREGUNTAS} preguntas ({preguntas_por_materia()}/materia)")
    print(f"Plantillas: {total_plant} (mínimo {minimo}/materia, objetivo 24/materia)")
    if not msgs:
        print("OK: cobertura de plantillas adecuada.")
        return 0
    print("Desviaciones:")
    for m in msgs:
        print(f"  - {m}")
    return 1


_USO_A_SLOT_PLANTILLA = {
    "general": ("Teoria", "Media"),
    "dificil": ("Teoria", "Dificil"),
    "calculo": ("Calculo", "Media"),
    "repuesto": None,
    "reserva": None,
}


def _norm_plantilla_campo(s: str) -> str:
    return (s or "").strip()


def _key_fila_auditoria(r: dict) -> tuple:
    return (
        _norm_plantilla_campo(r.get("Materia") or r.get("Tema", "")),
        _norm_plantilla_campo(r.get("Pregunta", "")),
        _norm_plantilla_campo(r.get("A", "")),
        _norm_plantilla_campo(r.get("B", "")),
        _norm_plantilla_campo(r.get("C", "")),
        _norm_plantilla_campo(r.get("D", "")),
        _norm_plantilla_campo(r.get("Correcta", "")),
    )


def _key_plantilla_auditoria(tema: str, t: dict) -> tuple:
    return (
        _norm_plantilla_campo(tema),
        _norm_plantilla_campo(t.get("pregunta", "")),
        _norm_plantilla_campo(t.get("A", "")),
        _norm_plantilla_campo(t.get("B", "")),
        _norm_plantilla_campo(t.get("C", "")),
        _norm_plantilla_campo(t.get("D", "")),
        _norm_plantilla_campo(t.get("correcta", "")),
    )


def _slot_plantilla_extra(t: dict) -> tuple[str, str] | None:
    tipo = _norm_plantilla_campo(t.get("tipo", ""))
    dif = _norm_plantilla_campo(t.get("dificultad", ""))
    if not tipo or not dif:
        uso = t.get("uso")
        infer = _USO_A_SLOT_PLANTILLA.get(uso) if isinstance(uso, str) else None
        if infer:
            tipo, dif = infer
    if tipo and dif:
        return tipo, dif
    return None


def _analizar_balance_extra_tema(
    tema: str,
    items: list,
    *,
    slots_objetivo: Counter,
    minimo: int,
) -> tuple[str | None, str | None]:
    extra = [t for t in items if not es_uso_copia_dataset(str(t.get("uso", "")))]
    por_slot: Counter = Counter()
    for t in extra:
        slot = _slot_plantilla_extra(t)
        if slot:
            por_slot[slot] += 1
    por_ds = Counter(
        (
            _norm_plantilla_campo(t.get("tipo", "Teoria")),
            _norm_plantilla_campo(t.get("dificultad", "Media")),
        )
        for t in items
        if es_uso_copia_dataset(str(t.get("uso", "")))
    )
    faltan_slot = [
        f"{tipo}/{dif}"
        for (tipo, dif), _need in slots_objetivo.items()
        if por_slot.get((tipo, dif), 0) < 1 and por_ds.get((tipo, dif), 0) < 1
    ]
    hueco = f"{tema}: falta {', '.join(faltan_slot)}" if faltan_slot else None
    bajo = f"{tema}: {len(items)} < {minimo}" if len(items) < minimo else None
    return hueco, bajo


def _imprimir_lista_auditoria(
    titulo: str, lineas: list[str], *, max_show: int, ok_msg: str
) -> None:
    if lineas:
        print(titulo)
        for line in lineas[:max_show]:
            print(f"    - {line}")
        if len(lineas) > max_show:
            print(f"    ... +{len(lineas) - max_show} más")
    else:
        print(ok_msg)


def _duplicados_exactos_plantillas(plantillas: dict) -> dict[tuple, list[str]]:
    from collections import defaultdict as dd

    por_clave: dict[tuple, list[str]] = dd(list)
    for tema, items in plantillas.items():
        for i, t in enumerate(items):
            k = (
                _norm_plantilla_campo(t.get("pregunta", "")),
                _norm_plantilla_campo(t.get("A", "")),
                _norm_plantilla_campo(t.get("B", "")),
                _norm_plantilla_campo(t.get("C", "")),
                _norm_plantilla_campo(t.get("D", "")),
            )
            por_clave[k].append(f"{tema}#{i}")
    return {k: v for k, v in por_clave.items() if len(v) > 1 and k[0]}


def _recoger_huecos_plantillas(
    plantillas: dict,
    temas: list[str],
    *,
    slots_objetivo: Counter,
    minimo: int,
) -> tuple[list[str], list[str]]:
    huecos_balance: list[str] = []
    bajo_minimo: list[str] = []
    for tema in temas:
        items = plantillas.get(tema, [])
        hueco, bajo = _analizar_balance_extra_tema(
            tema, items, slots_objetivo=slots_objetivo, minimo=minimo
        )
        if hueco:
            huecos_balance.append(hueco)
        if bajo:
            bajo_minimo.append(bajo)
    return huecos_balance, bajo_minimo


def auditar_plantillas_global() -> int:
    from objetivos_balanceo import SLOTS_CANONICOS_12, plantillas_minimas_por_materia
    from utils_orden_temas import cargar_orden_temas

    temas, _ = cargar_orden_temas()
    minimo = plantillas_minimas_por_materia()

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)
    rows = list(csv.DictReader(PATH_CSV.open(encoding="utf-8", newline=""), delimiter=";"))

    keys_plant = {
        _key_plantilla_auditoria(tema, t)
        for tema, items in plantillas.items()
        for t in items
    }
    faltan_ds = sum(1 for r in rows if _key_fila_auditoria(r) not in keys_plant)
    n_dataset_tag = sum(
        1
        for items in plantillas.values()
        for t in items
        if es_uso_copia_dataset(str(t.get("uso", "")))
    )

    print("=" * 72)
    print("AUDITORÍA GLOBAL DE PLANTILLAS")
    print("=" * 72)
    print(f"Dataset: {len(rows)} filas | Plantillas: {sum(len(v) for v in plantillas.values())}")
    print(f"Copias etiquetadas dataset_*: {n_dataset_tag}")
    print(f"Filas del CSV ausentes en plantillas: {faltan_ds}")

    slots_objetivo = Counter(SLOTS_CANONICOS_12)
    print("\nBalance pool EXTRA (sin dataset_*; tipo/dificultad o uso general/dificil/calculo):")
    print("-" * 72)

    huecos_balance, bajo_minimo = _recoger_huecos_plantillas(
        plantillas, temas, slots_objetivo=slots_objetivo, minimo=minimo
    )
    _imprimir_lista_auditoria(
        f"  [HUECOS] {len(huecos_balance)} materias sin cubrir algún slot "
        "(ni extra ni copia dataset_*):",
        huecos_balance,
        max_show=15,
        ok_msg="  [OK] Todas las materias tienen ≥1 plantilla extra por cada (Tipo, Dificultad)",
    )
    _imprimir_lista_auditoria(
        f"\n  [BAJO MÍNIMO] {len(bajo_minimo)} materias con <{minimo} entradas totales:",
        bajo_minimo,
        max_show=10,
        ok_msg=f"\n  [OK] Todas ≥ {minimo} entradas por materia (2× dataset)",
    )

    exact_global = _duplicados_exactos_plantillas(plantillas)
    print(f"\nDuplicados exactos globales (mismo enunciado+opciones): {len(exact_global)}")
    for _k, labels in list(exact_global.items())[:8]:
        print(f"  {' | '.join(labels[:4])}{'…' if len(labels) > 4 else ''}")

    print("\nComandos sugeridos:")
    print("  python Files/mantenimiento.py plantillas comprobar")
    print("  python Files/duplicados.py revisar")
    print("=" * 72)

    if faltan_ds or exact_global or huecos_balance:
        return 1
    return 0


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

    if json_path:
        out = {"dataset": inc_ds, "plantillas": inc_pl}
        destino = ruta_escritura_proyecto(json_path)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
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
