#!/usr/bin/env python3
"""Install a local skill or register a skills-only personal plugin. No network."""

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "auto-prompt-skill"
SKILL_NAME = "auto-prompt"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def package_files(source):
    # A positive list prevents copying local git history, credentials, or scratch files.
    return [source / "plugin.json", source / "LICENSE", source / "NOTICE", source / "skills"]


def same_tree(left, right):
    def snapshot(root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc")}
    return snapshot(left) == snapshot(right)


def replace_tree(staged, target):
    if target.is_symlink():
        raise ValueError("refusing to replace a symlink destination")
    if target.exists() and same_tree(staged, target):
        return None, False
    backup = None
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = target.with_name(target.name + ".backup-" + stamp)
        target.rename(backup)
    try:
        shutil.copytree(staged, target)
    except OSError:
        if target.exists():
            shutil.rmtree(target)
        if backup is not None:
            backup.rename(target)
        raise
    return backup, True


def write_json_atomic(path, data):
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = path.with_name(path.name + ".backup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
        shutil.copy2(path, backup)
    fd, temporary = tempfile.mkstemp(prefix=".auto-prompt-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return backup


def install(mode, home):
    home = Path(home).resolve()
    skill_source = ROOT / "skills" / SKILL_NAME
    if mode == "skill":
        target = home / ".agents" / "skills" / SKILL_NAME
        if target.exists():
            manifest = target / "SKILL.md"
            if not manifest.is_file() or "\nname: auto-prompt\n" not in manifest.read_text(encoding="utf-8"):
                raise ValueError("destination is not an existing auto-prompt skill")
        target.parent.mkdir(parents=True, exist_ok=True)
        backup, changed = replace_tree(skill_source, target)
        return {"mode": mode, "path": str(target), "changed": changed, "backup": str(backup) if backup else None}

    target = home / ".codex" / "plugins" / "local-auto-prompt-skill"
    catalog_path = home / ".agents" / "plugins" / "marketplace.json"
    if target.exists() and load_json(target / "plugin.json").get("name") != PLUGIN_NAME:
        raise ValueError("destination belongs to a different plugin")
    catalog = load_json(catalog_path) if catalog_path.exists() else {
        "name": "auto-prompt-local",
        "interface": {"displayName": "Auto Prompt Local"},
        "plugins": [],
    }
    if not isinstance(catalog, dict) or not isinstance(catalog.get("plugins"), list) or not isinstance(catalog.get("name"), str) or not catalog["name"]:
        raise ValueError("existing marketplace has an unsupported shape; it was not modified")
    entries = [entry for entry in catalog["plugins"] if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME]
    if len(entries) > 1:
        raise ValueError("multiple existing Auto Prompt entries; resolve them before installing")
    relative = "./" + target.relative_to(home).as_posix()
    if entries and entries[0].get("source") not in (relative, {"source": "local", "path": relative}):
        raise ValueError("another Auto Prompt source is registered; existing settings were not modified")
    new_entry = dict(entries[0]) if entries else {
        "name": PLUGIN_NAME,
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    new_entry["source"] = {"source": "local", "path": relative}
    catalog["plugins"] = [new_entry if entry is entries[0] else entry for entry in catalog["plugins"]] if entries else catalog["plugins"] + [new_entry]
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="auto-prompt-install-") as folder:
        stage = Path(folder) / PLUGIN_NAME
        stage.mkdir()
        for source in package_files(ROOT):
            if source.is_dir():
                shutil.copytree(source, stage / source.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                shutil.copy2(source, stage / source.name)
        backup, changed = replace_tree(stage, target)
        catalog_backup = write_json_atomic(catalog_path, catalog)
    return {
        "mode": mode,
        "path": str(target),
        "marketplace": str(catalog_path),
        "marketplaceName": catalog["name"],
        "changed": changed,
        "backup": str(backup) if backup else None,
        "catalogBackup": str(catalog_backup) if catalog_backup else None,
        "next": "Restart ChatGPT desktop / Codex, select this local marketplace in Plugins, and click Install for Auto Prompt Skill.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("skill", "plugin"), default="plugin")
    parser.add_argument("--home", type=Path, default=Path.home(), help="target home directory; useful for isolated testing")
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.mode, args.home), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, "Auto Prompt install: " + str(error) + "\n")


if __name__ == "__main__":
    main()
