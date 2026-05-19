from modules import desktop_launcher


def test_prepare_desktop_environment_sets_cwd_path_and_search_path(monkeypatch, tmp_path):
    path_entries = []
    monkeypatch.setattr(desktop_launcher.os, "chdir", lambda path: path_entries.append(path))
    monkeypatch.setattr(desktop_launcher.sys, "path", [])
    monkeypatch.setenv("PATH", "existing")

    root = desktop_launcher.prepare_desktop_environment(tmp_path)

    assert root == tmp_path
    assert path_entries == [tmp_path]
    assert desktop_launcher.sys.path[0] == str(tmp_path)
    assert desktop_launcher.os.environ["PATH"].startswith(str(tmp_path))


def test_desktop_log_path_lives_under_runtime(tmp_path):
    assert desktop_launcher.desktop_log_path(tmp_path) == (
        tmp_path / "runtime" / "desktop-launch.log"
    )


def test_redirect_desktop_output_writes_banner(tmp_path):
    log_path = tmp_path / "runtime" / "desktop-launch.log"
    original_stdout = desktop_launcher.sys.stdout
    original_stderr = desktop_launcher.sys.stderr

    stream = desktop_launcher.redirect_desktop_output(log_path)
    try:
        print("hello desktop")
    finally:
        desktop_launcher.sys.stdout = original_stdout
        desktop_launcher.sys.stderr = original_stderr
        stream.close()

    contents = log_path.read_text(encoding="utf-8")
    assert "Deep Live Cam Studio desktop launch" in contents
    assert "hello desktop" in contents
