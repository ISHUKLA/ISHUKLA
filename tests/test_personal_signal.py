from pathlib import Path

import pytest

from scripts.personal_signal import PersonalSignalError, render_personal_signal


def test_clean_profile_generates_accessible_personal_animation(tmp_path: Path) -> None:
    output = tmp_path / "personal-signal.svg"
    render_personal_signal(output)

    svg = output.read_text(encoding="utf-8")
    assert "Meet Shukla A." in svg
    assert "French actuary by training" in svg
    assert "build + analyse" in svg
    assert "AI tooling for insurers" in svg
    assert "FIP ↔ Claude FM" in svg
    assert "French tricolour" in svg
    assert "Σ" in svg
    assert "♫" in svg
    assert "prefers-reduced-motion" in svg


def test_blank_story_value_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(PersonalSignalError, match="must not be blank"):
        render_personal_signal(
            tmp_path / "bad.svg",
            lines=(("hello", "French actuary"), ("mode", ""), ("now", "AI")),
        )


def test_malformed_waveform_is_rejected(tmp_path: Path) -> None:
    malformed = (0.5,) * 15 + (1.5,)

    with pytest.raises(PersonalSignalError, match="between 0.15 and 1"):
        render_personal_signal(tmp_path / "bad.svg", waveform=malformed)
