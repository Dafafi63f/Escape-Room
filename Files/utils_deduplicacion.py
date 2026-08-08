#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Criterios compartidos para detectar preguntas duplicadas o muy similares.

Duplicado incluye:
- Mismo enunciado aunque cambien las opciones o la correcta.
- Bloque idéntico (pregunta + A + B + C + D).
- Enunciado casi igual o mismas opciones con redacción muy parecida.
- Misma respuesta correcta sustantiva con enunciado equivalente o mismo significado.
- Misma plantilla de cálculo: solo cambian números (y la respuesta numérica) pero la pregunta es la misma.
- Misma familia de plantilla (p. ej. «¿cuántos valores con N bits?» / «con N bits, ¿cuántos estados?»).
"""

from __future__ import annotations

_TOKEN_DEFINICION = "definición"

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

import math
import re
import unicodedata
from difflib import SequenceMatcher

from utils_plantillas_pool import es_uso_copia_dataset
from utils_texto import normalizar_pregunta

_STOPWORDS = frozenset(
    """
    de la el en y a los las del un una es son que se por con para al como
    en què com es el la els les un una per amb de del d en i o u qué cuál
    cuántos cómo definir definición qué es cuál es como se define cual es
    quantes quin quina quins quines definicio significa representa indica
    """.split()
)

_RESPUESTAS_TRIVIALES = frozenset(
    {
        "si",
        "sí",
        "no",
        "true",
        "false",
        "verdadero",
        "falso",
        "ninguna",
        "ninguna de las anteriores",
        "cap",
        "totes",
        "todas",
        "a",
        "b",
        "c",
        "d",
    }
)

# Cuantificadores acotados: evita backtracking superlineal (python:S8786).
_RE_COMPLEJIDAD = re.compile(
    r"(?:^o\s{0,8}\(?)|(?:log\s{0,8}n)|(?:n\s{0,8}log)"
    r"|(?:n\s{0,8}\^?\s{0,8}2)|(?:polinom)|(?:exponencial)|(?:constante)|(?:lineal)"
)
_RE_NUMERO = re.compile(r"\d+(?:[.,]\d+)?")

# Colapso léxico para detectar la misma pregunta con redacción distinta.
_COLAPSO_REGLAS: tuple[tuple[str, str], ...] = (
    (r"\b(qubits?)\b", "BITUNIT"),
    (r"\b(bits?)\b", "BITUNIT"),
    (r"\b(bytes?|kilobytes?|kb|mb|gb)\b", "BYTEUNIT"),
    (r"\b(cuantos?|cuantas?|numero de|que numero|quants?|quantes?)\b", "NQ"),
    (
        r"\b(valores?|estados?|simbolos?|numeros?|representables?|combinaciones?|símbolos?)\b",
        "ENUM",
    ),
    (r"\b(distintos?|diferents?|diferentes?|posibles?|maxims?|maximos?|base)\b", ""),
    (r"\b(representar|representa|codificar|codigo|codigos?|codificacion)\b", "REP"),
    (r"\b(con|para|per|usando|de|en|se|pueden|un|una|el|la|els?|les?|sin)\b", ""),
    (r"\b(sin signo|equiprobables?|equiprobable)\b", ""),
    (r"\b(n|m|k)\s*=\s*#", "#"),  # ya normalizado
)

# Contextos que comparten BITUNIT+NQ pero no son la misma plantilla.
_EXCLUIR_FAMILIA_BITS = re.compile(
    r"\b(entropia|bernoulli|shannon|aes|cifr|hash|clave|pixel|pixels?|rgb|bell|pauli|"
    r"grados de libertad|por pixel|mensaje|fuente|bernoulli|incertidumbre)\b",
    re.UNICODE,
)


def _quitar_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _enunciado_normalizado(fila: dict) -> str:
    return _quitar_acentos(normalizar_pregunta(enunciado_de(fila)))


def tokens(texto: str) -> set[str]:
    return set(normalizar_pregunta(texto).split())


def tokens_contenido(texto: str) -> set[str]:
    return {
        w
        for w in normalizar_pregunta(texto).split()
        if len(w) > 2 and w not in _STOPWORDS
    }


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = len(a | b)
    return (len(a & b) / union) if union else 0.0


def enunciado_de(fila: dict) -> str:
    return (fila.get("Pregunta") or fila.get("pregunta") or "").strip()


def letra_correcta(fila: dict) -> str:
    letra = (fila.get("Correcta") or fila.get("correcta") or "A").strip().upper()
    return letra if letra in "ABCD" else "A"


def texto_respuesta_correcta(fila: dict) -> str:
    letra = letra_correcta(fila)
    clave_opcion = letra if letra in fila else letra.lower()
    return normalizar_pregunta(fila.get(clave_opcion, ""))


def respuesta_es_sustantiva(texto: str) -> bool:
    if not texto or texto in _RESPUESTAS_TRIVIALES:
        return False
    if re.fullmatch(r"[\d\s\.\,\-]+", texto):
        return False
    if _RE_COMPLEJIDAD.search(texto):
        return True
    return len(texto) >= 8


def numeros_enunciado(fila: dict) -> tuple[str, ...]:
    return tuple(sorted(re.findall(r"\d+(?:\.\d+)?", enunciado_de(fila))))


def tipo_de(fila: dict) -> str:
    return (fila.get("Tipo") or fila.get("tipo") or "").strip()


def esqueleto_numerico(texto: str) -> str:
    """Sustituye números por # para comparar la misma plantilla con distintos datos."""
    t = normalizar_pregunta(texto)
    t = _RE_NUMERO.sub("#", t)
    return re.sub(r"\s+", " ", t).strip()


def clave_esqueleto_pregunta(fila: dict) -> str:
    return esqueleto_numerico(enunciado_de(fila))


def clave_esqueleto_bloque(fila: dict) -> tuple[str, ...]:
    return (
        esqueleto_numerico(enunciado_de(fila)),
        esqueleto_numerico(fila.get("A", "") or ""),
        esqueleto_numerico(fila.get("B", "") or ""),
        esqueleto_numerico(fila.get("C", "") or ""),
        esqueleto_numerico(fila.get("D", "") or ""),
    )


def clave_esqueleto_opciones(fila: dict) -> tuple[str, ...]:
    return tuple(sorted(esqueleto_numerico(fila.get(c, "") or "") for c in "ABCD"))


def _tiene_marcador_numerico(esqueleto: str) -> bool:
    return "#" in esqueleto


def esqueleto_colapsado(texto: str) -> str:
    """Enunciado con números→# y sinónimos unificados (orden de tokens irrelevante)."""
    t = _quitar_acentos(esqueleto_numerico(texto))
    for patron, reemplazo in _COLAPSO_REGLAS:
        t = re.sub(patron, reemplazo, t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    toks = sorted(tok for tok in t.split() if tok and tok != "#")
    return " ".join(toks)


def clave_esqueleto_colapsado(fila: dict) -> str:
    return esqueleto_colapsado(enunciado_de(fila))


def clave_familia_plantilla(fila: dict) -> str | None:
    """
    Familias de preguntas paramétricas que se repiten con otras palabras o cifras.
    Devuelve un id de familia o None.
    """
    t = _enunciado_normalizado(fila)
    fam = _familia_bits_enum(t)
    if fam is not None:
        return fam
    fam = _familia_conversion_bytes(t)
    if fam is not None:
        return fam
    fam = _familia_limite(t)
    if fam is not None:
        return fam
    fam = _familia_entropia(t)
    if fam is not None:
        return fam
    fam = _familia_kmeans(t)
    if fam is not None:
        return fam
    return _familia_pixeles(t)


def _familia_bits_enum(t: str) -> str | None:
    if not (
        re.search(r"\b(bits?|qubits?)\b", t)
        and re.search(r"\b(cuantos?|cuantas?|numero de|que numero)\b", t)
    ):
        return None
    if _EXCLUIR_FAMILIA_BITS.search(t):
        return None
    if re.search(
        r"\b(valores?|estados?|simbolos?|símbolos?|numeros?|representar|"
        r"codificar|codigo|codigos?|representables?)\b",
        t,
    ):
        return "fam:bits_enum"
    if re.search(r"\b(bits?|qubits?)\s+(para|per)\b", t) and re.search(
        r"\b(estados?|simbolos?|valores?)\b", t
    ):
        return "fam:bits_enum"
    return None


def _familia_conversion_bytes(t: str) -> str | None:
    if not (
        re.search(r"\b(cuantos?|cuantas?)\b", t)
        and re.search(r"\b(bytes?|kb|mb|gb|kilobytes?)\b", t)
    ):
        return None
    if re.search(r"\b(entropia|hash|aes|cifr)\b", t):
        return None
    return "fam:conversion_bytes"


def _familia_limite(t: str) -> str | None:
    if re.search(r"\blim(ite)?\b", t) and re.search(r"\b[xt]\b", t):
        if re.search(r"\b(0|infinito|infty)\b", t) or "cuando" in t:
            return "fam:limite_indeterminacion"
    return None


def _familia_entropia(t: str) -> str | None:
    if (
        re.search(r"\bentropia\b", t)
        and re.search(r"\b(simbolos?|símbolos?|estados?)\b", t)
        and re.search(r"\bequiprobables?\b", t)
    ):
        return "fam:entropia_simbolos"
    return None


def _familia_kmeans(t: str) -> str | None:
    if re.search(r"\bclusters?\b", t) and re.search(r"\bk\s*=\s*#|k\s*=\s*\d+", t):
        return "fam:kmeans_k"
    return None


def _familia_pixeles(t: str) -> str | None:
    if re.search(r"\b(pixeles?|píxeles?|pixels?)\b", t) and re.search(
        r"\b(total|en total|imagen)\b", t
    ):
        return "fam:pixeles_total"
    return None


def _motivo_familia_bits_cuantos(ca: str, cb: str, a: dict, b: dict) -> str | None:
    tags_a = set(ca.split())
    tags_b = set(cb.split())
    nucleo = {"BITUNIT", "NQ", "ENUM"}
    if nucleo <= tags_a and nucleo <= tags_b:
        if not _EXCLUIR_FAMILIA_BITS.search(_enunciado_normalizado(a)):
            if not _EXCLUIR_FAMILIA_BITS.search(_enunciado_normalizado(b)):
                return "misma_plantilla_bits_cuantos"
    if "BYTEUNIT" in tags_a and "BYTEUNIT" in tags_b and "NQ" in tags_a and "NQ" in tags_b:
        return "misma_plantilla_conversion_bytes"
    return None


def _motivo_familia_plantilla(a: dict, b: dict) -> str | None:
    fa, fb = clave_familia_plantilla(a), clave_familia_plantilla(b)
    if fa and fa == fb:
        return f"misma_familia_{fa}"

    ca, cb = clave_esqueleto_colapsado(a), clave_esqueleto_colapsado(b)
    if ca and ca == cb and _tiene_marcador_numerico(esqueleto_numerico(enunciado_de(a))):
        return "misma_plantilla_colapsada"

    if ca and cb and "#" in esqueleto_numerico(enunciado_de(a)):
        return _motivo_familia_bits_cuantos(ca, cb, a, b)

    return None


def _motivo_variante_numerica(a: dict, b: dict, qa: str, qb: str) -> str | None:
    """Misma pregunta de cálculo cambiando solo cifras (y respuesta numérica distinta)."""
    if qa == qb:
        return None

    sk_a, sk_b = clave_esqueleto_pregunta(a), clave_esqueleto_pregunta(b)
    if sk_a and sk_a == sk_b and _tiene_marcador_numerico(sk_a):
        return "misma_plantilla_numerica"

    blk_a, blk_b = clave_esqueleto_bloque(a), clave_esqueleto_bloque(b)
    if blk_a == blk_b and _tiene_marcador_numerico(blk_a[0]):
        return "misma_plantilla_numerica_bloque"

    if (
        sk_a
        and sk_b
        and _tiene_marcador_numerico(sk_a)
        and SequenceMatcher(None, sk_a, sk_b).ratio() >= 0.92
    ):
        ta, tb = tipo_de(a), tipo_de(b)
        if ta == "Calculo" and tb == "Calculo":
            return "misma_plantilla_numerica_calculo"

    return None


def opciones_de(fila: dict) -> set[str]:
    return {
        normalizar_pregunta(fila.get("A", "")),
        normalizar_pregunta(fila.get("B", "")),
        normalizar_pregunta(fila.get("C", "")),
        normalizar_pregunta(fila.get("D", "")),
    }


def clave_enunciado(fila: dict) -> str:
    return normalizar_pregunta(enunciado_de(fila))


def clave_bloque_exacto(fila: dict) -> tuple:
    return (
        enunciado_de(fila).strip(),
        (fila.get("A") or "").strip(),
        (fila.get("B") or "").strip(),
        (fila.get("C") or "").strip(),
        (fila.get("D") or "").strip(),
    )


def clave_plantilla_exacta(t: dict) -> tuple:
    return (
        normalizar_pregunta(t.get("pregunta", "")),
        normalizar_pregunta(t.get("A", "")),
        normalizar_pregunta(t.get("B", "")),
        normalizar_pregunta(t.get("C", "")),
        normalizar_pregunta(t.get("D", "")),
        normalizar_pregunta(t.get("correcta", "")),
    )


def clave_respuesta_sustantiva(fila: dict) -> str | None:
    rc = texto_respuesta_correcta(fila)
    return rc if respuesta_es_sustantiva(rc) else None


def _motivo_definicion_equivalente(
    ca: set[str], cb: set[str], jq_c: float
) -> str | None:
    def _es_definicional(tokens_enunciado: set[str]) -> bool:
        return bool(
            tokens_enunciado
            & {"definicion", _TOKEN_DEFINICION, "definicio", "defineix", "define"}
        ) or "es" in tokens_enunciado or "és" in tokens_enunciado

    if jq_c < 0.32 or not (_es_definicional(ca) or _es_definicional(cb)):
        return None
    nucleo_a = ca - {
        "definicion",
        _TOKEN_DEFINICION,
        "definicio",
        "defineix",
        "define",
        "es",
        "és",
        "que",
        "què",
    }
    nucleo_b = cb - {
        "definicion",
        _TOKEN_DEFINICION,
        "definicio",
        "defineix",
        "define",
        "es",
        "és",
        "que",
        "què",
    }
    if jaccard(nucleo_a, nucleo_b) >= 0.50:
        return "definicion_equivalente_misma_respuesta"
    return None


def _motivo_equivalencia_semantica(
    a: dict, b: dict, qa: str, qb: str, ta: set[str], tb: set[str], oa: set[str], ob: set[str]
) -> str | None:
    del ta, tb  # firma alineada con el caller; la semántica usa tokens_contenido.
    ra, rb = texto_respuesta_correcta(a), texto_respuesta_correcta(b)
    if not ra or ra != rb or not respuesta_es_sustantiva(ra):
        return None

    ca, cb = tokens_contenido(enunciado_de(a)), tokens_contenido(enunciado_de(b))
    jq_c = jaccard(ca, cb)
    seq = SequenceMatcher(None, qa, qb).ratio()
    jo = jaccard(oa, ob)
    na, nb = numeros_enunciado(a), numeros_enunciado(b)

    if jq_c >= 0.55:
        return "misma_respuesta_mismo_significado"
    if jq_c >= 0.40 and seq >= 0.50:
        return "misma_respuesta_enunciado_equivalente"
    if na == nb and na and jq_c >= 0.30:
        return "misma_respuesta_mismos_datos"
    if seq >= 0.58 and jq_c >= 0.35:
        return "misma_respuesta_parafrasis"
    if jo >= 0.70 and jq_c >= 0.38:
        return "misma_respuesta_opciones_equivalentes"

    return _motivo_definicion_equivalente(ca, cb, jq_c)


def _motivo_similitud_superficial(
    seq: float, jq: float, jo: float
) -> str | None:
    if seq >= 0.93 and jq >= 0.75:
        return "enunciado_muy_similar"
    if seq >= 0.95 and jq >= 0.82:
        return "enunciado_casi_identico"
    if jq >= 0.88 and jo >= 0.75:
        return "misma_idea_y_opciones_parecidas"
    if jo >= 0.85 and seq >= 0.92 and jq >= 0.78:
        return "opciones_iguales_enunciado_parecido"
    if math.isclose(jo, 1.0) and seq >= 0.85:
        return "mismas_opciones_enunciado_parecido"
    return None


def motivo_duplicado(a: dict, b: dict) -> str | None:
    qa = clave_enunciado(a)
    qb = clave_enunciado(b)
    if not qa or not qb:
        return None

    if qa == qb:
        return "mismo_enunciado"

    if clave_bloque_exacto(a) == clave_bloque_exacto(b):
        return "bloque_identico"

    ta, tb = tokens(enunciado_de(a)), tokens(enunciado_de(b))
    oa, ob = opciones_de(a), opciones_de(b)
    seq = SequenceMatcher(None, qa, qb).ratio()
    jq = jaccard(ta, tb)
    jo = jaccard(oa, ob)

    superficial = _motivo_similitud_superficial(seq, jq, jo)
    if superficial:
        return superficial

    num = _motivo_variante_numerica(a, b, qa, qb)
    if num:
        return num

    fam = _motivo_familia_plantilla(a, b)
    if fam:
        return fam

    return _motivo_equivalencia_semantica(a, b, qa, qb, ta, tb, oa, ob)


def es_duplicado(a: dict, b: dict) -> bool:
    return motivo_duplicado(a, b) is not None


def es_duplicado_de_alguna(candidata: dict, otras: list[dict]) -> bool:
    for o in otras:
        if es_duplicado(candidata, o):
            return True
    return False


def _bucket_key_plantilla(fila: dict) -> str:
    toks = sorted(clave_enunciado(fila).split())
    if len(toks) >= 3:
        return " ".join(toks[:3])
    return clave_enunciado(fila)[:40]


def _decidir_conservar_plantilla(
    t: dict,
    *,
    solo_exactas: bool,
    seen_exact: set[tuple],
    seen_enunciado: set[str],
    kept_by_bucket: dict[str, list[dict]],
) -> tuple[bool, str]:
    """Devuelve (conservar, motivo_descarte) con motivo '' si se conserva."""
    k = clave_plantilla_exacta(t)
    if k in seen_exact:
        return False, "exact"
    if solo_exactas:
        seen_exact.add(k)
        return True, ""
    comp = {"Pregunta": t.get("pregunta", ""), **t}
    eq = clave_enunciado(comp)
    if eq and eq in seen_enunciado:
        return False, "similar"
    bucket = _bucket_key_plantilla(comp)
    if es_duplicado_de_alguna(comp, kept_by_bucket[bucket]):
        return False, "similar"
    kept_by_bucket[bucket].append(comp)
    if eq:
        seen_enunciado.add(eq)
    seen_exact.add(k)
    return True, ""


def deduplicar_plantillas_dict(
    plantillas: dict, solo_exactas: bool = False
) -> tuple[dict, int, int]:
    """Unicidad global entre materias. Prioriza general > repuesto > … > dataset_*."""
    priority = {
        "general": 0,
        "repuesto": 1,
        "reserva": 1,
        "internet": 2,
        "dificil": 3,
        "calculo": 4,
        "dataset_480": 5,
        "ampliado_var": 6,
        "ampliado_perm": 7,
        "ampliado_num": 8,
    }
    exact_removed = 0
    similar_removed = 0

    flat: list[tuple[str, dict]] = []
    for tema, items in plantillas.items():
        for t in items:
            flat.append((tema, t))

    flat.sort(
        key=lambda x: (
            priority.get(str(x[1].get("uso", "")).lower(), 9),
            x[0],
        )
    )

    from collections import defaultdict

    seen_exact: set[tuple] = set()
    seen_enunciado: set[str] = set()
    kept_by_bucket: dict[str, list[dict]] = defaultdict(list)
    cleaned: dict = {tema: [] for tema in plantillas}

    for tema, t in flat:
        ok, motivo = _decidir_conservar_plantilla(
            t,
            solo_exactas=solo_exactas,
            seen_exact=seen_exact,
            seen_enunciado=seen_enunciado,
            kept_by_bucket=kept_by_bucket,
        )
        if not ok:
            if motivo == "exact":
                exact_removed += 1
            else:
                similar_removed += 1
            continue
        cleaned[tema].append(t)

    return cleaned, exact_removed, similar_removed


def _plantilla_duplica_dataset(
    t: dict,
    tema: str,
    ds_por_bucket: dict[str, list[dict]],
    enunciado_por_materia: dict[str, set[str]],
) -> bool:
    if es_uso_copia_dataset(str(t.get("uso", ""))):
        return False
    comp = {"Pregunta": t.get("pregunta", ""), **t}
    eq = clave_enunciado(comp)
    if eq and eq in enunciado_por_materia.get(tema, set()):
        return True
    candidatos = ds_por_bucket.get(_bucket_key_plantilla(comp), [])
    return bool(candidatos and es_duplicado_de_alguna(comp, candidatos))


def quitar_plantillas_presentes_en_dataset(
    plantillas: dict, filas_dataset: list[dict]
) -> tuple[dict, int]:
    """Elimina plantillas del pool que dupliquen el CSV (conserva copias ``dataset_*``)."""
    from collections import defaultdict

    from utils_dataset_csv import materia_de_fila

    ds_por_bucket: dict[str, list[dict]] = defaultdict(list)
    enunciado_por_materia: dict[str, set[str]] = defaultdict(set)
    for r in filas_dataset:
        ds_por_bucket[_bucket_key_plantilla(r)].append(r)
        materia = materia_de_fila(r)
        eq = clave_enunciado(r)
        if materia and eq:
            enunciado_por_materia[materia].add(eq)

    removed = 0
    cleaned: dict = {}
    for tema, items in plantillas.items():
        kept = []
        for t in items:
            if _plantilla_duplica_dataset(
                t, tema, ds_por_bucket, enunciado_por_materia
            ):
                removed += 1
            else:
                kept.append(t)
        cleaned[tema] = kept
    return cleaned, removed
