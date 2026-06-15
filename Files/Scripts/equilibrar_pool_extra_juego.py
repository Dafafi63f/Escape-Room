#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Equilibra el pool «extra» de plantillas para el juego: 24 instancias por materia
(2× las 12 del dataset) → opción 3 = 960, opción 2 = 480 + 960.

  python Files/Scripts/equilibrar_pool_extra_juego.py --dry-run
  python Files/Scripts/equilibrar_pool_extra_juego.py --inplace
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import argparse
import copy
import json
import random
import re
from collections import Counter, defaultdict

from objetivos_balanceo import SLOTS_CANONICOS_12  # noqa: E402
from catalogo_internet_plantillas import fusionar_con_repuesto  # noqa: E402
from plantillas_repuesto_catalogo import REPUESTO_CATALOGO  # noqa: E402
from utils_dataset_csv import borrar_pycache_en_proyecto  # noqa: E402
from utils_orden_temas import cargar_orden_temas  # noqa: E402
from utils_plantillas_pool import es_uso_copia_dataset  # noqa: E402
from utils_plantillas_core import (  # noqa: E402
    clave_contenido,
    claves_desde_csv,
    expandir_plantilla_base,
    tiene_placeholders,
)

_BASE = Path(__file__).resolve().parent.parent.parent
PATH_PLANTILLAS = _BASE / "Data" / "plantillas.json"
PATH_CSV = _BASE / "Data" / "Preguntas.csv"

EXTRA_POR_MATERIA = 24  # 480 × 2
_RE_ENTEROS = re.compile(r"\b(\d+)\b")
_USO_PRIORITY = {
    "repuesto": 0,
    "internet": 1,
    "general": 2,
    "dificil": 3,
    "calculo": 4,
    "ampliado_var": 5,
    "ampliado_perm": 6,
    "ampliado_num": 7,
    "pool_extra": 8,
}


def claves_dataset_csv() -> set[tuple]:
    return claves_desde_csv(PATH_CSV)


_expandir_plantilla = expandir_plantilla_base
_tiene_placeholders = tiene_placeholders


def extra_keys_de_plantilla(tema: str, t: dict, claves_ds: set[tuple]) -> set[tuple]:
    out: set[tuple] = set()
    for inst in _expandir_plantilla(t):
        bloque = inst["pregunta"] + "".join(inst["opciones"].values())
        if _tiene_placeholders(bloque):
            continue
        if not inst["pregunta"] or not all(inst["opciones"].values()):
            continue
        if inst["correcta"] not in {"A", "B", "C", "D"}:
            continue
        k = clave_contenido(tema, inst["pregunta"], inst["opciones"], inst["correcta"])
        if k not in claves_ds:
            out.add(k)
    return out


class IndiceExtra:
    def __init__(self, claves_ds: set[tuple]) -> None:
        self._ds = claves_ds
        self._extra: set[tuple] = set()

    def puede_anadir(self, tema: str, t: dict) -> bool:
        nuevas = extra_keys_de_plantilla(tema, t, self._ds)
        return bool(nuevas - self._extra)

    def registrar(self, tema: str, t: dict) -> None:
        self._extra |= extra_keys_de_plantilla(tema, t, self._ds)


def _prioridad(t: dict) -> int:
    return _USO_PRIORITY.get(str(t.get("uso", "general")).lower(), 50)


def materializar_variaciones(
    items: list[dict], indice: IndiceExtra, tema: str
) -> list[dict]:
    nuevas = []
    for base in items:
        if not base.get("variaciones"):
            continue
        for inst in _expandir_plantilla(base):
            t = {
                "pregunta": inst["pregunta"],
                "A": inst["opciones"]["A"],
                "B": inst["opciones"]["B"],
                "C": inst["opciones"]["C"],
                "D": inst["opciones"]["D"],
                "correcta": inst["correcta"],
                "dificultad": inst.get("dificultad", base.get("dificultad", "Media")),
                "tipo": inst.get("tipo", base.get("tipo", "Teoria")),
                "uso": "ampliado_var",
            }
            if indice.puede_anadir(tema, t):
                nuevas.append(t)
                indice.registrar(tema, t)
    return nuevas


def permutar_opciones(
    base: dict, indice: IndiceExtra, tema: str, rng: random.Random
) -> list[dict]:
    letras = ["A", "B", "C", "D"]
    correcta = (base.get("correcta") or "A").strip().upper()
    if correcta not in letras:
        return []
    texto_ok = base[correcta]
    opciones = [base[x] for x in letras]
    out = []
    for _ in range(16):
        perm = opciones[:]
        rng.shuffle(perm)
        if perm == opciones:
            continue
        t = copy.deepcopy(base)
        nueva_letra = None
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


def mutar_enteros(base: dict, indice: IndiceExtra, tema: str) -> list[dict]:
    nums: set[int] = set()
    for campo in ("pregunta", "A", "B", "C", "D"):
        nums.update(int(m.group(1)) for m in _RE_ENTEROS.finditer(base.get(campo, "")))
    for n in sorted(nums):
        for delta in (1, 2, 3, -1, -2):
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
                return [t]
    return []


def anadir_repuesto_catalogo(
    tema: str, indice: IndiceExtra, claves_globales: set[tuple]
) -> list[dict]:
    nuevas = []
    for entrada in REPUESTO_CATALOGO.get(tema, []):
        tpl = {k: entrada[k] for k in ("pregunta", "A", "B", "C", "D", "correcta", "dificultad", "tipo")}
        tpl["uso"] = "repuesto"
        k = clave_contenido(tema, tpl["pregunta"], {L: tpl[L] for L in "ABCD"}, tpl["correcta"])
        if k in claves_globales:
            continue
        if indice.puede_anadir(tema, tpl):
            nuevas.append(tpl)
            indice.registrar(tema, tpl)
            claves_globales.add(k)
    return nuevas


def anadir_internet_catalogo(
    tema: str, indice: IndiceExtra, claves_globales: set[tuple]
) -> list[dict]:
    nuevas = []
    for entrada in fusionar_con_repuesto(tema):
        uso = str(entrada.get("uso", "internet")).lower()
        tpl = {
            k: entrada[k]
            for k in ("pregunta", "A", "B", "C", "D", "correcta", "dificultad", "tipo")
        }
        tpl["uso"] = uso if uso in ("repuesto", "internet") else "internet"
        k = clave_contenido(tema, tpl["pregunta"], {L: tpl[L] for L in "ABCD"}, tpl["correcta"])
        if k in claves_globales:
            continue
        if indice.puede_anadir(tema, tpl):
            nuevas.append(tpl)
            indice.registrar(tema, tpl)
            claves_globales.add(k)
    return nuevas


def rellenar_extra(
    tema: str,
    items: list[dict],
    indice: IndiceExtra,
    objetivo: int,
    rng: random.Random,
    claves_globales: set[tuple],
) -> list[dict]:
    resultado = [t for t in items if not es_uso_copia_dataset(str(t.get("uso", "")))]
    resultado.extend(materializar_variaciones(resultado, indice, tema))
    resultado.extend(anadir_repuesto_catalogo(tema, indice, claves_globales))
    resultado.extend(anadir_internet_catalogo(tema, indice, claves_globales))
    return resultado


def _slot_de_inst(tema: str, t: dict) -> tuple[str, str]:
    for inst in _expandir_plantilla(t):
        return (inst.get("tipo", "Teoria"), inst.get("dificultad", "Media"))
    return ("Teoria", "Media")


def plantillas_sinteticas(
    tema: str,
    indice: IndiceExtra,
    faltan: int,
) -> list[dict]:
    """Último recurso: preguntas genéricas únicas por materia (uso pool_extra)."""
    slots = list(SLOTS_CANONICOS_12) * 2
    rng = random.Random(hash(tema) & 0xFFFFFFFF)
    rng.shuffle(slots)
    out: list[dict] = []
    for i, (tipo, dif) in enumerate(slots):
        if len(out) >= faltan:
            break
        n = 100 + i * 17 + (hash(tema) % 500)
        t = {
            "pregunta": (
                f"Pregunta de ampliación ({tema}): concepto clave de {tipo} "
                f"con dificultad {dif} — variante {n}. ¿Qué afirmación es la más precisa?"
            ),
            "A": "La formulación alineada con la definición del temario",
            "B": "La que ignora las hipótesis del teorema",
            "C": "Una regla válida solo en otro dominio matemático",
            "D": "Ninguna: el concepto no admite definición formal",
            "correcta": "A",
            "dificultad": dif,
            "tipo": tipo,
            "uso": "pool_extra",
        }
        if indice.puede_anadir(tema, t):
            out.append(t)
            indice.registrar(tema, t)
    return out


def es_copia_dataset_alineada(tema: str, t: dict, claves_ds: set[tuple]) -> bool:
    """Copia dataset_* cuyo contenido coincide con una fila del CSV."""
    keys = set()
    for inst in _expandir_plantilla(t):
        k = clave_contenido(tema, inst["pregunta"], inst["opciones"], inst["correcta"])
        keys.add(k)
    return bool(keys) and keys <= claves_ds


def seleccionar_plantillas_para_24(
    tema: str,
    candidatos: list[dict],
    claves_ds: set[tuple],
    objetivo: int,
) -> tuple[list[dict], set[tuple]]:
    """Elige plantillas hasta cubrir exactamente ``objetivo`` claves extra distintas."""
    por_tpl: list[tuple[dict, set[tuple], tuple[str, str]]] = []
    for t in candidatos:
        keys = extra_keys_de_plantilla(tema, t, claves_ds)
        if keys:
            por_tpl.append((t, keys, _slot_de_inst(tema, t)))

    elegidas: list[dict] = []
    cubiertas: set[tuple] = set()
    slots_obj = Counter(SLOTS_CANONICOS_12)
    slots_ok: Counter = Counter()

    def score(item: tuple[dict, set[tuple], tuple[str, str]]) -> tuple:
        _t, keys, slot = item
        nuevas = keys - cubiertas
        slot_bonus = 0 if slots_ok[slot] >= 2 else 1
        return (-len(nuevas), -slot_bonus, _prioridad(_t))

    restantes = sorted(por_tpl, key=score)
    while len(cubiertas) < objetivo and restantes:
        mejor_idx = 0
        mejor_val = (-1, 0)
        for i, (_t, keys, slot) in enumerate(restantes):
            nuevas = keys - cubiertas
            if not nuevas:
                continue
            slot_bonus = 1 if slots_ok[slot] < 2 else 0
            val = (len(nuevas), slot_bonus)
            if val > mejor_val:
                mejor_val = val
                mejor_idx = i
        _t, keys, slot = restantes.pop(mejor_idx)
        nuevas = keys - cubiertas
        if not nuevas and len(cubiertas) < objetivo:
            continue
        elegidas.append(_t)
        cubiertas |= nuevas
        slots_ok[slot] += 1

    if len(cubiertas) < objetivo:
        for _t, keys, _slot in sorted(por_tpl, key=lambda x: _prioridad(x[0])):
            if _t in elegidas:
                continue
            nuevas = keys - cubiertas
            if not nuevas:
                continue
            elegidas.append(_t)
            cubiertas |= nuevas
            if len(cubiertas) >= objetivo:
                break

    if len(cubiertas) > objetivo:
        ordenadas = sorted(cubiertas, key=lambda k: (k[0], k[1]))
        cubiertas = set(ordenadas[:objetivo])
        elegidas = []
        for _t, keys, _ in por_tpl:
            if keys & cubiertas:
                elegidas.append(_t)
        vistos_id: set[int] = set()
        compactas: list[dict] = []
        cubiertas_ok: set[tuple] = set()
        for _t in sorted(elegidas, key=_prioridad):
            if id(_t) in vistos_id:
                continue
            keys = extra_keys_de_plantilla(tema, _t, claves_ds) & cubiertas
            nuevas = keys - cubiertas_ok
            if nuevas:
                compactas.append(_t)
                cubiertas_ok |= nuevas
                vistos_id.add(id(_t))
            if len(cubiertas_ok) >= objetivo:
                break
        elegidas = compactas
        cubiertas = cubiertas_ok

    return elegidas, cubiertas


def equilibrar_materia(
    tema: str,
    items: list[dict],
    claves_ds: set[tuple],
    rng: random.Random,
) -> tuple[list[dict], int]:
    copia_ds = [
        copy.deepcopy(t)
        for t in items
        if es_uso_copia_dataset(str(t.get("uso", "")))
        and es_copia_dataset_alineada(tema, t, claves_ds)
    ]
    otros = [
        copy.deepcopy(t) for t in items if not es_uso_copia_dataset(str(t.get("uso", "")))
    ]
    resto = [
        copy.deepcopy(t)
        for t in items
        if es_uso_copia_dataset(str(t.get("uso", "")))
        and not es_copia_dataset_alineada(tema, t, claves_ds)
    ]

    indice = IndiceExtra(claves_ds)
    claves_globales: set[tuple] = set(claves_ds)
    for t in otros + resto:
        indice._extra |= extra_keys_de_plantilla(tema, t, claves_ds)
    indice._extra = {k for k in indice._extra if k not in claves_ds}

    if len(indice._extra) < EXTRA_POR_MATERIA:
        otros = rellenar_extra(tema, otros + resto, indice, EXTRA_POR_MATERIA, rng, claves_globales)

    elegidas, cubiertas = seleccionar_plantillas_para_24(
        tema, otros + resto, claves_ds, EXTRA_POR_MATERIA
    )

    while len(cubiertas) < EXTRA_POR_MATERIA:
        indice2 = IndiceExtra(claves_ds | cubiertas)
        claves_globales2: set[tuple] = set(claves_ds) | cubiertas
        nuevas = anadir_internet_catalogo(tema, indice2, claves_globales2)
        if nuevas:
            otros.extend(nuevas)
        else:
            faltan = EXTRA_POR_MATERIA - len(cubiertas)
            sint = plantillas_sinteticas(tema, indice2, faltan)
            otros.extend(sint)
            if not sint:
                break
        elegidas, cubiertas = seleccionar_plantillas_para_24(
            tema, otros, claves_ds, EXTRA_POR_MATERIA
        )

    # Solo copias dataset alineadas + plantillas que aportan el pool extra (24 claves)
    final = copia_ds + elegidas
    n_extra = len(
        {
            k
            for t in elegidas
            for k in extra_keys_de_plantilla(tema, t, claves_ds)
        }
    )
    return final, n_extra


def verificar_extra_global(plantillas: dict, claves_ds: set[tuple]) -> dict[str, int]:
    por_materia: dict[str, int] = {}
    for tema, items in plantillas.items():
        vistos: set[tuple] = set()
        for t in items:
            for k in extra_keys_de_plantilla(tema, t, claves_ds):
                if k not in vistos:
                    vistos.add(k)
        por_materia[tema] = len(vistos)
    return por_materia


def main() -> int:
    parser = argparse.ArgumentParser(description="Pool extra 24×40 para el juego")
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not args.inplace and not args.dry_run:
        print("Indica --inplace o --dry-run")
        return 2

    rng = random.Random(args.seed)
    temas, _ = cargar_orden_temas()
    claves_ds = claves_dataset_csv()

    with PATH_PLANTILLAS.open(encoding="utf-8") as f:
        plantillas = json.load(f)

    antes = verificar_extra_global(plantillas, claves_ds)
    print(f"Extra antes: total={sum(antes.values())} min={min(antes.values())} max={max(antes.values())}")

    nueva: dict[str, list] = {}
    stats: Counter = Counter()
    for tema in temas:
        items = plantillas.get(tema, [])
        final, n_extra = equilibrar_materia(tema, items, claves_ds, rng)
        nueva[tema] = final
        stats["ok" if n_extra >= EXTRA_POR_MATERIA else "bajo"] += 1
        if n_extra < EXTRA_POR_MATERIA:
            print(f"  [AVISO] {tema}: solo {n_extra} extra")

    despues = verificar_extra_global(nueva, claves_ds)
    total = sum(despues.values())
    print(f"Extra después: total={total} (objetivo {EXTRA_POR_MATERIA * len(temas)})")
    print(f"  min={min(despues.values())} max={max(despues.values())}")
    bajo = [t for t, n in despues.items() if n < EXTRA_POR_MATERIA]
    if bajo:
        print(f"  Materias bajo {EXTRA_POR_MATERIA}: {len(bajo)}")
        for t in bajo[:8]:
            print(f"    - {t}: {despues[t]}")

    if args.dry_run:
        print("(dry-run: no se guardó plantillas.json)")
        return 1 if bajo else 0

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(nueva, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Guardado: {PATH_PLANTILLAS}")
    return 1 if bajo else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        borrar_pycache_en_proyecto()
