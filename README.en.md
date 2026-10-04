# Auto Prompt Skill

Turn a **target agent + raw request** into a faithful structured prompt for ChatGPT Work or Codex.

The default strict mode ports the local Auto Prompt renderer into standard-library Python. Four legacy templates cover Chinese/English and development/general tasks. No Docker, Ollama, backend, MCP adapter, tunnel, API key, or network is needed. Flexible mode uses the current host model.

Download the **bundle ZIP** from [Releases](https://github.com/Saki-174/auto-prompt-skill/releases/latest). On Windows, extract it and run `Install-Windows.cmd`. Restart the desktop client, select the local marketplace reported by the installer, and install Auto Prompt Skill. The installer preserves existing entries and backs up changed files. On other systems, use Python 3.9+:

```sh
python scripts/install.py --mode plugin
```

For a standalone Codex skill:

```sh
python scripts/install.py --mode skill
```

Mention the skill with `@` in ChatGPT Work or `$auto-prompt` in Codex CLI/IDE. Merely attaching the ZIP to a regular chat does not install it. Local skills require the corresponding connected local execution environment.

Run the deterministic renderer directly:

```sh
python skills/auto-prompt/scripts/render_prompt.py --input examples/english.json
```

Identical JSON inputs produce identical UTF-8 outputs. Natural-language field extraction and flexible rewriting remain model-generated. Strict mode preserves legacy language detection; it does not translate the raw request. Missing agents are marked as unconfirmed. Unknown fields and invalid types fail explicitly.

```sh
python -m unittest discover -s tests -v
python scripts/build_release.py
```

[Chinese documentation](README.md) · [Installation](docs/install.md) · [Migration](docs/migration.md) · [ISC License](LICENSE) · [Provenance](NOTICE)
