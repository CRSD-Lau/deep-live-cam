from types import SimpleNamespace

import numpy as np

from modules.processors.frame import face_swapper


def test_swap_face_strips_alpha_channel_before_model_inference(monkeypatch):
    captured = {}

    class FakeSwapper:
        input_size = (4, 4)

        def get(self, frame, *_args, **_kwargs):
            captured["shape"] = frame.shape
            return np.zeros((4, 4, 3), dtype=np.uint8), np.eye(2, 3, dtype=np.float32)

    monkeypatch.setattr(face_swapper, "get_face_swapper", lambda: FakeSwapper())
    monkeypatch.setattr(
        face_swapper,
        "_fast_paste_back",
        lambda target_img, *_args, **_kwargs: target_img,
    )
    monkeypatch.setattr(face_swapper.modules.globals, "opacity", 1.0)
    monkeypatch.setattr(face_swapper.modules.globals, "mouth_mask", False)
    monkeypatch.setattr(face_swapper.modules.globals, "poisson_blend", False)
    monkeypatch.setattr(face_swapper.modules.globals, "execution_providers", [])

    source_face = SimpleNamespace(normed_embedding=np.ones(4, dtype=np.float32))
    target_face = SimpleNamespace()
    bgra_frame = np.zeros((12, 16, 4), dtype=np.uint8)

    result = face_swapper.swap_face(source_face, target_face, bgra_frame)

    assert captured["shape"] == (12, 16, 3)
    assert result.shape == (12, 16, 3)

