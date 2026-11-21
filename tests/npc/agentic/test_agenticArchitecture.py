"""Architecture rules for src/npc/agentic (ports and adapters).

- model, core and ports never import adapters or service (dependencies point
  inward), and never import I/O libraries directly.
- each port file and each adapter file declares exactly one top-level class.
"""

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3] / "src" / "npc" / "agentic"
INNER = [ROOT / "model.py", ROOT / "core.py", *sorted((ROOT / "ports").glob("*.py"))]
ONE_CLASS = [
    p
    for d in ("ports", "adapters")
    for p in sorted((ROOT / d).glob("*.py"))
    if p.name != "__init__.py"
]
OUTER = ("npc.agentic.adapters", "npc.agentic.service")
IO_MODULES = ("os", "threading", "anthropic", "socket", "urllib", "subprocess")


def _imports(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_layout_is_present():
    assert (ROOT / "service.py").exists()
    assert len(ONE_CLASS) >= 4


@pytest.mark.parametrize("path", INNER, ids=lambda p: p.name)
def test_inner_layers_do_not_import_outer_layers_or_io(path):
    for name in _imports(path):
        assert not name.startswith(OUTER), f"{path.name} imports {name}"
        assert name.split(".")[0] not in IO_MODULES, f"{path.name} imports {name}"


@pytest.mark.parametrize("path", ONE_CLASS, ids=lambda p: p.name)
def test_one_top_level_class_per_port_and_adapter_file(path):
    tree = ast.parse(path.read_text())
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1, f"{path.name} declares {classes}"
