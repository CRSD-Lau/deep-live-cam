import json
import os
from pathlib import Path

import pytest

from tools import summarize_manual_release_gates as gates


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collects_status_open_items_and_latest_evidence(tmp_path):
    write_file(tmp_path / "CLEAN_VM_VERIFICATION.md", "Status: PENDING\nRelease: `2.2.4`\n- [ ] install\n- [x] hash\n")
    write_file(tmp_path / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\nRelease: `2.2.4`\n- [x] obs\n")
    write_file(tmp_path / "LEGAL_REVIEW.md", "Status: PASS\nRelease: `2.2.4`\n- [ ] legal\n")
    write_file(tmp_path / "build/windows/manual-evidence/clean-vm/clean-vm-old.md", "old")
    new_evidence = tmp_path / "build/windows/manual-evidence/clean-vm/clean-vm-new.md"
    write_file(new_evidence, "new")
    os.utime(new_evidence, (2_000_000_000, 2_000_000_000))

    summaries = gates.collect(tmp_path, "2.2.4")

    clean_vm = summaries[0]
    assert clean_vm.status == "PENDING"
    assert clean_vm.open_items == ["install"]
    assert clean_vm.latest_evidence == "build/windows/manual-evidence/clean-vm/clean-vm-new.md"
    assert not clean_vm.passed
    assert summaries[1].passed
    assert not summaries[2].passed


def test_strict_mode_fails_until_all_manual_gates_pass(tmp_path, capsys):
    write_file(tmp_path / "CLEAN_VM_VERIFICATION.md", "Status: PASS\nRelease: `2.2.4`\n- [x] install\n")
    write_file(tmp_path / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PENDING\nRelease: `2.2.4`\n- [ ] obs\n")
    write_file(tmp_path / "LEGAL_REVIEW.md", "Status: PASS\nRelease: `2.2.4`\n- [x] legal\n")

    assert gates.main(["--repo-root", str(tmp_path), "--app-version", "2.2.4", "--strict"]) == 1
    output = capsys.readouterr().out
    assert "BLOCKED: `OBS_VIRTUAL_CAMERA_VERIFICATION.md`" in output
    assert "- obs" in output


def test_writes_json_summary(tmp_path):
    for _, gate_path, _ in gates.GATES:
        write_file(tmp_path / gate_path, "Status: PASS\nRelease: `2.2.4`\n- [x] done\n")

    output = tmp_path / "summary.json"
    assert gates.main(["--repo-root", str(tmp_path), "--app-version", "2.2.4", "--json-output", str(output), "--strict"]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["ready"] is True
    assert [gate["passed"] for gate in payload["gates"]] == [True] * len(gates.GATES)


def test_strict_mode_rejects_historical_release_evidence(tmp_path, capsys):
    write_file(tmp_path / "modules/metadata.py", "version = '2.2.4'\n")
    for _, gate_path, _ in gates.GATES:
        write_file(tmp_path / gate_path, "Status: PASS\nRelease: `2.2.3`\n- [x] done\n")

    assert gates.main(["--repo-root", str(tmp_path), "--strict"]) == 1
    output = capsys.readouterr().out
    assert "2.2.3" in output and "2.2.4" in output
    assert "does not match" in output


def test_strict_mode_requires_known_requested_release(tmp_path, capsys):
    for _, gate_path, _ in gates.GATES:
        write_file(tmp_path / gate_path, "Status: PASS\nRelease: `2.2.4`\n- [x] done\n")

    assert gates.main(["--repo-root", str(tmp_path), "--strict"]) == 1
    assert "requested app version is missing" in capsys.readouterr().out


@pytest.mark.parametrize("gate_path", [gate_path for _, gate_path, _ in gates.GATES])
@pytest.mark.parametrize("bad_evidence", [
    "Status: PASS\n- [x] missing release\n",
    "Release: `2.2.4`\n- [x] no verdict\n",
    "Status: PASS\nRelease: `2.2.4`\n+ [ ] incomplete\n",
    "Status: PASS\nStatus: PENDING\nRelease: `2.2.4`\n",
])
def test_all_summary_gates_require_unambiguous_release_approval(
    tmp_path, gate_path, bad_evidence,
):
    for _, path, _ in gates.GATES:
        write_file(tmp_path / path, "Status: PASS\nRelease: `2.2.4`\n- [x] done\n")
    write_file(tmp_path / gate_path, bad_evidence)

    summaries = gates.collect(tmp_path, "2.2.4")
    failed = [summary for summary in summaries if not summary.passed]

    assert [summary.path for summary in failed] == [gate_path]
    assert failed[0].failures
    assert (tmp_path / gate_path).read_text(encoding="utf-8") == bad_evidence


def test_explicit_app_version_overrides_metadata(tmp_path):
    write_file(tmp_path / "modules/metadata.py", "version = '2.2.5'\n")
    for _, gate_path, _ in gates.GATES:
        write_file(tmp_path / gate_path, "Status: PASS\nRelease: `2.2.4`\n")

    assert gates.main([
        "--repo-root", str(tmp_path), "--app-version", "2.2.4", "--strict",
    ]) == 0


def test_version_inference_does_not_execute_repository_metadata(tmp_path):
    write_file(
        tmp_path / "modules/metadata.py",
        "version = '2.2.4'\nraise RuntimeError('metadata must not execute')\n",
    )
    for _, gate_path, _ in gates.GATES:
        write_file(tmp_path / gate_path, "Status: PASS\nRelease: `2.2.4`\n")

    assert gates.main(["--repo-root", str(tmp_path), "--strict"]) == 0


@pytest.mark.parametrize("metadata", [
    "version = dynamic_version()\n",
    "version = '2.2.4'\nversion = dynamic_version()\n",
    "version = '2.2.4'\nversion = '2.2.3'\n",
    "version = 224\n",
    "version =\n",
])
def test_version_inference_rejects_dynamic_or_ambiguous_versions(tmp_path, metadata):
    write_file(tmp_path / "modules/metadata.py", metadata)
    assert gates.infer_app_version(tmp_path) == ""


def test_missing_gate_document_stays_blocked_with_explicit_version(tmp_path):
    summaries = gates.collect(tmp_path, "2.2.4")
    assert all(summary.status == "MISSING" and not summary.passed for summary in summaries)
