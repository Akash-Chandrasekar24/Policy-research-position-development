"""
Runtime settings for the Policy Intelligence Orchestrator.

Two different kinds of path live here, and they resolve differently on
purpose:

  - SKILLS_DIR is a *bundled resource* — it ships inside the installed
    package, so it's resolved relative to this file, not the caller's CWD.
    This is what makes `uv run policy-setup` work correctly regardless of
    which directory it's invoked from.
  - STATE_FILE and OUTPUT_DIR are *runtime artifacts* — they belong to
    wherever the operator chooses to run the tool from (so state/output for
    a dev checkout and a deployed instance don't collide), so they stay
    CWD-relative.
"""
import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent

# Bundled resource — see module docstring.
SKILLS_DIR = PACKAGE_ROOT / "skills"

# Runtime artifacts — CWD-relative by design.
STATE_FILE = Path("./policy_state.json")
OUTPUT_DIR = Path("./generated_policy_output")

ENVIRONMENT_NAME = "policy-intelligence-env"

# Model used for every agent (coordinator + all 8 subagents). Centralized
# here so changing it doesn't require touching cli/setup.py.
MODEL = "claude-sonnet-4-6"  # cheaper, smaller model for faster execution

BETA_HEADER = "managed-agents-2026-04-01"

# ---------------------------------------------------------------------------
# Research history (policy_orchestrator.history) — a Postgres+pgvector store
# of every finished run, used to answer "have we researched this before?"
# before spending a full 8-agent pass on a question. Entirely optional: if
# DATABASE_URL is unset, the history feature no-ops everywhere it's called
# (no lookup, no write) and the rest of the system behaves exactly as
# before. Read at import time, so callers must `load_dotenv()` first — see
# the entry points in cli/ and web/app.py, which all do this already.
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # fastembed/ONNX, local, free — no API key, no per-call cost
EMBEDDING_DIM = 384

# Cosine similarity above which a past question counts as "the same
# question" rather than merely "the same general topic". Calibrated
# empirically: true paraphrases of the same question scored ~0.86-0.87,
# genuinely unrelated questions scored ~0.60. 0.82 sits with margin on
# both sides — tune here if false positives/negatives show up in practice.
SIMILARITY_THRESHOLD = 0.82
