import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(r"C:\Users\34681\Documents\UAB\Running\Treball Final de Grau 🔘")
PREGUNTAS_PATH = ROOT / "Data" / "Preguntas.csv"
PLANTILLAS_PATH = ROOT / "Data" / "plantillas.json"
REPORTE_PATH = ROOT / "Data" / "reporte_contextualizacion.csv"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> list[str]:
    return [t for t in normalize_text(text).split() if len(t) > 2]


def jaccard_similarity(a: str, b: str) -> float:
    ta = set(tokens(a))
    tb = set(tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def choose_replacement(row: dict, templates: list[dict], usage: Counter) -> dict | None:
    same_dt = [
        t
        for t in templates
        if normalize_text(t.get("dificultad", "")) == normalize_text(row["Dificultad"])
        and normalize_text(t.get("tipo", "")) == normalize_text(row["Tipo"])
    ]
    candidates = same_dt or templates
    if not candidates:
        return None
    return min(candidates, key=lambda t: usage[t["pregunta"]])


def main() -> None:
    with PLANTILLAS_PATH.open("r", encoding="utf-8") as f:
        plantillas_raw = json.load(f)

    # Index templates by normalized materia.
    plantillas_by_materia = {
        normalize_text(materia): plantillas for materia, plantillas in plantillas_raw.items()
    }

    with PREGUNTAS_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise RuntimeError("No se pudieron leer cabeceras en Preguntas.csv")

    templates_usage = Counter()
    changed_rows = []

    # Replace questions that are not in the curated template bank of their own materia.
    for row in rows:
        mat_key = normalize_text(row["Materia"])
        templates = plantillas_by_materia.get(mat_key, [])
        if not templates:
            continue
        template_questions_norm = {normalize_text(t["pregunta"]) for t in templates}
        row_question_norm = normalize_text(row["Pregunta"])
        if row_question_norm in template_questions_norm:
            continue

        repl = choose_replacement(row, templates, templates_usage)
        if repl is None:
            continue

        old = row.copy()
        row["Pregunta"] = repl["pregunta"]
        row["A"] = repl["A"]
        row["B"] = repl["B"]
        row["C"] = repl["C"]
        row["D"] = repl["D"]
        row["Correcta"] = repl["correcta"]
        row["Dificultad"] = repl["dificultad"]
        row["Tipo"] = repl["tipo"]
        templates_usage[repl["pregunta"]] += 1

        changed_rows.append(
            {
                "Id": row["Id"],
                "Materia": row["Materia"],
                "Pregunta_Original": old["Pregunta"],
                "Pregunta_Nueva": row["Pregunta"],
                "Similitud_Inicial": f"{jaccard_similarity(old['Pregunta'], row['Pregunta']):.3f}",
            }
        )

    with PREGUNTAS_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)

    report_fields = ["Id", "Materia", "Similitud_Inicial", "Pregunta_Original", "Pregunta_Nueva"]
    with REPORTE_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=report_fields, delimiter=";")
        writer.writeheader()
        writer.writerows(changed_rows)

    print(f"Total preguntas: {len(rows)}")
    print(f"Preguntas reemplazadas: {len(changed_rows)}")
    print("Reporte generado en Data/reporte_contextualizacion.csv")


if __name__ == "__main__":
    main()
