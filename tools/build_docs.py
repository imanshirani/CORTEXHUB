# -*- coding: utf-8 -*-
"""Generate English pdoc HTML for app and DCC plugins.

Plugins are loose scripts (import style, pymxs, bpy, hou, maya). This
builder stubs those DCC modules, documents one plugin folder at a time,
and writes HTML under docs/en/ so it does not collide with docs/fa/.

Use the same Python that runs Cortex (PySide6 installed):

    python tools/build_docs.py
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
DOCS_EN = ROOT / "docs" / "en"


def _submodule(parent_name: str, child: str, parent: types.ModuleType) -> MagicMock:
    name = f"{parent_name}.{child}"
    mod = MagicMock(name=name)
    setattr(parent, child, mod)
    sys.modules[name] = mod
    return mod


def stub_dcc() -> None:
    """Enough fakes for plugin imports outside Max / Maya / Blender / Houdini."""
    pymxs = types.ModuleType("pymxs")
    pymxs.runtime = MagicMock(name="pymxs.runtime")
    sys.modules["pymxs"] = pymxs

    sys.modules["qtmax"] = MagicMock(name="qtmax")

    bpy = types.ModuleType("bpy")
    bpy.context = MagicMock()
    bpy.app = MagicMock()
    bpy.data = MagicMock()
    bpy.ops = MagicMock()
    sys.modules["bpy"] = bpy

    maya = types.ModuleType("maya")
    sys.modules["maya"] = maya
    _submodule("maya", "cmds", maya)
    _submodule("maya", "utils", maya)
    _submodule("maya", "mel", maya)

    hou = types.ModuleType("hou")
    hou.ui = MagicMock()
    hou.nodeType = MagicMock(return_value=MagicMock(instances=MagicMock(return_value=[])))
    hou.ropNodeTypeCategory = MagicMock()
    hou.shelves = MagicMock()
    hou.setFps = MagicMock()
    hou.hipFile = MagicMock()
    sys.modules["hou"] = hou
    sys.modules["hdefereval"] = MagicMock(name="hdefereval")

    sys.modules.setdefault("photoshop", MagicMock(name="photoshop"))


def purge_plugin_modules(names: list[str]) -> None:
    for name in names:
        sys.modules.pop(name, None)


def pdoc_folder(plugin_dir: Path, out_dir: Path, modules: list[str]) -> None:
    import pdoc

    out_dir.mkdir(parents=True, exist_ok=True)
    inserted = str(plugin_dir)
    sys.path.insert(0, inserted)
    sys.path.insert(0, str(ROOT))
    try:
        purge_plugin_modules(modules)
        pdoc.pdoc(*modules, output_directory=out_dir)
        print(f"  wrote {out_dir.relative_to(ROOT)} ({len(modules)} modules)")
    finally:
        purge_plugin_modules(modules)
        while inserted in sys.path:
            sys.path.remove(inserted)
        if str(ROOT) in sys.path:
            try:
                sys.path.remove(str(ROOT))
            except ValueError:
                pass


def build_app() -> None:
    import pdoc

    sys.path.insert(0, str(ROOT))
    print("pdoc app -> docs/en")
    pdoc.pdoc("app", output_directory=DOCS_EN)
    if str(ROOT) in sys.path:
        sys.path.remove(str(ROOT))


def build_plugins() -> None:
    plugins = ROOT / "plugins"
    groups = [
        (
            plugins / "3dsmax",
            DOCS_EN / "plugins" / "3dsmax",
            [
                "startup",
                "cortex_ui",
                "loader",
                "publisher_max",
                "publisher_mat_max",
                "save_view",
                "style",
            ],
        ),
        (
            plugins / "blender",
            DOCS_EN / "plugins" / "blender",
            [
                "startup",
                "cortex_ui",
                "loader",
                "publisher_blender",
                "publisher_mat_blender",
                "save_view",
                "style",
            ],
        ),
        (
            plugins / "maya",
            DOCS_EN / "plugins" / "maya",
            [
                "userSetup",
                "loader",
                "publisher_maya",
                "publisher_mat_maya",
                "save_view",
                "style",
            ],
        ),
        (
            plugins / "houdini" / "scripts",
            DOCS_EN / "plugins" / "houdini",
            [
                "loader",
                "publisher_houdini",
                "publisher_mat_houdini",
                "save_view",
                "open_latest",
                "hda_creator",
                "style",
            ],
        ),
        (
            plugins / "photoshop",
            DOCS_EN / "plugins" / "photoshop",
            [
                "startup",
                "cortex_ui",
                "photoshop_publisher",
                "save_view",
                "style",
            ],
        ),
        (
            plugins / "common",
            DOCS_EN / "plugins" / "common",
            ["publisher_2d"],
        ),
    ]
    print("pdoc plugins -> docs/en/plugins/<dcc>")
    for folder, out, modules in groups:
        pdoc_folder(folder, out, modules)


def main() -> int:
    stub_dcc()
    build_app()
    build_plugins()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
