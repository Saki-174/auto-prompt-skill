#!/usr/bin/env python3
"""Install Auto Prompt with file ownership, conflict detection and rollback."""
import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "auto-prompt-skill"
MANIFEST = ".auto-prompt-install.json"


def unique_object(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("duplicate JSON key: " + key)
        data[key] = value
    return data


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)


def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def plain_path(path):
    for item in [path, *path.parents]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked/reparse path is not supported: " + str(item))


def within(home, path):
    plain_path(path)
    path.resolve().relative_to(home.resolve())
    if path.resolve() == home.resolve():
        raise ValueError("refusing to modify the home directory itself")


def relative_name(name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("invalid managed-file name")
    parsed = PurePosixPath(name)
    if parsed.is_absolute() or ".." in parsed.parts or str(parsed) != name or name == ".":
        raise ValueError("unsafe managed-file name: " + name)
    return name


def tree_bytes(root):
    plain_path(root)
    result = {}
    if root.exists():
        if not root.is_dir():
            raise ValueError("expected a directory: " + str(root))
        for path in root.rglob("*"):
            plain_path(path)
            if path.is_file():
                result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def hashes(files):
    return {name: digest(data) for name, data in sorted(files.items())}


def locations(home, mode):
    if mode not in ("plugin", "skill"):
        raise ValueError("mode must be plugin or skill")
    return {
        "target": home / (".codex/plugins/local-auto-prompt-skill" if mode == "plugin" else ".agents/skills/auto-prompt"),
        "catalog": home / ".agents/plugins/marketplace.json" if mode == "plugin" else None,
        "runtime": home / ".codex/auto-prompt/runtime.json",
    }


def current_state(paths):
    result = {}
    for key, path in paths.items():
        if path is None:
            result[key] = None
        elif key == "target":
            result[key] = hashes(tree_bytes(path)) if path.exists() else None
        else:
            plain_path(path)
            result[key] = digest(path.read_bytes()) if path.exists() else None
    return result


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".auto-prompt-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def install_lock(home):
    path = home / ".codex/auto-prompt/install.lock"
    within(home, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError("another install or interrupted transaction holds install.lock; see docs/install.md recovery")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def source_files(mode):
    entries = load_json(ROOT / "scripts/package-files.json")["skill"]
    if mode == "plugin":
        entries = ["plugin.json", "LICENSE", "NOTICE"] + entries
    result = {}
    for name in entries:
        relative_name(name)
        path = ROOT / name
        plain_path(path)
        key = name if mode == "plugin" else str(PurePosixPath(name).relative_to("skills/auto-prompt"))
        result[key] = path.read_bytes()
    return result


def managed_baseline(old, mode):
    if not old:
        return {}
    if MANIFEST in old:
        data = json.loads(old[MANIFEST], object_pairs_hook=unique_object)
        if data.get("schema") != 1 or data.get("project") != PLUGIN_NAME or not isinstance(data.get("managed"), dict):
            raise ValueError("unsupported install manifest; destination was not modified")
        baseline = data["managed"]
    else:
        # v1.0.0 had no ownership manifest. Only its audited file hashes are trusted.
        baseline = load_json(ROOT / "scripts/legacy-v1.0.0.json")["files"]
        if mode == "skill":
            baseline = {str(PurePosixPath(k).relative_to("skills/auto-prompt")): v for k, v in baseline.items() if k.startswith("skills/auto-prompt/")}
        elif json.loads(old.get("plugin.json", b"{}")).get("name") != PLUGIN_NAME:
            raise ValueError("destination belongs to another plugin")
    for key, value in baseline.items():
        relative_name(key)
        if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value):
            raise ValueError("invalid managed-file hash")
    return baseline


def merge_program(old, program, mode, version):
    baseline = managed_baseline(old, mode)
    conflicts = [name for name, expected in baseline.items() if name not in old or digest(old[name]) != expected]
    conflicts += [name for name in program if name in old and name not in baseline and old[name] != program[name]]
    if conflicts:
        raise ValueError("customized program files conflict: " + ", ".join(sorted(set(conflicts))) +
                         "; preserve edits separately (for example user/), reconcile explicitly, then retry; nothing replaced")
    result = {name: value for name, value in old.items() if name not in baseline and name != MANIFEST}
    result.update(program)
    result[MANIFEST] = encoded({"schema": 1, "project": PLUGIN_NAME, "version": version, "managed": hashes(program)})
    return result


def catalog_update(path, home, target):
    catalog = load_json(path) if path.exists() else {"name": "auto-prompt-local", "interface": {"displayName": "Auto Prompt Local"}, "plugins": []}
    if not isinstance(catalog, dict) or not isinstance(catalog.get("plugins"), list) or not isinstance(catalog.get("name"), str) or not catalog["name"]:
        raise ValueError("unsupported marketplace shape; nothing modified")
    entries = [entry for entry in catalog["plugins"] if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME]
    relative = "./" + target.relative_to(home).as_posix()
    if len(entries) > 1 or (entries and entries[0].get("source") not in (relative, {"source": "local", "path": relative})):
        raise ValueError("conflicting or duplicate Auto Prompt source; nothing modified")
    new = dict(entries[0]) if entries else {"name": PLUGIN_NAME, "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "category": "Productivity"}
    new["source"] = {"source": "local", "path": relative}
    catalog["plugins"] = [new if entry is entries[0] else entry for entry in catalog["plugins"]] if entries else catalog["plugins"] + [new]
    return catalog


def runtime_data(python_path):
    python_path = Path(python_path).absolute()
    probe = subprocess.run([str(python_path), "-I", "-c",
                            "import sys,json,hashlib,zipfile,subprocess; assert (3,9)<=sys.version_info[:2]<(3,15); print(json.dumps(list(sys.version_info[:3])))"],
                           capture_output=True, timeout=20)
    if probe.returncode:
        raise ValueError("selected Python is incompatible; run Install-Windows.cmd to prepare a dedicated runtime")
    return encoded({"schema": 1, "python": str(python_path), "version": json.loads(probe.stdout)})


def restore_files(home, paths, transaction, before):
    for key, path in paths.items():
        if path is None:
            continue
        within(home, path)
        if key == "target":
            if path.exists():
                tree_bytes(path)  # Verify every descendant before recursive removal.
                shutil.rmtree(path)
            if before[key] is not None:
                shutil.copytree(transaction / "before/target", path)
        elif before[key] is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(transaction / "before" / key, path)


def install(mode, home, python_path=None):
    home = Path(home).absolute()
    plain_path(home)
    with install_lock(home):
        paths = locations(home, mode)
        for path in paths.values():
            if path is not None:
                within(home, path)
        version = load_json(ROOT / "plugin.json")["version"]
        old = tree_bytes(paths["target"])
        new = merge_program(old, source_files(mode), mode, version)
        catalog = catalog_update(paths["catalog"], home, paths["target"]) if mode == "plugin" else None
        desired = {"target": new, "catalog": encoded(catalog) if catalog else None, "runtime": runtime_data(python_path or sys.executable)}
        before = current_state(paths)
        after = {"target": hashes(new), "catalog": digest(desired["catalog"]) if catalog else None, "runtime": digest(desired["runtime"])}
        result = {"mode": mode, "version": version, "path": str(paths["target"]), "changed": before != after, "backup": None, "catalogBackup": None, "transaction": None}
        if catalog:
            result.update(marketplace=str(paths["catalog"]), marketplaceName=catalog["name"])
        result["next"] = "Files and catalog ready. In ChatGPT desktop, install/refresh Auto Prompt Skill from this local source, then start a new local chat. Host login/permissions/enablement are user steps."
        result["runtime"] = json.loads(desired["runtime"])
        if before == after:
            return result
        transaction = home / ".codex/auto-prompt/transactions" / uuid.uuid4().hex
        within(home, transaction)
        transaction.mkdir(parents=True)
        (transaction / "before").mkdir()
        for key, path in paths.items():
            if path is not None and before[key] is not None:
                if key == "target":
                    shutil.copytree(path, transaction / "before/target")
                else:
                    shutil.copy2(path, transaction / "before" / key)
        stage = transaction / "stage"
        stage.mkdir()
        for name, data in new.items():
            output = stage / name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
        journal = {"schema": 1, "mode": mode, "status": "applying", "before": before, "after": after, "version": version}
        write_atomic(transaction / "transaction.json", encoded(journal))
        # Check before the try: another process's newly edited data must not be restored over.
        if current_state(paths) != before:
            raise ValueError("installation changed during preparation; retry after closing other installers")
        mutated = False
        try:
            paths["target"].parent.mkdir(parents=True, exist_ok=True)
            if paths["target"].exists():
                paths["target"].rename(transaction / "displaced")
                mutated = True
            stage.rename(paths["target"])
            mutated = True
            for key in ("catalog", "runtime"):
                if desired[key] is not None and before[key] != after[key]:
                    write_atomic(paths[key], desired[key])
            if current_state(paths) != after:
                raise ValueError("post-install verification failed")
            journal["status"] = "committed"
            write_atomic(transaction / "transaction.json", encoded(journal))
        except Exception:
            if mutated:
                restore_files(home, paths, transaction, before)
            journal["status"] = "rolled_back"
            (transaction / "transaction.json").write_bytes(encoded(journal))
            raise
        result.update(transaction=transaction.name, backup=str(transaction / "before/target") if before["target"] is not None else None,
                      catalogBackup=str(transaction / "before/catalog") if before["catalog"] is not None else None)
        return result


def rollback(home, transaction_id):
    home = Path(home).absolute()
    plain_path(home)
    if not re.fullmatch("[a-f0-9]{32}", transaction_id):
        raise ValueError("rollback requires the transaction ID printed by the installer")
    with install_lock(home):
        transaction = home / ".codex/auto-prompt/transactions" / transaction_id
        within(home, transaction)
        journal = load_json(transaction / "transaction.json")
        if journal.get("schema") != 1 or journal.get("status") not in ("committed", "applying", "rolled_back"):
            raise ValueError("unsupported transaction journal")
        paths = locations(home, journal["mode"])
        now = current_state(paths)
        if now == journal["before"]:
            return {"rolledBack": True, "changed": False, "transaction": transaction_id}
        if any(now[key] not in (journal["before"][key], journal["after"][key]) for key in paths):
            raise ValueError("files/configuration changed since installation; rollback stopped to preserve later edits")
        backup_paths = {key: transaction / "before" / key if value is not None else None for key, value in journal["before"].items()}
        if current_state(backup_paths) != journal["before"]:
            raise ValueError("transaction backup is missing or modified; rollback stopped")
        restore_files(home, paths, transaction, journal["before"])
        journal["status"] = "rolled_back"
        write_atomic(transaction / "transaction.json", encoded(journal))
        return {"rolledBack": True, "changed": True, "transaction": transaction_id, "next": "Refresh/reinstall Auto Prompt Skill from its restored source in ChatGPT; client caches are host-managed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("skill", "plugin"), default="plugin")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--python", type=Path, help="compatible interpreter selected by bootstrapper")
    parser.add_argument("--rollback", metavar="TRANSACTION_ID")
    args = parser.parse_args()
    try:
        result = rollback(args.home, args.rollback) if args.rollback else install(args.mode, args.home, args.python)
        sys.stdout.buffer.write(encoded(result))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, "Auto Prompt install: " + str(error) + "\n")


if __name__ == "__main__":
    main()
