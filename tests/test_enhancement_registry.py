import pytest

from modules.enhancement_registry import (
    ENHANCER_KEYS,
    active_enhancer_key,
    active_enhancer_label,
    default_enhancer_state,
    enhancer_key_for_processor_name,
    get_enhancer_choices,
    get_enhancer_profile,
    is_enhancer_processor_name,
)


def test_registry_exposes_existing_enhancer_processors():
    assert ENHANCER_KEYS == (
        "face_enhancer",
        "face_enhancer_gpen512",
        "face_enhancer_gpen256",
    )
    assert get_enhancer_profile("face_enhancer_gpen512").label == "GPEN-512"
    assert get_enhancer_profile("face_enhancer_gpen256").output_size == 256


def test_registry_choices_are_ordered_for_ui_quality():
    labels = [profile.label for profile in get_enhancer_choices()]

    assert labels == ["GFPGAN", "GPEN-512", "GPEN-256"]


def test_default_and_active_enhancer_state():
    state = default_enhancer_state()

    assert state == {key: False for key in ENHANCER_KEYS}
    assert active_enhancer_key(state) is None
    state["face_enhancer_gpen512"] = True
    assert active_enhancer_key(state) == "face_enhancer_gpen512"
    assert active_enhancer_label(state) == "GPEN-512"


def test_processor_name_lookup():
    assert (
        enhancer_key_for_processor_name("DLC.FACE-ENHANCER-GPEN512")
        == "face_enhancer_gpen512"
    )
    assert is_enhancer_processor_name("DLC.FACE-ENHANCER")
    assert not is_enhancer_processor_name("DLC.FACE-SWAPPER")


def test_unknown_enhancer_raises_readable_error():
    with pytest.raises(ValueError, match="Unknown enhancer"):
        get_enhancer_profile("codeformer")
