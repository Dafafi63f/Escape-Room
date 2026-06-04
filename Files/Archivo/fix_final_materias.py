#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEGACY — deshabilitado (banco cerrado 2026-06-03).

Regeneraba y reclasificaba todo el CSV. No ejecutar.
Ver Memoria_TFG.md §14.4
"""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "Scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Scripts"))

from utils_banco_cerrado import rechazar_mutacion_dataset

rechazar_mutacion_dataset("fix_final_materias.py (legacy)")

from balance_lib import ejecutar_reordenar, ejecutar_validar
from utils_dataset_csv import fila_pregunta, guardar_filas_csv
from utils_texto import normalizar_pregunta

PATH = BASE / "Data" / "Preguntas.csv"
INI = "Iniciació a la Programació"
POO = "Programació Orientada als Objectes"
DEST = "Tècniques de Disseny d'Algoritmes"
FON = "Fonaments de Computadors"
PROG = "Programari de Sistema"
HPC = "Computació i Simulació d'Altes Prestacions"
GRAFS = "Algorítmia i Combinatòria en Grafs. Mètodes Heurístics"
CN = "Càlcul Numèric"
PROB = "Probabilitat"

with PATH.open(encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f, delimiter=";")
    fields = list(reader.fieldnames or [])
    rows = [r for r in reader if "(variante" not in (r.get("Pregunta") or "").lower()]

# Duplicados exactos de enunciado por materia.
for materia in {r.get("Materia") for r in rows}:
    vistos: set[str] = set()
    limpio: list[dict] = []
    for r in rows:
        if r.get("Materia") != materia:
            limpio.append(r)
            continue
        p = (r.get("Pregunta") or "").strip()
        if p in vistos:
            continue
        vistos.add(p)
        limpio.append(r)
    rows = limpio

# Restaurar piezas clave en Tècniques
must_tec = [
    {
        "Pregunta": "¿Qué es un algoritmo?",
        "A": "Secuencia finita de pasos para resolver un problema",
        "B": "Programa",
        "C": "Código",
        "D": "Función",
        "Correcta": "A",
        "Dificultad": "Facil",
        "Tipo": "Teoria",
    },
    {
        "Pregunta": "¿Qué estructura usa LIFO?",
        "A": "Pila",
        "B": "Cola",
        "C": "Lista",
        "D": "Árbol",
        "Correcta": "A",
        "Dificultad": "Dificil",
        "Tipo": "Teoria",
    },
    {
        "Pregunta": "¿Qué es backtracking?",
        "A": "Exploración con vuelta atrás",
        "B": "Voraz",
        "C": "Programación dinámica",
        "D": "Iterativo",
        "Correcta": "A",
        "Dificultad": "Facil",
        "Tipo": "Teoria",
    },
    {
        "Pregunta": "¿En programación dinámica top-down, qué estrategia evita recalcular subproblemas?",
        "A": "Guardar en una tabla o caché los resultados de subproblemas ya resueltos",
        "B": "Rellenar una tabla de abajo arriba iterativamente",
        "C": "Recursión pura sin almacenar resultados",
        "D": "Podar ramas del árbol de búsqueda",
        "Correcta": "A",
        "Dificultad": "Media",
        "Tipo": "Teoria",
    },
]

def _texto_fila(r: dict) -> str:
    return " ".join(
        str(r.get(k, "") or "") for k in ("Pregunta", "A", "B", "C", "D")
    ).lower()


def _es_paralelismo(r: dict) -> bool:
    """Computación/HPC paralela (no geometría «paralelo», ni clustering ML)."""
    pregunta = (r.get("Pregunta") or "").lower()
    if any(k in pregunta for k in ("semáforo", "semaforo", "mutex")):
        return True
    blob = _texto_fila(r)
    if "pipeline" in blob and "paraleliz" not in blob:
        return False
    if ("hilo" in pregunta or " thread" in pregunta or "thread)" in pregunta) and (
        "proceso" in pregunta or "ejecución" in pregunta or "ejecucion" in pregunta
    ):
        return True
    if any(
        x in blob
        for x in (
            "paralelepípedo",
            "paralelos al eje",
            "no son paralelos",
            "paralelismo cuántico",
            "paralelismo cuantico",
            "clustering",
            "k-means",
            "clusters en k",
        )
    ):
        return False
    if "escalabilidad" in blob and "iot" in blob:
        return False
    claves = (
        "speedup",
        "amdahl",
        " mpi ",
        "allreduce",
        "computación paralela",
        "computacion paralela",
        "paralelizable",
        "paraleliz",
        "escalabilidad fuerte",
        "escalabilidad débil",
        "escalabilidad debil",
        "memoria compartida",
        "openmp",
        "fracción secuencial",
        "fraccion secuencial",
        "parte secuencial",
        "ejecución simultánea",
        "ejecucion simultanea",
        "múltiples procesadores",
        "multiples procesadores",
        "paralelizar",
    )
    if any(k in blob for k in claves):
        return True
    if "4 cpus" in blob or ("4 cpu" in blob and "procesos listos" in blob):
        return True
    if "mpi" in blob and any(x in blob for x in ("broadcast", "allreduce", "scatter", "gather")):
        return True
    return False


def _destino_por_contenido(pregunta: str) -> str | None:
    p = (pregunta or "").lower()
    if _es_paralelismo({"Pregunta": pregunta}):
        return HPC
    if "evita recalcular subproblemas" in p:
        return DEST
    if "tflops" in p:
        return FON
    if "operador combina condiciones" in p:
        return INI
    if any(
        x in p
        for x in (
            "redirecci",
            "shell",
            "terminal",
            "touch",
            "cd ..",
            "comando sube",
            "comando crea un archivo",
            "comando lista archivos",
            "stdout",
            "stderr",
            "stdin",
            "git commit",
            "git add",
            "git status",
            "repositorio git",
            "compilador",
            "gcc ",
            "chmod",
            "#!/bin/bash",
            "script de shell",
        )
    ):
        return PROG
    if "pipe" in p and "pipeline" not in p:
        return PROG
    if "proceso" in p and any(
        k in p for k in ("planificación", "planificacion", "quantum", "round-robin", "páginas de", "paginas de")
    ):
        return None
    if "lifo" in p:
        return DEST
    if "1 bit" in p or "representar 1 bit" in p:
        return FON
    if "modelo documento" in p or "modelo documental" in p:
        return "Bases de Dades No Relacionals"
    if any(k in p for k in ("símplice", "simplic", "čech", "cech", "diagrama de persistencia")):
        return "Anàlisi Topològica de Dades"
    if "softmax" in p or "logits" in p:
        return "Xarxes Neuronals i Aprenentatge Profund"
    if "u(x,t)=f(x-ct)" in p.replace(" ", "") or "ecuación de onda" in p:
        return "Equacions en Derivades Parcials"
    if "parámetros en modelo con" in p and "inputs" in p:
        return "Aprenentatge Computacional"
    return None


# Reubicar por contenido (no solo por materia previa)
for r in rows:
    if _es_paralelismo(r):
        r["Materia"] = HPC
        continue
    dest = _destino_por_contenido(r.get("Pregunta") or "")
    if dest:
        r["Materia"] = dest
textos = {(r.get("Materia"), (r.get("Pregunta") or "").strip()) for r in rows}
for m in must_tec:
    if (DEST, m["Pregunta"]) not in textos:
        rows.append({**{k: "" for k in fields}, "Materia": DEST, **m})

# Quitar banquero de Tècniques (es de SO)
rows = [r for r in rows if "banquero" not in (r.get("Pregunta") or "").lower()]

# Mover complejidad que siga en POO
for r in rows:
    p = (r.get("Pregunta") or "").lower()
    if r.get("Materia") == POO and ("complejidad" in p or "lista no ordenada" in p):
        r["Materia"] = DEST

# Iniciació: solo Python (quitar algoritmo si quedó)
for r in rows:
    if r.get("Materia") == INI and (r.get("Pregunta") or "").startswith("¿Qué es un algoritmo"):
        r["Materia"] = DEST

from collections import Counter

fillers_extra = {
    "Càlcul en Diverses Variables": fila_pregunta(
        id_=0,
        materia="Càlcul en Diverses Variables",
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Cuál es el Jacobiano de x=r·cos(theta) y=r·sen(theta)?",
        a="r",
        b="r²",
        c="1",
        d="r/2",
        correcta="A",
    ),
}

def _count(m: str) -> int:
    return sum(1 for r in rows if r.get("Materia") == m)


def _tiene_pregunta(materia: str, texto: str, *, parcial: bool = False) -> bool:
    """Comprueba si la materia ya tiene ese enunciado (normalizado).

    parcial=True: texto es un fragmento del enunciado (p. ej. «pipeline ideal de 5 etapas»).
    """
    ref = normalizar_pregunta(texto)
    if not ref:
        return False
    for r in rows:
        if r.get("Materia") != materia:
            continue
        p = normalizar_pregunta(r.get("Pregunta") or "")
        if parcial:
            if ref in p:
                return True
        elif p == ref:
            return True
    return False


def _balance_tipo(materia: str, teoria_obj: int = 5, calculo_obj: int = 5) -> None:
    sub = [r for r in rows if r.get("Materia") == materia]
    t = sum(1 for r in sub if r.get("Tipo") == "Teoria")
    c = len(sub) - t
    while t > teoria_obj:
        for r in sub:
            if r.get("Tipo") != "Teoria":
                continue
            if "cohesión" in (r.get("Pregunta") or "").lower():
                r["Tipo"] = "Calculo"
                t -= 1
                c += 1
                break
        else:
            for r in sub:
                if r.get("Tipo") == "Teoria":
                    r["Tipo"] = "Calculo"
                    t -= 1
                    c += 1
                    break
            else:
                break
    while c > calculo_obj:
        for r in sub:
            if r.get("Tipo") == "Calculo" and "new X" in (r.get("Pregunta") or ""):
                r["Tipo"] = "Teoria"
                c -= 1
                t += 1
                break
        else:
            break
    while t < teoria_obj:
        for r in sub:
            if r.get("Tipo") != "Calculo":
                continue
            if any(
                k in (r.get("Pregunta") or "").lower()
                for k in ("complejidad", "algoritmo", "backtracking", "voraz", "lifo")
            ):
                r["Tipo"] = "Teoria"
                t += 1
                c -= 1
                break
        else:
            break


for materia in (INI, POO, DEST, FON, PROG, "Càlcul en Diverses Variables"):
    while _count(materia) > 10:
        for r in reversed(rows):
            if r.get("Materia") != materia:
                continue
            if materia == DEST and "1111 en binario" in (r.get("Pregunta") or ""):
                rows.remove(r)
                break
            if materia == DEST and "operador combina condiciones" in (r.get("Pregunta") or ""):
                rows.remove(r)
                break
            if materia == DEST and "tflops" in (r.get("Pregunta") or "").lower():
                rows.remove(r)
                break
            if materia == INI and (r.get("Pregunta") or "").startswith("¿Qué es un bucle while"):
                if _count(INI) > 10:
                    rows.remove(r)
                    break
            if materia == INI and "retorno 10%" in (r.get("Pregunta") or "").lower():
                rows.remove(r)
                break
            if materia == POO and "constructores puede tener" in (r.get("Pregunta") or ""):
                if sum(
                    1
                    for x in rows
                    if x.get("Materia") == POO and "constructores puede tener" in (x.get("Pregunta") or "")
                ) > 1:
                    rows.remove(r)
                    break
            if materia == FON and "latencia típica red local" in (r.get("Pregunta") or "").lower():
                rows.remove(r)
                break
            if materia == PROG and (
                "página de 4kb" in (r.get("Pregunta") or "").lower()
                or "pipeline ideal de 5 etapas" in (r.get("Pregunta") or "").lower()
            ):
                r["Materia"] = FON
                break
            if materia == HPC and _count(HPC) > 10:
                pl = (r.get("Pregunta") or "").lower()
                if "speedup 4 con 8 procesadores" in pl:
                    rows.remove(r)
                    break
                if pl.startswith("¿qué es la computación paralela"):
                    rows.remove(r)
                    break
                if "escalabilidad fuerte" in pl:
                    rows.remove(r)
                    break
            if materia == PROG and (
                "4 cpus" in (r.get("Pregunta") or "").lower()
                or "pipeline ideal" in (r.get("Pregunta") or "").lower()
            ):
                if "pipeline ideal" in (r.get("Pregunta") or "").lower():
                    r["Materia"] = FON
                else:
                    rows.remove(r)
                break
            if materia == FON and "tflops" in (r.get("Pregunta") or "").lower():
                if _tiene_pregunta(FON, "pipeline ideal de 5 etapas", parcial=True):
                    rows.remove(r)
                    break
            if materia == DEST and "complejidad de búsqueda binaria" in (r.get("Pregunta") or "").lower():
                if sum(
                    1
                    for x in rows
                    if x.get("Materia") == DEST
                    and "búsqueda binaria" in (x.get("Pregunta") or "").lower()
                ) > 1:
                    rows.remove(r)
                    break
            rows.remove(r)
            break

_ini_fillers = [
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es un bucle while?",
        a="Itera mientras condición sea verdadera",
        b="Itera n veces",
        c="Itera sobre lista",
        d="No existe",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué es un bucle for?",
        a="Iteración sobre secuencia o rango",
        b="Condicional",
        c="Función",
        d="Clase",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Qué es el scope de una variable?",
        a="Ámbito donde es visible",
        b="Tipo de dato",
        c="Valor inicial",
        d="Nombre",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="¿Cómo se define el operador módulo %?",
        a="Potencia",
        b="Resto de la división entera",
        c="División",
        d="Multiplicación",
        correcta="B",
    ),
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Qué es una función?",
        a="Bloque reutilizable que realiza una tarea",
        b="Variable",
        c="Bucle",
        d="Array",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es un condicional if?",
        a="Ejecuta código si condición es verdadera",
        b="Bucle",
        c="Función",
        d="Asignación",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=INI,
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Qué operador combina condiciones (y)?",
        a="OR",
        b="NOT",
        c="AND",
        d="XOR",
        correcta="C",
    ),
]
_hpc_fillers = [
    fila_pregunta(
        id_=0,
        materia=HPC,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es un semáforo?",
        a="Variable entera para sincronización entre procesos",
        b="Tipo de cola de mensajes",
        c="Planificador de CPU",
        d="Página de memoria",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=HPC,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Qué es un mutex?",
        a="Mecanismo de exclusión mutua",
        b="Cola de mensajes",
        c="Planificador",
        d="Página de memoria",
        correcta="A",
    ),
]
_prog_banco_terminal = [
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es un shell en Unix/Linux?",
        a="Interfaz que interpreta y ejecuta comandos del usuario",
        b="El núcleo del sistema operativo",
        c="Un compilador de C",
        d="Un gestor de paquetes",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es la salida estándar (stdout)?",
        a="Flujo donde un programa escribe su salida normal",
        b="La entrada del teclado",
        c="Solo mensajes de error",
        d="Un archivo fijo en /tmp",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué hace el operador de tubería (pipe) `|` en una shell tipo Unix?",
        a="Conecta la salida estándar de un comando con la entrada estándar del siguiente",
        b="Crea siempre un archivo temporal en disco",
        c="Ejecuta el segundo comando antes que el primero",
        d="Duplica la entrada estándar al error estándar",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué hace `git commit` en un repositorio local?",
        a="Registra una instantánea de los cambios preparados en el historial",
        b="Sube automáticamente al servidor remoto",
        c="Borra los cambios no guardados",
        d="Crea siempre una rama nueva",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué es un compilador?",
        a="Programa que traduce código fuente a código objeto o ejecutable",
        b="Programa que ejecuta el código línea a línea sin traducir",
        c="El intérprete de comandos del sistema",
        d="Una herramienta para clonar repositorios",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Qué comando sube un nivel de directorio?",
        a="cd ..",
        b="cd /",
        c="cd -",
        d="cd up",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Qué comando crea un archivo vacío?",
        a="mkfile",
        b="new",
        c="create",
        d="touch",
        correcta="D",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Qué comando lista archivos incluyendo ocultos?",
        a="ls",
        b="ls -a",
        c="dir",
        d="ls -l",
        correcta="B",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Media",
        tipo="Calculo",
        pregunta="Si en un directorio hay 5 archivos y ejecutas `ls | wc -l`, ¿qué número imprime wc -l?",
        a="5",
        b="1",
        c="0",
        d="10",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROG,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="Tras `gcc main.c -o ejecutable`, ¿cómo se llama el binario generado?",
        a="ejecutable",
        b="main.c",
        c="gcc",
        d="a.out siempre",
        correcta="A",
    ),
]
_prog_fillers = list(_prog_banco_terminal)


def _sustituir_bloque_programari() -> None:
    rows[:] = [r for r in rows if r.get("Materia") != PROG]
    for f in _prog_banco_terminal:
        rows.append({**{k: "" for k in fields}, **f})


_sustituir_bloque_programari()

_grafs_banco = [
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es un grafo completo K_n?",
        a="Todos los vértices están conectados entre sí",
        b="Un grafo sin aristas",
        c="Un árbol con raíz",
        d="Un grafo bipartito siempre",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es un árbol en teoría de grafos?",
        a="Grafo conexo sin ciclos",
        b="Grafo completo",
        c="Grafo con exactamente un ciclo por vértice",
        d="Grafo bipartito con raíz",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué es un grafo euleriano?",
        a="Grafo con un circuito que recorre cada arista exactamente una vez",
        b="Grafo completo",
        c="Árbol de expansión mínima",
        d="Grafo bipartito con matching perfecto",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué condición necesita un grafo conexo para tener un circuito euleriano?",
        a="Todos los vértices tienen grado par",
        b="Exactamente dos vértices tienen grado impar",
        c="Es bipartito",
        d="Tiene al menos un ciclo hamiltoniano",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="En un grafo bipartito con partición (X, Y), ¿qué acota el tamaño del matching máximo?",
        a="min(|X|, |Y|)",
        b="max(|X|, |Y|)",
        c="|X| + |Y|",
        d="|E|",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Cuál es el grado de un vértice en el grafo completo K5?",
        a="4",
        b="5",
        c="10",
        d="20",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Cuántas aristas tiene el grafo completo K5?",
        a="4",
        b="5",
        c="10",
        d="20",
        correcta="C",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Media",
        tipo="Calculo",
        pregunta="Grafo acíclico con 10 vértices y 7 aristas. ¿Cuántas componentes conexas?",
        a="1",
        b="3",
        c="2",
        d="4",
        correcta="B",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Cuántos caminos de longitud 2 hay en el grafo completo K4?",
        a="6",
        b="4",
        c="12",
        d="16",
        correcta="C",
    ),
    fila_pregunta(
        id_=0,
        materia=GRAFS,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="Grafo acíclico con 10 vértices y 4 aristas. ¿Cuántas componentes conexas?",
        a="1",
        b="5",
        c="6",
        d="No está determinado",
        correcta="C",
    ),
]


def _sustituir_bloque_grafs() -> None:
    rows[:] = [r for r in rows if r.get("Materia") != GRAFS]
    for f in _grafs_banco:
        rows.append({**{k: "" for k in fields}, **f})


_sustituir_bloque_grafs()

_calc_num_teoria = [
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es la regla del trapecio?",
        a="Aproximación de integral por trapecios",
        b="Método de Simpson",
        c="Monte Carlo",
        d="Cuadratura de Gauss",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es el error de redondeo?",
        a="Error por precisión finita de coma flotante",
        b="Error de truncamiento",
        c="Error de modelo",
        d="Error de medición",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué es un punto fijo de y'=f(y)?",
        a="Valor y donde f(y)=0",
        b="Donde y'=1",
        c="Máximo local",
        d="Mínimo local",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué es el método de Newton-Raphson?",
        a="Método iterativo que usa f(x) y f'(x) para aproximar una raíz de f(x)=0",
        b="Integración numérica por trapecios",
        c="Resolución directa de sistemas lineales",
        d="Búsqueda de raíz dividiendo un intervalo a la mitad",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué es el orden de convergencia?",
        a="Tasa con la que el error decrece al refinar el paso o las iteraciones",
        b="Número de evaluaciones de f",
        c="Estabilidad del método",
        d="Consistencia del esquema",
        correcta="A",
    ),
]

_calc_num_calculo = [
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="Si el valor real es 10 y la aproximación es 11, ¿cuál es el error relativo?",
        a="0,1",
        b="1",
        c="0,01",
        d="10",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="Newton-Raphson para f(x)=x²−2 con x₀=1. ¿Cuál es x₁?",
        a="1",
        b="1,5",
        c="2",
        d="0,5",
        correcta="B",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Cuántas iteraciones de bisección en [0,1] se necesitan para error < 0,001?",
        a="10",
        b="9",
        c="11",
        d="8",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="Regla de Simpson para ∫₀¹ x² dx con 2 subintervalos. ¿Resultado?",
        a="1/3",
        b="1/2",
        c="1/4",
        d="1",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=CN,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="Si f es C² en [a,b], ¿cómo escala usualmente el error global de la regla del trapecio compuesto con paso h=(b-a)/n?",
        a="O(h³)",
        b="O(h)",
        c="O(1/h)",
        d="O(h²)",
        correcta="D",
    ),
]


def _sustituir_bloque_cn() -> None:
    rows[:] = [r for r in rows if r.get("Materia") != CN]
    for f in _calc_num_teoria + _calc_num_calculo:
        rows.append({**{k: "" for k in fields}, **f})


_sustituir_bloque_cn()

_prob_banco = [
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es la esperanza E(X)?",
        a="Media (valor medio) de la distribución de X",
        b="Medida de dispersión de X",
        c="Valor más probable de X",
        d="Mediana de X",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Cuándo son independientes dos eventos A y B?",
        a="Si P(A∩B)=P(A)·P(B)",
        b="Si P(A|B)=P(B|A)",
        c="Si P(A)+P(B)=1",
        d="Si P(A∪B)=P(A)+P(B)",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Media",
        tipo="Teoria",
        pregunta="Si P(B)>0, ¿qué expresa P(A|B)=P(A∩B)/P(B)?",
        a="Definición de probabilidad condicional",
        b="Regla de la multiplicación",
        c="Ley de probabilidad total",
        d="Definición de independencia",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Cuál es la fórmula de la probabilidad de la unión P(A∪B)?",
        a="P(A)+P(B)−P(A∩B)",
        b="P(A)+P(B)",
        c="P(A)·P(B)",
        d="P(A)−P(B)",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="Si A₁,…,Aₙ forman una partición del espacio muestral, ¿cómo se expresa P(B)?",
        a="Σᵢ P(B|Aᵢ)·P(Aᵢ) (ley de probabilidad total)",
        b="P(B|A₁) únicamente",
        c="P(A₁)+P(A₂)",
        d="P(B)·P(Aᵢ)",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="¿Cuál es la varianza de la variable aleatoria constante X=5?",
        a="0",
        b="5",
        c="25",
        d="1",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="Si X sigue Binomial(n=5, p=0,5), ¿cuál es E(X)?",
        a="2",
        b="5",
        c="1,25",
        d="2,5",
        correcta="D",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Media",
        tipo="Calculo",
        pregunta="Si X~Poisson con λ=2, ¿cuál es P(X=0)?",
        a="0",
        b="e^(-2)",
        c="1−e^(-2)",
        d="2",
        correcta="B",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Media",
        tipo="Calculo",
        pregunta="Con una moneda justa, ¿cuál es P(obtener 2 caras en 2 lanzamientos)?",
        a="0,25",
        b="0,5",
        c="1",
        d="0",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=PROB,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="Si P(A)=0,1, P(B|A)=0,9 y P(B)=0,5, ¿cuál es P(A|B) según el teorema de Bayes?",
        a="0,18",
        b="0,9",
        c="0,05",
        d="0,5",
        correcta="A",
    ),
]


def _sustituir_bloque_prob() -> None:
    rows[:] = [r for r in rows if r.get("Materia") != PROB]
    for f in _prob_banco:
        rows.append({**{k: "" for k in fields}, **f})


_sustituir_bloque_prob()

_poo_banco = [
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es la herencia?",
        a="Una subclase hereda atributos y métodos de una superclase",
        b="Ocultar datos internos",
        c="Sustituir una implementación por otra",
        d="Definir varios métodos con el mismo nombre",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es el encapsulamiento?",
        a="Ocultar el estado interno y exponer una interfaz controlada",
        b="Herencia múltiple",
        c="Crear instancias sin constructor",
        d="Importar módulos",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué es el polimorfismo?",
        a="La misma interfaz con distintas implementaciones",
        b="Copiar código entre clases",
        c="Ejecutar código en paralelo",
        d="Compilar a bytecode",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué es el acoplamiento en diseño de software?",
        a="Grado de dependencia entre módulos o clases",
        b="Número de métodos públicos",
        c="Tamaño de la jerarquía de herencia",
        d="Uso de tipado estático",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué es la cohesión en diseño de software?",
        a="Grado en que los elementos de un módulo pertenecen juntos",
        b="Herencia entre clases",
        c="Número de instancias creadas",
        d="Velocidad de ejecución",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="En Python, si C es una clase, ¿cuántas instancias crea la expresión C()?",
        a="1",
        b="0",
        c="2",
        d="Depende del nombre de la clase",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Facil",
        tipo="Calculo",
        pregunta="En Python, en def metodo(self, x), ¿cuántos argumentos debe pasar el llamador (sin contar self)?",
        a="1",
        b="2",
        c="0",
        d="self",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Media",
        tipo="Calculo",
        pregunta="En Python, si a=Foo() y b=Foo() con la misma clase Foo, ¿es cierto a is b?",
        a="No",
        b="Sí",
        c="Solo si Foo tiene __slots__",
        d="Solo en Python 2",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Media",
        tipo="Calculo",
        pregunta="En Python, class C: def __init__(self): self.v=1. Tras c=C(), ¿cuál es c.v?",
        a="1",
        b="0",
        c="Ninguno",
        d="Error",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="En Python, ¿cuántas definiciones efectivas de __init__ puede tener una misma clase?",
        a="Una (la última definida sobrescribe las anteriores)",
        b="Tantas como métodos heredados",
        c="Ilimitadas simultáneas",
        d="Ninguna",
        correcta="A",
    ),
]


def _sustituir_bloque_poo() -> None:
    rows[:] = [r for r in rows if r.get("Materia") != POO]
    for f in _poo_banco:
        rows.append({**{k: "" for k in fields}, **f})


_sustituir_bloque_poo()

_poo_fillers = [
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Media",
        tipo="Teoria",
        pregunta="¿Qué es el encapsulamiento?",
        a="Ocultar datos internos",
        b="Herencia",
        c="Polimorfismo",
        d="Abstracción",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué es el polimorfismo?",
        a="Mismo interfaz, distinto comportamiento",
        b="Herencia",
        c="Abstracción",
        d="Encapsulación",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=POO,
        dificultad="Facil",
        tipo="Teoria",
        pregunta="¿Qué es una interfaz?",
        a="Contrato de métodos a implementar",
        b="Clase abstracta",
        c="Herencia",
        d="Composición",
        correcta="A",
    ),
]

_fon_fillers = [
    fila_pregunta(
        id_=0,
        materia=FON,
        dificultad="Media",
        tipo="Calculo",
        pregunta="¿Cuántos valores puede representar 1 bit?",
        a="8",
        b="0",
        c="2",
        d="1",
        correcta="C",
    ),
    fila_pregunta(
        id_=0,
        materia=FON,
        dificultad="Dificil",
        tipo="Calculo",
        pregunta="1 TFLOPS ejecutar 10^12 operaciones ¿tiempo?",
        a="1",
        b="10",
        c="0.1",
        d="1 s",
        correcta="D",
    ),
]

while _count(FON) < 10:
    added = False
    for f in _fon_fillers:
        if _tiene_pregunta(FON, f["Pregunta"]):
            continue
        rows.append(f)
        added = True
        break
    if not added:
        break

while _count(INI) < 10:
    added = False
    for f in _ini_fillers:
        if _tiene_pregunta(INI, f["Pregunta"]):
            continue
        rows.append(f)
        added = True
        break
    if not added:
        break

while _count(PROG) < 10:
    added = False
    for f in _prog_fillers:
        if _tiene_pregunta(PROG, f["Pregunta"]):
            continue
        rows.append(f)
        added = True
        break
    if not added:
        break

while _count(HPC) < 10:
    added = False
    for f in _hpc_fillers:
        if _tiene_pregunta(HPC, f["Pregunta"]):
            continue
        rows.append(f)
        added = True
        break
    if not added:
        break

while _count(POO) < 10:
    added = False
    for f in _poo_fillers:
        if _tiene_pregunta(POO, f["Pregunta"]):
            continue
        rows.append(f)
        added = True
        break
    if not added:
        break

_tec_fillers = [
    fila_pregunta(
        id_=0,
        materia=DEST,
        dificultad="Dificil",
        tipo="Teoria",
        pregunta="¿Qué estructura usa LIFO?",
        a="Pila",
        b="Cola",
        c="Lista",
        d="Árbol",
        correcta="A",
    ),
    fila_pregunta(
        id_=0,
        materia=DEST,
        dificultad="Media",
        tipo="Teoria",
        pregunta="Complejidad búsqueda en lista no ordenada de n elementos?",
        a="O(n)",
        b="O(log n)",
        c="O(1)",
        d="O(n²)",
        correcta="A",
    ),
]
while _count(DEST) < 10:
    added = False
    for m in must_tec:
        if not _tiene_pregunta(DEST, m["Pregunta"]):
            rows.append({**{k: "" for k in fields}, "Materia": DEST, **m})
            added = True
            break
    if not added:
        for f in _tec_fillers:
            if _tiene_pregunta(DEST, f["Pregunta"]):
                continue
            rows.append(f)
            added = True
            break
    if not added:
        break

while _count("Càlcul en Diverses Variables") < 10:
    extra = fillers_extra["Càlcul en Diverses Variables"]
    rows.append({**{k: "" for k in fields}, **extra})

# Càlcul DV: equilibrar 5 Teoria / 5 Calculo
cdv = [r for r in rows if r.get("Materia") == "Càlcul en Diverses Variables"]
t = sum(1 for r in cdv if r.get("Tipo") == "Teoria")
while t < 5:
    for r in cdv:
        if r.get("Tipo") == "Calculo" and "gradiente" in (r.get("Pregunta") or "").lower():
            r["Tipo"] = "Teoria"
            t += 1
            break
    else:
        break
while t > 5:
    for r in cdv:
        if r.get("Tipo") == "Teoria" and "(variante" in (r.get("Pregunta") or ""):
            r["Tipo"] = "Calculo"
            t -= 1
            break
    else:
        break

_materias = sorted({r.get("Materia") for r in rows})
for _ in range(500):
    if len(rows) == 480 and all(_count(m) == 12 for m in _materias):
        break
    over = [m for m in _materias if _count(m) > 10]
    under = [m for m in _materias if _count(m) < 10]
    if over:
        m = over[0]
        for r in reversed(rows):
            if r.get("Materia") == m:
                rows.remove(r)
                break
        continue
    if under:
        m = under[0]
        if m == POO:
            for f in _poo_fillers:
                if not _tiene_pregunta(POO, f["Pregunta"]):
                    rows.append(f)
                    break
            else:
                break
        elif m == INI:
            for f in _ini_fillers:
                if not _tiene_pregunta(INI, f["Pregunta"]):
                    rows.append(f)
                    break
            else:
                break
        elif m == PROG:
            for f in _prog_fillers:
                if not _tiene_pregunta(PROG, f["Pregunta"]):
                    rows.append(f)
                    break
            else:
                break
        elif m == HPC:
            for f in _hpc_fillers:
                if not _tiene_pregunta(HPC, f["Pregunta"]):
                    rows.append(f)
                    break
            else:
                break
        elif m == DEST:
            for mdef in must_tec + _tec_fillers:
                pregunta = mdef.get("Pregunta") or mdef.get("pregunta")
                if pregunta and not _tiene_pregunta(DEST, pregunta):
                    if "Materia" not in mdef:
                        rows.append({**{k: "" for k in fields}, "Materia": DEST, **mdef})
                    else:
                        rows.append(mdef)
                    break
            else:
                break
        else:
            break
    elif len(rows) > 480:
        rows.pop()
    else:
        break

for materia in {r.get("Materia") for r in rows}:
    if _count(materia) == 12:
        _balance_tipo(materia)

for i, r in enumerate(rows, start=1):
    r["Id"] = str(i)

guardar_filas_csv(fields, rows, PATH)
rc = ejecutar_reordenar(solo_metadatos=True, sin_permutar_respuestas=True)
print("reordenar", rc)
raise SystemExit(ejecutar_validar(detalle=False, estricto=False))
