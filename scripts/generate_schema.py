#!/usr/bin/env python3
"""
Generate JSON schemas for the API contracts.

This script exports the Pydantic schemas for the decision engine API payloads
to a JSON file so that external teams and consumers can auto-generate their clients.
"""

import json
import os
from pathlib import Path
from pydantic.json_schema import models_json_schema
from src.schemas.state_snapshot import StateSnapshot
from src.schemas.action_list import ActionList

def generate_schemas():
    """Extract and write JSON schemas to file."""
    # Create the docs/api directory if it doesn't exist
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "schema.json"

    # Generate JSON schema for both top-level models
    _, top_level_schema = models_json_schema(
        [(StateSnapshot, "validation"), (ActionList, "validation")],
        title="GardenStation API Contracts"
    )

    with open(output_path, "w") as f:
        json.dump(top_level_schema, f, indent=2)

    print(f"Schema successfully generated at {output_path}")

if __name__ == "__main__":
    generate_schemas()
