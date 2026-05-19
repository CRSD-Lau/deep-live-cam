from __future__ import annotations

import inspect
from typing import Any, Callable


def process_frame_with_target(
    processor: Any,
    source_face: Any,
    frame: Any,
    target_face: Any | None,
) -> Any:
    process_frame = processor.process_frame
    if target_face is not None and _accepts_keyword(
        process_frame, "detected_faces"
    ):
        return process_frame(source_face, frame, detected_faces=[target_face])
    if _accepts_keyword(process_frame, "target_face"):
        return process_frame(source_face, frame, target_face=target_face)
    return process_frame(source_face, frame)


def _accepts_keyword(func: Callable[..., Any], keyword: str) -> bool:
    try:
        parameters = inspect.signature(func).parameters.values()
    except (TypeError, ValueError):
        return False
    return any(
        parameter.name == keyword
        or parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )
