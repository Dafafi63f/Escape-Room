#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reordena Data/Preguntas.csv según el orden de asignaturas en Data/listado_materias.csv.

Qué hace (y qué NO hace)
------------------------
- SÍ: Recorre las materias en el mismo orden en que aparecen en listado_materias.csv (columna Materia).
- SÍ: Dentro de cada materia, el orden final de las 10 filas es el «ladder» TF→TM→TD y luego CF→CM→CD:
      todas las Teoría ordenadas por Dificultad (Facil, Media, Dificil) y a igualdad por Id antiguo;
      después todas las Cálculo con el mismo criterio. Así las dificultades no «saltan» dentro de cada mitad.
- SÍ: Reparte Dificultad en cada bloque de 10 para que, sumando los 40 bloques, salga el global
      134 Facil / 133 Media / 133 Dificil (14×(4,3,3) + 13×(3,4,3) + 13×(3,3,4)).
- SÍ: Renumera Id de 1 a 400 en ese orden de filas y permuta A–D para que Correcta siga
      el ciclo A,B,C,D,A,… según (Id-1) mod 4.

- NO: Ordena alfabéticamente por texto de Pregunta ni por ninguna otra columna de contenido.
- NO: Es lo mismo que utils_dataset_csv.ordenar_filas_por_tema_y_id (esa solo ordena tema+Id,
      sin forzar bloque Teoria→Calculo ni tocar dificultad ni respuestas).

Tras ejecutarlo, el archivo queda con filas 1–400 = bloques de 10 consecutivos por materia
en orden de listado. Si en Excel ordenas solo por «Materia» alfabéticamente, el orden de Id
dejará de reflejar el listado (es esperable).

Uso: python reordenar_balance_por_materia.py
     python reordenar_balance_por_materia.py --explicar   # solo imprime esta lógica y termina

No requiere scipy (fuerza bruta sobre permutaciones del multiset de dificultad, ~4200 casos).
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import COLUMNAS_PREGUNTAS, guardar_filas_csv

PATH_CSV = BASE / "Data" / "Preguntas.csv"
LETRAS = ("A", "B", "C", "D")


def ord_diff(k: object) -> int:
    """Orden Facil < Media < Dificil para el ladder TF… TM… TD… / CF… CM… CD…"""
    return {"Facil": 0, "Media": 1, "Dificil": 2}.get(str(k).strip(), 99)


def target_fmd(bloque_idx: int) -> tuple[int, int, int]:
    """Cuentas (Facil, Media, Dificil) para el bloque `bloque_idx` 0..39."""
    if bloque_idx < 14:
        return (4, 3, 3)
    if bloque_idx < 27:
        return (3, 4, 3)
    return (3, 3, 4)


def labels_from_fmd(f: int, m: int, d: int) -> tuple[str, ...]:
    return tuple(["Facil"] * f + ["Media"] * m + ["Dificil"] * d)


def mejor_asignacion_dificultad(rows: list[dict], fmd: tuple[int, int, int]) -> list[str]:
    """Devuelve lista de 10 etiquetas Dificultad (orden paralelo a `rows`) con mínimos cambios."""
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
    """Reordena A..D para que la respuesta correcta quede en `letra_objetivo` (contenido intacto)."""
    letra_objetivo = letra_objetivo.strip().upper()
    opts = {L: str(row.get(L, "") or "") for L in LETRAS}
    old = str(row.get("Correcta", "") or "").strip().upper()
    if old not in opts:
        raise ValueError(f"Correcta inválida {old!r} en fila Id={row.get('Id')}")
    val_ok = opts[old]
    otras = [opts[L] for L in LETRAS if L != old]
    nuevo: dict[str, str] = {}
    idx = 0
    for L in LETRAS:
        if L == letra_objetivo:
            nuevo[L] = val_ok
        else:
            nuevo[L] = otras[idx]
            idx += 1
    out = dict(row)
    for L in LETRAS:
        out[L] = nuevo[L]
    out["Correcta"] = letra_objetivo
    return out


def comprobar_orden_canonico_df(df) -> list[str]:
    """
    Comprueba que `df` cumple el orden canónico (listado, TTTTTCCCCC, ladder F/M/D
    en cada mitad, triple F/M/D por bloque, globales y ciclo Correcta).
    Devuelve lista de mensajes de error (vacía si todo OK).
    """
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
    for L in LETRAS:
        if df["Correcta"].value_counts().get(L, 0) != 100:
            errs.append(f"Correcta {L}: {df['Correcta'].value_counts().get(L, 0)} (obj. 100)")
    esp = df["Id"].astype(int).map(lambda x: LETRAS[(x - 1) % 4])
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


def imprimir_explicacion() -> None:
    print(__doc__)


def main() -> None:
    import pandas as pd

    if "--explicar" in sys.argv:
        imprimir_explicacion()
        return

    df = pd.read_csv(PATH_CSV, sep=";", encoding="utf-8")
    temas, _ = cargar_orden_temas()
    faltan = set(df["Materia"].unique()) - set(temas)
    if faltan:
        raise SystemExit(f"Materias no listadas: {faltan}")

    por_materia: dict[str, list[dict]] = {t: [] for t in temas}
    for _, r in df.iterrows():
        m = str(r["Materia"]).strip()
        por_materia[m].append(r.to_dict())

    nuevas: list[dict] = []
    for bi, tema in enumerate(temas):
        bloque = por_materia[tema]
        if len(bloque) != 10:
            raise SystemExit(f"{tema!r}: se esperaban 10 filas, hay {len(bloque)}")

        teo = [x for x in bloque if str(x.get("Tipo", "")).strip() == "Teoria"]
        cal = [x for x in bloque if str(x.get("Tipo", "")).strip() == "Calculo"]
        if len(teo) != 5 or len(cal) != 5:
            raise SystemExit(f"{tema!r}: tipo {len(teo)} Teoria / {len(cal)} Calculo")

        # Entrada al optimizador: ya agrupado T/C; por dificultad antigua + Id (estable).
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
        # Orden pedido: TF… TM… TD…, luego CF… CM… CD… (dificultad no decreciente en cada mitad).
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
        obj = LETRAS[(i - 1) % 4]
        r2 = permutar_abcd_objetivo(r, obj)
        nuevas[i - 1] = r2

    # Comprobaciones
    chk = pd.DataFrame(nuevas)
    errs = comprobar_orden_canonico_df(chk)
    if errs:
        raise SystemExit("Post-condición orden canónico:\n" + "\n".join(errs))

    guardar_filas_csv(list(COLUMNAS_PREGUNTAS), nuevas, PATH_CSV)
    print("OK: ladder TF..TM..TD luego CF..CM..CD, F/M/D por bloque, Id 1..400, ABCD ciclico.")
    print("  (Orden de materias = Data/listado_materias.csv; ver --explicar)")


if __name__ == "__main__":
    main()
