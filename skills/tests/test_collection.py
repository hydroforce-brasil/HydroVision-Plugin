"""Offline packaging and evidence regressions; no application, database or network."""
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

SKILLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILLS))
import collection

spec = importlib.util.spec_from_file_location("validate_delivery", SKILLS / "scripts/validate_delivery.py")
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)

# A real 1x1 PNG fixture; no operational data or production side effects.
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010804000000b51c0c020000000b4944415478da6364f80f00010501012718e3660000000049454e44ae426082")


def context():
    return {
        "version": "1.0.0", "title": "Fixture sintética", "profile": "technical",
        "generated_at": "2026-10-26T12:00:00-03:00", "scope": {"company_ids": [1]},
        "period": None, "method": {}, "coverage": {}, "warnings": [],
        "entities": [{"concept_id": "logger", "id": "001", "label": "Fixture"}],
        "metrics": [], "evidence": [],
    }


def add_evidence(value, image_path):
    value["evidence"].append({"id": "photo-1", "entity_type": "logger", "entity_id": "001",
                               "caption": "Foto de teste", "source_tool": "logger_installation_images",
                               "status": "available", "placement": "body", "image_path": image_path.name,
                               "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest()})


def office_fixture(path, mode="embedded"):
    layout = {
        ".docx": ("word/document.xml", "word/_rels/document.xml.rels", "word/media/photo.png", "media/photo.png"),
        ".pptx": ("ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels", "ppt/media/photo.png", "../media/photo.png"),
        ".xlsx": ("xl/drawings/drawing1.xml", "xl/drawings/_rels/drawing1.xml.rels", "xl/media/photo.png", "../media/photo.png"),
    }
    part, relations, media, target = layout[path.suffix]
    required = {".docx": "word/document.xml", ".pptx": "ppt/presentation.xml", ".xlsx": "xl/workbook.xml"}[path.suffix]
    attributes = f'Id="rId1" Type="{delivery.OFFICE_REL}/image" Target="{target}"'
    if mode == "external":
        attributes = f'Id="rId1" Type="{delivery.OFFICE_REL}/image" Target="https://example.invalid/photo.png" TargetMode="External"'
    drawing = '<a:blip r:embed="rId1"/>' if mode != "orphan" else ""
    with ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        if required != part:
            archive.writestr(required, "<root/>")
        archive.writestr(part, f'<root xmlns:a="{delivery.DRAWING}" xmlns:r="{delivery.OFFICE_REL}"><a:t>Foto de teste</a:t>{drawing}</root>')
        archive.writestr(relations, f'<Relationships xmlns="{delivery.REL}"><Relationship {attributes}/></Relationships>')
        if mode != "missing":
            archive.writestr(media, PNG)


class CollectionTests(unittest.TestCase):
    def test_catalog_matches_all_tools_and_inherited_performance_fields(self):
        collection.validate_sources()
        datasets = collection.source_datasets()
        self.assertEqual(len(datasets), 8)
        self.assertIn("snapshot_computed_at", datasets["logger_performance"])
        self.assertTrue(datasets["loggers"] <= datasets["logger_performance"])

    def test_bundled_templates_are_byte_identical_to_inventory(self):
        inventory = collection.read_json(SKILLS / "_shared/templates.json")
        self.assertEqual(len(inventory["items"]), 5)
        bundled = [item for item in inventory["items"] if item["bundled"]]
        self.assertEqual(len(bundled), 3)
        for item in bundled:
            self.assertEqual(collection.digest(collection.ASSET_ROOT / item["asset"]), item["sha256"])
        self.assertTrue(all("asset" not in item for item in inventory["items"] if not item["bundled"]))

    def test_installed_references_cannot_escape_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("[bad](../outside.md)", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "external local"):
                collection.validate_bundle(root)

    def test_build_is_self_contained_offline_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            root = Path(tmp)
            with patch.object(collection, "BACKEND", root / "missing-backend"):
                for name in ("first", "second"):
                    collection.build(root / name)
            top = collection.read_json(root / "first/manifest.json")
            self.assertEqual(set(top["targets"]), {"claude", "chatgpt"})
            for client in top["targets"]:
                base = root / "first" / client
                manifest = collection.read_json(base / "manifest.json")
                self.assertEqual(len(manifest["packages"]), 4)
                self.assertEqual(manifest["client"], client)
                for item in manifest["packages"] + [manifest["plugin"]]:
                    self.assertEqual(collection.digest(base / item["file"]), collection.digest(root / "second" / client / item["file"]))
                    with ZipFile(base / item["file"]) as archive:
                        self.assertTrue(all(not name.startswith("/") and ".." not in Path(name).parts for name in archive.namelist()))
                        if "skill" in item:
                            skill = item["skill"]
                            self.assertEqual({name.split("/")[0] for name in archive.namelist()}, {skill})
                            archive.extractall(root / "unpacked" / client / skill)
                            collection.validate_bundle(root / "unpacked" / client / skill / skill)
                            self.assertEqual(archive.read(f"{skill}/references/client.md"), (SKILLS / "_clients" / f"{client}.md").read_bytes())
                            self.assertEqual(archive.read(f"{skill}/references/concepts.json"), (SKILLS / "_shared/concepts.json").read_bytes())
                        else:
                            self.assertEqual(sum(name.endswith("/SKILL.md") for name in archive.namelist()), 4)
                            if client == "claude":
                                self.assertIn(".claude-plugin/plugin.json", archive.namelist())
                                self.assertNotIn("plugin.json", archive.namelist())
                                server = json.loads(archive.read(".mcp.json"))["mcpServers"]["hydrovision"]
                                self.assertEqual(server["oauth"]["clientId"], "claude-ai")
                            else:
                                self.assertIn("plugin.json", archive.namelist())
                                self.assertNotIn(".mcp.json", archive.namelist())
                                self.assertNotIn(".app.json", archive.namelist())
                                self.assertNotIn(".codex-plugin/plugin.json", archive.namelist())
                                portable = json.loads(archive.read("plugin.json"))
                                self.assertNotIn("apps", portable)
                                self.assertNotIn("apps", portable["extensions"]["com.openai"])
                                server = json.loads(archive.read("mcp.json"))["mcpServers"]["hydrovision"]
                                self.assertEqual(server["extensions"]["com.openai"]["auth"]["client"]["clientId"], "chatgpt")
            for client in ("claude", "chatgpt"):
                report = root / "first" / client / "hydrovision-reports"
                for item in collection.read_json(SKILLS / "_shared/templates.json")["items"]:
                    if item["bundled"]:
                        self.assertEqual(collection.digest(report / item["asset"]), item["sha256"])

    def test_single_target_and_generated_marketplace_are_usable(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            root = Path(tmp) / "release"
            collection.build(root, target="chatgpt")
            self.assertFalse((root / "claude").exists())
            entry = collection.read_json(root / ".agents/plugins/marketplace.json")["plugins"][0]
            plugin = (root / entry["source"]["path"]).resolve()
            self.assertTrue(plugin.is_relative_to(root))
            self.assertEqual(plugin, root / "chatgpt/hydrovision-plugin")
            collection.validate_client_configuration(plugin, "chatgpt")

    def test_legacy_build_entrypoint_includes_the_complete_portable_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "release"
            subprocess.run([sys.executable, str(collection.PLUGIN_ROOT / "build.py"),
                            "--output-dir", str(output), "--target", "chatgpt"],
                           check=True, capture_output=True, text=True)
            archive_path = output / "hydrovision-chatgpt.zip"
            self.assertEqual(collection.digest(archive_path),
                             collection.digest(output / "chatgpt/hydrovision-plugin.zip"))
            self.assertFalse((output / "hydrovision-claude.zip").exists())
            with ZipFile(archive_path) as archive:
                files = set(archive.namelist())
                self.assertIn("plugin.json", files)
                self.assertIn("mcp.json", files)
                self.assertNotIn(".app.json", files)
                for skill in collection.read_json(SKILLS / "collection.json")["skills"]:
                    self.assertIn(f"skills/{skill['name']}/SKILL.md", files)
                    for reference in skill["references"]:
                        self.assertIn(f"skills/{skill['name']}/references/{reference}", files)
                for item in collection.read_json(SKILLS / "_shared/templates.json")["items"]:
                    if item["bundled"]:
                        content = archive.read(f"skills/hydrovision-reports/{item['asset']}")
                        self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])
            original_hash = collection.digest(archive_path)
            repeated = subprocess.run([sys.executable, str(collection.PLUGIN_ROOT / "build.py"),
                                       "--output-dir", str(output), "--target", "chatgpt"],
                                      capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(collection.digest(archive_path), original_hash)

    def test_overlong_listing_and_stale_compatibility_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copyfile(collection.PLUGIN_ROOT / "mcp.json", root / "mcp.json")
            plugin = collection.read_json(collection.PLUGIN_ROOT / "plugin.json")
            interface = plugin["extensions"]["com.openai"]["interface"]
            interface["shortDescription"] = "x" * 31
            collection.write_json(root / "plugin.json", plugin)
            with self.assertRaisesRegex(ValueError, "shortDescription"):
                collection.validate_client_configuration(root, "chatgpt")
            interface["shortDescription"] = "Análises HydroVision"
            collection.write_json(root / "plugin.json", plugin)
            legacy = collection.read_json(collection.PLUGIN_ROOT / ".codex-plugin/plugin.json")
            legacy["version"] = "0.1.0"
            collection.write_json(root / ".codex-plugin/plugin.json", legacy)
            with self.assertRaisesRegex(ValueError, "out of sync"):
                collection.validate_client_configuration(root, "chatgpt")

    def test_public_client_authentication_cannot_cross_clients_or_embed_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copyfile(collection.PLUGIN_ROOT / "plugin.json", root / "plugin.json")
            payload = collection.read_json(collection.PLUGIN_ROOT / "mcp.json")
            server = payload["mcpServers"]["hydrovision"]
            server["extensions"]["com.openai"]["auth"]["client"]["clientId"] = "claude-ai"
            collection.write_json(root / "mcp.json", payload)
            with self.assertRaisesRegex(ValueError, "ChatGPT public OAuth"):
                collection.validate_client_configuration(root, "chatgpt")
            server["extensions"]["com.openai"]["auth"]["client"]["clientId"] = "chatgpt"
            server["headers"] = {"Authorization": "Bearer fake-test-fixture"}
            collection.write_json(root / "mcp.json", payload)
            with self.assertRaisesRegex(ValueError, "Credentials"):
                collection.validate_client_configuration(root, "chatgpt")

    def test_stale_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp)
            folder = plugin / "skills"
            shutil.copytree(SKILLS, folder, ignore=shutil.ignore_patterns("assets", "__pycache__"))
            shutil.copytree(collection.PLUGIN_ROOT / ".claude-plugin", plugin / ".claude-plugin")
            shutil.copyfile(collection.PLUGIN_ROOT / ".mcp.json", plugin / ".mcp.json")
            shutil.copyfile(collection.PLUGIN_ROOT / "plugin.json", plugin / "plugin.json")
            shutil.copyfile(collection.PLUGIN_ROOT / "mcp.json", plugin / "mcp.json")
            reference = folder / "hydrovision-analysis/references/domain.md"
            reference.write_text("Stale generated reference", encoding="utf-8")
            with patch.object(collection, "ROOT", folder), patch.object(collection, "SHARED", folder / "_shared"), patch.object(collection, "PLUGIN_ROOT", plugin):
                with self.assertRaisesRegex(ValueError, "Stale generated reference"):
                    collection.validate_sources()


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "photo.png"
        self.image.write_bytes(PNG)

    def test_context_accepts_unknown_null_metric_and_unavailable_image(self):
        value = context()
        value["metrics"] = [{"id": "flow", "label": "Vazão estimada", "value": None, "unit": "m³/dia",
                              "source_tool": "query_data", "scope": {"company_ids": [1]}, "period": None, "coverage": {}}]
        value["evidence"] = [{"id": "no-photo", "entity_type": "logger", "entity_id": 1, "caption": "Sem acesso aos bytes",
                              "source_tool": "logger_installation_images", "status": "unavailable", "placement": "appendix", "reason": "Falha parcial"}]
        delivery.validate_context(value, self.root)

    def test_scope_expansion_and_boolean_metric_rejected(self):
        value = context()
        value["metrics"] = [{"id": "count", "label": "Casos", "value": 1, "unit": "casos", "source_tool": "query_data",
                              "scope": {"company_ids": [2]}, "period": None, "coverage": {}}]
        with self.assertRaisesRegex(ValueError, "scope exceeds"):
            delivery.validate_context(value, self.root)
        value["metrics"][0]["scope"] = {"company_ids": [1]}
        value["metrics"][0]["value"] = True
        with self.assertRaises(ValueError):
            delivery.validate_context(value, self.root)

    def test_available_evidence_requires_real_matching_bytes(self):
        value = context()
        add_evidence(value, self.image)
        delivery.validate_context(value, self.root)
        self.image.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "integrity"):
            delivery.validate_context(value, self.root)

    def test_all_office_formats_require_used_embedded_image_not_link_or_orphan(self):
        value = context()
        add_evidence(value, self.image)
        for suffix in (".docx", ".pptx", ".xlsx"):
            for mode in ("embedded", "external", "missing", "orphan"):
                with self.subTest(suffix=suffix, mode=mode):
                    path = self.root / (mode + suffix)
                    office_fixture(path, mode)
                    if mode == "embedded":
                        result = delivery.audit_office(path, value)
                        self.assertEqual(result["embedded_image_count"], 1)
                        self.assertTrue(result["visual_review_required"])
                    else:
                        with self.assertRaises(ValueError):
                            delivery.audit_office(path, value)

    def test_caption_missing_rejected(self):
        value = context()
        add_evidence(value, self.image)
        value["evidence"][0]["caption"] = "Outra legenda"
        path = self.root / "caption.docx"
        office_fixture(path)
        with self.assertRaisesRegex(ValueError, "caption missing"):
            delivery.audit_office(path, value)

    def test_csv_preserves_multiline_quoted_cells_zero_ids_and_hash(self):
        data = '\ufeffid;observação\r\n001;"linha 1\nlinha 2;texto"\r\n'.encode("utf-8")
        path = self.root / "monthly.csv"
        path.write_bytes(data)
        result = delivery.audit_csv(path, hashlib.sha256(data).hexdigest(), len(data), 1)
        self.assertTrue(result["metadata_integrity_verified"])
        self.assertEqual(result["rows"], 1)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            delivery.audit_csv(path, "0" * 64, len(data), 1)

    def test_empty_csv_with_header_and_duplicate_bom(self):
        path = self.root / "empty.csv"
        path.write_bytes(b"\xef\xbb\xbfid;name\r\n")
        self.assertEqual(delivery.audit_csv(path)["rows"], 0)
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        with self.assertRaisesRegex(ValueError, "duplicate BOM"):
            delivery.audit_csv(path)

    def test_renamed_office_file_is_rejected(self):
        path = self.root / "renamed.xlsx"
        with ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<root/>")
        with self.assertRaisesRegex(ValueError, "does not match"):
            delivery.audit_office(path)

    def test_missing_period_fields_and_inverted_period_are_rejected(self):
        value = context()
        value["period"] = {"start": "2026-10-01", "end": "2026-09-01", "basis": "confirmed_at", "timezone": "America/Bahia"}
        with self.assertRaisesRegex(ValueError, "after start"):
            delivery.validate_context(value, self.root)
        del value["period"]["basis"]
        with self.assertRaisesRegex(ValueError, "missing"):
            delivery.validate_context(value, self.root)

    def test_truncated_pdf_does_not_pass(self):
        path = self.root / "broken.pdf"
        path.write_bytes(b"%PDF-1.7\ntruncated")
        with self.assertRaisesRegex(ValueError, "complete PDF"):
            delivery.audit_pdf(path)

    def test_new_schema_rules_cannot_be_silently_ignored(self):
        with self.assertRaisesRegex(ValueError, "Unsupported schema keyword"):
            delivery.validate_schema(10, {"type": "integer", "maximum": 5})


if __name__ == "__main__":
    unittest.main()
