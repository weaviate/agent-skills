#!/usr/bin/env python3
# /// script
# dependencies = [
#   "weaviate-client==4.23.1",
#   "typer==0.21.0",
# ]
# ///
"""
Fetch and filter objects from a Weaviate collection.

Usage:
    # Fetch random 10 objects
    uv run fetch_filter.py "JeopardyQuestion"

    # Fetch by ID
    uv run fetch_filter.py "JeopardyQuestion" --id "uuid-string"

    # Filter with simple JSON
    uv run fetch_filter.py "JeopardyQuestion" --filters '[{"property": "round", "operator": "equal", "value": "Double Jeopardy!"}]'

Environment Variables:
    WEAVIATE_URL: Weaviate Cloud cluster URL
    WEAVIATE_API_KEY: API key for authentication
"""

import json
import sys
from typing import Any

import typer
import weaviate
from weaviate.classes.query import Filter

# Import shared connection utilities (local to this skill)
from weaviate_conn import get_client

app = typer.Typer()


class FilterError(ValueError):
    """Raised when a --filters JSON document is malformed or unsupported."""


_MISSING = object()

# operator name -> (Filter method name, value kind)
#   "any"  : any JSON value
#   "list" : must be a JSON array
#   "bool" : must be a JSON boolean
_PROPERTY_OPERATORS: dict[str, tuple[str, str]] = {
    "equal": ("equal", "any"),
    "not_equal": ("not_equal", "any"),
    "less_than": ("less_than", "any"),
    "less_or_equal": ("less_or_equal", "any"),
    "greater_than": ("greater_than", "any"),
    "greater_or_equal": ("greater_or_equal", "any"),
    "like": ("like", "any"),
    "contains_any": ("contains_any", "list"),
    "contains_all": ("contains_all", "list"),
    "contains_none": ("contains_none", "list"),
    "is_none": ("is_none", "bool"),
}


def _coerce_bool(op: str, prop: str, val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str) and val.strip().lower() in ("true", "false"):
        return val.strip().lower() == "true"
    raise FilterError(
        f"Operator '{op}' on property '{prop}' needs a boolean value "
        f"(true/false), got {val!r}."
    )


def parse_filter_item(item: Any, path: str = "filters") -> Filter:
    """
    Recursively parse a single filter item (dict or list) into a Filter.

    Supported structures:
    1. List of filters (implicit AND): [filter1, filter2]
    2. Explicit Logical Operators:
       {"operator": "and", "filters": [...]}
       {"operator": "or", "filters": [...]}
    3. Property Filter:
       {"property": "name", "operator": "equal", "value": "foo"}

    Fails closed: anything that cannot be turned into a real filter raises
    FilterError instead of being silently dropped. Dropping a clause would
    return a *different* result set than the one that was asked for while
    looking like a successful, filtered query.
    """
    if isinstance(item, list):
        if not item:
            raise FilterError(f"{path}: filter list is empty.")
        return Filter.all_of(
            [parse_filter_item(x, f"{path}[{i}]") for i, x in enumerate(item)]
        )

    if not isinstance(item, dict):
        raise FilterError(
            f"{path}: expected a filter object or list, got {type(item).__name__} "
            f"({item!r})."
        )

    op = item.get("operator")
    if not isinstance(op, str) or not op:
        raise FilterError(f"{path}: missing 'operator'.")

    # Logical operators
    if op in ("and", "or"):
        sub_items = item.get("filters")
        if not isinstance(sub_items, list) or not sub_items:
            raise FilterError(
                f"{path}: '{op}' needs a non-empty 'filters' array."
            )
        sub_filters = [
            parse_filter_item(x, f"{path}.{op}[{i}]") for i, x in enumerate(sub_items)
        ]
        return Filter.all_of(sub_filters) if op == "and" else Filter.any_of(sub_filters)

    # Property filter
    prop = item.get("property")
    if not isinstance(prop, str) or not prop:
        raise FilterError(f"{path}: missing 'property' for operator '{op}'.")

    if op not in _PROPERTY_OPERATORS:
        raise FilterError(
            f"{path}: unknown operator '{op}' for property '{prop}'. "
            f"Supported: and, or, {', '.join(_PROPERTY_OPERATORS)}."
        )

    val = item.get("value", _MISSING)
    if val is _MISSING:
        raise FilterError(f"{path}: operator '{op}' on '{prop}' needs a 'value'.")

    method_name, kind = _PROPERTY_OPERATORS[op]
    if kind == "list" and not isinstance(val, list):
        raise FilterError(
            f"{path}: operator '{op}' on '{prop}' needs a list value, "
            f"got {type(val).__name__}."
        )
    if kind == "bool":
        val = _coerce_bool(op, prop, val)

    return getattr(Filter.by_property(prop), method_name)(val)


def parse_filters(filter_json: str | None) -> Filter | None:
    """
    Parse a JSON string of filters into a Weaviate Filter object.

    Returns None only when no filter was requested (None/empty string or an
    explicit empty list). Any malformed filter raises FilterError.
    """
    if not filter_json:
        return None

    try:
        data = json.loads(filter_json)
    except json.JSONDecodeError as e:
        raise FilterError(f"Invalid JSON in --filters: {e}") from e

    if data == []:
        return None

    return parse_filter_item(data)


@app.command()
def main(
    collection_name: str = typer.Argument(..., help="Collection name"),
    obj_id: str = typer.Option(None, "--id", help="Fetch specific object by UUID"),
    filters: str = typer.Option(None, "--filters", "-f", help="JSON string of filters"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of objects to fetch"),
    properties: str = typer.Option(
        None,
        "--properties",
        "-p",
        help="Comma-separated properties to include (default: all)",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Fetch objects with optional filtering."""
    if obj_id and filters:
        print(
            "Error: --id and --filters cannot be combined; --id fetches a single "
            "object and would ignore the filters.",
            file=sys.stderr,
        )
        raise typer.Exit(1)

    # Validate filters before opening a connection so mistakes fail fast.
    try:
        weaviate_filter = parse_filters(filters)
    except FilterError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)

    try:
        with get_client() as client:
            if not client.collections.exists(collection_name):
                print(
                    f"Error: Collection '{collection_name}' not found.", file=sys.stderr
                )
                raise typer.Exit(1)

            collection = client.collections.use(collection_name)

            # Determine return properties
            return_properties = None
            if properties:
                return_properties = [
                    p.strip() for p in properties.split(",") if p.strip()
                ]

            results = []

            if obj_id:
                # Fetch single object by ID
                if not json_output:
                    print(f"Fetching object {obj_id}...", file=sys.stderr)

                obj = collection.query.fetch_object_by_id(obj_id)

                if obj:
                    results.append(obj)
                else:
                    print(f"Error: Object {obj_id} not found.", file=sys.stderr)
                    raise typer.Exit(1)

            else:
                # Fetch multiple with filters
                if not json_output:
                    print(
                        f"Fetching objects from '{collection_name}'...", file=sys.stderr
                    )

                response = collection.query.fetch_objects(
                    filters=weaviate_filter,
                    limit=limit,
                    return_properties=return_properties,
                )
                results = list(response.objects)

            # Output Formatting
            output_data = []
            for obj in results:
                item = {
                    "uuid": str(obj.uuid),
                    "properties": obj.properties,
                    "metadata": {
                        "creation_time": str(obj.metadata.creation_time)
                        if obj.metadata.creation_time
                        else None,
                    },
                }
                output_data.append(item)

            if json_output:
                print(json.dumps(output_data, indent=2, default=str))
            else:
                if not results:
                    print("No objects found.")
                else:
                    print(f"## Found {len(results)} Objects\n")

                    # Gather all property keys for the table headers
                    all_keys = set()
                    for item in output_data:
                        all_keys.update(item["properties"].keys())
                    sorted_keys = sorted(list(all_keys))

                    # Table Header
                    headers = ["UUID"] + sorted_keys
                    print("| " + " | ".join(headers) + " |")
                    print("| " + " | ".join(["---"] * len(headers)) + " |")

                    for item in output_data:
                        row = [str(item["uuid"])]
                        for k in sorted_keys:
                            val = item["properties"].get(k, "-")
                            val_str = str(val).replace("\n", " ").replace("|", "\\|")
                            if len(val_str) > 100:
                                val_str = val_str[:97] + "..."
                            row.append(val_str)
                        print("| " + " | ".join(row) + " |")

    except weaviate.exceptions.WeaviateConnectionError as e:
        print(f"Error: Connection failed - {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
