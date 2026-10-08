#!/usr/bin/env python3
"""Offline, deterministic port of the local Auto Prompt strict template renderer."""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from string import Template

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
FIELDS = {"targetAgent", "rawPrompt", "requirements", "profile", "strictMode", "enableDeepReasoning"}
MAX_INPUT_BYTES = 1024 * 1024
MAX_AGENT_UNITS = 256


def clean(value):
    return value.strip().replace("\r\n", "\n")


def output_language(requirements):
    # Preserve legacy language detection, including its deliberately limited coverage.
    if re.search(r"日语|日文|法语|法文|德语|德文|西班牙语|韩语|韩文|俄语|阿拉伯语|葡萄牙语", requirements):
        raise ValueError("strictMode supports explicit Chinese or English output only; use the skill's flexible mode for another language")
    return "en" if re.search(r"english|英语|英文", requirements, re.I) else "zh"


def merge_requirements(requirements, language):
    defaults = []
    if not re.search(r"chinese|中文|汉语|english|英语|英文", requirements, re.I):
        defaults.append("保持中文。")
    if not re.search(r"(?:缺失|不足|未知|未提供|missing|unknown|unprovided).{0,30}(?:待确认|pending|to be confirmed)", requirements, re.I | re.S):
        defaults.append('Mark missing information as "To be confirmed".' if language == "en" else "缺失信息标记为“待确认”。")
    if not re.search(r"(?:不得|不要|禁止|do not|don't|must not).{0,20}(?:虚构|编造|invent|fabricat).{0,100}(?:项目文件|文件|接口|api|依赖|版本|数值|功能|feature)", requirements, re.I | re.S):
        defaults.append("Do not invent project files, APIs, dependencies, versions, numbers, or features." if language == "en" else "不得虚构项目文件、接口、依赖、版本、数值或功能。")
    return "\n".join(item for item in [requirements, *defaults] if item)


def utf16_length(value):
    """Match the legacy JavaScript input-length limits for non-BMP characters."""
    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def render_prompt(payload):
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    unknown = set(payload) - FIELDS
    if unknown:
        raise ValueError("unknown input fields are not supported; use the documented schema")
    for name in ("rawPrompt", "requirements", "targetAgent"):
        if name in payload and not isinstance(payload[name], str):
            raise ValueError(name + " must be a string")
    for name in ("strictMode", "enableDeepReasoning"):
        if name in payload and not isinstance(payload[name], bool):
            raise ValueError(name + " must be a boolean")
    if payload.get("strictMode", True) is False:
        raise ValueError("this offline renderer only supports strictMode=true; use the skill's flexible mode for model rewriting")
    profile = payload.get("profile", "development")
    if profile not in ("development", "general"):
        raise ValueError("profile must be development or general")
    raw = clean(payload.get("rawPrompt", ""))
    if not raw:
        raise ValueError("rawPrompt cannot be empty or whitespace")
    if utf16_length(raw) > 20000:
        raise ValueError("rawPrompt exceeds 20000 UTF-16 units")
    explicit = payload.get("requirements", "")
    if utf16_length(explicit) > 8000:
        raise ValueError("requirements exceeds 8000 UTF-16 units")
    requirements = clean(explicit)
    agent = payload.get("targetAgent", "")
    if utf16_length(agent) > MAX_AGENT_UNITS:
        raise ValueError("targetAgent exceeds 256 UTF-16 units")
    if "\r" in agent or "\n" in agent:
        raise ValueError("targetAgent must be a single line")
    agent = re.sub(r"\s+", " ", clean(agent)) or "待确认"
    language = output_language(requirements)
    if language == "en" and agent == "待确认":
        agent = "To be confirmed"
    template = Template((TEMPLATES / (language + "-" + profile + ".txt")).read_text(encoding="utf-8"))
    # substitute is a single pass: user text containing $ or braces stays untouched.
    return template.substitute(target_agent=agent, raw_prompt=raw, requirements=merge_requirements(requirements, language))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON keys are not supported")
        result[key] = value
    return result


def read_input(stream):
    data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError("input JSON exceeds 1048576 bytes")
    return data.decode("utf-8-sig")


def write_output(target, data, input_path=None):
    # Path spelling alone does not identify a file: hard links share an inode.
    if input_path is not None:
        if target.resolve() == input_path.resolve() or (target.exists() and target.samefile(input_path)):
            raise ValueError("output must not overwrite the input JSON")
    fd, temporary = tempfile.mkstemp(prefix=".auto-prompt-output-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        # Replacing the directory entry avoids truncating any existing hard-link peer.
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="UTF-8 JSON file, or - for stdin")
    source.add_argument("--raw-prompt", help="original request; use a JSON file for sensitive or multiline text")
    parser.add_argument("--agent", default=None)
    parser.add_argument("--requirements", default=None)
    parser.add_argument("--profile", choices=("development", "general"), default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", help="write UTF-8 output to this path instead of stdout")
    args = parser.parse_args(argv)
    try:
        if args.input is not None:
            if any(value is not None for value in (args.agent, args.requirements, args.profile)):
                raise ValueError("put agent, requirements and profile in the JSON when using --input")
            if args.input == "-":
                content = read_input(sys.stdin.buffer)
            else:
                with Path(args.input).open("rb") as handle:
                    content = read_input(handle)
            payload = json.loads(content, object_pairs_hook=unique_object)
        else:
            payload = {"rawPrompt": args.raw_prompt}
            for key, value in (("targetAgent", args.agent), ("requirements", args.requirements), ("profile", args.profile)):
                if value is not None:
                    payload[key] = value
        optimized = render_prompt(payload)
        result = optimized if args.format == "text" else json.dumps({"optimizedPrompt": optimized, "model": "strict-deterministic-v1"}, ensure_ascii=False, indent=2)
        data = result.encode("utf-8")
        if args.output:
            target = Path(args.output)
            write_output(target, data, Path(args.input) if args.input not in (None, "-") else None)
        else:
            sys.stdout.buffer.write(data)
        return 0
    except RecursionError:
        print("Auto Prompt: input JSON exceeds supported nesting depth", file=sys.stderr)
        return 2
    except UnicodeError:
        print("Auto Prompt: input must contain valid UTF-8 text", file=sys.stderr)
        return 2
    except (ValueError, OSError) as error:
        # Do not echo raw user content on validation errors.
        print("Auto Prompt: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
