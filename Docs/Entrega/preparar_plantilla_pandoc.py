"""Genera y ajusta la plantilla Pandoc para Word (estilos, pie con paginación)."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

_DIR_IMPORT = Path(__file__).resolve().parent
if str(_DIR_IMPORT) not in sys.path:
    sys.path.insert(0, str(_DIR_IMPORT))
from estilos_toc_word import compactar_estilos_toc as _compactar_estilos_toc

DIR = Path(__file__).resolve().parent
DEFAULT = DIR / "pandoc_reference_default.docx"
REFERENCE = DIR / "pandoc_reference.docx"

_FOOTER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:p>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:fldChar w:fldCharType="separate"/></w:r>
    <w:r><w:t>1</w:t></w:r>
    <w:r><w:fldChar w:fldCharType="end"/></w:r>
  </w:p>
</w:ftr>
"""


def _pandoc_bin() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("No se encontró pandoc en el PATH.")
    return pandoc


def exportar_plantilla_por_defecto(destino: Path = DEFAULT) -> None:
    resultado = subprocess.run(
        [_pandoc_bin(), "--print-default-data-file", "reference.docx"],
        capture_output=True,
        check=True,
    )
    destino.write_bytes(resultado.stdout)


def _quitar_cursiva_estilo(xml: str, style_id: str) -> str:
    pattern = rf'<w:style w:type="(?:paragraph|character)" w:styleId="{style_id}".*?</w:style>'

    def _fix_style(match: re.Match[str]) -> str:
        chunk = match.group(0)
        chunk = re.sub(r"<w:i\b[^>]*/>", "", chunk)
        chunk = re.sub(r"<w:iCs\b[^>]*/>", "", chunk)
        chunk = re.sub(r"<w:i\b[^>]*>.*?</w:i>", "", chunk, flags=re.DOTALL)
        chunk = re.sub(r"<w:iCs\b[^>]*>.*?</w:iCs>", "", chunk, flags=re.DOTALL)
        return chunk

    return re.sub(pattern, _fix_style, xml, count=1, flags=re.DOTALL)


def _ajustar_heading4(xml: str) -> str:
    for style_id in ("Heading4", "Heading4Char"):
        xml = _quitar_cursiva_estilo(xml, style_id)
    return xml


def _siguiente_rid(rels_xml: str) -> str:
    ids = [int(n) for n in re.findall(r'Id="rId(\d+)"', rels_xml)]
    return f"rId{max(ids, default=0) + 1}"


def _añadir_pie_pagina(
    document_xml: str,
    rels_xml: str,
    content_types_xml: str,
) -> tuple[str, str, str, bytes]:
    if "footer1.xml" in rels_xml:
        return document_xml, rels_xml, content_types_xml, b""

    footer_rid = _siguiente_rid(rels_xml)
    footer_ref = f'<w:footerReference w:type="default" r:id="{footer_rid}"/>'
    document_xml, n = re.subn(
        r"(</w:sectPr>)",
        footer_ref + r"\1",
        document_xml,
        count=1,
    )
    if n == 0:
        raise RuntimeError("No se encontró w:sectPr en la plantilla de referencia.")

    rel_line = (
        f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" '
        f'Id="{footer_rid}" Target="footer1.xml"/>'
    )
    rels_xml = rels_xml.replace("</Relationships>", rel_line + "</Relationships>")
    if "footer1.xml" not in content_types_xml:
        content_types_xml = content_types_xml.replace(
            "</Types>",
            '<Override PartName="/word/footer1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
            "</Types>",
        )
    return document_xml, rels_xml, content_types_xml, _FOOTER_XML.encode("utf-8")


def crear_plantilla_memoria(
    origen: Path = DEFAULT,
    destino: Path = REFERENCE,
) -> None:
    if not origen.is_file():
        exportar_plantilla_por_defecto(origen)
    tmp = destino.with_suffix(".tmp.docx")
    shutil.copyfile(origen, tmp)

    document_xml = ""
    rels_xml = ""
    content_types_xml = ""
    footer_bytes = b""

    with zipfile.ZipFile(tmp, "r") as zin:
        styles_xml = zin.read("word/styles.xml").decode("utf-8")
        styles_xml = _ajustar_heading4(styles_xml)
        styles_xml = _compactar_estilos_toc(styles_xml)
        document_xml = zin.read("word/document.xml").decode("utf-8")
        rels_xml = zin.read("word/_rels/document.xml.rels").decode("utf-8")
        content_types_xml = zin.read("[Content_Types].xml").decode("utf-8")
        document_xml, rels_xml, content_types_xml, footer_bytes = _añadir_pie_pagina(
            document_xml,
            rels_xml,
            content_types_xml,
        )

        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/styles.xml":
                    data = styles_xml.encode("utf-8")
                elif item.filename == "word/document.xml":
                    data = document_xml.encode("utf-8")
                elif item.filename == "word/_rels/document.xml.rels":
                    data = rels_xml.encode("utf-8")
                elif item.filename == "[Content_Types].xml":
                    data = content_types_xml.encode("utf-8")
                zout.writestr(item, data)
            if footer_bytes:
                zout.writestr("word/footer1.xml", footer_bytes)

    tmp.unlink(missing_ok=True)


def inspeccionar(docx: Path) -> None:
    with zipfile.ZipFile(docx) as z:
        names = z.namelist()
        print("footer:", "word/footer1.xml" in names)
        xml = z.read("word/styles.xml").decode("utf-8")
    for style in ("Heading1", "Heading2", "Heading3", "Heading4"):
        m = re.search(
            rf'<w:style w:type="paragraph" w:styleId="{style}".*?</w:style>',
            xml,
            re.DOTALL,
        )
        if not m:
            print(style, "NOT FOUND")
            continue
        chunk = m.group(0)
        italic = bool(re.search(r"<w:i\b[^/]*/>", chunk))
        bold = bool(re.search(r"<w:b\b[^/]*/>", chunk))
        print(style, "bold=", bold, "italic=", italic)


if __name__ == "__main__":
    crear_plantilla_memoria()
    print("Plantilla lista:", REFERENCE.name)
    inspeccionar(REFERENCE)
