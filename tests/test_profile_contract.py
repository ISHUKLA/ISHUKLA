from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_readme_uses_only_repository_owned_artwork_and_real_project_links() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "./assets/portrait.svg" in readme
    assert "./assets/info-card.svg" in readme
    assert "./assets/contribution-graph.svg" in readme
    assert "./assets/personal-signal.svg" in readme
    assert "./assets/fip-radio.svg" in readme
    assert "./assets/actuarial-signal.svg" not in readme
    assert "https://github.com/ISHUKLA/SolvaIIRAG" in readme
    assert "https://github.com/ISHUKLA/BACI-climate-index" in readme
    assert "https://github.com/ISHUKLA/ai-job-search" in readme
    assert "https://www.radiofrance.fr/fip" in readme
    assert "CHIC" not in readme
    assert "Claude FM" not in readme
    assert "French actuary by training" in readme
    assert "I like to build and analyse" in readme
    assert "AI tooling for insurers" in readme
    assert "Judgement-related strategic insurance work" in readme
    assert "savings and retirement lines" in readme
    assert "Excel Audit Agent" not in readme
    assert "github-readme-stats" not in readme


def test_fip_radio_button_is_accessible_and_motion_safe() -> None:
    button = (ROOT / "assets/fip-radio.svg").read_text(encoding="utf-8")
    assert "Open FIP Radio" in button
    assert "FIP RADIO" in button
    assert "ON / OFF" in button
    assert "prefers-reduced-motion" in button


def test_workflow_has_narrow_write_permission_and_no_token() -> None:
    workflow = (ROOT / ".github/workflows/update-profile-art.yml").read_text(encoding="utf-8")
    assert "contents: write" in workflow
    assert "python scripts/contributions.py --username ISHUKLA" in workflow
    assert "secrets." not in workflow
    assert "personal access token" not in workflow.lower()
    assert "stefanzweifel" not in workflow
    assert 'git config user.name "github-actions[bot]"' in workflow
    assert "uses: actions/checkout@v7" in workflow
    assert "uses: actions/setup-python@v7" in workflow
