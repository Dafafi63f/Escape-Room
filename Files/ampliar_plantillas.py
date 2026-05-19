#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amplía y equilibra Data/plantillas.json por materia.

1. Fusiona plantillas actuales + origin/main (sin dataset_400 ni copias del CSV).
2. Rellena hasta --objetivo con variaciones materializadas, permutaciones y mutaciones numéricas.
3. Dedup solo exacta global + quitar solapamiento semántico con el dataset activo.

Uso:
  python Files/ampliar_plantillas.py --inplace
  python Files/ampliar_plantillas.py --dry-run
  python Files/ampliar_plantillas.py --objetivo 22
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from borrar_pycache import borrar_pycache_en_proyecto
from objetivos_balanceo import plantillas_minimas_por_materia
from utils_deduplicacion import (
    clave_bloque_exacto,
    clave_enunciado,
    clave_plantilla_exacta,
    deduplicar_plantillas_dict,
    quitar_plantillas_presentes_en_dataset,
)
from utils_dataset_csv import materia_de_fila
from utils_orden_temas import cargar_orden_temas

BASE = Path(__file__).resolve().parent.parent
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
GIT_PLANTILLAS_REF = "origin/main:Data/plantillas.json"
_RE_ENTEROS = re.compile(r"\b(\d+)\b")
_USO_PRIORITY = {"general": 0, "dificil": 1, "calculo": 2, "ampliado_var": 3, "ampliado_perm": 4, "ampliado_num": 5}


class IndicePool:
    def __init__(self, filas_dataset: list[dict]) -> None:
        self._enunciados: set[str] = set()
        self._bloques: set[tuple] = set()
        self._por_tema: dict[str, list[dict]] = defaultdict(list)
        for r in filas_dataset:
            comp = {"Pregunta": r.get("Pregunta", ""), **r}
            self._enunciados.add(clave_enunciado(comp))
            self._bloques.add(clave_bloque_exacto(comp))
            self._por_tema[materia_de_fila(r)].append(comp)

    def puede_anadir(self, tema: str, t: dict) -> bool:
        comp = {"Pregunta": t.get("pregunta", ""), **t}
        if clave_enunciado(comp) in self._enunciados:
            return False
        if clave_bloque_exacto(comp) in self._bloques:
            return False
        return True

    def registrar(self, tema: str, t: dict) -> None:
        comp = {"Pregunta": t.get("pregunta", ""), **t}
        self._enunciados.add(clave_enunciado(comp))
        self._bloques.add(clave_bloque_exacto(comp))
        self._por_tema[tema].append(comp)


def _expandir_plantilla(t: dict) -> list[dict]:
    out = []
    if t.get("variaciones"):
        for var in t["variaciones"]:
            p, a, b, c, d = t["pregunta"], t["A"], t["B"], t["C"], t["D"]
            for key, val in var.items():
                ph = "{" + str(key) + "}"
                p, a, b, c, d = (
                    p.replace(ph, str(val)),
                    a.replace(ph, str(val)),
                    b.replace(ph, str(val)),
                    c.replace(ph, str(val)),
                    d.replace(ph, str(val)),
                )
            out.append(
                {
                    "pregunta": p,
                    "A": a,
                    "B": b,
                    "C": c,
                    "D": d,
                    "correcta": t["correcta"],
                    "dificultad": t.get("dificultad", "Media"),
                    "tipo": t.get("tipo", "Teoria"),
                }
            )
    else:
        out.append(
            {
                "pregunta": t["pregunta"],
                "A": t["A"],
                "B": t["B"],
                "C": t["C"],
                "D": t["D"],
                "correcta": t["correcta"],
                "dificultad": t.get("dificultad", "Media"),
                "tipo": t.get("tipo", "Teoria"),
            }
        )
    return out


def cargar_git_plantillas() -> dict:
    try:
        raw = subprocess.check_output(
            ["git", "show", GIT_PLANTILLAS_REF],
            cwd=BASE,
            text=True,
            encoding="utf-8",
        )
        return json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return {}


def fusionar_fuentes(
    tema: str,
    actual: list[dict],
    git: list[dict],
    indice: IndicePool,
) -> list[dict]:
    """Une actual + git; solo dedup exacta y sin copiar el banco activo."""
    vistos: set[tuple] = set()
    resultado: list[dict] = []

    def intentar_anadir(t: dict) -> None:
        if str(t.get("uso", "")).lower() == "dataset_400":
            return
        k = clave_plantilla_exacta(t)
        if k in vistos:
            return
        if not indice.puede_anadir(tema, t):
            return
        vistos.add(k)
        resultado.append(copy.deepcopy(t))
        indice.registrar(tema, t)

    for fuente in (actual, git):
        ordenada = sorted(
            fuente,
            key=lambda x: _USO_PRIORITY.get(str(x.get("uso", "")).lower(), 9),
        )
        for t in ordenada:
            intentar_anadir(t)

    return resultado


def materializar_variaciones(
    items: list[dict], indice: IndicePool, tema: str
) -> list[dict]:
    nuevas = []
    for base in items:
        if not base.get("variaciones"):
            continue
        for exp in _expandir_plantilla(base):
            t = {
                **exp,
                "dificultad": exp.get("dificultad", base.get("dificultad", "Media")),
                "tipo": exp.get("tipo", base.get("tipo", "Teoria")),
                "uso": "ampliado_var",
            }
            if indice.puede_anadir(tema, t):
                nuevas.append(t)
                indice.registrar(tema, t)
    return nuevas


def permutar_opciones(
    base: dict, indice: IndicePool, tema: str, rng: random.Random
) -> list[dict]:
    letras = ["A", "B", "C", "D"]
    correcta = (base.get("correcta") or "A").strip().upper()
    if correcta not in letras:
        return []
    texto_ok = base[correcta]
    opciones = [base[x] for x in letras]
    out = []
    for _ in range(12):
        perm = opciones[:]
        rng.shuffle(perm)
        if perm == opciones:
            continue
        nueva_letra = None
        t = copy.deepcopy(base)
        for i, letra in enumerate(letras):
            t[letra] = perm[i]
            if perm[i] == texto_ok:
                nueva_letra = letra
        if not nueva_letra:
            continue
        t["correcta"] = nueva_letra
        t["uso"] = "ampliado_perm"
        if indice.puede_anadir(tema, t):
            out.append(t)
            indice.registrar(tema, t)
            break
    return out


def mutar_enteros(base: dict, indice: IndicePool, tema: str) -> list[dict]:
    out = []
    nums = set()
    for campo in ("pregunta", "A", "B", "C", "D"):
        nums.update(int(m.group(1)) for m in _RE_ENTEROS.finditer(base.get(campo, "")))
    for n in sorted(nums):
        for delta in (1, 2, -1):
            nuevo = n + delta
            if nuevo < 0:
                continue
            t = copy.deepcopy(base)
            ok = False
            for campo in ("pregunta", "A", "B", "C", "D"):
                tx, c = _RE_ENTEROS.subn(
                    lambda m, _n=n, _v=nuevo: str(_v) if int(m.group(1)) == _n else m.group(0),
                    t.get(campo, ""),
                )
                if c:
                    t[campo] = tx
                    ok = True
            if not ok:
                continue
            t["uso"] = "ampliado_num"
            if indice.puede_anadir(tema, t):
                out.append(t)
                indice.registrar(tema, t)
                return out
    return out


def rellenar_hasta(
    tema: str,
    items: list[dict],
    indice: IndicePool,
    objetivo: int,
    rng: random.Random,
) -> list[dict]:
    resultado = list(items)
    resultado.extend(materializar_variaciones(resultado, indice, tema))

    bases = [t for t in resultado if not t.get("variaciones")]
    intentos = 0
    max_intentos = 800 if objetivo >= 22 else 400
    while len(resultado) < objetivo and bases and intentos < max_intentos:
        intentos += 1
        base = bases[intentos % len(bases)]
        for cand in permutar_opciones(base, indice, tema, rng):
            resultado.append(cand)
            if len(resultado) >= objetivo:
                return resultado
        # No generar mutaciones numéricas: se consideran duplicados (misma plantilla).
    return resultado


def equilibrar_uso(items: list[dict], objetivo: int) -> list[dict]:
    """Intenta acercar el reparto general/dificil/calculo si hay margen."""
    if len(items) <= objetivo:
        return items
    por_uso: dict[str, list[dict]] = defaultdict(list)
    for t in items:
        u = str(t.get("uso", "general")).lower()
        if u.startswith("ampliado"):
            u = "calculo" if t.get("tipo") == "Calculo" else "general"
        por_uso[u].append(t)
    meta = max(1, objetivo // 3)
    orden = sorted(items, key=lambda x: _USO_PRIORITY.get(str(x.get("uso", "")).lower(), 9))
    elegidas: list[dict] = []
    conteos: Counter = Counter()
    for t in orden:
        u = str(t.get("uso", "general")).lower()
        if u.startswith("ampliado"):
            u = "calculo" if t.get("tipo") == "Calculo" else "general"
        if conteos[u] >= meta + 2:
            continue
        elegidas.append(t)
        conteos[u] += 1
        if len(elegidas) >= objetivo:
            break
    if len(elegidas) < objetivo:
        for t in orden:
            if t not in elegidas:
                elegidas.append(t)
            if len(elegidas) >= objetivo:
                break
    return elegidas[: max(objetivo, len(elegidas))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--objetivo", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.inplace and not args.dry_run:
        print("Indica --inplace o --dry-run")
        sys.exit(2)

    rng = random.Random(args.seed)
    minimo = plantillas_minimas_por_materia()
    objetivo = args.objetivo or minimo
    temas, _ = cargar_orden_temas()

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        actual = json.load(f)
    with PATH_PREGUNTAS.open(encoding="utf-8", newline="") as f:
        filas_ds = list(csv.DictReader(f, delimiter=";"))

    git = cargar_git_plantillas()
    indice = IndicePool(filas_ds)

    total_antes = sum(len(actual.get(t, [])) for t in temas)
    ampliadas: dict[str, list[dict]] = {}
    stats: Counter = Counter()

    for tema in temas:
        fusion = fusionar_fuentes(tema, actual.get(tema, []), git.get(tema, []), indice)
        antes = len(fusion)
        meta_tema = objetivo
        fusion = rellenar_hasta(tema, fusion, indice, meta_tema, rng)
        if len(fusion) < minimo:
            fusion = rellenar_hasta(tema, fusion, indice, minimo + 2, rng)
        stats["fusion_git"] += max(0, antes - len(actual.get(tema, [])))
        stats["generadas"] += max(0, len(fusion) - antes)
        if len(fusion) > objetivo + 4:
            fusion = equilibrar_uso(fusion, objetivo + 2)
        ampliadas[tema] = fusion

    total_tras = sum(len(ampliadas.get(t, [])) for t in temas)

    ampliadas, ex, _ = deduplicar_plantillas_dict(ampliadas, solo_exactas=True)
    ampliadas, cruce = quitar_plantillas_presentes_en_dataset(ampliadas, filas_ds)
    total_final = sum(len(ampliadas.get(t, [])) for t in temas)
    counts = [len(ampliadas.get(t, [])) for t in temas]

    print(f"Objetivo por materia: {objetivo}")
    print(f"Antes: {total_antes} | tras fusion+generar: {total_tras} | final: {total_final}")
    print(f"Estadísticas: {dict(stats)} | dedup exacta={ex} | quitadas vs dataset={cruce}")
    print(f"Por materia: min={min(counts)} max={max(counts)} media={sum(counts)/len(counts):.1f}")

    bajo = [(t, len(ampliadas.get(t, []))) for t in temas if len(ampliadas.get(t, [])) < minimo]
    if bajo:
        print(f"Materias bajo mínimo ({minimo}): {len(bajo)}")
        for t, n in sorted(bajo, key=lambda x: x[1])[:12]:
            print(f"  - {t}: {n}")

    if args.dry_run:
        return

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(ampliadas, f, ensure_ascii=False, indent=2)
        f.write("\n")

    subprocess.run([sys.executable, "Files/duplicados.py", "revisar"], cwd=BASE, check=False)
    subprocess.run([sys.executable, "Files/revisar_plantillas.py"], cwd=BASE, check=False)


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
