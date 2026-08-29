from pathlib import Path

import pytest

from scripts.personal_signal import PersonalSignalError, render_personal_signal


def test_clean_profile_generates_accessible_personal_signature(tmp_path: Path) -> None:
    output = tmp_path / "personal-signal.svg"
    render_personal_signal(output)

    svg = output.read_text(encoding="utf-8")
    assert "Shukla A. — Actuary, Builder, Analyst" in svg
    assert "French actuary by training" in svg
    assert "AI tooling for insurers" in svg
    assert "judgement-led strategy" in svg
    assert "savings + retirement" in svg
    assert "Actuary · Builder · Analyst" in svg
    assert "projection · evidence · human judgement" in svg
    assert "French tricolour" in svg
    assert "prefers-reduced-motion" in svg
    assert "infinite" not in svg


def test_blank_story_value_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(PersonalSignalError, match="must not be blank"):
        render_personal_signal(
            tmp_path / "bad.svg",
            lines=(("hello", "French actuary"), ("mode", ""), ("now", "AI")),
        )


def test_decreasing_trajectory_is_rejected(tmp_path: Path) -> None:
    malformed = (0.1, 0.2, 0.3, 0.4, 0.35, 0.6, 0.8, 1.0)

    with pytest.raises(PersonalSignalError, match="non-decreasing"):
        render_personal_signal(tmp_path / "bad.svg", trajectory=malformed)
