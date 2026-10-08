# Auto Prompt Skill · v1.1.0

> v1.1.0 security fixes strengthen file, installation, input and runtime protections. See [release notes (Chinese)](docs/release-v1.1.0.md) for changes and upgrade limits.

Turn a target agent and a rough request into a copyable prompt inside ChatGPT. For people who want to clarify an idea before handing it to Codex, ChatGPT or a video model. Covers software, study, research, writing and video tasks.

[Desktop bundle](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-bundle.zip) · [Web plugin ZIP](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-plugin.zip) · [Installation guide (Chinese)](docs/install.md) · [中文](README.md)

## What it does

- **Organizes requests** while preserving goals, context, constraints, deliverables and validation criteria, without inventing missing facts.
- **Clarifies key choices** in short rounds, reusing information already supplied.
- **Revises prompts** through append, replace and undo requests, or starts a new task.
- **Offers two modes**: flexible model rewriting by default, or an explicitly chosen offline strict renderer.

The skill generates prompts; it does not execute their tasks. The **host** is the ChatGPT web or desktop environment running the skill. The **target agent** is the tool receiving the generated prompt. They may differ.

## Installation: choose your ChatGPT environment

| Environment | Download | Entry point |
| --- | --- | --- |
| ChatGPT in a browser on Windows | `auto-prompt-skill-1.1.0-plugin.zip` | Plugins → top-right `+` → Upload plugin |
| ChatGPT Windows x64 desktop app, local Work | `auto-prompt-skill-1.1.0-bundle.zip` | Extract → `Install-Windows.cmd` → enable in the client |

Find both downloads and `SHA256SUMS.txt` under **Assets** on the [v1.1.0 release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.1.0). Detailed instructions are in the [installation guide (Chinese)](docs/install.md).

### Web: upload the plugin

1. Download [plugin.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-plugin.zip), [verify its checksum](docs/install.md#1-下载网页插件包), and keep it zipped.
2. Open ChatGPT in your browser. Select **Plugins** in the left sidebar, select the `+` beside the search box, then **Upload plugin** and choose that ZIP.
3. After the import-success message, select **View plugin**. Find **Auto Prompt Skill** under **Personal → Created by me**. Complete installation if the detail page still offers an install button.
4. Start a new chat, type `@` and select the Auto Prompt plugin or skill, then send `Please invoke the Auto Prompt skill`. Supply your target agent and request when prompted.

Upload availability depends on account and workspace settings. Whether the web route depends on a local Windows installer or Python has not been independently verified. Strict script execution, task isolation and structured input controls on the web also remain unverified; see the [validation limits (Chinese)](docs/validation.md#网页版验证边界).

### Desktop: install locally

1. Install and sign in to the ChatGPT **Windows desktop app** with local Work and local plugin-source support.
2. Download [bundle.zip](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.1.0/auto-prompt-skill-1.1.0-bundle.zip), [verify its checksum](docs/install.md#2-下载并核对文件), extract it and double-click `Install-Windows.cmd`.
3. After `严格脚本自检：通过` (strict launcher self-test passed), refresh or restart the desktop client. In Plugins, switch to the local source printed by setup—normally **Auto Prompt Local** / `auto-prompt-local` for a new catalog—and install or refresh **Auto Prompt Skill**.
4. Open a new Work chat connected to this computer, select the skill and send `Please invoke the Auto Prompt skill`. The [desktop guide (Chinese)](docs/install.md#二windows-桌面客户端本地安装) explains source names, success checks and missing-source troubleshooting.

Setup reuses Python meeting the [maintenance policy (Chinese)](docs/security-maintenance.md#运行时维护) or downloads and verifies the pinned official Python 3.13.16 Windows x64 runtime into a project-owned directory. The first runtime download is about 10.9 MB. Global Python, PATH and the registry are unchanged; no pip, npm, Ollama, Docker or persistent service is required.

Setup checks the files and strict launcher; client enablement still needs a new-chat check. Local source installation and web upload are separate routes: local setup does not automatically create a web personal entry. Each route needs the appropriate account and client features. Other platforms retain a [manual compatibility route](docs/install.md#手动兼容路径), without a claim of full platform validation.

## Everyday use

Invoke the skill alone for guidance, or send the target, request and constraints together in ChatGPT:

~~~text
Please use Auto Prompt.
Target agent: ChatGPT
Request: Help me learn probability. I know the basics. Explain with everyday examples, then give two self-check questions.
Constraints: Use English. Do not assume I know calculus.
~~~

For other tasks, describe the desired result in the same way: ask Codex to fix `parser.py` while changing only that file and adding no dependencies, or prepare a rainy-day café video prompt after clarifying key delivery choices.

After generation, say `Append…`, `Replace… with…` or `Undo the last change`. Say `New task` to reset requirements, or `Use it as is` to end conversion. The first flexible result may include one optional revision hint outside the copyable prompt; strict outputs, revision replies and result-only requests omit it.

You can answer `Not sure yet`, `Suggest an option` or `Give me a draft first`. Suggestions stay separate from confirmed requirements. A suitable structured input tool is used when the host exposes it; otherwise clarification uses ordinary text.

## Flexible and strict modes

**Natural-language conversation defaults to flexible mode.** The current model interprets and rewrites the request, so outputs may vary with the model and context. **Explicit strict mode** guarantees identical UTF-8 output for identical JSON under a fixed renderer and templates. Extracting JSON from natural language is outside that guarantee.

Strict mode requires the host to execute the packaged script; the local route has been tested, while web execution has not. It retains four Chinese/English development/general templates. It does not automatically understand or translate arbitrary requests. The skill clarifies conflicts with fixed templates or legacy language rules; the direct CLI does not perform semantic clarification. Target-specific formats, parameters and permissions cannot be inferred from an agent's name.

Compatibility is unchanged: complete legacy JSON without `strictMode` still means `true`; `strictMode=false` uses flexible model rewriting; the strict CLI retains its parameters and defaults. See the [input reference (Chinese)](skills/auto-prompt/references/input.md) for fields and language limits.

## Upgrade, recovery and other installation routes

For local desktop updates, download the bundle and checksum list, run the same setup entry and refresh the client plugin. This local route preserves independent user files, stops on modified program files or conflicting paths, and avoids duplicate catalog entries. Web personal-import updates and their unverified scope have a separate [guide (Chinese)](docs/install.md#升级与自定义内容).

For **v1.1.0**, download the new package and checksums, rerun setup and refresh the plugin. If an existing interpreter does not meet the patch policy, setup prepares a dedicated runtime without upgrading shared dependencies. See [v1.1.0 release notes (Chinese)](docs/release-v1.1.0.md).

Historically, **v1.0.2 has same-version revisions; the version number alone does not identify an update.** The 2026-10-05 revision improved interpreter reuse and setup checks. The 2026-10-07 revision improved recovery, concurrent runtime preparation, packaging checks and malformed-configuration errors. See [release notes (Chinese)](docs/release-v1.0.2.md).

The [installation guide (Chinese)](docs/install.md) covers offline setup, explicit interpreters, directory migration, rollback, uninstall and manual compatibility routes. Offline support applies to dependency preparation and strict rendering; ChatGPT conversation still uses the host service. Preserved user files do not automatically apply their rules; provide or reference them when using the skill.

## Development and validation

From the repository root, in a terminal with compatible Python:

~~~sh
python -m unittest discover -s tests -v
python scripts/build_release.py
~~~

Release packages use a public-file allowlist and exclude runtimes, user configuration, backups and machine logs. See [validation (Chinese)](docs/validation.md) for automated checks, the Windows integration entry and unverified scope. Guidance, input controls and prompt quality require [real client acceptance (Chinese)](docs/chatgpt-acceptance.md).

## License and sources

The project uses the [ISC license](LICENSE). Clarification behavior is partly adapted from mattpocock/skills grill-me/grilling, retaining decision dependencies and short rounds while limiting questions and removing upstream tool and subagent dependencies. The pinned source, MIT license and adaptation scope are in the [attribution (Chinese)](skills/auto-prompt/references/grill-me-attribution.md).

The optional runtime comes from the [official pinned Python release](https://www.python.org/downloads/release/python-31316/) and retains its `LICENSE.txt`; the bundle itself contains no interpreter. See [OpenAI's skills documentation](https://learn.chatgpt.com/docs/build-skills) for skill mechanics, and the [migration guide (Chinese)](docs/migration.md) for legacy service and shared-dependency boundaries.
