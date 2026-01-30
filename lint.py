# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pandas>=3.0.0",
# ]
# ///
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent.resolve()
CURATION = HERE.joinpath("curation")


def main():
    for path in CURATION.glob("*.tsv"):
        df = pd.read_csv(path, sep="\t")
        df.to_csv(path, index=False, sep="\t")


if __name__ == "__main__":
    main()
