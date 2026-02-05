#!/usr/bin/env python3
# /// script
# dependencies = [
#   "weaviate-client>=4.19.2",
#   "weaviate-agents>=1.2.0",
#   "typer>=0.21.0",
# ]
# ///
"""
Query Weaviate using Query Agent in Search mode.

Usage:
    uv run search.py --query "your search" --collections "Collection1,Collection2" [--limit 10] [--json]

Environment Variables:
    WEAVIATE_URL: Weaviate Cloud cluster URL
    WEAVIATE_API_KEY: API key for authentication
    OPENAI_API_KEY: OpenAI API key (if collections use OpenAI embeddings)

Output:
    Retrieved objects in markdown format (or JSON with --json flag)
"""

import os
import sys
import json
import typer
import weaviate
from weaviate.classes.init import Auth
from weaviate.agents.query import QueryAgent

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


def parse_collections(collections_str: str) -> list[str]:
    """Parse comma-separated collection names."""
    collections = [c.strip() for c in collections_str.split(",") if c.strip()]
    if not collections:
        print("Error: At least one collection name required", file=sys.stderr)
        raise typer.Exit(1)
    return collections


@app.command()
def main(
    query: str = typer.Option(
        ..., "--query", "-q", help="Natural language search query"
    ),
    collections: str = typer.Option(
        ..., "--collections", "-c", help="Comma-separated collection names"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of results to return"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Query Weaviate using Query Agent in Search mode (retrieval only, no answer generation)."""

    url, api_key, openai_key = validate_env()
    collection_list = parse_collections(collections)

    try:
        headers = {"X-OpenAI-Api-Key": openai_key} if openai_key else None

        print("Connecting to Weaviate...", file=sys.stderr)
        with weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
            headers=headers,
        ) as client:
            agent = QueryAgent(client=client, collections=collection_list)

            print("Searching...", file=sys.stderr)
            response = agent.search(query, limit=limit)
            print("Done.", file=sys.stderr)

            # Extract objects from search results
            objects = []
            if hasattr(response, "search_results") and response.search_results:
                search_results = response.search_results
                if hasattr(search_results, "objects") and search_results.objects:
                    for obj in search_results.objects:
                        obj_data = {
                            "uuid": str(getattr(obj, "uuid", "")),
                            "collection": getattr(obj, "collection", None),
                            "properties": dict(getattr(obj, "properties", {})),
                        }
                        objects.append(obj_data)

            result = {
                "query": query,
                "collections": collection_list,
                "limit": limit,
                "objects": objects,
                "object_count": len(objects),
            }

            if json_output:
                print(json.dumps(result, indent=2, default=str))
            else:
                # Markdown output for agent consumption
                print(f"## Search Results\n")
                print(f"**Query:** {query}")
                print(f"**Collections:** {', '.join(collection_list)}")
                print(f"**Found:** {len(objects)} objects\n")

                if objects:
                    # Get all unique property keys
                    all_props = set()
                    for obj in objects:
                        all_props.update(obj.get("properties", {}).keys())

                    # Sort property keys for consistent display
                    sorted_props = sorted(list(all_props))

                    # Define headers
                    headers = ["#", "Full UUID", "Collection"] + sorted_props

                    # Create table header
                    header_row = "| " + " | ".join(headers) + " |"
                    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"

                    print(header_row)
                    print(separator_row)

                    for idx, obj in enumerate(objects, 1):
                        row_data = [
                            str(idx),
                            str(obj.get("uuid", "N/A")),  # Full UUID
                            obj.get("collection", "Unknown"),
                        ]

                        props = obj.get("properties", {})
                        for prop in sorted_props:
                            val = props.get(prop, "-")
                            val_str = str(val).replace("\n", " ").replace("|", "\\|")

                            # Only truncate if NOT 'content'
                            if prop.lower() != "content" and len(val_str) > 100:
                                val_str = val_str[:97] + "..."

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
