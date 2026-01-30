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

import base64
import textwrap
from collections import defaultdict
from typing import Literal, Any

import pandas as pd
from pathlib import Path
from pystow.utils import download
import pygraphviz as pgv
import cairosvg
from constants import (
    HERE,
    REACTIONS_PATH,
    REACTION_HIERARCHY_PATH,
    CONDITIONS_PATH,
    LABS_PATH,
    CHEMICAL_HIERARCHY_PATH,
)

IMG = HERE.joinpath("img")
OUTPUT = HERE.joinpath("output")

HIGHLIGHT = {
    "CHEBI:53259",  # PET
    "CHEBI:231672",  # BHET
    "CHEBI:156286",  # DMT
    "CHEBI:15702",  # TPA
}


def main(
    *,
    add_reagent: bool = False,
    add_output_2: bool = False,
    group_closed_loop: bool = True,
    direction: Literal["LR", "TD"] = "LR",
) -> None:
    conditions_df = pd.read_csv(CONDITIONS_PATH, sep="\t")
    labs_df = pd.read_csv(LABS_PATH, sep="\t")
    reactions_df = pd.read_csv(REACTIONS_PATH, sep="\t")
    reaction_hierarchy_df = pd.read_csv(REACTION_HIERARCHY_PATH, sep="\t")
    chemical_hierarchy_df = pd.read_csv(CHEMICAL_HIERARCHY_PATH, sep="\t")

    for kingdom, kingdom_df in reactions_df.groupby("kingdom"):
        draw(
            labs_df=labs_df,
            reactions_df=kingdom_df,
            conditions_df=conditions_df,
            reaction_hierarchy_df=reaction_hierarchy_df,
            chemical_hierarchy_df=chemical_hierarchy_df,
            add_reagent=add_reagent,
            add_output_2=add_output_2,
            group_closed_loop=group_closed_loop,
            direction=direction,
            output=OUTPUT.joinpath(f"{kingdom}.png"),
        )


def draw_bytes(*args: Any, **kwargs: Any) -> str:
    diagram_bytes = draw(*args, **kwargs)
    b64_bytes = base64.b64encode(diagram_bytes)
    b64_str = b64_bytes.decode("ascii")
    return b64_str


def draw(
    labs_df: pd.DataFrame,
    reactions_df: pd.DataFrame,
    conditions_df: pd.DataFrame,
    reaction_hierarchy_df: pd.DataFrame,
    chemical_hierarchy_df: pd.DataFrame,
    *,
    add_reagent: bool = False,
    add_output_2: bool = False,
    group_closed_loop: bool = True,
    draw_reaction_hierarchy: bool = True,
    draw_chemical_hierarchy: bool = True,
    direction: Literal["LR", "TD"] = "LR",
    output: Path | None = None,
) -> None | str:
    lab_id_to_name = {
        group_id: professor.split(" ", maxsplit=1)[1]
        for group_id, professor in labs_df[["group", "Professor"]].values
    }
    reaction_to_group_names = defaultdict(lambda: defaultdict(set))
    for reaction, reaction_method, group in conditions_df[
        ["reaction", "method", "group"]
    ].values:
        reaction_to_group_names[reaction][reaction_method].add(
            lab_id_to_name[group] if pd.notna(group) and group else "External"
        )

    graph = pgv.AGraph(directed=True)
    graph.graph_attr["rankdir"] = direction
    graph.node_attr.update(
        {
            "fontsize": "16",
            "fontname": "Helvetica",
        }
    )

    curies = {
        curie: name
        for pairs in [
            ["input", "input name"],
            ["output", "output name"],
            ["output 2", "output 2 name"],
            ["reagent", "reagent name"],
        ]
        for curie, name in reactions_df[pairs].values
        if pd.notna(curie)
    }

    keep = ["input", "output"]
    if add_reagent:
        keep.append("reagent")
    if add_output_2:
        keep.append("output 2")

    add_node_for = {curie for curies in reactions_df[keep].values for curie in curies}

    for curie, name in curies.items():
        if not curie.startswith("CHEBI:"):
            png_path = None
        else:
            chebi_id = curie.removeprefix("CHEBI:")
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
        if curie in add_node_for:
            node_attrs = dict(
                label=textwrap.fill(name, 30) if pd.notna(name) else "???",
                labelloc="b",
                shape="box",
            )
            if png_path is not None:
                node_attrs["image"] = png_path
            if curie in HIGHLIGHT:
                node_attrs.update(
                    color="blue"  # border color
                )
            graph.add_node(curie, **node_attrs)

    if group_closed_loop:
        sub = graph.add_subgraph(name="cluster_0", label="Closed Loop", color="blue")
        for node in HIGHLIGHT:
            if node in graph:
                sub.add_node(node)

    for (
        reaction_id,
        reactant_1,
        reactant_2,
        product_1,
        product_2,
        reaction_method,
    ) in reactions_df[
        ["reaction", "input", "reagent", "output", "output 2", "type name"]
    ].values:
        label_parts = []
        if pd.notna(reaction_method):
            label_parts.append(reaction_method)
        if type_to_groups := reaction_to_group_names.get(reaction_id):
            for rtype, groups in type_to_groups.items():
                groups_text = ", ".join(sorted(groups))
                label_parts.append(f"{rtype} ({groups_text})")

        label = "\n".join(label_parts)

        graph.add_node(reaction_id, label=label, shape="box")
        graph.add_edge(reactant_1, reaction_id)
        graph.add_edge(reaction_id, product_1)
        if add_reagent and pd.notna(reactant_2):
            graph.add_edge(reactant_2, reaction_id)
        if add_output_2 and pd.notna(product_2):
            graph.add_edge(reaction_id, product_2)

        if group_closed_loop and reactant_1 in HIGHLIGHT and product_1 in HIGHLIGHT:
            sub.add_node(reaction_id)

    if draw_reaction_hierarchy:
        for child, parent in reaction_hierarchy_df.values:
            if child in graph and parent in graph:
                graph.add_edge(child, parent, label="is a")

    if draw_chemical_hierarchy:
        for child, parent in chemical_hierarchy_df[["child", "parent"]].values:
            if child in graph and parent in graph:
                graph.add_edge(child, parent, label="is a")

    return graph.draw(output, format="png", prog="dot")


if __name__ == "__main__":
    main()
