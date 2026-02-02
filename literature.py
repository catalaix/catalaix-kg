# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "curies>=0.12.9",
#     "opencitations-client>=0.0.7",
#     "pandas>=3.0.0",
#     "pubmed-downloader>=0.0.12",
#     "pystow>=0.7.21",
#     "tqdm>=4.67.2",
# ]
# ///

"""Find papers authored by catalaix consortium members, cited by them, and that cite them."""

from collections import defaultdict

import pandas as pd
import pubmed_downloader
import pystow
from curies import Reference
from opencitations_client.cache import get_incoming_citations, get_outgoing_citations
from opencitations_client.download import (
    get_omid_from_pubmed,
    get_omid_from_doi,
    get_pubmed_from_omid,
)
from pystow.utils import safe_open_writer
from tqdm import tqdm
from constants import HERE

PAPERS_TSV_PATH = HERE.joinpath("literature.tsv")
PAPERS_JSONL_PATH = HERE.joinpath("literature.jsonl")
CITATIONS_PATH = HERE.joinpath("citations.tsv")

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

    extra_pmids: set[str] = set()
    with safe_open_writer(CITATIONS_PATH) as citations_writer:
        for article in tqdm(
            articles, unit="article", unit_scale=True, desc="retrieving citations"
        ):
            omid = get_omid_from_pubmed(article.pubmed)
            if not omid and (doi := _get_doi(article)):
                omid = get_omid_from_doi(doi)
            if not omid:
                continue
            omid_reference = Reference(prefix="omid", identifier=omid)

            for incoming_omid in get_incoming_citations(omid_reference):
                if incoming_pubmed := get_pubmed_from_omid(incoming_omid):
                    citations_writer.writerow((incoming_pubmed, str(article.pubmed)))
                    extra_pmids.add(incoming_pubmed)
            for outgoing_omid in get_outgoing_citations(omid_reference):
                if outgoing_pubmed := get_pubmed_from_omid(outgoing_omid):
                    citations_writer.writerow((str(article.pubmed), outgoing_pubmed))
                    extra_pmids.add(outgoing_pubmed)

    articles.extend(
        pubmed_downloader.get_articles(
            extra_pmids.difference(pubmed_ids), progress=True, error_strategy="skip"
        )
    )

    with safe_open_writer(PAPERS_TSV_PATH) as writer:
        writer.writerow(["pubmed", "year", "title", "professors"])
        for article in articles:
            writer.writerow(
                (
                    article.pubmed,
                    article.date_published.year if article.date_published else None,
                    article.title,
                    ",".join(sorted(pubmed_ids.get(str(article.pubmed), []))),
                )
            )


def _get_doi(article: pubmed_downloader.Article) -> str | None:
    for xref in article.xrefs:
        if xref.prefix == "doi":
            return xref.identifier
    return None


if __name__ == "__main__":
    main()
