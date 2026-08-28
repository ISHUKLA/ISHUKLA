import json
from pathlib import Path

import pytest

from scripts.contributions import (
    ContributionError,
    parse_contributions,
    render_svg,
    write_dataset,
)


CLEAN_HTML = """
<table>
  <tr>
    <td id="d1" data-date="2026-08-27" data-level="0"></td>
    <tool-tip for="d1">No contributions on August 27th.</tool-tip>
    <td id="d2" data-date="2026-08-28" data-level="2"></td>
    <tool-tip for="d2">3 contributions on August 28th.</tool-tip>
  </tr>
</table>
"""


def test_clean_contribution_page_round_trips_to_svg(tmp_path: Path) -> None:
    days = parse_contributions(CLEAN_HTML)
    data_file = tmp_path / "contributions.json"
    payload = write_dataset("ISHUKLA", days, data_file)
    output = tmp_path / "contribution-graph.svg"
    render_svg(payload, output)

    persisted = json.loads(data_file.read_text(encoding="utf-8"))
    svg = output.read_text(encoding="utf-8")
    assert persisted["days"][1]["count"] == 3
    assert "3 public contributions" in svg
    assert "current streak <tspan class=\"accent\">1</tspan>" in svg
    assert "prefers-reduced-motion" in svg


def test_contribution_parser_rejects_missing_cells() -> None:
    with pytest.raises(ContributionError, match="no contribution cells"):
        parse_contributions("<html><body>rate limited</body></html>")


def test_contribution_parser_rejects_active_cell_without_count() -> None:
    malformed = '<td id="d1" data-date="2026-08-28" data-level="2"></td>'
    with pytest.raises(ContributionError, match="missing contribution count"):
        parse_contributions(malformed)


def test_renderer_rejects_malformed_dataset(tmp_path: Path) -> None:
    malformed = {
        "schema_version": 1,
        "username": "ISHUKLA",
        "days": [{"date": "not-a-date", "count": 1, "level": 2}],
    }
    with pytest.raises(ContributionError, match="malformed contribution day"):
        render_svg(malformed, tmp_path / "graph.svg")
