"""Estilos compactos del índice (TOC) para documentos Word OOXML."""
from __future__ import annotations

import re

# Tamaños en half-points (24 = 12 pt). Interlineado en twips (288 ≈ 14,4 pt).
_TOC_CFG: dict[str, dict[str, int | None]] = {
    "TOCHeading": {"sz": 28, "after": 140, "line": 336, "left": None, "hanging": None},
    "TOC1": {"sz": 24, "after": 0, "line": 288, "left": 220, "hanging": 220},
    "TOC2": {"sz": 22, "after": 0, "line": 276, "left": 360, "hanging": 180},
    "TOC3": {"sz": 22, "after": 0, "line": 276, "left": 480, "hanging": 180},
}

_NOMBRES = {
    "TOCHeading": "TOC Heading",
    "TOC1": "toc 1",
    "TOC2": "toc 2",
    "TOC3": "toc 3",
}


def _pat_estilo(style_id: str) -> str:
    return rf"<w:style\b[^>]*\bw:styleId=\"{style_id}\"[^>]*>.*?</w:style>"


def _bloque_nuevo(style_id: str, cfg: dict[str, int | None]) -> str:
    ind = ""
    if cfg["left"] is not None:
        ind = (
            f'<w:ind w:left="{cfg["left"]}" w:hanging="{cfg["hanging"]}"/>'
        )
    extra_ppr = (
        '<w:outlineLvl w:val="9"/>' if style_id == "TOCHeading" else ""
    )
    if style_id == "TOCHeading":
        cabecera = (
            f'<w:basedOn w:val="Heading1"/>'
            f'<w:next w:val="BodyText"/>'
        )
    else:
        cabecera = (
            f'<w:basedOn w:val="Normal"/>'
            f'<w:next w:val="Normal"/>'
            f"<w:autoRedefine/>"
        )
    return (
        f'  <w:style w:type="paragraph" w:styleId="{style_id}">\n'
        f'    <w:name w:val="{_NOMBRES[style_id]}"/>\n'
        f"    {cabecera}\n"
        f'    <w:uiPriority w:val="39"/>\n'
        f"    <w:unhideWhenUsed/>\n"
        f"    <w:qFormat/>\n"
        f"    <w:pPr>\n"
        f'      <w:spacing w:before="0" w:after="{cfg["after"]}" '
        f'w:line="{cfg["line"]}" w:lineRule="auto"/>\n'
        f"      {ind}\n"
        f"      {extra_ppr}\n"
        f"    </w:pPr>\n"
        f"    <w:rPr>\n"
        f'      <w:sz w:val="{cfg["sz"]}"/>\n'
        f'      <w:szCs w:val="{cfg["sz"]}"/>\n'
        f"    </w:rPr>\n"
        f"  </w:style>"
    )


def _aplicar_cfg(bloque: str, cfg: dict[str, int | None]) -> str:
    bloque = re.sub(r"<w:spacing[^>]*/>\s*", "", bloque)
    if cfg["left"] is not None:
        bloque = re.sub(r"<w:ind[^>]*/>\s*", "", bloque)
    spacing = (
        f'<w:spacing w:before="0" w:after="{cfg["after"]}" '
        f'w:line="{cfg["line"]}" w:lineRule="auto"/>'
    )
    ind = ""
    if cfg["left"] is not None:
        ind = (
            f'<w:ind w:left="{cfg["left"]}" w:hanging="{cfg["hanging"]}"/>'
        )
    if "<w:pPr>" in bloque:
        bloque = bloque.replace("<w:pPr>", f"<w:pPr>{spacing}{ind}", 1)
    else:
        bloque = re.sub(
            r"(<w:style\b[^>]*>)",
            rf"\1<w:pPr>{spacing}{ind}</w:pPr>",
            bloque,
            count=1,
        )
    if "<w:rPr>" in bloque:
        if re.search(r"<w:sz\b", bloque):
            bloque = re.sub(
                r'<w:sz w:val="\d+"', f'<w:sz w:val="{cfg["sz"]}"', bloque
            )
            bloque = re.sub(
                r'<w:szCs w:val="\d+"', f'<w:szCs w:val="{cfg["sz"]}"', bloque
            )
        else:
            bloque = bloque.replace(
                "</w:rPr>",
                f'<w:sz w:val="{cfg["sz"]}"/>'
                f'<w:szCs w:val="{cfg["sz"]}"/></w:rPr>',
                1,
            )
    else:
        bloque = bloque.replace(
            "</w:style>",
            f'<w:rPr><w:sz w:val="{cfg["sz"]}"/>'
            f'<w:szCs w:val="{cfg["sz"]}"/></w:rPr></w:style>',
            1,
        )
    return bloque


def compactar_estilos_toc(styles_xml: str) -> str:
    """Aplica tipografía del índice (legible, una página) e inyecta TOC1/TOC2 si faltan."""
    for style_id, cfg in _TOC_CFG.items():
        pat = _pat_estilo(style_id)
        match = re.search(pat, styles_xml, flags=re.DOTALL)
        if match:
            nuevo = _aplicar_cfg(match.group(0), cfg)
            styles_xml = (
                styles_xml[: match.start()] + nuevo + styles_xml[match.end() :]
            )
        else:
            bloque = _bloque_nuevo(style_id, cfg)
            styles_xml = styles_xml.replace(
                "</w:styles>", f"{bloque}\n</w:styles>", 1
            )
    return styles_xml
