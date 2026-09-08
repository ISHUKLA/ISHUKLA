from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_readme_uses_only_repository_owned_artwork_and_real_project_links() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "./assets/portrait.svg" in readme
    assert "./assets/info-card.svg" in readme
    assert "./assets/contribution-graph.svg" in readme
    assert "./assets/actuarial-signature.svg" in readme
    assert "./assets/based-between.svg" in readme
    assert "./assets/professional-impact.svg" in readme
    assert "./assets/fip-listening.svg" in readme
    assert "./assets/personal-signal.svg" not in readme
    assert "./assets/fip-radio.svg" not in readme
    assert "./assets/actuarial-signal.svg" not in readme
    assert "https://github.com/ISHUKLA/SolvaIIRAG" in readme
    assert "https://github.com/ISHUKLA/BACI-climate-index" in readme
    assert "https://github.com/ISHUKLA/ai-job-search" in readme
    assert "https://www.radiofrance.fr/fip" in readme
    assert "CHIC" not in readme
    assert "Claude FM" in readme
    assert "French actuary by training" in readme
    assert "I like to build and analyse" in readme
    assert "AI tooling for insurers" in readme
    assert "Judgement-related strategic insurance work" in readme
    assert "savings and retirement lines" in readme
    assert "Excel Audit Agent" in readme
    assert "github-readme-stats" not in readme


def test_professional_impact_is_specific_and_evidence_led() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Professional impact" in readme
    assert "Insurance transformation grounded in actuarial practice" in readme
    assert "€1bn+ in reserves" in readme
    assert "50+ practising actuaries" in readme
    assert "89% Hit@4 across 127 Solvency II questions" in readme
    assert "four mandatory human-review gates" in readme
    assert "modelled estimate, not a" in readme
    assert "production benchmark" in readme
    assert "https://www.linkedin.com/in/shuklaisaaca/" in readme


def test_professional_impact_artwork_makes_evidence_immediately_visible() -> None:
    artwork = (ROOT / "assets/professional-impact.svg").read_text(encoding="utf-8")
    assert "<title" in artwork
    assert "<desc" in artwork
    assert "€1bn+" in artwork
    assert "50+" in artwork
    assert "89%" in artwork
    assert "127 Solvency II questions" in artwork
    assert "CFO × CRO" in artwork
    assert "4 gates" in artwork
    assert "@keyframes" not in artwork


def test_location_artwork_states_the_three_places_accessibly() -> None:
    artwork = (ROOT / "assets/based-between.svg").read_text(encoding="utf-8")
    assert "<title" in artwork
    assert "<desc" in artwork
    assert "Based between Charleroi, Paris and India" in artwork
    assert "I move between Charleroi, Paris and India." in artwork
    assert "@keyframes" not in artwork


def test_fip_radio_button_is_accessible_and_motion_safe() -> None:
    button = (ROOT / "assets/fip-listening.svg").read_text(encoding="utf-8")
    assert "Listen to FIP" in button
    assert "RADIO FRANCE · FIP" in button
    assert "Listen while I build" in button
    assert "@keyframes" not in button


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
