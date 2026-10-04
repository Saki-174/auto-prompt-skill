#!/usr/bin/env python3
"""Build portable ZIPs from a fixed public-file allowlist; no third-party packages."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = [
    "skills/auto-prompt/SKILL.md", "skills/auto-prompt/LICENSE", "skills/auto-prompt/NOTICE",
    "skills/auto-prompt/agents/openai.yaml", "skills/auto-prompt/references/input.md",
    "skills/auto-prompt/scripts/render_prompt.py",
    "skills/auto-prompt/templates/zh-development.txt", "skills/auto-prompt/templates/zh-general.txt",
    "skills/auto-prompt/templates/en-development.txt", "skills/auto-prompt/templates/en-general.txt",
]
PUBLIC = [
    "plugin.json", "LICENSE", "NOTICE", "README.md", "README.en.md",
    "Install-Windows.ps1", "Install-Windows.cmd", ".gitignore", ".gitattributes",
    ".agents/plugins/marketplace.json", ".github/workflows/ci.yml",
    "scripts/install.py", "scripts/build_release.py",
    "examples/codex.json", "examples/chatgpt.json", "examples/english.json",
    "tests/test_render_prompt.py", "tests/test_install_release.py", "tests/fixtures/legacy.json",
    "docs/install.md", "docs/migration.md", "docs/validation.md",
] + SKILL_FILES


def files_for(entries):
    files = []
    for entry in entries:
        path = ROOT / entry
        if not path.is_file():
            raise ValueError("missing release file: " + entry)
        files.append(path)
    return files


def archive(output, files, path_for):
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files):
            if path.is_symlink():
                raise ValueError("symlinks cannot enter release archives")
            info = zipfile.ZipInfo(path_for(path), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    outputs = []
    plugin_files = files_for(["plugin.json", "LICENSE", "NOTICE"] + SKILL_FILES)
    for suffix, files in (("bundle", files_for(PUBLIC)), ("plugin", plugin_files)):
        name = "auto-prompt-skill-" + version + "-" + suffix + ".zip"
        path = output / name
        archive(path, files, lambda p: "auto-prompt-skill/" + p.relative_to(ROOT).as_posix())
        outputs.append(path)
    skill = ROOT / "skills" / "auto-prompt"
    path = output / ("auto-prompt-" + version + "-skill.zip")
    archive(path, files_for(SKILL_FILES), lambda p: "auto-prompt/" + p.relative_to(skill).as_posix())
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
