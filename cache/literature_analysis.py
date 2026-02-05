import click
import networkx as nx
from pystow.utils import safe_open_reader

from pathlib import Path
from functools import partial
import textwrap

HERE = Path(__file__).parent.resolve()
OUT_STUB = HERE.joinpath("literature_subgraph_example")
OUT_SVG = OUT_STUB.with_suffix(".svg")
OUT_PNG = OUT_STUB.with_suffix(".png")


def main():
    graph = nx.DiGraph()

    with safe_open_reader(HERE.joinpath("literature.tsv")) as reader:
        next(reader)
        for pubmed, year, title, professors in reader:
            if not year or int(year) < 2015:
                continue
            if not professors:
                continue
            professors = ", ".join(p.split()[-1] for p in professors.split(","))
            label = f"{title}\n{professors} ({year})"
            graph.add_node(
                pubmed, label=label, year=int(year), title=title, professors=professors
            )

    with safe_open_reader(HERE.joinpath("citations.tsv")) as reader:
        for source, target in reader:
            if source in graph and target in graph:
                graph.add_edge(source, target)

    for node in list(graph):
        if not graph.in_degree(node) and not graph.out_degree(node):
            graph.remove_node(node)

    largest_component_nodes = max(
        (
            nx.descendants(graph, node) | {node}
            for node in graph.nodes()
            if graph.nodes[node]["year"] > 2021
        ),
        key=partial(_size, graph=graph),
    )

    largest_component = graph.subgraph(largest_component_nodes).copy()

    click.echo(digraph_to_mermaid(largest_component))

    relabelling = {
        node: f"{textwrap.fill(data['title'], 60)}\n{data['professors']} ({data['year']})"
        for node, data in graph.nodes(data=True)
    }
    subgraph = nx.relabel_nodes(largest_component, relabelling)
    agraph = nx.nx_agraph.to_agraph(subgraph)
    agraph.draw(OUT_SVG, prog="dot")
    agraph.draw(OUT_PNG, prog="dot")

    # TODO do some graph analytics. what is the:
    #  1. in-degree distribution,
    #  2. out-degree distribution,
    #  3. number of papers per year
    #  4. Author frequency
    #  5. build co-author network?
    #  looking forward, doing joint disambiguation of authors


def _size(nodes, graph):
    if len(nodes) < 5:
        return 0
    professors = {
        prof for node in nodes for prof in graph.nodes[node]["professors"].split(",")
    }
    return len(professors) / len(nodes)


def digraph_to_mermaid(graph: nx.DiGraph) -> str:
    lines = []
    for node, data in graph.nodes(data=True):
        if label := data.get("label"):
            lines.append(f'{node}["{label}"]')
    for u, v, data in graph.edges(data=True):
        if edge_label := data.get("label"):
            lines.append(f"{u} -- {edge_label} --> {v}")
        else:
            lines.append(f"{u} --> {v}")
    return "flowchart LR\n" + "\n".join("\t" + line for line in lines)


if __name__ == "__main__":
    main()
