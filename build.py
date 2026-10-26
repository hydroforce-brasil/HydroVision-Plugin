"""Package the shared skill for Claude and ChatGPT using only public metadata."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
MCP_URL = "https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    manifest_path = ".codex-plugin/plugin.json"
    manifest = json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))
    app_path = ".app.json"
    json.loads((ROOT / app_path).read_text(encoding="utf-8"))
    shared_paths = ["README.md", "skills/hydrovision-analysis/SKILL.md"]
    shared = {path: (ROOT / path).read_bytes() for path in shared_paths}

    claude_manifest = {
        key: manifest[key] for key in ("name", "version", "description", "author")
    }
    claude_manifest["displayName"] = manifest["interface"]["displayName"]
    claude_mcp = {"mcpServers": {"hydrovision": {"type": "http", "url": MCP_URL}}}
    claude = {
        **shared,
        ".claude-plugin/plugin.json": json.dumps(
            claude_manifest, ensure_ascii=False, indent=2
        ).encode("utf-8"),
        ".mcp.json": json.dumps(claude_mcp, indent=2).encode("utf-8"),
    }
    chatgpt = {
        **shared,
        manifest_path: (ROOT / manifest_path).read_bytes(),
        app_path: (ROOT / app_path).read_bytes(),
        ".agents/plugins/marketplace.json": (
            ROOT / ".agents/plugins/marketplace.json"
        ).read_bytes(),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for client, files in (("claude", claude), ("chatgpt", chatgpt)):
        archive = args.output_dir / f"hydrovision-{client}.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as package:
            for path, content in files.items():
                package.writestr(path, content)
        print(archive)


if __name__ == "__main__":
    main()
