#!/usr/bin/env python3
"""Build portable ZIPs from a fixed public-file allowlist; no third-party packages."""

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
_FILES = json.loads((ROOT / "scripts/package-files.json").read_text(encoding="utf-8"))
SKILL_FILES = _FILES["skill"]
PUBLIC = _FILES["bundle"]


def check_source(path):
    for item in [path, *path.parents]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked/reparse release source is unsupported: " + str(item))
    try:
        path.resolve().relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError("release file escapes source root") from error
    if not path.is_file():
        raise ValueError("missing release file: " + str(path))


def files_for(entries):
    files = []
    for entry in entries:
        if not isinstance(entry, str) or "\\" in entry or ":" in entry:
            raise ValueError("invalid release file name")
        relative = PurePosixPath(entry)
        if relative.is_absolute() or ".." in relative.parts or str(relative) != entry or entry == ".":
            raise ValueError("unsafe release file name")
        path = ROOT / entry
        check_source(path)
        files.append(path)
    return files


def archive(output, files, path_for):
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files):
            check_source(path)
            info = zipfile.ZipInfo(path_for(path), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())


def build(output):
    # Validate every source before creating any ZIP, including sources used only
    # by later archives. A failure must not leave a seemingly complete plugin ZIP.
    plugin_files = files_for(["plugin.json", "LICENSE", "NOTICE"] + SKILL_FILES)
    bundle_files = files_for(PUBLIC)
    skill_files = files_for(SKILL_FILES)
    output.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    outputs = []
    for suffix, files in (("bundle", bundle_files), ("plugin", plugin_files)):
        name = "auto-prompt-skill-" + version + "-" + suffix + ".zip"
        path = output / name
        archive(path, files, lambda p: "auto-prompt-skill/" + p.relative_to(ROOT).as_posix())
        outputs.append(path)
    skill = ROOT / "skills" / "auto-prompt"
    path = output / ("auto-prompt-" + version + "-skill.zip")
    archive(path, skill_files, lambda p: "auto-prompt/" + p.relative_to(skill).as_posix())
    outputs.append(path)
    checksum = output / "SHA256SUMS.txt"
    checksum.write_bytes("".join(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name + "\n" for path in outputs).encode("ascii"))
    return outputs + [checksum]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    for path in build(args.output):
        print(path)


if __name__ == "__main__":
    main()
