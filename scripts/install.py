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


def verify_backup(transaction, before):
    backup_paths = {key: transaction / "before" / key if value is not None else None
                    for key, value in before.items()}
    if current_state(backup_paths) != before:
        raise ValueError("transaction backup is missing or modified; rollback stopped")


def interrupted_target_gap(transaction, journal, now):
    # A missing directory alone is not evidence of our interrupted rename.
    return (journal["status"] in ("applying", "recovery_conflict")
            and now["target"] is None and journal["before"]["target"] is not None
            and current_state({"target": transaction / "displaced"})["target"] == journal["before"]["target"]
            and current_state({"target": transaction / "stage"})["target"] == journal["after"]["target"])


def recover_attempt(home, paths, transaction, journal, attempted):
    # Only restore resources this attempt tried to write. Preserve all foreign edits,
    # including edits to resources we wrote that no longer match our planned bytes.
    now = current_state(paths)
    safe, conflicts = {}, []
    for key in attempted:
        if now[key] == journal["before"][key]:
            continue
        if now[key] == journal["after"][key] or (key == "target" and interrupted_target_gap(transaction, journal, now)):
            safe[key] = paths[key]
        else:
            conflicts.append(key)
    verify_backup(transaction, {key: journal["before"][key] for key in safe})
    # Recheck each resource immediately before restoration. This is conflict
    # detection, not an OS-wide lock against other plugin managers.
    for key, path in safe.items():
        if current_state({key: path})[key] != now[key]:
            conflicts.append(key)
            continue
        restore_files(home, {key: path}, transaction, journal["before"])
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
        version = load_json(ROOT / "plugin.json")["version"]
        old = tree_bytes(paths["target"])
        new = merge_program(old, source_files(mode), mode, version)
        catalog = catalog_update(paths["catalog"], home, paths["target"]) if mode == "plugin" else None
        desired = {"target": new, "catalog": encoded(catalog) if catalog else None, "runtime": runtime_data(python_path or sys.executable)}
        if current_state(paths) != before:
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
        attempted = set()
        try:
            paths["target"].parent.mkdir(parents=True, exist_ok=True)
            if paths["target"].exists():
                paths["target"].rename(transaction / "displaced")
                attempted.add("target")
            stage.rename(paths["target"])
            attempted.add("target")
            for key in ("catalog", "runtime"):
                if desired[key] is not None and before[key] != after[key]:
                    if current_state({key: paths[key]})[key] != before[key]:
                        raise ValueError("installation changed before writing " + key)
                    attempted.add(key)
                    write_atomic(paths[key], desired[key])
            if current_state(paths) != after:
                raise ValueError("post-install verification failed")
            if check_launcher:
                result["selfTest"] = check_windows_launcher(home, mode)
            if current_state(paths) != after:
                raise ValueError("installation changed during launcher self-check")
            journal["status"] = "committed"
            write_atomic(transaction / "transaction.json", encoded(journal))
        except Exception as failure:
            try:
                if attempted:
                    recover_attempt(home, paths, transaction, journal, attempted)
            except Exception as recovery_error:
                journal["status"] = "recovery_conflict"
                (transaction / "transaction.json").write_bytes(encoded(journal))
                raise ValueError("installation failed: " + str(failure) + "; " + str(recovery_error)
                                 + "; transaction " + transaction.name + "; see docs/install.md recovery") from failure
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
        if journal.get("schema") != 1 or journal.get("status") not in ("committed", "applying", "rolled_back", "recovery_conflict"):
            raise ValueError("unsupported transaction journal")
        paths = locations(home, journal["mode"])
        now = current_state(paths)
        if now == journal["before"]:
            return {"rolledBack": True, "changed": False, "transaction": transaction_id}
        if any(now[key] not in (journal["before"][key], journal["after"][key])
               and not (key == "target" and interrupted_target_gap(transaction, journal, now)) for key in paths):
            raise ValueError("files/configuration changed since installation; rollback stopped to preserve later edits")
        verify_backup(transaction, journal["before"])
        recover_attempt(home, paths, transaction, journal, set(paths))
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
