#!/usr/bin/env python3
# /// script
# dependencies = [
#   "weaviate-client>=4.19.2",
#   "typer>=0.21.0",
# ]
# ///
"""
Get detailed configuration of a Weaviate collection.

Usage:
    uv run get_collection.py --name CollectionName [--json]

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
    name: str = typer.Option(..., "--name", "-n", help="Collection name"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Get detailed configuration of a Weaviate collection."""

    url, api_key = validate_env()

    try:
        print(f"Connecting to Weaviate...", file=sys.stderr)
        with weaviate.connect_to_weaviate_cloud(
            cluster_url=url,
            auth_credentials=Auth.api_key(api_key),
        ) as client:
            if not client.collections.exists(name):
                print(f"Error: Collection '{name}' not found.", file=sys.stderr)
                raise typer.Exit(1)

            print(f"Fetching config for '{name}'...", file=sys.stderr)
            collection = client.collections.use(name)
            config = collection.config.get()

            config_dict = {
                "name": config.name,
                "description": config.description,
                "vectorizer": str(config.vectorizer),
                "properties": [
                    {
                        "name": p.name,
                        "data_type": str(p.data_type),
                        "description": p.description,
                    }
                    for p in config.properties
                ],
                "replication_config": {
                    "factor": config.replication_config.factor
                    if config.replication_config
                    else None
                },
                "multi_tenancy_config": {
                    "enabled": config.multi_tenancy_config.enabled
                    if config.multi_tenancy_config
                    else False
                },
            }

            if json_output:
                print(json.dumps(config_dict, indent=2, default=str))
            else:
                print(f"## Collection: {name}\n")
                if config.description:
                    print(f"**Description**: {config.description}\n")

                print(f"**Vectorizer**: {config.vectorizer or 'None'}\n")

                print("### Properties\n")
                print("| Name | Data Type | Description |")
                print("|------|-----------|-------------|")
                for p in config.properties:
                    print(f"| {p.name} | {p.data_type} | {p.description or 'N/A'} |")

                if config.replication_config:
                    print(
                        f"\n**Replication Factor**: {config.replication_config.factor}"
                    )

                if config.multi_tenancy_config:
                    print(
                        f"**Multi-tenancy**: {'Enabled' if config.multi_tenancy_config.enabled else 'Disabled'}"
                    )

    except weaviate.exceptions.WeaviateConnectionError as e:
        print(f"Error: Connection failed - {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
