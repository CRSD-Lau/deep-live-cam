from types import SimpleNamespace

import numpy as np

import modules.face_analyser as face_analyser


def test_analyse_faces_strips_alpha_channel_before_detection(monkeypatch):
    captured = {}

    def detect(frame, **_kwargs):
        captured["shape"] = frame.shape
        return np.zeros((0, 5), dtype=np.float32), None

    monkeypatch.setattr(
        face_analyser,
        "get_face_analyser",
        lambda: SimpleNamespace(det_model=SimpleNamespace(detect=detect)),
    )

    bgra_frame = np.zeros((12, 16, 4), dtype=np.uint8)

    assert face_analyser._analyse_faces(bgra_frame) == []
    assert captured["shape"] == (12, 16, 3)

