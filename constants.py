from pathlib import Path

HERE = Path(__file__).parent.resolve()
CURATION_DIR = HERE.joinpath("curation")
LABS_PATH = CURATION_DIR.joinpath("labs.tsv")
REACTIONS_PATH = CURATION_DIR.joinpath("reactions.tsv")
REACTION_HIERARCHY_PATH = CURATION_DIR.joinpath("reaction_hierarchy.tsv")
CONDITIONS_PATH = CURATION_DIR.joinpath("conditions.tsv")
MEMBERSHIPS_PATH = CURATION_DIR.joinpath("memberships.tsv")
CLOSED_LOOPS_PATH = CURATION_DIR.joinpath("closed_loops.tsv")
