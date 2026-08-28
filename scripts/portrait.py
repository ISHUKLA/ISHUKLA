"""Convert a source photograph into a one-shot animated ASCII portrait SVG."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError


ASCII_RAMP = "@%#*+=-:. "
DEFAULT_CROP = (0.28, 0.13, 0.91, 0.68)


class PortraitError(ValueError):
    """Raised when a portrait cannot be generated safely."""


def _validated_crop(image: Image.Image, crop: tuple[float, float, float, float]) -> Image.Image:
    if len(crop) != 4 or any(not 0 <= value <= 1 for value in crop):
        raise PortraitError("crop must contain four normalized values between 0 and 1")
    left, top, right, bottom = crop
    if left >= right or top >= bottom:
        raise PortraitError("crop must have positive width and height")
    box = (
        round(left * image.width),
        round(top * image.height),
        round(right * image.width),
        round(bottom * image.height),
    )
    return image.crop(box)


def _suppress_background(image: Image.Image) -> Image.Image:
    """Suppress the bright sky and green foliage while preserving the subject."""

    rgb = image.convert("RGB")
    cleaned: list[tuple[int, int, int]] = []
    for red, green, blue in rgb.get_flattened_data():
        bright_sky = red > 242 and green > 242 and blue > 242
        green_foliage = green > 72 and green > red * 1.08 and green > blue * 1.08
        cleaned.append((255, 255, 255) if bright_sky or green_foliage else (red, green, blue))
    rgb.putdata(cleaned)
    return rgb


def image_to_ascii(
    source: Path,
    *,
    columns: int = 66,
    crop: tuple[float, float, float, float] = DEFAULT_CROP,
) -> list[str]:
    if columns < 24 or columns > 120:
        raise PortraitError("columns must be between 24 and 120")
    if not source.is_file():
        raise PortraitError(f"source photograph does not exist: {source}")

    try:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise PortraitError(f"source is not a readable image: {source}") from exc

    if image.width < 200 or image.height < 200:
        raise PortraitError("source photograph is too small; use at least 200 x 200 pixels")

    focused = _validated_crop(image, crop)
    focused = _suppress_background(focused)
    grayscale = ImageOps.grayscale(focused)
    grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
    grayscale = ImageEnhance.Contrast(grayscale).enhance(1.38)
    grayscale = ImageEnhance.Sharpness(grayscale).enhance(1.2)

    # Monospace characters are roughly 0.55 times as wide as they are tall.
    rows = max(1, round((focused.height / focused.width) * columns * 0.55))
    sample = grayscale.resize((columns, rows), Image.Resampling.LANCZOS)

    lines: list[str] = []
    for row in range(rows):
        characters: list[str] = []
        for column in range(columns):
            brightness = sample.getpixel((column, row))
            if brightness >= 244:
                characters.append(" ")
                continue
            index = min(len(ASCII_RAMP) - 1, int(brightness / 256 * len(ASCII_RAMP)))
            characters.append(ASCII_RAMP[index])
        lines.append("".join(characters).rstrip())

    if not any(line.strip() for line in lines):
        raise PortraitError("portrait preprocessing removed all visible detail")
    return lines


def render_svg(lines: list[str], destination: Path, *, animated: bool = True) -> None:
    if not lines or not any(line.strip() for line in lines):
        raise PortraitError("at least one non-empty ASCII row is required")

    width, height = 390, 500
    top = 47
    columns = max(len(line) for line in lines)
    font_size = min((width - 24) / (columns * 0.60), (height - top - 12) / len(lines))
    line_height = font_size
    animation = "" if animated else " static"

    rows: list[str] = []
    for index, line in enumerate(lines):
        y = top + (index + 1) * line_height
        delay = index * 0.035
        rows.append(
            f'<text class="ascii-row{animation}" x="12" y="{y:.2f}" '
            f'style="animation-delay:{delay:.3f}s">{html.escape(line)}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">ASCII portrait of Shukla A.</title>
  <desc id="desc">A monochrome terminal-style portrait that types itself once, row by row.</desc>
  <style>
    .ascii-row {{
      fill: #c9d1d9;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: {font_size:.2f}px;
      white-space: pre;
      opacity: 0;
      clip-path: inset(0 100% 0 0);
      animation: type-row .42s cubic-bezier(.2,.8,.2,1) forwards;
    }}
    .ascii-row.static {{ opacity: 1; clip-path: none; animation: none; }}
    @keyframes type-row {{
      1% {{ opacity: 1; }}
      100% {{ opacity: 1; clip-path: inset(0 0 0 0); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .ascii-row {{ opacity: 1; clip-path: none; animation: none; }}
    }}
  </style>
  <rect x="1" y="1" width="388" height="498" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <circle cx="20" cy="21" r="5" fill="#ff5f56"/>
  <circle cx="38" cy="21" r="5" fill="#ffbd2e"/>
  <circle cx="56" cy="21" r="5" fill="#27c93f"/>
  <text x="195" y="25" text-anchor="middle" fill="#8b949e" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="11">portrait.sh</text>
  {''.join(rows)}
</svg>
'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="source photograph")
    parser.add_argument("--output", type=Path, default=Path("assets/portrait.svg"))
    parser.add_argument("--columns", type=int, default=66)
    parser.add_argument("--static", action="store_true", help="render the final frame without animation")
    args = parser.parse_args()
    render_svg(
        image_to_ascii(args.source, columns=args.columns),
        args.output,
        animated=not args.static,
    )


if __name__ == "__main__":
    main()
