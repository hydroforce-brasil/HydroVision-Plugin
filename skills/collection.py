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
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
SHARED = ROOT / "_shared"
PLUGIN_ROOT = ROOT.parent
WORKSPACE = PLUGIN_ROOT.parent
BACKEND = WORKSPACE / "simpat-back"
ASSET_ROOT = ROOT / "hydrovision-reports"
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
    print(f"Validated {len(config['skills'])} skills, {len(concepts)} concepts, {len(names)} tools and template integrity.")


def validate_client_configuration(folder: Path, client: str, config=None):
    config = read_json(ROOT / "collection.json") if config is None else config
    settings = config["clients"][client]
    plugin = read_json(folder / settings["manifest"])
    server = read_json(folder / settings["mcp_config"])["mcpServers"]["hydrovision"]
    if plugin["name"] != "hydrovision" or plugin["version"] != config["version"] or server["url"] != config["endpoint"]:
        raise ValueError("Plugin metadata and collection endpoint/version differ.")
    if client == "claude":
        if server["type"] != "http" or server.get("oauth") != {"clientId": settings["oauth_client_id"]}:
            raise ValueError("Invalid Claude transport or OAuth client.")
    else:
        if plugin.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            raise ValueError("ChatGPT needs the portable plugin schema.")
        mcp = read_json(folder / settings["mcp_config"])
        if mcp.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json" or server["type"] != "streamable-http":
            raise ValueError("ChatGPT needs portable MCP Streamable HTTP configuration.")
        auth = server["extensions"]["com.openai"]["auth"]
        if (auth.get("type") != "oauth" or auth.get("client") != {
                "mode": "provided", "clientId": settings["oauth_client_id"], "tokenEndpointAuthMethod": "none"
        } or auth.get("baseScopes") != ["vision:read"]):
            raise ValueError("Invalid ChatGPT public OAuth client configuration.")
    for payload in (plugin, server):
        if re.search(r'"(?:clientSecret|access_token|refresh_token|Authorization)"\s*:', json.dumps(payload), re.I):
            raise ValueError("Credentials must not be embedded in plugin configuration.")


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
        manifest["targets"][client] = {"manifest": f"{client}/manifest.json", "plugin": f"{client}/hydrovision-plugin.zip"}
    write_json(output / "manifest.json", manifest)
    guide = (ROOT / "INSTALL.md").read_text(encoding="utf-8").replace("](../docs/", "](docs/")
    (output / "INSTALL.md").write_text(guide, encoding="utf-8", newline="\n")
    shutil.copytree(PLUGIN_ROOT / "docs", output / "docs")
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
    shutil.copytree(PLUGIN_ROOT / "docs", plugin_folder / "docs")
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
    args = parser.parse_args()
    if args.command == "import-templates":
        import_templates(args.source)
    elif args.command == "validate":
        validate_sources()
    elif args.command == "sync":
        sync()
    elif args.command == "refresh-sources":
        refresh_sources()
    else:
        build(args.output, args.target)


if __name__ == "__main__":
    main()
