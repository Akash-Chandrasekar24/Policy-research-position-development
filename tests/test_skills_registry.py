"""Agent Skills registry checks — verifies the 18 SKILL.md files on disk
actually match what core.skills_registry.SKILLS declares. No API calls."""
import re

from policy_orchestrator.core import SKILLS, SUBAGENT_KEYS, skill_path, skills_for


def test_exactly_eighteen_skills():
    assert len(SKILLS) == 18


def test_every_skill_file_exists_on_disk():
    missing = [s["key"] for s in SKILLS if not skill_path(s["key"]).exists()]
    assert missing == []


def test_every_skill_frontmatter_name_matches_its_key():
    for spec in SKILLS:
        text = skill_path(spec["key"]).read_text(encoding="utf-8")
        m = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
        assert m is not None, f"{spec['key']}: no 'name:' frontmatter field"
        assert m.group(1).strip() == spec["key"]


def test_every_skill_has_exactly_one_owner():
    # This design has no shared skills — each of the 18 belongs to exactly
    # one subagent, matching the original architecture doc.
    for spec in SKILLS:
        assert len(spec["owners"]) == 1


def test_every_owner_is_a_real_subagent_key():
    for spec in SKILLS:
        for owner in spec["owners"]:
            assert owner in SUBAGENT_KEYS


def test_skills_for_covers_all_eighteen_skills_across_all_subagents():
    total = sum(len(skills_for(key)) for key in SUBAGENT_KEYS)
    assert total == 18


def test_skills_for_unknown_subagent_returns_empty():
    assert skills_for("not_a_real_subagent") == []
