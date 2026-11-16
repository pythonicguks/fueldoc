"""`uv run fueldoc build|serve|generate` : génère les ressources 3D, puis délègue à Zensical.

Équivalent d'un hook pre-build (Zensical 0.1.x n'en expose pas) : la génération est mise en cache
par empreinte du code (modèle + scènes) et ne se relance que si nécessaire.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .ext import ensure_generated

OUT_DIR = Path("docs/generated")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("usage : fueldoc {build|serve|generate} [options Zensical]\n"
              "  generate [--force]  génère seulement les ressources (docs/generated)\n"
              "  build / serve       génère si nécessaire, puis lance `zensical build|serve`")
        raise SystemExit(0)
    cmd, rest = args[0], args[1:]
    if cmd == "generate":
        ensure_generated(OUT_DIR, force="--force" in rest)
        return
    if cmd in ("build", "serve"):
        # --clean : on repart d'une génération propre
        ensure_generated(OUT_DIR, force=False)
    from zensical.main import cli

    cli.main(args=args, prog_name="fueldoc", standalone_mode=True)


if __name__ == "__main__":
    main()
