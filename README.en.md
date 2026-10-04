# Auto Prompt Skill · v1.0.1

Accepted by the user in ChatGPT local Work. Download the bundle and SHA-256 checksums from the [v1.0.1 release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.0.1).

Turn a target agent and a rough request into a usable prompt inside ChatGPT. The **host** runs the skill; the **target agent** receives its generated prompt. Targets may include Codex, ChatGPT or video models, across software, study, research, writing and video tasks.

## Windows x64 quick start

Install/sign in to a ChatGPT desktop host that supports local skills. Extract the release bundle and run Install-Windows.cmd. Setup reuses a compatible interpreter or downloads the pinned official Python 3.13.12 embeddable package with SHA-256 verification. It installs only project-owned files; no global Python/PATH changes. Then install/refresh Auto Prompt Skill in the local Plugins source, restart and open a new local chat. Host installation, login, permissions and enablement remain user steps.

Offline setup can use a compatible interpreter or the official runtime archive via -RuntimeArchive. Runtime preparation is scoped to Windows x64; other platforms retain the existing Python installation route.

## Use and compatibility

Invoke the skill alone for brief guidance, or provide the target and request together. Supplied information is reused; material ambiguities are clarified in small rounds. Structured input is used only when the current host actually exposes a suitable tool; otherwise ordinary text questions work.

Natural-language requests now default to flexible model rewriting. Explicit strict mode runs the script and returns its result unchanged. Complete legacy JSON without strictMode still means true, and the direct CLI defaults are unchanged. Fixed renderer and templates plus identical JSON produce identical UTF-8 bytes. This does not make natural-language extraction deterministic.

## Upgrade and rollback

Run the same installer. Unknown user files and unrelated catalog entries are retained; modified program files cause an explicit conflict instead of silent overwrite. Reinstallation is idempotent. Failed transactions restore program files, catalog and runtime registration. Use -Rollback <transaction-id> to restore a completed install, provided no later edits would be overwritten. Refresh the host-managed plugin afterward.

See [installation, upgrade, recovery and uninstall](docs/install.md), [design and runtime comparison](docs/v1.0.1-design.md), [validation](docs/validation.md), [ChatGPT acceptance](docs/chatgpt-acceptance.md), and [release notes](docs/release-v1.0.1.md). These detailed guides are in Chinese.

The project remains ISC licensed, with MIT attribution for the adapted clarification mechanism from mattpocock/skills. Runtime licenses remain inside the official Python archive. No runtime binaries, credentials, user configuration or machine logs are included in release packages.
