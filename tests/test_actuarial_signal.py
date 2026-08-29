from pathlib import Path

import pytest

from scripts.actuarial_signal import ActuarialSignalError, render_actuarial_signal


def test_clean_scenarios_generate_accessible_animated_svg(tmp_path: Path) -> None:
    output = tmp_path / "actuarial-signal.svg"
    render_actuarial_signal(output)

    svg = output.read_text(encoding="utf-8")
    assert "Animated actuarial scenario signal" in svg
    assert "Savings" not in svg  # labels stay lower case or sentence case, not promotional copy
    assert "savings &amp; retirement" in svg
    assert "Downside" in svg
    assert "Central" in svg
    assert "Upside" in svg
    assert "Data" in svg
    assert "Assumptions" in svg
    assert "Scenarios" in svg
    assert "Judgement" in svg
    assert "not model output" in svg
    assert "prefers-reduced-motion" in svg
    assert 'repeatCount="indefinite"' not in svg


def test_crossing_scenarios_are_rejected(tmp_path: Path) -> None:
    crossing = {
        "downside": (100, 120, 140),
        "central": (100, 115, 150),
        "upside": (100, 130, 145),
    }

    with pytest.raises(ActuarialSignalError, match="crosses"):
        render_actuarial_signal(tmp_path / "bad.svg", scenarios=crossing)


def test_incomplete_scenario_set_is_rejected(tmp_path: Path) -> None:
    incomplete = {"central": (100, 110, 120)}

    with pytest.raises(ActuarialSignalError, match="downside, central, and upside"):
        render_actuarial_signal(tmp_path / "bad.svg", scenarios=incomplete)
