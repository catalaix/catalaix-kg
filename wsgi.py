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

HERE = Path(__file__).parent.resolve()
LABS_PATH = HERE.joinpath("labs.tsv")
REACTIONS_PATH = HERE.joinpath("reactions.tsv")

app = flask.Flask(__name__)
Bootstrap5(app)


@app.route("/")
def get_home() -> str:
    labs_df = pd.read_csv(LABS_PATH, sep="\t")
    reactions_df = pd.read_csv(REACTIONS_PATH, sep="\t")
    return flask.render_template("home.html", labs=labs_df, reactions=reactions_df)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
