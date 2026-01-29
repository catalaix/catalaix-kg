# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "bootstrap-flask>=2.5.0",
#     "flask>=3.1.2",
#     "pandas>=3.0.0",
# ]
# ///

import flask
from pathlib import Path
import pandas as pd
from flask_bootstrap import Bootstrap5
import pyobo

from draw import draw
import base64


HERE = Path(__file__).parent.resolve()
CURATION_DIR = HERE.joinpath("curation")
LABS_PATH = CURATION_DIR.joinpath("labs.tsv")
REACTIONS_PATH = CURATION_DIR.joinpath("reactions.tsv")
CONDITIONS_PATH = CURATION_DIR.joinpath("conditions.tsv")

app = flask.Flask(__name__)
Bootstrap5(app)


@app.route("/")
def get_home() -> str:
    labs_df = pd.read_csv(LABS_PATH, sep="\t")
    reactions_df = pd.read_csv(REACTIONS_PATH, sep="\t")
    conditions_df = pd.read_csv(CONDITIONS_PATH, sep="\t")
    return flask.render_template(
        "home.html", labs=labs_df, reactions=reactions_df, conditions=conditions_df
    )


@app.route("/entity/<curie>")
def get_entity(curie: str) -> str:
    name = pyobo.get_name(curie)
    description = pyobo.get_definition(curie)
    if curie.startswith("CHEBI:"):
        image_url = f"https://bioregistry.io/{curie}?provider=chebi-img"
    else:
        image_url = None
    labs_df = pd.read_csv(LABS_PATH, sep="\t")
    reactions_df = pd.read_csv(REACTIONS_PATH, sep="\t")
    conditions_df = pd.read_csv(CONDITIONS_PATH, sep="\t")

    reactions_df = reactions_df[reactions_df["input"] == curie]
    reaction_ids = reactions_df["reaction"]
    conditions_df = conditions_df[conditions_df["reaction"].isin(reaction_ids)]

    diagram_bytes = draw(
        labs_df=labs_df,
        reactions_df=reactions_df,
        conditions_df=conditions_df,
        direction="TD",
        group_closed_loop=False,
    )
    b64_bytes = base64.b64encode(diagram_bytes)
    b64_str = b64_bytes.decode("ascii")

    return flask.render_template(
        "entity.html",
        name=name,
        description=description,
        image_url=image_url,
        reactions=reactions_df,
        conditions=conditions_df,
        diagram=b64_str,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
