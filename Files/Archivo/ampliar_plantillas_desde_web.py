#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amplia Data/plantillas.json con nuevas preguntas semilla basadas en
contenidos tipicos de guias docentes (fuentes web publicas).

No modifica Data/Preguntas.csv.
Evita duplicados exactos dentro del mismo tema.

Uso:
  python Files/ampliar_plantillas_desde_web.py --dry-run
  python Files/ampliar_plantillas_desde_web.py --inplace
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PATH_PLANTILLAS = BASE / "Data" / "JSON" / "plantillas.json"


def _key(t: dict) -> tuple[str, str, str, str, str, str]:
    return (
        str(t.get("pregunta", "")).strip().lower(),
        str(t.get("A", "")).strip().lower(),
        str(t.get("B", "")).strip().lower(),
        str(t.get("C", "")).strip().lower(),
        str(t.get("D", "")).strip().lower(),
        str(t.get("correcta", "")).strip().upper(),
    )


NUEVAS_SEMILLAS: dict[str, list[dict]] = {
    "Anàlisi Topològica de Dades": [
        {
            "pregunta": "En TDA, ¿qué resume un diagrama de persistencia?",
            "A": "La evolución de clases topológicas al variar la filtración",
            "B": "La matriz de covarianza",
            "C": "La solución exacta de una EDP",
            "D": "La transformada de Fourier",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué representa típicamente β0 en homología persistente?",
            "A": "Número de componentes conexas",
            "B": "Número de cavidades tridimensionales",
            "C": "Curvatura media",
            "D": "Orden del método numérico",
            "correcta": "A",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "En una filtración de Vietoris-Rips, si aumenta epsilon normalmente:",
            "A": "Aparecen más conexiones y se fusionan componentes",
            "B": "Disminuye el número de aristas siempre",
            "C": "Se eliminan todos los símplices",
            "D": "No cambia la complejidad",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué captura de forma típica β1 en datos geométricos?",
            "A": "Número de ciclos/agujeros de dimensión 1",
            "B": "Número de componentes conexas",
            "C": "Número de tetraedros",
            "D": "Rango de una matriz",
            "correcta": "A",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
    ],
    "Computació i Simulació d'Altes Prestacions": [
        {
            "pregunta": "Según la ley de Amdahl, si la parte secuencial aumenta, el speedup máximo:",
            "A": "Aumenta sin límite",
            "B": "Disminuye",
            "C": "No cambia nunca",
            "D": "Es igual al número de nodos",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "En computación paralela, ¿qué mide la escalabilidad fuerte?",
            "A": "Rendimiento al crecer datos y recursos proporcionalmente",
            "B": "Latencia de red únicamente",
            "C": "Rendimiento con problema fijo al aumentar recursos",
            "D": "Consumo eléctrico por nodo",
            "correcta": "C",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "En MPI, ¿qué operación combina valores de todos los procesos y distribuye el resultado?",
            "A": "Broadcast",
            "B": "Allreduce",
            "C": "Scatter",
            "D": "Gather",
            "correcta": "B",
            "dificultad": "Dificil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "Si un programa tiene fracción paralelizable p=0.9, el speedup máximo teórico (Amdahl) al infinito es:",
            "A": "9",
            "B": "10",
            "C": "100",
            "D": "1/0.9",
            "correcta": "B",
            "dificultad": "Dificil",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
    ],
    "Teoria de la Informació": [
        {
            "pregunta": "¿Qué expresa H(X) en teoría de la información?",
            "A": "Entropía de la variable aleatoria X",
            "B": "Error cuadrático medio",
            "C": "Capacidad de memoria caché",
            "D": "Tiempo de convergencia",
            "correcta": "A",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "En un canal sin ruido, la capacidad del canal es:",
            "A": "Cero",
            "B": "Igual a la tasa de símbolos útil",
            "C": "Siempre 1 bit/s",
            "D": "Independiente del alfabeto",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Cuándo alcanza máximo la entropía de una Bernoulli(p)?",
            "A": "p=0.1",
            "B": "p=0.5",
            "C": "p=0.9",
            "D": "p=1",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
        {
            "pregunta": "La información mutua I(X;Y) es siempre:",
            "A": "Negativa",
            "B": "No negativa",
            "C": "Menor que -1",
            "D": "Compleja",
            "correcta": "B",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
    ],
    "Informació Quàntica": [
        {
            "pregunta": "¿Cuántos estados base tiene un qubit?",
            "A": "1",
            "B": "2",
            "C": "4",
            "D": "Infinitos discretos",
            "correcta": "B",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "Una puerta Hadamard aplicada a |0> genera:",
            "A": "Un estado de superposición equiprobable",
            "B": "Siempre |1>",
            "C": "Un estado clásico determinista",
            "D": "Colapso inmediato",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué propiedad caracteriza al entrelazamiento cuántico?",
            "A": "Correlaciones no factorizables entre subsistemas",
            "B": "Independencia estadística completa",
            "C": "Ausencia de superposición",
            "D": "Determinismo clásico estricto",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "La medida en base computacional de un qubit en superposición produce:",
            "A": "Un vector continuo",
            "B": "Un resultado clásico 0 o 1 según probabilidades",
            "C": "Siempre 0",
            "D": "Siempre 1",
            "correcta": "B",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
    ],
    "Modelització i Simulació": [
        {
            "pregunta": "En simulación de eventos discretos, ¿qué estructura gestiona el próximo evento?",
            "A": "Lista/cola de eventos ordenada por tiempo",
            "B": "Matriz de covarianza",
            "C": "Cola de prioridades de gradientes",
            "D": "Pila LIFO de hilos",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "En Monte Carlo, al aumentar N muestras, el error típico decrece como:",
            "A": "O(1/N)",
            "B": "O(1/sqrt(N))",
            "C": "O(log N)",
            "D": "No decrece",
            "correcta": "B",
            "dificultad": "Dificil",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
        {
            "pregunta": "En validación de modelos de simulación, calibrar parámetros significa:",
            "A": "Ajustarlos para reproducir observaciones reales",
            "B": "Eliminar todas las variables",
            "C": "Fijar semilla aleatoria a cero siempre",
            "D": "Usar solo datos sintéticos",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "Si una simulación discreta procesa 500 eventos en 10 segundos simulados, la tasa media es:",
            "A": "5 eventos/seg",
            "B": "50 eventos/seg",
            "C": "5000 eventos/seg",
            "D": "0.5 eventos/seg",
            "correcta": "B",
            "dificultad": "Facil",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
    ],
    "Sistemes Distribuïts i el Núvol": [
        {
            "pregunta": "En el teorema CAP, bajo partición de red se prioriza normalmente:",
            "A": "Consistencia o disponibilidad (no ambas fuertes a la vez)",
            "B": "Siempre consistencia y disponibilidad simultáneas",
            "C": "Solo rendimiento gráfico",
            "D": "Solo latencia cero",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué describe la consistencia eventual?",
            "A": "Nunca hay discrepancias de réplicas",
            "B": "Las réplicas convergen si cesan escrituras",
            "C": "Lecturas siempre linealizables",
            "D": "No existe replicación",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué ventaja principal aporta la replicación en sistemas distribuidos?",
            "A": "Mayor disponibilidad y tolerancia a fallos",
            "B": "Elimina toda latencia de red",
            "C": "Evita la sincronización completamente",
            "D": "Reduce a cero el almacenamiento",
            "correcta": "A",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "En arquitectura cloud, escalar horizontalmente implica:",
            "A": "Aumentar CPU/RAM de un único nodo",
            "B": "Añadir más instancias/nodos",
            "C": "Reducir número de réplicas",
            "D": "Desactivar balanceador",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
    ],
    "Visió per Computador": [
        {
            "pregunta": "En una CNN, ¿qué hace un kernel de convolución?",
            "A": "Extrae patrones locales de la imagen",
            "B": "Ordena etiquetas alfabéticamente",
            "C": "Reduce siempre a un escalar",
            "D": "Sustituye la función de pérdida",
            "correcta": "A",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué efecto tiene el pooling en mapas de características?",
            "A": "Aumenta resolución espacial",
            "B": "Reduce dimensionalidad espacial y gana robustez",
            "C": "Elimina no linealidades",
            "D": "Convierte RGB en texto",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "La IoU (Intersection over Union) se usa habitualmente para:",
            "A": "Evaluar solapamiento en detección/segmentación",
            "B": "Medir precisión de punto flotante",
            "C": "Calcular entropía de canal",
            "D": "Ordenar clases por frecuencia",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "Una imagen RGB de 128x128 tiene cuántos valores de canal:",
            "A": "16384",
            "B": "32768",
            "C": "49152",
            "D": "65536",
            "correcta": "C",
            "dificultad": "Facil",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
    ],
    "Equacions en Derivades Parcials": [
        {
            "pregunta": "La ecuación del calor clásica es un ejemplo de EDP:",
            "A": "Elíptica",
            "B": "Parabólica",
            "C": "Hiperbólica pura",
            "D": "Algebraica",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "La ecuación de ondas unidimensional se clasifica típicamente como:",
            "A": "Parabólica",
            "B": "Elíptica",
            "C": "Hiperbólica",
            "D": "No lineal obligatoriamente",
            "correcta": "C",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "Si una malla espacial tiene paso h y un dominio de longitud 1, al reducir h a la mitad, los nodos 1D aproximadamente:",
            "A": "Se mantienen",
            "B": "Se duplican",
            "C": "Se cuadruplican",
            "D": "Se reducen a la mitad",
            "correcta": "B",
            "dificultad": "Media",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
    ],
    "Anàlisi de Dades Temporals": [
        {
            "pregunta": "Un proceso AR(1) estacionario requiere típicamente:",
            "A": "|phi| < 1",
            "B": "|phi| > 1",
            "C": "phi = 2",
            "D": "phi siempre complejo",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "¿Qué describe la autocorrelación en una serie temporal?",
            "A": "Dependencia entre observaciones separadas por un retardo",
            "B": "Correlación entre variables distintas en un mismo instante",
            "C": "Error de medición sistemático",
            "D": "Solo tendencia determinista",
            "correcta": "A",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "Si una serie tiene estacionalidad mensual, un retardo natural para comparar patrones es:",
            "A": "1",
            "B": "6",
            "C": "12",
            "D": "24",
            "correcta": "C",
            "dificultad": "Facil",
            "tipo": "Calculo",
            "uso": "web_seed",
        },
    ],
    "Informació i Seguretat": [
        {
            "pregunta": "¿Qué propiedad asegura una función hash criptográfica?",
            "A": "Resistencia a colisiones (idealmente difícil de encontrar)",
            "B": "Cifrado reversible con clave pública",
            "C": "Anonimato perfecto de red",
            "D": "Compresión sin pérdida garantizada",
            "correcta": "A",
            "dificultad": "Media",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
        {
            "pregunta": "El principio de mínimo privilegio recomienda:",
            "A": "Otorgar más permisos por defecto",
            "B": "Dar solo permisos necesarios para la tarea",
            "C": "Evitar auditorías",
            "D": "Eliminar autenticación",
            "correcta": "B",
            "dificultad": "Facil",
            "tipo": "Teoria",
            "uso": "web_seed",
        },
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.inplace and not args.dry_run:
        args.dry_run = True

    with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
        data = json.load(f)

    total_add = 0
    detalle: list[str] = []
    for materia, seeds in NUEVAS_SEMILLAS.items():
        if materia not in data:
            data[materia] = []
        seen = {_key(t) for t in data[materia]}
        add_here = 0
        for s in seeds:
            k = _key(s)
            if k in seen:
                continue
            data[materia].append(s)
            seen.add(k)
            add_here += 1
        if add_here:
            total_add += add_here
            detalle.append(f"  - {materia}: +{add_here}")

    print(f"Nuevas plantillas añadidas: {total_add}")
    if detalle:
        print("Detalle:")
        for d in detalle:
            print(d)
    else:
        print("Sin cambios (ya existían).")

    if args.dry_run or not args.inplace:
        print("Dry-run: no se ha escrito plantillas.json")
        return 0

    with PATH_PLANTILLAS.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Guardado: {PATH_PLANTILLAS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
