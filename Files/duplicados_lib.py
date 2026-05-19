# -*- coding: utf-8 -*-
"""
Lógica de deduplicación: revisar, plantillas, dataset+plantillas, exacto, enunciado.
Invocado desde duplicados.py.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from balance_lib import ejecutar_validar
from balance_lib import ejecutar_reordenar
from utils_deduplicacion import (
    clave_enunciado,
    clave_esqueleto_colapsado,
    clave_esqueleto_pregunta,
    clave_familia_plantilla,
    clave_respuesta_sustantiva,
    deduplicar_plantillas_dict,
    es_duplicado_de_alguna,
    motivo_duplicado,
    quitar_plantillas_presentes_en_dataset,
)
from utils_dataset_csv import fila_pregunta, guardar_filas_csv, materia_de_fila, ordenar_filas_por_tema_y_id, renumerar_ids
from utils_texto import normalizar_basico

PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"


def _safe_print(msg: str) -> None:
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode(enc, errors="replace").decode(enc))


def expandir_plantilla(template: dict) -> list[dict]:
    preguntas = []
    variaciones = template.get("variaciones")
    if variaciones:
        for var in variaciones:
            p = template["pregunta"]
            a, b, c, d = template["A"], template["B"], template["C"], template["D"]
            for key, val in var.items():
                ph = "{" + str(key) + "}"
                p = p.replace(ph, str(val))
                a = a.replace(ph, str(val))
                b = b.replace(ph, str(val))
                c = c.replace(ph, str(val))
                d = d.replace(ph, str(val))
            preguntas.append(
                {
                    "Pregunta": p,
                    "A": a,
                    "B": b,
                    "C": c,
                    "D": d,
                    "Correcta": template["correcta"],
                    "Dificultad": template.get("dificultad", "Media"),
                    "Tipo": template.get("tipo", "Teoria"),
                }
            )
    else:
        preguntas.append(
            {
                "Pregunta": template["pregunta"],
                "A": template["A"],
                "B": template["B"],
                "C": template["C"],
                "D": template["D"],
                "Correcta": template["correcta"],
                "Dificultad": template.get("dificultad", "Media"),
                "Tipo": template.get("tipo", "Teoria"),
            }
        )
    return preguntas


def _bucket_key(fila: dict) -> str:
    toks = sorted(clave_enunciado(fila).split())
    if len(toks) >= 3:
        return " ".join(toks[:3])
    return clave_enunciado(fila)[:40]


def pares_duplicados(items: list[tuple[str, dict]]) -> list[tuple[str, str, str]]:
    """Compara solo candidatos en el mismo bucket léxico (evita O(n²) global)."""
    out: list[tuple[str, str, str]] = []
    por_enunciado: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    por_bucket: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    por_respuesta: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    por_esqueleto: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    por_familia: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    por_colapsado: dict[str, list[tuple[str, dict]]] = defaultdict(list)

    for label, fila in items:
        eq = clave_enunciado(fila)
        if eq:
            por_enunciado[eq].append((label, fila))
        por_bucket[_bucket_key(fila)].append((label, fila))
        rc = clave_respuesta_sustantiva(fila)
        if rc:
            por_respuesta[rc].append((label, fila))
        sk = clave_esqueleto_pregunta(fila)
        if "#" in sk:
            por_esqueleto[sk].append((label, fila))
        fam = clave_familia_plantilla(fila)
        if fam:
            por_familia[fam].append((label, fila))
        col = clave_esqueleto_colapsado(fila)
        if col and "#" in clave_esqueleto_pregunta(fila):
            por_colapsado[col].append((label, fila))

    for ids in por_enunciado.values():
        if len(ids) < 2:
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                out.append((ids[i][0], ids[j][0], "mismo_enunciado"))

    vistos = {tuple(sorted((a, b))) for a, b, _ in out}
    for grupo in por_familia.values():
        if len(grupo) < 2:
            continue
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                par = tuple(sorted((grupo[i][0], grupo[j][0])))
                if par in vistos:
                    continue
                m = motivo_duplicado(grupo[i][1], grupo[j][1])
                if m:
                    out.append((grupo[i][0], grupo[j][0], m))
                    vistos.add(par)

    for grupo in por_colapsado.values():
        if len(grupo) < 2:
            continue
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                par = tuple(sorted((grupo[i][0], grupo[j][0])))
                if par in vistos:
                    continue
                m = motivo_duplicado(grupo[i][1], grupo[j][1])
                if m:
                    out.append((grupo[i][0], grupo[j][0], m))
                    vistos.add(par)

    for grupo in por_esqueleto.values():
        if len(grupo) < 2:
            continue
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                par = tuple(sorted((grupo[i][0], grupo[j][0])))
                if par in vistos:
                    continue
                m = motivo_duplicado(grupo[i][1], grupo[j][1])
                if m:
                    out.append((grupo[i][0], grupo[j][0], m))
                    vistos.add(par)

    for grupo in por_respuesta.values():
        if len(grupo) < 2:
            continue
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                par = tuple(sorted((grupo[i][0], grupo[j][0])))
                if par in vistos:
                    continue
                m = motivo_duplicado(grupo[i][1], grupo[j][1])
                if m:
                    out.append((grupo[i][0], grupo[j][0], m))
                    vistos.add(par)

    for grupo in por_bucket.values():
        if len(grupo) < 2:
            continue
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                par = tuple(sorted((grupo[i][0], grupo[j][0])))
                if par in vistos:
                    continue
                m = motivo_duplicado(grupo[i][1], grupo[j][1])
                if m:
                    out.append((grupo[i][0], grupo[j][0], m))
                    vistos.add(par)
    return out


def revisar_dataset() -> dict:
    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))

    items = [(f.get("Id", "?"), f) for f in filas]
    pares = pares_duplicados(items)

    por_enunciado: dict[str, list[str]] = defaultdict(list)
    for fid, f in items:
        por_enunciado[clave_enunciado(f)].append(fid)
    exactos_enunciado = {k: v for k, v in por_enunciado.items() if len(v) > 1 and k}

    return {
        "total": len(filas),
        "pares": pares,
        "enunciados_repetidos": exactos_enunciado,
    }


def revisar_plantillas() -> dict:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)

    total = 0
    pares_por_tema: dict[str, list] = {}
    pares_global: list[tuple[str, str, str, str]] = []

    for tema, lst in plantillas.items():
        total += len(lst)
        tema_items = [(f"{tema}#{i}", t) for i, t in enumerate(lst)]
        p = pares_duplicados(
            [
                (k, {"Pregunta": t.get("pregunta", ""), **t})
                for k, t in tema_items
            ]
        )
        if p:
            pares_por_tema[tema] = p

    # Cruce entre temas: solo buckets con posible solapamiento léxico
    por_bucket_global: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for tema, lst in plantillas.items():
        for i, t in enumerate(lst):
            fila = {"Pregunta": t.get("pregunta", ""), **t}
            por_bucket_global[_bucket_key(fila)].append((f"{tema}#{i}", fila))

    for grupo in por_bucket_global.values():
        if len(grupo) < 2:
            continue
        temas_en_grupo = {k.split("#")[0] for k, _ in grupo}
        if len(temas_en_grupo) < 2:
            continue
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                if grupo[i][0].split("#")[0] == grupo[j][0].split("#")[0]:
                    continue
                m = motivo_duplicado(grupo[i][1], grupo[j][1])
                if m:
                    pares_global.append((grupo[i][0], grupo[j][0], m))

    return {
        "total": total,
        "temas": len(plantillas),
        "pares_intra_tema": sum(len(v) for v in pares_por_tema.values()),
        "pares_global": pares_global,
        "detalle_tema": pares_por_tema,
    }


def revisar_cruce() -> list[tuple[str, str, str]]:
    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)

    por_bucket: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for f in filas:
        por_bucket[_bucket_key(f)].append((f"Id {f.get('Id', '?')}", f))
    for tema, lst in plantillas.items():
        for i, t in enumerate(lst):
            fila = {"Pregunta": t.get("pregunta", ""), **t}
            por_bucket[_bucket_key(fila)].append((f"{tema}#{i}", fila))

    cruce = []
    for grupo in por_bucket.values():
        ds = [(k, d) for k, d in grupo if k.startswith("Id ")]
        pl = [(k, d) for k, d in grupo if not k.startswith("Id ")]
        if not ds or not pl:
            continue
        for did, d in ds:
            for pid, p in pl:
                m = motivo_duplicado(d, p)
                if m:
                    cruce.append((did, pid, m))
    return cruce


def generar_reemplazo(
    tema: str,
    plantillas: dict,
    filas_restantes: list[dict],
    rng: random.Random,
) -> dict | None:
    templates = plantillas.get(tema, [])
    if not templates:
        return None

    orden = list(range(len(templates)))
    rng.shuffle(orden)

    for idx in orden:
        for cand in expandir_plantilla(templates[idx]):
            if not es_duplicado_de_alguna(cand, filas_restantes):
                return cand
    return None


def indices_duplicados_dataset(filas: list[dict]) -> list[int]:
    """Segunda y siguientes apariciones de cada grupo duplicado (por orden de Id)."""
    ordenadas = sorted(enumerate(filas), key=lambda t: int(t[1].get("Id") or 0))
    kept_by_eq: dict[str, list[dict]] = defaultdict(list)
    kept_by_bucket: dict[str, list[dict]] = defaultdict(list)
    dup_idx: list[int] = []

    for idx, fila in ordenadas:
        eq = clave_enunciado(fila)
        bk = _bucket_key(fila)
        candidatos: list[dict] = []
        if eq:
            candidatos.extend(kept_by_eq.get(eq, []))
        candidatos.extend(kept_by_bucket.get(bk, []))
        vistos: set[int] = set()
        uniq: list[dict] = []
        for c in candidatos:
            cid = id(c)
            if cid not in vistos:
                vistos.add(cid)
                uniq.append(c)
        if es_duplicado_de_alguna(fila, uniq):
            dup_idx.append(idx)
        else:
            if eq:
                kept_by_eq[eq].append(fila)
            kept_by_bucket[bk].append(fila)
    return dup_idx


def deduplicar_dataset(
    filas: list[dict],
    plantillas: dict,
    rng: random.Random,
    max_pasadas: int = 5,
) -> tuple[list[dict], int, int]:
    reemplazadas = 0
    sin_reemplazo = 0

    for _ in range(max_pasadas):
        dup = indices_duplicados_dataset(filas)
        if not dup:
            break

        for idx in sorted(dup):
            fila = filas[idx]
            materia = materia_de_fila(fila)
            otras = [f for i, f in enumerate(filas) if i != idx]
            reemplazo = generar_reemplazo(materia, plantillas, otras, rng)
            if reemplazo:
                filas[idx] = fila_pregunta(
                    id_=fila.get("Id", ""),
                    materia=materia,
                    dificultad=reemplazo["Dificultad"],
                    tipo=reemplazo["Tipo"],
                    pregunta=reemplazo["Pregunta"],
                    a=reemplazo["A"],
                    b=reemplazo["B"],
                    c=reemplazo["C"],
                    d=reemplazo["D"],
                    correcta=reemplazo["Correcta"],
                )
                reemplazadas += 1
            else:
                sin_reemplazo += 1
                break
        if sin_reemplazo:
            break

    return filas, reemplazadas, sin_reemplazo



def ejecutar_todo(inplace: bool = False, dry_run: bool = False, seed: int = 42) -> int:
    if not inplace and not dry_run:
        print("Indica inplace=True o dry_run=True")
        return 2

    rng = random.Random(seed)

    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)

    total_pl_before = sum(len(v) for v in plantillas.values())
    if dry_run:
        # En dry-run solo duplicados exactos (la dedup semántica es costosa).
        plantillas_limpias, ex_pl, sim_pl = deduplicar_plantillas_dict(
            plantillas, solo_exactas=True
        )
    else:
        plantillas_limpias, ex_pl, sim_pl = deduplicar_plantillas_dict(plantillas)
    total_pl_after = sum(len(v) for v in plantillas_limpias.values())

    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    filas_work = [dict(f) for f in filas]
    dup_antes = len(indices_duplicados_dataset(filas_work))
    if dry_run:
        filas_nuevas = filas_work
        reempl, sin_rep = 0, 0
        dup_despues = dup_antes
    else:
        filas_nuevas, reempl, sin_rep = deduplicar_dataset(
            filas_work, plantillas_limpias, rng
        )
        dup_despues = len(indices_duplicados_dataset(filas_nuevas))

    if dry_run:
        plantillas_sin_cruce = plantillas_limpias
        cruce_removed = 0
    else:
        plantillas_sin_cruce, cruce_removed = quitar_plantillas_presentes_en_dataset(
            plantillas_limpias, filas_nuevas
        )
    total_pl_final = sum(len(v) for v in plantillas_sin_cruce.values())

    print("=== Plantillas ===")
    print(f"  Antes: {total_pl_before} | Tras dedup interna: {total_pl_after}")
    print(f"  Eliminadas exactas: {ex_pl} | muy similares: {sim_pl}")
    if dry_run:
        print("  (dry-run: similares y cruce con dataset solo en --inplace)")
    print(f"  Quitadas por coincidir con el dataset: {cruce_removed}")
    print(f"  Total final plantillas: {total_pl_final}")

    print("=== Dataset ===")
    print(f"  Filas duplicadas detectadas: {dup_antes}")
    print(f"  Reemplazadas: {reempl}")
    if sin_rep:
        print(f"  AVISO: {sin_rep} sin reemplazo (revisar plantillas del tema)")
    print(f"  Duplicados restantes: {dup_despues}")

    if dup_despues:
        rest = indices_duplicados_dataset(filas_nuevas)
        for idx in rest[:5]:
            f = filas_nuevas[idx]
            print(f"    Id {f.get('Id')} Materia={materia_de_fila(f)}")

    if dry_run:
        return 0

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(plantillas_sin_cruce, f, ensure_ascii=False, indent=2)
        f.write("\n")

    guardar_filas_csv(fieldnames, filas_nuevas, PATH_PREGUNTAS)

    if ejecutar_reordenar(solo_metadatos=True) != 0:
        return 1
    rc_val = ejecutar_validar()
    if rc_val != 0:
        return rc_val
    return 1 if dup_despues else 0



def ejecutar_plantillas() -> int:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        plantillas = json.load(f)

    total_before = sum(len(v) for v in plantillas.values())
    cleaned, exact_removed, similar_removed = deduplicar_plantillas_dict(plantillas)
    total_after = sum(len(v) for v in cleaned.values())

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Total antes: {total_before}")
    print(f"Total despues: {total_after}")
    print(f"Eliminadas exactas: {exact_removed}")
    print(f"Eliminadas muy similares: {similar_removed}")
    return 0


def _cargar_plantillas_exacto() -> dict:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        return json.load(f)



def ejecutar_exacto() -> int:
    plantillas = _cargar_plantillas_exacto()

    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    clave_a_indices = {}
    for idx, fila in enumerate(filas):
        clave = (fila["Pregunta"], fila["A"], fila["B"], fila["C"], fila["D"])
        clave_a_indices.setdefault(clave, []).append(idx)

    indices_a_reemplazar = []
    for clave, indices in clave_a_indices.items():
        if len(indices) > 1:
            indices_a_reemplazar.extend(indices[1:])

    if not indices_a_reemplazar:
        print("No hay preguntas duplicadas.")
        return 0

    claves_existentes = set()
    for idx, fila in enumerate(filas):
        if idx not in indices_a_reemplazar:
            clave = (fila["Pregunta"], fila["A"], fila["B"], fila["C"], fila["D"])
            claves_existentes.add(clave)

    reemplazadas = 0
    eliminadas = 0

    for idx in sorted(indices_a_reemplazar):
        fila = filas[idx]
        materia = (fila.get("Materia") or fila.get("Tema") or "").strip()
        reemplazo = _generar_reemplazo_exacto(materia, plantillas, claves_existentes)
        if reemplazo:
            filas[idx] = fila_pregunta(
                id_=fila["Id"],
                materia=materia,
                dificultad=reemplazo["Dificultad"],
                tipo=reemplazo["Tipo"],
                pregunta=reemplazo["Pregunta"],
                a=reemplazo["A"],
                b=reemplazo["B"],
                c=reemplazo["C"],
                d=reemplazo["D"],
                correcta=reemplazo["Correcta"],
            )
            clave_nueva = (
                reemplazo["Pregunta"],
                reemplazo["A"],
                reemplazo["B"],
                reemplazo["C"],
                reemplazo["D"],
            )
            claves_existentes.add(clave_nueva)
            reemplazadas += 1
        else:
            filas[idx] = None
            eliminadas += 1

    filas = [f for f in filas if f is not None]
    filas = ordenar_filas_por_tema_y_id(filas)
    renumerar_ids(filas)
    guardar_filas_csv(list(fieldnames or []), filas, PATH_PREGUNTAS)

    print(f"Duplicados procesados: {len(indices_a_reemplazar)}")
    print(f"  Reemplazados por preguntas nuevas: {reemplazadas}")
    if eliminadas > 0:
        print(f"  Eliminados (sin plantilla de reemplazo): {eliminadas}")
    print(f"Total final: {len(filas)} preguntas")
    return 0


def _generar_reemplazo_exacto(tema, plantillas, claves_existentes):
    templates = plantillas.get(tema, [])
    if not templates:
        return None
    orden = list(range(len(templates)))
    random.shuffle(orden)
    for idx in orden:
        for n in expandir_plantilla(templates[idx]):
            clave = (n["Pregunta"], n["A"], n["B"], n["C"], n["D"])
            if clave not in claves_existentes:
                return {**n, "Materia": tema}
    return None


def normalizar_enunciado(texto: str) -> str:
    return normalizar_basico(texto)


def ejecutar_enunciado(inplace: bool = False, output: str | None = None, seed: int = 42) -> int:
    random.seed(seed)
    plantillas = _cargar_plantillas_enunciado()

    with PATH_PREGUNTAS.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    if not fieldnames:
        raise ValueError("No se encontraron columnas en Data/Preguntas.csv")

    enunciado_a_indices: dict[str, list[int]] = defaultdict(list)
    for idx, fila in enumerate(filas):
        enunciado_a_indices[normalizar_enunciado(fila.get("Pregunta", ""))].append(idx)

    indices_a_reemplazar = []
    for _, indices in enunciado_a_indices.items():
        if len(indices) > 1:
            indices_a_reemplazar.extend(indices[1:])

    if not indices_a_reemplazar:
        print("No hay duplicados por enunciado.")
        return 0

    enunciados_existentes = set()
    bloques_existentes = set()
    for idx, fila in enumerate(filas):
        if idx in indices_a_reemplazar:
            continue
        enunciados_existentes.add(normalizar_enunciado(fila.get("Pregunta", "")))
        bloques_existentes.add(
            (
                (fila.get("Pregunta") or "").strip(),
                (fila.get("A") or "").strip(),
                (fila.get("B") or "").strip(),
                (fila.get("C") or "").strip(),
                (fila.get("D") or "").strip(),
            )
        )

    reemplazadas = 0
    eliminadas = 0

    for idx in sorted(indices_a_reemplazar):
        fila = filas[idx]
        materia = (fila.get("Materia") or fila.get("Tema") or "").strip()
        reemplazo = generar_reemplazo_enunciado(
            materia, plantillas, enunciados_existentes, bloques_existentes
        )
        if reemplazo:
            filas[idx] = fila_pregunta(
                id_=fila.get("Id", ""),
                materia=materia,
                dificultad=reemplazo["Dificultad"],
                tipo=reemplazo["Tipo"],
                pregunta=reemplazo["Pregunta"],
                a=reemplazo["A"],
                b=reemplazo["B"],
                c=reemplazo["C"],
                d=reemplazo["D"],
                correcta=reemplazo["Correcta"],
            )
            enunciados_existentes.add(normalizar_enunciado(reemplazo["Pregunta"]))
            bloques_existentes.add(
                (
                    reemplazo["Pregunta"].strip(),
                    reemplazo["A"].strip(),
                    reemplazo["B"].strip(),
                    reemplazo["C"].strip(),
                    reemplazo["D"].strip(),
                )
            )
            reemplazadas += 1
        else:
            filas[idx] = None
            eliminadas += 1

    filas = [f for f in filas if f is not None]
    filas = ordenar_filas_por_tema_y_id(filas)
    renumerar_ids(filas)

    out_path = PATH_PREGUNTAS if inplace else (BASE / (output or "Data/Preguntas_sin_duplicados_enunciado.csv"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    guardar_filas_csv(fieldnames, filas, out_path)

    print(f"Duplicados por enunciado detectados: {len(indices_a_reemplazar)}")
    print(f"  Reemplazados: {reemplazadas}")
    if eliminadas:
        print(f"  Eliminados sin reemplazo: {eliminadas}")
    print(f"Total final: {len(filas)}")
    print(f"Escrito en: {out_path}")
    return 0


def _cargar_plantillas_enunciado() -> dict[str, list[dict]]:
    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        return json.load(f)


def generar_reemplazo_enunciado(
    tema: str,
    plantillas: dict[str, list[dict]],
    enunciados_existentes: set[str],
    bloques_existentes: set[tuple[str, str, str, str, str]],
) -> dict | None:
    templates = plantillas.get(tema, [])
    if not templates:
        return None
    orden = list(range(len(templates)))
    random.shuffle(orden)
    for idx in orden:
        for cand in expandir_plantilla(templates[idx]):
            enunciado_norm = normalizar_enunciado(cand["Pregunta"])
            bloque = (
                cand["Pregunta"].strip(),
                cand["A"].strip(),
                cand["B"].strip(),
                cand["C"].strip(),
                cand["D"].strip(),
            )
            if enunciado_norm in enunciados_existentes:
                continue
            if bloque in bloques_existentes:
                continue
            return cand
    return None


def ejecutar_revisar() -> int:
    ds = revisar_dataset()
    pl = revisar_plantillas()
    cruce = revisar_cruce()

    _safe_print("=== DATASET (Preguntas.csv) ===")
    _safe_print(f"Filas: {ds['total']}")
    _safe_print(f"Pares duplicados/similares: {len(ds['pares'])}")
    if ds["enunciados_repetidos"]:
        _safe_print(f"Enunciados normalizados repetidos: {len(ds['enunciados_repetidos'])}")
    for a, b, m in ds["pares"][:30]:
        _safe_print(f"  Id {a} <-> Id {b} [{m}]")

    _safe_print("\n=== PLANTILLAS ===")
    _safe_print(f"Entradas: {pl['total']} en {pl['temas']} temas")
    _safe_print(f"Pares similares dentro del mismo tema: {pl['pares_intra_tema']}")
    _safe_print(f"Pares similares entre temas distintos: {len(pl['pares_global'])}")
    for tema, pares in sorted(pl["detalle_tema"].items(), key=lambda x: -len(x[1]))[:5]:
        _safe_print(f"  {tema}: {len(pares)} pares")
    for a, b, m in pl["pares_global"][:15]:
        _safe_print(f"  {a} <-> {b} [{m}]")

    _safe_print("\n=== CRUCE dataset ↔ plantillas ===")
    _safe_print(f"Coincidencias (informativo; el pool puede repetir el banco): {len(cruce)}")
    for a, b, m in cruce[:10]:
        _safe_print(f"  {a} <-> {b} [{m}]")

    if cruce:
        _safe_print(
            f"\n[CRUCE] {len(cruce)} plantillas coinciden con filas del dataset "
            "(quitar del pool con: python Files/duplicados.py todo --inplace)"
        )

    if ds["pares"] or pl["pares_intra_tema"] or pl["pares_global"] or cruce:
        _safe_print("\nEjecuta: python Files/duplicados.py todo --inplace")
        return 1
    _safe_print("\nOK: no se detectan duplicados con los criterios actuales.")
    return 0
