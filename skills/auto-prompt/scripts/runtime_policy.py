#!/usr/bin/env python3
"""Interpreter reuse policy, reviewed against upstream releases on 2026-10-08."""
import hashlib
import json
import subprocess
import sys
import zipfile

# Keep legacy renderer syntax compatibility separate from installation maintenance.
MINIMUM_PATCH = {(3, 11): 17, (3, 12): 15, (3, 13): 16, (3, 14): 8}


def supported(version):
    minimum = MINIMUM_PATCH.get(tuple(version[:2]))
    return minimum is not None and version[2] >= minimum


def main():
    if not supported(sys.version_info):
        print("Python does not meet the maintained runtime policy; prepare the dedicated runtime", file=sys.stderr)
        return 2
    print(json.dumps({"python": sys.executable, "version": list(sys.version_info[:3])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
