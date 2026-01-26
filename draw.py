# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "cairosvg>=2.8.2",
#     "pandas>=3.0.0",
#     "pygraphviz>=1.14",
#     "pystow>=0.7.15",
# ]
# ///

"""Create a diagram with the reaction network."""

import pandas as pd
from pathlib import Path
from pystow.utils import download
import pygraphviz as pgv
import cairosvg

HERE = Path(__file__).parent.resolve()
IMG = HERE.joinpath("img")
OUT = HERE.joinpath("graph.png")


def main(add_reagent: bool = False) -> None:
    df = pd.read_csv(
        HERE.joinpath("reactions.tsv"),
        sep="\t",
    )

    graph = pgv.AGraph(directed=True)
    graph.graph_attr["rankdir"] = "LR"
    graph.node_attr.update(
        {
            "fontsize": "16",
            "fontname": "Helvetica",
        }
    )

    chebi_curies = {
        curie: name
        for pairs in [
            ["input", "input name"],
            ["output", "output name"],
            ["output 2", "output 2 name"],
            ["reagent", "reagent name"],
            ["catalyst", "catalyst name"],
        ]
        for curie, name in df[pairs].values
        if pd.notna(curie)
    }

    keep = ["input", "output", "output 2"]
    if add_reagent:
        keep.append("reagent")

    add_node_for = {curie for curies in df[keep].values for curie in curies}

    imgs = {}
    for chebi_curie, name in chebi_curies.items():
        chebi_id = chebi_curie.removeprefix("CHEBI:")
        svg_path = IMG.joinpath(f"chebi_{chebi_id}.svg")
        png_path = IMG.joinpath(f"chebi_{chebi_id}.png")
        url = f"https://www.ebi.ac.uk/chebi/backend/api/public/compound/{chebi_id}/structure/?width=300&height=300"
        if not svg_path.is_file():
            download(url, svg_path)
        if not png_path.is_file():
            cairosvg.svg2png(
                url=svg_path.as_posix(),
                write_to=png_path.as_posix(),
                output_width=256,  # optional
                output_height=256,  # optional
                scale=3.125,
            )

        imgs[chebi_id] = png_path
        if chebi_curie in add_node_for:
            node_attrs = dict(
                label=name if pd.notna(name) else "???",
                image=png_path,
                labelloc="b",
                shape="box",
                # imagescale="true",
                # imagepos="tc",
            )
            graph.add_node(chebi_curie, **node_attrs)

    r = 1
    for inp, out, reagent, out2, catalyst, typen in df[
        ["input", "output", "reagent", "output 2", "catalyst name", "type name"]
    ].values:
        label_parts = []
        if pd.notna(typen):
            label_parts.append(typen)
        if pd.notna(catalyst):
            label_parts.append(f"catalyzed by {catalyst}")

        label = "\n".join(label_parts)

        graph.add_node(r, label=label, shape="box")
        graph.add_edge(inp, r)
        graph.add_edge(r, out)
        if add_reagent and pd.notna(reagent):
            graph.add_edge(reagent, r)
        if pd.notna(out2):
            graph.add_edge(r, out2)
        r += 1

    graph.draw(OUT, prog="dot")


if __name__ == "__main__":
    main()
