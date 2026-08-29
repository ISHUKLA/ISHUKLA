"""Render an understated actuarial signature panel for Shukla A."""

from __future__ import annotations

import argparse
import html
import math
from pathlib import Path
from typing import Sequence


DEFAULT_LINES: tuple[tuple[str, str], ...] = (
    ("building", "AI tooling for insurers"),
    ("interest", "judgement-led strategy"),
    ("focus", "savings + retirement"),
)

DEFAULT_TRAJECTORY: tuple[float, ...] = (
    0.08,
    0.12,
    0.17,
    0.23,
    0.30,
    0.38,
    0.47,
    0.57,
    0.68,
    0.79,
    0.90,
    1.00,
)


class PersonalSignalError(ValueError):
    """Raised when signature-panel content cannot be rendered safely."""


def _validate_lines(lines: Sequence[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    if not 3 <= len(lines) <= 5:
        raise PersonalSignalError("the signature needs between three and five lines")
    output: list[tuple[str, str]] = []
    for line in lines:
        if len(line) != 2:
            raise PersonalSignalError("each signature line needs a label and value")
        label, value = (part.strip() for part in line)
        if not label or not value:
            raise PersonalSignalError("signature labels and values must not be blank")
        if len(label) > 12 or len(value) > 38:
            raise PersonalSignalError("signature text is too long for the layout")
        output.append((label, value))
    return tuple(output)


def _validate_trajectory(trajectory: Sequence[float]) -> tuple[float, ...]:
    if not 8 <= len(trajectory) <= 24:
        raise PersonalSignalError("trajectory needs between 8 and 24 points")
    try:
        values = tuple(float(value) for value in trajectory)
    except (TypeError, ValueError) as exc:
        raise PersonalSignalError("trajectory values must be numeric") from exc
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise PersonalSignalError("trajectory values must be finite and between 0 and 1")
    if any(right < left for left, right in zip(values, values[1:])):
        raise PersonalSignalError("trajectory values must be non-decreasing")
    if values[0] == values[-1]:
        raise PersonalSignalError("trajectory must show a change over time")
    return values


def render_personal_signal(
    destination: Path,
    *,
    lines: Sequence[tuple[str, str]] = DEFAULT_LINES,
    trajectory: Sequence[float] = DEFAULT_TRAJECTORY,
    animated: bool = True,
) -> None:
    story = _validate_lines(lines)
    values = _validate_trajectory(trajectory)
    static = " static" if not animated else ""

    start_x, end_x = 65.0, 405.0
    baseline_y, height = 241.0, 142.0
    step = (end_x - start_x) / (len(values) - 1)
    points = [
        (start_x + index * step, baseline_y - value * height)
        for index, value in enumerate(values)
    ]
    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)
    area = f"{path} L {points[-1][0]:.1f} {baseline_y:.1f} L {points[0][0]:.1f} {baseline_y:.1f} Z"

    rendered_points = "".join(
        f'<circle class="point{static}" cx="{x:.1f}" cy="{y:.1f}" r="3" '
        f'style="animation-delay:{1.15 + index * 0.07:.2f}s"/>'
        for index, (x, y) in enumerate(points)
        if index in {0, len(points) - 1} or index % 3 == 0
    )

    rendered_lines = "".join(
        f'<g class="story{static}" style="animation-delay:{0.65 + index * 0.16:.2f}s">'
        f'<text x="500" y="{184 + index * 34}" class="label">{html.escape(label.upper())}</text>'
        f'<text x="612" y="{184 + index * 34}" class="value">{html.escape(value)}</text>'
        "</g>"
        for index, (label, value) in enumerate(story)
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300" role="img" aria-labelledby="title desc">
  <title id="title">Shukla A. — Actuary, Builder, Analyst</title>
  <desc id="desc">Shukla A. is a French actuary by training, builder, and analyst. An elegant actuarial projection accompanies his focus on judgement-led insurance strategy, savings, retirement, and AI tooling for insurers.</desc>
  <defs>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#111c2c"/>
      <stop offset="1" stop-color="#09111d"/>
    </linearGradient>
    <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c9a96e" stop-opacity=".22"/>
      <stop offset="1" stop-color="#c9a96e" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .eyebrow {{ fill: #c9a96e; font-size: 10px; font-weight: 650; letter-spacing: 2.4px; }}
    .name {{ fill: #f1f3f5; font-family: Georgia, "Times New Roman", serif; font-size: 35px; letter-spacing: .4px; }}
    .role {{ fill: #d7dde5; font-family: Georgia, "Times New Roman", serif; font-size: 23px; }}
    .subtle {{ fill: #8390a3; font-size: 11px; letter-spacing: .5px; }}
    .label {{ fill: #c9a96e; font-size: 9px; font-weight: 700; letter-spacing: 1.5px; }}
    .value {{ fill: #d7dde5; font-size: 14px; }}
    .trace {{ fill: none; stroke: #d7b574; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; path-length: 1; stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 2.1s .25s cubic-bezier(.2,.75,.2,1) forwards; }}
    .area {{ opacity: 0; animation: reveal .9s 1.1s ease-out forwards; }}
    .point {{ fill: #d7b574; stroke: #111c2c; stroke-width: 2; opacity: 0; animation: reveal .3s ease-out forwards; }}
    .story {{ opacity: 0; transform: translateY(4px); animation: settle .55s ease-out forwards; }}
    .rule {{ stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw 1.2s .15s ease-out forwards; }}
    .static {{ opacity: 1 !important; transform: none !important; stroke-dashoffset: 0 !important; animation: none !important; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes reveal {{ to {{ opacity: 1; }} }}
    @keyframes settle {{ to {{ opacity: 1; transform: none; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .trace, .area, .point, .story, .rule {{ opacity: 1; transform: none; stroke-dashoffset: 0; animation: none; }}
    }}
  </style>

  <rect x="1" y="1" width="898" height="298" rx="10" fill="url(#panel)" stroke="#26354a" stroke-width="2"/>
  <path class="rule{static}" pathLength="1" d="M28 24 H872" stroke="#c9a96e" stroke-width="1" opacity=".55"/>

  <g aria-label="Actuarial long-term projection">
    <text x="65" y="57" class="eyebrow">LONG-TERM VIEW</text>
    <text x="405" y="57" text-anchor="end" class="subtle">SAVINGS · RETIREMENT</text>
    <path d="M65 87 H405 M65 138 H405 M65 190 H405 M65 241 H405" stroke="#314056" stroke-width="1" opacity=".68"/>
    <path d="M65 87 V241 M178 87 V241 M291 87 V241 M405 87 V241" stroke="#26354a" stroke-width="1" opacity=".7"/>
    <path class="area{static}" d="{area}" fill="url(#area)"/>
    <path class="trace{static}" pathLength="1" d="{path}"/>
    {rendered_points}
    <text x="65" y="267" class="subtle">TODAY</text>
    <text x="405" y="267" text-anchor="end" class="subtle">HORIZON</text>
    <text x="235" y="286" text-anchor="middle" class="subtle">projection · evidence · human judgement</text>
  </g>

  <path d="M455 50 V264" stroke="#26354a" stroke-width="1"/>
  <g aria-label="French tricolour" transform="translate(500 49)">
    <rect width="26" height="3" rx="1.5" fill="#315fa4"/>
    <rect x="26" width="26" height="3" fill="#e8ebef"/>
    <rect x="52" width="26" height="3" rx="1.5" fill="#a84f58"/>
  </g>
  <text x="500" y="94" class="name">Shukla A.</text>
  <text x="500" y="127" class="role">Actuary · Builder · Analyst</text>
  <text x="500" y="150" class="subtle">FRENCH ACTUARY BY TRAINING</text>
  <path d="M500 163 H846" stroke="#314056" stroke-width="1"/>
  {rendered_lines}
</svg>
'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("assets/personal-signal.svg"))
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    render_personal_signal(args.output, animated=not args.static)


if __name__ == "__main__":
    main()
