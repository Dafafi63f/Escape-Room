# -*- coding: utf-8 -*-
"""
Palabras clave por Id de materia (listado_materias.csv) y puntuacion de texto
para priorizar filas al balancear por tema (`balancear_dataset.py`).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

MATERIAS: dict[int, str] = {}
with (BASE / "Data" / "listado_materias.csv").open("r", encoding="utf-8", newline="") as _f:
    _reader = csv.DictReader(_f, delimiter=";")
    for _row in _reader:
        MATERIAS[int(_row["Id"])] = _row["Materia"]

MATERIA_TO_ID = {m: i for i, m in MATERIAS.items()}

KEYWORDS: dict[int, list[str]] = {
    1: ["grassmann", "dim(ker)", "producto escalar", "subespacio", "subespacio propio", "subespacio trivial",
        "matriz", "determinante", "rango de una matriz", "autovalor", "autovectores", "base",
        "espacio vectorial", "álgebra lineal", "vector", "transformación lineal", "kernel", "imagen",
        "ortogonal", "traza", "inversa de una matriz", "suma directa", "dimensión de r", "dim(u+v)",
        "cuerpo finito", "z_7", "ideal en un anillo", "subconjunto", "complemento ortogonal",
        "proyección ortogonal", "suma de vectores", "producto mixto", "paralelepípedo", "volumen del paralelepípedo"],
    2: ["derivada", "integral", "límite", "continuidad", "continuidad en un punto", "función continua",
        "gradiente", "trapecio", "simpson", "punto fijo", "newton", "convergencia", "derivable",
        "regla cadena", "integral de 0 a 1", "integral dx", "teorema fundamental del cálculo"],
    3: ["cd ", "comando", "directorio", "retorno", "valor de retorno", "comando sube", "cd ..",
        "touch", "find", "redirección", "pipe", "variable de clase", "iniciación programación"],
    4: ["ancho de banda", "throughput", "latencia", "arquitectura cliente-servidor", "sistema operativo",
        "protocolo", "vpn", "dns", "https", "coap", "mqtt", "limit", "select", "insert", "where",
        "group by", "having", "like", "sql", "limit en una consulta", "codificación huffman",
        "entropía", "shannon", "canal", "capacidad del canal", "teorema de codificación",
        "segundo teorema de shannon", "cifrado", "criptografía", "hash", "seguridad", "ataque",
        "firewall", "cia", "esteganografía", "diffie-hellman", "rsa", "mongodb", "$project", "$eq",
        "operador $group", "operador $project", "codificación", "redundancia",
        "capacidad canal", "codificación fuente", "codificación canal", "codificación aritmética"],
    5: ["kernel", "proceso", "thread", "programari sistema", "sistema operativo"],
    6: ["probabilidad", "p(a)", "p(b)", "poisson", "bayes", "eventos independientes", "esperanza",
        "varianza", "distribución", "monte carlo", "muestreo", "probabilidad de cara",
        "p(x mayor", "p(x menor", "p(a y b)", "p(a|b)", "ley de probabilidad total",
        "parámetro", "población", "muestra", "estimación puntual"],
    7: ["derivada parcial", "gradiente", "jacobiano", "integral doble", "múltiples variables",
        "plano tangente", "punto crítico", "derivada direccional", "integral de x sobre",
        "integral doble de", "coordenadas cilíndricas", "coordenadas esféricas"],
    8: ["grafo", "vértice", "arista", "grafo bipartito", "matching", "floyd-warshall", "árbol",
        "símplice", "2-símplice", "1-símplice", "0-símplice", "persistencia", "homología",
        "barcode", "complejo", "algoritmia", "combinatoria", "vértices tiene", "aristas tiene",
        "diagrama de persistencia", "filtración", "betti", "índice de morse", "complejo alpha"],
    9: ["objeto", "clase", "herencia", "polimorfismo", "encapsulación", "equals", "constructor",
        "getter", "setter", "interface", "programación orientada", "quicksort", "complejidad",
        "recursión", "búsqueda binaria", "memoización", "fibonacci", "algoritmo", "instancia",
        "clase abstracta", "principio liskov", "subproblemas en quicksort", "complejidad de quicksort",
        "complejidad de búsqueda binaria", "método equals", "método toString", "variable static",
        "cliente-servidor", "niveles de herencia"],
    10: ["newton-raphson", "trapecio", "simpson", "jacobi", "sor", "diferencias finitas",
        "método numérico", "integral numérica", "punto fijo", "error de truncamiento",
        "aproximación del trapecio", "regla de simpson", "método del punto fijo",
        "cálcul numèric", "replicas para ic", "iteraciones monte carlo"],
    11: ["iluminación", "iluminación especular", "iluminación ambiente", "proyección", "esfera",
        "cilindro", "cubo", "3d", "visualización", "perspectiva", "traslación", "rotación",
        "escala", "coeficiente reducción", "gouraud", "phong", "frustum", "viewport",
        "paralelepípedo", "volumen", "superficie nivel", "distancia bottleneck", "wasserstein",
        "puntos definen una recta", "recta perpendicular", "transformación de traslación",
        "transformación de rotación", "volumen de una esfera", "volumen de un cilindro",
        "volumen de un cubo", "volumen de un cono", "área de un rectángulo", "área de un círculo",
        "distancia entre", "ángulo entre", "vector director", "plano", "recta", "geometría"],
    12: ["inferencia", "estimación", "intervalo confianza", "contraste", "hipótesis", "p-valor",
        "potencia estadística", "potencia de un contraste", "bootstrap", "verosimilitud",
        "bayesiano", "modelo estadístico", "parámetro población", "modelització inferència",
        "estadístico t", "distribución t", "student", "razón de verosimilitud",
        "nivel de confianza", "margen de error", "bias-variance", "odds ratio", "nnt", "ic 95"],
    13: ["programación dinámica", "voraz", "divide y vencer", "complejidad", "diseño algoritmos",
        "branch and bound", "backtracking", "elección voraz", "subestructura óptima",
        "orden bottom-up", "código óptimo", "algoritmo voraz", "mochila voraz"],
    14: ["sql", "select", "join", "tabla", "relacional", "base datos", "limit", "where",
        "group by", "insert", "bases datos relacionals", "tabla en una bd", "clave compuesta",
        "having", "select", "from", "insert"],
    15: ["monte carlo", "réplicas", "simulación", "métodos numéricos", "probabilístico",
        "mètodes numèrics", "simulación estocástica", "generación de números pseudoaleatorios",
        "simulación de eventos discretos", "lista de eventos", "convergencia de una simulación"],
    16: ["optimización", "óptimo", "gradiente", "hessiano", "programación lineal", "dual",
        "primal", "voraz", "simplex", "optimització", "anulador", "subespacio generado",
        "método de newton-raphson", "gradiente descendente", "relajación sor"],
    17: ["edo", "ecuación diferencial", "wronskiano", "ordinaria", "equacions diferencials",
        "y''+y", "y'=", "runge-kutta", "euler", "ecuación de calor", "wronskiano"],
    18: ["inteligencia artificial", "modelo", "agente", "colas", "modelo de colas",
        "clasificación", "regresión", "clustering", "machine learning", "intel·ligència artificial",
        "modelo basado en agentes", "modelo estocástico"],
    19: ["análisis datos", "regresión lineal", "correlación", "matriz correlación", "sensibilidad",
        "análisis de sensibilidad", "datos complejos", "consistencia eventual", "reduce", "gather",
        "recall", "precisión", "f1", "matriz confusión", "valor predictivo", "coeficiente de correlación",
        "anàlisi dades complexes", "data augmentation", "servidor sin estado", "resolución de un sensor"],
    20: ["fourier", "complejo", "residuo", "laurent", "holomorfa", "transformada fourier",
        "serie fourier", "convolución", "anàlisi complexa", "cuerpo de los reales", "módulo de i",
        "conjugado", "z=a+bi", "forma exponencial", "argumento de", "teorema de los residuos",
        "frecuencia fundamental", "coeficiente de fourier", "a_0", "coeficiente a_n",
        "transformada inversa", "expansion de laurent", "residuo de 1/z"],
    21: ["edp", "ecuación calor", "derivadas parciales", "hiperbólica", "elíptica", "parabólica",
        "cfl", "equacions derivades", "u_t", "u_xx", "formulación débil", "h0^1"],
    22: ["física", "newton", "aceleración", "fuerza", "energía", "ecosistema", "geología",
        "litosfera", "manto", "deriva continental", "ph", "concentración", "química", "átomo",
        "molécula", "mitosis", "gen", "adn", "proteína", "biología", "física abstracció",
        "acuífero", "manto terrestre", "deriva continental", "respiración celular", "fotosíntesis",
        "ley de newton", "segunda ley", "tercera ley", "f=ma", "energía cinética", "energía potencial",
        "cantidad de movimiento", "hidrocarburo", "electronegatividad", "mineral", "ecuación de arrhenius",
        "estequiometría", "equilibrio ácido-base", "titulación", "kps", "solubilidad", "velocidad de escape",
        "longitud de onda", "frecuencia", "ley de ohm", "cuerpo negro", "función luminosidad",
        "redshift", "paralaje", "corrección k", "expresión diferencial", "datación radiométrica"],
    23: ["aprendizaje", "entrenamiento", "modelo", "feature", "label", "epoch", "batch",
        "overfitting", "regularización", "aprenentatge computacional", "entrenamiento de un modelo",
        "modelo de regresión", "modelo predictivo"],
    24: ["speedup", "paralelo", "amdahl", "hpc", "cluster", "computación paralela", "distribuido",
        "mpi", "memoria compartida", "mensajes", "thread", "procesador", "computació altes prestacions",
        "gpu", "kubernetes", "pod", "fog computing", "cloud", "nube", "cluster hpc",
        "teorema cap", "modelo de memoria compartida", "modelo de paso de mensajes", "message queue",
        "granularidad", "comunicaciones", "broadcast", "scatter", "reduce paralelo",
        "escalabilidad fuerte", "escalabilidad débil", "cuello de botella",
        "criterio de parada", "criterio parada"],
    25: ["shannon", "entropía", "información", "capacidad canal", "codificación fuente",
        "codificación canal", "teoria informació", "entropía condicional", "entropía de una fuente",
        "segundo teorema de shannon", "código óptimo", "codificación de fuente"],
    26: ["distribuido", "nube", "cloud", "kubernetes", "consistencia", "cap", "sistemes distribuïts",
        "núvol", "particiones", "cap se sacrifican"],
    27: ["red neuronal", "neural", "deep learning", "lstm", "rnn", "transformer", "attention",
        "embedding", "softmax", "convolución", "pooling", "stride", "xarxes neuronals",
        "aprenentatge profund", "convolution", "stride en convolución", "batch normalization",
        "residual connection", "skip connection", "self-attention", "encoder-decoder",
        "detección de bordes", "visión", "reconocimiento imagen"],
    28: ["qubit", "cuántico", "quantum", "bell", "puerta cuántica", "teleportación cuántica",
        "paralelismo cuántico", "cnot", "informació quàntica", "estado de bell", "grados de libertad qubit",
        "estados de bell", "puerta x", "cnot con control"],
    29: ["mongodb", "nosql", "documental", "clave-valor", "cassandra", "bases datos no relacionals",
        "base de datos documental", "base de datos clave-valor", "tipos de nosql"],
    30: ["simulación", "modelo", "eventos discretos", "monte carlo", "modelització simulació",
        "simulación en tiempo real", "simulación de eventos discretos", "lista de eventos"],
    31: ["financiero", "economía", "pib", "deflactor", "beta", "mercado", "riesgo", "volatilidad",
        "dividendo", "acción", "inflación", "excedente", "keynes", "anàlisi dades financeres",
        "multiplicador keynesiano", "pmc", "deflactor", "riesgo sistemático", "alpha", "ratio sharpe",
        "ratio sortino", "tipo de cambio", "mercado otc", "riesgo de liquidez", "excedente del consumidor",
        "excedente del productor", "propensión marginal", "colateral", "margin"],
    32: ["serie temporal", "raíz unitaria", "arima", "sarima", "estacionariedad", "dickey-fuller",
        "tendencia", "anàlisi dades temporals", "media móvil", "ventana de predicción"],
    33: ["salud", "medicina", "clínico", "ic 95", "odds ratio", "nnt", "sensibilidad", "especificidad",
        "mètodes anàlisi ciències salut", "meta-análisis", "heterogeneidad", "análisis de mediación",
        "valor predictivo positivo", "valor predictivo negativo"],
    34: ["gen", "adn", "secuencia", "atcg", "codón", "bioinformática", "k-mer", "alineamiento",
        "bioinformàtica", "secuencia 1000 bases", "k-mers únicos", "codones posibles",
        "similitud de secuencia", "identidad de secuencia", "proteoma", "genoma", "transcriptoma",
        "intrón", "exón", "traducción", "arn a proteína", "transcripción", "replicación",
        "alineamiento múltiple", "reads", "contig", "expresión diferencial"],
    35: ["astrofísica", "estrella", "galaxia", "luminosidad", "redshift", "paralaje", "cuerpo negro",
        "función luminosidad", "anàlisi dades astrofísica", "stefan-boltzmann", "flujo luminosidad",
        "redshift z="],
    36: ["seguridad", "cifrado", "criptografía", "hash", "ataque", "salt", "informació seguretat",
        "ataque de repetición", "ataque de texto cifrado", "esteganografía", "principio mínimo privilegio",
        "tríada cia", "problema de logaritmo discreto", "longitud mínima de clave"],
    37: ["persistencia", "homología", "topología", "betti", "diagrama persistencia", "filtración",
        "anàlisi topològica", "dimensión de homología", "módulo de persistencia", "persistencia de una característica"],
    38: ["juego", "nash", "equilibrio", "estrategia", "teoría juegos", "teoria jocs", "equilibrio de nash",
        "juego repetido", "spe", "juego 3x3", "equilibrio de nash en estrategias"],
    39: ["iot", "sensor", "actuador", "dispositivo", "conectividad", "gateway", "internet cosas",
        "mqtt", "coap", "conectividad en iot", "seguridad en iot", "escalabilidad en iot"],
    40: ["imagen", "visión", "bordes", "detección", "resolución", "píxel", "convolution",
        "visió computador", "reconocimiento imagen", "detección de bordes", "normalización de imagen",
        "resolución de una imagen", "píxeles", "histograma", "bins", "canales", "rgb", "rgba",
        "tensor", "batch", "feature map", "kernel", "stride", "padding", "pooling", "softmax",
        "distancia edición", "levenshtein"],
}


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    t = str(texto).lower().strip()
    t = re.sub(r"[àáâãäå]", "a", t)
    t = re.sub(r"[èéêë]", "e", t)
    t = re.sub(r"[ìíîï]", "i", t)
    t = re.sub(r"[òóôõö]", "o", t)
    t = re.sub(r"[ùúûü]", "u", t)
    t = re.sub(r"[ñ]", "n", t)
    t = re.sub(r"[·]", "", t)
    return t


def puntuar_texto_completo(pregunta: str, a: str, b: str, c: str, d: str) -> dict[int, float]:
    """Usa pregunta + opciones para mejor contexto."""
    texto = normalizar(f"{pregunta} {a} {b} {c} {d}")
    scores: dict[int, float] = {}
    for id_mat, keywords in KEYWORDS.items():
        s = sum(1.0 for kw in keywords if normalizar(kw) in texto)
        if s > 0:
            scores[id_mat] = s
    return scores
