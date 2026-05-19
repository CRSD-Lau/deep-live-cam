import json
import os
from pathlib import Path

from tools import summarize_manual_release_gates as gates


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_collects_status_open_items_and_latest_evidence(tmp_path):
    write_file(tmp_path / "CLEAN_VM_VERIFICATION.md", "Status: PENDING\n- [ ] install\n- [x] hash\n")
    write_file(tmp_path / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [x] obs\n")
    write_file(tmp_path / "LEGAL_REVIEW.md", "Status: PASS\n- [ ] legal\n")
    write_file(tmp_path / "build/windows/manual-evidence/clean-vm/clean-vm-old.md", "old")
    new_evidence = tmp_path / "build/windows/manual-evidence/clean-vm/clean-vm-new.md"
    write_file(new_evidence, "new")
    os.utime(new_evidence, (2_000_000_000, 2_000_000_000))

    summaries = gates.collect(tmp_path)

    clean_vm = summaries[0]
    assert clean_vm.status == "PENDING"
    assert clean_vm.open_items == ["install"]
    assert clean_vm.latest_evidence == "build/windows/manual-evidence/clean-vm/clean-vm-new.md"
    assert not clean_vm.passed
    assert summaries[1].passed
    assert not summaries[2].passed


def test_strict_mode_fails_until_all_manual_gates_pass(tmp_path, capsys):
    write_file(tmp_path / "CLEAN_VM_VERIFICATION.md", "Status: PASS\n- [x] install\n")
    write_file(tmp_path / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PENDING\n- [ ] obs\n")
    write_file(tmp_path / "LEGAL_REVIEW.md", "Status: PASS\n- [x] legal\n")

    assert gates.main(["--repo-root", str(tmp_path), "--strict"]) == 1
    output = capsys.readouterr().out
    assert "BLOCKED: `OBS_VIRTUAL_CAMERA_VERIFICATION.md`" in output
    assert "- obs" in output


def test_writes_json_summary(tmp_path):
    for _, gate_path, _ in gates.GATES:
        write_file(tmp_path / gate_path, "Status: PASS\n- [x] done\n")

    output = tmp_path / "summary.json"
    assert gates.main(["--repo-root", str(tmp_path), "--json-output", str(output), "--strict"]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["ready"] is True
    assert [gate["passed"] for gate in payload["gates"]] == [True, True, True]
