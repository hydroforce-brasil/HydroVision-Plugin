"""Build the complete HydroVision collection, retaining the original ZIP names."""

import argparse
import shutil
from pathlib import Path

from skills.collection import build


ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--target", choices=("all", "claude", "chatgpt"), default="all")
    args = parser.parse_args()
    build(args.output_dir, target=args.target)
    clients = ("claude", "chatgpt") if args.target == "all" else (args.target,)
    for client in clients:
        archive = args.output_dir / f"hydrovision-{client}.zip"
        shutil.copyfile(args.output_dir / client / "hydrovision-plugin.zip", archive)
        print(archive.resolve())


if __name__ == "__main__":
    main()
