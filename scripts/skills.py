#!/usr/bin/env python3
"""Build portable skill folders and deterministic, individual ZIP downloads."""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("codex", "claude")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
IGNORED = {"__pycache__", ".DS_Store"}


def inventory(directory: Path) -> dict[str, bytes]:
    """Never follow links out of a source or generated directory."""
    if directory.is_symlink():
        raise ValueError(f"Symlink is not a portable bundle: {directory}")
    result = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if any(part in IGNORED for part in relative.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink is not a portable bundle: {path}")
        if path.is_file():
            result[relative.as_posix()] = path.read_bytes()
    return result


def sources(root: Path, refresh_shared: bool = False) -> dict[str, Path]:
    parents = [root / "skills"]
    collections = root / "collections"
    if collections.is_symlink():
        raise ValueError(f"Collections root must not be a symlink: {collections}")
    if collections.exists():
        for collection in sorted(collections.iterdir()):
            if collection.is_symlink():
                raise ValueError(f"Collection must not be a symlink: {collection}")
            if (collection / "skills").exists():
                parents.append(collection / "skills")
    found = {}
    shared_updates = []
    for parent in parents:
        if parent.is_symlink():
            raise ValueError(f"Source root must not be a symlink: {parent}")
        if not parent.exists():
            continue
        shared = {}
        if parent != root / "skills":
            shared = inventory(parent.parent / "shared")
            license_file = parent.parent / "LICENSE"
            if license_file.is_symlink():
                raise ValueError(f"Collection license must not be a symlink: {license_file}")
            if license_file.is_file():
                shared["LICENSE"] = license_file.read_bytes()
        for path in sorted(parent.iterdir()):
            if not path.is_dir():
                continue
            if path.name in found:
                raise ValueError(f"Duplicate skill name: {path.name}")
            found[path.name] = path
            actual = inventory(path)
            for relative, data in shared.items():
                if actual.get(relative) != data:
                    if not refresh_shared:
                        raise ValueError(f"Shared resource out of sync: {path / relative}. "
                                         "Run python scripts/skills.py sync.")
                    shared_updates.append((path / relative, data))
    if not found:
        raise ValueError("No skills found")
    for name, path in found.items():
        if not NAME.fullmatch(name) or len(name) > 64 or name in {"synced", "anthropic-skills"}:
            raise ValueError(f"Invalid or reserved skill name: {name}")
    # Check all names and symlinks before updating shared resources in source copies.
    for file, data in shared_updates:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
    for path in found.values():
        validate(path)
    return found


def validate(path: Path) -> None:
    files = inventory(path)
    if "SKILL.md" not in files:
        raise ValueError(f"Missing {path}/SKILL.md")
    text = files["SKILL.md"].decode()
    match = re.fullmatch(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not match:
        raise ValueError(f"Missing YAML frontmatter: {path}")
    metadata = yaml.safe_load(match[1])
    required = {"name", "description"}
    supported = required | {"license", "compatibility", "metadata", "allowed-tools"}
    if not isinstance(metadata, dict) or not required <= metadata.keys() or metadata.keys() - supported:
        raise ValueError(f"Use portable Agent Skills frontmatter: {path}")
    description = metadata["description"]
    if metadata["name"] != path.name:
        raise ValueError(f"Directory and skill name differ: {path}")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise ValueError(f"Description must be 1–1024 characters: {path}")
    for field in ("license", "compatibility", "allowed-tools"):
        if field in metadata and (not isinstance(metadata[field], str) or not metadata[field].strip()):
            raise ValueError(f"{field} must be a nonempty string: {path}")
    if len(metadata.get("compatibility", "")) > 500:
        raise ValueError(f"compatibility must be at most 500 characters: {path}")
    extra = metadata.get("metadata", {})
    if not isinstance(extra, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                         for k, v in extra.items()):
        raise ValueError(f"metadata must map strings to strings: {path}")
    if len(match[2].splitlines()) >= 500 or not match[2].strip():
        raise ValueError(f"Keep the skill body nonempty and under 500 lines: {path}")
    if "!`" in text:
        raise ValueError(f"Keep dynamic shell expansion out of portable instructions: {path}")
    # Inline local links must survive copying this one directory in isolation.
    for name, data in files.items():
        if not name.endswith(".md"):
            continue
        for link in re.findall(r"\]\(([^)\s]+)\)", data.decode()):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (path / name).parent / unquote(parsed.path)
            if not destination.resolve().is_relative_to(path.resolve()) or not destination.exists():
                raise ValueError(f"Broken or external local link in {path / name}: {link}")
    print(f"{path.name}: description {len(description)} chars; body {len(match[2].split())} words")


def rendered(source: Path, target: str) -> dict[str, bytes]:
    files = inventory(source)
    # The only current product-specific resource is Codex's optional UI metadata.
    if target == "claude":
        files.pop("agents/openai.yaml", None)
    files.pop("SHA256SUMS", None)
    checksums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                        for name, data in sorted(files.items()))
    return files | {"SHA256SUMS": checksums.encode()}


def target_directory(root: Path, target: str) -> Path:
    directory = root / target
    if directory.is_symlink():
        raise ValueError(f"Refusing symlinked output root: {directory}")
    return directory


def check(root: Path, skills: dict[str, Path]) -> None:
    failures = []
    for target in TARGETS:
        parent = target_directory(root, target)
        if parent.exists():
            for entry in parent.iterdir():
                if entry.name not in skills and entry.name not in IGNORED:
                    failures.append(f"Unexpected generated entry: {entry}")
        for name, source in skills.items():
            expected = rendered(source, target)
            actual = inventory(parent / name)
            for file in sorted(expected.keys() | actual.keys()):
                if actual.get(file) != expected.get(file):
                    failures.append(f"Out of sync: {target}/{name}/{file}")
    if failures:
        raise ValueError("\n".join(failures) + "\nRun python scripts/skills.py sync.")
    print("Claude and Codex bundles match their sources.")


def sync(root: Path, skills: dict[str, Path]) -> None:
    # Preflight both trees before replacing any generated skill.
    for target in TARGETS:
        parent = target_directory(root, target)
        inventory(parent)
        if parent.exists():
            extra = {p.name for p in parent.iterdir()} - skills.keys() - IGNORED
            if extra:
                raise ValueError(f"Review/remove obsolete generated entries in {parent}: {sorted(extra)}")
    for target in TARGETS:
        for name, source in skills.items():
            destination = root / target / name
            if destination.exists():
                shutil.rmtree(destination)
            destination.mkdir(parents=True)
            for relative, data in rendered(source, target).items():
                file = destination / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
    check(root, skills)


def package(root: Path, skills: dict[str, Path], names: list[str], target: str) -> None:
    unknown = set(names) - skills.keys()
    if unknown:
        raise ValueError(f"Unknown skills: {sorted(unknown)}")
    check(root, skills)
    output = root / "dist"
    if output.is_symlink():
        raise ValueError("Refusing symlinked dist directory")
    output.mkdir(exist_ok=True)
    for name in names or skills:
        for product in TARGETS if target == "both" else (target,):
            archive = output / f"{name}-{product}.zip"
            if archive.is_symlink():
                raise ValueError(f"Refusing symlinked archive: {archive}")
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for relative, data in sorted(rendered(skills[name], product).items()):
                    entry = zipfile.ZipInfo(f"{name}/{relative}", date_time=(2020, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    bundle.writestr(entry, data)
            print(archive.relative_to(root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("sync", help="Regenerate both product trees; overwrites generated edits")
    sub.add_parser("check", help="Validate portable sources and detect generated drift")
    archive = sub.add_parser("package", help="Build one ZIP per selected skill and product")
    archive.add_argument("skills", nargs="*")
    archive.add_argument("--target", choices=(*TARGETS, "both"), default="both")
    args = parser.parse_args()
    try:
        skills = sources(ROOT, refresh_shared=args.command == "sync")
        if args.command == "sync":
            sync(ROOT, skills)
        elif args.command == "check":
            check(ROOT, skills)
        else:
            package(ROOT, skills, args.skills, args.target)
    except (ValueError, OSError, yaml.YAMLError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
