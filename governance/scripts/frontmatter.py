"""Minimal, dependency-free frontmatter parser for sdd-gov.

The supported subset is deliberately small:

    ---
    key: value
    list: [one, two]
    block:
      - one
      - two
    ---

Nested maps are not supported. This keeps every parser implementation
identical across languages and removes PyYAML from the adoption path.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

STANDARD_ORDER = [
    "id",
    "title",
    "status",
    "layer",
    "epic",
    "owner",
    "trust_boundary",
    "size",
    "depends_on",
    "decision_refs",
    "issue_refs",
    "touches",
    "created",
    "updated",
    "superseded_by",
]


def _split_commas(value):
    parts = []
    buf = []
    quote = None
    for char in value:
        if quote:
            buf.append(char)
            if char == quote:
                quote = None
        elif char in ("'", '"'):
            quote = char
            buf.append(char)
        elif char == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
    if buf:
        parts.append("".join(buf).strip())
    return [part for part in parts if part != ""]


def parse_scalar(value):
    text = value.strip()
    if text == "" or text.lower() in ("null", "~"):
        return None
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        if text[0] == '"':
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text[1:-1]
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [] if inner == "" else [parse_scalar(item) for item in _split_commas(inner)]
    return text


def parse(text):
    """Return (mapping, body, errors) for a Markdown document."""
    if not text.startswith("---"):
        return {}, text, []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, []
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}, text, ["unterminated frontmatter"]

    data = {}
    errors = []
    duplicates = []
    index = 1
    while index < end:
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line.startswith("  - ") or line.startswith("- "):
            errors.append("line %d: list item without a key" % (index + 1))
            index += 1
            continue
        if ":" not in line:
            errors.append("line %d: missing colon" % (index + 1))
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in data:
            duplicates.append(key)
        if value == "":
            items = []
            cursor = index + 1
            while cursor < end and (
                lines[cursor].startswith("  - ") or lines[cursor].startswith("- ")
            ):
                items.append(parse_scalar(lines[cursor].split("-", 1)[1].strip()))
                cursor += 1
            data[key] = items
            index = cursor
        else:
            data[key] = parse_scalar(value)
            index += 1

    for key in duplicates:
        errors.append("duplicate key: %s" % key)
    body = "\n".join(lines[end + 1 :])
    return data, body, errors


def read(path):
    return parse(Path(path).read_text(encoding="utf-8"))


def format_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_scalar(item) for item in value) + "]"
    text = str(value)
    if text == "" or text.strip() != text or any(char in text for char in ":#[]{},"):
        return json.dumps(text, ensure_ascii=False)
    return text


def dump(data, body, order=None):
    order = order or STANDARD_ORDER
    keys = [key for key in order if key in data]
    keys += sorted(key for key in data if key not in keys)
    lines = ["---"]
    for key in keys:
        lines.append("%s: %s" % (key, format_scalar(data[key])))
    lines.append("---")
    if body and not body.startswith("\n"):
        lines.append("")
    return "\n".join(lines) + "\n" + body.lstrip("\n")
