#!/usr/bin/env python3
"""Verify the checked-in dataset release using only the Python standard library."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys

REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPOSITORY / "datasets" / "manifest.json"
CHUNK_BYTES = 1024 * 1024
DEFAULT_MAX_BYTES = 25 * 1024 * 1024
DEFAULT_FORBIDDEN_COLUMNS = {"label", "gold_label", "ground_truth", "matched_label"}


class DatasetError(ValueError):
    """Invalid manifest or release file."""


def safe_path(root: Path, relative: str) -> Path:
    """Resolve a portable relative path without allowing escape or symlinks."""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise DatasetError(f"Invalid relative path: {relative!r}")
    parts = PurePosixPath(relative)
    if parts.is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise DatasetError(f"Unsafe relative path: {relative!r}")
    candidate = root.joinpath(*parts.parts)
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise DatasetError(f"Path escapes its root: {relative!r}") from exc
    current = candidate
    while current != root and current != current.parent:
        if current.is_symlink():
            raise DatasetError(f"Symlink is not allowed: {relative!r}")
        current = current.parent
    return candidate


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_encoding(record: dict) -> str:
    encoding = record.get("encoding", "gzip" if record["path"].endswith(".gz") else "identity")
    if encoding not in {"identity", "gzip"}:
        raise DatasetError(f"Unsupported encoding {encoding!r} for {record['path']}")
    return encoding


def open_payload(path: Path, record: dict):
    return gzip.open(path, "rb") if file_encoding(record) == "gzip" else path.open("rb")


def read_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        manifest = json.load(stream)
    if not isinstance(manifest, dict) or manifest.get("schema_version", 1) != 1:
        raise DatasetError(f"Unsupported manifest schema: {path}")
    records = manifest.get("files", manifest.get("shards", []))
    if not isinstance(records, list):
        raise DatasetError(f"Manifest files must be a list: {path}")
    return manifest


def manifest_records(manifest: dict) -> list[dict]:
    return manifest.get("files", manifest.get("shards", []))


def manifest_tree(path: Path) -> list[tuple[Path, dict]]:
    """Follow explicitly recorded nested manifests; paths are relative to each manifest."""
    result = []
    seen = set()

    def visit(current: Path):
        resolved = current.resolve()
        if resolved in seen:
            raise DatasetError(f"Repeated or cyclic nested manifest: {current}")
        seen.add(resolved)
        manifest = read_manifest(current)
        result.append((current, manifest))
        for record in manifest_records(manifest):
            if not isinstance(record, dict) or "path" not in record:
                raise DatasetError(f"Invalid file record in {current}")
            nested = record.get("nested_manifest", record.get("submanifest", False))
            if nested:
                visit(safe_path(current.parent, record["path"]))
        for relative in manifest.get("manifests", []):
            visit(safe_path(current.parent, relative))

    visit(path)
    return result


class HashingReader(io.RawIOBase):
    """Hash the uncompressed bytes while the CSV parser consumes the same stream."""

    def __init__(self, source):
        super().__init__()
        self.source = source
        self.digest = hashlib.sha256()
        self.bytes_read = 0

    def readable(self):
        return True

    def readinto(self, buffer):
        data = self.source.read(len(buffer))
        self.digest.update(data)
        self.bytes_read += len(data)
        buffer[:len(data)] = data
        return len(data)


def payload_expectations(record: dict) -> tuple[str | None, int | None]:
    digest = record.get("uncompressed_sha256")
    size = record.get("uncompressed_bytes")
    # When bytes were redacted, source_* describes provenance, not the published payload.
    if not record.get("privacy_redactions"):
        digest = digest or record.get("source_sha256")
        size = size if size is not None else record.get("source_bytes")
    return digest, size


def check_payload(path: Path, record: dict) -> tuple[int | None, list[str] | None]:
    is_csv = record.get("format") == "csv" or record["path"].lower().removesuffix(".gz").endswith(".csv")
    is_jsonl = record.get("format") in {"jsonl", "ndjson"} or record["path"].lower().removesuffix(".gz").endswith((".jsonl", ".ndjson"))
    rows, columns = None, None
    with open_payload(path, record) as source:
        hashed = HashingReader(source)
        buffer = io.BufferedReader(hashed, buffer_size=CHUNK_BYTES)
        if is_csv:
            with io.TextIOWrapper(buffer, encoding=record.get("text_encoding", "utf-8-sig"), newline="") as text_stream:
                reader = csv.reader(text_stream, delimiter=record.get("delimiter", ","))
                columns = next(reader, None)
                if columns is None:
                    raise DatasetError(f"CSV has no header: {path}")
                rows = 0
                for row in reader:
                    if len(row) != len(columns):
                        raise DatasetError(f"CSV row {rows + 2} has {len(row)} fields; expected {len(columns)}: {path}")
                    rows += 1
        elif is_jsonl:
            rows = 0
            keys = set()
            with io.TextIOWrapper(buffer, encoding=record.get("text_encoding", "utf-8-sig"), newline="") as text_stream:
                for number, line in enumerate(text_stream, 1):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise DatasetError(f"JSONL row {number} must be an object: {path}")
                    keys.update(value)
                    rows += 1
            columns = sorted(keys)
        else:
            with buffer:
                while buffer.read(CHUNK_BYTES):
                    pass
        digest, size = payload_expectations(record)
        if digest is not None and hashed.digest.hexdigest() != digest:
            raise DatasetError(f"Uncompressed SHA-256 mismatch: {path}")
        if size is not None and hashed.bytes_read != size:
            raise DatasetError(f"Uncompressed size mismatch: {path} ({hashed.bytes_read} != {size})")
    if rows is not None:
        if "rows" in record and rows != record["rows"]:
            raise DatasetError(f"Row count mismatch: {path} ({rows} != {record['rows']})")
        expected_columns = sorted(record["columns"]) if is_jsonl and "columns" in record else record.get("columns")
        if expected_columns is not None and columns != expected_columns:
            raise DatasetError(f"CSV column names/order mismatch: {path}")
        if record.get("role") == "model_input":
            forbidden = DEFAULT_FORBIDDEN_COLUMNS | {str(name).casefold() for name in record.get("forbidden_columns", [])}
            leaked = [column for column in columns if column.casefold() in forbidden]
            if leaked:
                raise DatasetError(f"Gold/label columns found in model input {path}: {leaked}")
    return rows, columns


def verify_record(root: Path, record: dict, full: bool, max_bytes: int) -> None:
    path = safe_path(root, record["path"])
    if not path.is_file():
        raise DatasetError(f"Missing dataset file: {path}")
    size = path.stat().st_size
    if size > max_bytes:
        raise DatasetError(f"File exceeds {max_bytes} bytes: {path} ({size})")
    if "size_bytes" not in record or "sha256" not in record:
        raise DatasetError(f"File record needs size_bytes and sha256: {path}")
    if size != record["size_bytes"]:
        raise DatasetError(f"File size mismatch: {path} ({size} != {record['size_bytes']})")
    if digest_file(path) != record["sha256"]:
        raise DatasetError(f"SHA-256 mismatch: {path}")
    file_encoding(record)
    if full:
        check_payload(path, record)


def shard_header(manifest: dict) -> bytes:
    if "header_hex" in manifest:
        try:
            return bytes.fromhex(manifest["header_hex"])
        except ValueError as exc:
            raise DatasetError("Invalid header_hex in shard manifest") from exc
    if "header" in manifest:
        return manifest["header"].encode(manifest.get("text_encoding", "utf-8"))
    raise DatasetError("Shard reconstruction needs header_hex or header")


def reconstruction_chunks(root: Path, manifest: dict):
    """Yield original CSV bytes, discarding exactly the repeated header on later shards."""
    header = shard_header(manifest)
    for index, record in enumerate(manifest_records(manifest)):
        if record.get("nested_manifest") or not record["path"].lower().removesuffix(".gz").endswith(".csv"):
            raise DatasetError("A reconstructed CSV manifest can contain only ordered CSV shards")
        with open_payload(safe_path(root, record["path"]), record) as source:
            prefix = source.read(len(header))
            if prefix != header:
                raise DatasetError(f"Shard header does not match manifest: {record['path']}")
            if index == 0:
                yield prefix
            for chunk in iter(lambda: source.read(CHUNK_BYTES), b""):
                yield chunk


def reconstruction_expectations(manifest: dict) -> tuple[str | None, int | None]:
    return (manifest.get("full_source_sha256", manifest.get("source_sha256")),
            manifest.get("full_source_bytes", manifest.get("source_bytes")))


def is_sharded(manifest: dict) -> bool:
    return "reconstruction" in manifest and bool(manifest_records(manifest))


def verify_reconstruction(root: Path, manifest: dict) -> None:
    digest = hashlib.sha256()
    size = 0
    for chunk in reconstruction_chunks(root, manifest):
        digest.update(chunk)
        size += len(chunk)
    expected_digest, expected_size = reconstruction_expectations(manifest)
    if expected_digest is None or expected_size is None:
        raise DatasetError("Shard manifest needs full_source_sha256 and full_source_bytes")
    if digest.hexdigest() != expected_digest or size != expected_size:
        raise DatasetError(f"Reconstructed original hash/size mismatch: {root}")
    if "rows" in manifest and all("rows" in item for item in manifest_records(manifest)):
        total_rows = sum(item["rows"] for item in manifest_records(manifest))
        if total_rows != manifest["rows"]:
            raise DatasetError(f"Shard total row count mismatch: {root} ({total_rows} != {manifest['rows']})")


def verify_aliases(root: Path, manifest: dict) -> None:
    files = {item["path"]: item for item in manifest_records(manifest)}
    for alias in manifest.get("aliases", []):
        safe_path(root, alias.get("path"))
        canonical = alias.get("canonical_path")
        safe_path(root, canonical)
        if canonical not in files:
            raise DatasetError(f"Alias references an unmanifested canonical file: {canonical}")
        if canonical in files and alias.get("source_sha256") and files[canonical].get("source_sha256"):
            if alias["source_sha256"] != files[canonical]["source_sha256"]:
                raise DatasetError(f"Alias source digest differs from canonical file: {alias.get('path')}")
        if alias.get("source_bytes") is not None and files[canonical].get("source_bytes") is not None:
            if alias["source_bytes"] != files[canonical]["source_bytes"]:
                raise DatasetError(f"Alias source size differs from canonical file: {alias.get('path')}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--quick", action="store_true", help="Check packaged sizes/hashes only; skip payload/count/reconstruction checks")
    parser.add_argument("--max-file-mib", type=float, default=25, help="Maximum size of any checked-in release file (default: 25 MiB)")
    parser.add_argument("--check-repository-size", action="store_true", help="Also reject oversized repository files outside .git")
    args = parser.parse_args(argv)
    try:
        csv.field_size_limit(sys.maxsize)
        max_bytes = int(args.max_file_mib * 1024 * 1024)
        if max_bytes <= 0:
            raise DatasetError("--max-file-mib must be positive")
        tree = manifest_tree(args.manifest)
        count = 0
        for path, manifest in tree:
            for record in manifest_records(manifest):
                verify_record(path.parent, record, not args.quick, max_bytes)
                count += 1
                print(f"OK {record['path']}", flush=True)
            verify_aliases(path.parent, manifest)
            if is_sharded(manifest):
                if not args.quick:
                    verify_reconstruction(path.parent, manifest)
                elif "rows" in manifest and all("rows" in item for item in manifest_records(manifest)):
                    if sum(item["rows"] for item in manifest_records(manifest)) != manifest["rows"]:
                        raise DatasetError(f"Shard row totals disagree with manifest: {path}")
        if args.check_repository_size:
            for path in REPOSITORY.rglob("*"):
                if ".git" in path.relative_to(REPOSITORY).parts or not path.is_file():
                    continue
                if path.stat().st_size > max_bytes:
                    raise DatasetError(f"Repository file exceeds {max_bytes} bytes: {path}")
        mode = "packaged hashes" if args.quick else "packaged and payload hashes, CSV schemas/counts, reconstruction"
        print(f"Verified {count} file records in {len(tree)} manifests ({mode}).")
        return 0
    except (DatasetError, OSError, UnicodeError, csv.Error, json.JSONDecodeError, EOFError) as exc:
        print(f"Dataset verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
