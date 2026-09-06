import json
import pytest

from modules import ui
from modules.enhancement_registry import ENHANCER_KEYS
from modules.quality_profiles import apply_quality_profile


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    for name, value in vars(ui.modules.globals).copy().items():
        if not name.startswith("_"):
            monkeypatch.setattr(ui.modules.globals, name, value)
    apply_quality_profile("balanced", ui.modules.globals)
    monkeypatch.setattr(ui.modules.globals, "opacity", 1.0)
    path = tmp_path / "switch_states.json"
    monkeypatch.setattr(ui, "_switch_state_path", lambda: path)
    return path


@pytest.mark.parametrize("payload", [[], None, True, 3, "settings"])
def test_non_object_settings_do_not_break_startup(settings_path, payload):
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    ui.load_switch_states()

    assert ui.modules.globals.quality_mode == "balanced"
    assert ui.modules.globals.opacity == 1.0


@pytest.mark.parametrize("payload", [None, [1], "bad", {"unknown_processor": True}])
def test_invalid_enhancer_settings_keep_known_profile_defaults(settings_path, payload):
    expected = ui.modules.globals.fp_ui.copy()
    settings_path.write_text(json.dumps({"fp_ui": payload}), encoding="utf-8")

    ui.load_switch_states()

    assert ui.modules.globals.fp_ui == expected
    assert set(ui.modules.globals.fp_ui) == set(ENHANCER_KEYS)


@pytest.mark.parametrize("value", [None, "broken", True, -1, 2, float("nan"), float("inf")])
def test_invalid_opacity_uses_default(settings_path, value):
    settings_path.write_text(json.dumps({"opacity": value}), encoding="utf-8")

    ui.load_switch_states()

    assert ui.modules.globals.opacity == 1.0
    assert not isinstance(ui.modules.globals.opacity, bool)


def test_invalid_utf8_settings_do_not_break_startup(settings_path):
    settings_path.write_bytes(b"\xff\xfeinvalid")

    ui.load_switch_states()

    assert ui.modules.globals.quality_mode == "balanced"


def test_invalid_quality_values_preserve_valid_settings(settings_path):
    expected_sharpness = ui.modules.globals.sharpness
    expected_mouth_size = ui.modules.globals.mouth_mask_size
    settings_path.write_text(json.dumps({
        "sharpness": None,
        "mouth_mask_size": "broken",
        "face_tracking_max_missed": 1.5,
        "live_detection_interval_ratio": float("nan"),
        "keep_audio": "false",
        "live_mirror": True,
        "opacity": 0.65,
        "interpolation_weight": 0.42,
    }), encoding="utf-8")

    ui.load_switch_states()

    assert ui.modules.globals.sharpness == expected_sharpness
    assert ui.modules.globals.mouth_mask_size == expected_mouth_size
    assert ui.modules.globals.face_tracking_max_missed == 1
    assert ui.modules.globals.live_detection_interval_ratio == 0.08
    assert ui.modules.globals.keep_audio is True
    assert ui.modules.globals.live_mirror is True
    assert ui.modules.globals.opacity == 0.65
    assert ui.modules.globals.interpolation_weight == 0.42


def test_save_preserves_previous_settings_when_write_fails(settings_path, monkeypatch):
    previous = '{"opacity": 0.5}'
    settings_path.write_text(previous, encoding="utf-8")

    def interrupted_dump(_state, handle, **_kwargs):
        handle.write('{"partial":')
        raise OSError("disk full")

    monkeypatch.setattr(ui.json, "dump", interrupted_dump)

    ui.save_switch_states()

    assert settings_path.read_text(encoding="utf-8") == previous
    assert list(settings_path.parent.iterdir()) == [settings_path]


def test_save_preserves_previous_settings_when_replacement_fails(settings_path, monkeypatch):
    previous = '{"opacity": 0.5}'
    settings_path.write_text(previous, encoding="utf-8")

    def failed_replace(*_args):
        raise PermissionError("settings are locked")

    monkeypatch.setattr(ui.os, "replace", failed_replace)

    ui.save_switch_states()

    assert settings_path.read_text(encoding="utf-8") == previous
    assert list(settings_path.parent.iterdir()) == [settings_path]


def test_settings_round_trip_preserves_user_choices(settings_path):
    ui.modules.globals.opacity = 0.7
    ui.modules.globals.sharpness = 2.0
    ui.modules.globals.mouth_mask_size = 14.0
    ui.modules.globals.keep_audio = False
    ui.modules.globals.fp_ui = dict.fromkeys(ENHANCER_KEYS, False)

    ui.save_switch_states()
    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    apply_quality_profile("experimental", ui.modules.globals)
    ui.load_switch_states()

    assert saved["opacity"] == ui.modules.globals.opacity == 0.7
    assert ui.modules.globals.sharpness == 2.0
    assert ui.modules.globals.mouth_mask_size == 14.0
    assert ui.modules.globals.keep_audio is False
    assert not any(ui.modules.globals.fp_ui.values())


def test_unserializable_settings_preserve_previous_file(settings_path):
    previous = '{"opacity": 0.5}'
    settings_path.write_text(previous, encoding="utf-8")
    ui.modules.globals.opacity = float("nan")

    ui.save_switch_states()

    assert settings_path.read_text(encoding="utf-8") == previous
    assert list(settings_path.parent.iterdir()) == [settings_path]
