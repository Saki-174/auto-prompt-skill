#!/usr/bin/env python3
"""Install Auto Prompt with file ownership, conflict detection and rollback."""
import argparse
import importlib.util
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
_permission_spec = importlib.util.spec_from_file_location("install_permissions", Path(__file__).with_name("install_permissions.py"))
permissions = importlib.util.module_from_spec(_permission_spec)
_permission_spec.loader.exec_module(permissions)


def unique_object(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("duplicate JSON keys are not supported")
        data[key] = value
    return data


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError) as error:
        raise ValueError("invalid JSON in " + path.name + "; preserve the file and restore intact JSON before retrying: " + str(error)) from error


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


def permission_state(paths):
    result = {}
    for key, path in paths.items():
        if path is None or not path.exists():
            result[key] = None
        elif key == "target":
            entries = [path, *sorted(path.rglob("*"))]
            result[key] = {}
            for item in entries:
                plain_path(item)
                name = "." if item == path else item.relative_to(path).as_posix()
                result[key][name] = permissions.capture(item)
        else:
            plain_path(path)
            result[key] = permissions.capture(path)
    return result


def apply_tree_permissions(root, snapshot):
    # Include empty user directories. Restore each descriptor individually;
    # the Windows API deliberately does not propagate parent ACEs to children.
    for name, security in snapshot.items():
        path = root if name == "." else root / relative_name(name)
        plain_path(path)
        if not path.exists():
            path.mkdir(parents=True)
        permissions.apply(path, security)


def matches(paths, state, security=None):
    if current_state(paths) != {key: state[key] for key in paths}:
        return False
    return security is None or permission_state(paths) == {key: security[key] for key in paths}


def journal_permissions(journal, phase):
    if journal["schema"] != 2:
        return None
    return journal.get("permissions", {}).get(phase)


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    original = permissions.capture(path) if path.exists() else None
    fd, temporary = permissions.temporary_file(path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if original is not None:
            permissions.apply(temporary, original)
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
        try:
            data = json.loads(old[MANIFEST], object_pairs_hook=unique_object)
        except (ValueError, UnicodeError) as error:
            raise ValueError("invalid install manifest JSON; preserve it and restore an intact ownership manifest before retrying") from error
        if (not isinstance(data, dict) or type(data.get("schema")) is not int or data["schema"] != 1
                or data.get("project") != PLUGIN_NAME or not isinstance(data.get("managed"), dict)):
            raise ValueError("unsupported install manifest; preserve it and restore an intact ownership manifest before retrying; destination was not modified")
        baseline = data["managed"]
    else:
        # v1.0.0 had no ownership manifest. Only its audited file hashes are trusted.
        baseline = load_json(ROOT / "scripts/legacy-v1.0.0.json")["files"]
        if mode == "skill":
            baseline = {str(PurePosixPath(k).relative_to("skills/auto-prompt")): v for k, v in baseline.items() if k.startswith("skills/auto-prompt/")}
        else:
            plugin = json.loads(old.get("plugin.json", b"{}"), object_pairs_hook=unique_object)
            if mode == "plugin" and (not isinstance(plugin, dict) or plugin.get("name") != PLUGIN_NAME):
                raise ValueError("destination belongs to another plugin or has invalid plugin metadata")
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
    probe = subprocess.run([str(python_path), "-I", str(ROOT / "skills/auto-prompt/scripts/runtime_policy.py")],
                           capture_output=True, timeout=20)
    if probe.returncode:
        raise ValueError("selected Python is incompatible; run Install-Windows.cmd to prepare a dedicated runtime")
    return encoded({"schema": 1, "python": str(python_path), "version": json.loads(probe.stdout)["version"]})


def restore_receipt(transaction, journal):
    path = transaction / "restore.json"
    plain_path(path)
    if not path.exists():
        return None
    data = load_json(path)
    if (not isinstance(data, dict) or data.get("schema") != 1
            or data.get("phase") not in ("preparing", "ready")
            or data.get("before") != journal["before"]["target"]
            or "original" not in data
            or data["original"] not in (None, journal["after"]["target"])):
        raise ValueError("unsupported target restoration receipt; recovery stopped")
    return data


def interrupted_restore_gap(transaction, journal, now):
    if now["target"] is not None or journal["before"]["target"] is None:
        return False
    receipt = restore_receipt(transaction, journal)
    if receipt is None or receipt["phase"] != "ready":
        return False
    stage = current_state({"target": transaction / "restore-stage"})["target"]
    moved = current_state({"target": transaction / "restore-displaced"})["target"]
    return (stage == receipt["before"]
            and matches({"target": transaction / "restore-stage"}, journal["before"], journal_permissions(journal, "before")) and
            ((receipt["original"] is not None and moved == receipt["original"]
              and matches({"target": transaction / "restore-displaced"}, journal["after"], journal_permissions(journal, "after")))
             or (receipt["original"] is None and moved is None
                 and interrupted_target_gap(transaction, journal, now))))


def restore_target(home, path, transaction, journal):
    stage, moved = transaction / "restore-stage", transaction / "restore-displaced"
    for item in (stage, moved, transaction / "restore.json"):
        within(home, item)
    current = current_state({"target": path})["target"]
    receipt = restore_receipt(transaction, journal)
    if receipt is None:
        if stage.exists() or moved.exists():
            raise ValueError("unregistered restoration directories; recovery stopped")
        receipt = {"schema": 1, "phase": "preparing", "original": current,
                   "before": journal["before"]["target"]}
        write_atomic(transaction / "restore.json", encoded(receipt))
    expected_security = journal_permissions(journal, "after")
    if expected_security is not None and receipt["original"] is None:
        expected_security = {"target": None}
    # A completed preparation is immutable evidence for the rename gap.
    if receipt["phase"] == "preparing":
        if (current != receipt["original"] or moved.exists()
                or not matches({"target": path}, {"target": receipt["original"]},
                               expected_security)):
            raise ValueError("target changed during restoration preparation; recovery stopped")
        if stage.exists():
            tree_bytes(stage)
            shutil.rmtree(stage)  # Only this receipt's incomplete private staging copy.
        if receipt["before"] is not None:
            shutil.copytree(transaction / "before/target", stage)
            security = journal_permissions(journal, "before")
            if security is not None:
                apply_tree_permissions(stage, security["target"])
            if current_state({"target": stage})["target"] != receipt["before"]:
                raise ValueError("restoration staging verification failed")
        receipt["phase"] = "ready"
        write_atomic(transaction / "restore.json", encoded(receipt))
    if receipt["before"] is not None and not matches({"target": stage}, journal["before"], journal_permissions(journal, "before")):
        raise ValueError("restoration staging is missing or modified; recovery stopped")
    current = current_state({"target": path})["target"]
    if current is None and moved.exists():
        if not interrupted_restore_gap(transaction, journal, {"target": current}):
            raise ValueError("restoration rename evidence is missing or modified")
    else:
        if (current != receipt["original"] or moved.exists()
                or not matches({"target": path}, {"target": receipt["original"]},
                               expected_security)):
            raise ValueError("target changed during restoration; recovery stopped")
        if path.exists():
            path.rename(moved)  # Keep the current program until restoration has completed.
    if receipt["before"] is not None:
        stage.rename(path)


def restore_files(home, paths, transaction, journal):
    before = journal["before"]
    for key, path in paths.items():
        if path is None:
            continue
        within(home, path)
        if key == "target":
            restore_target(home, path, transaction, journal)
        elif before[key] is None:
            if path.exists():
                path.unlink()
        else:
            security = journal_permissions(journal, "before")
            restore_config(path, (transaction / "before" / key).read_bytes(), security[key] if security else None)
        if not matches({key: path}, before, journal_permissions(journal, "before")):
            raise ValueError("resource changed during restoration: " + key)


def restore_config(path, data, security):
    # Restore ACL on an empty private temporary before writing any bytes.
    if security is None:
        write_atomic(path, data)
        return
    fd, temporary = permissions.temporary_file(path.parent)
    try:
        os.close(fd)
        permissions.apply(temporary, security)
        write_atomic(temporary, data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_backup(transaction, before, security=None):
    backup_paths = {key: transaction / "before" / key if value is not None else None
                    for key, value in before.items()}
    if not matches(backup_paths, before, security):
        raise ValueError("transaction backup is missing or modified; rollback stopped")


def interrupted_target_gap(transaction, journal, now):
    # A missing directory alone is not evidence of our interrupted rename.
    return (journal["status"] in ("applying", "recovery_conflict")
            and now["target"] is None and journal["before"]["target"] is not None
            and matches({"target": transaction / "displaced"}, journal["before"], journal_permissions(journal, "before"))
            and matches({"target": transaction / "stage"}, journal["after"], journal_permissions(journal, "after")))


def recover_attempt(home, paths, transaction, journal, attempted):
    # Only restore resources this attempt tried to write. Preserve all foreign edits,
    # including edits to resources we wrote that no longer match our planned bytes.
    now = current_state(paths)
    now_permissions = permission_state(paths)
    before_permissions = journal_permissions(journal, "before")
    after_permissions = journal_permissions(journal, "after")
    safe, conflicts = {}, []
    for key in attempted:
        if matches({key: paths[key]}, journal["before"], before_permissions):
            continue
        if matches({key: paths[key]}, journal["after"], after_permissions) or (key == "target" and
                (interrupted_target_gap(transaction, journal, now) or interrupted_restore_gap(transaction, journal, now))):
            safe[key] = paths[key]
        else:
            conflicts.append(key)
    backup_permissions = journal_permissions(journal, "backup")
    verify_backup(transaction, {key: journal["before"][key] for key in safe},
                  {key: backup_permissions[key] for key in safe} if backup_permissions else None)
    # Recheck each resource immediately before restoration. This is conflict
    # detection, not an OS-wide lock against other plugin managers.
    for key, path in safe.items():
        if not matches({key: path}, now, now_permissions):
            conflicts.append(key)
            continue
        restore_files(home, {key: path}, transaction, journal)
    if conflicts:
        raise ValueError("recovery preserved later edits to: " + ", ".join(sorted(conflicts)))


def check_windows_launcher(home, mode):
    if os.name != "nt":
        raise ValueError("launcher self-check requires Windows")
    target = locations(home, mode)["target"]
    runner = target / ("skills/auto-prompt/scripts/Run-Strict.ps1" if mode == "plugin" else "scripts/Run-Strict.ps1")
    sample = {"targetAgent": "ChatGPT Work", "rawPrompt": "根据我提供的会议记录，整理决定、行动项及待确认信息。",
              "requirements": "用中文。保留已给出的负责人和截止时间，不推测缺失值。", "profile": "general", "strictMode": True}
    expected = "650b898d02661131657e3d3f502c7bf9d0e3c0ce1f47bca85257e76d725e52d2"
    state = home / ".codex/auto-prompt"
    within(home, state)
    # The launcher is Windows PowerShell 5.1; avoid inherited PS7 module paths.
    env = {key: value for key, value in os.environ.items() if key.lower() != "psmodulepath"}
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    with tempfile.TemporaryDirectory(prefix="self-check-", dir=state) as folder:
        input_path, output_path = Path(folder) / "input.json", Path(folder) / "output.txt"
        input_path.write_bytes(encoded(sample))
        process = subprocess.run([str(powershell), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(runner),
                                  "-HomeDirectory", str(home), "-InputPath", str(input_path), "-OutputPath", str(output_path)],
                                 env=env, capture_output=True, timeout=45)
        if process.returncode or not output_path.is_file() or digest(output_path.read_bytes()) != expected:
            detail = process.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError("installed strict launcher self-check failed" + (": " + detail if detail else "; unexpected output"))
    return {"status": "passed", "sha256": expected}


def install(mode, home, python_path=None, check_launcher=False):
    home = Path(home).absolute()
    plain_path(home)
    with install_lock(home):
        paths = locations(home, mode)
        for path in paths.values():
            if path is not None:
                within(home, path)
        before = current_state(paths)
        before_permissions = permission_state(paths)
        version = load_json(ROOT / "plugin.json")["version"]
        old = tree_bytes(paths["target"])
        new = merge_program(old, source_files(mode), mode, version)
        catalog = catalog_update(paths["catalog"], home, paths["target"]) if mode == "plugin" else None
        desired = {"target": new, "catalog": encoded(catalog) if catalog else None, "runtime": runtime_data(python_path or sys.executable)}
        if not matches(paths, before, before_permissions):
            raise ValueError("installation changed during preparation; retry after closing other installers")
        after = {"target": hashes(new), "catalog": digest(desired["catalog"]) if catalog else None, "runtime": digest(desired["runtime"])}
        result = {"mode": mode, "version": version, "path": str(paths["target"]), "changed": before != after, "backup": None, "catalogBackup": None, "transaction": None}
        if catalog:
            result.update(marketplace=str(paths["catalog"]), marketplaceName=catalog["name"])
        result["next"] = "Files and catalog ready. In ChatGPT desktop, install/refresh Auto Prompt Skill from this local source, then start a new local chat. Host login/permissions/enablement are user steps."
        result["runtime"] = json.loads(desired["runtime"])
        if before == after:
            if check_launcher:
                result["selfTest"] = check_windows_launcher(home, mode)
            return result
        transaction = home / ".codex/auto-prompt/transactions" / uuid.uuid4().hex
        within(home, transaction)
        permissions.mkdir_private(transaction)
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
        if before_permissions["target"] is not None:
            surviving = {name: value for name, value in before_permissions["target"].items()
                         if name not in old or name in new}
            apply_tree_permissions(stage, surviving)
        after_permissions = permission_state({"target": stage})
        for key in ("catalog", "runtime"):
            after_permissions[key] = before_permissions[key]
            if desired[key] is not None and after_permissions[key] is None:
                probe = transaction / ("permission-probe-" + key)
                fd = permissions.private_file(probe)
                os.close(fd)
                after_permissions[key] = permissions.capture(probe)
                probe.unlink()
        backup_paths = {key: transaction / "before" / key if before[key] is not None else None for key in paths}
        journal = {"schema": 2, "mode": mode, "status": "applying", "before": before, "after": after, "version": version,
                   "permissions": {"before": before_permissions, "after": after_permissions, "backup": permission_state(backup_paths)}}
        write_atomic(transaction / "transaction.json", encoded(journal))
        # Check before the try: another process's newly edited data must not be restored over.
        if not matches(paths, before, before_permissions):
            raise ValueError("installation changed during preparation; retry after closing other installers")
        attempted = set()
        switch_conflict = False
        try:
            paths["target"].parent.mkdir(parents=True, exist_ok=True)
            if paths["target"].exists():
                paths["target"].rename(transaction / "displaced")
                attempted.add("target")
                # Recheck the actual moved tree, closing the final pre-rename check window.
                try:
                    moved_matches = matches({"target": transaction / "displaced"}, before, before_permissions)
                except (OSError, ValueError):
                    moved_matches = False
                if not moved_matches:
                    switch_conflict = True
                    if not paths["target"].exists():
                        (transaction / "displaced").rename(paths["target"])
                        attempted.discard("target")
                    raise ValueError("installation directory changed during switch; latest edits preserved; transaction "
                                     + transaction.name + "; close editors and retry; see docs/install.md recovery")
            stage.rename(paths["target"])
            attempted.add("target")
            for key in ("catalog", "runtime"):
                if desired[key] is not None and before[key] != after[key]:
                    if not matches({key: paths[key]}, before, before_permissions):
                        raise ValueError("installation changed before writing " + key)
                    attempted.add(key)
                    write_atomic(paths[key], desired[key])
            if not matches(paths, after, after_permissions):
                raise ValueError("post-install verification failed")
            if check_launcher:
                result["selfTest"] = check_windows_launcher(home, mode)
            if not matches(paths, after, after_permissions):
                raise ValueError("installation changed during launcher self-check")
            journal["status"] = "committed"
            write_atomic(transaction / "transaction.json", encoded(journal))
        except Exception as failure:
            try:
                if attempted:
                    recover_attempt(home, paths, transaction, journal, attempted)
            except Exception as recovery_error:
                journal["status"] = "recovery_conflict"
                write_atomic(transaction / "transaction.json", encoded(journal))
                raise ValueError("installation failed: " + str(failure) + "; " + str(recovery_error)
                                 + "; transaction " + transaction.name + "; see docs/install.md recovery") from failure
            journal["status"] = "recovery_conflict" if switch_conflict else "rolled_back"
            write_atomic(transaction / "transaction.json", encoded(journal))
            raise
        result.update(transaction=transaction.name, backup=str(transaction / "before/target") if before["target"] is not None else None,
                      catalogBackup=str(transaction / "before/catalog") if before["catalog"] is not None else None)
        return result


def validate_journal(journal):
    message = "unsupported transaction journal; preserve the transaction directory and restore intact evidence before retrying"
    if (not isinstance(journal, dict) or type(journal.get("schema")) is not int or journal["schema"] not in (1, 2)
            or journal.get("status") not in ("committed", "applying", "rolled_back", "recovery_conflict")
            or journal.get("mode") not in ("plugin", "skill")):
        raise ValueError(message)
    for name in ("before", "after"):
        snapshot = journal.get(name)
        if not isinstance(snapshot, dict) or set(snapshot) != {"target", "catalog", "runtime"}:
            raise ValueError(message)
        for key, value in snapshot.items():
            if value is None:
                continue
            if key == "target":
                if not isinstance(value, dict):
                    raise ValueError(message)
                for file, checksum in value.items():
                    try:
                        relative_name(file)
                    except ValueError as error:
                        raise ValueError(message) from error
                    if not isinstance(checksum, str) or not re.fullmatch("[a-f0-9]{64}", checksum):
                        raise ValueError(message)
            elif not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value):
                raise ValueError(message)


    if journal["schema"] == 2:
        security = journal.get("permissions")
        if not isinstance(security, dict) or set(security) != {"before", "after", "backup"}:
            raise ValueError(message)
        for phase, snapshot in security.items():
            state = journal["after" if phase == "after" else "before"]
            if not isinstance(snapshot, dict) or set(snapshot) != set(state):
                raise ValueError(message)
            for key, value in snapshot.items():
                if state[key] is None:
                    if value is not None:
                        raise ValueError(message)
                    continue
                entries = value if key == "target" else {"config": value}
                if not isinstance(entries, dict) or not entries or (key == "target" and "." not in entries):
                    raise ValueError(message)
                for name, descriptor in entries.items():
                    if key == "target" and name != ".":
                        relative_name(name)
                    if not isinstance(descriptor, dict) or (
                            os.name == "nt" and (set(descriptor) != {"sddl"} or not isinstance(descriptor["sddl"], str))
                            or os.name != "nt" and (set(descriptor) != {"mode"} or type(descriptor["mode"]) is not int
                                                   or not 0 <= descriptor["mode"] <= 0o7777)):
                        raise ValueError(message)


def rollback(home, transaction_id):
    home = Path(home).absolute()
    plain_path(home)
    if not re.fullmatch("[a-f0-9]{32}", transaction_id):
        raise ValueError("rollback requires the transaction ID printed by the installer")
    with install_lock(home):
        transaction = home / ".codex/auto-prompt/transactions" / transaction_id
        within(home, transaction)
        journal = load_json(transaction / "transaction.json")
        validate_journal(journal)
        if os.name == "nt" and journal["schema"] == 1 and any(value is not None for value in journal["before"].values()):
            raise ValueError("legacy transaction has no original ACL evidence; keep backups and restore permissions manually")
        paths = locations(home, journal["mode"])
        now = current_state(paths)
        if matches(paths, journal["before"], journal_permissions(journal, "before")):
            return {"rolledBack": True, "changed": False, "transaction": transaction_id}
        if any(not (matches({key: paths[key]}, journal["before"], journal_permissions(journal, "before"))
                    or matches({key: paths[key]}, journal["after"], journal_permissions(journal, "after")))
               and not (key == "target" and (interrupted_target_gap(transaction, journal, now)
                                            or interrupted_restore_gap(transaction, journal, now))) for key in paths):
            raise ValueError("files/configuration changed since installation; rollback stopped to preserve later edits")
        verify_backup(transaction, journal["before"], journal_permissions(journal, "backup"))
        recover_attempt(home, paths, transaction, journal, set(paths))
        if not matches(paths, journal["before"], journal_permissions(journal, "before")):
            raise ValueError("files/configuration changed during rollback; later edits preserved")
        journal["status"] = "rolled_back"
        write_atomic(transaction / "transaction.json", encoded(journal))
        return {"rolledBack": True, "changed": True, "transaction": transaction_id, "next": "Refresh/reinstall Auto Prompt Skill from its restored source in ChatGPT; client caches are host-managed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("skill", "plugin"), default="plugin")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--python", type=Path, help="compatible interpreter selected by bootstrapper")
    parser.add_argument("--rollback", metavar="TRANSACTION_ID")
    parser.add_argument("--check-launcher", action="store_true", help="verify the installed Windows strict launcher before committing")
    parser.add_argument("--human", action="store_true", help="show a concise Chinese installation summary")
    args = parser.parse_args()
    try:
        result = rollback(args.home, args.rollback) if args.rollback else install(args.mode, args.home, args.python, args.check_launcher)
        if args.human:
            if args.rollback:
                message = "Auto Prompt 已恢复。请在客户端刷新插件，并在新聊天确认恢复后的版本。\n"
            else:
                checked = result.get("selfTest", {}).get("status") == "passed"
                message = ("Auto Prompt " + result["version"] + (" 安装完成。\n" if result["changed"] else " 文件已是当前内容，无需重复安装。\n")
                           + ("严格脚本自检：通过。\n" if checked else "严格脚本自检：未执行。\n")
                           + "安装位置：" + result["path"] + "\nPython：" + result["runtime"]["python"] + "\n")
                if result["transaction"]:
                    message += "恢复事务 ID：" + result["transaction"] + "\n"
                if result["mode"] == "plugin":
                    message += "客户端待启用：打开 Plugins，选择本地来源 " + result["marketplaceName"] + "，安装或刷新 Auto Prompt Skill。\n"
                else:
                    message += "客户端待启用：按宿主的技能发现方式加载上述目录。\n"
                message += "然后新建本地聊天，发送：请调用 Auto Prompt 技能。文件安装和脚本自检不代表客户端已启用。\n"
            sys.stdout.buffer.write(message.encode("utf-8"))
        else:
            sys.stdout.buffer.write(encoded(result))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, "Auto Prompt install: " + str(error) + "\n")


if __name__ == "__main__":
    main()
