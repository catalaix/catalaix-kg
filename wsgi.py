# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "bootstrap-flask>=2.5.0",
#     "flask>=3.1.2",
#     "pandas>=3.0.0",
# ]
# ///

from collections import defaultdict

import flask
import pandas as pd
from flask_bootstrap import Bootstrap5
import pyobo

from constants import (
    LABS_PATH,
    REACTIONS_PATH,
    REACTION_HIERARCHY_PATH,
    CONDITIONS_PATH,
    MEMBERSHIPS_PATH,
    CLOSED_LOOPS_PATH,
    CHEMICAL_HIERARCHY_PATH,
    PAPERS_PATH,
)
from draw import draw_bytes

app = flask.Flask(__name__)
Bootstrap5(app)


def _get_catalysts_df(conditions: pd.DataFrame) -> pd.DataFrame:
    return conditions[conditions["catalyst"].notna()][
        ["catalyst", "catalyst name"]
    ].drop_duplicates()


CHEMICAL_HIERARCHY_DF = pd.read_csv(CHEMICAL_HIERARCHY_PATH, sep="\t")
CLOSED_LOOPS_DF = pd.read_csv(CLOSED_LOOPS_PATH, sep="\t")
LABS_DF = pd.read_csv(LABS_PATH, sep="\t")
PROFESSOR_TO_GROUP = dict(LABS_DF[["Professor", "group"]].values)

LITERATURE_DF = pd.read_csv(PAPERS_PATH, sep="\t", dtype=str).sort_values(
    "date", ascending=False
)
LITERATURE_DF["is_review"] = LITERATURE_DF["types"].map(
    lambda types: "D016454" in types
)
GROUP_TO_PUBMEDS = defaultdict(set)
GROUP_TO_DOIS = defaultdict(set)
for _, row in LITERATURE_DF.iterrows():
    if pd.notna(professors := row["professors"]):
        for professor in professors.split(","):
            GROUP_TO_PUBMEDS[PROFESSOR_TO_GROUP[professor]].add(row["pubmed"])
            if pd.notna(row["doi"]):
                GROUP_TO_DOIS[PROFESSOR_TO_GROUP[professor]].add(row["doi"].lower())

DOI_TO_PUBMED = dict(
    LITERATURE_DF[LITERATURE_DF["doi"].notna()][["doi", "pubmed"]].values
)


REACTIONS_DF = pd.read_csv(REACTIONS_PATH, sep="\t")
del REACTIONS_DF["desc."]
REACTION_HIERARCHY_DF = pd.read_csv(REACTION_HIERARCHY_PATH, sep="\t")
CONDITIONS_DF = pd.read_csv(CONDITIONS_PATH, sep="\t").join(
    REACTIONS_DF, on="reaction", how="left", rsuffix="_reaction", lsuffix="_condition"
)
CONDITIONS_DF["pubmed"] = CONDITIONS_DF["doi"].map(DOI_TO_PUBMED)

MEMBERSHIPS_DF = pd.read_csv(MEMBERSHIPS_PATH, sep="\t")
ORCID_TO_GROUPS: defaultdict[str, set[int]] = defaultdict(set)
GROUP_TO_ORCIDS: defaultdict[int, set[str]] = defaultdict(set)
for orcid, _name, lab_id, _lab_name in MEMBERSHIPS_DF.values:
    if pd.notna(orcid):
        ORCID_TO_GROUPS[orcid].add(lab_id)
        GROUP_TO_ORCIDS[lab_id].add(orcid)

PEOPLE_DF = CONDITIONS_DF[
    CONDITIONS_DF["chemist"].notna() & CONDITIONS_DF["chemist name"].notna()
][["chemist", "chemist name"]].drop_duplicates()
PEOPLE: dict[str, str] = {}
for orcid, name in (
    CONDITIONS_DF[
        CONDITIONS_DF["chemist"].notna() & CONDITIONS_DF["chemist name"].notna()
    ][["chemist", "chemist name"]]
    .drop_duplicates()
    .values
):
    PEOPLE[orcid] = name

CATALYST_GROUPING = CONDITIONS_DF[
    CONDITIONS_DF["catalyst"].notna()
    & (CONDITIONS_DF["catalyst"].notna() != "no catalyst")
    & CONDITIONS_DF["catalyst name"].notna()
].groupby(["catalyst", "catalyst name"])

SUBSTRATE_GROUPING = REACTIONS_DF.groupby(["input", "input name"])
PRODUCT_GROUPING = REACTIONS_DF.groupby(["output", "output name"])


@app.route("/")
def get_home() -> str:
    return flask.render_template(
        "home.html",
        people=PEOPLE,
        labs=LABS_DF,
        reactions=REACTIONS_DF,
        conditions=CONDITIONS_DF,
        catalysts=CATALYST_GROUPING,
        substrates=SUBSTRATE_GROUPING,
        products=PRODUCT_GROUPING,
        closed_loops=CLOSED_LOOPS_DF,
    )


@app.route("/person/")
def get_people() -> str:
    return flask.render_template("people.html", people=PEOPLE)


@app.route("/person/<orcid>")
def get_person(orcid: str) -> str:
    conditions = CONDITIONS_DF[CONDITIONS_DF["chemist"] == orcid]
    catalysts = _get_catalysts_df(conditions)
    return flask.render_template(
        "person.html",
        orcid=orcid,
        name=PEOPLE[orcid],
        groups=LABS_DF[LABS_DF["group"].isin(ORCID_TO_GROUPS[orcid])],
        conditions=conditions,
        catalysts=catalysts,
    )


@app.route("/group/<int:group>")
def get_group(group: int) -> str:
    data = LABS_DF.loc[LABS_DF["group"] == group].iloc[0].to_dict()
    members = MEMBERSHIPS_DF[MEMBERSHIPS_DF["lab"] == group]
    conditions = CONDITIONS_DF[CONDITIONS_DF["chemist"].isin(GROUP_TO_ORCIDS[group])]
    catalysts = _get_catalysts_df(conditions)
    papers = GROUP_TO_PUBMEDS[group]
    literature = LITERATURE_DF[LITERATURE_DF["pubmed"].isin(papers)]
    return flask.render_template(
        "group.html",
        data=data,
        members=members,
        conditions=conditions,
        catalysts=catalysts,
        literature=literature,
    )


@app.route("/catalyst/<curie>")
def get_catalyst(curie: str) -> str:
    name = pyobo.get_name(curie)
    description = pyobo.get_definition(curie)
    if curie.startswith("CHEBI:"):
        image_url = f"https://bioregistry.io/{curie}?provider=chebi-img"
    else:
        image_url = None

    conditions = CONDITIONS_DF[CONDITIONS_DF["catalyst"] == curie]
    groups = conditions[["group", "group name"]].drop_duplicates()
    people = conditions[["chemist", "chemist name"]].drop_duplicates()
    return flask.render_template(
        "catalyst.html",
        curie=curie,
        name=name,
        description=description,
        image_url=image_url,
        conditions=conditions,
        groups=groups,
        people=people,
    )


@app.route("/entity/<curie>")
def get_entity(curie: str) -> str:
    name = pyobo.get_name(curie)
    description = pyobo.get_definition(curie)
    if curie.startswith("CHEBI:"):
        image_url = f"https://bioregistry.io/{curie}?provider=chebi-img"
    else:
        image_url = None

    substrate_reactions_df = REACTIONS_DF[REACTIONS_DF["input"] == curie]
    substrate_reaction_ids = substrate_reactions_df["reaction"]
    substrate_conditions_df = CONDITIONS_DF[
        CONDITIONS_DF["reaction"].isin(substrate_reaction_ids)
    ]
    substrate_diagram = draw_bytes(
        labs_df=LABS_DF,
        reactions_df=substrate_reactions_df,
        conditions_df=substrate_conditions_df,
        reaction_hierarchy_df=REACTION_HIERARCHY_DF,
        chemical_hierarchy_df=CHEMICAL_HIERARCHY_DF,
        direction="TD",
        group_closed_loop=False,
    )

    product_reactions_df = REACTIONS_DF[REACTIONS_DF["output"] == curie]
    product_reaction_ids = product_reactions_df["reaction"]
    product_conditions_df = CONDITIONS_DF[
        CONDITIONS_DF["reaction"].isin(product_reaction_ids)
    ]
    product_diagram = draw_bytes(
        labs_df=LABS_DF,
        reactions_df=product_reactions_df,
        conditions_df=product_conditions_df,
        reaction_hierarchy_df=REACTION_HIERARCHY_DF,
        chemical_hierarchy_df=CHEMICAL_HIERARCHY_DF,
        direction="TD",
        group_closed_loop=False,
    )

    return flask.render_template(
        "entity.html",
        name=name,
        description=description,
        image_url=image_url,
        substrate_conditions=substrate_conditions_df,
        input_diagram=substrate_diagram,
        product_diagram=product_diagram,
        product_conditions=product_conditions_df,
    )


@app.route("/paper/<pubmed>")
def get_paper(pubmed: str) -> str:
    """Get a page for a paper."""
    row = LITERATURE_DF[LITERATURE_DF["pubmed"] == pubmed].iloc[0].to_dict()
    conditions = CONDITIONS_DF[CONDITIONS_DF["pubmed"] == pubmed]
    return flask.render_template("paper.html", data=row, conditions=conditions)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
