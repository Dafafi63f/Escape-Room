#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cuestionario en consola — **modo libre** (único implementado).

Modos previstos en el TFG:
  - Libre (este script): partida configurable, filtros, dificultad progresiva, ranking.
  - Historia (en desarrollo): progresión narrativa tipo escape room / novela gráfica.
  - Feedback (en desarrollo): retroalimentación pedagógica tras cada respuesta.

Banco de preguntas (modo libre; por defecto solo 1):
  1) Dataset — MODO SEGURO (`Preguntas.csv`, revisado).
  2) Todo — MODO BETA (dataset + plantillas extra; 480 + N).
  3) Solo plantillas extra — MODO BETA (no revisadas).

Uso:
  python Juego/juego_cuestionario.py
"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


def _roots_busqueda() -> list[Path]:
    """Genera raíces candidatas para buscar ficheros externos."""
    candidatos: list[Path] = []
    vistos: set[Path] = set()

    rutas_base = [Path(__file__).resolve().parent, Path.cwd()]
    if getattr(sys, "frozen", False):
        rutas_base.append(Path(sys.executable).resolve().parent)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        rutas_base.append(Path(meipass))

    for base in rutas_base:
        try:
            base = base.resolve()
        except OSError:
            continue
        for ruta in (base, *base.parents):
            if ruta not in vistos and ruta.exists():
                vistos.add(ruta)
                candidatos.append(ruta)
    return candidatos


def resolver_dataset() -> Path:
    """
    Localiza Preguntas.csv dentro del proyecto aunque no esté en Data/.
    Prioriza Data/Preguntas.csv cuando exista.
    """
    candidatos: list[Path] = []
    vistos: set[Path] = set()

    # Prioriza ubicaciones típicas antes de búsqueda recursiva.
    for raiz in _roots_busqueda():
        if raiz in vistos:
            continue
        vistos.add(raiz)
        candidatos.append(raiz)

    # Búsqueda rápida en ubicaciones esperadas.
    for raiz in candidatos:
        for preferida in (raiz / "Data" / "Preguntas.csv", raiz / "Preguntas.csv"):
            if preferida.exists():
                return preferida

    # Búsqueda recursiva en el proyecto.
    for raiz in candidatos:
        coincidencias = sorted(
            raiz.rglob("Preguntas.csv"),
            key=lambda p: (0 if p.parent.name.lower() == "data" else 1, len(p.parts), str(p)),
        )
        if coincidencias:
            return coincidencias[0]

    raise FileNotFoundError("No se encontró un archivo 'Preguntas.csv' en rutas accesibles.")


def resolver_ranking() -> Path:
    """
    Guarda el ranking en una ruta persistente:
    - Ejecutable: junto al .exe.
    - Script: junto al .py.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "ranking_quiz.csv"
    return Path(__file__).resolve().parent / "ranking_quiz.csv"


def resolver_listado_materias() -> Path:
    """
    Localiza listado_materias.csv para enriquecer las preguntas con
    metadatos academicos (grupo, nivel, curso, semestre).
    """
    candidatos: list[Path] = []
    vistos: set[Path] = set()
    for raiz in _roots_busqueda():
        if raiz in vistos:
            continue
        vistos.add(raiz)
        candidatos.append(raiz)

    for raiz in candidatos:
        for candidata in (raiz / "Data" / "listado_materias.csv", raiz / "listado_materias.csv"):
            if candidata.exists():
                return candidata

    for raiz in candidatos:
        coincidencias = sorted(
            raiz.rglob("listado_materias.csv"),
            key=lambda p: (0 if p.parent.name.lower() == "data" else 1, len(p.parts), str(p)),
        )
        if coincidencias:
            return coincidencias[0]

    raise FileNotFoundError("No se encontró 'listado_materias.csv' en rutas accesibles.")


def resolver_plantillas() -> Path:
    """Localiza plantillas.json (mismo criterio de búsqueda que Preguntas.csv)."""
    for raiz in _roots_busqueda():
        candidata = raiz / "Data" / "plantillas.json"
        if candidata.exists():
            return candidata
    for raiz in _roots_busqueda():
        coincidencias = sorted(
            raiz.rglob("plantillas.json"),
            key=lambda p: (0 if p.parent.name.lower() == "data" else 1, len(p.parts), str(p)),
        )
        if coincidencias:
            return coincidencias[0]
    raise FileNotFoundError("No se encontró 'plantillas.json' en rutas accesibles.")


def _norm_clave(texto: str) -> str:
    return (texto or "").strip().lower()


def clave_contenido(materia: str, texto: str, opciones: dict[str, str], correcta: str) -> tuple:
    """Misma idea que la deduplicación mantenimiento: materia + enunciado + opciones + correcta."""
    return (
        _norm_clave(materia),
        _norm_clave(texto),
        _norm_clave(opciones.get("A", "")),
        _norm_clave(opciones.get("B", "")),
        _norm_clave(opciones.get("C", "")),
        _norm_clave(opciones.get("D", "")),
        _norm_clave(correcta),
    )


def claves_dataset(path_csv: Path) -> set[tuple]:
    claves: set[tuple] = set()
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            materia = (row.get("Materia") or row.get("Tema") or "").strip()
            opciones = {L: (row.get(L) or "").strip() for L in ("A", "B", "C", "D")}
            correcta = (row.get("Correcta") or "").strip().upper()
            if not materia or not (row.get("Pregunta") or "").strip():
                continue
            claves.add(
                clave_contenido(materia, row.get("Pregunta", ""), opciones, correcta)
            )
    return claves


def _tiene_placeholders(texto: str) -> bool:
    return bool(re.search(r"\{[^{}]+\}", texto or ""))


def _expandir_plantilla(tema: str, t: dict) -> list[dict]:
    """Instancias jugables de una plantilla (sustituye variaciones si existen)."""
    base_opts = {L: (t.get(L) or "").strip() for L in ("A", "B", "C", "D")}
    base = {
        "materia": tema,
        "pregunta": (t.get("pregunta") or "").strip(),
        "opciones": dict(base_opts),
        "correcta": (t.get("correcta") or "").strip().upper(),
        "dificultad": (t.get("dificultad") or "Media").strip(),
        "tipo": (t.get("tipo") or "Teoria").strip(),
        "uso": (t.get("uso") or "").strip(),
    }
    variaciones = t.get("variaciones")
    if not variaciones:
        return [base]
    instancias: list[dict] = []
    for var in variaciones:
        p = base["pregunta"]
        opts = dict(base["opciones"])
        for key, val in var.items():
            ph = "{" + str(key) + "}"
            p = p.replace(ph, str(val))
            for L in ("A", "B", "C", "D"):
                opts[L] = opts[L].replace(ph, str(val))
        instancias.append({**base, "pregunta": p, "opciones": opts})
    return instancias


def _plantilla_a_pregunta(inst: dict, materias_meta: dict[str, dict[str, str]]) -> Pregunta | None:
    correcta = inst["correcta"]
    if correcta not in {"A", "B", "C", "D"}:
        return None
    texto = inst["pregunta"]
    opciones = inst["opciones"]
    if not texto or not all(opciones.values()):
        return None
    bloque = texto + "".join(opciones.values())
    if _tiene_placeholders(bloque):
        return None
    materia = inst["materia"]
    mm = materias_meta.get(materia, {})
    return Pregunta(
        texto=texto,
        materia=materia,
        tematica=mm.get("tematica", ""),
        dificultad=inst["dificultad"],
        tipo=inst["tipo"],
        grupo=mm.get("grupo", ""),
        nivel=mm.get("nivel", ""),
        curso=mm.get("curso", ""),
        semestre=mm.get("semestre", ""),
        opciones=opciones,
        correcta=correcta,
        fuente="plantilla",
    )


def cargar_preguntas_plantillas(
    path_json: Path,
    materias_meta: dict[str, dict[str, str]],
    *,
    solo_fuera_dataset: bool,
    claves_ds: set[tuple],
) -> list[Pregunta]:
    if not path_json.exists():
        raise FileNotFoundError(f"No se encontró plantillas: {path_json}")

    data = json.loads(path_json.read_text(encoding="utf-8"))
    preguntas: list[Pregunta] = []
    vistos: set[tuple] = set()

    for tema, items in data.items():
        if not tema:
            continue
        for t in items:
            for inst in _expandir_plantilla(tema, t):
                k = clave_contenido(
                    inst["materia"],
                    inst["pregunta"],
                    inst["opciones"],
                    inst["correcta"],
                )
                if solo_fuera_dataset and k in claves_ds:
                    continue
                if k in vistos:
                    continue
                p = _plantilla_a_pregunta(inst, materias_meta)
                if p:
                    vistos.add(k)
                    preguntas.append(p)
    return preguntas


def cargar_banco_todo(
    path_csv: Path,
    path_plantillas: Path,
    materias_meta: dict[str, dict[str, str]],
) -> list[Pregunta]:
    """Todo jugable = dataset revisado + plantillas que no están en el CSV."""
    claves = claves_dataset(path_csv)
    revisadas = cargar_preguntas(path_csv, materias_meta)
    extra = cargar_preguntas_plantillas(
        path_plantillas, materias_meta, solo_fuera_dataset=True, claves_ds=claves
    )
    return revisadas + extra


def contar_bancos(path_csv: Path, path_plantillas: Path, materias_meta: dict) -> dict[BancoPreguntas, int]:
    n_ds = len(cargar_preguntas(path_csv, materias_meta))
    claves = claves_dataset(path_csv)
    n_extra = len(
        cargar_preguntas_plantillas(
            path_plantillas, materias_meta, solo_fuera_dataset=True, claves_ds=claves
        )
    )
    return {
        BancoPreguntas.DATASET: n_ds,
        BancoPreguntas.PLANTILLAS_EXTRA: n_extra,
        BancoPreguntas.PLANTILLAS_TODO: n_ds + n_extra,
    }


def elegir_banco_preguntas(
    path_csv: Path,
    path_plantillas: Path,
    materias_meta: dict[str, dict[str, str]],
) -> tuple[list[Pregunta], BancoPreguntas]:
    try:
        conteos = contar_bancos(path_csv, path_plantillas, materias_meta)
    except FileNotFoundError as e:
        print(str(e))
        print("Usando solo el dataset revisado.")
        return cargar_preguntas(path_csv, materias_meta), BancoPreguntas.DATASET

    n_ds = conteos[BancoPreguntas.DATASET]
    n_extra = conteos[BancoPreguntas.PLANTILLAS_EXTRA]
    n_todo = conteos[BancoPreguntas.PLANTILLAS_TODO]

    print("\nBanco de preguntas:")
    print(
        f"  1) Dataset revisado — MODO SEGURO ({n_ds} preguntas) [por defecto, recomendado]"
    )
    print(
        f"  2) Todo — MODO BETA ({n_ds} + {n_extra} = {n_todo}): "
        "dataset + plantillas no revisadas"
    )
    print(f"  3) Solo plantillas extra — MODO BETA ({n_extra} no revisadas)")
    print("     Pulsa Enter para el banco 1 (modo seguro). Las opciones 2 y 3 incluyen contenido beta.")

    while True:
        entrada = input("Selecciona banco [1 = modo seguro]: ").strip() or "1"
        if entrada == "1":
            banco = BancoPreguntas.DATASET
        elif entrada == "2":
            banco = BancoPreguntas.PLANTILLAS_TODO
        elif entrada == "3":
            banco = BancoPreguntas.PLANTILLAS_EXTRA
        else:
            print("Opción no válida. Elige 1, 2 o 3.")
            continue
        n = conteos[banco]
        if n == 0:
            print("Ese banco no tiene preguntas jugables. Prueba otra opción.")
            continue
        break

    modo_txt, desc = ETIQUETA_BANCO[banco]
    print(f"\n>>> {modo_txt}: {desc} ({n} preguntas cargadas)")
    if banco != BancoPreguntas.DATASET:
        print(
            "AVISO: incluye preguntas no revisadas. "
            "Usa el banco 1 (modo seguro) para evaluación fiable del TFG."
        )

    if banco == BancoPreguntas.DATASET:
        preguntas = cargar_preguntas(path_csv, materias_meta)
    elif banco == BancoPreguntas.PLANTILLAS_TODO:
        preguntas = cargar_banco_todo(path_csv, path_plantillas, materias_meta)
    else:
        claves = claves_dataset(path_csv)
        preguntas = cargar_preguntas_plantillas(
            path_plantillas, materias_meta, solo_fuera_dataset=True, claves_ds=claves
        )
    return preguntas, banco


PATH_PREGUNTAS = resolver_dataset()
PATH_RANKING = resolver_ranking()
PATH_MATERIAS = resolver_listado_materias()


class BancoPreguntas(str, Enum):
    DATASET = "dataset"
    PLANTILLAS_TODO = "plantillas_todo"
    PLANTILLAS_EXTRA = "plantillas_extra"


ETIQUETA_BANCO: dict[BancoPreguntas, tuple[str, str]] = {
    BancoPreguntas.DATASET: ("MODO SEGURO", "Data/Preguntas.csv (banco revisado)"),
    BancoPreguntas.PLANTILLAS_TODO: (
        "MODO BETA",
        "dataset revisado + plantillas fuera del dataset",
    ),
    BancoPreguntas.PLANTILLAS_EXTRA: (
        "MODO BETA",
        "solo plantillas.json fuera del dataset (no revisadas)",
    ),
}


@dataclass
class Pregunta:
    texto: str
    materia: str
    tematica: str
    dificultad: str
    tipo: str
    grupo: str
    nivel: str
    curso: str
    semestre: str
    opciones: dict[str, str]
    correcta: str
    fuente: str = "dataset"


def cargar_materias(path_csv: Path) -> dict[str, dict[str, str]]:
    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el listado de materias: {path_csv}")

    materias: dict[str, dict[str, str]] = {}
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            materia = (row.get("Materia") or "").strip()
            if not materia:
                continue
            materias[materia] = {
                "grupo": (row.get("Grupo") or "").strip(),
                "nivel": (row.get("Nivel") or "").strip(),
                "tematica": (row.get("Tematica") or "").strip(),
                "curso": (
                    row.get("Curso")
                    or row.get("Año")
                    or row.get("Ano")
                    or ""
                ).strip(),
                "semestre": (row.get("Semestre") or "").strip(),
            }
    return materias


def cargar_preguntas(path_csv: Path, materias_meta: dict[str, dict[str, str]]) -> list[Pregunta]:
    """
    Lee el CSV de preguntas. Esquema esperado: Id, Materia, Dificultad, Tipo, Pregunta, A, B, C, D, Correcta.
    Tematica, grupo, nivel, curso y semestre se obtienen de `materias_meta` (listado_materias.csv);
    si el CSV incluyera esas columnas (formato antiguo), los valores no vacíos del CSV prevalecen.
    """
    if not path_csv.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {path_csv}")

    preguntas: list[Pregunta] = []
    with path_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            correcta = (row.get("Correcta") or "").strip().upper()
            if correcta not in {"A", "B", "C", "D"}:
                continue
            materia = (row.get("Materia") or row.get("Tema") or "Sin materia").strip()
            mm = materias_meta.get(materia, {})

            def _campo(csv_key: str, meta_key: str) -> str:
                v = (row.get(csv_key) or "").strip()
                return v if v else mm.get(meta_key, "")

            pregunta = Pregunta(
                texto=(row.get("Pregunta") or "").strip(),
                materia=materia,
                tematica=_campo("Tematica", "tematica"),
                dificultad=(row.get("Dificultad") or "Desconocida").strip(),
                tipo=(row.get("Tipo") or "General").strip(),
                grupo=_campo("Grupo", "grupo"),
                nivel=_campo("Nivel", "nivel"),
                curso=_campo("Curso", "curso"),
                semestre=_campo("Semestre", "semestre"),
                opciones={
                    "A": (row.get("A") or "").strip(),
                    "B": (row.get("B") or "").strip(),
                    "C": (row.get("C") or "").strip(),
                    "D": (row.get("D") or "").strip(),
                },
                correcta=correcta,
            )
            if pregunta.texto and all(pregunta.opciones.values()):
                preguntas.append(pregunta)
    return preguntas


def pedir_opcion(mensaje: str, validas: Iterable[str], default: str | None = None) -> str:
    validas_set = {v.upper() for v in validas}
    default_up = default.upper() if default else None
    while True:
        valor = input(mensaje).strip().upper()
        if valor == "" and default_up and default_up in validas_set:
            return default_up
        if valor in validas_set:
            return valor
        print(f"Opción inválida. Elige una de: {', '.join(sorted(validas_set))}")


def elegir_filtro(nombre: str, valores: list[str]) -> str | None:
    # Conserva el orden de aparición original del dataset.
    valores = list(dict.fromkeys(v for v in valores if v))
    print(f"\nFiltrar por {nombre}:")
    print("0) Todos (por defecto)")
    for i, valor in enumerate(valores, start=1):
        print(f"{i}) {valor}")
    while True:
        entrada = input("Selecciona una opción: ").strip()
        if entrada == "":
            return None
        if entrada.isdigit():
            idx = int(entrada)
            if idx == 0:
                return None
            if 1 <= idx <= len(valores):
                return valores[idx - 1]
        print("Selección no válida.")


def elegir_filtro_obligatorio(nombre: str, valores: list[str]) -> str:
    valores = list(dict.fromkeys(v for v in valores if v))
    print(f"\nFiltrar por {nombre}:")
    if not valores:
        raise ValueError(f"No hay valores disponibles para el filtro '{nombre}'.")
    for i, valor in enumerate(valores, start=1):
        etiqueta = " (por defecto)" if i == 1 else ""
        print(f"{i}) {valor}{etiqueta}")
    while True:
        entrada = input("Selecciona una opción: ").strip()
        if entrada == "":
            return valores[0]
        if entrada.isdigit():
            idx = int(entrada)
            if 1 <= idx <= len(valores):
                return valores[idx - 1]
        print("Selección no válida.")


def calcular_puntos(dificultad: str, acierto: bool) -> int:
    base = {"Facil": 10, "Media": 20, "Dificil": 30}.get(dificultad, 15)
    return base if acierto else -max(5, base // 2)


def dificultad_base(dificultad: str) -> int:
    return {"Facil": 1, "Media": 2, "Dificil": 3}.get(dificultad, 2)


def nivel_materia(nivel: str) -> int:
    try:
        return max(1, int(nivel))
    except (TypeError, ValueError):
        return 1


def complejidad_pregunta(pregunta: Pregunta) -> int:
    # Combina dificultad propia de la pregunta y nivel de la materia.
    return nivel_materia(pregunta.nivel) + dificultad_base(pregunta.dificultad) - 1


def dificultad_global_actual(
    respondidas: int,
    global_inicial: int,
    max_global: int,
    cada_n: int = 40,
) -> int:
    # Se mantiene constante y solo aumenta +1 cada "cada_n" respuestas.
    subida = respondidas // max(1, cada_n)
    return min(global_inicial + subida, max_global)


def pedir_entero_en_rango(mensaje: str, minimo: int, maximo: int, defecto: int) -> int:
    while True:
        entrada = input(mensaje).strip()
        if not entrada:
            return defecto
        if entrada.isdigit():
            valor = int(entrada)
            if minimo <= valor <= maximo:
                return valor
        print(f"Valor inválido. Introduce un número entre {minimo} y {maximo}.")


def guardar_ranking(nombre: str, puntos: int, total: int, aciertos: int) -> None:
    PATH_RANKING.parent.mkdir(parents=True, exist_ok=True)
    existe = PATH_RANKING.exists()
    with PATH_RANKING.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        if not existe:
            writer.writerow(["Jugador", "Puntos", "Preguntas", "Aciertos"])
        writer.writerow([nombre, str(puntos), str(total), str(aciertos)])


def mostrar_top_ranking(top_n: int = 10) -> None:
    if not PATH_RANKING.exists():
        print("\nNo hay ranking todavía. ¡Sé la primera puntuación!")
        return

    filas = []
    with PATH_RANKING.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                filas.append(
                    (
                        row.get("Jugador", "Anonimo"),
                        int(row.get("Puntos", "0")),
                        int(row.get("Aciertos", "0")),
                        int(row.get("Preguntas", "0")),
                    )
                )
            except ValueError:
                continue

    filas.sort(key=lambda x: (x[1], x[2]), reverse=True)
    print("\n=== TOP RANKING ===")
    for i, (jugador, puntos, aciertos, total) in enumerate(filas[:top_n], start=1):
        print(f"{i:>2}. {jugador:<15} {puntos:>4} pts | {aciertos}/{total}")


def jugar_partida(
    preguntas: list[Pregunta],
    banco: BancoPreguntas,
) -> None:
    modo_txt, desc_banco = ETIQUETA_BANCO[banco]
    print("\n=== QUIZ DATASET CHALLENGE ===")
    print("Modo de juego: LIBRE (partida abierta con filtros y ranking).")
    print(f"Banco activo: {modo_txt} — {desc_banco}")
    print("En desarrollo: modo HISTORIA (narrativa) y modo FEEDBACK (explicación tras cada respuesta).")
    print("Responde A/B/C/D. Tienes 3 vidas.")
    print("La dificultad global empieza baja y escala durante la partida.")

    nombre = input("Nombre de jugador: ").strip() or "Anonimo"
    modo_infinito = pedir_opcion("¿Activar modo infinito? (S/N): ", ["S", "N"], default="S") == "S"
    total = 0
    if not modo_infinito:
        n_preguntas = input("¿Cuántas preguntas quieres jugar? [10]: ").strip()
        total = int(n_preguntas) if n_preguntas.isdigit() and int(n_preguntas) > 0 else 10

    print("\nModo de filtro principal:")
    print("0) Todas (por defecto)")
    print("1) Por tematica")
    print("2) Por semestre")
    print("3) Por tipo")
    modo_filtro = pedir_opcion("Selecciona modo (0/1/2/3): ", ["0", "1", "2", "3"], default="0")

    tematica = None
    semestre = None
    curso = None
    tipo_principal = None
    if modo_filtro == "1":
        tematica = elegir_filtro("tematica", [p.tematica for p in preguntas])
    elif modo_filtro == "2":
        combos = [f"{p.curso}-{p.semestre}" for p in preguntas if p.curso and p.semestre]
        curso_semestre = elegir_filtro_obligatorio("curso-semestre", combos)
        curso, semestre = curso_semestre.split("-", 1)
    elif modo_filtro == "3":
        tipo_principal = elegir_filtro_obligatorio("tipo", [p.tipo for p in preguntas])

    pool = [
        p
        for p in preguntas
        if (tematica is None or p.tematica == tematica)
        and (curso is None or p.curso == curso)
        and (semestre is None or p.semestre == semestre)
        and (tipo_principal is None or p.tipo == tipo_principal)
    ]

    if not pool:
        print("\nNo hay preguntas para ese filtro. Prueba con otra combinación.")
        return

    if modo_filtro in {"0", "1"} and tematica is None:
        # Si no se filtra en el criterio principal (opción "Todos"), mezcla para evitar
        # que salgan bloques seguidos por orden original del CSV.
        random.shuffle(pool)
    total_objetivo = min(total, len(pool)) if not modo_infinito else None
    max_global = max(complejidad_pregunta(p) for p in pool)
    # Evita repeticiones recientes: una pregunta solo puede repetirse tras
    # responder al menos el 25% del pool activo.
    ventana_no_repeticion = max(1, len(pool) // 4)
    historial_reciente: deque[int] = deque(maxlen=ventana_no_repeticion)
    global_inicial = pedir_entero_en_rango(
        f"Dificultad global inicial [1-{max_global}] (Enter=1): ",
        1,
        max_global,
        1,
    )
    usadas: set[int] = set()

    vidas = 3
    aciertos = 0
    puntos = 0
    respondidas = 0

    while (modo_infinito or respondidas < total_objetivo) and vidas > 0:
        global_actual = dificultad_global_actual(
            respondidas=respondidas,
            global_inicial=global_inicial,
            max_global=max_global,
        )
        bloqueadas = set(historial_reciente)
        candidatas = [
            idx
            for idx, p in enumerate(pool)
            if idx not in usadas
            and idx not in bloqueadas
            and complejidad_pregunta(p) <= global_actual
        ]
        if not candidatas:
            if modo_infinito:
                usadas.clear()
                candidatas = [
                    idx
                    for idx, p in enumerate(pool)
                    if idx not in bloqueadas and complejidad_pregunta(p) <= global_actual
                ]
                if not candidatas:
                    # Fallback: si el pool es pequeño o la ventana bloquea todo,
                    # se permite repetir para no bloquear la partida.
                    candidatas = list(range(len(pool)))
            else:
                candidatas = [idx for idx in range(len(pool)) if idx not in usadas]
                if not candidatas:
                    break
        idx_elegida = random.choice(candidatas)
        usadas.add(idx_elegida)
        historial_reciente.append(idx_elegida)
        p = pool[idx_elegida]
        respondidas += 1

        print("\n" + "=" * 60)
        progreso = (
            f"Pregunta {respondidas}/∞"
            if modo_infinito
            else f"Pregunta {respondidas}/{total_objetivo}"
        )
        print(f"{progreso} | Vidas: {vidas} | Puntos: {puntos}")
        origen = "plantilla" if p.fuente == "plantilla" else "dataset"
        print(
            f"Tematica: {p.tematica or '-'} | Materia: {p.materia} | Tipo: {p.tipo} | Origen: {origen}"
        )
        print(f"Curso: {p.curso or '-'} | Semestre: {p.semestre or '-'} | Nivel: {p.nivel or '-'}")
        print(f"Dificultad: {p.dificultad} | Dificultad global: {global_actual}/{max_global}")
        print(f"\n{p.texto}")
        for letra in ("A", "B", "C", "D"):
            print(f"  {letra}) {p.opciones[letra]}")

        respuesta = pedir_opcion("\nTu respuesta: ", ["A", "B", "C", "D"], default="A")
        es_correcta = respuesta == p.correcta
        delta = calcular_puntos(p.dificultad, es_correcta)
        puntos += delta

        if es_correcta:
            aciertos += 1
            print(f"[OK] Correcto (+{delta} puntos)")
        else:
            vidas -= 1
            print(
                f"[X] Incorrecto ({delta} puntos). "
                f"Correcta: {p.correcta}) {p.opciones[p.correcta]}"
            )
            if vidas <= 0:
                print("\nTe has quedado sin vidas. Fin de la partida.")
                break

    print("\n" + "=" * 60)
    print("FIN DE PARTIDA")
    print(f"Jugador: {nombre}")
    print(f"Puntos totales: {puntos}")
    print(f"Aciertos: {aciertos}/{respondidas}")
    guardar_ranking(nombre, puntos, respondidas, aciertos)
    mostrar_top_ranking()


def main() -> None:
    try:
        materias_meta = cargar_materias(PATH_MATERIAS)
        path_plantillas = resolver_plantillas()
    except FileNotFoundError as e:
        print(str(e))
        return

    while True:
        try:
            preguntas, banco = elegir_banco_preguntas(
                PATH_PREGUNTAS, path_plantillas, materias_meta
            )
        except FileNotFoundError as e:
            print(str(e))
            break
        if not preguntas:
            print("No hay preguntas jugables en ese banco.")
            continue
        jugar_partida(preguntas, banco)
        otra = pedir_opcion("\n¿Quieres jugar otra partida? (S/N): ", ["S", "N"], default="N")
        if otra == "N":
            print("¡Gracias por jugar!")
            break


if __name__ == "__main__":
    main()
