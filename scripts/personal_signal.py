"""Render a playful animated profile hero for Shukla A."""

from __future__ import annotations

import argparse
import html
import math
from pathlib import Path
from typing import Sequence


DEFAULT_LINES: tuple[tuple[str, str], ...] = (
    ("hello", "French actuary by training"),
    ("mode", "build + analyse"),
    ("now", "AI tooling for insurers"),
    ("play", "FIP ↔ Claude FM"),
)

DEFAULT_WAVEFORM: tuple[float, ...] = (
    0.28, 0.52, 0.74, 0.43, 0.88, 0.62, 0.34, 0.67,
    0.91, 0.48, 0.72, 0.39, 0.81, 0.58, 0.96, 0.51,
    0.69, 0.36, 0.79, 0.57, 0.86, 0.45, 0.65, 0.93,
    0.54, 0.76, 0.41, 0.84, 0.61, 0.33, 0.71, 0.49,
)


class PersonalSignalError(ValueError):
    """Raised when personal hero content cannot be rendered safely."""


def _validate_lines(lines: Sequence[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    if not 3 <= len(lines) <= 6:
        raise PersonalSignalError("the hero needs between three and six story lines")
    output: list[tuple[str, str]] = []
    for line in lines:
        if len(line) != 2:
            raise PersonalSignalError("each story line needs a label and value")
        label, value = (part.strip() for part in line)
        if not label or not value:
            raise PersonalSignalError("story labels and values must not be blank")
        if len(label) > 10 or len(value) > 42:
            raise PersonalSignalError("story text is too long for the hero layout")
        output.append((label, value))
    return tuple(output)


def _validate_waveform(waveform: Sequence[float]) -> tuple[float, ...]:
    if not 16 <= len(waveform) <= 48:
        raise PersonalSignalError("waveform needs between 16 and 48 bars")
    try:
        values = tuple(float(value) for value in waveform)
    except (TypeError, ValueError) as exc:
        raise PersonalSignalError("waveform values must be numeric") from exc
    if any(not math.isfinite(value) or not 0.15 <= value <= 1 for value in values):
        raise PersonalSignalError("waveform values must be finite and between 0.15 and 1")
    return values


def render_personal_signal(
    destination: Path,
    *,
    lines: Sequence[tuple[str, str]] = DEFAULT_LINES,
    waveform: Sequence[float] = DEFAULT_WAVEFORM,
    animated: bool = True,
) -> None:
    story = _validate_lines(lines)
    bars = _validate_waveform(waveform)
    static = " static" if not animated else ""

    rendered_lines: list[str] = []
    for index, (label, value) in enumerate(story):
        y = 102 + index * 42
        delay = 0.75 + index * 0.28
        rendered_lines.append(
            f'<g class="story-line{static}" style="animation-delay:{delay:.2f}s">'
            f'<text x="430" y="{y}" class="line-label">{html.escape(label)}</text>'
            f'<text x="505" y="{y}" class="line-value">{html.escape(value)}</text>'
            "</g>"
        )

    rendered_bars: list[str] = []
    bar_width = 8
    gap = 5
    total_width = len(bars) * bar_width + (len(bars) - 1) * gap
    start_x = 430 + (420 - total_width) / 2
    palette = ("#58a6ff", "#ff7ab2", "#7ee787", "#d29922")
    for index, amplitude in enumerate(bars):
        bar_height = 6 + amplitude * 24
        x = start_x + index * (bar_width + gap)
        delay = -(index % 9) * 0.11
        rendered_bars.append(
            f'<rect class="eq-bar{static}" x="{x:.2f}" y="{306 - bar_height:.2f}" '
            f'width="{bar_width}" height="{bar_height:.2f}" rx="4" '
            f'fill="{palette[index % len(palette)]}" style="animation-delay:{delay:.2f}s"/>'
        )

    badges = (
        (82, 76, "Σ", "#58a6ff", "0s"),
        (356, 84, "{ }", "#ff7ab2", "-.8s"),
        (76, 235, "♫", "#d29922", "-1.6s"),
        (362, 225, "AI", "#7ee787", "-2.4s"),
    )
    rendered_badges = "".join(
        f'<g transform="translate({x} {y})"><g class="badge{static}" style="animation-delay:{delay}">'
        f'<circle r="23" fill="#161b22" stroke="{colour}" stroke-width="1.5"/>'
        f'<text text-anchor="middle" y="5" fill="{colour}">{html.escape(symbol)}</text>'
        "</g></g>"
        for x, y, symbol, colour, delay in badges
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="330" viewBox="0 0 900 330" role="img" aria-labelledby="title desc">
  <title id="title">Meet Shukla A.</title>
  <desc id="desc">Playful round glasses frame the initials S and A while actuarial, coding, AI, and music symbols float nearby. A terminal introduces a French actuary who likes to build, analyse, and listen to FIP and Claude FM.</desc>
  <defs>
    <radialGradient id="lens-blue" cx="35%" cy="30%">
      <stop offset="0" stop-color="#58a6ff" stop-opacity="0.24"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="0.4"/>
    </radialGradient>
    <radialGradient id="lens-pink" cx="35%" cy="30%">
      <stop offset="0" stop-color="#ff7ab2" stop-opacity="0.22"/>
      <stop offset="1" stop-color="#0d1117" stop-opacity="0.4"/>
    </radialGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#ffffff" stop-opacity="0.34"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .subtle {{ fill: #8b949e; font-size: 11px; }}
    .glasses {{ opacity: 0; transform-origin: 220px 155px; animation: glasses-in .85s cubic-bezier(.17,.9,.28,1.25) forwards; }}
    .initial {{ fill: #f0f6fc; font-size: 48px; font-weight: 700; }}
    .badge {{ animation: float 3.6s ease-in-out infinite; }}
    .badge text {{ font-size: 14px; font-weight: 700; }}
    .story-line {{ opacity: 0; clip-path: inset(0 100% 0 0); animation: type-line .72s cubic-bezier(.2,.8,.2,1) forwards; }}
    .line-label {{ fill: #ff7ab2; font-size: 12px; font-weight: 700; }}
    .line-value {{ fill: #c9d1d9; font-size: 15px; }}
    .cursor {{ animation: blink .9s steps(1) infinite; }}
    .eq-bar {{ transform-box: fill-box; transform-origin: center bottom; animation: beat 1.15s ease-in-out infinite alternate; }}
    .shine {{ opacity: 0; animation: lens-shine 1.1s .6s ease-in-out forwards; }}
    .static {{ opacity: 1 !important; transform: none !important; clip-path: none !important; animation: none !important; }}
    @keyframes glasses-in {{ 0% {{ opacity: 0; transform: translateY(18px) rotate(-6deg) scale(.88); }} 100% {{ opacity: 1; transform: none; }} }}
    @keyframes float {{ 0%,100% {{ transform: translateY(0) rotate(-3deg); }} 50% {{ transform: translateY(-8px) rotate(3deg); }} }}
    @keyframes type-line {{ 1% {{ opacity: 1; }} 100% {{ opacity: 1; clip-path: inset(0 0 0 0); }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @keyframes beat {{ 0% {{ transform: scaleY(.35); opacity: .55; }} 100% {{ transform: scaleY(1); opacity: 1; }} }}
    @keyframes lens-shine {{ 0% {{ opacity: 0; transform: translateX(-70px); }} 35% {{ opacity: .7; }} 100% {{ opacity: 0; transform: translateX(115px); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .glasses, .badge, .story-line, .cursor, .eq-bar, .shine {{ opacity: 1; transform: none; clip-path: none; animation: none; }}
      .shine {{ display: none; }}
    }}
  </style>
  <rect x="1" y="1" width="898" height="328" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <circle cx="20" cy="21" r="5" fill="#ff5f56"/>
  <circle cx="38" cy="21" r="5" fill="#ffbd2e"/>
  <circle cx="56" cy="21" r="5" fill="#27c93f"/>
  <text x="450" y="25" text-anchor="middle" class="subtle">shukla@github: ~ /about_me --play</text>

  {rendered_badges}
  <g class="glasses{static}">
    <path d="M 85 140 Q 62 128 48 134" fill="none" stroke="#8b949e" stroke-width="5" stroke-linecap="round"/>
    <path d="M 355 140 Q 378 128 392 134" fill="none" stroke="#8b949e" stroke-width="5" stroke-linecap="round"/>
    <circle cx="150" cy="155" r="66" fill="url(#lens-blue)" stroke="#58a6ff" stroke-width="5"/>
    <circle cx="290" cy="155" r="66" fill="url(#lens-pink)" stroke="#ff7ab2" stroke-width="5"/>
    <path d="M 216 151 Q 220 140 224 151" fill="none" stroke="#c9d1d9" stroke-width="5" stroke-linecap="round"/>
    <text x="150" y="172" text-anchor="middle" class="initial">S</text>
    <text x="290" y="172" text-anchor="middle" class="initial">A</text>
    <path class="shine{static}" d="M 104 116 L 137 92 L 192 192 L 165 211 Z" fill="url(#shine)"/>
    <path class="shine{static}" d="M 244 116 L 277 92 L 332 192 L 305 211 Z" fill="url(#shine)"/>
  </g>
  <g aria-label="French tricolour">
    <rect x="184" y="238" width="24" height="6" rx="3" fill="#0055a4"/>
    <rect x="208" y="238" width="24" height="6" fill="#f0f6fc"/>
    <rect x="232" y="238" width="24" height="6" rx="3" fill="#ef4135"/>
  </g>
  <text x="220" y="265" text-anchor="middle" class="subtle">FRENCH ACTUARY · BUILDER · ANALYST</text>
  <text x="430" y="61" fill="#7ee787" font-size="15">$ ./about_me --play<tspan class="cursor{static}">_</tspan></text>
  {''.join(rendered_lines)}
  <rect x="505" y="252" width="92" height="24" rx="12" fill="#161b22" stroke="#58a6ff"/>
  <text x="551" y="268" text-anchor="middle" fill="#58a6ff" font-size="10">savings</text>
  <rect x="607" y="252" width="104" height="24" rx="12" fill="#161b22" stroke="#ff7ab2"/>
  <text x="659" y="268" text-anchor="middle" fill="#ff7ab2" font-size="10">retirement</text>
  <text x="850" y="268" text-anchor="end" class="subtle">soundtrack_to_build</text>
  {''.join(rendered_bars)}
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
