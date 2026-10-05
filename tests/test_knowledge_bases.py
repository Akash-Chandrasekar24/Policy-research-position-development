"""MEMORY_STORES structural checks — no API calls."""
from policy_orchestrator.core import MEMORY_STORES


def test_exactly_five_knowledge_bases():
    assert len(MEMORY_STORES) == 5


def test_all_keys_are_unique():
    keys = [kb["key"] for kb in MEMORY_STORES]
    assert len(keys) == len(set(keys))


def test_every_kb_has_required_fields():
    for kb in MEMORY_STORES:
        assert kb["key"]
        assert kb["name"]
        assert kb["description"]
        assert kb["access"] in ("read_write", "read_only")


def test_exactly_one_read_only_store_and_it_is_the_position_register():
    read_only = [kb for kb in MEMORY_STORES if kb["access"] == "read_only"]
    assert len(read_only) == 1
    assert read_only[0]["key"] == "position_register"
