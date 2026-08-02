import json
from pathlib import Path

from tools import check_windows_release_cutover as cutover


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_classifies_release_mixed_and_unknown_paths():
    release_paths, mixed_paths, unknown_paths = cutover.classify(
        [
            "build/windows/run_release_checks.ps1",
            "CHANGELOG.md",
            "modules/metadata.py",
            "modules/model_manager.py",
            "modules/compositing/blend.py",
            "scratch.txt",
        ]
    )

    assert release_paths == [
        "CHANGELOG.md",
        "build/windows/run_release_checks.ps1",
        "modules/metadata.py",
        "modules/model_manager.py",
    ]
    assert mixed_paths == ["modules/compositing/blend.py"]
    assert unknown_paths == ["scratch.txt"]


def test_porcelain_rename_uses_new_path():
    assert cutover.parse_porcelain_line("R  old/path.py -> modules/model_manager.py") == "modules/model_manager.py"


def test_porcelain_entry_tracks_staged_and_unstaged_state():
    staged = cutover.parse_porcelain_entry("M  modules/model_manager.py")
    unstaged = cutover.parse_porcelain_entry(" M modules/model_manager.py")
    untracked = cutover.parse_porcelain_entry("?? modules/model_manager.py")

    assert staged.path == "modules/model_manager.py"
    assert staged.staged
    assert not staged.unstaged
    assert not unstaged.staged
    assert unstaged.unstaged
    assert not untracked.staged
    assert untracked.unstaged


def test_evidence_gate_requires_pass_and_no_open_items(tmp_path):
    evidence = tmp_path / "LEGAL_REVIEW.md"
    write_file(evidence, "Status: PASS\n\n- [ ] pending legal signoff\n")

    assert cutover.evidence_status(evidence) == "PASS"
    assert cutover.evidence_open_items(evidence) == 1

    write_file(evidence, "Status: PASS\n\n- [x] legal signoff recorded\n")

    assert cutover.evidence_status(evidence) == "PASS"
    assert cutover.evidence_open_items(evidence) == 0


def test_strict_mode_fails_until_tree_and_gates_are_clean(tmp_path, monkeypatch, capsys):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: " M modules/model_manager.py\n?? modules/compositing/blend.py\n",
    )

    assert cutover.main(["--repo-root", str(tmp_path), "--strict"]) == 1
    output = capsys.readouterr().out
    assert "modules/model_manager.py" in output
    assert "modules/compositing/blend.py" in output
    assert "mixed-scope dirty paths" in output


def test_strict_mode_can_ignore_known_mixed_scope_dirty_paths_for_git_ref_release(tmp_path, monkeypatch, capsys):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: "?? modules/compositing/blend.py\n",
    )

    assert (
        cutover.main(
            [
                "--repo-root",
                str(tmp_path),
                "--strict",
                "--allow-mixed-scope-dirty",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Mixed-scope dirty paths block verdict: `NO`" in output
    assert "NOTE: mixed-scope dirty paths were reported" in output


def test_mixed_scope_override_still_blocks_release_owned_paths(tmp_path, monkeypatch, capsys):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: " M modules/model_manager.py\n?? modules/compositing/blend.py\n",
    )

    assert (
        cutover.main(
            [
                "--repo-root",
                str(tmp_path),
                "--strict",
                "--allow-mixed-scope-dirty",
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "release-owned dirty paths must be committed" in output
    assert "modules/model_manager.py" in output


def test_writes_markdown_report(tmp_path, monkeypatch):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: " M modules/model_manager.py\n?? modules/compositing/blend.py\n",
    )

    output = tmp_path / "RELEASE_CUTOVER_STATUS.md"

    assert cutover.main(["--repo-root", str(tmp_path), "--output", str(output)]) == 0
    report = output.read_text(encoding="utf-8")
    assert "# Windows Release Cutover Status" in report
    assert "`modules/model_manager.py`" in report
    assert "`modules/compositing/blend.py`" in report
    assert "BLOCKED: mixed-scope dirty paths" in report


def test_output_report_path_does_not_block_itself(tmp_path, monkeypatch):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: " M RELEASE_CUTOVER_STATUS.md\n?? modules/compositing/blend.py\n",
    )

    output = tmp_path / "RELEASE_CUTOVER_STATUS.md"

    assert (
        cutover.main(
            [
                "--repo-root",
                str(tmp_path),
                "--output",
                str(output),
                "--strict",
                "--allow-mixed-scope-dirty",
            ]
        )
        == 0
    )
    report = output.read_text(encoding="utf-8")
    assert "Release-required or release-owned dirty paths: 0" in report
    assert "`RELEASE_CUTOVER_STATUS.md`" not in report


def test_generated_clean_worktree_source_scratch_does_not_block_cutover(tmp_path, monkeypatch, capsys):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: (
            "?? build/windows/clean-worktree-source-check/DeepLiveCamStudio-2.1.7-source-test.zip\n"
            "?? build/windows/clean-worktree-source-check/DeepLiveCamStudio-2.1.7-source-test.zip.sha256\n"
            "?? build/windows/clean-worktree-source-check/DeepLiveCamStudio-2.1.7-source-test.manifest.md\n"
        ),
    )

    assert cutover.main(["--repo-root", str(tmp_path), "--strict"]) == 0
    output = capsys.readouterr().out
    assert "Dirty paths: `0`" in output
    assert "clean-worktree-source-check" not in output


def test_writes_json_report(tmp_path, monkeypatch):
    for gate in cutover.MANUAL_GATE_FILES:
        write_file(tmp_path / gate, "Status: PASS\n- [x] done\n")

    monkeypatch.setattr(
        cutover,
        "run_git",
        lambda args, cwd: " M modules/model_manager.py\n?? modules/compositing/blend.py\n",
    )

    output = tmp_path / "cutover.json"

    assert cutover.main(["--repo-root", str(tmp_path), "--json-output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["release_paths"] == ["modules/model_manager.py"]
    assert payload["mixed_scope_paths"] == ["modules/compositing/blend.py"]
    assert payload["unknown_paths"] == []
    assert payload["staged_release_paths"] == []
    assert payload["unstaged_release_paths"] == ["modules/model_manager.py"]
    assert not payload["ready"]
