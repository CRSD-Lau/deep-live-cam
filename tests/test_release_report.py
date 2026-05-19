from pathlib import Path


def test_windows_release_report_covers_required_final_report_sections():
    report = Path("RELEASE_REPORT.md").read_text(encoding="utf-8")

    required_sections = [
        "## Packaging Approach",
        "## Files Changed For Packaging And Compliance",
        "## Build Commands",
        "## Installer Output",
        "## Dependencies Bundled",
        "## Dependencies Not Bundled",
        "## Model Files",
        "## License Obligations Found",
        "## Remaining Legal Risks",
        "## Manual Checks Required Before Publishing",
    ]

    for section in required_sections:
        assert section in report

    required_phrases = [
        "PyInstaller onedir application bundle wrapped by Inno Setup",
        "Bundled model files: none.",
        "DeepLiveCamStudioCLI.exe --download-models",
        "%LOCALAPPDATA%\\DeepLiveCamStudio\\models",
        "Deep-Live-Cam is AGPL-3.0",
        "Do not bundle without legal review",
        "set `Status: PASS` only after",
    ]

    for phrase in required_phrases:
        assert phrase in report
