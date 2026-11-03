"""Offline packaging and evidence regressions; no application, database or network."""
import hashlib
import importlib.util
import io
import json
import shutil
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
                            for operator_doc in collection.OPERATOR_DOCS:
                                self.assertNotIn(f"docs/{operator_doc}", archive.namelist())
                            self.assertIn("docs/ACCEPTANCE.md", archive.namelist())
                            self.assertIn(f"docs/INSTALL-{client.upper()}.md", archive.namelist())
                            if client == "claude":
                                self.assertIn(".claude-plugin/plugin.json", archive.namelist())
                                self.assertNotIn("plugin.json", archive.namelist())
                                server = json.loads(archive.read(".mcp.json"))["mcpServers"]["hydrovision"]
                                self.assertNotIn("oauth", server)  # CIMD: Claude uses its published identity
                            else:
                                self.assertIn("plugin.json", archive.namelist())
                                self.assertNotIn(".mcp.json", archive.namelist())
                                server = json.loads(archive.read("mcp.json"))["mcpServers"]["hydrovision"]
                                self.assertEqual(server["extensions"]["com.openai"]["auth"]["client"], {"mode": "cimd"})
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

    def test_client_authentication_requires_cimd_without_client_ids_or_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copyfile(collection.PLUGIN_ROOT / "plugin.json", root / "plugin.json")
            payload = collection.read_json(collection.PLUGIN_ROOT / "mcp.json")
            server = payload["mcpServers"]["hydrovision"]
            collection.write_json(root / "mcp.json", payload)
            collection.validate_client_configuration(root, "chatgpt")
            server["extensions"]["com.openai"]["auth"]["client"] = {"mode": "provided", "clientId": "chatgpt", "tokenEndpointAuthMethod": "none"}
            collection.write_json(root / "mcp.json", payload)
            with self.assertRaisesRegex(ValueError, "ChatGPT OAuth"):
                collection.validate_client_configuration(root, "chatgpt")
            server["extensions"]["com.openai"]["auth"]["client"] = {"mode": "cimd"}
            server["headers"] = {"Authorization": "Bearer fake-test-fixture"}
            collection.write_json(root / "mcp.json", payload)
            with self.assertRaisesRegex(ValueError, "Credentials"):
                collection.validate_client_configuration(root, "chatgpt")
            shutil.copytree(collection.PLUGIN_ROOT / ".claude-plugin", root / ".claude-plugin")
            claude = collection.read_json(collection.PLUGIN_ROOT / ".mcp.json")
            collection.write_json(root / ".mcp.json", claude)
            collection.validate_client_configuration(root, "claude")
            claude["mcpServers"]["hydrovision"]["oauth"] = {"clientId": "claude-ai"}
            collection.write_json(root / ".mcp.json", claude)
            with self.assertRaisesRegex(ValueError, "CIMD needs no oauth"):
                collection.validate_client_configuration(root, "claude")

    def test_bump_and_check_version_cover_every_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp)
            for name in collection.VERSION_FILES:
                (plugin / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(collection.PLUGIN_ROOT / name, plugin / name)
            with patch.object(collection, "PLUGIN_ROOT", plugin), redirect_stdout(io.StringIO()):
                current = collection.check_version()
                self.assertEqual(collection.check_version("v" + current), current)
                with self.assertRaisesRegex(ValueError, "Expected version 0.0.1"):
                    collection.check_version("v0.0.1")
                with self.assertRaisesRegex(ValueError, "semantic version"):
                    collection.bump("1.2")
                before = {name: (plugin / name).read_text(encoding="utf-8") for name in collection.VERSION_FILES}
                collection.bump("9.8.7")
                self.assertEqual(collection.check_version("9.8.7"), "9.8.7")
                for name in collection.VERSION_FILES:
                    after = (plugin / name).read_text(encoding="utf-8")
                    self.assertEqual(json.loads(after)["version"], "9.8.7")
                    # Only the version line changes; formatting of inline objects is preserved.
                    self.assertEqual(after.replace('"version": "9.8.7"', f'"version": "{current}"', 1), before[name])
                stale = collection.read_json(plugin / "plugin.json")
                stale["version"] = "0.1.0"
                collection.write_json(plugin / "plugin.json", stale)
                with self.assertRaisesRegex(ValueError, "Declared versions differ"):
                    collection.check_version()

    def test_stage_release_matches_private_bucket_contract(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            root = Path(tmp)
            with patch.object(collection, "BACKEND", root / "missing-backend"):
                collection.build(root / "build")
            latest = collection.stage_release(root / "build", root / "release", published_at="2026-10-28T12:00:00Z")
            version = collection.read_json(SKILLS / "collection.json")["version"]
            self.assertEqual(list(latest), ["version", "published_at", "packages"])
            self.assertEqual(latest["version"], version)
            self.assertEqual(latest["published_at"], "2026-10-28T12:00:00Z")
            self.assertEqual(list(latest["packages"]), ["claude", "chatgpt"])
            prefix = root / "release" / collection.RELEASE_PREFIX
            self.assertEqual(latest, collection.read_json(prefix / "latest.json"))
            # The staged tree mirrors the bucket: every object path in latest.json exists under release/.
            self.assertEqual(sorted(path.name for path in prefix.iterdir()), [version, "latest.json"])
            self.assertEqual(sorted(path.name for path in (prefix / version).iterdir()),
                             ["hydrovision-chatgpt.zip", "hydrovision-claude.zip", "manifest.json"])
            build_manifest = collection.read_json(root / "build/manifest.json")
            self.assertEqual(collection.read_json(prefix / version / "manifest.json"), build_manifest)
            for client, package in latest["packages"].items():
                self.assertEqual(list(package), ["object", "filename", "sha256", "size_bytes"])
                self.assertEqual(package["object"], f"hydrovision-plugin/{version}/hydrovision-{client}.zip")
                self.assertEqual(package["filename"], f"hydrovision-{client}-{version}.zip")
                self.assertNotIn("http", json.dumps(package))
                archive = root / "release" / package["object"]
                self.assertEqual(package["sha256"], collection.digest(archive))
                self.assertEqual(package["sha256"], build_manifest["targets"][client]["sha256"])
                self.assertEqual(package["size_bytes"], archive.stat().st_size)
            with self.assertRaisesRegex(ValueError, "not empty"):
                collection.stage_release(root / "build", root / "release")

    def test_lost_accents_and_non_utf8_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills/hydrovision-analysis"
            skill.mkdir(parents=True)
            good = ["---", "name: x", "description: usuários e investigações", "---", "`a?b` e https://x.test/?q=1", ""]
            (skill / "SKILL.md").write_text("\n".join(good), encoding="utf-8")
            collection.validate_text_encoding(root)
            lost = ["---", "name: x", "description: usu?rios e investiga??es", "---", ""]
            (skill / "SKILL.md").write_text("\n".join(lost), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Lost accent"):
                collection.validate_text_encoding(root)
            (skill / "SKILL.md").write_text("descrição".encode("utf-8").decode("latin-1"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mojibake"):
                collection.validate_text_encoding(root)
            (skill / "SKILL.md").write_bytes("descrição".encode("cp1252"))
            with self.assertRaisesRegex(ValueError, "Not UTF-8"):
                collection.validate_text_encoding(root)

    def test_marketplaces_and_no_ignored_codex_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(collection.PLUGIN_ROOT / name, root / name)
            collection.validate_marketplaces(root)
            (root / ".app.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ignored next to plugin.json"):
                collection.validate_marketplaces(root)
            (root / ".app.json").unlink()
            codex = collection.read_json(root / ".agents/plugins/marketplace.json")
            del codex["plugins"][0]["policy"]
            collection.write_json(root / ".agents/plugins/marketplace.json", codex)
            with self.assertRaisesRegex(ValueError, "needs policy"):
                collection.validate_marketplaces(root)

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
