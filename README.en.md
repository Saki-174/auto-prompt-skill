# Auto Prompt Skill · v1.0.2

Turn a target agent and a rough request into a copyable prompt inside ChatGPT. For people who want to clarify an idea before handing it to Codex, ChatGPT or a video model. Covers software, study, research, writing and video tasks.

[Download the Windows bundle](https://github.com/Saki-174/auto-prompt-skill/releases/download/v1.0.2/auto-prompt-skill-1.0.2-bundle.zip) · [Installation guide (Chinese)](docs/install.md) · [中文](README.md)

## What it does

- **Organizes requests** while preserving goals, context, constraints, deliverables and validation criteria, without inventing missing facts.
- **Clarifies key choices** in short rounds, reusing information already supplied.
- **Revises prompts** through append, replace and undo requests, or starts a new task.
- **Offers two modes**: flexible model rewriting by default, or an explicitly chosen offline strict renderer.

The skill generates prompts; it does not execute their tasks. The **host** is the ChatGPT environment running the skill. The **target agent** is the tool receiving the generated prompt. They may differ.

## Quick start: Windows x64

Install and sign in to a ChatGPT desktop client with local Work and local plugin support. Availability depends on your account, client and workspace settings; installing files cannot supply a missing host feature. See [OpenAI's local plugin guidance](https://developers.openai.com/plugins/build/plugins).

1. **Download and extract.** Open the [v1.0.2 release](https://github.com/Saki-174/auto-prompt-skill/releases/tag/v1.0.2). Under **Assets**, download `auto-prompt-skill-1.0.2-bundle.zip` and `SHA256SUMS.txt`. [Verify the checksum](docs/install.md#2-下载并核对文件), extract the ZIP, and open the folder containing `Install-Windows.cmd`. New users need the bundle, without separate plugin or skill ZIPs.
2. **Run setup.** Double-click `Install-Windows.cmd`. Success shows a Chinese completion or unchanged-files message and `严格脚本自检：通过` (strict launcher self-test passed). Keep the recovery transaction ID when changes are made.
3. **Enable the plugin.** Refresh or restart ChatGPT. In **Plugins**, select the local source printed by setup and install or refresh **Auto Prompt Skill**. Complete permissions and enablement in the client.
4. **Try it in a new chat.** Open a Work chat connected to this computer and send `Please invoke the Auto Prompt skill`. Expect brief guidance, then supply your target agent and request. Use the [new-chat checklist (Chinese)](docs/chatgpt-acceptance.md) for full acceptance.

No Python preinstallation is required. Setup reuses compatible Python 3.9–3.14 or downloads the pinned official Python 3.13.12 Windows x64 runtime with SHA-256 verification into a project-owned directory. The first runtime download is about 10.4 MB. Setup does not change global Python, PATH or the registry; no pip, npm, Ollama, Docker or persistent service is needed.

**A passed setup self-test confirms files and the strict launcher, while client enablement and dialogue behavior need a new-chat check.** Other platforms retain a [manual compatibility route](docs/install.md#手动兼容路径); this is not a claim of full host validation. Local installation does not automatically synchronize to web, mobile or cloud environments.

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

Strict mode retains four Chinese/English development/general templates. It does not automatically understand or translate arbitrary requests. The skill clarifies conflicts with fixed templates or legacy language rules; the direct CLI does not perform semantic clarification. Target-specific formats, parameters and permissions cannot be inferred from an agent's name.

Compatibility is unchanged: complete legacy JSON without `strictMode` still means `true`; `strictMode=false` uses flexible model rewriting; the strict CLI retains its parameters and defaults. See the [input reference (Chinese)](skills/auto-prompt/references/input.md) for fields and language limits.

## Upgrade, recovery and other installation routes

Download the bundle and checksum list again, run the same setup entry, then refresh the client plugin. Independent user files are preserved. Modified program files or conflicting paths stop installation with a clear error instead of being silently overwritten or merged. Reinstallation does not duplicate catalog entries.

**v1.0.2 has same-version revisions; the version number alone does not identify an update.** The 2026-10-05 revision improved interpreter reuse and setup checks. The 2026-10-07 revision improved recovery, concurrent runtime preparation, packaging checks and malformed-configuration errors. See [release notes (Chinese)](docs/release-v1.0.2.md).

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

The optional runtime comes from the [official pinned Python release](https://www.python.org/downloads/release/python-31312/) and retains its `LICENSE.txt`; the bundle itself contains no interpreter. See [OpenAI's skills documentation](https://learn.chatgpt.com/docs/build-skills) for skill mechanics, and the [migration guide (Chinese)](docs/migration.md) for legacy service and shared-dependency boundaries.
