"""Fetch public GitHub activity and render a self-contained animated SVG."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
COUNT_PATTERN = re.compile(r"([\d,]+) contribution")
PALETTE = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353")


class ContributionError(ValueError):
    """Raised when public contribution data is missing or inconsistent."""


@dataclass(frozen=True)
class ContributionDay:
    date: str
    count: int
    level: int


def fetch_contribution_html(username: str) -> str:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ContributionError("username is not a valid GitHub username")
    response = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={
            "Accept": "text/html",
            "User-Agent": "ISHUKLA-profile-art/1.0 (+https://github.com/ISHUKLA)",
        },
        timeout=20,
    )
    response.raise_for_status()
    if len(response.text) < 1_000:
        raise ContributionError("GitHub returned an unexpectedly short contribution page")
    return response.text


def parse_contributions(page: str) -> list[ContributionDay]:
    soup = BeautifulSoup(page, "html.parser")
    cells = soup.select("[data-date][data-level]")
    if not cells:
        raise ContributionError("no contribution cells were found in the page")

    tooltip_text: dict[str, str] = {}
    for tooltip in soup.select("tool-tip[for]"):
        target = tooltip.get("for")
        if target:
            tooltip_text[target] = tooltip.get_text(" ", strip=True)

    parsed: list[ContributionDay] = []
    seen_dates: set[str] = set()
    for cell in cells:
        raw_date = cell.get("data-date", "")
        try:
            date.fromisoformat(raw_date)
        except ValueError as exc:
            raise ContributionError(f"invalid contribution date: {raw_date!r}") from exc
        if raw_date in seen_dates:
            raise ContributionError(f"duplicate contribution date: {raw_date}")
        seen_dates.add(raw_date)

        try:
            level = int(cell.get("data-level", ""))
        except ValueError as exc:
            raise ContributionError(f"invalid contribution level for {raw_date}") from exc
        if level not in range(len(PALETTE)):
            raise ContributionError(f"contribution level is outside 0-{len(PALETTE) - 1}: {level}")

        text = tooltip_text.get(cell.get("id", ""), "")
        if text.lower().startswith("no contribution"):
            count = 0
        else:
            match = COUNT_PATTERN.search(text)
            if match is None:
                raise ContributionError(f"missing contribution count for {raw_date}")
            count = int(match.group(1).replace(",", ""))

        if (count == 0) != (level == 0):
            raise ContributionError(f"count and intensity level disagree for {raw_date}")
        parsed.append(ContributionDay(date=raw_date, count=count, level=level))

    return sorted(parsed, key=lambda item: item.date)


def write_dataset(username: str, days: list[ContributionDay], destination: Path) -> dict[str, Any]:
    if not days:
        raise ContributionError("cannot write an empty contribution dataset")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "username": username,
        "observed_through": days[-1].date,
        "source": f"https://github.com/users/{username}/contributions",
        "days": [asdict(day) for day in days],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def load_dataset(source: Path) -> dict[str, Any]:
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContributionError(f"dataset is not readable JSON: {source}") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("days"), list):
        raise ContributionError("dataset does not follow profile activity schema version 1")
    return payload


def _validated_days(payload: dict[str, Any]) -> list[ContributionDay]:
    output: list[ContributionDay] = []
    try:
        for raw in payload["days"]:
            day = ContributionDay(date=raw["date"], count=int(raw["count"]), level=int(raw["level"]))
            date.fromisoformat(day.date)
            if day.count < 0 or day.level not in range(len(PALETTE)):
                raise ValueError
            if (day.count == 0) != (day.level == 0):
                raise ValueError
            output.append(day)
    except (KeyError, TypeError, ValueError) as exc:
        raise ContributionError("dataset contains a malformed contribution day") from exc
    if not output:
        raise ContributionError("dataset contains no contribution days")
    if len({item.date for item in output}) != len(output):
        raise ContributionError("dataset contains duplicate dates")
    return sorted(output, key=lambda item: item.date)


def _streak_statistics(days: list[ContributionDay]) -> tuple[int, int]:
    counts = {date.fromisoformat(item.date): item.count for item in days}
    first, last = min(counts), max(counts)
    longest = run = 0
    cursor = first
    while cursor <= last:
        if counts.get(cursor, 0) > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        cursor += timedelta(days=1)

    current = 0
    cursor = last
    while counts.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def render_svg(payload: dict[str, Any], destination: Path, *, animated: bool = True) -> None:
    days = _validated_days(payload)
    username = payload.get("username")
    if not isinstance(username, str) or not USERNAME_PATTERN.fullmatch(username):
        raise ContributionError("dataset username is missing or invalid")

    by_date = {date.fromisoformat(item.date): item for item in days}
    last_day = max(by_date)
    current_week_sunday = last_day - timedelta(days=(last_day.weekday() + 1) % 7)
    first_week_sunday = current_week_sunday - timedelta(weeks=52)

    width, height = 900, 210
    x_origin, y_origin = 91, 50
    cell, gap, stride = 12, 3, 15
    weekday_labels = ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    rectangles: list[str] = []

    for week in range(53):
        for weekday in range(7):
            day_date = first_week_sunday + timedelta(weeks=week, days=weekday)
            if day_date > last_day:
                continue
            item = by_date.get(day_date, ContributionDay(day_date.isoformat(), 0, 0))
            delay = (week + weekday) * 0.008
            css_class = "day" if animated else "day static"
            noun = "contribution" if item.count == 1 else "contributions"
            rectangles.append(
                f'<rect class="{css_class}" x="{x_origin + week * stride}" '
                f'y="{y_origin + weekday * stride}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{PALETTE[item.level]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{item.date}: {item.count} {noun}</title></rect>'
            )

    month_labels: list[str] = []
    shown_months: set[tuple[int, int]] = set()
    for week in range(53):
        week_start = first_week_sunday + timedelta(weeks=week)
        for offset in range(7):
            candidate = week_start + timedelta(days=offset)
            if candidate > last_day:
                break
            key = (candidate.year, candidate.month)
            if candidate.day <= 7 and key not in shown_months:
                shown_months.add(key)
                month_labels.append(
                    f'<text x="{x_origin + week * stride}" y="35" class="label">{candidate.strftime("%b")}</text>'
                )
                break

    total = sum(item.count for item in days)
    active_days = sum(item.count > 0 for item in days)
    current_streak, longest_streak = _streak_statistics(days)
    observed = html.escape(str(payload.get("observed_through", last_day.isoformat())))

    labels = "".join(
        f'<text x="52" y="{y_origin + index * stride + 10}" class="label">{name}</text>'
        for index, name in weekday_labels
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Public GitHub contribution activity for {html.escape(username)}</title>
  <desc id="desc">A 53-week activity calendar with {total} public contributions across {active_days} active days.</desc>
  <style>
    text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .label {{ fill: #8b949e; font-size: 11px; }}
    .metric {{ fill: #c9d1d9; font-size: 12px; }}
    .accent {{ fill: #7ee787; font-weight: 600; }}
    .day {{ opacity: 0; transform: translateY(-5px); animation: reveal .28s ease-out forwards; }}
    .day.static {{ opacity: 1; transform: none; animation: none; }}
    @keyframes reveal {{ to {{ opacity: 1; transform: translateY(0); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .day {{ opacity: 1; transform: none; animation: none; }}
    }}
  </style>
  <rect x="1" y="1" width="898" height="208" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  {''.join(month_labels)}
  {labels}
  {''.join(rectangles)}
  <line x1="28" y1="166" x2="872" y2="166" stroke="#21262d"/>
  <text x="28" y="190" class="metric"><tspan class="accent">{total}</tspan> public contributions · <tspan class="accent">{active_days}</tspan> active days · current streak <tspan class="accent">{current_streak}</tspan> · longest <tspan class="accent">{longest_streak}</tspan></text>
  <text x="872" y="190" text-anchor="end" class="label">through {observed}</text>
</svg>
'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="ISHUKLA")
    parser.add_argument("--input-html", type=Path, help="parse a saved page instead of fetching")
    parser.add_argument("--data", type=Path, default=Path("data/contributions.json"))
    parser.add_argument("--output", type=Path, default=Path("assets/contribution-graph.svg"))
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()

    page = args.input_html.read_text(encoding="utf-8") if args.input_html else fetch_contribution_html(args.username)
    payload = write_dataset(args.username, parse_contributions(page), args.data)
    render_svg(payload, args.output, animated=not args.static)


if __name__ == "__main__":
    main()
