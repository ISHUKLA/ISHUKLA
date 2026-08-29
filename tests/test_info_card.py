from pathlib import Path

import pytest

from scripts.info_card import InfoCardError, render_info_card


def test_info_card_clean_content_generates_accessible_svg(tmp_path: Path) -> None:
    output = tmp_path / "info-card.svg"
    render_info_card(output)

    svg = output.read_text(encoding="utf-8")
    assert "Profile summary for Shukla A." in svg
    assert "French actuary by training" in svg
    assert "Build · Analyse" in svg
    assert "AI tooling for insurers" in svg
    assert "Judgement-led strategic work" in svg
    assert "Savings · Retirement" in svg
    assert "prefers-reduced-motion" in svg


def test_info_card_rejects_incomplete_line(tmp_path: Path) -> None:
    with pytest.raises(InfoCardError, match="must not be blank"):
        render_info_card(tmp_path / "card.svg", lines=(("Role", ""),))
