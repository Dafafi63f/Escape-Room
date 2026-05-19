# -*- coding: utf-8 -*-
"""
Lógica de balance: validar, ajustar (regeneración desde plantillas), corregir (parches).

Por defecto `ejecutar_ajuste` borra filas mal encajadas y crea preguntas nuevas
con todos los campos coherentes. El modo `--intercambios` (solo etiquetas) queda
obsoleto y no debe usarse salvo pruebas.
"""

from __future__ import annotations

import csv
import io
import itertools
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from objetivos_balanceo import (
    TARGET_TOTAL_PREGUNTAS,
    objetivos_correcta_por_letra,
    objetivos_dificultad_por_totales,
    preguntas_por_materia,
    preguntas_por_tipo_global,
)
from utils_dataset_csv import COLUMNAS_PREGUNTAS, guardar_filas_csv, materia_de_fila
from utils_orden_temas import cargar_orden_temas
from utils_clasificacion_pregunta import comparar_con_asignacion
from utils_puntuacion_materia import MATERIA_TO_ID, MATERIAS, score_fila_para_materia

PATH_CSV = BASE / "Data" / "Preguntas.csv"
COLS = ["Id", "Materia", "Dificultad", "Tipo", "Pregunta", "A", "B", "C", "D", "Correcta"]
LETRAS_ORDEN = ("A", "B", "C", "D")


def ord_diff(k: object) -> int:
    return {"Facil": 0, "Media": 1, "Dificil": 2}.get(str(k).strip(), 99)


def target_fmd(bloque_idx: int) -> tuple[int, int, int]:
    if bloque_idx < 14:
        return (4, 3, 3)
    if bloque_idx < 27:
        return (3, 4, 3)
    return (3, 3, 4)


def labels_from_fmd(f: int, m: int, d: int) -> tuple[str, ...]:
    return tuple(["Facil"] * f + ["Media"] * m + ["Dificil"] * d)


def mejor_asignacion_dificultad(rows: list[dict], fmd: tuple[int, int, int]) -> list[str]:
    f, m, d = fmd
    base = labels_from_fmd(f, m, d)
    best: tuple[str, ...] | None = None
    best_cost = math.inf
    for perm in set(itertools.permutations(base)):
        cost = sum(1 for i, r in enumerate(rows) if str(r.get("Dificultad", "")).strip() != perm[i])
        if cost < best_cost or (cost == best_cost and best is not None and perm < tuple(best)):
            best_cost = cost
            best = perm
    assert best is not None
    return list(best)


def permutar_abcd_objetivo(row: dict, letra_objetivo: str) -> dict:
    letra_objetivo = letra_objetivo.strip().upper()
    opts = {L: str(row.get(L, "") or "") for L in LETRAS_ORDEN}
    old = str(row.get("Correcta", "") or "").strip().upper()
    if old not in opts:
        raise ValueError(f"Correcta inválida {old!r} en fila Id={row.get('Id')}")
    val_ok = opts[old]
    otras = [opts[L] for L in LETRAS_ORDEN if L != old]
    nuevo: dict[str, str] = {}
    idx = 0
    for L in LETRAS_ORDEN:
        if L == letra_objetivo:
            nuevo[L] = val_ok
        else:
            nuevo[L] = otras[idx]
            idx += 1
    out = dict(row)
    for L in LETRAS_ORDEN:
        out[L] = nuevo[L]
    out["Correcta"] = letra_objetivo
    return out


def comprobar_orden_canonico_df(df) -> list[str]:
    import pandas as pd

    errs: list[str] = []
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    temas, _ = cargar_orden_temas()
    if len(df) != 400:
        errs.append(f"Filas: se esperaban 400, hay {len(df)}")
    if set(df["Materia"].unique()) - set(temas):
        errs.append(f"Materias no listadas: {set(df['Materia'].unique()) - set(temas)}")
    if df["Tipo"].value_counts().get("Teoria", 0) != 200 or df["Tipo"].value_counts().get("Calculo", 0) != 200:
        errs.append("Tipos globales distintos de 200/200")
    dc = df["Dificultad"].value_counts()
    if dc.get("Facil", 0) != 134 or dc.get("Media", 0) != 133 or dc.get("Dificil", 0) != 133:
        errs.append(f"Dificultad global: {dc.to_dict()} (obj. 134/133/133)")
    for L in LETRAS_ORDEN:
        if df["Correcta"].value_counts().get(L, 0) != 100:
            errs.append(f"Correcta {L}: {df['Correcta'].value_counts().get(L, 0)} (obj. 100)")
    esp = df["Id"].astype(int).map(lambda x: LETRAS_ORDEN[(x - 1) % 4])
    corr = df["Correcta"].astype(str).str.strip().str.upper()
    bad_ciclo = df[corr != esp]
    if len(bad_ciclo):
        errs.append(f"Ciclo Correcta vs Id: {len(bad_ciclo)} filas (muestra Id {bad_ciclo['Id'].head(5).tolist()})")

    for bi, tema in enumerate(temas):
        sub = df[df["Materia"] == tema].copy()
        if len(sub) != 10:
            errs.append(f"{tema!r}: {len(sub)} filas (obj. 10)")
            continue
        sub["_ord"] = sub["Id"].astype(int)
        sub = sub.sort_values("_ord")
        tipos = sub["Tipo"].tolist()
        if tipos != ["Teoria"] * 5 + ["Calculo"] * 5:
            errs.append(f"{tema!r}: tipo no es TTTTTCCCCC: {tipos}")
        fmd = target_fmd(bi)
        vc = sub["Dificultad"].value_counts()
        if vc.get("Facil", 0) != fmd[0] or vc.get("Media", 0) != fmd[1] or vc.get("Dificil", 0) != fmd[2]:
            errs.append(f"{tema!r}: F/M/D bloque {vc.to_dict()} vs obj. {fmd}")
        difs_t = [ord_diff(x) for x in sub.iloc[:5]["Dificultad"]]
        for i in range(4):
            if difs_t[i] > difs_t[i + 1]:
                errs.append(f"{tema!r}: ladder Teoría roto en pos. {i}: {difs_t}")
                break
        difs_c = [ord_diff(x) for x in sub.iloc[5:10]["Dificultad"]]
        for i in range(4):
            if difs_c[i] > difs_c[i + 1]:
                errs.append(f"{tema!r}: ladder Cálculo roto en pos. {i}: {difs_c}")
                break
    return errs


def ejecutar_reordenar(
    solo_metadatos: bool = False,
    explicar: bool = False,
    sin_permutar_respuestas: bool = False,
) -> int:
    import pandas as pd

    if explicar:
        print(__doc__ if __doc__ else "Orden canónico: listado_materias + ladder TF..TD/CF..CD")
        return 0

    sin_permutar = sin_permutar_respuestas or solo_metadatos
    df = pd.read_csv(PATH_CSV, sep=";", encoding="utf-8")
    temas, _ = cargar_orden_temas()
    faltan = set(df["Materia"].unique()) - set(temas)
    if faltan:
        raise SystemExit(f"Materias no listadas: {faltan}")

    por_materia: dict[str, list[dict]] = {t: [] for t in temas}
    for _, r in df.iterrows():
        por_materia[str(r["Materia"]).strip()].append(r.to_dict())

    nuevas: list[dict] = []
    for bi, tema in enumerate(temas):
        bloque = por_materia[tema]
        if len(bloque) != 10:
            raise SystemExit(f"{tema!r}: se esperaban 10 filas, hay {len(bloque)}")
        teo = [x for x in bloque if str(x.get("Tipo", "")).strip() == "Teoria"]
        cal = [x for x in bloque if str(x.get("Tipo", "")).strip() == "Calculo"]
        if len(teo) != 5 or len(cal) != 5:
            raise SystemExit(f"{tema!r}: tipo {len(teo)} Teoria / {len(cal)} Calculo")
        teo.sort(key=lambda x: (ord_diff(x.get("Dificultad")), int(x["Id"])))
        cal.sort(key=lambda x: (ord_diff(x.get("Dificultad")), int(x["Id"])))
        ordenados = teo + cal
        fmd = target_fmd(bi)
        nuevas_difs = mejor_asignacion_dificultad(ordenados, fmd)
        bloque_filas: list[dict] = []
        for row, nd in zip(ordenados, nuevas_difs, strict=True):
            r = dict(row)
            r["Dificultad"] = nd
            bloque_filas.append(r)
        bloque_filas.sort(
            key=lambda r: (
                0 if str(r.get("Tipo", "")).strip() == "Teoria" else 1,
                ord_diff(r["Dificultad"]),
                int(r["Id"]),
            )
        )
        nuevas.extend(bloque_filas)

    assert len(nuevas) == 400
    for i, r in enumerate(nuevas, start=1):
        r["Id"] = str(i)
        if not sin_permutar:
            nuevas[i - 1] = permutar_abcd_objetivo(r, LETRAS_ORDEN[(i - 1) % 4])

    chk = pd.DataFrame(nuevas)
    errs = comprobar_orden_canonico_df(chk)
    if sin_permutar:
        errs = [e for e in errs if not e.startswith("Correcta ") and "Ciclo Correcta" not in e]
    if errs:
        raise SystemExit("Post-condición orden canónico:\n" + "\n".join(errs))

    guardar_filas_csv(list(COLUMNAS_PREGUNTAS), nuevas, PATH_CSV)
    modo = "solo metadatos" if solo_metadatos else ("sin permutar A-D" if sin_permutar else "ABCD cíclico")
    print(f"OK: orden canónico, Id 1..400 ({modo})")
    return 0


def validar(rows: list[dict], detalle: bool = False, estricto: bool = False) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    n = len(rows)
    tgt_m = preguntas_por_materia()
    tgt_tipo = preguntas_por_tipo_global()
    tgt_diff = objetivos_dificultad_por_totales(n)
    tgt_corr = objetivos_correcta_por_letra(n)
    temas, _ = cargar_orden_temas()

    if n != TARGET_TOTAL_PREGUNTAS:
        msgs.append(f"Total: {n} filas (objetivo {TARGET_TOTAL_PREGUNTAS})")

    por_materia = Counter(materia_de_fila(r) for r in rows)
    for t in temas:
        c = por_materia.get(t, 0)
        if c != tgt_m:
            msgs.append(f"Materia {t!r}: {c} preguntas (objetivo {tgt_m})")
            if detalle and c != tgt_m:
                msgs.append(f"  → {'déficit' if c < tgt_m else 'exceso'} de {abs(c - tgt_m)}")

    faltan_listado = set(por_materia) - set(temas)
    if faltan_listado:
        msgs.append(f"Materias en CSV no presentes en listado: {faltan_listado}")

    por_tipo = Counter(r["Tipo"] for r in rows)
    if por_tipo.get("Teoria", 0) != tgt_tipo or por_tipo.get("Calculo", 0) != tgt_tipo:
        msgs.append(
            f"Tipos globales: Teoria={por_tipo.get('Teoria', 0)}, "
            f"Calculo={por_tipo.get('Calculo', 0)} (objetivo {tgt_tipo}/{tgt_tipo})"
        )

    por_dificultad = Counter(r["Dificultad"] for r in rows)
    for d in ("Facil", "Media", "Dificil"):
        if por_dificultad.get(d, 0) != tgt_diff[d]:
            msgs.append(f"Dificultad {d}: {por_dificultad.get(d, 0)} (objetivo {tgt_diff[d]})")

    if estricto:
        por_correcta = Counter(r["Correcta"] for r in rows)
        for letra in ("A", "B", "C", "D"):
            if por_correcta.get(letra, 0) != tgt_corr[letra]:
                msgs.append(f"Correcta {letra}: {por_correcta.get(letra, 0)} (objetivo {tgt_corr[letra]})")

    if detalle:
        for bi, tema in enumerate(temas):
            sub = [r for r in rows if materia_de_fila(r) == tema]
            if len(sub) != 10:
                continue
            teo = sum(1 for r in sub if r["Tipo"] == "Teoria")
            cal = sum(1 for r in sub if r["Tipo"] == "Calculo")
            if teo != 5 or cal != 5:
                msgs.append(f"  {tema!r}: {teo} Teoria / {cal} Calculo (objetivo 5/5)")

        n_incoh = sum(1 for r in rows if comparar_con_asignacion(r).debe_sustituir)
        if n_incoh:
            msgs.append(
                f"  Clasificación contenido: {n_incoh} filas con Materia/Tipo/Dificultad "
                f"incoherentes (python Files/clasificar_pregunta.py --dataset --solo-incoherentes)"
            )

    import pandas as pd

    orden = comprobar_orden_canonico_df(pd.DataFrame(rows))
    for e in orden:
        if e not in msgs:
            if not estricto and ("Ciclo Correcta" in e or e.startswith("Correcta ")):
                continue
            msgs.append(f"Orden canónico: {e}")

    return len(msgs) == 0, msgs


def ejecutar_validar(detalle: bool = False, estricto: bool = False) -> int:
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    ok, msgs = validar(rows, detalle=detalle, estricto=estricto)
    if ok:
        print("OK: el dataset cumple todos los criterios de balance comprobados.")
        return 0

    print("Desviaciones respecto al objetivo:")
    for m in msgs:
        print(f"  - {m}")
    print(
        "\nSugerencia: python Files/balance.py conservador "
        "(regenera desde plantillas) o python Files/balance.py agresivo"
    )
    return 1


def _score_fila_materia(fila: dict, mat_id: int) -> float:
    materia = MATERIAS.get(mat_id, "")
    return score_fila_para_materia(fila, materia)


def intercambiar_materia(rows: list[dict], i: int, j: int) -> None:
    a, b = rows[i]["Materia"], rows[j]["Materia"]
    rows[i]["Materia"] = b
    rows[j]["Materia"] = a


def ajustar_conteos_materia(rows: list[dict], max_pasos: int = 200) -> int:
    """Intercambia Materia entre filas de materias con exceso y déficit."""
    temas, _ = cargar_orden_temas()
    tgt = preguntas_por_materia()
    cambios = 0

    for _ in range(max_pasos):
        por = Counter(materia_de_fila(r) for r in rows)
        exceso = [(t, por[t] - tgt) for t in temas if por.get(t, 0) > tgt]
        deficit = [(t, tgt - por.get(t, 0)) for t in temas if por.get(t, 0) < tgt]
        if not exceso or not deficit:
            break

        exceso.sort(key=lambda x: -x[1])
        deficit.sort(key=lambda x: -x[1])
        tema_exc, _ = exceso[0]
        tema_def, _ = deficit[0]
        id_exc = MATERIA_TO_ID[tema_exc]
        id_def = MATERIA_TO_ID[tema_def]

        idx_exc = [
            i for i, r in enumerate(rows) if materia_de_fila(r) == tema_exc
        ]
        idx_def = [i for i, r in enumerate(rows) if materia_de_fila(r) == tema_def]

        mejor_par = None
        mejor_ganancia = -1.0
        for i in idx_exc:
            for j in idx_def:
                antes = _score_fila_materia(rows[i], id_exc) + _score_fila_materia(rows[j], id_def)
                despues = _score_fila_materia(rows[i], id_def) + _score_fila_materia(rows[j], id_exc)
                ganancia = despues - antes
                if ganancia > mejor_ganancia:
                    mejor_ganancia = ganancia
                    mejor_par = (i, j)

        if mejor_par is None:
            i, j = idx_exc[0], idx_def[0]
        else:
            i, j = mejor_par

        intercambiar_materia(rows, i, j)
        cambios += 1

    return cambios


def intercambiar_tipo(rows: list[dict], i: int, j: int) -> None:
    a, b = rows[i]["Tipo"], rows[j]["Tipo"]
    rows[i]["Tipo"] = b
    rows[j]["Tipo"] = a


def ajustar_tipos_globales(rows: list[dict], max_pasos: int = 50) -> int:
    tgt = preguntas_por_tipo_global()
    cambios = 0
    for _ in range(max_pasos):
        c = Counter(r["Tipo"] for r in rows)
        if c["Teoria"] == tgt and c["Calculo"] == tgt:
            break
        if c["Teoria"] > tgt:
            tipo_exc, tipo_def = "Teoria", "Calculo"
        else:
            tipo_exc, tipo_def = "Calculo", "Teoria"
        idx_exc = [i for i, r in enumerate(rows) if r["Tipo"] == tipo_exc]
        idx_def = [i for i, r in enumerate(rows) if r["Tipo"] == tipo_def]
        if not idx_exc or not idx_def:
            break
        intercambiar_tipo(rows, idx_exc[0], idx_def[0])
        cambios += 1
    return cambios


def ajustar_tipos_por_materia(rows: list[dict], max_pasos: int = 200) -> int:
    temas, _ = cargar_orden_temas()
    cambios = 0
    for _ in range(max_pasos):
        hubo = False
        for tema in temas:
            sub = [(i, r) for i, r in enumerate(rows) if materia_de_fila(r) == tema]
            if len(sub) != 10:
                continue
            teo = [i for i, r in sub if r["Tipo"] == "Teoria"]
            cal = [i for i, r in sub if r["Tipo"] == "Calculo"]
            if len(teo) == 5 and len(cal) == 5:
                continue
            if len(teo) > 5 and cal:
                intercambiar_tipo(rows, teo[0], cal[0])
                cambios += 1
                hubo = True
            elif len(cal) > 5 and teo:
                intercambiar_tipo(rows, cal[0], teo[0])
                cambios += 1
                hubo = True
        if not hubo:
            break
    return cambios


def ajustar_dificultad_bloques(rows: list[dict]) -> int:
    """Reetiqueta Dificultad por bloque de 10 con mínimos cambios (sin tocar texto)."""
    temas, _ = cargar_orden_temas()
    por_materia: dict[str, list[dict]] = {t: [] for t in temas}
    for r in rows:
        por_materia[materia_de_fila(r)].append(r)

    cambios = 0
    for bi, tema in enumerate(temas):
        bloque = por_materia[tema]
        if len(bloque) != 10:
            continue
        nuevas = mejor_asignacion_dificultad(bloque, target_fmd(bi))
        for r, nd in zip(bloque, nuevas, strict=True):
            if r["Dificultad"] != nd:
                r["Dificultad"] = nd
                cambios += 1
    return cambios


def ajustar_dificultad_global_por_intercambio(rows: list[dict], max_pasos: int = 100) -> int:
    tgt = objetivos_dificultad_por_totales(len(rows))
    cambios = 0
    for _ in range(max_pasos):
        c = Counter(r["Dificultad"] for r in rows)
        ok = all(c.get(d, 0) == tgt[d] for d in ("Facil", "Media", "Dificil"))
        if ok:
            break
        exc = max(("Facil", "Media", "Dificil"), key=lambda d: c.get(d, 0) - tgt[d])
        defi = min(("Facil", "Media", "Dificil"), key=lambda d: c.get(d, 0) - tgt[d])
        if c.get(exc, 0) <= tgt[exc] or c.get(defi, 0) >= tgt[defi]:
            break
        i = next(i for i, r in enumerate(rows) if r["Dificultad"] == exc)
        j = next(i for i, r in enumerate(rows) if r["Dificultad"] == defi)
        rows[i]["Dificultad"], rows[j]["Dificultad"] = rows[j]["Dificultad"], rows[i]["Dificultad"]
        cambios += 1
    return cambios


def _ejecutar_ajuste_intercambios(
    dry_run: bool = False, sin_dificultad: bool = False
) -> int:
    """Modo legado: intercambia Materia/Tipo/Dificultad sin cambiar el enunciado."""
    print(
        "AVISO: modo --intercambios (solo etiquetas). "
        "Preferible el modo por defecto (regeneración desde plantillas)."
    )
    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    ok_antes, msgs_antes = validar(rows)
    print(f"Estado inicial: {'OK' if ok_antes else len(msgs_antes)} desviación(es)")

    n_mat = ajustar_conteos_materia(rows)
    n_tg = ajustar_tipos_globales(rows)
    n_tm = ajustar_tipos_por_materia(rows)
    n_dif = 0
    if not sin_dificultad:
        n_dif += ajustar_dificultad_bloques(rows)
        n_dif += ajustar_dificultad_global_por_intercambio(rows)

    print(
        f"Intercambios: materia={n_mat}, tipo_global={n_tg}, "
        f"tipo_materia={n_tm}, dificultad={n_dif}"
    )

    ok_despues, msgs_despues = validar(rows)
    if ok_despues:
        print("Estado final: OK")
    else:
        print(f"Estado final: quedan {len(msgs_despues)} desviación(es)")
        for m in msgs_despues[:12]:
            print(f"  - {m}")
        if len(msgs_despues) > 12:
            print(f"  ... y {len(msgs_despues) - 12} más (python Files/balance.py validar --detalle)")

    if dry_run:
        print("(dry-run: no se ha guardado el CSV)")
        return 0 if ok_despues else 1

    guardar_filas_csv(None, rows, PATH_CSV)
    print("Guardado:", str(PATH_CSV))
    if not ok_despues:
        print("Prueba: python Files/balance.py reordenar --solo-metadatos")
    return 0 if ok_despues else 1


def ejecutar_ajuste(
    dry_run: bool = False,
    sin_dificultad: bool = False,
    intercambios: bool = False,
) -> int:
    if intercambios:
        return _ejecutar_ajuste_intercambios(
            dry_run=dry_run, sin_dificultad=sin_dificultad
        )

    from dataset_pipeline import PASOS_PIPELINE, ejecutar_pipeline_regenerar

    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    ok_antes, msgs_antes = validar(rows)
    print(f"Estado inicial: {'OK' if ok_antes else len(msgs_antes)} desviación(es)")

    pasos = list(PASOS_PIPELINE)
    if sin_dificultad:
        pasos = [(n, f) for n, f in pasos if "dificultad" not in n.lower()]

    rc = ejecutar_pipeline_regenerar(pasos, dry_run=dry_run)
    if rc != 0 or dry_run:
        return rc

    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    ok_despues, msgs_despues = validar(rows)
    if ok_despues:
        print("Estado final: OK")
    else:
        print(f"Estado final: quedan {len(msgs_despues)} desviación(es)")
        for m in msgs_despues[:12]:
            print(f"  - {m}")
        if len(msgs_despues) > 12:
            print(f"  ... y {len(msgs_despues) - 12} más (validar --detalle)")
        print("Prueba: python Files/balance.py reordenar")
    return 0 if ok_despues else 1


def _row(
    materia: str,
    dificultad: str,
    tipo: str,
    pregunta: str,
    a: str,
    b: str,
    c: str,
    d: str,
    correcta: str,
) -> dict[str, str]:
    return {
        "Materia": materia,
        "Dificultad": dificultad,
        "Tipo": tipo,
        "Pregunta": pregunta,
        "A": a,
        "B": b,
        "C": c,
        "D": d,
        "Correcta": correcta,
    }


# Parches por Id (solo columnas de pregunta; Materia/Dificultad/Tipo se ajustan si faltan)
PATCHES: dict[int, dict[str, str]] = {
    # Àlgebra: quitar triplicado polinomio característico
    3: _row(
        "Àlgebra Lineal", "Media", "Teoria",
        "¿Qué es un subespacio vectorial?",
        "Un conjunto cualquiera", "Solo los vectores nulos",
        "Un subconjunto cerrado bajo suma y producto por escalar", "El espacio completo", "C",
    ),
    4: _row(
        "Àlgebra Lineal", "Media", "Teoria",
        "¿Qué es el subespacio generado por vectores?",
        "La suma", "El producto", "La intersección",
        "Conjunto de todas las combinaciones lineales", "D",
    ),
    # Càlcul I: contenido de una variable (los numéricos pasan a CN)
    11: _row(
        "Càlcul en una Variable", "Facil", "Teoria",
        "¿Qué es la derivada?",
        "Integral", "Límite", "Tasa de cambio instantánea", "Serie", "C",
    ),
    12: _row(
        "Càlcul en una Variable", "Facil", "Teoria",
        "¿Qué es el límite de f(x) cuando x tiende a a?",
        "El valor de f(a) siempre", "La recta tangente", "La derivada en a",
        "El valor al que tiende f(x)", "D",
    ),
    13: _row(
        "Càlcul en una Variable", "Media", "Teoria",
        "¿Qué enuncia el teorema fundamental del cálculo (parte II)?",
        "Toda función es derivable", "La integral de la derivada recupera la función (salvo constante)",
        "Toda serie converge", "El gradiente es cero", "B",
    ),
    22: _row(
        "Fonaments de Computadors", "Facil", "Teoria",
        "En la arquitectura von Neumann, programa e instrucciones se almacenan:",
        "En memorias físicas separadas sin bus común",
        "En la misma memoria accesible por el mismo mecanismo",
        "Solo en registros del ALU", "Únicamente en disco óptico", "B",
    ),
    14: _row(
        "Càlcul en una Variable", "Media", "Teoria",
        "¿Qué es el radio de convergencia de una serie de potencias?",
        "Límite superior de |x| donde converge", "Número de términos",
        "Suma total", "Derivada", "A",
    ),
    15: _row(
        "Càlcul en una Variable", "Dificil", "Teoria",
        "¿Qué es la continuidad de f en un punto a?",
        "f(a)=0", "Existe límite pero no es finito",
        "lim(x→a) f(x)=f(a)", "f está definida solo en a", "C",
    ),
    20: _row(
        "Càlcul en una Variable", "Dificil", "Calculo",
        "Si f(x)=x², ¿cuál es la integral definida de 0 a 2?",
        "4", "8/3", "2", "6", "B",
    ),
    24: _row(
        "Fonaments de Computadors", "Media", "Teoria",
        "¿Qué es un hazard de datos en pipeline?",
        "Fallido de predicción", "Error de caché", "Interrupción",
        "Dependencia que impide ejecución paralela", "D",
    ),
    # Iniciació: quitar 4× complejidad BST
    31: _row(
        "Iniciació a la Programació", "Facil", "Teoria",
        "¿Qué es la redirección en la terminal?",
        "Un comando", "Una variable", "Enviar salida o entrada a archivos o comandos", "Un pipe", "C",
    ),
    32: _row(
        "Iniciació a la Programació", "Facil", "Teoria",
        "¿Qué es una variable?",
        "Función", "Clase", "Constante", "Contenedor con nombre para un valor", "D",
    ),
    33: _row(
        "Iniciació a la Programació", "Media", "Teoria",
        "¿Qué hace el operador de tubería (pipe) `|` en una shell tipo Unix?",
        "Conecta la salida estándar de un comando con la entrada estándar del siguiente",
        "Crea siempre un archivo temporal en disco",
        "Ejecuta el segundo comando antes que el primero",
        "Duplica la entrada estándar al error estándar", "A",
    ),
    34: _row(
        "Iniciació a la Programació", "Dificil", "Teoria",
        "¿Cómo se define el operador módulo %?",
        "Potencia", "Resto de la división entera", "División", "Multiplicación", "B",
    ),
    35: _row(
        "Iniciació a la Programació", "Dificil", "Teoria",
        "¿Cómo se define un parámetro de función?",
        "Variable global", "Valor de retorno", "Variable de entrada de una función", "Constante", "C",
    ),
    # Programari: genética → waitpid
    47: _row(
        "Programari de Sistema", "Facil", "Calculo",
        "¿Qué hace típicamente waitpid() en Unix cuando el hijo aún no ha terminado?",
        "Crea un hilo nuevo en el mismo espacio de direcciones",
        "Mapea memoria compartida entre procesos",
        "Bloquea al llamador hasta que el hijo cambie de estado (p.ej. termine)",
        "Envía señal SIGKILL al padre", "C",
    ),
    # Diverses: quitar período (Fourier) → jacobiano polar
    69: _row(
        "Càlcul en Diverses Variables", "Media", "Calculo",
        "¿Cuál es el Jacobiano de x=r·cos(theta) y=r·sen(theta)?",
        "r", "r²", "1", "r/2", "A",
    ),
    # Fonaments: quitar duplicado de localidad espacial
    23: _row(
        "Fonaments de Computadors", "Media", "Teoria",
        "¿Qué es la localidad temporal en acceso a memoria?",
        "Misma dirección se reutiliza en poco tiempo",
        "Paginação", "Acceso aleatorio", "Direcciones cercanas se acceden juntas", "A",
    ),
    # Diverses: sustituir punto crítico duplicado (git 63) por derivada parcial
    63: _row(
        "Càlcul en Diverses Variables", "Media", "Teoria",
        "¿Qué es la derivada parcial de f respecto a x?",
        "La derivada total", "La derivada de f tratando las demás variables como constantes",
        "La integral de f", "El gradiente", "B",
    ),
    # Diverses: sustituir segundo punto crítico (git 62) por diferenciabilidad
    62: _row(
        "Càlcul en Diverses Variables", "Facil", "Teoria",
        "¿Cuándo f es diferenciable en un punto?",
        "Si tiene derivadas parciales", "Si es continua",
        "Si existe plano tangente que aproxima bien", "Si tiene gradiente", "C",
    ),
    # Càlcul Numèric: bloque coherente
    71: _row(
        "Càlcul Numèric", "Facil", "Teoria",
        "¿Qué es el método de bisección?",
        "Para derivadas", "Para integrales",
        "Para encontrar raíces dividiendo el intervalo", "Para interpolación", "C",
    ),
    72: _row(
        "Càlcul Numèric", "Facil", "Calculo",
        "¿Qué es el error de truncamiento?",
        "Por la máquina", "Por redondeo",
        "Por aproximar una serie infinita con términos finitos", "Por el método", "C",
    ),
    73: _row(
        "Càlcul Numèric", "Media", "Teoria",
        "¿Qué es el método de diferencias finitas?",
        "Para integrales", "Para series", "Para Monte Carlo",
        "Aproximar derivadas con cocientes incrementales", "D",
    ),
    74: _row(
        "Càlcul Numèric", "Media", "Teoria",
        "¿Cómo se define el método del punto fijo?",
        "Iterar x=g(x) hasta convergencia", "Bisección", "Secante", "Newton", "A",
    ),
    75: _row(
        "Càlcul Numèric", "Dificil", "Teoria",
        "En cálculo numérico con aritmética finita, el error de redondeo aparece porque:",
        "Toda función es analítica en ℝ",
        "Solo existe un conjunto finito de números máquina representables",
        "El método del trapecio siempre diverge", "La derivada segunda es nula", "B",
    ),
    76: _row(
        "Càlcul Numèric", "Dificil", "Teoria",
        "¿Cómo se define la regla de Simpson?",
        "Monte Carlo", "Trapecio", "Aproximación por parábolas", "Rectángulos", "C",
    ),
    77: _row(
        "Càlcul Numèric", "Facil", "Calculo",
        "Newton-Raphson para x²-2, x₀=1. ¿x₁?",
        "1", "1.5", "2", "0.5", "B",
    ),
    78: _row(
        "Càlcul Numèric", "Facil", "Calculo",
        "Aproximación trapecio para ∫₀¹ x dx con 2 subintervalos?",
        "0.25", "0.75", "1", "0.5", "D",
    ),
    79: _row(
        "Càlcul Numèric", "Media", "Calculo",
        "¿Qué es la tolerancia en un método numérico?",
        "El número de iteraciones", "La precisión", "El error máximo",
        "El criterio de parada (error aceptable)", "D",
    ),
    80: _row(
        "Càlcul Numèric", "Dificil", "Calculo",
        "Si f es C² en [a,b], ¿cómo escala usualmente el error global de la regla del trapecio compuesto con paso h=(b-a)/n?",
        "O(h³)", "O(h)", "O(1/h)", "O(h²)", "D",
    ),
}


def cargar_git_rows() -> list[dict]:
    raw = subprocess.check_output(["git", "show", "HEAD:Data/Preguntas.csv"], cwd=BASE)
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter=";"))


def aplicar_parches(rows: list[dict]) -> int:
    n = 0
    for r in rows:
        rid = int(r["Id"])
        if rid not in PATCHES:
            continue
        for k, v in PATCHES[rid].items():
            r[k] = v
        n += 1
    return n


def ejecutar_corregir() -> int:
    print("1) Cargando base git HEAD…")
    try:
        rows = cargar_git_rows()
    except subprocess.CalledProcessError:
        print("Error: no se pudo leer HEAD:Data/Preguntas.csv desde git")
        return 1
    if len(rows) != 400:
        print(f"Se esperaban 400 filas en git, hay {len(rows)}")
        return 1

    print("2) Aplicando parches de contenido/materia…")
    n = aplicar_parches(rows)
    print(f"   {n} filas actualizadas")

    print("3) Guardando CSV…")
    for i, r in enumerate(rows, start=1):
        r["Id"] = str(i)
    guardar_filas_csv(None, rows, PATH_CSV)

    print("4) Sincronizar plantillas (dataset → plantillas.json)…")
    r_inj = subprocess.run(
        [sys.executable, str(BASE / "Files" / "asegurar_plantillas_sobre_dataset.py")],
        cwd=BASE,
    )
    if r_inj.returncode != 0:
        return r_inj.returncode

    print("5) Reordenar (solo metadatos)…")
    if ejecutar_reordenar(solo_metadatos=True) != 0:
        return 1

    with PATH_CSV.open(encoding="utf-8", newline="") as f:
        final = list(csv.DictReader(f, delimiter=";"))
    ok, msgs = validar(final)
    print("\n" + ("OK: dataset corregido y balanceado." if ok else "Avisos tras corrección:"))
    for m in msgs:
        print(f"  - {m}")
    return 0 if ok else 1


