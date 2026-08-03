import re
import struct
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = (
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "docs/README.md",
    "docs/BUILDING.md",
    "docs/DIRECTML_TESTING.md",
    "docs/OBS_VIRTUAL_CAMERA.md",
)


def _relative_links(markdown: str) -> list[str]:
    targets = re.findall(r"!?(?:\[[^\]]*\])\(([^)]+)\)", markdown)
    targets.extend(re.findall(r'<img\s+[^>]*src="([^"]+)"', markdown))
    return [target.strip().split(" ", 1)[0].strip("<>") for target in targets]


def test_public_documentation_has_no_broken_relative_links():
    broken: list[str] = []

    for relative_doc in PUBLIC_DOCS:
        document = ROOT / relative_doc
        assert document.is_file(), relative_doc
        for target in _relative_links(document.read_text(encoding="utf-8")):
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            relative_target = unquote(target.split("#", 1)[0])
            if not relative_target:
                continue
            resolved = (document.parent / relative_target).resolve()
            if not resolved.exists():
                broken.append(f"{relative_doc} -> {target}")

    assert broken == []


def test_repository_has_complete_community_health_files():
    required = (
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "SUPPORT.md",
        "GOVERNANCE.md",
        ".github/CODEOWNERS",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
    )

    assert [path for path in required if not (ROOT / path).is_file()] == []


def test_issue_forms_are_valid_and_disable_blank_issues():
    bug = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/bug_report.yml").read_text(encoding="utf-8"))
    feature = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/feature_request.yml").read_text(encoding="utf-8"))
    config = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE/config.yml").read_text(encoding="utf-8"))

    assert bug["name"] == "Bug report"
    assert bug["description"]
    assert feature["name"] == "Feature request"
    assert feature["description"]
    assert config["blank_issues_enabled"] is False
    assert any("security/advisories/new" in link["url"] for link in config["contact_links"])


def test_readme_uses_release_independent_download_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "releases/latest" in readme
    assert "/releases/tag/v" not in readme
    assert "/releases/download/v" not in readme
    assert "DeepLiveCamStudio-<version>-x64-setup.exe" in readme
    assert "DeepLiveCamStudio-<version>-DirectML-x64-portable.zip" in readme


def test_social_preview_matches_github_recommendations():
    preview = ROOT / "docs/images/social-preview.png"
    data = preview.read_bytes()

    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (1280, 640)
    assert preview.stat().st_size < 1_000_000
