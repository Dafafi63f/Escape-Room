# -*- coding: utf-8 -*-
"""
Variedad temática del banco: análisis, diversificación automática y parches curados.

  python Files/variedad_materias.py analizar
  python Files/variedad_materias.py diversificar [--dry-run] [--umbral 0.38]
  python Files/variedad_materias.py curado
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"
LETTERS = "ABCD"

sys.path.insert(0, str(BASE / "Files"))
from utils_variedad import (  # noqa: E402
    UMBRAL_INFORME,
    agrupar_por_materia,
    jaccard,
    palabras_frecuentes_por_materia,
    pares_similares_en_materia,
    stem_words,
)

# --- diversificar (constantes) ---
UMBRAL_DIVERSIFICAR = 0.38
MAX_POR_MATERIA = 5
MAX_SIM_GRUPO = 0.24
SKIP_MATERIAS = {"Visualització 3D"}
UMBRAL_SUSTITUCION = 0.42

# --- curado (parches por Id) ---
PARCHES: dict[int, dict[str, str]] = {
    51: {
        "Pregunta": "¿Qué es una heurística en optimización sobre grafos?",
        "A": "Algoritmo que siempre encuentra el óptimo global",
        "B": "Regla que solo aplica a árboles",
        "C": "Criterio práctico que busca buenas soluciones sin garantizar el óptimo",
        "D": "Medida del grado medio del grafo",
        "Correcta": "C",
    },
    53: {
        "Pregunta": "¿Qué papel tiene la función heurística h(n) en el algoritmo A*?",
        "A": "Estima el coste restante hasta la meta para guiar la expansión",
        "B": "Garantiza optimalidad aunque h sea arbitraria",
        "C": "Sustituye el coste acumulado g(n) desde el origen",
        "D": "Solo se aplica en grafos no ponderados",
        "Correcta": "A",
    },
    56: {
        "Pregunta": "¿Cuántos árboles de expansión (spanning trees) tiene el grafo completo K3?",
        "A": "1",
        "B": "2",
        "C": "4",
        "D": "3",
        "Correcta": "D",
    },
    57: {
        "Pregunta": "¿Cuántas aristas tiene el grafo completo K4?",
        "A": "6",
        "B": "4",
        "C": "5",
        "D": "3",
        "Correcta": "A",
    },
    59: {
        "Pregunta": "En A*, si para un nodo n se tiene g(n)=5 y h(n)=2, ¿cuál es f(n)=g(n)+h(n)?",
        "A": "3",
        "B": "10",
        "C": "7",
        "D": "2",
        "Correcta": "C",
    },
    60: {
        "Pregunta": "¿Qué calcula el algoritmo de Dijkstra desde un vértice origen s (pesos no negativos)?",
        "A": "Un matching bipartito máximo",
        "B": "Distancias mínimas entre todos los pares de vértices",
        "C": "Un ciclo hamiltoniano",
        "D": "Las distancias mínimas desde s hasta cada vértice alcanzable",
        "Correcta": "D",
    },
    20: {
        "Pregunta": "¿Cuál es el radio de convergencia de la serie Σ_{n=0}^∞ x^n?",
        "A": "0",
        "B": "2",
        "C": "∞",
        "D": "1",
        "Correcta": "D",
    },
    114: {
        "Pregunta": "¿Qué garantiza el teorema de existencia y unicidad (Picard-Lindelöf) para y'=f(t,y)?",
        "A": "Existencia sin condiciones sobre f",
        "B": "Existencia y unicidad local si f es continua y Lipschitz en y",
        "C": "Solución global obligatoria para cualquier f",
        "D": "Solo aplica a EDO lineales con coeficientes constantes",
        "Correcta": "B",
    },
    116: {
        "Pregunta": "¿Cuál es la solución general de y''-4y=0?",
        "A": "C1 cos(2x)+C2 sin(2x)",
        "B": "C1+C2 x",
        "C": "C1 e^{2x}+C2 e^{-2x}",
        "D": "e^{4x}",
        "Correcta": "C",
    },
    171: {
        "Pregunta": "¿Para qué sirve el test de Turing en IA?",
        "A": "Medir la velocidad del procesador",
        "B": "Demostrar teoremas de primer orden",
        "C": "Evaluar si el comportamiento es indistinguible del humano en conversación",
        "D": "Calcular la complejidad espacial de BFS",
        "Correcta": "C",
    },
    173: {
        "Pregunta": "¿Qué caracteriza la búsqueda no informada (p. ej. BFS o DFS)?",
        "A": "No usa heurística de dominio h(n) para estimar coste a la meta",
        "B": "Siempre requiere h(n) admisible",
        "C": "Solo aplica a juegos con MIN y MAX",
        "D": "Equivale a hill climbing",
        "Correcta": "A",
    },
    174: {
        "Pregunta": "En búsqueda local (p. ej. hill climbing), ¿qué vecino se elige habitualmente?",
        "A": "El que más empeora la función objetivo",
        "B": "Uno que mejora (o no empeora) la función objetivo",
        "C": "El que minimiza la utilidad en un nodo MIN",
        "D": "El primero del grafo en orden alfabético siempre",
        "Correcta": "B",
    },
    175: {
        "Pregunta": "En minimax para dos jugadores, ¿qué hace el nivel MAX?",
        "A": "Minimiza la utilidad asumiendo un oponente óptimo",
        "B": "Elige siempre la primera jugada alfabética",
        "C": "Maximiza la utilidad propia asumiendo que el oponente (MIN) juega óptimo",
        "D": "Aplica solo BFS por niveles",
        "Correcta": "C",
    },
    172: {
        "Pregunta": "En búsqueda informada, ¿qué significa que la heurística h sea admisible?",
        "A": "Sobreestima siempre el coste hasta la meta",
        "B": "No usa estimación del coste restante",
        "C": "Solo aplica en búsqueda local",
        "D": "No sobreestima el coste real óptimo hasta la meta",
        "Correcta": "D",
    },
    176: {
        "Pregunta": "En clasificación binaria, con TP=8 y FN=2, ¿cuál es el recall TP/(TP+FN)?",
        "A": "0,2",
        "B": "1",
        "C": "0,5",
        "D": "0,8",
        "Correcta": "D",
    },
    177: {
        "Pregunta": "¿Cuántas hojas tiene un árbol binario completo de profundidad 3?",
        "A": "8",
        "B": "3",
        "C": "6",
        "D": "16",
        "Correcta": "A",
    },
    178: {
        "Pregunta": "En clasificación, con 90 aciertos de 100 casos, ¿cuál es la accuracy?",
        "A": "0,1",
        "B": "0,9",
        "C": "9",
        "D": "0,09",
        "Correcta": "B",
    },
    179: {
        "Pregunta": "En minimax, un nodo MIN tiene hijos con utilidades 9, 4 y 7. ¿Qué valor propaga hacia arriba?",
        "A": "9",
        "B": "7",
        "C": "4",
        "D": "20",
        "Correcta": "C",
    },
    180: {
        "Pregunta": "En lógica proposicional, con P=0 y Q=1, ¿valor de P∧Q?",
        "A": "1",
        "B": "2",
        "C": "Indeterminado",
        "D": "0",
        "Correcta": "D",
    },
    191: {
        "Pregunta": "En el método de Newton para minimizar f(x), ¿qué información usa en cada iteración?",
        "A": "Solo valores de f sin derivadas",
        "B": "Solo el signo de f",
        "C": "La primera y segunda derivada (f' y f'')",
        "D": "Solo restricciones lineales del dual",
        "Correcta": "C",
    },
    192: {
        "Pregunta": "Si f es estrictamente convexa, ¿cuántos minimizadores globales puede tener?",
        "A": "Infinitos",
        "B": "Ninguno",
        "C": "Dos como mínimo",
        "D": "Como máximo uno",
        "Correcta": "D",
    },
    193: {
        "Pregunta": "En programación lineal, ¿qué método recorre vértices del politopo factible?",
        "A": "Simplex",
        "B": "Eliminación gaussiana de series de Fourier",
        "C": "Quicksort",
        "D": "Backpropagation",
        "Correcta": "A",
    },
    247: {
        "Pregunta": "En teoría de la información, ¿qué es la capacidad de canal?",
        "A": "Entropía de la fuente únicamente",
        "B": "Número de símbolos del alfabeto",
        "C": "Tasa máxima transmisible con error arbitrariamente pequeño",
        "D": "Longitud del mensaje en bytes",
        "Correcta": "C",
    },
    250: {
        "Pregunta": "¿Qué mide la información mutua I(X;Y)?",
        "A": "Cuánto reduce conocer Y la incertidumbre sobre X",
        "B": "Solo la entropía marginal H(X)",
        "C": "La latencia de red",
        "D": "El tamaño del alfabeto",
        "Correcta": "A",
    },
    267: {
        "Pregunta": "¿Qué establece el teorema de no-clonación?",
        "A": "Cualquier estado cuántico puede copiarse perfectamente",
        "B": "Solo aplica a qubits en estado |0⟩",
        "C": "No existe procedimiento universal que clone un estado desconocido",
        "D": "Equivale a la codificación Huffman",
        "Correcta": "C",
    },
    268: {
        "Pregunta": "En un sistema de n qubits, ¿cuántas amplitudes complejas hay en la base computacional?",
        "A": "n",
        "B": "2n",
        "C": "n²",
        "D": "2^n",
        "Correcta": "D",
    },
    303: {
        "Pregunta": "¿Qué mide el coeficiente beta de un activo financiero?",
        "A": "Exceso de rentabilidad por unidad de volatilidad",
        "B": "Sensibilidad de la rentabilidad del activo respecto al mercado",
        "C": "Probabilidad de default anual",
        "D": "Dividendo por acción",
        "Correcta": "B",
    },
    320: {
        "Pregunta": "¿Cuántos parámetros autoregresivos tiene un modelo AR(2)?",
        "A": "0",
        "B": "1",
        "C": "3",
        "D": "2",
        "Correcta": "D",
    },
    326: {
        "Pregunta": "En homología persistente, ¿qué cuenta habitualmente el número de Betti β₀?",
        "A": "Componentes conexas",
        "B": "Túneles de dimensión 1",
        "C": "Cavidades tridimensionales",
        "D": "Puntos en el infinito",
        "Correcta": "A",
    },
    349: {
        "Pregunta": "¿Qué es el odds ratio (razón de momios) en epidemiología?",
        "A": "Cociente de odds entre expuestos y no expuestos",
        "B": "Igual al NNT siempre",
        "C": "La especificidad del test",
        "D": "El intervalo de confianza del 95% obligatoriamente",
        "Correcta": "A",
    },
    358: {
        "Pregunta": "Con paralaje p=0,01 arcsec (10 mas), ¿distancia aproximada en pc (d≈1/p)?",
        "A": "1",
        "B": "10",
        "C": "100",
        "D": "1000",
        "Correcta": "C",
    },
    370: {
        "Pregunta": "¿Cuántos codones distintos codifica el código genético estándar?",
        "A": "64",
        "B": "20",
        "C": "4",
        "D": "61",
        "Correcta": "A",
    },
    63: {
        "Pregunta": "¿Qué es un punto crítico de f(x,y) en cálculo multivariable?",
        "A": "Punto donde el gradiente se anula o no existe",
        "B": "Punto del borde del dominio siempre",
        "C": "Punto con curvatura gaussiana máxima",
        "D": "Punto donde f es discontinua",
        "Correcta": "A",
    },
    73: {
        "Pregunta": "¿Qué es el error de truncamiento en métodos numéricos?",
        "A": "Error al aproximar el problema continuo (p. ej. truncar una serie o discretizar)",
        "B": "Error por la precisión finita de coma flotante",
        "C": "Error de medición en el laboratorio",
        "D": "Error debido solo al número de iteraciones de Newton",
        "Correcta": "A",
    },
    76: {
        "Pregunta": "Si el valor real es 10 y la aproximación es 11, ¿cuál es el error relativo |real−aprox|/|real|?",
        "A": "1",
        "B": "0,01",
        "C": "10",
        "D": "0,1",
        "Correcta": "D",
    },
    77: {
        "Pregunta": "Un paso de Newton-Raphson para f(x)=x²−2 con x₀=1 (f(1)=−1, f'(1)=2). ¿x₁?",
        "A": "1,5",
        "B": "2",
        "C": "1",
        "D": "0,5",
        "Correcta": "A",
    },
    78: {
        "Pregunta": "¿Cuántas iteraciones de bisección en [0,1] se necesitan para error < 0,001?",
        "A": "9",
        "B": "10",
        "C": "11",
        "D": "8",
        "Correcta": "B",
    },
    79: {
        "Pregunta": "Regla de Simpson para ∫₀¹ x² dx con 2 subintervalos. ¿Resultado?",
        "A": "1/2",
        "B": "1/4",
        "C": "1/3",
        "D": "1",
        "Correcta": "C",
    },
    75: {
        "Pregunta": "¿En qué se basa el método de Romberg para integración numérica?",
        "A": "Solo un paso de Simpson",
        "B": "Extrapolación de Richardson a partir de refinamientos del trapecio",
        "C": "Únicamente cuadratura de Gauss",
        "D": "Muestreo aleatorio sin refinamiento",
        "Correcta": "B",
    },
    181: {
        "Pregunta": "¿Para qué se usa el método de Monte Carlo en integración numérica?",
        "A": "Estimar integrales mediante muestreo aleatorio",
        "B": "Resolver EDO rígidas de forma exacta",
        "C": "Calcular autovalores de matrices",
        "D": "Aplicar solo la regla del trapecio",
        "Correcta": "A",
    },
    184: {
        "Pregunta": "En el método de Taylor para EDO, ¿qué error se controla al truncar términos de orden superior?",
        "A": "Solo error de redondeo en coma flotante",
        "B": "Error de medición experimental",
        "C": "Error de discretización espacial",
        "D": "Error de truncamiento del desarrollo en serie",
        "Correcta": "D",
    },
    185: {
        "Pregunta": "¿Qué caracteriza un método multipaso lineal para EDO?",
        "A": "Usa varios valores anteriores (y_n, y_{n-1}, …) para calcular y_{n+1}",
        "B": "Solo evalúa f una vez por paso",
        "C": "No requiere condiciones iniciales",
        "D": "Es siempre Euler de primer orden",
        "Correcta": "A",
    },
    186: {
        "Pregunta": "En Monte Carlo, ¿cómo escala típicamente el error estándar al duplicar N?",
        "A": "Se divide por 2",
        "B": "Se divide por √2",
        "C": "No cambia",
        "D": "Se multiplica por 2",
        "Correcta": "B",
    },
    187: {
        "Pregunta": "Si el error estándar escala como 1/√N y se pasa de N=100 a N=400, ¿por cuánto se divide el error?",
        "A": "4",
        "B": "1",
        "C": "2",
        "D": "√2",
        "Correcta": "C",
    },
    183: {
        "Pregunta": "¿Qué orden local tiene el método de Euler explícito para resolver y'=f(t,y)?",
        "A": "Orden 4",
        "B": "Orden 2",
        "C": "Orden 1",
        "D": "Orden 0",
        "Correcta": "C",
    },
    188: {
        "Pregunta": "Método de Euler: y'=y−t²+1, y(0)=0,5, h=0,5. ¿Aproximación de y(0,5)?",
        "A": "0,5",
        "B": "0,75",
        "C": "1",
        "D": "1,25",
        "Correcta": "D",
    },
    189: {
        "Pregunta": "Con muestras uniformes 0,2, 0,4, 0,6 y 0,8 en [0,1], ¿media muestral (estimador MC de ∫₀¹ x dx)?",
        "A": "0,5",
        "B": "0,2",
        "C": "1",
        "D": "0",
        "Correcta": "A",
    },
    190: {
        "Pregunta": "En el método RK4 clásico para EDO, ¿cuántas evaluaciones de f se hacen por paso h?",
        "A": "1",
        "B": "4",
        "C": "2",
        "D": "0",
        "Correcta": "B",
    },
    36: {
        "Pregunta": "En Python, ¿qué imprime print(type([]))?",
        "A": "<class 'list'>",
        "B": "<class 'dict'>",
        "C": "<class 'tuple'>",
        "D": "<class 'set'>",
        "Correcta": "A",
    },
    246: {
        "Pregunta": "¿Qué es la entropía condicional H(X|Y)?",
        "A": "Incertidumbre de X una vez observado Y",
        "B": "Suma de entropías marginales siempre",
        "C": "Capacidad de canal C",
        "D": "Código Huffman óptimo",
        "Correcta": "A",
    },
    12: {
        "Pregunta": "¿Cuál es la derivada de ln(x) para x>0?",
        "A": "1/x",
        "B": "x",
        "C": "ln(x)",
        "D": "e^x",
        "Correcta": "A",
    },
    313: {
        "Pregunta": "¿Qué indica un test de Dickey-Fuller en series temporales?",
        "A": "Ayuda a detectar raíz unitaria (no estacionariedad)",
        "B": "Mide la media móvil óptima",
        "C": "Calcula el periodo estacional automáticamente",
        "D": "Estima el beta de un activo",
        "Correcta": "A",
    },
    321: {
        "Pregunta": "¿Qué es un diagrama de persistencia en TDA?",
        "A": "Gráfico birth-death de características topológicas por escala",
        "B": "Matriz de confusión de un clasificador",
        "C": "Árbol de expansión mínima",
        "D": "Histograma de luminosidad",
        "Correcta": "A",
    },
    368: {
        "Pregunta": "¿Qué mide el porcentaje de identidad entre dos secuencias alineadas?",
        "A": "Fracción de posiciones coincidentes en el alineamiento",
        "B": "Número de intrones",
        "C": "Temperatura de hibridación únicamente",
        "D": "El genoma completo de la especie",
        "Correcta": "A",
    },
    327: {
        "Pregunta": "En una filtración de Vietoris-Rips, si aumenta ε normalmente:",
        "A": "Disminuye siempre el número de aristas",
        "B": "Se eliminan todos los símplices",
        "C": "Aparecen más conexiones y pueden fusionarse componentes",
        "D": "El complejo queda sin vértices",
        "Correcta": "C",
    },
    197: {
        "Pregunta": "Para f(x)=x²−4x+5, ¿cuál es su valor mínimo global?",
        "A": "1",
        "B": "0",
        "C": "4",
        "D": "No existe",
        "Correcta": "A",
    },
}


def _cargar_filas() -> list[dict]:
    return list(csv.DictReader(PATH_CSV.open(encoding="utf-8"), delimiter=";"))


def _guardar_filas(rows: list[dict]) -> None:
    cols = rows[0].keys()
    with PATH_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for r in sorted(rows, key=lambda x: int(x["Id"])):
            w.writerow(r)


def cmd_analizar(_args: argparse.Namespace) -> int:
    rows = _cargar_filas()
    print("=== Materias con pares de preguntas muy parecidas (Jaccard >= 0.35) ===\n")
    flagged: list[str] = []
    for mat in sorted(agrupar_por_materia(rows).keys()):
        items = agrupar_por_materia(rows)[mat]
        pairs = pares_similares_en_materia(items, UMBRAL_INFORME, max_pares=6)
        if not pairs:
            continue
        flagged.append(mat)
        print(f"## {mat}")
        for sim, id_a, id_b, pre_a, pre_b in pairs:
            print(f"  sim={sim:.2f}  Id {id_a} vs {id_b}")
            print(f"    A: {pre_a}")
            print(f"    B: {pre_b}")
        print()
    print(f"Total materias con similitud alta: {len(flagged)}/40")

    print("\n=== Palabra frecuente (>=4) en enunciado por materia ===\n")
    for mat in sorted(agrupar_por_materia(rows).keys()):
        hot = palabras_frecuentes_por_materia(agrupar_por_materia(rows)[mat])
        if hot:
            print(f"{mat}: {hot}")
    return 0


def letra_canonica(qid: int) -> str:
    return LETTERS[(int(qid) - 1) % 4]


def expandir_plantilla(template: dict) -> list[dict]:
    out = []
    variaciones = template.get("variaciones")
    if variaciones:
        for var in variaciones:
            p, a, b, c, d = (
                template["pregunta"],
                template["A"],
                template["B"],
                template["C"],
                template["D"],
            )
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
        out.append(
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
    return out


def cargar_keywords_materia() -> dict[str, list[str]]:
    path = BASE / "Data" / "criterios_clasificacion_materia.csv"
    out: dict[str, list[str]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            raw = row.get("Palabras_clave") or ""
            out[row["Materia"]] = [p.strip().lower() for p in raw.split("|") if p.strip()]
    return out


def relevancia_materia(pregunta: str, keywords: list[str]) -> int:
    t = pregunta.lower()
    return sum(1 for k in keywords if k and k in t)


def max_sim_pregunta(pregunta: str, grupo: list[dict], excluir_id: int) -> float:
    st = stem_words(pregunta)
    sims = [
        jaccard(st, stem_words(r["Pregunta"]))
        for r in grupo
        if int(r["Id"]) != excluir_id
    ]
    return max(sims) if sims else 0.0


def cargar_plantillas_por_materia() -> dict[str, list[dict]]:
    raw = json.loads(PATH_PLANTILLAS.read_text(encoding="utf-8"))
    por_materia: dict[str, list[dict]] = defaultdict(list)
    for materia, items in raw.items():
        for tpl in items:
            for p in expandir_plantilla(tpl):
                p["_materia"] = materia
                por_materia[materia].append(p)
    return por_materia


def reordenar_opciones(preg: dict, qid: int) -> dict:
    target = letra_canonica(qid)
    src = str(preg["Correcta"]).strip().upper()
    if src not in LETTERS:
        src = "A"
    opts = {k: preg[k] for k in LETTERS}
    correct_text = opts[src]
    wrong = [opts[k] for k in LETTERS if k != src]
    nuevo: dict[str, str] = {}
    wi = 0
    for letter in LETTERS:
        if letter == target:
            nuevo[letter] = correct_text
        else:
            nuevo[letter] = wrong[wi]
            wi += 1
    return {
        "Pregunta": preg["Pregunta"],
        "A": nuevo["A"],
        "B": nuevo["B"],
        "C": nuevo["C"],
        "D": nuevo["D"],
        "Correcta": target,
        "Dificultad": preg.get("Dificultad", "Media"),
        "Tipo": preg.get("Tipo", "Teoria"),
    }


def mejor_par(rows: list[dict], umbral: float) -> tuple[float, int, int] | None:
    stems = [(int(r["Id"]), stem_words(r["Pregunta"])) for r in rows]
    best = None
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            sim = jaccard(stems[i][1], stems[j][1])
            if sim >= umbral and (best is None or sim > best[0]):
                best = (sim, stems[i][0], stems[j][0])
    return best


def elegir_sustituto(
    materia: str,
    fila: dict,
    plantillas: list[dict],
    stems_usados: list[set],
    grupo: list[dict],
    keywords: list[str],
    textos_usados: set[str],
) -> dict | None:
    tipo = fila["Tipo"]
    dif = fila["Dificultad"]
    orden_dif = {"Facil": 0, "Media": 1, "Dificil": 2}
    candidatos = []
    for p in plantillas:
        if p.get("_materia") != materia:
            continue
        st = stem_words(p["Pregunta"])
        if any(jaccard(st, u) >= 0.28 for u in stems_usados):
            continue
        if p["Pregunta"] in textos_usados:
            continue
        if max_sim_pregunta(p["Pregunta"], grupo, int(fila["Id"])) > MAX_SIM_GRUPO:
            continue
        rel = relevancia_materia(p["Pregunta"], keywords) if keywords else 1
        if keywords and rel < 2:
            continue
        score = 0
        if p["Tipo"] == tipo:
            score += 3
        score -= abs(orden_dif.get(p["Dificultad"], 1) - orden_dif.get(dif, 1))
        score += relevancia_materia(p["Pregunta"], keywords)
        candidatos.append((score, p))
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: (-x[0], x[1]["Pregunta"]))
    return reordenar_opciones(candidatos[0][1], int(fila["Id"]))


def cmd_diversificar(args: argparse.Namespace) -> int:
    umbral = args.umbral
    plantillas = cargar_plantillas_por_materia()
    keywords_mat = cargar_keywords_materia()
    rows = _cargar_filas()
    by_id = {int(r["Id"]): r for r in rows}
    by_mat: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_mat[r["Materia"]].append(r)

    cambios: list[tuple[int, str, str]] = []

    for materia in sorted(by_mat.keys()):
        if materia in SKIP_MATERIAS:
            continue
        grupo = by_mat[materia]
        textos_usados = {r["Pregunta"] for r in grupo}
        kw = keywords_mat.get(materia, [])
        n = 0
        while n < MAX_POR_MATERIA:
            par = mejor_par(grupo, umbral)
            if not par:
                break
            sim, id_a, id_b = par
            if sim < UMBRAL_SUSTITUCION:
                break
            qid = max(id_a, id_b)
            fila = by_id[qid]
            stems_usados = [stem_words(r["Pregunta"]) for r in grupo if int(r["Id"]) != qid]
            sust = elegir_sustituto(
                materia,
                fila,
                plantillas.get(materia, []),
                stems_usados,
                grupo,
                kw,
                textos_usados,
            )
            if not sust:
                break
            old_p = fila["Pregunta"][:60]
            for k in ("Pregunta", "A", "B", "C", "D", "Correcta", "Dificultad", "Tipo"):
                fila[k] = sust[k]
            textos_usados.add(fila["Pregunta"])
            grupo = [by_id[int(r["Id"])] for r in grupo]
            cambios.append((qid, old_p, fila["Pregunta"][:60]))
            n += 1

    print(f"Sustituciones propuestas: {len(cambios)}")
    for qid, old, new in cambios:
        print(f"  Id {qid}:")
        print(f"    - {old}...")
        print(f"    + {new}...")

    if args.dry_run:
        return 0
    if cambios:
        _guardar_filas(rows)
        print(f"Escrito {PATH_CSV}")
    return 0


def cmd_curado(_args: argparse.Namespace) -> int:
    rows = _cargar_filas()
    aplicados = 0
    for r in rows:
        qid = int(r["Id"])
        if qid not in PARCHES:
            continue
        for k, v in PARCHES[qid].items():
            r[k] = v
        aplicados += 1
    _guardar_filas(rows)
    print(f"Parches curados aplicados: {aplicados}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Variedad temática del banco de preguntas")
    sub = p.add_subparsers(dest="accion", required=True)

    p_an = sub.add_parser("analizar", help="Informe de pares similares y palabras repetidas")
    p_an.set_defaults(func=cmd_analizar)

    p_div = sub.add_parser("diversificar", help="Sustituye preguntas muy parecidas (plantillas)")
    p_div.add_argument("--dry-run", action="store_true")
    p_div.add_argument("--umbral", type=float, default=UMBRAL_DIVERSIFICAR)
    p_div.set_defaults(func=cmd_diversificar)

    p_cur = sub.add_parser("curado", help="Aplica parches manuales por Id")
    p_cur.set_defaults(func=cmd_curado)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    from utils_banco_cerrado import rechazar_script_deprecado

    rechazar_script_deprecado("variedad_materias.py")
    raise SystemExit(main())
