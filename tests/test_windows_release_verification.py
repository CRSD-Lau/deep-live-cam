import zipfile

from tools import generate_windows_release_verification as verification


def write_file(path, content="ok"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_release_layout(tmp_path, monkeypatch):
    repo_root = tmp_path
    dist_dir = repo_root / "dist" / "DeepLiveCamStudio"
    output_dir = repo_root / "build" / "windows" / "installer"

    for relative_path in verification.REQUIRED_DIST_FILES:
        write_file(dist_dir / relative_path)

    manifest = dist_dir / "LICENSES" / "WINDOWS_BUNDLE_MANIFEST.md"
    write_file(manifest, "Forbidden model/checkpoint files found: 0\n")

    installer = output_dir / "DeepLiveCamStudio-2.1.5-x64-setup.exe"
    installer.parent.mkdir(parents=True, exist_ok=True)
    installer.write_bytes(b"fake installer")
    write_file(installer.with_suffix(installer.suffix + ".sha256"), f"{verification.sha256(installer)}  {installer.name}\n")

    source_archive = output_dir / "DeepLiveCamStudio-2.1.5-source-testref.zip"
    with zipfile.ZipFile(source_archive, "w") as archive:
        archive.writestr("DeepLiveCamStudio-2.1.5-source/README.md", "source")
    write_file(source_archive.with_suffix(".manifest.md"), "Archive mode: `git-ref`\n")
    write_file(source_archive.with_suffix(source_archive.suffix + ".sha256"), f"{verification.sha256(source_archive)}  {source_archive.name}\n")

    write_file(repo_root / verification.MODEL_DOWNLOAD_VERIFICATION, "models verified")
    write_file(repo_root / verification.PROCESSING_VERIFICATION, "processing verified")
    write_file(
        repo_root / verification.CUTOVER_STATUS,
        "\n".join(
            [
                "# Windows Release Cutover Status",
                "",
                "Dirty paths: `0`",
                "Staged release-owned paths: `0`",
                "Unstaged release-owned paths: `0`",
                "",
                "## Release-required or release-owned dirty paths: 0",
                "",
                "## Mixed-scope dirty paths requiring explicit include/exclude decision: 0",
                "",
                "## Unknown dirty paths requiring review: 0",
                "",
                "## Verdict",
                "",
                "- READY: working tree and manual cutover evidence are clean",
            ]
        ),
    )

    monkeypatch.setattr(
        verification,
        "run_git",
        lambda args, cwd: "abc123" if args == ["rev-parse", "HEAD"] else "",
    )
    return repo_root, dist_dir, output_dir


def test_manual_gate_evidence_requires_pass_and_no_open_items(tmp_path):
    evidence = tmp_path / "gate.md"
    write_file(evidence, "Status: PASS\n\n- [ ] unfinished\n")

    assert verification.evidence_status(evidence) == "PASS"
    assert verification.evidence_open_items(evidence) == 1
    assert not verification.evidence_passed(evidence)

    write_file(evidence, "Status: PASS\n\n- [x] finished\n")
    assert verification.evidence_open_items(evidence) == 0
    assert verification.evidence_passed(evidence)


def test_publish_ready_requires_completed_manual_evidence(tmp_path, monkeypatch):
    repo_root, dist_dir, output_dir = make_release_layout(tmp_path, monkeypatch)

    write_file(repo_root / "CLEAN_VM_VERIFICATION.md", "Status: PASS\n- [x] install checked\n")
    write_file(repo_root / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [ ] obs still pending\n")
    write_file(repo_root / "LEGAL_REVIEW.md", "Status: PASS\n- [x] legal checked\n")

    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert not publishable
    assert blockers
    assert "`OBS_VIRTUAL_CAMERA_VERIFICATION.md`" in text
    assert "Open checklist items: `1`" in text
    assert "OBS_VIRTUAL_CAMERA_VERIFICATION.md is `PASS` with 1 open checklist item(s)." in text

    write_file(repo_root / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [x] obs checked\n")
    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert publishable
    assert not blockers
    assert "Ready to publish without remaining manual gates: **YES**" in text


def test_publish_ready_requires_matching_source_hash_sidecar(tmp_path, monkeypatch):
    repo_root, dist_dir, output_dir = make_release_layout(tmp_path, monkeypatch)

    write_file(repo_root / "CLEAN_VM_VERIFICATION.md", "Status: PASS\n- [x] install checked\n")
    write_file(repo_root / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [x] obs checked\n")
    write_file(repo_root / "LEGAL_REVIEW.md", "Status: PASS\n- [x] legal checked\n")
    write_file(output_dir / "DeepLiveCamStudio-2.1.5-source-testref.zip.sha256", "BADHASH  source.zip\n")

    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert not publishable
    assert blockers
    assert "Corresponding-source SHA-256 sidecar matches" in text
    assert "Corresponding-source archive, hash sidecar, manifest, or forbidden-file scan is incomplete." in blockers


def test_publish_ready_requires_clean_cutover_status(tmp_path, monkeypatch):
    repo_root, dist_dir, output_dir = make_release_layout(tmp_path, monkeypatch)

    write_file(repo_root / "CLEAN_VM_VERIFICATION.md", "Status: PASS\n- [x] install checked\n")
    write_file(repo_root / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [x] obs checked\n")
    write_file(repo_root / "LEGAL_REVIEW.md", "Status: PASS\n- [x] legal checked\n")
    write_file(
        repo_root / verification.CUTOVER_STATUS,
        "Dirty paths: `2`\n\n"
        "Staged release-owned paths: `1`\n"
        "Unstaged release-owned paths: `0`\n\n"
        "## Release-required or release-owned dirty paths: 1\n\n"
        "## Mixed-scope dirty paths requiring explicit include/exclude decision: 1\n\n"
        "## Unknown dirty paths requiring review: 0\n\n"
        "## Verdict\n\n"
        "- BLOCKED: mixed-scope dirty paths still need an include/exclude decision\n",
    )

    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert not publishable
    assert "## Cutover Status" in text
    assert "Staged release-owned paths: `1`" in text
    assert "Mixed-scope dirty paths: `1`" in text
    assert "RELEASE_CUTOVER_STATUS.md reports unresolved cutover blockers." in blockers


def test_git_ref_source_allows_known_mixed_scope_dirty_worktree(tmp_path, monkeypatch):
    repo_root, dist_dir, output_dir = make_release_layout(tmp_path, monkeypatch)

    write_file(repo_root / "CLEAN_VM_VERIFICATION.md", "Status: PASS\n- [x] install checked\n")
    write_file(repo_root / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [x] obs checked\n")
    write_file(repo_root / "LEGAL_REVIEW.md", "Status: PASS\n- [x] legal checked\n")
    write_file(
        repo_root / verification.CUTOVER_STATUS,
        "\n".join(
            [
                "# Windows Release Cutover Status",
                "",
                "Dirty paths: `1`",
                "Staged release-owned paths: `0`",
                "Unstaged release-owned paths: `0`",
                "Mixed-scope dirty paths block verdict: `NO`",
                "",
                "## Release-required or release-owned dirty paths: 0",
                "",
                "## Mixed-scope dirty paths requiring explicit include/exclude decision: 1",
                "",
                "## Unknown dirty paths requiring review: 0",
                "",
                "## Verdict",
                "",
                "- READY: release-owned paths, unknown paths, and manual cutover evidence are clean",
                "- NOTE: mixed-scope dirty paths were reported but did not block this Git-ref release cutover",
            ]
        ),
    )
    monkeypatch.setattr(
        verification,
        "run_git",
        lambda args, cwd: (
            "abc123"
            if args == ["rev-parse", "HEAD"]
            else "?? modules/compositing/blend.py\n"
        ),
    )

    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert publishable
    assert not blockers
    assert "Public-release source archive from clean Git ref: **YES**" in text
    assert "Mixed-scope dirty paths block verdict: **NO**" in text


def test_git_ref_source_still_blocks_unknown_dirty_paths(tmp_path, monkeypatch):
    repo_root, dist_dir, output_dir = make_release_layout(tmp_path, monkeypatch)

    write_file(repo_root / "CLEAN_VM_VERIFICATION.md", "Status: PASS\n- [x] install checked\n")
    write_file(repo_root / "OBS_VIRTUAL_CAMERA_VERIFICATION.md", "Status: PASS\n- [x] obs checked\n")
    write_file(repo_root / "LEGAL_REVIEW.md", "Status: PASS\n- [x] legal checked\n")
    write_file(
        repo_root / verification.CUTOVER_STATUS,
        "Dirty paths: `1`\n\n"
        "Staged release-owned paths: `0`\n"
        "Unstaged release-owned paths: `0`\n"
        "Mixed-scope dirty paths block verdict: `NO`\n\n"
        "## Release-required or release-owned dirty paths: 0\n\n"
        "## Mixed-scope dirty paths requiring explicit include/exclude decision: 0\n\n"
        "## Unknown dirty paths requiring review: 1\n\n"
        "## Verdict\n\n"
        "- BLOCKED: unknown dirty paths still need review\n",
    )
    monkeypatch.setattr(
        verification,
        "run_git",
        lambda args, cwd: "abc123" if args == ["rev-parse", "HEAD"] else "?? scratch.txt\n",
    )

    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert not publishable
    assert "Working tree contains release-owned or unknown dirty paths." in blockers
    assert "Release cutover status clean: **NO**" in text


def test_release_verification_prefers_git_ref_source_archive(tmp_path, monkeypatch):
    repo_root, dist_dir, output_dir = make_release_layout(tmp_path, monkeypatch)
    source_archive = output_dir / "DeepLiveCamStudio-2.1.5-source-testref.zip"
    draft_archive = output_dir / "DeepLiveCamStudio-2.1.5-source-worktree-testref.zip"
    draft_archive.write_bytes(source_archive.read_bytes())
    write_file(draft_archive.with_suffix(draft_archive.suffix + ".sha256"), f"{verification.sha256(draft_archive)}  {draft_archive.name}\n")
    write_file(draft_archive.with_suffix(".manifest.md"), "Archive mode: `draft-working-tree`\n")

    text, publishable, blockers = verification.generate(repo_root, dist_dir, output_dir, "2.1.5")

    assert "Latest source archive:" in text
    assert "RELEASE_ASSETS.md" in text
    assert "DeepLiveCamStudio-*-source-*.zip" in text
    assert "source-worktree-testref.zip`" not in text
