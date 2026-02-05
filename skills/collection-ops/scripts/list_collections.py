#!/usr/bin/env python3
# /// script
# dependencies = [
#   "weaviate-client>=4.19.2",
#   "typer>=0.21.0",
# ]
# ///
"""
List all Weaviate collections.

Usage:
    uv run list_collections.py [--json]

Environment Variables:
    WEAVIATE_URL: Weaviate Cloud cluster URL
    WEAVIATE_API_KEY: API key for authentication
"""

import os
import sys
import json
import typer
import weaviate
from weaviate.classes.init import Auth

app = typer.Typer()


def validate_env() -> tuple[str, str]:
    """Validate required environment variables."""
    url = os.environ.get("WEAVIATE_URL", "").strip()
    api_key = os.environ.get("WEAVIATE_API_KEY", "").strip()

    if not url:
        print("Error: WEAVIATE_URL environment variable not set", file=sys.stderr)
        raise typer.Exit(1)

    if not api_key:
        print("Error: WEAVIATE_API_KEY environment variable not set", file=sys.stderr)
        raise typer.Exit(1)

    return url, api_key


@app.command()
def main(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List all Weaviate collections."""

    url, api_key = validate_env()

    try:
        print("Connecting to Weaviate...", file=sys.stderr)
        with weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
        ) as client:
            print("Fetching collections...", file=sys.stderr)
            collections = client.collections.list_all(simple=False)
            print(f"Found {len(collections)} collections.", file=sys.stderr)

            if json_output:
                result = []
                for name, config in collections.items():
                    result.append({
                        "name": name,
                        "description": config.description,
                        "properties": [
                            {"name": p.name, "data_type": str(p.data_type)}
                            for p in config.properties
                        ]
                    })
                print(json.dumps(result, indent=2, default=str))
            else:
                if not collections:
                    print("No collections found.")
                else:
                    print("## Collections\n")
                    print("| Name | Description | Properties |")
                    print("|------|-------------|------------|")
                    for name, config in collections.items():
                        props = ", ".join([p.name for p in config.properties])
                        desc = config.description or "N/A"
                        print(f"| {name} | {desc} | {props} |")

    except weaviate.exceptions.WeaviateConnectionError as e:
        print(f"Error: Connection failed - {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
