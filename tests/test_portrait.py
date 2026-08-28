from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from scripts.portrait import PortraitError, image_to_ascii, render_svg


def test_portrait_clean_image_generates_accessible_svg(tmp_path: Path) -> None:
    source = tmp_path / "portrait.png"
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((105, 65, 295, 315), fill=(90, 65, 50))
    draw.ellipse((145, 145, 175, 175), fill="black")
    draw.ellipse((225, 145, 255, 175), fill="black")
    image.save(source)

    lines = image_to_ascii(source, columns=40, crop=(0, 0, 1, 1))
    output = tmp_path / "portrait.svg"
    render_svg(lines, output)

    svg = output.read_text(encoding="utf-8")
    assert "ASCII portrait of Shukla A." in svg
    assert "prefers-reduced-motion" in svg
    assert "@keyframes type-row" in svg
    assert any(line.strip() for line in lines)


def test_portrait_rejects_malformed_source(tmp_path: Path) -> None:
    source = tmp_path / "not-an-image.jpeg"
    source.write_text("not image bytes", encoding="utf-8")

    with pytest.raises(PortraitError, match="not a readable image"):
        image_to_ascii(source)


def test_portrait_rejects_inverted_crop(tmp_path: Path) -> None:
    source = tmp_path / "portrait.png"
    Image.new("RGB", (300, 300), "gray").save(source)

    with pytest.raises(PortraitError, match="positive width"):
        image_to_ascii(source, crop=(0.8, 0.2, 0.1, 0.9))
