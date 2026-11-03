"""Build Claude and ChatGPT plugins from shared skills, offline and without Django."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
SHARED = ROOT / "_shared"
PLUGIN_ROOT = ROOT.parent
WORKSPACE = PLUGIN_ROOT.parent
BACKEND = WORKSPACE / "simpat-back"
ASSET_ROOT = ROOT / "hydrovision-reports"
# Every file that declares the plugin version; `bump` rewrites them and `check-version` compares them.
VERSION_FILES = (".claude-plugin/plugin.json", "plugin.json", "skills/collection.json")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
RELEASE_PREFIX = "hydrovision-plugin"
RELEASE_CLIENTS = ("claude", "chatgpt")
# Text files shipped in the packages; checked for strict UTF-8 and lost accents ("usu?rios").
TEXT_SUFFIXES = {".md", ".json", ".py"}
MOJIBAKE = re.compile(r"[A-Za-zÀ-ÿ]\?[A-Za-zÀ-ÿ]|�|Ã[\u0080-¿]")
# Codex marketplace entries need an install/auth policy and a category (developers.openai.com/plugins/build/plugins).
CODEX_POLICY = {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
# Operator-only docs (bucket/IAM setup, CI secrets, maintenance); never shipped inside the end-user packages.
OPERATOR_DOCS = ("RELEASE.md", "MAINTENANCE.md")
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml_summary(path: Path) -> dict:
    """Inspect theme/layout metadata, not example business content."""
    with ZipFile(path) as archive:
        names = archive.namelist()
        themes = []
        for name in names:
            if re.fullmatch(r"(?:ppt|word)/theme/theme\d+\.xml", name):
                tree = ET.fromstring(archive.read(name))
                colors = {}
                scheme = tree.find(".//a:clrScheme", NS)
                if scheme is not None:
                    for color in scheme:
                        if len(color):
                            value = color[0].get("lastClr") or color[0].get("val")
                            colors[color.tag.split("}")[-1]] = value
                fonts = {kind: tree.find(f".//a:{kind}/a:latin", NS).get("typeface")
                         for kind in ("majorFont", "minorFont")
                         if tree.find(f".//a:{kind}/a:latin", NS) is not None}
                themes.append({"part": name, "name": tree.get("name"), "colors": colors, "fonts": fonts})
        result = {"themes": themes, "media_count": sum("/media/" in name for name in names)}
        if "ppt/presentation.xml" in names:
            tree = ET.fromstring(archive.read("ppt/presentation.xml"))
            size = tree.find("p:sldSz", NS)
            result["slide_size_emu"] = dict(size.attrib) if size is not None else None
            result["slide_count"] = sum(bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", name)) for name in names)
            result["layouts"] = []
            for name in names:
                if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name):
                    layout = ET.fromstring(archive.read(name))
                    common = layout.find("p:cSld", NS)
                    result["layouts"].append({"part": name, "type": layout.get("type"),
                                               "name": common.get("name") if common is not None else None})
        if "word/document.xml" in names:
            tree = ET.fromstring(archive.read("word/document.xml"))
            result["sections"] = []
            for section in tree.findall(".//w:sectPr", NS):
                result["sections"].append({child.tag.split("}")[-1]:
                                           {key.split("}")[-1]: value for key, value in child.attrib.items()}
                                           for child in section if child.tag.split("}")[-1] in ("pgSz", "pgMar")})
            styles = ET.fromstring(archive.read("word/styles.xml"))
            result["styles"] = [{"id": style.get(f"{{{NS['w']}}}styleId"),
                                  "name": style.find("w:name", NS).get(f"{{{NS['w']}}}val")}
                                 for style in styles.findall("w:style", NS)
                                 if style.find("w:name", NS) is not None]
            result["explicit_fonts"] = sorted({value for element in styles.findall(".//w:rFonts", NS)
                                                 for key, value in element.attrib.items()
                                                 if key.split("}")[-1] in ("ascii", "hAnsi")})
        result["thumbnails"] = [name for name in names if name.startswith("docProps/thumbnail.")]
        return result


def import_templates(source: Path):
    config = read_json(ROOT / "collection.json")
    source = source.resolve(strict=True)
    items = []
    for spec in config["templates"]:
        path = source / spec["source_name"]
        if not path.is_file():
            raise ValueError(f"Required institutional source is missing: {path.name}")
        item = {**spec, "sha256": digest(path), "bytes": path.stat().st_size,
                "inspection": xml_summary(path)}
        if spec["bundled"]:
            relative = f"assets/templates/{spec['id']}{path.suffix.lower()}"
            target = ASSET_ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            item["asset"] = relative
            with ZipFile(path) as archive:
                thumbnails = item["inspection"]["thumbnails"]
                if thumbnails:
                    preview = f"assets/previews/{spec['id']}{Path(thumbnails[0]).suffix}"
                    target = ASSET_ROOT / preview
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(thumbnails[0]))
                    item["preview"] = preview
        items.append(item)
    write_json(SHARED / "templates.json", {"version": config["version"], "items": items,
               "selection": "Explicit template_id first; one compatible bundled template can be selected; otherwise ask for variant.",
               "example_policy": "Example decks are inspected as references and are not bundled or used as report content."})
    print(f"Inspected {len(items)} sources; bundled {sum(item['bundled'] for item in items)} templates.")


def source_tools() -> set[str]:
    if not (BACKEND / "web/mcp_server/catalog.py").is_file():
        return set(read_json(SHARED / "sources.json")["tools"])
    names = set()
    for filename, variable in (("allowlist.py", "EXPOSED"), ("catalog.py", "CONTRACTS")):
        module = ast.parse((BACKEND / "web/mcp_server" / filename).read_text(encoding="utf-8"))
        assignment = next(node for node in module.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == variable for target in node.targets))
        if variable == "CONTRACTS":
            names.update(ast.literal_eval(key) for key in assignment.value.keys)
        else:
            names.update(ast.literal_eval(call.args[0]) for call in assignment.value.elts)
    return names


def source_datasets() -> dict[str, set[str]]:
    if not (BACKEND / "web/mcp_server/catalog.py").is_file():
        return {name: set(fields) for name, fields in read_json(SHARED / "sources.json")["datasets"].items()}
    module = ast.parse((BACKEND / "web/mcp_server/catalog.py").read_text(encoding="utf-8"))
    assignment = next(node for node in module.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "DATASETS" for target in node.targets))
    result = {}

    def fields(expression):
        values = set()
        for key, value in zip(expression.keys, expression.values):
            if key is not None:
                values.add(ast.literal_eval(key))
            elif (isinstance(value, ast.Attribute) and value.attr == "fields"
                  and isinstance(value.value, ast.Subscript)
                  and isinstance(value.value.value, ast.Name) and value.value.value.id == "DATASETS"):
                values.update(result[ast.literal_eval(value.value.slice)])
            else:
                raise ValueError("Unsupported dataset field expansion; inspect the updated source catalog.")
        return values

    for key, value in zip(assignment.value.keys, assignment.value.values):
        result[ast.literal_eval(key)] = fields(value.args[2])
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
                        and target.value.id == "DATASETS"):
                    result[ast.literal_eval(target.slice)] = fields(node.value.args[2])
    return result


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {path}")
    header = text.split("---", 2)[1]
    return dict(line.split(":", 1) for line in header.strip().splitlines() if ":" in line)


def validate_sources():
    config = read_json(ROOT / "collection.json")
    for client, settings in config["clients"].items():
        validate_client_configuration(PLUGIN_ROOT, client, config)
        if not (ROOT / "_clients" / settings["reference"]).is_file():
            raise ValueError(f"Missing runtime guide: {client}")
    tools = read_json(SHARED / "tools.json")["tools"]
    names = {tool["name"] for tool in tools}
    if len(names) != len(tools) or names != source_tools():
        raise ValueError("Tool catalog differs from the source allowlist/contracts.")
    concepts = read_json(SHARED / "concepts.json")["concepts"]
    ids = {concept["id"] for concept in concepts}
    if len(ids) != len(concepts):
        raise ValueError("Duplicate concept ids.")
    datasets = source_datasets()
    for concept in concepts:
        if not set(concept["tools"]) <= names:
            raise ValueError(f"Unknown tool in concept {concept['id']}")
        for relation in concept["relations"]:
            if relation["target"] not in ids:
                raise ValueError(f"Unknown relation target in {concept['id']}")
        dataset = concept.get("dataset")
        if dataset and (dataset not in datasets or not set(concept.get("fields", [])) <= datasets[dataset]):
            raise ValueError(f"Unsupported dataset fields in concept {concept['id']}")
    for view in read_json(SHARED / "views.json")["views"]:
        if not set(view["tools"]) <= names or not set(view["concepts"]) <= ids:
            raise ValueError(f"Unknown reference in view {view['id']}")
    for spec in config["skills"]:
        body = (ROOT / spec["name"] / "SKILL.md").read_text(encoding="utf-8")
        if re.search(r"\b(?:Claude|ChatGPT)\b", body):
            raise ValueError("Shared skill instructions must be provider-neutral; use the client guide.")
        if re.search(r"[A-Za-zÀ-ÿ]\?+[A-Za-zÀ-ÿ]", body):
            raise ValueError(f"Damaged text encoding in {spec['name']}")
        header = frontmatter(ROOT / spec["name"] / "SKILL.md")
        if header.get("name", "").strip() != spec["name"] or len(header.get("description", "").strip()) > 200:
            raise ValueError(f"Invalid skill metadata: {spec['name']}")
        for reference in spec["references"]:
            if not (SHARED / reference).is_file():
                raise ValueError(f"Missing reference: {reference}")
        for script in spec.get("scripts", []):
            if not (ROOT / "scripts" / script).is_file():
                raise ValueError(f"Missing runtime script: {script}")
        folder = ROOT / spec["name"]
        validate_bundle(folder)
        for reference in spec["references"]:
            if not (folder / "references" / reference).is_file() or digest(SHARED / reference) != digest(folder / "references" / reference):
                raise ValueError(f"Stale generated reference; run sync: {spec['name']}/{reference}")
        for script in spec.get("scripts", []):
            if digest(ROOT / "scripts" / script) != digest(folder / "scripts" / script):
                raise ValueError("Stale runtime script; run sync.")
    for template in read_json(SHARED / "templates.json")["items"]:
        if template["bundled"]:
            path = ASSET_ROOT / template["asset"]
            if not path.is_file() or digest(path) != template["sha256"]:
                raise ValueError(f"Template integrity check failed: {template['id']}")
    validate_text_encoding()
    validate_marketplaces()
    print(f"Validated {len(config['skills'])} skills, {len(concepts)} concepts, {len(names)} tools and template integrity.")


def validate_text_encoding(root: Path | None = None):
    """Reject files that are not strict UTF-8 or whose accents were replaced by '?' or mojibake."""
    root = PLUGIN_ROOT if root is None else root
    folders = [root / "skills", root / "docs"]
    files = [path for folder in folders if folder.exists() for path in folder.rglob("*")
             if path.is_file() and path.suffix in TEXT_SUFFIXES and "tests" not in path.relative_to(root).parts]
    files += [root / name for name in ("README.md", "plugin.json", "mcp.json", ".mcp.json", ".claude-plugin/plugin.json",
                                       ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")
              if (root / name).exists()]
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Not UTF-8: {path.relative_to(root)}") from error
        # Only prose can lose accents; code, URLs and regexes legitimately contain "?" between letters.
        if path.suffix == ".md":
            prose = re.sub(r"```.*?```|`[^`\n]*`|https?://\S+", "", text, flags=re.S)
        elif path.suffix == ".json":
            prose = " ".join(value for value in json_strings(json.loads(text)) if not re.search(r"https?://|[\\^$]", value))
        else:
            continue
        match = MOJIBAKE.search(prose)
        if match:
            raise ValueError(f"Lost accent or mojibake in {path.relative_to(root)}: {match.group(0)!r}")


def json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from json_strings(item)


def validate_marketplaces(root: Path | None = None):
    root = PLUGIN_ROOT if root is None else root
    codex = read_json(root / ".agents/plugins/marketplace.json")
    for entry in codex["plugins"]:
        if entry.get("policy") != CODEX_POLICY or not entry.get("category"):
            raise ValueError(f"Codex marketplace entry {entry.get('name')} needs policy {CODEX_POLICY} and a category.")
    claude = read_json(root / ".claude-plugin/marketplace.json")
    if [entry["name"] for entry in claude["plugins"]] != ["hydrovision"]:
        raise ValueError("Claude marketplace must list exactly the hydrovision plugin.")
    if (root / ".codex-plugin").exists() or (root / ".app.json").exists():
        # plugin.json declares extensions.com.openai, which replaces the .codex-plugin overlay entirely.
        raise ValueError(".codex-plugin/ and .app.json are ignored next to plugin.json; keep OpenAI settings in plugin.json.")


def validate_client_configuration(folder: Path, client: str, config=None):
    config = read_json(ROOT / "collection.json") if config is None else config
    settings = config["clients"][client]
    plugin = read_json(folder / settings["manifest"])
    server = read_json(folder / settings["mcp_config"])["mcpServers"]["hydrovision"]
    if plugin["name"] != "hydrovision" or plugin["version"] != config["version"] or server["url"] != config["endpoint"]:
        raise ValueError("Plugin metadata and collection endpoint/version differ.")
    if client == "claude":
        # CIMD: Claude presents its published client identity; a static clientId must not be pinned.
        if server["type"] != "http" or "oauth" in server:
            raise ValueError("Invalid Claude transport or OAuth client; CIMD needs no oauth block.")
    else:
        if plugin.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            raise ValueError("ChatGPT needs the portable plugin schema.")
        mcp = read_json(folder / settings["mcp_config"])
        if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json" or server["type"] != "streamable-http":
            raise ValueError("ChatGPT needs portable MCP Streamable HTTP configuration.")
        auth = server["extensions"]["com.openai"]["auth"]
        # CIMD mode per developers.openai.com/plugins/build/plugins: no clientId or credentials in the client object.
        if (auth.get("type") != "oauth" or auth.get("client") != {"mode": "cimd"}
                or auth.get("baseScopes") != ["vision:read"]):
            raise ValueError("Invalid ChatGPT OAuth client configuration; use CIMD without clientId.")
    for payload in (plugin, server):
        if re.search(r'"(?:clientSecret|client_secret|access_token|refresh_token|Authorization)"\s*:', json.dumps(payload), re.I):
            raise ValueError("Credentials must not be embedded in plugin configuration.")


def declared_versions() -> dict[str, str]:
    return {name: read_json(PLUGIN_ROOT / name)["version"] for name in VERSION_FILES}


def check_version(expected: str | None = None) -> str:
    """Fail when the manifests disagree or when a release tag (v1.2.0) names another version."""
    found = declared_versions()
    if len(set(found.values())) != 1:
        raise ValueError("Declared versions differ: " + ", ".join(f"{name}={value}" for name, value in found.items()))
    version = next(iter(found.values()))
    if not SEMVER.match(version):
        raise ValueError(f"Version is not x.y.z: {version}")
    if expected is not None and expected.removeprefix("v") != version:
        raise ValueError(f"Expected version {expected.removeprefix('v')} but the manifests declare {version}.")
    print(f"Version {version} is declared consistently in {len(found)} files.")
    return version


def bump(version: str):
    """Rewrite the top-level version of every manifest in place, preserving their formatting."""
    if not SEMVER.match(version):
        raise ValueError(f"Use a semantic version x.y.z, got: {version}")
    for name in VERSION_FILES:
        path = PLUGIN_ROOT / name
        text, count = re.subn(r'^(  "version": ")[^"]*(")', rf"\g<1>{version}\g<2>",
                              path.read_text(encoding="utf-8"), count=1, flags=re.M)
        if count != 1 or json.loads(text)["version"] != version:
            raise ValueError(f"Could not rewrite the top-level version in {name}")
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"Set version {version} in {len(VERSION_FILES)} files; run validate and update CHANGELOG.md.")


def stage_release(build_dir: Path, output: Path, published_at: str | None = None) -> dict:
    """Lay out the private bucket objects for one release and write latest.json (contract with simpat-back).

    The bucket is private: latest.json names objects, not URLs. The backend reads it with its own
    service account and returns a short-lived V4 signed URL for the requested package.
    """
    published_at = published_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", published_at):
        raise ValueError("published_at must be UTC like 2026-10-28T12:00:00Z")
    build_manifest = read_json(build_dir / "manifest.json")
    version = build_manifest["version"]
    if version != check_version():
        raise ValueError(f"Build {version} does not match the declared version.")
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Release output is not empty; choose a fresh directory: {output}")
    target = output / RELEASE_PREFIX / version
    target.mkdir(parents=True)
    packages = {}
    for client in RELEASE_CLIENTS:
        entry = build_manifest["targets"].get(client)
        if entry is None:
            raise ValueError(f"Build has no {client} target; a release needs both clients.")
        name = f"hydrovision-{client}.zip"
        shutil.copyfile(build_dir / entry["plugin"], target / name)
        sha256 = digest(target / name)
        if sha256 != entry["sha256"]:
            raise ValueError(f"Plugin archive differs from the build manifest: {client}")
        packages[client] = {"object": f"{RELEASE_PREFIX}/{version}/{name}", "filename": f"hydrovision-{client}-{version}.zip",
                            "sha256": sha256, "size_bytes": (target / name).stat().st_size}
    shutil.copyfile(build_dir / "manifest.json", target / "manifest.json")
    latest = {"version": version, "published_at": published_at, "packages": packages}
    write_json(output / RELEASE_PREFIX / "latest.json", latest)
    print(f"Staged {RELEASE_PREFIX}/{version}/ and {RELEASE_PREFIX}/latest.json in {output}")
    return latest


def sync():
    """Materialize shared references for direct plugin loading and standalone uploads."""
    for spec in read_json(ROOT / "collection.json")["skills"]:
        folder = ROOT / spec["name"]
        (folder / "references").mkdir(exist_ok=True)
        for reference in spec["references"]:
            shutil.copyfile(SHARED / reference, folder / "references" / reference)
        for script in spec.get("scripts", []):
            (folder / "scripts").mkdir(exist_ok=True)
            shutil.copyfile(ROOT / "scripts" / script, folder / "scripts" / script)
        validate_bundle(folder)
    render_catalog()
    print("Synchronized self-contained skill directories.")


def render_catalog():
    concepts = read_json(SHARED / "concepts.json")["concepts"]
    views = read_json(SHARED / "views.json")["views"]
    tools = read_json(SHARED / "tools.json")["tools"]
    labels = {"partial": "Parcial", "unavailable": "Indisponível", "full": "Integral"}
    lines = ["# Catálogo HydroVision", "", "Gerado por `python skills/collection.py sync`; edite as fontes em `skills/_shared`.", "",
             "## Relações principais", "", "```mermaid", "flowchart TD",
             "  Organization --> Account", "  Organization -. projeção .-> Company",
             "  Account -. projeção .-> Employee", "  Company --> Directory --> Management --> City --> Locale --> Sector",
             "  Sector --> MeasurementPoint", "  Sector --> Logger", "  Logger --> MeasurementPoint",
             "  Sector --> Leak", "  Company --> Investigation", "  Leak -. vínculo opcional .-> Investigation",
             "  Investigation --> Participant --> Session", "  Sector --> LocalizationRun --> LocalizationCluster",
             "  LocalizationCluster -. snapshot de origem .-> Investigation", "```", "",
             "As relações de projeção não autorizam juntar IDs do Accounts e do Vision por igualdade.", "",
             "## Objetos e conceitos", "", "| Nome canônico | ID | Modelo | Acesso MCP | Significado |", "|---|---|---|---|---|"]
    lines += [f"| {item['label']} | `{item['id']}` | `{item['model']}` | {labels[item['availability']]} | {item['definition']} |" for item in concepts]
    lines += ["", "## Visões", "", "| Visão | Rotas de referência | Blocos | Limitações |", "|---|---|---|---|"]
    lines += [f"| {item['label']} | {', '.join('`' + route + '`' for route in item['frontend_routes'])} | {'; '.join(item['blocks'])} | {'; '.join(item['limitations'])} |" for item in views]
    lines += ["", "## Tools", "", "| Tool | Uso | Escopo | Paginação |", "|---|---|---|---|"]
    lines += [f"| `{item['name']}` | {item['use']} | {item['scope']} | {item['pagination']} |" for item in tools]
    lines += ["", "Schemas atuais das tools prevalecem. Notas, campos e cardinalidades completos estão nos catálogos JSON.", ""]
    path = PLUGIN_ROOT / "docs/CATALOG.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def refresh_sources():
    paths = {
        "simpat-back": ["web/mcp_server/allowlist.py", "web/mcp_server/catalog.py", "web/mcp_server/tools.py",
                        "web/mcp_server/images.py", "web/mcp_server/analytics.py", "web/mcp_server/queries.py",
                        "web/company/models.py", "web/employee/models.py", "web/logger/models.py",
                        "web/field_ops/models.py", "web/processing/models.py", "docs/arquitetura/dominio.md"],
        "hydrovision": ["apps/web/src/utils/api/routes/pages.ts", "apps/web/src/Layouts/Home/Management/types.ts",
                        "apps/web/src/Layouts/Home/Management/managementPresenter.ts", "Docs/reports-guide.md"],
        "accounts-back": ["accounts/models.py", "docs/arquitetura/dominio.md", "oauth/README.md"],
    }
    repositories = {}
    for name, files in paths.items():
        repo = WORKSPACE / name
        repositories[name] = {**git_revision(repo), "files": {path: digest(repo / path) for path in files}}
    write_json(SHARED / "sources.json", {"repositories": repositories, "tools": sorted(source_tools()),
               "datasets": {name: sorted(fields) for name, fields in source_datasets().items()}})
    print("Recorded source revisions, public dataset fields and file hashes without importing applications.")


def validate_bundle(folder: Path):
    """Require local links to resolve inside the uploaded skill, never to sibling skills."""
    for path in folder.rglob("*.md"):
        markdown = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        markdown = re.sub(r"`[^`\n]*`", "", markdown)
        for target in re.findall(r"\]\(([^)]+)\)", markdown):
            if re.match(r"[a-z]+://", target) or target.startswith("#"):
                continue
            local = (path.parent / target.split("#", 1)[0]).resolve()
            if not local.is_relative_to(folder.resolve()) or not local.exists():
                raise ValueError(f"Unresolved or external local reference: {path.name}: {target}")


def git_revision(path: Path) -> dict:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True, check=True)
    return {"revision": result.stdout.strip(), "working_tree_dirty": bool(status.stdout.strip())}


def build(output: Path, target="all"):
    validate_sources()
    output = output.resolve()
    if output == ROOT or ROOT.is_relative_to(output) or output.is_relative_to(ROOT):
        raise ValueError("Build output must be separate from the source directory.")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output is not empty; choose a fresh directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config = read_json(ROOT / "collection.json")
    clients = list(config["clients"]) if target == "all" else [target]
    if any(client not in config["clients"] for client in clients):
        raise ValueError("Unknown client target.")
    provenance = read_json(SHARED / "sources.json")["repositories"]
    manifest = {"version": config["version"], "endpoint": config["endpoint"],
                "source_repositories": provenance, "targets": {}}
    for client in clients:
        client_output = output / client
        client_output.mkdir()
        build_client(client_output, client, config, provenance)
        built = read_json(client_output / "manifest.json")
        manifest["targets"][client] = {"manifest": f"{client}/manifest.json", "plugin": f"{client}/hydrovision-plugin.zip",
                                       "bytes": built["plugin"]["bytes"], "sha256": built["plugin"]["sha256"],
                                       "packages": built["packages"]}
    write_json(output / "manifest.json", manifest)
    guide = (ROOT / "INSTALL.md").read_text(encoding="utf-8").replace("](../docs/", "](docs/")
    (output / "INSTALL.md").write_text(guide, encoding="utf-8", newline="\n")
    shutil.copytree(PLUGIN_ROOT / "docs", output / "docs", ignore=shutil.ignore_patterns(*OPERATOR_DOCS))
    if "chatgpt" in clients:
        marketplace = read_json(PLUGIN_ROOT / ".agents/plugins/marketplace.json")
        marketplace["plugins"][0]["source"]["path"] = "./chatgpt/hydrovision-plugin"
        write_json(output / ".agents/plugins/marketplace.json", marketplace)
    print(f"Built {', '.join(clients)} plugins and self-contained skill ZIPs in {output}")


def build_client(output: Path, client: str, config, provenance):
    settings = config["clients"][client]
    manifest = {"version": config["version"], "client": client, "endpoint": config["endpoint"],
                "source_repositories": provenance, "packages": []}
    for spec in config["skills"]:
        folder = output / spec["name"]
        if folder.exists():
            raise ValueError(f"Output already exists; choose a fresh directory: {folder}")
        folder.mkdir()
        shutil.copyfile(ROOT / spec["name"] / "SKILL.md", folder / "SKILL.md")
        references = folder / "references"
        references.mkdir()
        for reference in spec["references"]:
            source = ROOT / "_clients" / settings["reference"] if reference == "client.md" else SHARED / reference
            shutil.copyfile(source, references / reference)
        for script in spec.get("scripts", []):
            (folder / "scripts").mkdir(exist_ok=True)
            shutil.copyfile(ROOT / "scripts" / script, folder / "scripts" / script)
        if spec.get("assets"):
            shutil.copytree(ASSET_ROOT / "assets", folder / "assets")
        write_json(folder / "manifest.json", {"version": config["version"], "client": client, "skill": spec["name"],
                   "endpoint": config["endpoint"], "source_repositories": provenance})
        validate_bundle(folder)
        archive_path = output / f"{spec['name']}.zip"
        zip_directory(folder, archive_path, prefix=spec["name"])
        manifest["packages"].append({"skill": spec["name"], "file": archive_path.name,
                                     "bytes": archive_path.stat().st_size, "sha256": digest(archive_path)})
    plugin_folder = output / "hydrovision-plugin"
    plugin_folder.mkdir()
    for key in ("manifest", "mcp_config"):
        destination = plugin_folder / settings[key]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PLUGIN_ROOT / settings[key], destination)
    for spec in config["skills"]:
        shutil.copytree(output / spec["name"], plugin_folder / "skills" / spec["name"])
    install_guide = PLUGIN_ROOT / "docs" / f"INSTALL-{client.upper()}.md"
    shutil.copyfile(install_guide, plugin_folder / "INSTALL.md")
    shutil.copytree(PLUGIN_ROOT / "docs", plugin_folder / "docs", ignore=shutil.ignore_patterns(*OPERATOR_DOCS))
    validate_client_configuration(plugin_folder, client, config)
    plugin_archive = output / "hydrovision-plugin.zip"
    zip_directory(plugin_folder, plugin_archive)
    manifest["plugin"] = {"file": plugin_archive.name, "bytes": plugin_archive.stat().st_size,
                          "sha256": digest(plugin_archive)}
    write_json(output / "manifest.json", manifest)
    shutil.copyfile(install_guide, output / "INSTALL.md")


def zip_directory(folder: Path, target: Path, prefix=""):
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                name = "/".join(part for part in (prefix, path.relative_to(folder).as_posix()) if part)
                info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("import-templates")
    inventory.add_argument("source", type=Path)
    commands.add_parser("validate")
    commands.add_parser("sync")
    commands.add_parser("refresh-sources")
    builder = commands.add_parser("build")
    builder.add_argument("--output", type=Path, required=True)
    builder.add_argument("--target", choices=("all", "claude", "chatgpt"), default="all")
    bumper = commands.add_parser("bump", help="Set the same version in every manifest, e.g. bump 1.2.0")
    bumper.add_argument("version")
    checker = commands.add_parser("check-version", help="Fail when manifests differ or do not match an expected tag")
    checker.add_argument("expected", nargs="?", help="Expected version or tag, e.g. v1.2.0")
    stager = commands.add_parser("stage-release", help="Copy a build into the bucket layout and write latest.json")
    stager.add_argument("--build", type=Path, required=True, help="Directory produced by build --output")
    stager.add_argument("--output", type=Path, required=True)
    stager.add_argument("--published-at", help="UTC timestamp like 2026-10-28T12:00:00Z; default now")
    args = parser.parse_args()
    if args.command == "import-templates":
        import_templates(args.source)
    elif args.command == "validate":
        validate_sources()
    elif args.command == "sync":
        sync()
    elif args.command == "refresh-sources":
        refresh_sources()
    elif args.command == "bump":
        bump(args.version)
    elif args.command == "check-version":
        check_version(args.expected)
    elif args.command == "stage-release":
        stage_release(args.build, args.output, args.published_at)
    else:
        build(args.output, args.target)


if __name__ == "__main__":
    main()
