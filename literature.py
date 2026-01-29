"""Get papers.

1. Search for papers attached to ORCiD
2. Search for papers attached to Wikidata
3. Search PubMed
"""

from collections import defaultdict
from pathlib import Path

import click
import pandas as pd
import pubmed_downloader
import pystow
from curies import Reference
from opencitations_client import get_incoming_citations, get_outgoing_citations
from pystow.utils import safe_open_writer, write_pydantic_jsonl
from tqdm import tqdm

HERE = Path(__file__).parent.resolve()
PAPERS_TSV_PATH = HERE.joinpath("literature.tsv")
PAPERS_JSONL_PATH = HERE.joinpath("literature.jsonl")

OPENCITATIONS_MOD = pystow.module("opencitations")
INCOMING_MOD = OPENCITATIONS_MOD.module("incoming")
OUTGOING_MOD = OPENCITATIONS_MOD.module("outgoing")


def main(use_pubmed: bool = True, minimum_year: int = 2015) -> None:
    labs_df = pd.read_csv(HERE.joinpath("curation", "labs.tsv"), sep="\t")

    pubmed_ids: defaultdict[str, set[str]] = defaultdict(set)

    if use_pubmed:
        for name in tqdm(
            labs_df["Professor"], unit="laboratory", desc="searching literature"
        ):
            for pubmed_id in pubmed_downloader.search(f"{name}[Author]"):
                pubmed_ids[pubmed_id].add(name)

    articles = list(
        pubmed_downloader.get_articles(pubmed_ids, progress=True, error_strategy="skip")
    )

    for article in tqdm(
        articles, unit="article", unit_scale=True, desc="retrieving citations"
    ):
        if not article.date_published or article.date_published.year < minimum_year:
            continue
        if doi_reference := _get_doi(article):
            incoming_path = INCOMING_MOD.join(name=f"{article.pubmed}.jsonl")
            if not incoming_path.is_file():
                incoming_citations = get_incoming_citations(doi_reference)
                write_pydantic_jsonl(incoming_citations, incoming_path)
            outgoing_path = OUTGOING_MOD.join(name=f"{article.pubmed}.jsonl")
            if not outgoing_path.is_file():
                outgoing_citations = get_outgoing_citations(doi_reference)
                write_pydantic_jsonl(outgoing_citations, outgoing_path)

    with_cites = 0
    with (
        PAPERS_JSONL_PATH.open("w") as file,
        safe_open_writer(PAPERS_TSV_PATH) as writer,
    ):
        writer.writerow(["pubmed", "year", "title", "professors"])
        for article in articles:
            writer.writerow(
                (
                    article.pubmed,
                    article.date_published.year if article.date_published else None,
                    article.title,
                    ",".join(sorted(pubmed_ids[str(article.pubmed)])),
                )
            )
            file.write(
                article.model_dump_json(
                    exclude_none=True, exclude_unset=True, exclude_defaults=True
                )
                + "\n"
            )
            if article.cites_pubmed_ids:
                with_cites += 1

    click.echo(
        f"with citations: {with_cites:,}/{len(articles):,} ({with_cites / len(articles):.1%})"
    )


def _get_doi(article: pubmed_downloader.Article) -> Reference | None:
    for xref in article.xrefs:
        if xref.prefix == "doi":
            return xref
    return None


if __name__ == "__main__":
    main()
