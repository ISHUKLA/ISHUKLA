"""Render an animated actuarial savings-and-retirement scenario signal."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Mapping, Sequence


DEFAULT_SCENARIOS: dict[str, tuple[float, ...]] = {
    "downside": (100, 106, 113, 122, 132, 143, 155),
    "central": (100, 112, 127, 145, 166, 190, 218),
    "upside": (100, 118, 140, 168, 202, 244, 296),
}

COLOURS = {
    "downside": "#d29922",
    "central": "#58a6ff",
    "upside": "#7ee787",
}


class ActuarialSignalError(ValueError):
    """Raised when scenario data cannot be rendered without being misleading."""


def _validated_scenarios(
    scenarios: Mapping[str, Sequence[float]],
) -> dict[str, tuple[float, ...]]:
    required = {"downside", "central", "upside"}
    if set(scenarios) != required:
        raise ActuarialSignalError("scenarios must contain downside, central, and upside")

    output: dict[str, tuple[float, ...]] = {}
    lengths: set[int] = set()
    for name in ("downside", "central", "upside"):
        try:
            values = tuple(float(value) for value in scenarios[name])
        except (TypeError, ValueError) as exc:
            raise ActuarialSignalError(f"{name} contains a non-numeric value") from exc
        if len(values) < 3:
            raise ActuarialSignalError("each scenario needs at least three projection points")
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ActuarialSignalError(f"{name} contains a non-positive or non-finite value")
        if any(later < earlier for earlier, later in zip(values, values[1:])):
            raise ActuarialSignalError(f"{name} must be non-decreasing")
        output[name] = values
        lengths.add(len(values))

    if len(lengths) != 1:
        raise ActuarialSignalError("all scenarios must have the same number of points")
    for index, ordered in enumerate(
        zip(output["downside"], output["central"], output["upside"])
    ):
        if not ordered[0] <= ordered[1] <= ordered[2]:
            raise ActuarialSignalError(f"scenario ordering crosses at point {index}")
    return output


def _smooth_path(points: Sequence[tuple[float, float]]) -> str:
    """Convert points to a smooth Catmull-Rom-derived cubic path."""

    commands = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for index in range(len(points) - 1):
        previous = points[index - 1] if index > 0 else points[index]
        current = points[index]
        following = points[index + 1]
        after = points[index + 2] if index + 2 < len(points) else following
        control_1 = (
            current[0] + (following[0] - previous[0]) / 6,
            current[1] + (following[1] - previous[1]) / 6,
        )
        control_2 = (
            following[0] - (after[0] - current[0]) / 6,
            following[1] - (after[1] - current[1]) / 6,
        )
        commands.append(
            "C "
            f"{control_1[0]:.2f} {control_1[1]:.2f}, "
            f"{control_2[0]:.2f} {control_2[1]:.2f}, "
            f"{following[0]:.2f} {following[1]:.2f}"
        )
    return " ".join(commands)


def render_actuarial_signal(
    destination: Path,
    *,
    scenarios: Mapping[str, Sequence[float]] = DEFAULT_SCENARIOS,
    animated: bool = True,
) -> None:
    values = _validated_scenarios(scenarios)
    point_count = len(values["central"])

    width, height = 900, 320
    x_start, x_end = 64.0, 800.0
    y_top, y_bottom = 64.0, 188.0
    flat_values = [value for series in values.values() for value in series]
    minimum = min(flat_values) * 0.94
    maximum = max(flat_values) * 1.04

    def x_at(index: int) -> float:
        return x_start + index * (x_end - x_start) / (point_count - 1)

    def y_at(value: float) -> float:
        share = (value - minimum) / (maximum - minimum)
        return y_bottom - share * (y_bottom - y_top)

    points = {
        name: tuple((x_at(index), y_at(value)) for index, value in enumerate(series))
        for name, series in values.items()
    }

    upper = " ".join(f"{x:.2f},{y:.2f}" for x, y in points["upside"])
    lower = " ".join(f"{x:.2f},{y:.2f}" for x, y in reversed(points["downside"]))
    static_class = " static" if not animated else ""

    paths: list[str] = []
    labels: list[str] = []
    delays = {"downside": 0.90, "central": 0.65, "upside": 1.15}
    label_offsets = {"downside": 5, "central": 4, "upside": -4}
    for name in ("downside", "central", "upside"):
        end_x, end_y = points[name][-1]
        paths.append(
            f'<path class="projection {name}{static_class}" '
            f'style="animation-delay:{delays[name]:.2f}s" '
            f'd="{_smooth_path(points[name])}"/>'
        )
        labels.append(
            f'<g class="end-label{static_class}" style="animation-delay:{delays[name] + 1.8:.2f}s">'
            f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="4" fill="{COLOURS[name]}"/>'
            f'<text x="{end_x + 12:.2f}" y="{end_y + label_offsets[name]:.2f}" '
            f'fill="{COLOURS[name]}">{name.title()}</text></g>'
        )

    axis_labels = []
    for index in range(point_count):
        if index in {0, (point_count - 1) // 3, 2 * (point_count - 1) // 3, point_count - 1}:
            year = round(index * 30 / (point_count - 1))
            axis_labels.append(
                f'<text x="{x_at(index):.2f}" y="207" text-anchor="middle" class="axis-label">Year {year}</text>'
            )

    flow = (
        ("Data", 32),
        ("Assumptions", 243),
        ("Scenarios", 454),
        ("Judgement", 665),
    )
    nodes: list[str] = []
    arrows: list[str] = []
    for index, (label, x) in enumerate(flow):
        delay = 3.0 + index * 0.35
        final = " judgement-node" if label == "Judgement" else ""
        nodes.append(
            f'<g class="flow-node{final}{static_class}" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x}" y="244" width="170" height="42" rx="10"/>'
            f'<text x="{x + 85}" y="270" text-anchor="middle">{label}</text></g>'
        )
        if index < len(flow) - 1:
            next_x = flow[index + 1][1]
            arrows.append(
                f'<path class="flow-arrow{static_class}" style="animation-delay:{delay + 0.20:.2f}s" '
                f'd="M {x + 176} 265 L {next_x - 8} 265"/>'
            )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Animated actuarial scenario signal</title>
  <desc id="desc">Illustrative savings and retirement projections reveal downside, central, and upside paths, followed by data, assumptions, scenarios, and human judgement.</desc>
  <defs>
    <linearGradient id="fan" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#d29922" stop-opacity="0.08"/>
      <stop offset="0.5" stop-color="#58a6ff" stop-opacity="0.11"/>
      <stop offset="1" stop-color="#7ee787" stop-opacity="0.14"/>
    </linearGradient>
    <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7ee787" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#7ee787" stop-opacity="0.75"/>
      <stop offset="1" stop-color="#7ee787" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .title {{ fill: #c9d1d9; font-size: 13px; font-weight: 600; }}
    .subtle, .axis-label {{ fill: #8b949e; font-size: 10px; }}
    .grid {{ stroke: #21262d; stroke-width: 1; }}
    .fan {{ opacity: 0; animation: fade-in .8s .35s ease-out forwards; }}
    .projection {{
      fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;
      stroke-dasharray: 1200; stroke-dashoffset: 1200;
      animation: draw-path 2.1s cubic-bezier(.2,.75,.25,1) forwards;
    }}
    .projection.downside {{ stroke: {COLOURS['downside']}; }}
    .projection.central {{ stroke: {COLOURS['central']}; stroke-width: 3.6; }}
    .projection.upside {{ stroke: {COLOURS['upside']}; }}
    .end-label {{ opacity: 0; animation: fade-in .35s ease-out forwards; font-size: 10px; }}
    .scan {{ opacity: 0; animation: scan 2.8s .45s ease-in-out forwards; }}
    .flow-node {{ opacity: 0; transform: translateY(8px); animation: node-in .35s ease-out forwards; }}
    .flow-node rect {{ fill: #161b22; stroke: #30363d; stroke-width: 1.5; }}
    .flow-node text {{ fill: #c9d1d9; font-size: 12px; }}
    .judgement-node rect {{ fill: #10251a; stroke: #7ee787; }}
    .judgement-node text {{ fill: #7ee787; font-weight: 600; }}
    .judgement-node {{ animation-name: node-in, judgement-pulse; animation-duration: .35s, 1.1s; animation-iteration-count: 1, 2; animation-fill-mode: forwards, none; }}
    .flow-arrow {{ fill: none; stroke: #484f58; stroke-width: 1.5; stroke-dasharray: 46; stroke-dashoffset: 46; animation: arrow-in .35s linear forwards; }}
    .static {{ opacity: 1; transform: none; animation: none; stroke-dashoffset: 0; }}
    @keyframes fade-in {{ to {{ opacity: 1; }} }}
    @keyframes draw-path {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes scan {{ 0% {{ opacity: 0; transform: translateX(0); }} 12% {{ opacity: 1; }} 88% {{ opacity: .7; }} 100% {{ opacity: 0; transform: translateX(736px); }} }}
    @keyframes node-in {{ to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes arrow-in {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes judgement-pulse {{ 50% {{ filter: drop-shadow(0 0 5px #7ee787); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .fan, .projection, .end-label, .flow-node, .flow-arrow {{ opacity: 1; transform: none; animation: none; stroke-dashoffset: 0; }}
      .scan {{ display: none; }}
    }}
  </style>
  <rect x="1" y="1" width="898" height="318" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <circle cx="20" cy="21" r="5" fill="#ff5f56"/>
  <circle cx="38" cy="21" r="5" fill="#ffbd2e"/>
  <circle cx="56" cy="21" r="5" fill="#27c93f"/>
  <text x="450" y="25" text-anchor="middle" class="subtle">scenario_engine · savings &amp; retirement</text>
  <text x="32" y="51" class="title">Illustrative projection fan</text>
  <text x="868" y="51" text-anchor="end" class="subtle">EPV = Σ CFₜ × pₜ × vᵗ · not model output</text>
  <line x1="{x_start}" y1="95" x2="{x_end}" y2="95" class="grid"/>
  <line x1="{x_start}" y1="137" x2="{x_end}" y2="137" class="grid"/>
  <line x1="{x_start}" y1="{y_bottom}" x2="{x_end}" y2="{y_bottom}" class="grid"/>
  <polygon class="fan{static_class}" points="{upper} {lower}" fill="url(#fan)"/>
  {''.join(paths)}
  <line class="scan{static_class}" x1="{x_start}" y1="58" x2="{x_start}" y2="190" stroke="url(#sweep)" stroke-width="2"/>
  {''.join(labels)}
  {''.join(axis_labels)}
  <text x="32" y="229" class="subtle">actuarial workflow</text>
  {''.join(arrows)}
  {''.join(nodes)}
</svg>
'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("assets/actuarial-signal.svg"))
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    render_actuarial_signal(args.output, animated=not args.static)


if __name__ == "__main__":
    main()
