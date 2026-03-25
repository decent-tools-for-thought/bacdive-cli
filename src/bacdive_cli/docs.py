from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EndpointDoc:
    command: str
    cli_usage: str
    http_method: str
    http_path: str
    purpose: str
    path_parameters: tuple[str, ...]
    query_parameters: tuple[str, ...]
    response_shape: str
    result_shape: str
    notes: tuple[str, ...]
    example_queries: tuple[str, ...]
    observed_examples: tuple[str, ...]


OBSERVED_ON = "2026-03-24"
DOC_SOURCES = (
    "https://api.bacdive.dsmz.de/",
    "https://api.bacdive.dsmz.de/strain_fields_information",
)

ENDPOINT_DOCS: dict[str, EndpointDoc] = {
    "fetch": EndpointDoc(
        command="fetch",
        cli_usage="bacdive-cli fetch <bacdive_id> [<bacdive_id> ...] [--predictions] [--page N]",
        http_method="GET",
        http_path="/v2/fetch/{bacdive_id_or_semicolon_separated_ids}",
        purpose="Retrieve full BacDive strain detail records for one or more BacDive IDs.",
        path_parameters=("bacdive_id_or_semicolon_separated_ids: up to 100 BacDive IDs",),
        query_parameters=(
            "page: integer page index, observed default 0",
            "predictions: 0 or 1, used to request genome-based predictions",
        ),
        response_shape=(
            "JSON object with top-level keys count, next, previous, and results. "
            "For fetch, results is an object keyed by BacDive ID strings."
        ),
        result_shape=(
            "Each result value is a rich strain document with sections such as General, "
            "Name and taxonomic classification, Culture and growth conditions, "
            "Interaction and safety, Physiology and metabolism, Sequence information, "
            "Literature, Reference, and optionally Genome-based predictions."
        ),
        notes=(
            "The BacDive landing page states that v2 is the current endpoint family.",
            (
                "The docs state that legacy v1 detail endpoints stopped receiving "
                "updates after April 2025."
            ),
            (
                "The field documentation page states that empty fields are omitted, "
                "while major sections remain present."
            ),
        ),
        example_queries=(
            "bacdive-cli fetch 962",
            "bacdive-cli fetch 12757",
            "bacdive-cli fetch 24493 24494 --predictions",
        ),
        observed_examples=(
            (
                "bacdive-cli fetch 962 returned count=1 and results['962'] with "
                "Bacillus subtilis DSM 1088, DSM number 1088, NCBI tax id 1423, "
                "growth temperature 30 C, biosafety level 1, 16S accessions "
                "AB680377 and HQ231914, and genome accession GCA_040371185."
            ),
            (
                "bacdive-cli fetch 12757 returned count=1 and results['12757'] "
                "with Pseudomonas aeruginosa DSM 288, NCBI tax id 287, growth "
                "temperature 37 C, biosafety level 2, pathogenicity human=yes, "
                "and phenotype blocks including API 20NE and metabolite "
                "utilization."
            ),
        ),
    ),
    "culture-collection": EndpointDoc(
        command="culture-collection",
        cli_usage=(
            "bacdive-cli culture-collection <culture_collection_number> "
            "[<culture_collection_number> ...] [--search-type MODE] [--page N]"
        ),
        http_method="GET",
        http_path="/v2/culturecollectionno/{culturecollectionno_or_semicolon_separated_values}",
        purpose="Resolve culture collection numbers to BacDive IDs.",
        path_parameters=(
            (
                "culturecollectionno_or_semicolon_separated_values: culture "
                "collection numbers such as DSM 288 or DSM 26640"
            ),
        ),
        query_parameters=(
            "search_type: exact, contains, startswith, or endswith",
            "page: integer page index, observed default 0",
        ),
        response_shape=(
            "JSON object with top-level keys count, next, previous, and results. "
            "For this endpoint, results is a list of BacDive integer IDs."
        ),
        result_shape="A flat list of BacDive IDs suitable for follow-up fetch calls.",
        notes=(
            "Exact lookups can be batched with semicolon-separated values.",
            "This is an identifier-resolution endpoint, not a detail endpoint.",
        ),
        example_queries=(
            "bacdive-cli culture-collection 'DSM 288'",
            "bacdive-cli culture-collection DSM --search-type startswith",
        ),
        observed_examples=(
            (
                "bacdive-cli culture-collection 'DSM 288' returned count=1 and "
                "results=[12757]."
            ),
        ),
    ),
    "taxon": EndpointDoc(
        command="taxon",
        cli_usage=(
            "bacdive-cli taxon <genus> [<species_epithet>] [<subspecies_epithet>] [--page N]"
        ),
        http_method="GET",
        http_path="/v2/taxon/{genus}/{species_epithet?}/{subspecies_epithet?}",
        purpose="Resolve taxonomic names to BacDive IDs.",
        path_parameters=(
            "genus: required taxonomic genus",
            "species_epithet: optional species epithet",
            (
                "subspecies_epithet: optional subspecies epithet, only valid when "
                "species epithet is supplied"
            ),
        ),
        query_parameters=("page: integer page index, observed default 0",),
        response_shape=(
            "JSON object with top-level keys count, next, previous, and results. "
            "For this endpoint, results is a list of BacDive integer IDs."
        ),
        result_shape="A flat list of BacDive IDs for strains matching the taxon query.",
        notes=(
            (
                "The endpoint is broad and usually returns many strain records "
                "rather than a single canonical organism record."
            ),
            "Follow up with fetch to inspect specific strains.",
        ),
        example_queries=(
            "bacdive-cli taxon Bacillus",
            "bacdive-cli taxon Bacillus subtilis",
            "bacdive-cli taxon Pseudomonas aeruginosa",
        ),
        observed_examples=(
            (
                "bacdive-cli taxon Bacillus subtilis returned count=286, "
                "next=https://api.bacdive.dsmz.de/v2/taxon/Bacillus/subtilis?"
                "page=1, and first-page IDs beginning with 962, 963, 964, 965."
            ),
            (
                "bacdive-cli taxon Pseudomonas aeruginosa returned count=560, "
                "next=https://api.bacdive.dsmz.de/v2/taxon/Pseudomonas/"
                "aeruginosa?page=1, and first-page IDs beginning with 12757, "
                "12758, 12759, 12760."
            ),
        ),
    ),
    "sequence-16s": EndpointDoc(
        command="sequence-16s",
        cli_usage=(
            "bacdive-cli sequence-16s <accession> [<accession> ...] "
            "[--search-type MODE] [--page N]"
        ),
        http_method="GET",
        http_path="/v2/sequence_16s/{seq_acc_num_or_semicolon_separated_values}",
        purpose="Resolve 16S sequence accession numbers to BacDive IDs.",
        path_parameters=(
            (
                "seq_acc_num_or_semicolon_separated_values: INSDC or related "
                "accession strings used by BacDive"
            ),
        ),
        query_parameters=(
            "search_type: exact, contains, startswith, or endswith",
            "page: integer page index, observed default 0",
        ),
        response_shape=(
            "JSON object with top-level keys count, next, previous, and results. "
            "For this endpoint, results is a list of BacDive integer IDs."
        ),
        result_shape="A flat list of BacDive IDs matching the accession query.",
        notes=(
            "Useful when you already have a 16S accession and want the linked BacDive strain IDs.",
        ),
        example_queries=(
            "bacdive-cli sequence-16s HQ231914",
            "bacdive-cli sequence-16s AF000162",
        ),
        observed_examples=(
            (
                "bacdive-cli sequence-16s HQ231914 returned count=1 and "
                "results=[962]."
            ),
        ),
    ),
    "sequence-genome": EndpointDoc(
        command="sequence-genome",
        cli_usage=(
            "bacdive-cli sequence-genome <accession> [<accession> ...] "
            "[--search-type MODE] [--page N]"
        ),
        http_method="GET",
        http_path="/v2/sequence_genome/{seq_acc_num_or_semicolon_separated_values}",
        purpose="Resolve genome assembly accessions to BacDive IDs.",
        path_parameters=(
            (
                "seq_acc_num_or_semicolon_separated_values: genome accession "
                "strings such as GCA identifiers"
            ),
        ),
        query_parameters=(
            "search_type: exact, contains, startswith, or endswith",
            "page: integer page index, observed default 0",
        ),
        response_shape=(
            "JSON object with top-level keys count, next, previous, and results. "
            "For this endpoint, results is a list of BacDive integer IDs."
        ),
        result_shape="A flat list of BacDive IDs matching the accession query.",
        notes=(
            "Useful when you want to pivot from genome assemblies to BacDive strain records.",
        ),
        example_queries=(
            "bacdive-cli sequence-genome GCA_040371185",
            "bacdive-cli sequence-genome GCA_006094295",
        ),
        observed_examples=(
            (
                "bacdive-cli sequence-genome GCA_040371185 returned count=1 and "
                "results=[962]."
            ),
        ),
    ),
}


def endpoint_names() -> tuple[str, ...]:
    return tuple(ENDPOINT_DOCS.keys())


def render_docs(endpoint: str, output_format: str) -> str:
    payload = _docs_payload(endpoint)
    if output_format == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    return _render_markdown(payload)


def _docs_payload(endpoint: str) -> dict[str, Any]:
    if endpoint == "all":
        endpoints = list(ENDPOINT_DOCS.values())
    else:
        endpoints = [ENDPOINT_DOCS[endpoint]]
    return {
        "kind": "bacdive_cli_endpoint_docs",
        "observed_on": OBSERVED_ON,
        "sources": list(DOC_SOURCES),
        "endpoints": [_endpoint_payload(doc) for doc in endpoints],
    }


def _endpoint_payload(doc: EndpointDoc) -> dict[str, Any]:
    return {
        "command": doc.command,
        "cli_usage": doc.cli_usage,
        "http_method": doc.http_method,
        "http_path": doc.http_path,
        "purpose": doc.purpose,
        "path_parameters": list(doc.path_parameters),
        "query_parameters": list(doc.query_parameters),
        "response_shape": doc.response_shape,
        "result_shape": doc.result_shape,
        "notes": list(doc.notes),
        "example_queries": list(doc.example_queries),
        "observed_examples": list(doc.observed_examples),
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# BacDive CLI Endpoint Documentation")
    lines.append("")
    lines.append("## Provenance")
    lines.append("")
    lines.append(f"- observed_on: {payload['observed_on']}")
    lines.append("- sources:")
    for source in payload["sources"]:
        lines.append(f"  - {source}")
    for endpoint in payload["endpoints"]:
        lines.append("")
        lines.append(f"## Endpoint: {endpoint['command']}")
        lines.append("")
        lines.append(f"- cli_usage: `{endpoint['cli_usage']}`")
        lines.append(f"- http_method: `{endpoint['http_method']}`")
        lines.append(f"- http_path: `{endpoint['http_path']}`")
        lines.append(f"- purpose: {endpoint['purpose']}")
        lines.append("- path_parameters:")
        for item in endpoint["path_parameters"]:
            lines.append(f"  - {item}")
        lines.append("- query_parameters:")
        for item in endpoint["query_parameters"]:
            lines.append(f"  - {item}")
        lines.append(f"- response_shape: {endpoint['response_shape']}")
        lines.append(f"- result_shape: {endpoint['result_shape']}")
        lines.append("- notes:")
        for item in endpoint["notes"]:
            lines.append(f"  - {item}")
        lines.append("- example_queries:")
        for item in endpoint["example_queries"]:
            lines.append(f"  - `{item}`")
        lines.append("- observed_examples:")
        for item in endpoint["observed_examples"]:
            lines.append(f"  - {item}")
    lines.append("")
    return "\n".join(lines)
