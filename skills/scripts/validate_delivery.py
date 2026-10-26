"""Check report context, embedded Office images and original CSV integrity offline.

Layout and chat presentation still require visual inspection. PDF image inspection
uses PyMuPDF if already available; otherwise the command reports incomplete checks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import posixpath
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile

REL = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DRAWING = "http://schemas.openxmlformats.org/drawingml/2006/main"


def load_json(path):
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant)


def validate_schema(value, schema, root=None, location="context"):
    """Evaluate the JSON Schema keywords used by the bundled delivery contract."""
    supported = {"$schema", "$id", "title", "description", "default", "examples", "$defs", "$ref", "type",
                 "required", "additionalProperties", "properties", "items", "enum", "const", "minimum",
                 "minLength", "minItems", "pattern", "uniqueItems", "format"}
    if set(schema) - supported:
        raise ValueError("Unsupported schema keyword; update the bundled validator before using this contract.")
    root = schema if root is None else root
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/"):
            raise ValueError("Only bundled local schema references are supported.")
        target = root
        for part in reference[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return validate_schema(value, target, root, location)
    kinds = {
        "object": isinstance(value, dict), "array": isinstance(value, list),
        "string": isinstance(value, str), "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and math.isfinite(value)),
        "null": value is None,
    }
    expected = schema.get("type")
    if expected and not any(kinds[kind] for kind in ([expected] if isinstance(expected, str) else expected)):
        raise ValueError(f"{location}: expected {expected}")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{location}: unexpected constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{location}: value outside enum")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise ValueError(f"{location}: missing {sorted(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - properties.keys():
            raise ValueError(f"{location}: unknown properties")
        for key, child in value.items():
            if key in properties:
                validate_schema(child, properties[key], root, f"{location}.{key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"{location}: too few items")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise ValueError(f"{location}: duplicate items")
        for index, child in enumerate(value):
            if "items" in schema:
                validate_schema(child, schema["items"], root, f"{location}[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or ("pattern" in schema and not re.search(schema["pattern"], value)):
            raise ValueError(f"{location}: invalid string")
        if schema.get("format") == "date-time":
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError(f"{location}: timestamp must include timezone")
    if kinds["number"] and "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"{location}: value below minimum")


def reference_root():
    root = Path(__file__).resolve().parent.parent
    return root / "references" if (root / "references").is_dir() else root / "_shared"


def validate_context(context, base: Path):
    references = reference_root()
    validate_schema(context, load_json(references / "analysis-context.schema.json"))
    concepts = {item["id"] for item in load_json(references / "concepts.json")["concepts"]}
    tools = {item["name"] for item in load_json(references / "tools.json")["tools"]}
    companies = set(context["scope"]["company_ids"])
    for entity in context["entities"]:
        if entity["concept_id"] not in concepts:
            raise ValueError(f"Unknown concept: {entity['concept_id']}")
    if context["period"] is not None:
        validate_period(context["period"])
    for metric in context["metrics"]:
        if metric["source_tool"] not in tools:
            raise ValueError(f"Unknown metric source tool: {metric['source_tool']}")
        if not set(metric["scope"]["company_ids"]) <= companies:
            raise ValueError("Metric scope exceeds the declared company scope.")
        if metric["period"] is not None:
            validate_period(metric["period"])
    for visual in context.get("visualizations", []):
        view_ids = {view["id"] for view in load_json(references / "views.json")["views"]}
        if visual["view_id"] not in view_ids or not set(visual["source_tools"]) <= tools:
            raise ValueError("Unknown visualization source or view.")
    seen = set()
    for evidence in context["evidence"]:
        if evidence["id"] in seen:
            raise ValueError("Duplicate evidence ID.")
        seen.add(evidence["id"])
        if evidence["source_tool"] not in tools or evidence["entity_type"] not in concepts:
            raise ValueError("Unknown evidence source or entity type.")
        if evidence["status"] == "unavailable":
            if not evidence.get("reason"):
                raise ValueError("Unavailable evidence needs a reason.")
            continue
        if not evidence.get("image_path") or not evidence.get("sha256"):
            raise ValueError("Available evidence needs materialized bytes and SHA-256.")
        if re.match(r"[a-z]+://", evidence["image_path"], re.I):
            raise ValueError("Evidence image_path must identify a real local file, not a URL.")
        path = base / evidence["image_path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != evidence["sha256"]:
            raise ValueError(f"Evidence integrity check failed: {evidence['id']}")


def validate_period(period):
    start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
    if end <= start:
        raise ValueError("Period end must be after start.")
    from zoneinfo import ZoneInfo
    # Windows may not ship an IANA database. Validate the declared zone when available.
    try:
        ZoneInfo(period["timezone"])
    except KeyError:
        if not re.fullmatch(r"[A-Za-z_]+/[A-Za-z_]+(?:/[A-Za-z_]+)?", period["timezone"]):
            raise ValueError("Invalid timezone identifier.") from None


def audit_office(path: Path, context=None):
    embedded = {}
    text = []
    expected_part = {".docx": "word/document.xml", ".pptx": "ppt/presentation.xml",
                     ".xlsx": "xl/workbook.xml"}[path.suffix.lower()]
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        if expected_part not in names or "[Content_Types].xml" not in names:
            raise ValueError("File content does not match the requested Office format.")
        for name in sorted(names):
            if name.endswith(".rels"):
                for relationship in ET.fromstring(archive.read(name)):
                    if relationship.get("Type", "").endswith("/image") and relationship.get("TargetMode") == "External":
                        raise ValueError("External image relationship: bytes must be embedded.")
            if not name.endswith(".xml"):
                continue
            tree = ET.fromstring(archive.read(name))
            if not re.search(r"/(?:styles|theme\d*|slideLayout\d*|slideMaster\d*)\.xml$", name):
                text.extend(node.text for node in tree.iter() if node.tag.split("}")[-1] == "t" and node.text)
            relation_path = posixpath.join(posixpath.dirname(name), "_rels", posixpath.basename(name) + ".rels")
            relationships = {}
            if relation_path in names:
                relationships = {node.get("Id"): node for node in ET.fromstring(archive.read(relation_path))}
            for node in tree.iter():
                if node.tag == f"{{{DRAWING}}}blip":
                    if node.get(f"{{{OFFICE_REL}}}link"):
                        raise ValueError("Linked image: bytes must be embedded.")
                    relation_id = node.get(f"{{{OFFICE_REL}}}embed")
                elif node.tag.split("}")[-1] == "imagedata":
                    relation_id = node.get(f"{{{OFFICE_REL}}}id")
                else:
                    continue
                if not relation_id or relation_id not in relationships:
                    raise ValueError("Image drawing has no valid relationship.")
                relationship = relationships[relation_id]
                target = relationship.get("Target", "")
                target = (target.lstrip("/") if target.startswith("/") else
                          posixpath.normpath(posixpath.join(posixpath.dirname(name), target)))
                if target.startswith("../") or target not in names:
                    raise ValueError("Image drawing references missing media.")
                embedded[target] = hashlib.sha256(archive.read(target)).hexdigest()
    content_text = " ".join(" ".join(text).split())
    for placeholder in ("[Nome]", "[Área responsável]", "Título do Documento", "[dd/mm/aaaa]", "Lorem ipsum"):
        if placeholder.casefold() in content_text.casefold():
            raise ValueError(f"Unfilled institutional template text: {placeholder}")
    if context:
        for item in context["evidence"]:
            if item["status"] == "available":
                if item["sha256"] not in embedded.values():
                    raise ValueError(f"Evidence not used by an image drawing: {item['id']}")
                if " ".join(item["caption"].split()) not in content_text:
                    raise ValueError(f"Evidence caption missing: {item['id']}")
    return {"embedded_image_count": len(embedded), "image_sha256": sorted(set(embedded.values())),
            "visual_review_required": True, "structural_check": "passed"}


def audit_csv(path: Path, expected_hash=None, expected_bytes=None, expected_rows=None):
    data = path.read_bytes()
    if not data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("Original monthly CSV must have a UTF-8 BOM.")
    if data.startswith(b"\xef\xbb\xbf\xef\xbb\xbf"):
        raise ValueError("CSV has a duplicate BOM.")
    if not data.endswith(b"\r\n"):
        raise ValueError("Original monthly CSV must end with CRLF.")
    actual_hash = hashlib.sha256(data).hexdigest()
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), delimiter=";"))
    if not rows or not rows[0]:
        raise ValueError("CSV header is missing.")
    if any(len(row) != len(rows[0]) for row in rows[1:]):
        raise ValueError("CSV rows have inconsistent column counts.")
    for actual, expected, label in ((actual_hash, expected_hash, "SHA-256"), (len(data), expected_bytes, "byte count"),
                                     (len(rows) - 1, expected_rows, "row count")):
        if expected is not None and actual != expected:
            raise ValueError(f"Original CSV {label} differs from MCP metadata.")
    return {"sha256": actual_hash, "bytes": len(data), "rows": len(rows) - 1,
            "metadata_integrity_verified": all(value is not None for value in (expected_hash, expected_bytes, expected_rows)),
            "visual_review_required": False, "structural_check": "passed"}


def audit_pdf(path: Path, context=None):
    data = path.read_bytes()
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
        raise ValueError("Not a complete PDF file.")
    try:
        import fitz
    except ImportError:
        return {"structural_check": "incomplete", "visual_review_required": True,
                "reason": "PyMuPDF is unavailable; inspect PDF pages and images with the client renderer."}
    with fitz.open(path) as document:
        if document.is_encrypted or not len(document):
            raise ValueError("PDF cannot be inspected or has no pages.")
        image_count = sum(len(page.get_images(full=True)) for page in document)
        content_text = " ".join(" ".join(page.get_text() for page in document).split())
        if context:
            available = [item for item in context["evidence"] if item["status"] == "available"]
            if available and not image_count:
                raise ValueError("PDF contains no embedded images for the declared evidence.")
            for item in available:
                if " ".join(item["caption"].split()) not in content_text:
                    raise ValueError(f"PDF evidence caption missing: {item['id']}")
        return {"structural_check": "passed", "pages": len(document), "embedded_image_occurrences": image_count,
                "visual_review_required": True, "note": "Verify image identity, placement and legibility visually; PDF re-encoding may change hashes."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--context", type=Path)
    parser.add_argument("--csv-sha256")
    parser.add_argument("--csv-bytes", type=int)
    parser.add_argument("--csv-rows", type=int)
    args = parser.parse_args()
    try:
        context = load_json(args.context) if args.context else None
        if context:
            validate_context(context, args.context.resolve().parent)
        suffix = args.file.suffix.lower()
        if suffix in (".docx", ".pptx", ".xlsx"):
            report = audit_office(args.file, context)
        elif suffix == ".csv":
            report = audit_csv(args.file, args.csv_sha256, args.csv_bytes, args.csv_rows)
        elif suffix == ".pdf":
            report = audit_pdf(args.file, context)
        else:
            raise ValueError("Supported formats: DOCX, PPTX, XLSX, PDF, CSV.")
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 2 if report["structural_check"] == "incomplete" else 0
    except (ValueError, KeyError, TypeError, OSError, BadZipFile, ET.ParseError) as exc:
        print(json.dumps({"structural_check": "failed", "error": str(exc)}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
