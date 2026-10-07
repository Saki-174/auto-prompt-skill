# Auto Prompt Skill · v1.0.2

v1.0.2 improves recovery, strict-mode conflict clarification and prompt revisions. Download the bundle and SHA-256 checksums from the [v1.0.2 release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.0.2).

Same-version installer revision (2026-10-05): Unicode interpreter paths are supported, compatible registered interpreters are reused off PATH, and Windows setup checks the actual strict launcher before reporting success. The CMD entry shows a Chinese summary; the PowerShell entry retains JSON by default. Existing 1.0.2 users must download the refreshed assets/checksums, rerun setup and refresh their host plugin; the version number alone does not identify this revision.

Turn a target agent and a rough request into a usable prompt inside ChatGPT. The **host** runs the skill; the **target agent** receives its generated prompt. Targets may include Codex, ChatGPT or video models, across software, study, research, writing and video tasks.

Same-version recovery and packaging revision (2026-10-07; version remains 1.0.2): atomic shared-file restoration, verified directory recovery retries, serialized runtime preparation, source symlink/reparse checks before any ZIP is created, and clear errors for malformed ownership manifests and transaction journals. Download the refreshed bundle and checksums and use its installer; the version number alone does not identify the revision. The skill instructions, renderer and templates remain unchanged. Unknown or modified restoration evidence still stops recovery rather than overwriting user work.

## Windows x64 quick start

Install/sign in to a ChatGPT desktop host that supports local skills. Extract the release bundle and run Install-Windows.cmd. Setup reuses a compatible interpreter or downloads the pinned official Python 3.13.12 embeddable package with SHA-256 verification. It installs only project-owned files; no global Python/PATH changes. Then install/refresh Auto Prompt Skill in the local Plugins source, restart and open a new local chat. Host installation, login, permissions and enablement remain user steps.

Offline setup can use a compatible interpreter or the official runtime archive via -RuntimeArchive. Runtime preparation is scoped to Windows x64; other platforms retain the existing Python installation route.

## Use and compatibility

Invoke the skill alone for brief guidance, or provide the target and request together. Supplied information is reused; material ambiguities are clarified in small rounds. Structured input is used only when the current host actually exposes a suitable tool; otherwise ordinary text questions work.

Natural-language requests now default to flexible model rewriting. Explicit strict mode runs the script and returns its result unchanged. Complete legacy JSON without strictMode still means true, and the direct CLI defaults are unchanged. Fixed renderer and templates plus identical JSON produce identical UTF-8 bytes. This does not make natural-language extraction deterministic.

The first flexible result may include one optional revision hint outside the copyable prompt. Append, replace and undo requests preserve unaffected constraints. A new task clears old requirements. Strict mode and revision replies omit the hint. Conflicting strict templates or legacy language rules require a targeted choice before final output; the renderer and direct CLI remain unchanged.

## Upgrade and rollback

Run the same installer. Unknown user files and unrelated catalog entries are retained; modified program files cause an explicit conflict instead of silent overwrite. Reinstallation is idempotent. Failed transactions restore only attempted resources whose contents can still be verified; concurrent foreign edits are preserved and reported. Use -Rollback <transaction-id> to restore a completed install, provided no later edits would be overwritten. Refresh the host-managed plugin afterward.

See [installation, upgrade, recovery and uninstall](docs/install.md), [design and runtime comparison](docs/v1.0.1-design.md), [validation](docs/validation.md), [ChatGPT acceptance](docs/chatgpt-acceptance.md), and [release notes](docs/release-v1.0.2.md). These detailed guides are in Chinese.

The project remains ISC licensed, with MIT attribution for the adapted clarification mechanism from mattpocock/skills. Runtime licenses remain inside the official Python archive. No runtime binaries, credentials, user configuration or machine logs are included in release packages.
