"""
Knowledge Bases -> Memory Stores.

All 5 attach to every session as `resources` (max 8 memory stores/session,
so there's headroom). KB5 (the Policy Position Register) is mounted
read_only for every agent — the *only* way an approved position gets
written to it is through the register_approved_position custom tool in
tools/handlers.py, which is gated on a prior human-approval event. This is a
hard boundary: no agent, however phrased its instructions, can write to KB5
by itself.
"""
MEMORY_STORES = [
    {
        "key": "mp_profile",
        "name": "MP Policy Profile",
        "description": (
            "The MP's previous speeches, parliamentary questions, committee "
            "interventions, approved policy positions, priority areas, "
            "preferred argument style, and positions that changed over time. "
            "Consult this to keep new positions consistent with prior public "
            "record, but do not let it block adopting a new position when the "
            "evidence has changed."
        ),
        "access": "read_write",
    },
    {
        "key": "gov_policy",
        "name": "Parliamentary and Government Policy",
        "description": (
            "Bills and draft legislation, ministry policy documents, "
            "parliamentary committee reports, ministerial Q&A, CAG and NITI "
            "Aayog reports, Union and Karnataka budgets, and government "
            "consultation papers, organised by domain (technology, urban "
            "development, transport, economy/startups, education, "
            "environment, agriculture, youth affairs)."
        ),
        "access": "read_write",
    },
    {
        "key": "karnataka_bengaluru",
        "name": "Karnataka and Bangalore South",
        "description": (
            "Karnataka/Bangalore South economic profile, major industries, "
            "technology ecosystem, infrastructure projects, employment and "
            "skill data, constituency issues, state policies, and stakeholder "
            "representations relevant to the constituency."
        ),
        "access": "read_write",
    },
    {
        "key": "global_policy",
        "name": "Global Policy Repository",
        "description": (
            "Official foreign laws and regulatory frameworks, government "
            "evaluations of those frameworks, and OECD/multilateral reports "
            "with country-specific policy outcomes, used for international "
            "benchmarking."
        ),
        "access": "read_write",
    },
    {
        "key": "position_register",
        "name": "Policy Position Register",
        "description": (
            "The office's institutional policy memory: one entry per policy "
            "topic with the approved position, supporting evidence, "
            "conditions/safeguards, date approved, approver, previous "
            "version, reason for change, and related speeches/questions. "
            "THIS STORE IS READ-ONLY for every agent in this session — check "
            "it for consistency with prior approved positions, but positions "
            "are only ever added to it through the human-approval workflow, "
            "never by direct agent writes."
        ),
        "access": "read_only",
    },
]
