"""
Agent Skills registry — real Skills-API resources
(policy_orchestrator/skills/<key>/SKILL.md, bundled with the package), NOT
inline system-prompt text.

cli/setup.py uploads each SKILL.md via client.beta.skills.create(files=[...])
and attaches the returned skill_id to the owning subagent(s) via the agent's
`skills` field. Each entry below is one skill; `owners` says which subagent
key(s) use it (all 18 are single-owner in this design — no skill is shared
across agents, matching the original architecture doc).
"""
from pathlib import Path

from policy_orchestrator.settings import SKILLS_DIR

SKILLS = [
    {"key": "policy-question-framing", "owners": ["question_framing"]},
    {"key": "official-policy-source-research", "owners": ["evidence_research"]},
    {"key": "claim-evidence-mapping", "owners": ["evidence_research"]},
    {"key": "citation-and-fact-verification", "owners": ["evidence_research"]},
    {"key": "stakeholder-position-analysis", "owners": ["stakeholder_mapping"]},
    {"key": "karnataka-bengaluru-impact-assessment", "owners": ["karnataka_bengaluru_impact"]},
    {"key": "global-policy-benchmarking", "owners": ["global_benchmark"]},
    {"key": "policy-option-generation", "owners": ["options_tradeoff"]},
    {"key": "cost-benefit-and-tradeoff-analysis", "owners": ["options_tradeoff"]},
    {"key": "legal-and-institutional-feasibility", "owners": ["options_tradeoff"]},
    {"key": "implementation-readiness-assessment", "owners": ["options_tradeoff"]},
    {"key": "policy-position-development", "owners": ["position_redteam"]},
    {"key": "policy-position-red-teaming", "owners": ["position_redteam"]},
    {"key": "mp-position-consistency-check", "owners": ["position_redteam"]},
    {"key": "policy-brief-writing", "owners": ["output_action"]},
    {"key": "speech-and-question-conversion", "owners": ["output_action"]},
    {"key": "sensitivity-and-confidentiality-review", "owners": ["output_action"]},
    {"key": "approved-position-versioning", "owners": ["output_action"]},
]


def skill_path(skill_key: str) -> Path:
    return SKILLS_DIR / skill_key / "SKILL.md"


def skills_for(subagent_key: str) -> list[str]:
    return [s["key"] for s in SKILLS if subagent_key in s["owners"]]
