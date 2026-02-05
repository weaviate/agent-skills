#!/usr/bin/env python3
# /// script
# dependencies = [
#   "weaviate-client>=4.19.2",
#   "typer>=0.21.0",
# ]
# ///
"""
Hybrid search on a Weaviate collection (combines vector and keyword search).

Usage:
    uv run hybrid_search.py --query "your query" --collection "CollectionName" [--alpha 0.5] [--limit 10] [--json]

Environment Variables:
    WEAVIATE_URL: Weaviate Cloud cluster URL
    WEAVIATE_API_KEY: API key for authentication
    OPENAI_API_KEY: OpenAI API key (if collections use OpenAI embeddings)

Output:
    Search results with scores in markdown format (or JSON with --json flag)
"""

import os
import sys
import json
import typer
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery

app = typer.Typer()


def validate_env() -> tuple[str, str, str | None]:
    """Validate required environment variables."""
    url = os.environ.get("WEAVIATE_URL", "").strip()
    api_key = os.environ.get("WEAVIATE_API_KEY", "").strip()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip() or None

    if not url:
        print("Error: WEAVIATE_URL environment variable not set", file=sys.stderr)
        raise typer.Exit(1)

    if not api_key:
        print("Error: WEAVIATE_API_KEY environment variable not set", file=sys.stderr)
        raise typer.Exit(1)

    return url, api_key, openai_key


def parse_properties(properties_str: str | None) -> list[str] | None:
    """Parse comma-separated property names with optional boost."""
    if not properties_str:
        return None
    return [p.strip() for p in properties_str.split(",") if p.strip()]


@app.command()
def main(
    query: str = typer.Option(..., "--query", "-q", help="Search query text"),
    collection: str = typer.Option(..., "--collection", "-c", help="Collection name"),
    alpha: float = typer.Option(
        0.7,
        "--alpha",
        "-a",
        help="Balance: 1.0=vector only, 0.0=keyword only (default: 0.7)",
    ),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results to return"),
    properties: str = typer.Option(
        None, "--properties", "-p", help="Comma-separated properties to search"
    ),
    target_vector: str = typer.Option(
        None,
        "--target-vector",
        "-t",
        help="Target vector name for named vector collections",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Perform hybrid search (vector + keyword) on a Weaviate collection."""

    url, api_key, openai_key = validate_env()
    query_properties = parse_properties(properties)

    try:
        headers = {"X-OpenAI-Api-Key": openai_key} if openai_key else None

        print("Connecting to Weaviate...", file=sys.stderr)
        with weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
            headers=headers,
        ) as client:
            if not client.collections.exists(collection):
                print(f"Error: Collection '{collection}' not found.", file=sys.stderr)
                raise typer.Exit(1)

            coll = client.collections.use(collection)

            print("Searching...", file=sys.stderr)
            response = coll.query.hybrid(
                query=query,
                alpha=alpha,
                limit=limit,
                query_properties=query_properties,
                target_vector=target_vector,
                return_metadata=MetadataQuery(score=True, explain_score=True),
            )
            print("Done.", file=sys.stderr)

            objects = []
            for obj in response.objects:
                obj_data = {
                    "uuid": str(obj.uuid),
                    "properties": dict(obj.properties),
                    "score": obj.metadata.score if obj.metadata else None,
                    "explain_score": obj.metadata.explain_score
                    if obj.metadata
                    else None,
                }
                objects.append(obj_data)

            result = {
                "query": query,
                "collection": collection,
                "alpha": alpha,
                "limit": limit,
                "target_vector": target_vector,
                "objects": objects,
                "object_count": len(objects),
            }

            if json_output:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"## Hybrid Search Results\n")
                print(f"**Query:** {query}")
                print(f"**Collection:** {collection}")
                print(f"**Alpha:** {alpha} (1=vector, 0=keyword)")
                print(f"**Found:** {len(objects)} objects\n")

                if objects:
                    all_props = set()
                    for obj in objects:
                        all_props.update(obj.get("properties", {}).keys())
                    sorted_props = sorted(list(all_props))

                    headers = ["#", "UUID", "Score"] + sorted_props
                    header_row = "| " + " | ".join(headers) + " |"
                    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"

                    print(header_row)
                    print(separator_row)

                    for idx, obj in enumerate(objects, 1):
                        score = obj.get("score")
                        score_str = f"{score:.4f}" if score is not None else "N/A"
                        row_data = [
                            str(idx),
                            str(obj.get("uuid", "N/A")),
                            score_str,
                        ]

                        props = obj.get("properties", {})
                        for prop in sorted_props:
                            val = props.get(prop, "-")
                            val_str = str(val).replace("\n", " ").replace("|", "\\|")
                            row_data.append(val_str)

                        print("| " + " | ".join(row_data) + " |")
                    print()
                else:
                    print("No objects found matching the query.\n")

    except weaviate.exceptions.WeaviateConnectionError as e:
        print(f"Error: Connection failed - {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
