"""Registry for optional face enhancement processors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnhancerProfile:
    key: str
    label: str
    processor_name: str
    model_family: str
    output_size: int
    realtime_rank: int
    quality_rank: int
    notes: str


ENHANCER_PROFILES: dict[str, EnhancerProfile] = {
    "face_enhancer": EnhancerProfile(
        key="face_enhancer",
        label="GFPGAN",
        processor_name="DLC.FACE-ENHANCER",
        model_family="GFPGAN",
        output_size=512,
        realtime_rank=3,
        quality_rank=2,
        notes="Balanced restoration model; useful as the legacy default enhancer.",
    ),
    "face_enhancer_gpen512": EnhancerProfile(
        key="face_enhancer_gpen512",
        label="GPEN-512",
        processor_name="DLC.FACE-ENHANCER-GPEN512",
        model_family="GPEN",
        output_size=512,
        realtime_rank=2,
        quality_rank=3,
        notes="Sharper 512px restoration pass for cinematic/offline profiles.",
    ),
    "face_enhancer_gpen256": EnhancerProfile(
        key="face_enhancer_gpen256",
        label="GPEN-256",
        processor_name="DLC.FACE-ENHANCER-GPEN256",
        model_family="GPEN",
        output_size=256,
        realtime_rank=1,
        quality_rank=1,
        notes="Lower-latency 256px restoration option for live use.",
    ),
}

ENHANCER_KEYS = tuple(ENHANCER_PROFILES.keys())
ENHANCER_PROCESSOR_NAMES = tuple(
    profile.processor_name for profile in ENHANCER_PROFILES.values()
)
_PROCESSOR_NAME_TO_KEY = {
    profile.processor_name: profile.key for profile in ENHANCER_PROFILES.values()
}


def get_enhancer_profile(key: str) -> EnhancerProfile:
    try:
        return ENHANCER_PROFILES[key]
    except KeyError as exc:
        choices = ", ".join(ENHANCER_KEYS)
        raise ValueError(f"Unknown enhancer '{key}'. Choose one of: {choices}.") from exc


def get_enhancer_choices() -> tuple[EnhancerProfile, ...]:
    return tuple(ENHANCER_PROFILES.values())


def default_enhancer_state() -> dict[str, bool]:
    return {key: False for key in ENHANCER_KEYS}


def active_enhancer_key(fp_ui: dict[str, bool] | None) -> str | None:
    fp_ui = fp_ui or {}
    for key in ENHANCER_KEYS:
        if fp_ui.get(key, False):
            return key
    return None


def active_enhancer_label(fp_ui: dict[str, bool] | None) -> str:
    active_key = active_enhancer_key(fp_ui)
    if active_key is None:
        return "None"
    return ENHANCER_PROFILES[active_key].label


def enhancer_key_for_processor_name(processor_name: str) -> str | None:
    return _PROCESSOR_NAME_TO_KEY.get(processor_name)


def is_enhancer_processor_name(processor_name: str) -> bool:
    return enhancer_key_for_processor_name(processor_name) is not None
