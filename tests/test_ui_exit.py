import inspect

from modules import ui


def test_destroy_without_quit_passes_non_quitting_cleanup_flag():
    calls = []

    def destroy(*, to_quit=True):
        calls.append(to_quit)

    ui._destroy_without_quit(destroy)

    assert calls == [False]


def test_destroy_without_quit_swallows_legacy_system_exit():
    def destroy():
        raise SystemExit(0)

    ui._destroy_without_quit(destroy)


def test_exit_button_uses_qt_close_path():
    source = inspect.getsource(ui.MainWindow._on_exit)

    assert "_destroy_without_quit" in source
    assert "_finish_exit" in source
