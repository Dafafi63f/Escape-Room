"""Reordena Word: portada+resumen (p.1) → índice (p.2) → cuerpo (desde p.3)."""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

_ENTREGA = Path(__file__).resolve().parent
if str(_ENTREGA) not in sys.path:
    sys.path.insert(0, str(_ENTREGA))
from estilos_toc_word import compactar_estilos_toc as _compactar_estilos_toc

_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_PAGEBREAK = (
    f'<w:p xmlns:w="{_NS}"><w:r><w:br w:type="page"/></w:r></w:p>'
)
_SDT_TOC_RE = re.compile(
    r"<w:sdt\b[^>]*>.*?Table of Contents.*?</w:sdt>",
    re.DOTALL,
)


def _extraer_sdt_indice(contenido: str) -> tuple[str | None, str]:
    coincidencia = _SDT_TOC_RE.search(contenido)
    if not coincidencia:
        return None, contenido
    sin_indice = contenido[: coincidencia.start()] + contenido[coincidencia.end() :]
    return coincidencia.group(0), sin_indice


def _texto_parrafo(xml: str) -> str:
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml)).strip()


def _es_salto_pagina(xml: str) -> bool:
    return 'w:type="page"' in xml


def _estilo_parrafo(xml: str) -> str | None:
    m = re.search(r'<w:pStyle w:val="([^"]+)"', xml)
    return m.group(1) if m else None


def _es_nodo_parrafo(nodo: str) -> bool:
    return nodo.startswith("<w:p")


def _es_nodo_bookmark_start(nodo: str) -> bool:
    return nodo.startswith("<w:bookmarkStart")


def _es_nodo_bookmark_end(nodo: str) -> bool:
    return nodo.startswith("<w:bookmarkEnd")


def _es_nodo_tabla(nodo: str) -> bool:
    return nodo.startswith("<w:tbl")


def _es_nodo_sdt(nodo: str) -> bool:
    return nodo.startswith("<w:sdt")


def _extraer_elemento_cerrado(xml: str, local: str) -> tuple[str, int]:
    """Extrae un elemento OOXML contando etiquetas anidadas del mismo tipo."""
    abrir = f"<w:{local}"
    cerrar = f"</w:{local}>"
    start = xml.find(abrir)
    if start < 0:
        return "", 0
    pos = start
    depth = 0
    while pos < len(xml):
        next_open = xml.find(abrir, pos)
        next_close = xml.find(cerrar, pos)
        if next_close < 0:
            return xml[start:], len(xml) - start
        if next_open >= 0 and next_open < next_close:
            depth += 1
            pos = next_open + len(abrir)
        else:
            depth -= 1
            pos = next_close + len(cerrar)
            if depth == 0:
                return xml[start:pos], pos
    return xml[start:], len(xml) - start


def _nodos_top_level(cuerpo: str) -> list[str]:
    """Nodos de primer nivel en w:body (no aplana párrafos dentro de tablas)."""
    nodos: list[str] = []
    i = 0
    n = len(cuerpo)
    while i < n:
        while i < n and cuerpo[i].isspace():
            i += 1
        if i >= n:
            break
        if cuerpo.startswith("<w:bookmarkStart", i):
            m = re.match(r"<w:bookmarkStart\b[^>]*/>", cuerpo[i:])
            if m:
                nodos.append(m.group(0))
                i += m.end()
                continue
        if cuerpo.startswith("<w:bookmarkEnd", i):
            m = re.match(r"<w:bookmarkEnd\b[^>]*/>", cuerpo[i:])
            if m:
                nodos.append(m.group(0))
                i += m.end()
                continue
        if cuerpo.startswith("<w:tbl", i):
            bloque, consumed = _extraer_elemento_cerrado(cuerpo[i:], "tbl")
            if consumed:
                nodos.append(bloque)
                i += consumed
                continue
        if cuerpo.startswith("<w:sdt", i):
            bloque, consumed = _extraer_elemento_cerrado(cuerpo[i:], "sdt")
            if consumed:
                nodos.append(bloque)
                i += consumed
                continue
        if cuerpo.startswith("<w:p", i):
            m = re.match(r"<w:p\b.*?</w:p>", cuerpo[i:], re.DOTALL)
            if m:
                nodos.append(m.group(0))
                i += m.end()
                continue
        i += 1
    return nodos


def _split_body_nodos(contenido: str) -> tuple[list[str], str]:
    sectpr_m = re.search(r"(<w:sectPr\b.*?</w:sectPr>\s*)$", contenido, re.DOTALL)
    sectpr = sectpr_m.group(1) if sectpr_m else ""
    cuerpo = contenido[: sectpr_m.start()] if sectpr_m else contenido
    return _nodos_top_level(cuerpo), sectpr


def _indices_parrafos(nodos: list[str]) -> list[int]:
    return [i for i, nodo in enumerate(nodos) if _es_nodo_parrafo(nodo)]


def _parrafos_desde_nodos(nodos: list[str]) -> list[str]:
    return [nodo for nodo in nodos if _es_nodo_parrafo(nodo)]


def _nodos_solo_parrafos(nodos: list[str], indices_para: list[int]) -> list[str]:
    objetivo = set(indices_para)
    resultado: list[str] = []
    pi = -1
    for nodo in nodos:
        if not _es_nodo_parrafo(nodo):
            continue
        pi += 1
        if pi in objetivo:
            resultado.append(nodo)
    return resultado


def _nodos_cuerpo_con_marcadores(nodos: list[str], indices_para: list[int]) -> list[str]:
    objetivo = set(indices_para)
    resultado: list[str] = []
    pendiente: list[str] = []
    pi = -1
    for nodo in nodos:
        if _es_nodo_bookmark_start(nodo):
            pendiente.append(nodo)
            continue
        if _es_nodo_bookmark_end(nodo):
            if pendiente:
                pendiente.pop()
            elif resultado:
                resultado.append(nodo)
            continue
        if not _es_nodo_parrafo(nodo):
            if pendiente:
                resultado.extend(pendiente)
                pendiente.clear()
            resultado.append(nodo)
            continue
        pi += 1
        if pi not in objetivo:
            pendiente.clear()
            continue
        resultado.extend(pendiente)
        pendiente.clear()
        resultado.append(nodo)
    return resultado


def _quitar_saltos_pagina(nodos: list[str], *, al_inicio: bool = False, al_final: bool = False) -> list[str]:
    resultado = list(nodos)
    if al_inicio:
        while resultado and _es_nodo_parrafo(resultado[0]) and _es_salto_pagina(resultado[0]):
            resultado.pop(0)
    if al_final:
        while resultado and _es_nodo_parrafo(resultado[-1]) and _es_salto_pagina(resultado[-1]):
            resultado.pop()
    return resultado


def _es_bloque_indice(parrafos: list[str], i: int) -> bool:
    estilo = _estilo_parrafo(parrafos[i])
    if estilo == "TOCHeading":
        return True
    if estilo is not None:
        return False
    if _texto_parrafo(parrafos[i]):
        return False
    j = i + 1
    while j < len(parrafos) and not _texto_parrafo(parrafos[j]) and not _estilo_parrafo(parrafos[j]):
        if "TOC" in parrafos[j] or "instrText" in parrafos[j]:
            return True
        j += 1
    return "TOC" in parrafos[i]


def _rango_bloque_indice(parrafos: list[str], inicio: int) -> range:
    fin = inicio + 1
    while fin < len(parrafos):
        if _estilo_parrafo(parrafos[fin]) and _estilo_parrafo(parrafos[fin]) != "TOCHeading":
            break
        if _texto_parrafo(parrafos[fin]) and _estilo_parrafo(parrafos[fin]) != "TOCHeading":
            break
        fin += 1
    return range(inicio, fin)


def _es_author(parrafo: str) -> bool:
    return _estilo_parrafo(parrafo) == "Author"


def _es_nota_portada_latex(parrafo: str) -> bool:
    estilo = _estilo_parrafo(parrafo)
    if estilo not in ("FirstParagraph", "BodyText", None):
        return False
    texto = _texto_parrafo(parrafo)
    return (
        texto.startswith("Nota sobre")
        or "Versión de entrega" in texto
        or texto.startswith("El detalle técnico")
    )


def _rango_bloque_abstract(parrafos: list[str], inicio: int) -> range:
    fin = inicio + 1
    while fin < len(parrafos) and _estilo_parrafo(parrafos[fin]) == "Abstract":
        fin += 1
    return range(inicio, fin)


def _es_inicio_portada(parrafo: str) -> bool:
    if _estilo_parrafo(parrafo) != "FirstParagraph":
        return False
    texto = _texto_parrafo(parrafo)
    return texto.startswith("Alumno:") or texto.startswith("**Alumno:")


def _rango_bloque_portada(parrafos: list[str], inicio: int) -> range:
    fin = inicio
    while fin < len(parrafos):
        if _es_salto_pagina(parrafos[fin]):
            return range(inicio, fin + 1)
        fin += 1
    return range(inicio, min(inicio + 1, len(parrafos)))


def _bloque_portada_latex(parrafos: list[str]) -> tuple[list[str], set[int]]:
    idx_author = next((i for i, p in enumerate(parrafos) if _es_author(p)), None)
    if idx_author is None:
        return [], set()

    indices: set[int] = {idx_author}
    bloque = [parrafos[idx_author]]
    for i, p in enumerate(parrafos):
        if i in indices:
            continue
        if _es_nota_portada_latex(p):
            bloque.append(p)
            indices.add(i)
    return bloque, indices


def _rango_bloque_resumen_md(parrafos: list[str], inicio: int) -> range:
    fin = inicio + 1
    while fin < len(parrafos):
        estilo = _estilo_parrafo(parrafos[fin])
        if estilo and estilo.startswith("Heading"):
            break
        fin += 1
    return range(inicio, fin)


def _bloque_resumen_md(parrafos: list[str]) -> tuple[list[str], set[int]]:
    idx = next(
        (
            i
            for i, p in enumerate(parrafos)
            if _estilo_parrafo(p) == "Heading1" and _texto_parrafo(p) == "Resumen"
        ),
        None,
    )
    if idx is None:
        return [], set()
    rango = set(_rango_bloque_resumen_md(parrafos, idx))
    return [parrafos[i] for i in sorted(rango)], rango


def _arreglar_campo_toc(xml: str) -> str:
    """Asegura instrucción TOC válida (con enlaces) y marca el campo como pendiente de actualizar."""
    patron = re.compile(
        r'(<w:instrText[^>]*>)\s*([^<]*)(</w:instrText>)',
    )
    reemplazado = False

    def _normalizar_instr(instr: str) -> str:
        texto = instr.strip()
        if not texto.startswith("TOC"):
            texto = f"TOC {texto}"
        if '\\o "1-2"' not in texto:
            texto = re.sub(
                r'\\o\s+"1-\d+"',
                lambda _m: r'\o "1-2"',
                texto,
            )
        if "\\h" not in texto:
            texto += " \\h"
        if "\\z" not in texto:
            texto += " \\z"
        if "\\u" not in texto:
            texto += " \\u"
        return texto

    for match in patron.finditer(xml):
        cuerpo = match.group(2)
        if "TOC" not in cuerpo and '\\o' not in cuerpo:
            continue
        nuevo = match.group(1) + _normalizar_instr(cuerpo) + match.group(3)
        xml = xml[: match.start()] + nuevo + xml[match.end() :]
        reemplazado = True
        break

    if not reemplazado:
        return xml

    bloque_toc = re.search(
        r"<w:p\b[^>]*>.*?TOC \\o.*?</w:p>",
        xml,
        re.DOTALL,
    )
    if not bloque_toc:
        return xml
    bloque = bloque_toc.group(0)
    bloque_nuevo = re.sub(
        r'<w:fldChar w:fldCharType="begin"(?![^>]*\bw:dirty\b)',
        '<w:fldChar w:fldCharType="begin" w:dirty="true"',
        bloque,
        count=1,
    )
    return xml[: bloque_toc.start()] + bloque_nuevo + xml[bloque_toc.end() :]


def _activar_update_fields(settings_xml: str) -> str:
    if "<w:updateFields" in settings_xml:
        return re.sub(
            r'<w:updateFields w:val="(?:false|0)"',
            '<w:updateFields w:val="true"',
            settings_xml,
            count=1,
        )
    return settings_xml.replace(
        "</w:settings>",
        '<w:updateFields w:val="true"/></w:settings>',
    )


def ajustar_portada_indice(docx: Path) -> bool:
    """Coloca portada y resumen en p.1, índice en p.2 y el cuerpo desde p.3."""
    if not docx.is_file():
        return False

    tmp = docx.with_suffix(".ajuste.tmp.docx")
    shutil.copyfile(docx, tmp)
    with zipfile.ZipFile(tmp, "r") as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        m_body = re.search(r"(<w:body>)(.*)(</w:body>)", xml, re.DOTALL)
        if not m_body:
            tmp.unlink(missing_ok=True)
            return False

        nodos, sectpr = _split_body_nodos(m_body.group(2))
        bloque_sdt_toc, _ = _extraer_sdt_indice(m_body.group(2))
        if bloque_sdt_toc is not None:
            _, contenido_sin_toc = _extraer_sdt_indice(m_body.group(2))
            nodos, sectpr = _split_body_nodos(contenido_sin_toc)
        parrafos = _parrafos_desde_nodos(nodos)
        if not parrafos:
            tmp.unlink(missing_ok=True)
            return False

        idx_toc = next((i for i, p in enumerate(parrafos) if _es_bloque_indice(parrafos, i)), None)
        if idx_toc is None and bloque_sdt_toc is None:
            tmp.unlink(missing_ok=True)
            return False

        rango_toc = set(_rango_bloque_indice(parrafos, idx_toc)) if idx_toc is not None else set()

        idx_abs = next(
            (i for i, p in enumerate(parrafos) if _estilo_parrafo(p) == "AbstractTitle"),
            None,
        )
        rango_abs: set[int] = set()
        if idx_abs is not None:
            rango_abs = set(_rango_bloque_abstract(parrafos, idx_abs))

        idx_portada = next(
            (i for i, p in enumerate(parrafos) if _es_inicio_portada(p)),
            None,
        )
        rango_portada: set[int] = set()
        if idx_portada is not None:
            rango_portada = set(_rango_bloque_portada(parrafos, idx_portada))
        else:
            _, rango_portada = _bloque_portada_latex(parrafos)

        _, rango_resumen_md = _bloque_resumen_md(parrafos)

        rango_notas_latex = {
            i for i, p in enumerate(parrafos) if _es_nota_portada_latex(p)
        }
        idx_author = next((i for i, p in enumerate(parrafos) if _es_author(p)), None)

        excluir = (
            rango_toc
            | rango_portada
            | rango_abs
            | rango_resumen_md
            | rango_notas_latex
            | ({idx_author} if idx_author is not None else set())
            | {i for i, p in enumerate(parrafos) if _estilo_parrafo(p) == "Title"}
        )

        titulo_idx = [i for i, p in enumerate(parrafos) if _estilo_parrafo(p) == "Title"]
        cuerpo_idx = [i for i in range(len(parrafos)) if i not in excluir]

        if idx_portada is not None:
            pagina1_idx = titulo_idx + sorted(rango_portada) + sorted(rango_resumen_md)
        elif idx_author is not None:
            pagina1_idx = (
                titulo_idx
                + [idx_author]
                + sorted(rango_abs)
                + sorted(rango_notas_latex)
            )
        else:
            pagina1_idx = (
                titulo_idx
                + sorted(rango_portada)
                + sorted(rango_abs)
                + sorted(rango_resumen_md)
            )

        pagina1 = _nodos_solo_parrafos(nodos, pagina1_idx)
        pagina1 = _quitar_saltos_pagina(pagina1, al_final=True)
        if pagina1:
            pagina1.append(_PAGEBREAK)

        bloque_toc = (
            [bloque_sdt_toc]
            if bloque_sdt_toc is not None
            else _nodos_solo_parrafos(nodos, sorted(rango_toc))
        )
        bloque_cuerpo = _nodos_cuerpo_con_marcadores(nodos, cuerpo_idx)
        bloque_cuerpo = _quitar_saltos_pagina(bloque_cuerpo, al_inicio=True)

        nuevo_cuerpo = pagina1 + bloque_toc + [_PAGEBREAK] + bloque_cuerpo + [sectpr]
        nuevo_xml = _arreglar_campo_toc(
            xml[: m_body.start(2)]
            + "".join(nuevo_cuerpo)
            + xml[m_body.end(2) :]
        )

        styles_xml = zin.read("word/styles.xml").decode("utf-8")
        styles_xml = _compactar_estilos_toc(styles_xml)
        settings_xml = zin.read("word/settings.xml").decode("utf-8")
        settings_xml = _activar_update_fields(settings_xml)

        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = nuevo_xml.encode("utf-8")
                elif item.filename == "word/settings.xml":
                    data = settings_xml.encode("utf-8")
                elif item.filename == "word/styles.xml":
                    data = styles_xml.encode("utf-8")
                zout.writestr(item, data)

    tmp.unlink(missing_ok=True)
    return True
