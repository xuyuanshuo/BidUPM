#!/usr/bin/env python3
"""Restore packaged dataset bytes and optionally extract safe ZIP/TAR archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
import zipfile

from verify_datasets import (
    CHUNK_BYTES, DEFAULT_MANIFEST, DEFAULT_MAX_BYTES, REPOSITORY, DatasetError, digest_file, file_encoding,
    is_sharded, manifest_records, manifest_tree, open_payload, payload_expectations,
    reconstruction_chunks, reconstruction_expectations, safe_path, verify_aliases, verify_record,
)


def atomic_restore(destination: Path, chunks, expected_digest=None, expected_size=None, overwrite=False):
    if destination.exists() and not overwrite:
        raise DatasetError(f"Output already exists; use --overwrite to replace it: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest, size = hashlib.sha256(), 0
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".bidupm-", delete=False) as stream:
            temporary = Path(stream.name)
            for chunk in chunks:
                stream.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        if expected_digest is not None and digest.hexdigest() != expected_digest:
            raise DatasetError(f"Restored SHA-256 mismatch: {destination}")
        if expected_size is not None and size != expected_size:
            raise DatasetError(f"Restored size mismatch: {destination}")
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def file_chunks(path: Path, record: dict):
    with open_payload(path, record) as stream:
        yield from iter(lambda: stream.read(CHUNK_BYTES), b"")


def checked_members(names, output: Path):
    """Validate every member before writing, including duplicate destination paths."""
    paths = {}
    for name in names:
        clean = name.rstrip("/")
        if not clean:
            continue
        target = safe_path(output, clean)
        if target in paths.values():
            raise DatasetError(f"Archive contains duplicate path: {name!r}")
        paths[name] = target
    return paths


def extract_archive(archive: Path, output: Path, overwrite: bool, max_expanded_bytes: int):
    """Extract ordinary files/directories only; reject traversal, links and special files."""
    output.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as source:
            members = source.infolist()
            paths = checked_members((member.filename for member in members), output)
            if sum(member.file_size for member in members) > max_expanded_bytes:
                raise DatasetError(f"Archive exceeds the expanded-size limit: {archive}")
            for member in members:
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}):
                    raise DatasetError(f"Archive links/special files are not supported: {member.filename}")
                destination = paths.get(member.filename)
                if destination is None:
                    continue
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    with source.open(member) as stream:
                        atomic_restore(destination, iter(lambda: stream.read(CHUNK_BYTES), b""), expected_size=member.file_size, overwrite=overwrite)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive, "r:*") as source:
            members = source.getmembers()
            paths = checked_members((member.name for member in members), output)
            if sum(member.size for member in members if member.isfile()) > max_expanded_bytes:
                raise DatasetError(f"Archive exceeds the expanded-size limit: {archive}")
            if any(not member.isfile() and not member.isdir() for member in members):
                raise DatasetError(f"Archive links/special files are not supported: {archive}")
            for member in members:
                destination = paths.get(member.name)
                if destination is None:
                    continue
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    with source.extractfile(member) as stream:
                        atomic_restore(destination, iter(lambda: stream.read(CHUNK_BYTES), b""), expected_size=member.size, overwrite=overwrite)
    else:
        raise DatasetError(f"Unsupported archive format: {archive}")


def restore_transport(directory: Path, repository: Path, overwrite: bool, max_expanded_bytes: int) -> int:
    """Restore repository-relative dataset members from hash-indexed transport ZIPs."""
    manifest_path = directory / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as stream:
        manifest = json.load(stream)
    archives = manifest.get("archives")
    if not isinstance(archives, list) or not archives:
        raise DatasetError(f"Transport manifest has no archives: {manifest_path}")
    restored = 0
    all_paths = set()
    for record in archives:
        archive = safe_path(directory, record["path"])
        if archive.stat().st_size != record["size_bytes"] or digest_file(archive) != record["sha256"]:
            raise DatasetError(f"Transport archive hash/size mismatch: {archive}")
        if archive.stat().st_size > DEFAULT_MAX_BYTES:
            raise DatasetError(f"Transport archive exceeds 25 MiB: {archive}")
        expected = {}
        for member in record["members"]:
            relative = member["path"]
            safe_path(repository, relative)
            if not relative.startswith("datasets/"):
                raise DatasetError(f"Transport member must be beneath datasets/: {relative}")
            if relative in expected or relative in all_paths:
                raise DatasetError(f"Duplicate transport member: {relative}")
            expected[relative] = member
            all_paths.add(relative)
        with zipfile.ZipFile(archive) as source:
            members = source.infolist()
            checked_members((member.filename for member in members), repository)
            if {member.filename for member in members} != set(expected):
                raise DatasetError(f"Transport archive contents differ from manifest: {archive}")
            if sum(member.file_size for member in members) > max_expanded_bytes:
                raise DatasetError(f"Transport archive exceeds expanded-size limit: {archive}")
            for member in members:
                mode = member.external_attr >> 16
                if member.is_dir() or stat.S_ISLNK(mode) or stat.S_IFMT(mode) not in {0, stat.S_IFREG}:
                    raise DatasetError(f"Transport member must be a regular file: {member.filename}")
                metadata = expected[member.filename]
                if member.file_size != metadata["size_bytes"]:
                    raise DatasetError(f"Transport member size mismatch: {member.filename}")
                destination = safe_path(repository, member.filename)
                if destination.is_file() and destination.stat().st_size == metadata["size_bytes"] and digest_file(destination) == metadata["sha256"]:
                    continue
                with source.open(member) as stream:
                    atomic_restore(destination, iter(lambda: stream.read(CHUNK_BYTES), b""), metadata["sha256"], metadata["size_bytes"], overwrite)
                restored += 1
        print(f"Restored transport archive {record['path']}", flush=True)
    return restored


def materialize_aliases(manifest_path: Path, manifest: dict, package_root: Path,
                        output: Path, matches, overwrite: bool) -> int:
    """Restore logical duplicate-source paths from verified canonical payloads."""
    verify_aliases(manifest_path.parent, manifest)
    records = {record["path"]: record for record in manifest_records(manifest)}
    relative_root = manifest_path.parent.resolve().relative_to(package_root.resolve()).as_posix()
    relative_root = "" if relative_root == "." else relative_root
    restored = 0
    for alias in manifest.get("aliases", []):
        logical = "/".join(part for part in (relative_root, alias["path"]) if part)
        if not matches(logical, alias):
            continue
        canonical = records[alias["canonical_path"]]
        verify_record(manifest_path.parent, canonical, False, DEFAULT_MAX_BYTES)
        expected_digest = alias.get("source_sha256")
        if not isinstance(expected_digest, str) or len(expected_digest) != 64:
            raise DatasetError(f"Alias needs a source SHA-256: {alias['path']}")
        _, payload_size = payload_expectations(canonical)
        expected_size = alias.get("source_bytes", payload_size)
        # Aliases describe original logical names; remove a packaging suffix only.
        name = alias.get("materialized_path", alias["path"].removesuffix(".gz"))
        destination_name = "/".join(part for part in (relative_root, name) if part)
        destination = safe_path(output, destination_name)
        source = safe_path(manifest_path.parent, canonical["path"])
        atomic_restore(destination, file_chunks(source, canonical), expected_digest, expected_size, overwrite)
        restored += 1
        print(f"Restored alias {destination_name}", flush=True)
    return restored


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Destination outside the packaged datasets (default: ./data)")
    parser.add_argument("--dataset", action="append", default=[], help="Dataset id or relative path prefix; repeat to select several")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing destination files")
    parser.add_argument("--restore-archives", type=Path, help="Restore hash-indexed transport ZIPs (usually data_archives) into the repository first")
    parser.add_argument("--restore-only", action="store_true", help="Restore transport files and verify packaged hashes; leave datasets compressed")
    parser.add_argument("--reconstruct-large", action="store_true", help="Also reconstruct the multi-gigabyte raw pair CSV (otherwise only explicit --dataset selection enables it)")
    parser.add_argument("--extract-archives", action="store_true", help="Also extract recorded ZIP/TAR archives into sibling directories")
    parser.add_argument("--max-expanded-gib", type=float, default=50, help="Expanded-size ceiling per archive (default: 50 GiB)")
    args = parser.parse_args(argv)
    try:
        if args.max_expanded_gib <= 0:
            raise DatasetError("--max-expanded-gib must be positive")
        if args.restore_only and not args.restore_archives:
            raise DatasetError("--restore-only requires --restore-archives")
        if args.restore_archives:
            restored_transport = restore_transport(args.restore_archives, REPOSITORY, args.overwrite, int(args.max_expanded_gib * 1024 ** 3))
            print(f"Restored {restored_transport} transport member files.", flush=True)
        tree = manifest_tree(args.manifest)
        if args.restore_only:
            for manifest_path, manifest in tree:
                for record in manifest_records(manifest):
                    verify_record(manifest_path.parent, record, False, DEFAULT_MAX_BYTES)
            print("Transport restore complete; packaged hashes and sizes verified.")
            return 0
        package_root = args.manifest.resolve().parent
        output = args.output_dir.resolve()
        try:
            output.relative_to(package_root)
        except ValueError:
            pass
        else:
            raise DatasetError("--output-dir must be outside the packaged datasets directory")
        selected = set(args.dataset)
        dataset_paths = {}
        for _, manifest in tree:
            for item in manifest.get("datasets", []):
                if "id" in item and "path" in item:
                    dataset_paths[item["id"]] = str(item["path"]).rstrip("/")
        prefixes = {dataset_paths.get(item, item).rstrip("/") for item in selected}

        def matches(relative, record=None):
            if not prefixes:
                return True
            return any(relative == prefix or relative.startswith(prefix + "/") for prefix in prefixes) or bool(record and record.get("dataset_id") in selected)

        restored = 0
        for manifest_path, manifest in tree:
            relative_root = manifest_path.parent.resolve().relative_to(package_root).as_posix()
            relative_root = "" if relative_root == "." else relative_root
            if is_sharded(manifest):
                name = manifest.get("reconstructed_path", manifest.get("source_filename", "full_pairs.csv"))
                relative = "/".join(part for part in (relative_root, name) if part)
                if not matches(relative, manifest):
                    continue
                if not args.reconstruct_large and not selected:
                    print(f"Skipped large reconstruction {relative}; use --dataset ncdot_raw or --reconstruct-large.", flush=True)
                    continue
                for record in manifest_records(manifest):
                    verify_record(manifest_path.parent, record, False, DEFAULT_MAX_BYTES)
                digest, size = reconstruction_expectations(manifest)
                if digest is None or size is None:
                    raise DatasetError(f"Shard manifest lacks reconstructed hash/size: {manifest_path}")
                atomic_restore(safe_path(output, relative), reconstruction_chunks(manifest_path.parent, manifest), digest, size, args.overwrite)
                restored += 1
                print(f"Restored {relative}", flush=True)
                continue
            for record in manifest_records(manifest):
                if record.get("nested_manifest", record.get("submanifest", False)):
                    continue
                relative = "/".join(part for part in (relative_root, record["path"]) if part)
                if not matches(relative, record):
                    continue
                verify_record(manifest_path.parent, record, False, DEFAULT_MAX_BYTES)
                name = record.get("materialized_path", record["path"].removesuffix(".gz") if file_encoding(record) == "gzip" else record["path"])
                output_relative = "/".join(part for part in (relative_root, name) if part)
                destination = safe_path(output, output_relative)
                digest, size = payload_expectations(record)
                if file_encoding(record) == "identity":
                    digest, size = record["sha256"], record["size_bytes"]
                atomic_restore(destination, file_chunks(safe_path(manifest_path.parent, record["path"]), record), digest, size, args.overwrite)
                restored += 1
                print(f"Restored {output_relative}", flush=True)
                archive_format = record.get("format", "")
                if args.extract_archives and (archive_format in {"zip", "tar", "archive"} or destination.suffix.lower() in {".zip", ".tar", ".tgz"}):
                    extraction = safe_path(output, output_relative + ".extracted")
                    extract_archive(destination, extraction, args.overwrite, int(args.max_expanded_gib * 1024 ** 3))
                    print(f"Extracted {extraction.relative_to(output)}", flush=True)
        for manifest_path, manifest in tree:
            restored += materialize_aliases(manifest_path, manifest, package_root, output, matches, args.overwrite)
        if restored == 0:
            raise DatasetError("No dataset files matched the requested selection")
        print(f"Restored {restored} files into {output}")
        return 0
    except (DatasetError, OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile, tarfile.TarError) as exc:
        print(f"Dataset materialization failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
