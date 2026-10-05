"""Domain configuration: knowledge bases, skills registry, subagents, coordinator.

Pure data and prompt-building — no API calls happen at import time. Split
by concern so each file has one reason to change:

    knowledge_bases   the 5 Memory Store definitions
    skills_registry   the 18 Agent Skills and their subagent ownership
    subagents         the 8 specialist subagent definitions + system prompts
    orchestrator      the coordinator's system prompt
"""
from policy_orchestrator.core.knowledge_bases import MEMORY_STORES
from policy_orchestrator.core.orchestrator import ORCHESTRATOR_SYSTEM
from policy_orchestrator.core.skills_registry import SKILLS, skill_path, skills_for
from policy_orchestrator.core.subagents import SUBAGENT_KEYS, SUBAGENTS

__all__ = [
    "MEMORY_STORES",
    "ORCHESTRATOR_SYSTEM",
    "SKILLS",
    "skill_path",
    "skills_for",
    "SUBAGENT_KEYS",
    "SUBAGENTS",
]
