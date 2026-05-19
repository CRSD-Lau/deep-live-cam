#!/usr/bin/env python3
"""Generate Windows installer/app logo assets from the root Logo.png."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
WIZARD_SIZE = (164, 314)
WIZARD_SMALL_SIZE = (55, 55)


def contain_rgba(image: Image.Image, size: tuple[int, int], padding: int = 0) -> Image.Image:
    target = (max(1, size[0] - padding * 2), max(1, size[1] - padding * 2))
    fitted = ImageOps.contain(image.convert("RGBA"), target, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", size, (255, 255, 255, 0))
    offset = ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2)
    canvas.alpha_composite(fitted, offset)
    return canvas


def flatten_for_bmp(image: Image.Image, background: tuple[int, int, int] = (24, 24, 24)) -> Image.Image:
    canvas = Image.new("RGB", image.size, background)
    alpha = image.getchannel("A") if image.mode == "RGBA" else None
    canvas.paste(image.convert("RGB"), mask=alpha)
    return canvas


def generate(source: Path, output_dir: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Logo source not found: {source}")

    output_dir.mkdir(parents=True, exist_ok=True)
    logo = Image.open(source).convert("RGBA")

    ico_path = output_dir / "Logo.ico"
    ico_images = [contain_rgba(logo, (size, size)) for size in ICO_SIZES]
    ico_images[-1].save(ico_path, sizes=[(size, size) for size in ICO_SIZES], append_images=ico_images[:-1])

    wizard = flatten_for_bmp(contain_rgba(logo, WIZARD_SIZE, padding=18))
    wizard.save(output_dir / "WizardImage.bmp")

    wizard_small = flatten_for_bmp(contain_rgba(logo, WIZARD_SMALL_SIZE, padding=4))
    wizard_small.save(output_dir / "WizardSmallImage.bmp")

    print(f"Generated Windows logo assets in: {output_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="Logo.png", help="Source logo PNG.")
    parser.add_argument("--output-dir", default="build/windows/assets", help="Output asset directory.")
    args = parser.parse_args()

    generate(Path(args.source), Path(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
