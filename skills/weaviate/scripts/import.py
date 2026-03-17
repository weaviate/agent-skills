#!/usr/bin/env python3
# /// script
# dependencies = [
#   "weaviate-client>=4.19.2",
#   "typer>=0.21.0",
#   "pdf2image>=1.17.0",
#   "pillow>=10.0.0",
# ]
# ///
"""
Import data from CSV, JSON, JSONL, or PDF files to a Weaviate collection.

Usage:
    uv run import.py data.csv --collection "CollectionName" [options]
    uv run import.py document.pdf --collection "CollectionName" [options]

Environment Variables:
    WEAVIATE_URL: Weaviate Cloud cluster URL
    WEAVIATE_API_KEY: API key for authentication
    + Any provider API keys (OPENAI_API_KEY, COHERE_API_KEY, etc.) - auto-detected
"""

import base64
import csv
import json
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}$")
_RESERVED_FIELDS = {"id", "_additional"}

from pdf2image import convert_from_path

import typer
import weaviate
from weaviate.classes.config import Configure, DataType, Property

# Import shared connection utilities (local to this skill)
from weaviate_conn import get_client

app = typer.Typer()


def detect_file_format(file_path: Path) -> str:
    """
    Detect file format based on extension.

    Args:
        file_path: Path to the file

    Returns:
        File format: "csv", "json", or "jsonl"

    Raises:
        ValueError: If file format is not supported
    """
    extension = file_path.suffix.lower()

    if extension == ".csv":
        return "csv"
    elif extension == ".json":
        return "json"
    elif extension == ".jsonl":
        return "jsonl"
    elif extension == ".pdf":
        return "pdf"
    else:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            f"Supported formats: .csv, .json, .jsonl, .pdf"
        )


def read_csv(
    file_path: Path, mapping: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    """
    Read data from CSV file with automatic dialect detection.

    Args:
        file_path: Path to CSV file
        mapping: Optional column name mapping

    Returns:
        List of dictionaries with data
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        # Read a sample to detect the CSV dialect
        sample = f.read(8192)
        f.seek(0)

        # Use Sniffer to detect the dialect (delimiter, quoting, etc.)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
            has_header = sniffer.has_header(sample)
        except csv.Error:
            # Fall back to default dialect if detection fails
            dialect = csv.excel
            has_header = True

        # Read the CSV with detected dialect
        if has_header:
            reader = csv.DictReader(f, dialect=dialect)
        else:
            # If no header detected, use default field names
            f.seek(0)
            reader_base = csv.reader(f, dialect=dialect)
            first_row = next(reader_base)
            fieldnames = [f"column_{i + 1}" for i in range(len(first_row))]
            f.seek(0)
            reader = csv.DictReader(f, fieldnames=fieldnames, dialect=dialect)
            next(reader)  # Skip first row since it's data, not header

        for row in reader:
            # Apply mapping if provided
            if mapping:
                row = {mapping.get(k, k): v for k, v in row.items()}
            data.append(row)
    return data


def read_json(
    file_path: Path, mapping: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    """
    Read data from JSON file (expects array of objects).

    Args:
        file_path: Path to JSON file
        mapping: Optional key name mapping

    Returns:
        List of dictionaries with data

    Raises:
        ValueError: If JSON is not an array
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"JSON file must contain an array of objects, got {type(data).__name__}"
        )

    # Apply mapping if provided
    if mapping:
        data = [{mapping.get(k, k): v for k, v in obj.items()} for obj in data]

    return data


def read_jsonl(
    file_path: Path, mapping: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    """
    Read data from JSONL file (one JSON object per line).

    Args:
        file_path: Path to JSONL file
        mapping: Optional key name mapping

    Returns:
        List of dictionaries with data
    """
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Apply mapping if provided
                if mapping:
                    obj = {mapping.get(k, k): v for k, v in obj.items()}
                data.append(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}")

    return data


def read_pdf(file_path: Path, image_field: str = "doc_page") -> list[dict[str, Any]]:
    """
    Convert each page of a PDF to a base64-encoded JPEG and return as objects.

    Each page becomes one Weaviate object with the base64 image stored in
    `image_field`, plus `page_number` and `file_name` metadata properties.

    Args:
        file_path: Path to the PDF file
        image_field: Name of the BLOB property to store the base64 image

    Returns:
        List of dicts with image_field, page_number, and file_name keys

    Raises:
        RuntimeError: If poppler is not installed
    """
    try:
        pages = convert_from_path(str(file_path))
    except Exception as e:
        if "poppler" in str(e).lower() or "pdftoppm" in str(e).lower():
            raise RuntimeError(
                f"Poppler is not installed or not in PATH. "
                f"Install it with:\n"
                f"  macOS:         brew install poppler\n"
                f"  Ubuntu/Debian: sudo apt-get install poppler-utils\n"
                f"Original error: {e}"
            )
        raise

    data = []
    for page_num, page_img in enumerate(pages, 1):
        buffer = BytesIO()
        page_img.save(buffer, format="JPEG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        data.append(
            {
                image_field: img_base64,
                "page_number": page_num,
                "file_name": file_path.stem,
            }
        )
    return data


def create_pdf_collection(
    client: weaviate.WeaviateClient, name: str, image_field: str
) -> None:
    """
    Create a Weaviate collection with the standard multimodal PDF schema.

    Properties: image_field (BLOB), page_number (INT), file_name (TEXT)
    Vectorizer: multi2vec_weaviate with ModernVBERT/colmodernvbert + MUVERA encoding

    Args:
        client: Connected Weaviate client
        name: Collection name
        image_field: Name of the BLOB property to store base64 page images
    """
    client.collections.create(
        name=name,
        properties=[
            Property(name=image_field, data_type=DataType.BLOB),
            Property(name="page_number", data_type=DataType.INT),
            Property(name="file_name", data_type=DataType.TEXT),
        ],
        vector_config=[
            Configure.MultiVectors.multi2vec_weaviate(
                name="doc_vector",
                image_field=image_field,
                model="ModernVBERT/colmodernvbert",
                encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(
                    ksim=4,
                    dprojections=16,
                    repetitions=20,
                ),
            )
        ],
    )


def convert_types(obj: dict[str, Any]) -> dict[str, Any]:
    """
    Convert string values to appropriate types where possible.

    Args:
        obj: Dictionary with potentially string values

    Returns:
        Dictionary with converted types
    """
    result = {}
    for key, value in obj.items():
        if value is None or value == "":
            # Skip None and empty strings
            continue

        # If already not a string, keep as is
        if not isinstance(value, str):
            result[key] = value
            continue

        # Try to convert string values
        # Check for boolean
        if value.lower() in ("true", "false"):
            result[key] = value.lower() == "true"
        # Check for numbers
        elif value.isdigit():
            result[key] = int(value)
        elif value.replace(".", "", 1).replace("-", "", 1).isdigit():
            try:
                result[key] = float(value)
            except ValueError:
                result[key] = value
        # Normalize date strings to RFC3339
        elif _DATE_RE.match(value):
            result[key] = f"{value}T00:00:00Z"
        elif _DATETIME_RE.match(value):
            result[key] = value.replace(" ", "T") + "Z"
        else:
            result[key] = value

    return result


@app.command()
def main(
    file: str = typer.Argument(..., help="Path to CSV, JSON, JSONL, or PDF file"),
    collection: str = typer.Option(
        ..., "--collection", "-c", help="Target collection name"
    ),
    mapping: str = typer.Option(
        None,
        "--mapping",
        "-m",
        help="JSON object mapping file columns/keys to properties",
    ),
    tenant: str = typer.Option(
        None, "--tenant", "-t", help="Tenant name for multi-tenant collections"
    ),
    batch_size: int = typer.Option(
        100, "--batch-size", "-b", help="Number of objects per batch"
    ),
    image_field: str = typer.Option(
        "doc_page",
        "--image-field",
        "-i",
        help="BLOB property name to store base64 page images (PDF imports only)",
    ),
    skip_fields: str = typer.Option(
        None,
        "--skip-fields",
        help="Comma-separated field names to exclude from import (e.g. 'id,created_at')",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Import data from CSV, JSON, JSONL, or PDF files to a Weaviate collection."""
    try:
        # Validate file path
        file_path = Path(file)
        if not file_path.exists():
            print(f"Error: File not found: {file}", file=sys.stderr)
            raise typer.Exit(1)

        # Parse mapping if provided
        mapping_dict = None
        if mapping:
            try:
                mapping_dict = json.loads(mapping)
                if not isinstance(mapping_dict, dict):
                    raise ValueError("Mapping must be a JSON object")
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in mapping: {e}", file=sys.stderr)
                raise typer.Exit(1)

        # Parse skip_fields
        skip_set: set[str] = (
            {f.strip() for f in skip_fields.split(",")} if skip_fields else set()
        )

        # Validate batch size
        if batch_size < 1:
            print("Error: Batch size must be at least 1", file=sys.stderr)
            raise typer.Exit(1)

        # Detect file format
        try:
            file_format = detect_file_format(file_path)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            raise typer.Exit(1)

        print(f"Detected file format: {file_format.upper()}", file=sys.stderr)
        print(f"Reading file: {file_path}", file=sys.stderr)

        # Read data based on format
        try:
            if file_format == "csv":
                data = read_csv(file_path, mapping_dict)
            elif file_format == "json":
                data = read_json(file_path, mapping_dict)
            elif file_format == "jsonl":
                data = read_jsonl(file_path, mapping_dict)
            elif file_format == "pdf":
                data = read_pdf(file_path, image_field)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            raise typer.Exit(1)

        if not data:
            print("Error: No data found in file", file=sys.stderr)
            raise typer.Exit(1)

        print(f"Loaded {len(data)} objects from file", file=sys.stderr)

        # Warn about reserved Weaviate fields before connecting
        if file_format != "pdf" and data:
            reserved_found = set(data[0].keys()) & _RESERVED_FIELDS - skip_set
            if reserved_found:
                print(
                    f"Warning: Reserved Weaviate field(s) detected in data: "
                    f"{', '.join(sorted(reserved_found))}. "
                    f"These will cause import failures. "
                    f"Use --skip-fields to exclude or --mapping to rename them.",
                    file=sys.stderr,
                )

        # Connect to Weaviate
        with get_client() as client:
            if file_format == "pdf":
                # PDF always creates a new collection
                if client.collections.exists(collection):
                    print(
                        f"Error: Collection '{collection}' already exists. "
                        f"Use a different name.",
                        file=sys.stderr,
                    )
                    raise typer.Exit(1)
                print(
                    f"Creating collection '{collection}' with multimodal PDF schema...",
                    file=sys.stderr,
                )
                create_pdf_collection(client, collection, image_field)
                print(f"Collection '{collection}' created.", file=sys.stderr)
            else:
                # CSV/JSON/JSONL require an existing collection
                if not client.collections.exists(collection):
                    print(
                        f"Error: Collection '{collection}' does not exist. "
                        f"Read `weaviate` skill's `create_collection.md` reference to create it first.",
                        file=sys.stderr,
                    )
                    raise typer.Exit(1)

            # Get collection reference
            coll = client.collections.get(collection)

            # Check if collection is multi-tenant
            config = coll.config.get()
            is_multi_tenant = (
                config.multi_tenancy_config.enabled
                if config.multi_tenancy_config
                else False
            )

            # Validate tenant parameter
            if is_multi_tenant and not tenant:
                print(
                    f"Error: Collection '{collection}' is multi-tenant, "
                    f"--tenant parameter is required",
                    file=sys.stderr,
                )
                raise typer.Exit(1)
            elif not is_multi_tenant and tenant:
                print(
                    f"Warning: Collection '{collection}' is not multi-tenant, "
                    f"--tenant parameter will be ignored",
                    file=sys.stderr,
                )
                tenant = None

            # Get tenant-specific collection if needed
            if tenant:
                coll = coll.with_tenant(tenant)
                print(f"Using tenant: {tenant}", file=sys.stderr)

            # Import data in batches
            print(
                f"Importing {len(data)} objects in batches of {batch_size}...",
                file=sys.stderr,
            )

            imported_count = 0
            failed_count = 0
            errors = []

            with coll.batch.dynamic() as batch:
                for i, obj in enumerate(data, 1):
                    try:
                        # Convert types and drop skipped fields
                        converted_obj = convert_types(obj)
                        if skip_set:
                            converted_obj = {
                                k: v
                                for k, v in converted_obj.items()
                                if k not in skip_set
                            }

                        # Add object to batch
                        batch.add_object(properties=converted_obj)
                        imported_count += 1

                        # Show progress
                        if i % batch_size == 0:
                            print(
                                f"Progress: {i}/{len(data)} objects processed",
                                file=sys.stderr,
                            )

                    except Exception as e:
                        failed_count += 1
                        error_msg = f"Object {i}: {str(e)}"
                        errors.append(error_msg)
                        if len(errors) <= 5:
                            print(f"Warning: {error_msg}", file=sys.stderr)

            # Check for server-side failures
            for failed_obj in coll.batch.failed_objects:
                failed_count += 1
                if len(errors) < 10:
                    errors.append(f"Batch error: {failed_obj.message}")

            success_count = imported_count - failed_count

            result = {
                "collection": collection,
                "tenant": tenant,
                "total_objects": len(data),
                "imported": success_count,
                "failed": failed_count,
                "file": str(file_path),
                "format": file_format,
            }
            if file_format == "pdf":
                result["image_field"] = image_field

            if errors:
                result["errors"] = errors[:10]  # Limit errors in output

            if json_output:
                print(json.dumps(result, indent=2))
            else:
                print(f"\n✓ Import completed!", file=sys.stderr)
                print(f"\n**Collection:** {collection}")
                if tenant:
                    print(f"**Tenant:** {tenant}")
                print(f"**Total Objects:** {len(data)}")
                print(f"**Successfully Imported:** {success_count}")
                if failed_count > 0:
                    print(f"**Failed:** {failed_count}")
                    if errors:
                        print(f"\n**Sample Errors:**")
                        for error in errors[:5]:
                            print(f"  - {error}")

            # Exit with error code if any imports failed
            if failed_count > 0:
                raise typer.Exit(1)

    except weaviate.exceptions.WeaviateConnectionError as e:
        print(f"Error: Connection failed - {e}", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
