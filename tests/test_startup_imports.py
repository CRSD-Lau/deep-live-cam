import ast
from pathlib import Path


STARTUP_MODULES = (
    Path("modules/core.py"),
    Path("modules/platform_info.py"),
    Path("modules/ui.py"),
    Path("modules/processors/frame/face_swapper.py"),
    Path("modules/processors/frame/face_enhancer.py"),
)


def test_desktop_startup_modules_do_not_eagerly_import_heavy_ml_runtimes():
    for module_path in STARTUP_MODULES:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {node.module.split(".")[0]} if node.module else set()
            else:
                continue

            assert "tensorflow" not in names, f"{module_path} eagerly imports tensorflow"
            assert "torch" not in names, f"{module_path} eagerly imports torch"
