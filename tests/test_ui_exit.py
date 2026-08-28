import inspect
from types import SimpleNamespace

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


def test_status_flush_excludes_user_input_to_prevent_reentrant_render_clicks(monkeypatch):
    current_thread = ui.QThread.currentThread()
    processed_with = []

    class FakeApp:
        def thread(self):
            return current_thread

        def processEvents(self, *flags):
            processed_with.append(flags)

    monkeypatch.setattr(ui, "_APP", FakeApp())
    monkeypatch.setattr(ui, "_emit_status", lambda _text: None)

    ui.update_status("Processing...")

    assert processed_with == [
        (ui.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents,)
    ]


def test_file_operation_gate_rejects_reentrant_preview_or_render_calls():
    button_states = []

    class FakeButton:
        def setEnabled(self, enabled):
            button_states.append(enabled)

    window = SimpleNamespace(
        _file_operation_running=False,
        btn_start=FakeButton(),
        btn_preview=FakeButton(),
    )
    calls = []

    def outer_operation():
        calls.append("outer")
        nested_started = ui.MainWindow._run_file_operation(
            window,
            lambda: calls.append("nested"),
            "Nested operation failed.",
        )
        calls.append(f"nested_started={nested_started}")

    started = ui.MainWindow._run_file_operation(
        window,
        outer_operation,
        "Outer operation failed.",
    )

    assert started is True
    assert calls == ["outer", "nested_started=False"]
    assert window._file_operation_running is False
    assert button_states == [False, False, True, True]


def test_file_preview_does_not_start_while_live_output_is_open(monkeypatch):
    class FakeWindow:
        _file_operation_running = False

        def _run_file_operation(self, *_args, **_kwargs):
            raise AssertionError("file Preview must not start during Live Output")

    preview = SimpleNamespace(isVisible=lambda: False)
    live_preview = SimpleNamespace(isVisible=lambda: True)
    statuses = []

    monkeypatch.setattr(ui, "_PREVIEW", preview)
    monkeypatch.setattr(ui, "_WEBCAM_PREVIEW", live_preview)
    monkeypatch.setattr(ui, "update_status", statuses.append)
    monkeypatch.setattr(ui.modules.globals, "source_path", "source.jpg")
    monkeypatch.setattr(ui.modules.globals, "target_path", "target.mp4")

    ui.MainWindow._on_toggle_preview(FakeWindow())

    assert statuses == ["Stop live output before opening file Preview."]
